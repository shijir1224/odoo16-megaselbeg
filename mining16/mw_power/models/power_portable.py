# -*- coding: utf-8 -*-

from odoo import api, models, fields
from datetime import datetime, timedelta

class power_portable(models.Model):
    _name = 'power.portable'
    _description = 'power portable'
    
    notes_id = fields.Many2one('power.notes', 'Ээлжийн Бүртгэлд', ondelete='cascade')
    power_technic_id = fields.Many2one('power.selection', domain="[('type','=','technic')]",  string='Цахилгаан экскаватор')
    start_date = fields.Datetime('Эхэлсэн он сар өдөр', default=fields.Datetime.now)
    end_date = fields.Datetime('Дууссан он сар өдөр', default=fields.Datetime.now)
    start_time = fields.Float('Зогссон цаг /цаг/')
    end_time = fields.Float('Ажилласан цаг /цаг/')
    diff_time = fields.Float('Зарцуулсан хугацаа', compute='_compute_diff_time_work', store=True)
    naryad_number = fields.Char('Нарядын №')
    description = fields.Text('Тайлбар')
    rounting_master_id = fields.Many2one('res.users', string='Шугамын мастер')
    cause_id = fields.Many2one('power.portable.cause', string='Зогсолтын шалтгаан')
    product_expense_ids = fields.One2many('power.product', 'portable_id',string='Ашигласан Бараа Материал')
    shift = fields.Selection(related='notes_id.shift', store=True, readonly=True)
    date = fields.Date(related='notes_id.date', store=True, readonly=True)

    @api.depends('start_date','end_date','shift')
    def _compute_diff_time_work(self):
        # for item in self:
        #     if item.start_date and item.end_date:
                # end_date = datetime.strptime(item.end_date, '%Y-%m-%d %H:%M:%S')
                # start_date = datetime.strptime(item.start_date, '%Y-%m-%d %H:%M:%S')
                # seconds = (end_date-start_date).seconds
                # hours =  float(seconds / 3600)
                # mm = seconds-hours*3600
                # minut = mm/3600
                # item.diff_time = hours+minut
                # item.diff_time = item.end_time-item.start_time
        for item in self:
            if item.shift=='night' and item.end_time<item.start_time:
                item.diff_time = item.end_time+24-item.start_time
            else:
                item.diff_time = item.end_time-item.start_time


class power_portable_cause(models.Model):
    _name = 'power.portable.cause'
    _description = 'power portable cause'

    name = fields.Char('Шалтгаан', required=True)
