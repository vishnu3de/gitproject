from odoo import models, fields, api


class Announcements(models.Model):
    _name = 'dgz.announcements'
    _description = 'Announcements for users and employees'

    name = fields.Char('Name',default=lambda self: ('New'))
    announcement = fields.Char('Announcement Text')
    bg_color = fields.Char('Background Colors', default="#FFFFFF")
    font_color = fields.Char('Font Colors', default="#000000")
    active_state = fields.Boolean('Active')
    url_link = fields.Char('URL Link')
    scheduled_date = fields.Datetime('Scheduled date')
    announcement_ids = fields.Many2many('res.users', string='Announcement cancelled users')

    @api.model_create_multi
    def create(self, record):
        for rec in record:
            rec['name'] = self.env['ir.sequence'].next_by_code('dgz.announcements')
        result = super(Announcements, self).create(record)
        return result
