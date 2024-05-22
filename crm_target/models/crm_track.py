from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import json


class Crm_Track(models.Model):
    _name = "crm.track"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Many2one('res.users', string='SalesPerson Name', tracking=True)
    filter = fields.Boolean("Filter by Date")
    email = fields.Char('Email')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    count_pipelines = fields.Integer('Open Opportunities',compute='_compute_count_pipelines',store=True)
    opportunities_amount = fields.Float('Open opportunities revenue',compute='_compute_count_pipelines',store=True)
    won_leads = fields.Integer('Won opportunities',compute='_compute_count_pipelines',store=True)
    won_leads_amount = fields.Float('Won opportunities revenue',compute='_compute_count_pipelines',store=True)
    lost_leads = fields.Integer('Lost opportunities',compute='_compute_count_pipelines',store=True)
    lost_leads_amount = fields.Float('Lost opportunities revenue',compute='_compute_count_pipelines',store=True)
    total_revenue = fields.Float('Total opportunities revenue',compute='_compute_count_pipelines',store=True)
    proposals = fields.Integer("Proposals",compute='_compute_count_pipelines',store=True)
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')

    def create_crm_track_records(self):
        users_with_leads = self.env['crm.lead'].read_group(
            domain=[('user_id', '!=', False)],
            fields=['user_id'],
            groupby=['user_id']
        )
        for group in users_with_leads:
            user_id = group['user_id'][0]
            if not self.search([('name', '=', user_id)]):
                user = self.env['res.users'].browse(user_id)
                self.create({
                    'name': user_id,
                    'email': user.email,
                    'company_id': user.company_id.id,
                })

    def action_primary_channel_button(self):
        return {
            'name': 'Pipeline',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'kanban,form',
            'domain': [('user_id', '=', self.name.id)],
            'context': {
                'group_by': 'user_id',
            },

        }

    @api.depends('name','date_from','date_to','filter')
    def _compute_count_pipelines(self):
        for record in self:
            if record.name:
                domain = [('user_id', '=', record.name.id)]
                if record.filter != True:
                    record.date_from=False
                    record.date_to = False
                if record.date_from:
                    domain.append(('create_date', '>=', record.date_from))
                if record.date_to:
                    domain.append(('create_date', '<=', record.date_to))
                open_pipeline = self.env['crm.lead'].search(domain + [('stage_id.is_won', '=', False)])
                won_pipeline = self.env['crm.lead'].search(domain + [('stage_id.is_won', '=', True)])
                lost_pipeline = self.env['crm.lead'].search(domain + [('active', '=', False), ('probability', '=', 0)])
                total_revenue = self.env['crm.lead'].search(domain)
                total_proposals = self.env['sale.order'].search_count(domain)

                open_total_revenue = sum(record.expected_revenue for record in open_pipeline)
                won_total_revenue = sum(record.expected_revenue for record in won_pipeline)
                lost_total_revenue = sum(record.expected_revenue for record in lost_pipeline)
                total_total_revenue = sum(record.expected_revenue for record in total_revenue)

                record.count_pipelines = len(open_pipeline)
                record.opportunities_amount = open_total_revenue

                record.won_leads = len(won_pipeline)
                record.won_leads_amount = won_total_revenue

                record.lost_leads = len(lost_pipeline)
                record.lost_leads_amount = lost_total_revenue

                record.total_revenue = total_total_revenue

                record.proposals = total_proposals

            else:
                record.count_pipelines = 0
                record.opportunities_amount = 0
                record.won_leads = 0
                record.won_leads_amount = 0
                record.lost_leads = 0
                record.lost_leads_amount = 0
                record.total_revenue = 0
                record.proposals = 0




    # def _kanban_dashboard_graphs(self):
    #     data_per_week = []
    #     current_date = fields.Date.today()
    #     for target in self:
    #         if target.won_target_count > 0:
    #
    #             for i in range(4):
    #                 start_date = current_date - timedelta(days=7 * (3 - i))
    #                 end_date = start_date + timedelta(days=6)
    #                 proportion = target.won_target
    #                 data_per_week.append({
    #                     'label': start_date.strftime('%d-%b') + '-' + end_date.strftime('%d %b'),
    #                     'value': proportion,
    #                     'type': 'past' if start_date < fields.Date.today() else 'future',
    #                 })
    #     json_data = json.dumps([{
    #         'values': data_per_week,
    #         'area': False,
    #         'title': 'Won Targets',
    #         'key': 'Won Targets',
    #
    #     }])
    #     self.kanban_dashboard_graph = json_data
