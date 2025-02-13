# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo.exceptions import UserError

class power_notes(models.Model):
    _name = 'power.notes'
    _inherit = ['mail.thread']
    _description = 'power notes'
    _order = 'date desc, shift'
    
    date = fields.Date('Огноо', default=fields.Date.context_today, required=True)
    state = fields.Selection([('draft','Ноорог'),('done','Батлагдсан')], string='Төлөв', default='draft', track_visibility='onchange')
    shift = fields.Selection([('night','Шөнө'),('day','Өдөр')], string='Ээлж', default='day', track_visibility='onchange')
    dispatcher_id = fields.Many2one('res.users', 'Ээлжинд диспетчер техникч')
    master_id = fields.Many2one('res.users', 'Ээлжинд мастер')
    brigad_ids = fields.Many2many('res.users', 'power_notes_brigad_res_users_rel', 'power_id', 'user_id', string='Шуурхай ажиллагааы бригад')
    maintenance_ids = fields.Many2many('res.users', 'power_notes_maintenance_res_users_rel', 'power_id', 'user_id', string='ШУГАМын биргад')
    down_ids = fields.One2many('power.down', 'notes_id', string='Тасралтын мэдээ')
    down_order_ids = fields.One2many('power.down', 'notes_order_id', string='Захиалгат таслалт')
    down_plan_ids = fields.One2many('power.down', 'notes_plan_id', string='Төлөвлөгөөт таслалтын ажил')
    down_call_ids = fields.One2many('power.down', 'notes_call_id', string='Дуудлагаар хийгдсэн ажил')
    down_daily_ids = fields.One2many('power.down', 'notes_daily_id', string='Өдөр тутмын шуурхайд төлөвлөгдсөн ажил')
    portable_ids = fields.One2many('power.portable', 'notes_id', string='Экскаваторын зогсолт')
    
    @api.constrains('date','shift')
    def _check_shift_date(self):
        for rec in self.sudo():
            if self.sudo().search([('id','!=',rec.id),('date','=',rec.date),('shift','=',rec.shift)]):
                raise UserError('Өдөрт нэг удаа үүсэх ёстой')
    
    @api.depends('date','shift')
    def name_get(self):
        result = []
        for s in self:
            name = unicode(s.date) +' / '+ s.shift
            result.append((s.id, name))
        return result
        
    def action_to_done(self):
        self.state='done'

    def action_to_draft(self):
        self.state='draft'