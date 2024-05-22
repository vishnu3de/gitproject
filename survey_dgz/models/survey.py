import datetime

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError, RedirectWarning
from odoo.exceptions import UserError
from odoo.tools import email_split, email_normalize, email_split_and_format
import logging
import werkzeug


_logger = logging.getLogger(__name__)


class Question(models.Model):
    _inherit = 'survey.question'
    checkbox = fields.Boolean('Checkbox', default=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super(Question, self).default_get(fields_list)

        if 'constr_mandatory' in fields_list:
            defaults.update({
                'constr_mandatory': True,
            })
        if 'matrix_subtype' in fields_list:
            defaults.update({
                'matrix_subtype': 'simple',
            })

        if 'suggested_answer_ids' in fields_list:
            question_values = [
                (0, 0, {'value': _('Very good')}),
                (0, 0, {'value': _('Good')}),
                (0, 0, {'value': _('Fair')})
            ]

            defaults.update({
                'suggested_answer_ids': question_values,
            })

        if 'matrix_row_ids' in fields_list:
            question_sub_values = [
                (0, 0, {'value': 'How would you rate your overall customer experience?'}),
                (0, 0, {'value': 'How satisfied were you with the product & technical support?'}),
                (0, 0, {'value': 'How satisfied were you with customer support?'}),
                (0, 0, {'value': 'How was the timeliness of delivery & coordination support?'}),
                (0, 0, {'value': 'How would you rate the Overall satisfaction & experience?'})
            ]

            defaults.update({
                'matrix_row_ids': question_sub_values,
            })

        return defaults


class Survey_input(models.Model):
    _inherit = 'survey.survey'

    expire_onoff = fields.Boolean(string="Reset Link", default=False)
    token_expiration = fields.Integer(string='Reset Token')
    interval_type = fields.Selection([
        ('minutes', 'Minutes'),
        ('days', 'Days'), ('weeks', 'Weeks')], default="days")
    date_expire = fields.Datetime(string="expire")
    partner_ids = fields.Many2many(
        'res.partner', 'survey_survey_partner_ids', 'survey_id', 'partner_id', string='Recipients',
        domain="[ \
                '|', (survey_users_can_signup, '=', 1), \
                '|', (not survey_users_login_required, '=', 1), \
                     ('user_ids', '!=', False), \
            ]"
    )

    survey_users_login_required = fields.Boolean(related="users_login_required", readonly=True)
    survey_users_can_signup = fields.Boolean(related='users_can_signup')

    @api.onchange('token_expiration', 'interval_type')
    def calculate_new_date(self):
        """ Calculate the new date and time based on the value of my_field and the interval_type field. """
        now = datetime.now()

        if self.interval_type == 'minutes':
            new_date = now + timedelta(minutes=self.token_expiration)
        elif self.interval_type == 'days':
            new_date = now + timedelta(days=self.token_expiration)
        elif self.interval_type == 'weeks':
            new_date = now + timedelta(weeks=self.token_expiration)
        else:
            new_date = now

        self.date_expire = new_date

    def check_token_expiration(self):
        """ Check if the survey token has expired. """
        now = datetime.now()
        if self.expire_onoff == True:
            if self.date_expire < now:
                new_access_token = self._get_default_access_token()
                self.access_token = new_access_token
                self.expire_onoff = False
                self.token_expiration = False
                self.interval_type = False
                self.date_expire = False

    def action_send_survey(self):
        self.check_token_expiration()
        return super(Survey_input, self).action_send_survey()

    @api.model
    def default_get(self, fields_list):
        defaults = super(Survey_input, self).default_get(fields_list)

        if 'title' in fields_list and 'title' not in defaults:
            defaults['title'] = 'Clientele testimonial'

        if 'question_and_page_ids' in fields_list:
            question_defaults = [

                (0, 0, {
                    'title': 'Kindly provide any additional comments or suggestions',
                    'question_type': 'matrix', }),
                (0, 0, {'title': 'OVERALL CUSTOMER EXPERIENCE', 'question_type': 'char_box'}),
            ]

            defaults['question_and_page_ids'] = question_defaults

        defaults['questions_layout'] = 'one_page'
        defaults[
            'description_done'] = 'Thank you for taking the time to provide your feedback. Your insights are invaluable to us as we strive for excellence. We look forward to continuing to serve you and exceeding your expectations in the future. If you have any further comments or suggestions, please feel free to contact us. Have a great day!'
        defaults[
            'description'] = 'At Testron, we value your thoughts and opinions. Your feedback helps us understand your experiences better, allowing us to continually improve our products and services to better serve you. Please take a few moments to fill out this feedback form, and let us know how we re doing. Your responses are invaluable to us and will be kept confidential.'

        return defaults

    def _get_pages_and_questions_to_show(self):
        result = super(Survey_input, self)._get_pages_and_questions_to_show()
        result = result.filtered(lambda question: question.checkbox)
        if not result:
            raise ValidationError("No Validated Questions.")
        return result


class User_input(models.Model):
    _inherit = 'survey.user_input'


class SurveyInvite(models.TransientModel):
    _name = 'survey.invite'
    _inherit = 'survey.invite'



    def _send_mail(self, answer):
        """ Create mail specific for recipient containing notably its access token """
        email_from = self._render_field('email_from', answer.ids)[answer.id]
        if not email_from:
            raise UserError(_("Unable to post message, please configure the sender's email address."))
        subject = self._render_field('subject', answer.ids)[answer.id]
        body = self._render_field('body', answer.ids, post_process=True)[answer.id]
        # post the message
        mail_values = {
            'email_from': email_from,
            'author_id': self.author_id.id,
            'model': None,
            'res_id': None,
            'subject': subject,
            'body_html': body,
            'attachment_ids': [(4, att.id) for att in self.attachment_ids],
            'auto_delete': True,
        }
        if answer.partner_id:
            mail_values['recipient_ids'] = [(4, answer.partner_id.id)]
        else:
            mail_values['email_to'] = answer.email

        # optional support of default_email_layout_xmlid in context
        email_layout_xmlid = self.env.context.get('default_email_layout_xmlid', self.env.context.get('notif_layout'))
        if email_layout_xmlid:
            template_ctx = {
                'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=self.survey_id.title)),
                'model_description': self.env['ir.model']._get('survey.survey').display_name,
                'company': self.env.company,
            }
            body = self.env['ir.qweb']._render(email_layout_xmlid, template_ctx, minimal_qcontext=True, raise_if_not_found=False)
            if body:
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            else:
                _logger.warning('QWeb template %s not found or is empty when sending survey mails. Sending without layout', email_layout_xmlid)

        return self.env['mail.mail'].sudo().create(mail_values)

    def action_invite(self):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed """
        self.ensure_one()
        Partner = self.env['res.partner']

        # compute partners and emails, try to find partners for given emails
        valid_partners = self.survey_id.partner_ids
        langs = set(valid_partners.mapped('lang')) - {False}
        if len(langs) == 1:
            self = self.with_context(lang=langs.pop())
        valid_emails = []
        emails = email_split(self.emails or '')
        for email in emails:
            partner = False
            email_normalized = email_normalize(email)
            if email_normalized:
                limit = None if self.survey_id.users_login_required else 1
                partner = Partner.search([('email_normalized', '=', email_normalized)], limit=limit)
            if partner:
                valid_partners |= partner
            else:
                email_formatted = email_split_and_format(email)
                if email_formatted:
                    valid_emails.extend(email_formatted)

        if not valid_partners and not valid_emails:
            raise UserError(_("Please enter at least one valid recipient."))

        answers = self._prepare_answers(valid_partners, valid_emails)
        for answer in answers:
            self._send_mail(answer)

        return {'type': 'ir.actions.act_window_close'}
