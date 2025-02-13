# -*- coding: utf-8 -*-
import time
import datetime
from datetime import  datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
month=[('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
        ('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
        ('90','10 сар'), ('91','11 сар'), ('92','12 сар')]


class HrTimetableLine(models.Model):
    _name = "hr.timetable.line"
    _description = "Timetable Line"
    _inherit = ['mail.thread']
    _order = 'sequence,job_id'

    def line_update(self):
        for l in self.line_ids:
            if l.is_update == True:
                l.update({'shift_attribute_id':self.shift_id.id})

    def all_cancel(self):
        for l in self.line_ids:
            l.update({'is_update':False})

    def all_yes(self):
        for l in self.line_ids:
            l.update({'is_update':True})

    is_update = fields.Boolean('Update')
    shift_id = fields.Many2one('hr.shift.time','Хуваарь')
    shift_roster_id = fields.Many2one('hr.shift','Ростер')
    parent_id=fields.Many2one('hr.timetable', 'Parent',ondelete='cascade')
    year= fields.Char(string='Жил', size=8, readonly='1')
    month=fields.Selection(month, 'Сар', readonly='1')
    day_to_work_month=fields.Float('Ажиллавал зохих өдөр', default='21')
    hour_to_work_month=fields.Float('Ажиллавал зохих цаг', default='168')
    sequence = fields.Integer('Дугаар')
    department_id= fields.Many2one('hr.department', "Хэлтэс", readonly='1')
    job_id= fields.Many2one('hr.job','Албан тушаал', readonly='1')
    employee_id= fields.Many2one('hr.employee', 'Ажилтан', readonly='1')
    identification_id= fields.Char('Ажилтны код', readonly='1',related='employee_id.identification_id')
    date_from = fields.Date('Эхлэх огноо', related='parent_id.date_from',store=True)
    date_to = fields.Date('Дуусах огноо', related='parent_id.date_to' ,store=True)
    line_ids= fields.One2many('hr.timetable.line.line', 'parent_id', 'Employee hour balance')
    state= fields.Selection([('draft','Ноорог'),
                ('send',u'Илгээсэн'),
                ('confirm',u'ХН хянасан'),
                ('done',u'НЯБО хүлээж авсан'),
                ('refuse',u'Цуцлагдсан')], 'Status',readonly=True, tracking=True, copy=False,related='parent_id.state')
    description = fields.Text('Тайлбар')
    
    def view_form(self):
        self.ensure_one()
        action = {
            'name':'Төлөвлөгөөний мөр',
            'type':'ir.actions.act_window',
            'view_mode':'form',
            'res_model':'hr.timetable.line',
            'target':'current',
        }
        view = self.env.ref('mw_timetable.view_hr_timetable_line_form')
        view_id = view and view.id or False
        action['view_id'] = view_id
        action['res_id'] = self.id
        return action
class HrTimetableLineLine(models.Model):
    _name = "hr.timetable.line.line"
    _description = "Timetable Line Line"
    _inherit = ['mail.thread']
    
    def write(self,vals):
        res = super(HrTimetableLineLine, self).write(vals)
        for obj in self:
            if obj.worked_salary_hour:
                message = """
                    <!DOCTYPE html>
                    <html>
                    <style>
                        li::marker {
                            font-weight: bold;
                            color:black;
                        }
                    </style>
                    <body>
                        <ul>
                            <li>
                                <span>%s </span> : <span>%s </span>
                            </li>
                        </ul>
                    </body>
                    </html>
                """ %(obj.employee_id.name,obj.worked_salary_hour)
                obj.parent_id.parent_id.message_post(body=message, subject='')
        return res
    
    def get_line_vals(self, vals):
        return vals

    def name_get(self):
        res = []
        for line in self:
            name = line.name or ''
            res.append((line.id, name))
        return res

    green = fields.Boolean('green')
    number = fields.Integer(u'Дугаар', readonly=True)
    name = fields.Char(compute='_compute_name', string = u'Нэр',store=False)
    color = fields.Integer('Color',compute='_compute_name',store=True)
    is_update = fields.Boolean('Update')
    date = fields.Date('Огноо',index=True)
    shift_plan_id = fields.Many2one('hr.shift.time','Үндсэн хуваарь')
    shift_attribute_id = fields.Many2one('hr.shift.time','Тодотгосон хуваарь')
    department_id= fields.Many2one('hr.department', "Хэлтэс")
    job_id = fields.Many2one('hr.job','Албан тушаал')
    employee_id = fields.Many2one('hr.employee', 'Ажилтан')
    parent_id=fields.Many2one('hr.timetable.line', 'Balance',ondelete='cascade',index=True)
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил', tracking=True)
    year= fields.Char(string='Жил', size=8)
    month=fields.Selection(month, 'Сар')
    state= fields.Selection([('draft','Ноорог'),
                ('send',u'Илгээсэн'),
                ('confirm',u'ХН хянасан'),
                ('done',u'НЯБО хүлээж авсан'),
                ('refuse',u'Цуцлагдсан')], 'Status',readonly=True, default = 'draft', tracking=True, copy=False)
# Цагууд
    is_public_holiday = fields.Boolean('Нийтээр амрах өдөр', default=False)
    hour_to_work= fields.Float('Ажиллавал зохих цаг',related='shift_plan_id.compute_sum_all_time',store=True)
    worked_hour = fields.Float(compute='_compute_worked_hour',store=True, string = u'Ажилласан цаг', digits=(3, 2))
    worked_salary_hour = fields.Float(compute='_compute_worked_salary_hour',store=True, string = u'Цалин тооцох цаг', digits=(3, 2))
    night_hour = fields.Float(compute='_compute_worked_hour',store=True, string =u'Шөнө ажилласан цаг', digits=(3, 2))
    tourist_hour = fields.Float(compute='_compute_worked_hour',store=True, string = u'Аялалын цаг', digits=(3, 2))
    sickness_hour = fields.Float(compute='_compute_worked_hour',store=True, string =u'Тасалсан цаг', digits=(3, 2))
    delayed_min = fields.Float(compute='_compute_worked_hour',store=True, string = u'Хоцорсон минут', digits=(3, 2))
    early_min = fields.Float(compute='_compute_worked_hour', store=True, string=u'Эрт гарсан минут', digits=(3, 2))
    long_min = fields.Float(compute='_compute_long_min', store=True, string=u'Илүү ажилласан минут', digits=(3, 2))
    lunch_hour = fields.Float('Цайны цаг', digits=(3, 2))
    out_working_hour = fields.Float('Гадуур ажил', digits=(3, 2))
    accumlated_hour = fields.Float('Нөхөн амарсан', digits=(3, 2))
    training_hour = fields.Float('Сургалт', digits=(3, 2))
    online_working_hour = fields.Float('Зайнаас ажилласан', digits=(3, 2))
    free_wage_hour = fields.Float(u'Цалинтай чөлөө', digits=(3, 2))
    parental_hour = fields.Float(u'Аавын 10 хоног', digits=(3, 2))
    overtime_hour = fields.Float(u'Илүү цаг', digits=(3, 2))
    req_overtime_hour = fields.Float(u'Хүсэлтийн илүү цаг', digits=(3, 2))
    holiday_worked_hour = fields.Float(u'Баярын өдөр ажилласан цаг', digits=(3, 2))
    vacation_day = fields.Float('ЭА цаг')
    busines_trip_hour = fields.Float(u'Томилолттой цаг', digits=(3, 2))
    sick_hour = fields.Float(u'Өвчтэй цаг', digits=(3, 2))
    free_hour = fields.Float(u'Цалингүй чөлөө', digits=(3, 2))
    # free_hour = fields.Float(u'Цалингүй чөлөө', digits=(3, 2))
    outage_hour = fields.Float('Сул зогсолт цаг', digits=(3, 2))
    over_work_night = fields.Float(string = u'Сунаж ажилласан цаг/шөнө/', digits=(3, 2))
    over_work_day = fields.Float(string = u'Сунаж ажилласан цаг/өдөр/', digits=(3, 2))
    sign_in = fields.Datetime("Орсон/Тооцоолох/")
    sign_out = fields.Datetime("Гарсан/Тооцоолох/")
    sign_in_emp = fields.Datetime("Орсон")
    sign_out_emp = fields.Datetime("Гарсан")
    is_not_tourist= fields.Boolean('Зам хоног тооцохгүй', default=False)
    is_request = fields.Selection([('yes','Yes'),('no','No')],'Хүсэлт',default='no')
    is_work_schedule = fields.Selection([('day',u'Өдөр'),('night',u'Шөнө'),('vacation',u'Ээлжийн амралт'),('sick',u'Өвчтэй'),('leave',u'Чөлөөтэй'),('pay_leave',u'Цалинтай чөлөө'),('overtime_hour',u'Илүү цаг'),('outage',u'Сул зогсолт'),('sickness',u'Тасалсан'),('none',u'Амралт'),('in','In'),('out','Out'),('parental',u'Аавын 10 хоног'),('bereavement',u'Ажил явдал'),('business_trip',u'Томилолт'),('training',u'Сургалт'),('out_work',u'Гадуур ажилласан'),('online_work',u'Зайнаас ажилласан'),('accumlated',u'Нөхөж амрах'),('attendance',u'Орсон ирц нөхөн бүртгүүлэх'),('attendance_out',u'Гарсан ирц нөхөн бүртгүүлэх'),('resigned',u'Ажлаас гарсан'),('public_holiday',u'Нийтээр амрах өдөр')], u'Хуваарь', related='shift_attribute_id.is_work',store=True)    


    # float to datetime
    start_time = fields.Datetime("Эхлэх цаг",compute = '_compute_limit_time')
    end_time = fields.Datetime("Дуусах цаг",compute = '_compute_limit_time')

    lunch_start_time = fields.Datetime("Цайны эхлэх цаг",compute = '_compute_limit_time')
    lunch_end_time = fields.Datetime("Цайны дуусах цаг",compute = '_compute_limit_time')

    in_limit_start = fields.Datetime("Орох лимит эхлэх",compute = '_compute_limit_time')
    in_limit_end = fields.Datetime("Орох лимит дуусах",compute = '_compute_limit_time')
    out_limit_start = fields.Datetime("Гарах лимит эхлэх",compute = '_compute_limit_time')
    out_limit_end = fields.Datetime("Гарах лимит дуусах",compute = '_compute_limit_time')

    late_s = fields.Datetime("Хоцролт тооцох",compute = '_compute_limit_time')
    out_s = fields.Datetime("Гарсан тооцох",compute = '_compute_limit_time')

    leave_request_start = fields.Datetime("Хүсэлтийн эхлэх огноо")
    leave_request_end = fields.Datetime("Хүсэлтийн дуусах огноо")

    def hour_minute_replace(self,float_hour,date):
        if float_hour and date:
            datee = str(date) + ' ' + '00' +':'+'00'+':'+'00'    
            date_s = datetime.strptime(str(datee), DATETIME_FORMAT)    
            hour = float_hour/1
            minute = float_hour%1*60
            date_time = date_s.replace(hour=int(hour), minute=int(minute), second=0,microsecond=0) - timedelta(hours=8)
            return date_time

    @api.depends('shift_plan_id')
    def _compute_limit_time(self):
        for obj in self:
            if obj.date:
                if obj.shift_plan_id.in_s_time:
                    obj.in_limit_start = obj.hour_minute_replace(obj.shift_plan_id.in_s_time,obj.date)
                else:
                    obj.in_limit_start =None

                if obj.shift_plan_id.in_e_time:
                    obj.in_limit_end = obj.hour_minute_replace(obj.shift_plan_id.in_e_time,obj.date)
                else:
                    obj.in_limit_end =None
                    
                if obj.shift_plan_id.out_s_time:
                    obj.out_limit_start = obj.hour_minute_replace(obj.shift_plan_id.out_s_time,obj.date)
                else:
                    obj.out_limit_start =None

                if obj.shift_plan_id.out_e_time:
                    if obj.shift_plan_id.out_e_time > 0:
                        obj.out_limit_end = obj.hour_minute_replace(obj.shift_plan_id.out_e_time,obj.date)
                    else:
                        obj.out_limit_end = obj.hour_minute_replace(obj.shift_plan_id.out_e_time,obj.date)
                else:
                    obj.out_limit_end =None

                if obj.shift_plan_id.start_time:
                    obj.start_time = obj.hour_minute_replace(obj.shift_plan_id.start_time,obj.date)
                else:
                    obj.start_time =None

                if obj.shift_plan_id.end_time:
                    obj.end_time = obj.hour_minute_replace(obj.shift_plan_id.end_time,obj.date)
                else:
                    obj.end_time =None

                if obj.shift_plan_id.lunch_start_time:
                    obj.lunch_start_time = obj.hour_minute_replace(obj.shift_plan_id.lunch_start_time,obj.date)
                else:
                    obj.lunch_start_time =None

                if obj.shift_plan_id.lunch_end_time:
                    obj.lunch_end_time = obj.hour_minute_replace(obj.shift_plan_id.lunch_end_time,obj.date)
                else:
                    obj.lunch_end_time =None

                if obj.shift_plan_id.late_s_time:
                    obj.late_s = obj.hour_minute_replace(obj.shift_plan_id.late_s_time,obj.date)
                else:
                    obj.late_s =None

                if obj.shift_plan_id.out_e_time:
                    obj.out_s = obj.hour_minute_replace(obj.shift_plan_id.out_e_time,obj.date)
                else:
                    obj.out_s =None
        
# Onchange
    @api.onchange('shift_plan_id')
    def onchange_shift_plan_id(self):
        self.is_work_schedule = self.shift_plan_id.is_work
        self.hour_to_work = self.shift_plan_id.compute_sum_all_time

    @api.onchange('shift_attribute_id')
    def onchange_shift_attribute_id(self):
        self.is_work_schedule = self.shift_attribute_id.is_work
        self.hour_to_work = self.shift_attribute_id.compute_sum_all_time
        self.night_hour = self.shift_attribute_id.compute_sum_ov_time
        self.worked_hour = self.shift_attribute_id.compute_sum_time 
        # self.start_time = self.shift_attribute_id.start_time
        # self.end_time = self.shift_attribute_id.end_time

############### Functions ##################
    # Цагийн төлөвлөгөөний өнгө болон тэмдэглэгээ авах функц
    @api.depends('is_work_schedule','shift_attribute_id')
    def _compute_name(self):
        for obj in self:
            if obj.shift_attribute_id.flag:
                if obj.is_work_schedule in ('day','night') or obj.is_work_schedule=='attendance':
                    # if obj.worked_hour:
                    #     obj.name = obj.shift_attribute_id.flag + str(obj.worked_hour+obj.night_hour)[:4]
                    #     obj.color = obj.shift_attribute_id.color
                    # elif obj.night_hour:
                    #     obj.name = obj.shift_attribute_id.flag + str(obj.night_hour)[:4]
                    #     obj.color = obj.shift_attribute_id.color
                    # else:
                    # if obj.worked_salary_hour:
                        obj.name = obj.shift_attribute_id.flag+str(obj.worked_salary_hour)[:4]
                        obj.color = obj.shift_attribute_id.color
                elif obj.is_work_schedule == 'none':
                    obj.name = obj.shift_attribute_id.flag
                    obj.color = obj.shift_attribute_id.color
                elif obj.is_work_schedule == 'overtime_hour':
                    obj.name = obj.shift_attribute_id.flag +str(obj.worked_salary_hour + obj.overtime_hour)[:4]
                    obj.color = obj.shift_attribute_id.color
                else:
                    obj.name = obj.shift_attribute_id.flag+str(obj.worked_salary_hour)[:4]
                    obj.color = obj.shift_attribute_id.color
            else:
                obj.name = str(obj.worked_salary_hour)[:4]
                obj.color = obj.shift_attribute_id.color

#1 Ажилласан цаг тооцох  функц
    @api.depends('sign_in', 'sign_out','is_work_schedule','shift_attribute_id', 'free_hour','hour_to_work','free_wage_hour', 'busines_trip_hour', 'sick_hour',)
    def _compute_worked_hour(self):
        for obj in self:
            full_hour_emp = self.env['hr.employee'].search([('full_worked_hour', '=', True),('employee_type', '!=', 'resigned'),('id','=',obj.employee_id.id)])
            # Төхөөрөмжийн ирцээс татах
            if obj.parent_id.parent_id.is_attendance==True or obj.parent_id.parent_id.is_mining!=True:
                if full_hour_emp:
                    for full_emp in full_hour_emp:
                        self.worked_hour_schedule(obj)
                else:
                    self.worked_hour_attendance(obj)
            # хуваарьгүй дан ирцээс тооцох
            # elif obj.parent_id.parent_id.only_attendance==True:
            #     self.worked_hour_only_attendance(obj)
            # Ээлжээс ажилласан цаг тооцох
            else:
                self.worked_hour_schedule(obj)

    @api.depends('sign_out_emp','sign_out','shift_plan_id','sign_in_emp')
    def _compute_long_min(self):
        for obj in self:
            if obj.shift_plan_id.is_work in ('day','night') and obj.shift_plan_id.is_limit: #уян хатан бол
                if obj.sign_out_emp and obj.sign_in_emp:
                    uyan_oroh_duusah=obj.shift_plan_id.in_e_time
                    uyan_oroh_ehleh=obj.shift_plan_id.in_s_time
                    uyan_garah_duusah=obj.shift_plan_id.out_e_time
                    uyan_garah_ehleh=obj.shift_plan_id.out_s_time
                    ajillah_yostoi=uyan_garah_ehleh-uyan_oroh_ehleh
                    time_delta = obj.sign_out_emp-obj.sign_in_emp
                    duration_in_hour = time_delta.total_seconds()
                    hour = divmod(duration_in_hour, 60)[0]
                    if hour>ajillah_yostoi:
                        garah_yostoi=obj.sign_in_emp+timedelta(hours=ajillah_yostoi)
                        if obj.sign_out_emp >garah_yostoi:
                            long_min_delta = obj.sign_out_emp - garah_yostoi
                            obj.long_min =self._delayed_min(long_min_delta)
                        else:
                            obj.long_min =0
                    else:
                        obj.long_min =0
                else:
                    obj.long_min =0
            else:
                if obj.sign_out_emp and obj.sign_out:
                    sign_out_emp = datetime.strptime(str(obj.sign_out_emp),DATETIME_FORMAT)
                    sign_out = datetime.strptime(str(obj.sign_out), DATETIME_FORMAT)
                    minutes_emp = sign_out_emp.hour * 60 + sign_out_emp.minute
                    min_emp = sign_out.hour * 60 + sign_out.minute
                    if minutes_emp >min_emp:
                        obj.long_min = minutes_emp  - min_emp
                    else:
                        obj.long_min =0
                else:
                    obj.long_min = 0
    
    def _delayed_min(self,time_delta):
        delayed_min=0
        if time_delta:
            duration_in_s = time_delta.total_seconds()
            minuts = divmod(duration_in_s, 60)[0] + divmod(duration_in_s, 60)[1]/60    
            delayed_min = minuts
        return delayed_min
    
    def worked_hour_only_attendance(self,obj):
        delayed_min = 0
        early_min = 0
        worked_hour = 0
        hour = 0
        lunch_hour=0
        hour,delayed_min,lunch_hour,early_min = self.set_delayed_hour(obj,obj.sign_in_emp,obj.sign_out_emp)
        obj.delayed_min = delayed_min
        obj.early_min = early_min
        worked_hour = hour/60-lunch_hour
        if worked_hour > 0 and obj.is_public_holiday==False:
            if obj.hour_to_work < worked_hour:
                obj.worked_hour = obj.hour_to_work
            else:
                obj.worked_hour = worked_hour
        else:
            obj.worked_hour = 0
        if obj.is_public_holiday==True and worked_hour>0 and obj.work_location_id.location_number!='3':
            if obj.hour_to_work < worked_hour:
                obj.holiday_worked_hour = obj.hour_to_work
            else:
                obj.holiday_worked_hour = worked_hour
        elif obj.is_public_holiday==True and obj.work_location_id.location_number=='3':
            obj.holiday_worked_hour = obj.hour_to_work

#1.1 Төхөөрөмжийн ирцээс ажилласан цаг хоцролт, эрт гарсан  тооцно
    def worked_hour_attendance(self,obj):
        delayed_min = 0
        early_min = 0
        worked_hour = 0
        hour = 0
        lunch_hour=0
        is_work =''
        type_vac = ''
        if is_work != 'none' and is_work != 'public_holiday':
            # Ажилласан цаг энд орж ирнэ
            hour,delayed_min,lunch_hour,early_min = self.set_delayed_hour(obj,obj.sign_in,obj.sign_out)
            # Ээлжийн амралттай болон бүх нийтийн амралтын өдөр ажилласан бол хоцролт тооцохгүй
            if type_vac == 'vacation' or obj.is_public_holiday==True:
                obj.delayed_min = 0
                obj.early_min = 0
            else:
                obj.delayed_min = delayed_min
                obj.early_min = early_min
            # if hour/60>4:
            #     worked_hour = hour/60 - lunch_hour
            # else:
            worked_hour = hour/60-lunch_hour
            if worked_hour > 0 and obj.is_work_schedule !='night' and obj.is_public_holiday==False:
                if obj.hour_to_work < worked_hour:
                    obj.worked_hour = obj.hour_to_work
                else:
                    obj.worked_hour = worked_hour
            else:
                obj.worked_hour = 0 
            if obj.is_work_schedule =='night':
                if worked_hour>4:
                    obj.night_hour = obj.shift_attribute_id.compute_sum_ov_time
                    obj.worked_hour = obj.shift_attribute_id.compute_sum_time
                    obj.sickness_hour = 0
            elif obj.shift_plan_id.is_work =='night':
                if worked_hour>4:
                    if obj.is_work_schedule =='overtime_hour':
                        obj.night_hour = obj.shift_plan_id.compute_sum_ov_time
                        obj.worked_hour = obj.shift_plan_id.compute_sum_time
                    elif obj.is_work_schedule =='night_over':
                        obj.night_hour = obj.shift_plan_id.compute_sum_ov_time
                        obj.worked_hour = obj.shift_plan_id.compute_sum_time
            elif obj.shift_plan_id.is_work =='none':
                obj.worked_hour = 0
                obj.night_hour = 0
            elif obj.shift_attribute_id.is_work == 'out_attend':
                obj.night_hour = 0
                obj.tourist_hour = 6
            elif obj.shift_attribute_id.is_work in ('work_night','work_day'):
                obj.worked_hour = 0
            else:
                obj.night_hour =0
            if obj.is_public_holiday==True and worked_hour>0 and obj.work_location_id.location_number!='3' and obj.shift_plan_id.is_work !='none':
                if obj.hour_to_work < worked_hour:
                    obj.holiday_worked_hour = obj.hour_to_work
                else:
                    obj.holiday_worked_hour = worked_hour
            elif obj.is_public_holiday==True and obj.work_location_id.location_number=='3':
                obj.holiday_worked_hour = obj.hour_to_work

    # Хоцролт тооцох цаг
    def late_hour(self,obj,late_s,s_time):
        start_time=None
        if obj.parent_id.parent_id.is_late == True:
            if late_s:
                start_time = late_s
        else:
            if s_time:
                start_time = s_time
        return start_time

    def delayed_delta_compute(self,s_in,sign_out):
        # self.late_s хоцролт тооцох цаг
        # s_in орсон цаг
        # s_work # ажил эхлэх ёстой цаг
        
        s_start_time=self.start_time
        s_late_time=self.late_s
        delayed_delta=0
        if  self.shift_plan_id and self.shift_plan_id.is_limit: #уян хатан бол
            uyan_oroh_duusah=self.shift_plan_id.in_e_time
            uyan_oroh_ehleh=self.shift_plan_id.in_s_time
    
            uyan_garah_duusah=self.shift_plan_id.out_e_time
            uyan_garah_ehleh=self.shift_plan_id.out_s_time
            if uyan_oroh_duusah and uyan_oroh_ehleh and \
                uyan_garah_duusah and uyan_garah_ehleh:
                s_start_time = self.hour_minute_replace(uyan_oroh_duusah,self.date) #10 цаг
                s_work = datetime.strptime(str(s_start_time), DATETIME_FORMAT)+timedelta(hours=8) 
                if s_work<s_in:
                    delayed_delta = s_in-s_work
            else:
                raise UserError(('Ээлж дээр Лимит тохируулах эсэх? идэвхитэй байгаа боловч цагуудаа бүрэн бөглөөгүй байна {}'.format(self.shift_plan_id.name)))
                
        else:
            # s_start_time = obj.hour_minute_replace(self.shift_plan_id.start_time,self.date)
            # s_start_time = self.hour_minute_replace(self.shift_plan_id.in_e_time,self.date)
            start_time = self.late_hour(self,s_late_time,s_start_time)
            s_work = datetime.strptime(str(start_time), DATETIME_FORMAT)+timedelta(hours=8) 
            delayed_delta = s_in-s_work
            
        return delayed_delta
    

    def early_delta_compute(self,req_out,s_out,s_in):
        # self.late_s хоцролт тооцох цаг
        # s_in орсон цаг
        # s_work # ажил эхлэх ёстой цаг
        
        s_start_time=self.start_time
        s_late_time=self.late_s
        early_min_delta=0
        if  self.shift_plan_id and self.shift_plan_id.is_limit: #уян хатан бол
            uyan_oroh_duusah=self.shift_plan_id.in_e_time
            uyan_oroh_ehleh=self.shift_plan_id.in_s_time
    
            uyan_garah_duusah=self.shift_plan_id.out_e_time
            uyan_garah_ehleh=self.shift_plan_id.out_s_time
            
            ajillah_yostoi=uyan_garah_ehleh-uyan_oroh_ehleh
            if uyan_oroh_duusah and uyan_oroh_ehleh and \
                uyan_garah_duusah and uyan_garah_ehleh:
                s_start_time = self.hour_minute_replace(uyan_oroh_duusah,self.date)
                s_work = datetime.strptime(str(s_start_time), DATETIME_FORMAT)+timedelta(hours=8) 
                garah_yostoi=s_in+timedelta(hours=ajillah_yostoi)
                if garah_yostoi>s_out:
                    early_min_delta=garah_yostoi-s_out
                # if s_work<s_in:
                #     delayed_delta = s_in-s_work
                # elif s_work>s_in:
                #     ert_irsen=s_in-s_work
                #     print ('ert_irsenert_irsen ',ert_irsen)
                # if sign_out:
            else:
                raise UserError(('Ээлж дээр Лимит тохируулах эсэх? идэвхитэй байгаа боловч цагуудаа бүрэн бөглөөгүй байна {}'.format(self.shift_plan_id.name)))
                
        else:
            e_work = datetime.strptime(str(self.end_time),DATETIME_FORMAT)+timedelta(hours=8)
            early_min_delta=0
            if req_out:
                if req_out >= e_work:
                    early_min_delta = e_work - req_out
                else:
                    early_min_delta = e_work - s_out
            else:
                early_min_delta = e_work - s_out
    
        return early_min_delta    

# Ажилласан цаг болон хоцролт,таслалт тооцох функц
    def set_delayed_hour(self,obj,sign_in, sign_out):
        time_delta=None
        lunch_in = None
        lunch_out = None
        req_out=None
        req_in = None
        delayed_min = 0
        lunch_hour=0
        hour = 0
        s_work = None
        e_work = None
        s_in = None
        delayed_delta=0
        early_min=0
        if obj.lunch_start_time:
            lunch_in = datetime.strptime(str(obj.lunch_start_time), DATETIME_FORMAT) + timedelta(hours=8)
        if obj.lunch_end_time:
            lunch_out = datetime.strptime(str(obj.lunch_end_time), DATETIME_FORMAT) + timedelta(hours=8)
        # Хоцролт тохиргоон дээр сонгосон цагаас тооцох
        start_time = self.late_hour(obj,obj.late_s,obj.start_time)
        if start_time:
            s_work = datetime.strptime(str(start_time), DATETIME_FORMAT)+timedelta(hours=8)
        if obj.end_time:
            e_work = datetime.strptime(str(obj.end_time),DATETIME_FORMAT)+timedelta(hours=8)
        
        
        if obj.leave_request_end and obj.leave_request_start:
            req_out = datetime.strptime(str(obj.leave_request_end), DATETIME_FORMAT)+timedelta(hours=8)
            req_in = datetime.strptime(str(obj.leave_request_start), DATETIME_FORMAT)+timedelta(hours=8)
        if obj.shift_plan_id:
            lunch_hour = obj.shift_plan_id.compute_sum_lunch
        # Орсон гарсан ирц 2 уулаа байх үед
        if obj.sign_in_emp and obj.sign_out_emp:
            s_in = datetime.strptime(str(obj.sign_in_emp), DATETIME_FORMAT) + timedelta(hours=8)
            s_out = datetime.strptime(str(obj.sign_out_emp), DATETIME_FORMAT) + timedelta(hours=8)
            obj.sickness_hour = 0
            # s_in - Орсон цаг 8:33
            # s_work - Орох ёстой цаг 8:00
            # s_out - garsan цаг 8:33
            # e_work - garah ёстой цаг 8:00
            if s_in and s_work:
                if s_in > s_work:
                    # delayed_delta = s_in - s_work
                    if req_in and req_out:
                        if req_in<=s_in and req_in<=s_out:
                            time_delta = s_out-req_out
                            if req_in > s_work:
                                delayed_delta = req_in - s_work
                                delayed_min = self._delayed_min(delayed_delta)
                            else:
                                delayed_min = 0
                    delayed_delta = obj.delayed_delta_compute(s_in,s_out)
                    delayed_min = self._delayed_min(delayed_delta)
                    
            if s_out and e_work:
                if s_out <= e_work:
                    # if req_out:
                    #     if req_out >= e_work:
                    #         early_min_delta = e_work - req_out
                    #     else:
                    #         early_min_delta = e_work - s_out
                    # else:
                    #     early_min_delta = e_work - s_out
                    early_min_delta =obj.early_delta_compute(req_out,s_out,s_in)
                    early_min = self._delayed_min(early_min_delta)
            if s_out>s_in:
                # Хүсэлтийн цагаас АЦ,хоцролт тооцох
                if req_in and req_out:
                    if req_in<=s_in and req_in<=s_out:
                        time_delta = s_out-req_out
                        if s_work:
                            if req_in > s_work:
                                delayed_delta = req_in - s_work
                                delayed_min = self._delayed_min(delayed_delta)
                            else:
                                delayed_min = 0
                    elif req_in>=s_in and req_in<=s_out:
                        time_delta = req_in-s_in
                    elif req_in>=s_in and req_in>=s_out:
                        time_delta = req_in-s_in
                elif req_in:
                    if req_in<=s_out:
                        time_delta = req_in-s_in
                elif req_out:
                    if req_out<=s_in:
                        time_delta = s_out-req_out
                else:
                    if lunch_out and lunch_in:
                        # Гарсан цаг цайны цаг дуусахаас өмнө үед:
                        if lunch_out>=s_out and lunch_in<=s_out:
                            time_delta = lunch_in-s_in
                        # Орсон цаг цайны цагаас хойш үед хоцролтоос цайны цаг хасагдана
                        elif s_in<=lunch_out and s_in>=lunch_in:
                            time_delta = s_out-lunch_out
                        # else:
                        #     # Орсон цаг цайны цагаас хойш үед хоцролтоос цайны цаг хасагдана
                        #     time_delta = s_out-s_in
                        elif s_work and s_in > s_work:
                            if s_out > e_work:
                                time_delta = e_work-s_in
                            else:
                                time_delta = s_out-s_in
                        elif e_work and s_work:
                            if s_out < e_work:
                                time_delta = s_out-s_work
                            else:
                               time_delta = e_work-s_work
                            # if lunch_in<=s_in:
                            #     # noon = lunch_in - s_work
                            #     # after = s_in - lunch_out
                            #     # delayed_delta = noon + after
                            #     delayed_delta = obj.delayed_delta_compute(s_in,s_out)
                            #     delayed_min = self._delayed_min(delayed_delta)
                    else:
                        time_delta = s_out-s_in
                if time_delta:
                    duration_in_hour = time_delta.total_seconds()
                    hour = divmod(duration_in_hour, 60)[0]
                else:
                    hour = 0
            else:
                time_delta = s_in-s_out
                duration_in_hour = time_delta.total_seconds()
                hour = divmod(duration_in_hour, 60)[0]
        # Орсан гарсан аль нэг нь байвал цайны цагаас тооцно. нэмэлт хүсэлт орж ирвэл хүсэлтээс тооцно
        elif sign_in and lunch_in:
            s_in = datetime.strptime(str(sign_in), DATETIME_FORMAT) + timedelta(hours=8)
            if req_in and req_out:
                if req_in<s_in:
                    if s_work:
                        if req_in > s_work:
                            delayed_delta = req_in - s_work
                            delayed_min = self._delayed_min(delayed_delta)
                    if e_work:
                        time_delta =e_work - req_out
                elif req_in>=s_in:
                    if s_in and s_work:
                        if s_in > s_work:
                            delayed_delta = s_in - s_work
                            delayed_min = self._delayed_min(delayed_delta)
                    time_delta = req_in-s_in
            else:
                if e_work and lunch_out:
                    early_min_delta = e_work - lunch_out
                    early_min = self._delayed_min(early_min_delta)
                if s_in and s_work:
                    if s_in > s_work:
                        delayed_delta = s_in - s_work
                        delayed_min = self._delayed_min(delayed_delta)
                s_out = lunch_in
                time_delta = s_out-s_in
            duration_in_hour = time_delta.total_seconds()
            hour = divmod(duration_in_hour, 60)[0]
            obj.sickness_hour = 0
        elif sign_out and lunch_out and lunch_in:
            s_out = datetime.strptime(str(sign_out), DATETIME_FORMAT) + timedelta(hours=8)
            if req_in and req_out:
                if req_in<=s_out and s_out>=req_out:
                    if req_out >= lunch_in and req_out<=lunch_out:
                        time_delta = e_work - lunch_out
                    else:
                        time_delta = s_out-req_out

                    delayed_delta = req_in - s_work
                    delayed_min = self._delayed_min(delayed_delta)
                else:
                    if e_work and lunch_out:
                        time_delta = e_work - lunch_out
            else:
                if s_out<=e_work:
                    early_min_delta = e_work - s_out
                    early_min = self._delayed_min(early_min_delta)
                time_delta = s_out-lunch_out
                if lunch_in and s_work:
                    delayed_delta = lunch_in - s_work
                delayed_min = self._delayed_min(delayed_delta)
            if time_delta:
                duration_in_hour = time_delta.total_seconds()
                hour = divmod(duration_in_hour, 60)[0]
                obj.sickness_hour = 0
        else:
            hour = 0
            # Тасалсан цаг АЗ цаг онооно Бүх нийтийн амралтын өдөр бол таслалт тооцохгүй
            if obj.shift_plan_id.is_work == 'public_holiday':
                obj.sickness_hour = 0
            else:
                hasah = obj.shift_attribute_id.compute_sum_time-obj.free_wage_hour-obj.free_hour-obj.sick_hour-obj.out_working_hour-obj.accumlated_hour
                if hasah >=0:
                    obj.sickness_hour = hasah
                else:
                    obj.sickness_hour =0
        return hour,delayed_min,lunch_hour,early_min

        
#1.2 Төхөөрөмжийн ирцээс татахгүй бол ажилласан цагуудыг АЗохих цагаас шууд тооцно
    def worked_hour_schedule(self,obj):
        if obj.shift_plan_id:
            hasah = obj.hour_to_work-obj.sick_hour - obj.sickness_hour-obj.free_hour-obj.vacation_day - obj.busines_trip_hour - obj.free_wage_hour - obj.out_working_hour
            hasah_night = obj.shift_plan_id.compute_sum_ov_time-obj.sick_hour - obj.sickness_hour-obj.free_hour-obj.vacation_day - obj.busines_trip_hour - obj.free_wage_hour - obj.out_working_hour
            hasah_add = hasah if hasah>=0 else 0
            hasah_add1 = hasah_night if hasah>=0 else 0
            if obj.shift_plan_id.is_work == 'night':
                if obj.is_public_holiday == True:
                    obj.holiday_worked_hour = hasah_add
                    obj.night_hour = 0
                    obj.tourist_hour = 0
                    obj.worked_hour = 0
                else:
                    obj.worked_hour = obj.shift_plan_id.compute_sum_time
                    obj.night_hour = hasah_add1
                    obj.tourist_hour = 0
            elif obj.shift_plan_id.is_work == 'in':
                if obj.is_public_holiday == True:
                    obj.holiday_worked_hour = hasah_add
                    obj.worked_hour = 0
                    obj.night_hour = 0
                    obj.tourist_hour = 0
                else:
                    obj.worked_hour = 0
                    obj.night_hour = 0
                    obj.tourist_hour = obj.hour_to_work
            elif obj.shift_plan_id.is_work == 'out':
                if obj.is_public_holiday == True:
                    obj.holiday_worked_hour = hasah_add
                    obj.night_hour = 0
                    obj.tourist_hour = 0
                    obj.worked_hour = 0
                else:
                    obj.worked_hour = 0
                    obj.night_hour = 0
                    obj.tourist_hour = obj.hour_to_work
            elif obj.shift_plan_id.is_work == 'day':
                if obj.is_public_holiday == True:
                    obj.holiday_worked_hour = hasah_add
                    obj.night_hour = 0
                    obj.tourist_hour = 0
                    obj.worked_hour = 0
                else:
                    obj.worked_hour = hasah_add
                    obj.overtime_hour = 0
                    obj.night_hour = 0
                    obj.tourist_hour = 0
            #  Доорх цагууд 0 байх тохиолдол
            elif obj.shift_plan_id.is_work in ('bereavement','vacation','sickness','leave','sick','pay_leave','outage','none','parental','business_trip'):
                obj.worked_hour = 0
                obj.night_hour = 0
                obj.tourist_hour = 0
            

#1 Цалин тооцох цаг тооцох  функц
    @api.depends('is_work_schedule','worked_hour', 'out_working_hour', 'online_working_hour', 'free_wage_hour','accumlated_hour','night_hour','parental_hour','training_hour','tourist_hour','over_work_day')
    def _compute_worked_salary_hour(self):
        for obj in self:
            worked_hour=0
            if obj.is_work_schedule == 'night':
                worked_hour = obj.night_hour + obj.worked_hour
            else:
                worked_hour = obj.worked_hour 
            sum_hour  = worked_hour+obj.out_working_hour+obj.online_working_hour+obj.free_wage_hour + obj.accumlated_hour  + obj.training_hour + obj.tourist_hour+obj.over_work_day
            if obj.hour_to_work <= sum_hour:
                obj.worked_salary_hour = obj.hour_to_work - obj.night_hour
            else:
                obj.worked_salary_hour = sum_hour
            