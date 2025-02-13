# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import UserError

class power_relay(models.Model):
    _name = 'power.relay'
    _inherit = ['mail.thread']
    _description = 'power relay'
    _order = 'object_name desc'

    # date = fields.Date('Огноо', default=fields.Date.context_today, required=True)
    object_id = fields.Many2one('power.category', string='Станц', domain="[('main_type', '=', 'group')]")
    object_name = fields.Char(string='Станц нэр', required=True, track_visibility='onchange')
    lines = fields.One2many('power.relay.line','parent_id', string='Мөр')

class power_relay_line(models.Model):
    _name = 'power.relay.line'
    _inherit = ['mail.thread']
    _order = 'fider_id desc'

    parent_id = fields.Many2one('power.relay', string='Parent', ondelete='cascade')
    # date = fields.Date(related='parent_id.date', store=True)
    fider_id = fields.Many2one('power.category', domain="[('main_type','in',['asset'])]", string='Фидер')
    tonoglol_id = fields.Many2one('power.implements', string='Тоноглолууд')
    tavil_id = fields.Many2one('power.selection', string='Тавил', domain="[('type','=','tavil')]", required=True, track_visibility='onchange')
    quidel = fields.Char('Гүйдэл', track_visibility='onchange')
    hugatsaa = fields.Char('Хугацаа', track_visibility='onchange')
    sec1 = fields.Char('Гүйдлийн хамгаалалт Хугацаатай А', track_visibility='onchange')
    sec2 = fields.Char('Гүйдлийн хамгаалалт Хугацаатай Сек', track_visibility='onchange')
    sec3 = fields.Char('Гүйдлийн хамгаалалт хугацаагүй /А/', track_visibility='onchange')
    sec4 = fields.Char('Хүчдлийн хамгаалалт ихсэлт', track_visibility='onchange')
    sec5 = fields.Char('Хүчдлийн хамгаалалт Бууралт', track_visibility='onchange')
    sec6 = fields.Char('Давтамжийн хамгаалал ихсэлт', track_visibility='onchange')
    sec7 = fields.Char('Давтамжийн хамгаалал Бууралт', track_visibility='onchange')
    sec8 = fields.Char('Газардлагын хамгаалалт Хугацаатай', track_visibility='onchange')
    sec9 = fields.Char('Газардлагын хамгаалалт хугацаагүй', track_visibility='onchange')
    sec10 = fields.Char('Ялгаварт гүйдлийн хамгаалалт Хугацаатай', track_visibility='onchange')
    sec11 = fields.Char('Ялгаварт гүйдлийн хамгаалалт хугацаагүй', track_visibility='onchange')
    sec12 = fields.Char('Хийн хамгаалалт', track_visibility='onchange')
    sec13 = fields.Char('Температурын хамгаалалт', track_visibility='onchange')
    cause = fields.Char('Тавил өөрчилсөн шалтгаан', track_visibility='onchange')
    user = fields.Char('Тавил өөрчилсөн хүн', track_visibility='onchange')

    # line uurchilugdunguut main deer uurchilult
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False, attachments=None,
                     content_subtype='html', **kwargs):
        res = super(power_relay_line, self).message_post(body, subject, message_type,
                     subtype, parent_id, attachments,
                     content_subtype, **kwargs)
        if self.parent_id and res and res.model=='power.relay.line':
            cc = res.copy()
            cc.model = 'power.relay'
            cc.res_id = self.parent_id.id
            cc.record_name = 'power.relay,'+str(self.parent_id.id)
            for item in res.sudo().tracking_value_ids:
                tr = item.sudo().copy()
                tr.sudo().mail_message_id = cc.id
        return res
    

# class power_category(models.Model):
#     _inherit = 'power.category'

#     relay_ids = fields.One2many('power.relay', 'object_id', string='Реле хамгаалалтын тавил')