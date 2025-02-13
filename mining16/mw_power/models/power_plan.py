# -*- coding: utf-8 -*-

from odoo import api, models, fields, tools
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from calendar import monthrange

class power_power(models.Model):
    _name = 'power.plan'
    _inherit = ['mail.thread']
    _description = 'power plan'
    _order = 'start_date asc'

    def _default_type(self):
        return self.env.context.get('main_type', False)

    def _default_s_date(self):
        wk = self.env.context.get('main_type', False)
        if wk=='week':
            return datetime.today().strftime('%Y-%m-%D')
        elif wk == 'month':
            return datetime.today().strftime('%Y-%m-01')
        elif wk == 'year':
            return datetime.today().strftime('%Y-01-01')
        return datetime.today().strftime('%Y-%m-%D')
    
    def _default_e_date(self):
        wk = self.env.context.get('main_type', False)
        if wk=='week':
            return datetime.today().strftime('%Y-%m-%D')
        elif wk == 'month':
            current_date = datetime.now()
            current_year = current_date.year
            current_month = current_date.month
            days = monthrange(int(current_year),int(current_month))[1]
            return datetime.today().strftime('%Y-%m')+'-'+str(days)
        elif wk == 'year':
            return datetime.today().strftime('%Y-12-31')
        return datetime.today().strftime('%Y-%m-%D')

    name = fields.Char('Нэр', compute='_compute_name')
    start_date = fields.Date('Эхлэх Огноо', default=_default_s_date, required=True, track_visibility='onchange')
    end_date = fields.Date('Дуусах Огноо', default=_default_e_date, required=True, track_visibility='onchange')
    type = fields.Selection([('week','Долоо Хоног'), ('month','Сар'), ('year','Жил')], default=_default_type, string='Төрөл', required=True, track_visibility='onchange')
    attachment_ids = fields.Many2many('ir.attachment', string='Төлөвлөгөө Файл', required=True)
    attachment_actual_ids = fields.Many2many('ir.attachment', 'power_plan_actual_attachment_rel', 'plan_id', 'attach_id',string='Гүйцэтгэл Файл')
    lines = fields.One2many('power.plan.line','parent_id',string='Мөр')
    @api.depends('start_date','end_date')
    def _compute_name(self):
        for item in self:
            s_date = item.start_date or ''
            e_date = item.end_date or ''
            cname = '%s'%(dict(self._fields['type'].selection).get(item.type))
            item.name = s_date+' '+e_date+' '+cname

class power_power_line(models.Model):
    _name = 'power.plan.line'
    _description = 'power plan line'
    _order = 'date asc'

    parent_id = fields.Many2one('power.plan','Parent')
    parent_id = fields.Char('Parent')
    date = fields.Date('Хийгдэх Огноо')
    implement_id = fields.Many2one('power.implements','Тоноглол')
    category_id = fields.Many2one('power.category','Хөрөнгө')
    desc = fields.Text('Хийгдэх ажил')
    