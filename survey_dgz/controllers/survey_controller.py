from odoo import http
from datetime import datetime, timedelta
from odoo.http import request

from odoo.addons.survey.controllers.main import Survey

class SurveyExtended(Survey):
    @http.route('/survey/start/<string:survey_token>', type='http', auth='public', website=True)
    def survey_start(self, survey_token, answer_token=None, email=False, **post):
        survey_record = http.request.env['survey.survey'].search([('access_token', '=', survey_token)])
        survey_record.check_token_expiration()
        return super(SurveyExtended, self).survey_start(survey_token, answer_token, email, **post)
