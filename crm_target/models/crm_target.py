from odoo import models,fields,api,_
from odoo.exceptions import ValidationError
from datetime import datetime,timedelta
import json

class Crm_Target(models.Model):
    _name = "crm.target"
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Many2one('res.users',string='SalesPerson Name',tracking=True)
    email = fields.Char('Email')
    yearly_target = fields.Integer(string="Target", tracking=True , default='1',store = True)
    won_target = fields.Integer(string="Won Target", compute='_compute_won_target',search=True,store = True)
    won_target_count = fields.Integer(string="Won Target Count", compute='_compute_won_target_count',search=True)
    goal_startdate = fields.Date(string="Goal Startdate", tracking=True)
    goal_deadline = fields.Date(string="Goal Deadline", tracking=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    sales_target_achievement = fields.Char(string="Sales Target Achievement", compute="_compute_target_achieved")
    count_pipelines = fields.Integer(compute='_compute_count_pipelines')
    select_state =  fields.Selection([('draft', 'Draft'), ('ongoing', 'Ongoing'), ('completed', 'Completed'), ('closed', 'Closed')], string='Status',store = True,compute='_check_target_completion',tracking=True)
    duration = fields.Integer(string="Duration", compute='_compute_duration', store=True)
    flag = fields.Boolean(compute='check_group')
    kanban_dashboard_graph = fields.Text(compute='_kanban_dashboard_graphs')

    @api.depends('won_target_count', 'yearly_target')
    def _kanban_dashboard_graphs(self):
        data_per_week = []
        current_date = fields.Date.today()
        for target in self:
            if target.won_target_count > 0:

                for i in range(4):
                    start_date = current_date - timedelta(days=7 * (3 - i))
                    end_date = start_date + timedelta(days=6)
                    proportion = target.won_target
                    data_per_week.append({
                        'label': start_date.strftime('%d-%b') + '-' + end_date.strftime('%d %b'),
                        'value': proportion,
                        'type': 'past' if start_date < fields.Date.today() else 'future',
                    })
        json_data = json.dumps([{
            'values': data_per_week,
            'area': False,
            'title': 'Won Targets',
            'key': 'Won Targets',

        }])
        self.kanban_dashboard_graph = json_data




    def check_group(self):
        if self.user_has_groups('crm_target.crm_target_admin'):
            self.flag = True
        else:
            self.flag = False

    def draft_status(self):
        for record in self:
            record.select_state = 'draft'

    def ongoing_status(self):
        for record in self:
            record.select_state = 'ongoing'

    @api.model
    def send_deadline_notification_emails(self):
        today = fields.Date.today()
        tomorrow = today + timedelta(days=1)

        deadline_approaching_targets = self.search([('select_state', '=', 'ongoing'), ('goal_deadline', '=', tomorrow)])
        mail_template = self.env.ref(
            'crm_target.target_reminder_mail_template')

        for target in deadline_approaching_targets:
            mail_template.send_mail(target.id, force_send=True)

    @api.depends('goal_deadline')
    def _compute_duration(self):
        for record in self:
            if record.goal_deadline:
                deadline = fields.Datetime.from_string(record.goal_deadline)
                today = datetime.now()
                if today <= deadline:
                    duration = (deadline - today).days
                    record.duration = duration
                else:
                    record.duration = 0
            else:
                record.duration = 0
    @api.onchange('name')
    def _onchnage_name(self):
        self.email = self.name.email

    @api.constrains('yearly_target')
    def _check_target(self):
        for record in self:
            if record.yearly_target <= 0:
                raise ValidationError("Target can't be zero.")

    @api.model
    def create(self, vals):
        if vals.get('goal_startdate') and vals.get('goal_deadline'):
            start_date = fields.Date.from_string(vals['goal_startdate'])
            deadline = fields.Date.from_string(vals['goal_deadline'])
            if start_date > deadline:
                raise ValidationError("The deadline date cannot be later than the start date.")

        return super(Crm_Target, self).create(vals)

    @api.onchange('name')
    def onchange_users_edit(self):
        if self._origin:
            for record in self:
                if record.name and record.name != record._origin.name:
                    raise ValidationError("Once set, the Salesperson field cannot be altered.")


    def write(self, vals):
        if 'goal_startdate' in vals or 'goal_deadline' in vals:
            start_date = fields.Date.from_string(vals.get('goal_startdate', self.goal_startdate))
            deadline = fields.Date.from_string(vals.get('goal_deadline', self.goal_deadline))
            if start_date > deadline:
                raise ValidationError("The deadline date cannot be later than the start date.")
        return super(Crm_Target, self).write(vals)

    @api.depends('name', 'goal_deadline','goal_startdate')
    def _compute_won_target_count(self):
        for record in self:
            if record.name and record.goal_deadline:
                won_pipeline = self.env['crm.lead'].search_count([
                    ('user_id', '=', record.name.id),
                    ('stage_id.is_won', '=', True),
                    ('date_won', '>=', record.goal_startdate),
                    ('date_won', '<=', record.goal_deadline),
                ])
                record.won_target_count = won_pipeline
    @api.depends('name', 'goal_deadline','goal_startdate')
    def _compute_won_target(self):
        for record in self:
            if record.name and record.goal_deadline:
                won_pipeline = self.env['crm.lead'].search([
                    ('user_id', '=', record.name.id),
                    ('stage_id.is_won', '=', True),
                    ('date_won', '>=', record.goal_startdate),
                    ('date_won', '<=', record.goal_deadline),
                ])
                total_amount = sum(pipeline.expected_revenue for pipeline in won_pipeline)
                record.won_target = total_amount
                if record.select_state != 'closed' and record.select_state != 'draft':
                    if record.won_target >= record.yearly_target:
                        record.select_state = 'completed'
            else:
                record.won_target = (0)

    @api.depends('name', 'goal_deadline','goal_startdate')
    def _compute_count_pipelines(self):
        for record in self:
            if record.name:
                won_pipeline = self.env['crm.lead'].search_count([
                    ('user_id', '=', record.name.id),
                    ('stage_id.is_won', '=', False),
                ])
                record.count_pipelines = won_pipeline

            else:
                record.count_pipelines = 0

    @api.depends('yearly_target','won_target')
    def _compute_target_achieved(self):
        for record in self:
            if record.yearly_target != 0:
                target_achievement = (record.won_target / record.yearly_target) * 100
                percentage= round(target_achievement)
                record.sales_target_achievement = (f"{percentage}%")
            else:
                record.sales_target_achievement = 0.0

    def open_opportunity(self):
        return {
            'name': 'Pipeline',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'kanban,form',
            'domain': [('user_id', '=', self.name.id), ('stage_id.is_won', '=', False)],
            'context': {
                'group_by': 'user_id',
            },

        }

    def won_states(self):
        return {
            'name': 'Pipeline',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'kanban,form',
            'domain': [('user_id', '=', self.name.id), ('stage_id.is_won', '=', True),('create_date', '>=', self.goal_startdate),('create_date', '<=', self.goal_deadline)],
        }

    def close_status(self):
        for record in self:
            record.select_state = 'closed'

    @api.depends('yearly_target', 'won_target','goal_startdate','goal_deadline','select_state')
    def _check_target_completion(self):
        today_date = fields.Date.today()
        records = self.search([])
        for record in records:
            if record.select_state != 'closed':
                if record.yearly_target <= record.won_target:
                    record.select_state = 'completed'
                elif record.goal_deadline and today_date > record.goal_deadline:
                    record.select_state = 'closed'
                elif record.goal_startdate and today_date >= record.goal_startdate:
                     record.select_state = 'ongoing'
                else:
                    record.select_state = "draft"

    def send_mail(self):
       if self.email:
            template = self.env.ref('crm_target.payment_reminder_template')
            for rec in self:
                template.send_mail(rec.id, force_send=True)

class CRMLeads(models.Model):
    _inherit = 'crm.lead'

    date_won = fields.Datetime(string='Date Won', compute='_compute_date_won', store=True)


    @api.depends('stage_id')
    def _compute_date_won(self):
        for lead in self:
            if lead.stage_id and lead.stage_id.is_won:
                lead.date_won = fields.Datetime.now()
            else:
                lead.date_won = False