# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)
from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
HOURS_PER_DAY = 8


class HrTimeCompute(models.Model):
    _name = "hr.time.compute"
    _description = "Hr Time Compute"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_from"
    
    @api.depends('time_to', 'time_from')
    def _compute_amount(self):
        for obj in self:
            if obj.time_to > obj.time_from:
                if obj.time_to > 13 and obj.time_from <= 13:
                    obj.number_of_hour = obj.time_to-obj.time_from - obj.lunch_time
                else:
                    obj.number_of_hour = obj.time_to-obj.time_from
            else:
                obj.number_of_hour = 24-obj.time_from+obj.time_to - obj.lunch_time

    date_from = fields.Datetime(
        'Огноо', copy=False, required=False, tracking=True, compute=False, default=False)
    in_out_time = fields.Datetime(
        'Орсон, Гарсан цаг', copy=False, required=False, tracking=True, compute=False, default=False)
    time_from = fields.Float('Эхлэх цаг', tracking=True)
    time_to = fields.Float('Дуусах цаг', tracking=True)
    lunch_time = fields.Float('Цайны цаг', default='1', tracking=True)
    number_of_hour = fields.Float(
        'Үргэлжлэх хугацаа', store=True, compute='_compute_amount', tracking=True)
    hr_parent_id = fields.Many2one(
        'hr.leave.mw', 'Parent', ondelete='cascade', tracking=True)
    employee_id = fields.Many2one('hr.employee', 'Ажилтан', tracking=True)
    shift_plan_id = fields.Many2one(
        'hr.shift.time', 'Хүсэлтийн төрөл', tracking=True,domain="[('is_request','=',True)]")
    description = fields.Char(string='Тайлбар')

    @api.onchange('hr_parent_id')
    def _onchange_parent_id(self):
        self.employee_id = self.hr_parent_id.employee_id.id


class HolidaysRequestConfirm(models.TransientModel):
    _name = "hr.leave.confirm"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'hr leave confirm'

    def action_to_confirm_all_mw(self):
        context = self._context
        if context['active_model'] == 'hr.leave.mw':
            for cd_id in (context['active_ids']):
                leave = self.env['hr.leave.mw'].search(
                    [('id', '=', cd_id)], limit=1)
                if leave:
                    leave.action_next_stage()


class HrLeaveRequestMw(models.Model):
    _name = "hr.leave.mw"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Hr Leave Request Mw'

    def name_get(self):
        res = []
        for item in self:
            name = item.shift_plan_id.name +' ' +item.employee_id.last_name[:1]+'.' +item.employee_id.name
            res.append((item.id, name))
        return res

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    def unlink(self):
        for bl in self:
            if bl.state_type != 'draft':
                raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
        return super(HrLeaveRequestMw, self).unlink()

    return_description = fields.Char('Буцаах тайлбар', tracking=True)
    time_from = fields.Float('Эхлэх цаг', tracking=True)
    time_to = fields.Float('Дуусах цаг', tracking=True)
    number_of_hour = fields.Float(
        'Цаг', copy=False, readonly=True, compute='_compute_number_of_hour')
    days = fields.Float('Нийт хоног', readonly=True, compute="_compute_day",
                        store=True, default=0, digits=(2, 1), tracking=True)
    total_hour = fields.Float('Нийт цаг', copy=False, readonly=True,
                              compute='_compute_day', store=True, tracking=True)
    lunch_hour = fields.Float('Цайны цаг', default='1',
                              readonly='1', tracking=True)
    date_from = fields.Datetime(
        'Эхлэх', copy=False, required=False, tracking=True, compute=False, default=False)
    date_to = fields.Datetime(
        'Дуусах', copy=False, required=False, tracking=True, compute=False, default=False)
    # create_date = fields.Date('Бүртгэсэн огноо', readonly=True,
    #                           default=fields.Date.context_today, tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', u'Ажилтан', default=_default_employee, tracking=True)
    company_id = fields.Many2one(
        'res.company', 'Компани', related='employee_id.company_id', store=True,readonly=True)
    work_location_id = fields.Many2one(
        'hr.work.location', 'Ажлын байршил', related='employee_id.work_location_id', store=True)
    department_id = fields.Many2one('hr.department', 'Хэлтэс')
    shift_plan_id = fields.Many2one('hr.shift.time', 'Хүсэлтийн төрөл',required=True, tracking=True)
    hr_time_ids = fields.One2many('hr.time.compute', 'hr_parent_id', 'Өдрүүд')
    is_work = fields.Selection([('day',u'Өдөр'),('night',u'Шөнө'),('vacation',u'Ээлжийн амралт'),('sick',u'Өвчтэй'),('leave',u'Чөлөөтэй'),('pay_leave',u'Цалинтай чөлөө'),('overtime_hour',u'Илүү цаг'),('outage',u'Сул зогсолт'),('sickness',u'Тасалсан'),('none',u'Амралт'),('in','In'),('out','Out'),('parental',u'Аавын 10 хоног'),('bereavement',u'Ажил явдал'),('business_trip',u'Томилолт'),('training',u'Сургалт'),('out_work',u'Гадуур ажилласан'),('online_work',u'Зайнаас ажилласан'),('accumlated',u'Нөхөж амрах'),('attendance',u'Орсон ирц нөхөн бүртгүүлэх'),('attendance_out',u'Гарсан ирц нөхөн бүртгүүлэх'),('resigned',u'Ажлаас гарсан'),('public_holiday',u'Нийтээр амрах өдөр'),('over_day',u'Сунаж ажилласан өдөр'),('over_night',u'Сунаж ажилласан шөнө')], u'Хуваарь', related='shift_plan_id.is_work', store=True)
    is_many = fields.Boolean('Мөр үүсгэх эсэх',default=False)
    remain_days = fields.Float(
        'Үлдсэн амрах хоног', compute='_compute_vac_days', store=True)
    vac_days = fields.Float('Амрах хоног')
    description = fields.Char(string='Тайлбар')
    employee_ids = fields.Many2many('hr.employee',string='Ажилчид')
    warning = fields.Text(string=u'Санамж', readonly=True,default="*Олон ажилтан сонгож хүсэлт илгээх эсвэл 1 ажилтан олон төрлийн хүсэлт илгээх тохиолдолд чеклэнэ үү.")
    is_work_ids = fields.Many2many('hr.shift.time','is work', compute='get_work_domain')

    @api.depends('company_id')
    def get_work_domain(self):
        for item in self:
            if item.company_id:
                item.is_work_ids = item.env['hr.shift.time'].search([('company_id', '=', item.company_id.id),('is_request', '=', True)]).ids
            else:
                item.is_work_ids = False
                
    @api.onchange('employee_id')
    def onchange_employee_id(self):
        for item in self:
            if item.employee_id:
                total_vac_days=sum(self.env['hr.leave.mw'].search([('employee_id','=',item.employee_id.id),('flow_line_id.state_type','=','done')]).mapped('days'))
                item.vac_days = int(item.employee_id.days_of_annualleave) - total_vac_days
                item.department_id = item.employee_id.department_id.id

    @api.depends('days', 'vac_days')
    def _compute_vac_days(self):
        for item in self:
            day = item.vac_days - item.days
            if day > 0:
                item.remain_days = day
            else:
                item.remain_days = 0

    @api.onchange('date_from')
    def _onchange_date_to(self):
        self.date_to = self.date_from

    def line_create(self):
        time_data_pool =  self.env['hr.time.compute']
        if self.hr_time_ids:
            self.hr_time_ids.unlink()
        from_dt = datetime.strptime(
            str(self.date_from + timedelta(hours=8)), DATETIME_FORMAT).date()
        to_dt = datetime.strptime(
            str(self.date_to + timedelta(hours=8)), DATETIME_FORMAT).date()
        step = timedelta(days=1)
        # for obj in self:
        if not self.employee_ids:
            while from_dt <= to_dt:
                time_line_conf = time_data_pool.create({
                        'date_from':from_dt,
                        'hr_parent_id':self.id,
                        'employee_id':self.employee_id.id,
                        'shift_plan_id':self.shift_plan_id.id,
                        'time_to':self.time_to,
                        'time_from':self.time_from,
                    })
                from_dt += step
        else:
            while from_dt <= to_dt:
                for emp in self.employee_ids:
                    time_line_conf = time_data_pool.create({
                        'date_from':from_dt,
                        'hr_parent_id':self.id,
                        'employee_id':emp.id,
                        'shift_plan_id':self.shift_plan_id.id,
                        'time_to':self.time_to,
                        'time_from':self.time_from,
                        })
                from_dt += step

    @api.depends('time_from', 'time_to')
    def _compute_number_of_hour(self):
        for obj in self:
            if obj.time_to > obj.time_from:
                if obj.time_to > 13 and obj.time_from <= 13:
                    obj.number_of_hour = obj.time_to-obj.time_from - obj.lunch_hour
                else:
                    obj.number_of_hour = obj.time_to-obj.time_from
            else:
                obj.number_of_hour = 24-obj.time_from+obj.time_to - obj.lunch_hour
                # хүсэлт дээрээ цайны цаг хасч харуулах

    def daterange(self, date_from, date_to):
        for n in range(int((date_to - date_from).days)+1):
            yield date_from + timedelta(n)

    @api.depends('date_from', 'date_to', 'number_of_hour')
    def _compute_day(self):
        st_d = 0
        en_d = 0
        for item in self:
            if item.date_from and item.date_to:
                st_d = datetime.strptime(
                    str(item.date_from + timedelta(hours=8)), DATETIME_FORMAT).date()
                en_d = datetime.strptime(
                    str(item.date_to +timedelta(hours=8)), DATETIME_FORMAT).date()
                day_too = 0
                # Оффис Location number = 1 байх ёстой
                # Уурхай Location number = 2  уурхай амралтын өдөр хамааралгүй хүсэлт тооцох учир
                if item.work_location_id.location_number == '1':
                    if item.is_work=='business_trip' or item.is_work=='training':
                        for single_date in item.daterange(st_d, en_d):
                            day_too += 1
                            _logger.info('Testing Holiday location===2: %s  %s  %s' % (
                            day_too, st_d, en_d))
                    else:
                        for single_date in item.daterange(st_d, en_d):
                            day_too += 1 if single_date.weekday() < 5 else 0
                        _logger.info('Testing Holiday location===1: %s  %s  %s' % (
                            day_too, st_d, en_d))
                else:
                    # if item.is_work=='parental' or item.is_work=='vacation':
                    #     for single_date in item.daterange(st_d, en_d):
                    #         day_too += 1 if single_date.weekday() < 5 else 0
                    #     _logger.info('Testing Holiday location===2: %s  %s  %s' % (
                    #         day_too, st_d, en_d))
                    # else:
                    for single_date in item.daterange(st_d, en_d):
                        day_too += 1
                    _logger.info('Testing Holiday location===2: %s  %s  %s' % (
                        day_too, st_d, en_d))
                item.days = day_too
                item.total_hour = item.days * item.number_of_hour
