from odoo import models, fields, api

class SurveyInviteWizard(models.TransientModel):
    _name = 'survey.invite.wizard'
    _description = 'Survey Invite Wizard'

    invite_lines = fields.One2many('survey.invite.wizard.line', 'wizard_id', string='Invite Lines')

class SurveyInviteWizardLine(models.TransientModel):
    _name = 'survey.invite.wizard.line'
    _description = 'Survey Invite Wizard Line'

    wizard_id = fields.Many2one('survey.invite.wizard', string='Wizard')
    email = fields.Char(string='Email')
    survey_link = fields.Char(string='Survey Link')