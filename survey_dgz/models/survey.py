import datetime
import logging
import re
import werkzeug
from odoo import models, fields, tools, api, _
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, UserError, RedirectWarning

_logger = logging.getLogger(__name__)

emails_split = re.compile(r"[;,\n\r]+")


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


class survey_invite(models.TransientModel):
    _inherit = 'survey.invite'

    def copy_link(self):

        self.ensure_one()
        Partner = self.env['res.partner']

        # compute partners and emails, try to find partners for given emails
        valid_partners = self.partner_ids
        langs = set(valid_partners.mapped('lang')) - {False}
        if len(langs) == 1:
            self = self.with_context(lang=langs.pop())
        valid_emails = []
        for email in emails_split.split(self.emails or ''):
            partner = False
            email_normalized = tools.email_normalize(email)
            if email_normalized:
                limit = None if self.survey_users_login_required else 1
                partner = Partner.search([('email_normalized', '=', email_normalized)], limit=limit)
            if partner:
                valid_partners |= partner
            else:
                email_formatted = tools.email_split_and_format(email)
                if email_formatted:
                    valid_emails.extend(email_formatted)

        if not valid_partners and not valid_emails:
            raise UserError(_("Please enter at least one valid recipient."))

        answers = self._prepare_answers(valid_partners, valid_emails)
        for answer in answers:
            self._send_mail(answer)

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        invite_lines = []

        if self.partner_ids:
            for invite in self.partner_ids:
                # Ensure partner_id is a single record and not a recordset

                partner_id = invite.id

                # Retrieve the corresponding user input record(s)
                user_inputs = self.env['survey.user_input'].search([
                    ('survey_id', '=', self.survey_id.id),
                    ('partner_id', '=', partner_id)
                ])

                for user_input in user_inputs:
                    full_survey_link = f"{base_url}{user_input.get_start_url()}"
                    invite_lines.append((0, 0, {
                        'email': invite.name,
                        'survey_link': full_survey_link
                    }))
        if invite_lines:
            wizard = self.env['survey.invite.wizard'].create({
                'invite_lines': invite_lines
            })

        return {
            'name': 'Survey Invite Wizard',
            'type': 'ir.actions.act_window',
            'res_model': 'survey.invite.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': wizard.id,
            'target': 'new',
        }

