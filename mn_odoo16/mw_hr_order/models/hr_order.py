# -*- coding: utf-8 -*-
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
from odoo import api, fields, models, _
from odoo.addons.mw_base.verbose_format import verbose_format
import logging

_logger = logging.getLogger(__name__)
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d"
DATE_FORMAT = "%Y-%m-%d"


class HrOrder(models.Model):
    _name = "hr.order"
    _description = "Hr order"
    _inherit = ['mail.thread']
    _order = 'name desc'

    def unlink(self):
        for bl in self:
            if bl.state != 'draft':
                raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
        return super(HrOrder, self).unlink()

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

    # _sql_constraints = [
    #     ('config_name_uniq', 'unique(name)', 'Name must be unique!')]

    name = fields.Char(string='Дугаар', tracking=True)
    year = fields.Char(string='Жил', readonly=True)
    month = fields.Char(string='Сар', readonly=True)
    day = fields.Char(string='Өдөр', readonly=True)

    start_year = fields.Char(string='Жил', readonly=True)
    start_month = fields.Char(string='Сар', readonly=True)
    start_day = fields.Char(string='Өдөр', readonly=True)

    start_date_year = fields.Char(string='Жил', readonly=True)
    start_date_month = fields.Char(string='Сар', readonly=True)
    start_date_day = fields.Char(string='Өдөр', readonly=True)

    end_date_year = fields.Char(string='Жил', readonly=True)
    end_date_month = fields.Char(string='Сар', readonly=True)
    end_date_day = fields.Char(string='Өдөр', readonly=True)

    employees_name = fields.Char(
        compute='_employees_name', type='char', store=True, string=u'Ажилчид')
    is_many_emp = fields.Boolean(string='Олон ажилтан сонгох')
    is_wage_change = fields.Boolean(
        string='Цалин өөрчлөгдөх эсэх', default=False, tracking=True)
    is_this_month_wage = fields.Boolean(
        string='Энэ сард цалин бодох бол чеклэнэ үү', default=False, tracking=True)
    warning = fields.Text(string=u'Санамж', readonly=True,
                          default="*Та цалинд өөрчлөлт орохтой холбоотой тушаал бүртгэж байгаа бол Цалин өөрчлөгдөх эсэхийг заавал чеклэнэ үү!!")
    description = fields.Text(string='Тайлбар')
    starttime = fields.Date(string='Хэрэгжүүлэх огноо',
                            required=True, tracking=True)
    approveddate = fields.Date(string='Батлагдсан огноо', tracking=True)
    trainee_end_date = fields.Date(string='Дуусах огноо', tracking=True)

    employee_id = fields.Many2one('hr.employee', string=u'Бүртгэсэн ажилтан',
                                  store=True, default=_default_employee, required=True)
    emp_name_melen = fields.Char(string=u'ажилтан нэрийн эхний үсэг')
    department_id = fields.Many2one(
        'hr.department', string='Хэлтэс', tracking=True)
    job_id = fields.Many2one('hr.job', string='Албан тушаал')
    company_id = fields.Many2one('res.company', string='Компани',required=False,index=True)
    resigned_type = fields.Selection(
        [('type1', 'Ажилтны санаачилга'), ('type2', 'АО санаачилга')], 'Ажлаас гарах шалтгаан')
    state = fields.Selection([('draft', u'Ноорог'), ('send', u'Илгээсэн'), ('approve', u'Хянасан'), (
        'done', u'Баталсан'), ('canceled', u'Цуцалсан')], 'Төлөв', default='draft', tracking=True)
    order_type_id = fields.Many2one(
        'hr.order.type', string='Тушаалын төрөл', tracking=True, required=True)
    type = fields.Selection(related='order_type_id.type', string='Type')
    days = fields.Integer(string='Хоног')
    months = fields.Integer(string='Хугацаа')
    wage = fields.Float(string='Үндсэн цалин',tracking=True)
    wage_ch = fields.Char(string='Үндсэн цалин/хэвлэх/')
    wage_str = fields.Char(string='Үндсэн цалин/үсгээр/',
                           compute='_amount_wage_str')
    contract_id = fields.Many2one(
        'hr.contract', 'Contract', readonly=True)
    reward = fields.Float('Шагналын дүн')

    endtime = fields.Date(string='Хэрэгжүүлж дуусах огноо')
    remain_date = fields.Date(string='Үлдсэн огноо')
    remain_end_date = fields.Date(string='Үлдсэн дуусах огноо')
    vac_days = fields.Char('Нийт амрах хоног', related='employee_id.days_of_annualleave')
    start_days = fields.Char(string='Эхний амралт', compute='_compute_day')
    end_days = fields.Char(string='Үлдсэн амралт', compute='_compute_vac_days')
    leave_type = fields.Selection([
        ('married', 'Шинэ хүүхэд мэндэлсэн'),
        ('died', 'Гэр бүлийн гишүүн нас барсан'),
    ], string='Төрөл', tracking=True)

    allowance_type = fields.Selection([
        ('newborn', 'Гэрлэлт'),
        ('died', 'Гэр бүлийн гишүүн нас барсан'),
        ('other', 'Бусад шалтгаан'),
    ], string='Төрөл', tracking=True)
    res_currency_id = fields.Many2one('res.currency', 'Валют', default=111)
    wage_mnt = fields.Float(u'Үндсэн цалин MNT', digits=(
        0, 0), compute='_compute_one_day_wage', tracking=True)

# Үндсэн цалин/үсгээр/
    @api.depends('wage')
    def _amount_wage_str(self):
        for line in self:
            if line.wage:
                line.wage_str = verbose_format(abs(line.wage))
            else:
                line.wage_str = ''

# Нэг ажилтан дээр тушаал гарах Тушаал хэвлэхэд ашиглана
    order_employee_id = fields.Many2one(
        'hr.employee', string='Ажилтан', tracking=True,index=True)
    order_department_id = fields.Many2one(
        'hr.department', string='Хэлтэс', related='order_employee_id.department_id')
    order_job_id = fields.Many2one(
        'hr.job', string='Албан тушаал', tracking=True)
    order_name_melen = fields.Char('Melen')

    department_id_after = fields.Many2one(
        'hr.department', string=u'Шинэ хэлтэс', related='job_id_after.department_id', tracking=True)
    job_id_after = fields.Many2one(
        'hr.job', string=u'Шинэ албан тушаал', tracking=True)
    order_lines = fields.One2many(
        'hr.order.line', 'order', string='Ажилтан', tracking=True)
    inactive_user = fields.Text(
        string='Идэвхгүй болсон хэрэглэгч', readonly=True)

    new_wage = fields.Float(string='Нэмэгдэл цалин')
    new_wage_ch = fields.Char(string='Нэмэгдэл цалин/хэвлэх/')
    new_wage_str = fields.Char(
        string='Нэмэгдэл цалин/үсгээр/', compute='_amount_new_wage_str')
    contract_number = fields.Char(string='ХГэрээний дугаар', readonly=True)

    discipline_name = fields.Char(string='Сахилгын нэр')
    start_date = fields.Date(string='Эхлэх огноо',index=True)
    end_date = fields.Date(string='Дуусах огноо',index=True)
    desc = fields.Char(string='Шалтгаан')
    prize_desc = fields.Char(string='Тайлбар')
    deduct = fields.Float(string='Суутгалын хувь',index=True)

    prize_name_id = fields.Many2one('hr.prize.name', string='Шагналын нэр')
    prize_date = fields.Date(string='Шагналын огноо')
    prize_type = fields.Selection([('1', 'Төрийн шагнал'),
                                   ('2', 'Засгийн газрын шагнал'),
                                   ('3', 'Төрийн бус байгууллагын шагнал'),
                                   ('4', 'Группын шагнал'),
                                   ('5', 'Байгууллагын шагнал')], string='Шагналын төрөл')
    begin_date = fields.Date(string='Ажлаас гарсан огноо')

    allowance = fields.Integer(string='Олгох тэтгэмж')
    allowance_name = fields.Char(string='Олгох тэтгэмжийн нэр')

    con_day = fields.Float(string='Ногдох хоног', readonly=True,
                           compute='_compute_con_day', store=True)
    is_con = fields.Boolean(string='Ногдуулж авах эсэх?', default=True)
    in_company_date = fields.Date(
        string='Компанид ажилд орсон огноо', readonly=True)
    before_shift_vac_date = fields.Date(
        string='Өмнө жил ЭА цалин авсан огноо', readonly=True)
    this_vac_date = fields.Date(
        string='Хуваарьт ЭА цалин авах огноо', readonly=True)
    payslip_date = fields.Date(string='ЭАЦалин авах огноо', tracking=True)
    count_day = fields.Char(string='Амрах хоног', readonly=True)

    @api.depends('is_con', 'payslip_date', 'before_shift_vac_date', 'count_day')
    def _compute_con_day(self):
        for item in self:
            if item.is_con == True and item.payslip_date and item.before_shift_vac_date and item.count_day:
                date1 = datetime.strptime(
                    str(item.before_shift_vac_date), "%Y-%m-%d")
                date2 = datetime.strptime(str(item.payslip_date), "%Y-%m-%d")
                delta = date2-date1
                item.con_day = delta.days * float(item.count_day)/365
            else:
                item.con_day = float(item.count_day)

# Тушаалд оролцох хүмүүс

    def default_hr_employee(self):
        res = self.env['ir.config_parameter'].sudo(
        ).get_param('default_hr_employee')
        emp = self.browse(int(res))
        return emp

    def default_acc_employee(self):
        res = self.env['ir.config_parameter'].sudo(
        ).get_param('default_acc_employee')
        emp = self.browse(int(res))
        return emp
    
    def default_law_employee(self):
        res = self.env['ir.config_parameter'].sudo(
        ).get_param('default_law_employee')
        emp = self.browse(int(res))
        return emp

    doc_employee_id = fields.Many2one(
        'hr.employee', string='Шууд удирдлага', tracking=True)
    doc_name_melen = fields.Char(string='ШУ-ын нэрний эхний үсэг')
    doc_job_id = fields.Many2one(
        'hr.job', string='Албан тушаал', related='doc_employee_id.job_id', tracking=True)

    hr_employee_id = fields.Many2one(
        'hr.employee', string='Хүний нөөцийн мэргэжилтэн', default=default_hr_employee)
    hr_name_melen = fields.Char('ХНМ нэрний эхний үсэг')
    acc_employee_id = fields.Many2one(
        'hr.employee', string='Нягтлан', default=default_acc_employee)
    acc_name_melen = fields.Char('Нягтлан нэрний эхний үсэг')
    law_employee_id = fields.Many2one(
        'hr.employee', string='Хууль', default=default_law_employee)
    law_name_melen = fields.Char('Хууль нэрний эхний үсэг')

# нэмэгдэл цалин хэвлэхэд

    @api.depends('new_wage')
    def _amount_new_wage_str(self):
        for line in self:
            if line.new_wage:
                line.new_wage_str = verbose_format(abs(line.new_wage))
            else:
                line.new_wage_str = ''

# ONCHANGE
    @api.onchange('new_wage')
    def onchange_new_wage(self):
        if self.new_wage:
            self.new_wage_ch = '{0:,.2f}'.format(self.new_wage).split('.')[0]

    @api.onchange('wage')
    def onchange_wage(self):
        if self.wage:
            self.wage_ch = '{0:,.2f}'.format(self.wage).split('.')[0]

    @api.onchange('order_employee_id')
    def _onchange_order_employee_id(self):
        if self.order_employee_id:
            contract_pool = self.env['hr.employee.contract'].search(
                [('employee_id', '=', self.order_employee_id.id)], limit=1)
            if contract_pool:
                self.contract_number = contract_pool.number
            self.in_company_date = self.order_employee_id.engagement_in_company
            self.before_shift_vac_date = self.order_employee_id.before_shift_vac_date
            self.count_day = self.order_employee_id.days_of_annualleave
            self.this_vac_date = self.order_employee_id.before_year_shipt_leave_date
            self.order_department_id = self.order_employee_id.department_id.id
            self.order_job_id = self.order_employee_id.job_id.id
            self.order_name_melen = self.order_employee_id.last_name[:1]

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
            self.emp_name_melen = self.employee_id.last_name[:1]
            self.company_id = self.employee_id.company_id.id


    @api.onchange('hr_employee_id')
    def onchange_hr_employee_id(self):
        if self.hr_employee_id:
            self.hr_name_melen = self.hr_employee_id.last_name[:1]

    @api.onchange('acc_employee_id')
    def onchange_acc_employee_id(self):
        if self.acc_employee_id:
            self.acc_name_melen = self.acc_employee_id.last_name[:1]
            
    @api.onchange('law_employee_id')
    def onchange_law_employee_id(self):
        if self.law_employee_id:
            self.law_name_melen = self.law_employee_id.last_name[:1]

    @api.onchange('doc_employee_id')
    def onchange_doc_employee_id(self):
        if self.doc_employee_id:
            self.doc_name_melen = self.doc_employee_id.last_name[:1]

    @api.onchange('trainee_end_date')
    def onchange_trainee_end_date(self):
        if self.trainee_end_date:
            end_date = datetime.strptime(
                str(self.trainee_end_date), DATE_FORMAT)
            self.year = str(self.trainee_end_date)[:4]
            self.month = end_date.month
            self.day = end_date.day

    @api.onchange('starttime')
    def onchange_starttime(self):
        if self.starttime:
            start_time = datetime.strptime(str(self.starttime), DATE_FORMAT)
            self.start_year = str(self.starttime)[:4]
            self.start_month = start_time.month
            self.start_day = start_time.day

    @api.onchange('start_date')
    def onchange_start_date(self):
        if self.start_date:
            start = datetime.strptime(str(self.start_date), DATE_FORMAT)
            self.start_date_year = str(self.start_date)[:4]
            self.start_date_month = start.month
            self.start_date_day = start.day

    @api.onchange('end_date')
    def onchange_end_date(self):
        if self.end_date:
            end = datetime.strptime(str(self.end_date), DATE_FORMAT)
            self.end_date_year = str(self.end_date)[:4]
            self.end_date_month = end.month
            self.end_date_day = end.day

# Ээлжийн амралт
    # @api.onchange('remain_date')
    # def onchange_remain_date(self):
    #     if self.remain_date:
    #         start_time = datetime.strptime(str(self.remain_date), DATE_FORMAT)
    #         self.start_year = str(self.remain_date)[:4]
    #         self.start_month = start_time.month
    #         self.start_day = start_time.day

    # @api.onchange('remain_end_date')
    # def onchange_remain_end_date(self):
    #     if self.remain_end_date:
    #         start_time = datetime.strptime(
    #             str(self.remain_end_date), DATE_FORMAT)
    #         self.start_year = str(self.remain_end_date)[:4]
    #         self.start_month = start_time.month
    #         self.start_day = start_time.day

    # @api.onchange('endtime')
    # def onchange_end_time(self):
    #     if self.endtime:
    #         start_time = datetime.strptime(str(self.endtime), DATE_FORMAT)
    #         self.start_year = str(self.endtime)[:4]
    #         self.start_month = start_time.month
    #         self.start_day = start_time.day

    def daterange(self, starttime, endtime):
        for n in range(int((endtime - starttime).days)+1):
            yield starttime + timedelta(n)

    @api.depends('starttime', 'endtime')
    def _compute_day(self):
        for item in self:
            st_d = None
            en_d = None
            if item.starttime and item.endtime:
                st_d = datetime.strptime(
                    str(item.starttime), DATETIME_FORMAT).date()
                en_d = datetime.strptime(
                    str(item.endtime), DATETIME_FORMAT).date()
                days_count = 0
                day_too = 0
                for single_date in item.daterange(st_d, en_d):
                    days_count += 1 if single_date.weekday() < 5 else 0
                    day_too = days_count
                item.start_days = day_too
            else:
                item.start_days = 0

    @api.depends('vac_days', 'start_days')
    def _compute_vac_days(self):
        for item in self:
            if item.start_days:
                item.end_days = int(item.vac_days) - int(item.start_days)
            else:
                item.end_days = ''

# flow
    def action_send(self):
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('hr.order')
        self._notification_send()
        return self.write({'state': 'send'})

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_canceled(self):
        return self.write({'state': 'canceled'})

    def action_approve(self):
        return self.write({'state': 'approve'})

# Хэрэглэгч эрх идэвхгүй болгох
    def action_user_inactive(self):
        users = []
        if self.is_many_emp == True:
            for item in self.order_lines:
                item.employee_id.user_id.update({'active': False})
                item.employee_id.user_id.update(
                    {'login': item.employee_id.user_id.name})
                item.employee_id.partner_id.update(
                    {'email': item.employee_id.user_id.name})
                users.append(item.employee_id.identification_id)
        else:
            self.order_employee_id.user_id.update({'active': False})
            self.order_employee_id.user_id.update(
                {'login': self.order_employee_id.user_id.name})
            self.order_employee_id.partner_id.update(
                {'email': self.order_employee_id.user_id.name})
            users.append(self.order_employee_id.identification_id)
        self.inactive_user = users

    def _notification_send(self):
        base_url = self.env['ir.config_parameter'].sudo(
        ).get_param('web.base.url')
        action_id = self.env.ref('mw_hr_order.hr_order_action').id
        html = u'<b>Б тушаал</b><br/>'
        html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.order&action=%s>%s</a></b>, ажилтан <b>%s</b> тушаал илгээлээ""" % (
            base_url, self.id, action_id, self.employee_id.name, self.order_type_id.name)
        partners = self.env.ref(
            'mw_hr.group_hr_confirm').sudo().users.mapped('partner_id')
        for receiver in partners:
            self.env.user.send_chat(html, receiver)

# Батлах товчоор ажилтны мэдээлэл рүү шинэчлэлт хийгдэнэ
    def action_done(self):
        # Үндсэн ажилтан
        if self.type == 'type1':
            self.update_type1()

        # Туршилтын ажилтан
        if self.type == 'type2':
            if self.is_many_emp == True:
                for item in self.order_lines:
                    item.employee_id.update({'employee_type': 'trainee'})
                    item.employee_id.update({'job_id': item.job_id.id})
                    item.employee_id.update(
                        {'department_id': item.department_id.id})
                    #item.employee_id.update(
                       # {'engagement_in_company': self.starttime})
                    # if not item.employee_id.identification_id:
                    #   seq_id = self.env['ir.sequence'].search([('code','=','hr.employee'), ('name','=','Identification_id')], limit=1)
                    #   item.employee_id.identification_id =seq_id.next_by_id()
            else:
                self.order_employee_id.update({'employee_type': 'trainee'})
                self.order_employee_id.update({'job_id': self.order_job_id.id})
                self.order_employee_id.update(
                    {'department_id': self.order_department_id.id})
                self.order_employee_id.update(
                    {'engagement_in_company': self.starttime})
                # if not self.order_employee_id.identification_id:
                #   seq_id = self.env['ir.sequence'].search([('code','=','hr.employee'), ('name','=','Identification_id')], limit=1)
                #   self.order_employee_id.identification_id =seq_id.next_by_id()

        # Ажлын байр өөрчлөх тухай
        if self.type == 'type4':
            history_line_id = self.env['hr.company.history']
            if self.is_many_emp == True:
                for item in self.order_lines:
                    history_line_id = history_line_id.create({
                        'employee_id': item.employee_id.id,
                        'pre_value': item.job_id.name,
                        'new_value': item.new_job_id.name,
                        'type': 'job',
                        'order': self.id,
                        'date': self.starttime,
                    })
                    item.employee_id.update({'job_id': item.new_job_id.id})
                    item.employee_id.update(
                        {'department_id': item.new_department_id.id})
            else:
                history_line_id = history_line_id.create({
                    'employee_id': self.order_employee_id.id,
                    'pre_value': self.order_job_id.name,
                    'new_value': self.job_id_after.name,
                    'type': 'job',
                    'order': self.id,
                    'date': self.starttime,
                })
                self.order_employee_id.update({'job_id': self.job_id_after.id})
                self.order_employee_id.update(
                    {'department_id': self.department_id_after.id})
        # Шагнал
        prize_id = self.env['hr.prize']
        if self.is_many_emp == True:
            for item in self.order_lines:
                data = prize_id.create({
                    'employee_id': item.employee_id.id,
                    # 'prize_type': item.prize_type,
                    'prize_date': item.prize_date,
                    'prize_name_id': item.prize_name_id.id,
                    'award_amount': self.reward,
                })
        else:
            data = prize_id.create({
                'employee_id': self.order_employee_id.id,
                'prize_type': self.prize_type,
                'prize_date': self.prize_date,
                'prize_name_id': self.prize_name_id.id,
                'award_amount': self.reward,
            })

        # Ажлаас гарсан төлөвт орох
        if self.type == 'type6':
            self.update_type6()

        # Жирэмсний чөлөө авах тохиолдол
        if self.type == 'type7':
            if self.is_many_emp == True:
                for item in self.order_lines:
                    item.employee_id.update(
                        {'employee_type': 'pregnant_leave'})
            else:
                self.order_employee_id.update(
                    {'employee_type': 'pregnant_leave'})

        # Хүүхэд асрах чөлөө авах тухай
        if self.type == 'type8':
            if self.is_many_emp == True:
                for item in self.order_lines:
                    item.employee_id.update({'employee_type': 'maternity'})
            else:
                self.order_employee_id.update({'employee_type': 'maternity'})

        # Урт хугацааны чөлөө
        if self.type == 'type9':
            if self.is_many_emp == True:
                for item in self.order_lines:
                    item.employee_id.update({'employee_type': 'longleave'})
            else:
                self.order_employee_id.update({'employee_type': 'longleave'})
        # Ээлжийн амралтын тушаалаас цагийн хүсэлт үүсгэх
        if self.type == 'type13':
            leave_pool = self.env['hr.leave.mw'].sudo()
            type = self.env['hr.shift.time'].sudo().search(
                [('is_work', '=', 'vacation')], limit=1)
            flow = self.env['dynamic.flow'].sudo().search(
                [('model_id.model', '=', 'hr.leave.mw')], limit=1)
            employee = self.env['hr.employee'].search(
                [('id', '=', self.order_employee_id.id)])
            leave_data_id = leave_pool.create({
                'department_id': self.order_department_id.id,
                'employee_id': self.order_employee_id.id,
                'work_location_id': self.order_employee_id.work_location_id.id,
                'shift_plan_id': type.id,
                'flow_id': flow.id,
                'date_from': self.starttime,
                'date_to': self.trainee_end_date,
                'time_from': 8,
                'time_to': 17,
            })
            emp = employee.update({
                'start_days': self.start_days,
                'end_days': self.end_days
            })
        if self.type == 'type9':
            leave_pool = self.env['hr.leave.mw'].sudo()
            type = self.env['hr.shift.time'].sudo().search(
                [('is_work', '=', 'leave')], limit=1)
            flow = self.env['dynamic.flow'].sudo().search(
                [('model_id.model', '=', 'hr.leave.mw')], limit=1)
            leave_data_id = leave_pool.create({
                'department_id': self.order_department_id.id,
                'employee_id': self.order_employee_id.id,
                'work_location_id': self.order_employee_id.work_location_id.id,
                'shift_plan_id': type.id,
                'flow_id': flow.id,
                'date_from': self.starttime,
                'date_to': self.trainee_end_date,
                'time_from': 8,
                'time_to': 17,

            })
        # self.create_hr_contract()
        return self.write({'state': 'done'})

    def update_type1(self):
        history_line_id = self.env['hr.company.history']
        if self.is_many_emp == True:
                for item in self.order_lines:
                    item.employee_id.update({'employee_type': 'employee'})
                    item.employee_id.update({'job_id': item.job_id.id})
                    item.employee_id.update({'department_id': item.department_id.id})
        else:
            history_line_id = history_line_id.create({
                'employee_id': self.order_employee_id.id,
                'pre_value': dict(self.order_employee_id._fields['employee_type'].selection).get(self.order_employee_id.employee_type),
                'type': 'type',
                'order': self.id,
                'date': self.starttime,
            })
            self.order_employee_id.update({'employee_type': 'employee'})
            self.order_employee_id.update({'job_id': self.order_job_id.id})
            self.order_employee_id.update(
                {'department_id': self.order_department_id.id})
            history_line_id = history_line_id.update({
                'employee_id': self.order_employee_id.id,
                'new_value': dict(self.order_employee_id._fields['employee_type'].selection).get(self.order_employee_id.employee_type),
            })

    def update_type6(self):
        if self.is_many_emp == True:
            for item in self.order_lines:
                item.employee_id.update({'employee_type': 'resigned'})
                item.employee_id.update({'work_end_date': self.starttime})
                item.employee_id.update(
                    {'is_this_month_wage': self.is_this_month_wage})
        else:
            self.order_employee_id.update({'employee_type': 'resigned'})
            self.order_employee_id.update({'work_end_date': self.starttime})
            self.order_employee_id.update(
                {'is_this_month_wage': self.is_this_month_wage})

    # Ажилчдын нэрс авч байгаа функц
    @api.depends('order_lines')
    def _employees_name(self):
        employees_name = []
        for obj in self:
            for l in obj.order_lines:
                if l.employee_id.id:
                    employees_name.append(l.employee_id.name)
            obj.employees_name = employees_name

    # Цалингийн гэрээ үүсгэх
    def _compute_one_day_wage(self):
        self.wage_mnt = self.res_currency_id.rate * self.wage

    def create_hr_contract(self):
        if self.is_many_emp:
            for item in self.order_lines:
                if item.employee_id:
                    existing_contracts = self.env['hr.contract'].search([
                        ('employee_id', '=', item.employee_id.id),
                        ('active', '=', True)
                    ])
                    existing_contracts.write({'active': False})
                    vals = {
                        'employee_id': item.employee_id.id,
                        'name': item.employee_id.identification_id,
                        'wage': item.new_wage,
                        # 'start_date': self.starttime,
                        'active': True,
                    }
                    item._compute_one_day_wage()
                    contract_id = self.env['hr.contract'].create(vals)
                    item.contract_id = contract_id.id
        else:
            if self.order_employee_id:
                existing_contracts = self.env['hr.contract'].search([
                    ('employee_id', '=', self.order_employee_id.id),
                    ('active', '=', True)
                ])
                existing_contracts.write({'active': False})
                vals = {
                    'employee_id': self.order_employee_id.id,
                    'name': self.order_employee_id.identification_id,
                    'wage': self.wage,
                    'start_date': self.starttime,
                    'active': True,
                }
                self._compute_one_day_wage()
                contract_id = self.env['hr.contract'].create(vals)
                self.contract_id = contract_id.id

    def get_company_logo(self, ids):
        report_id = self.browse(ids)
        image_buf = report_id.company_id.logo
        image_str = """<img alt="Embedded Image" width="180" src='data:image/png;base64,%s""" % image_buf+'/>'
        image_str = image_str.replace("base64,b'", "base64,", 1)
        return image_str

# Print function
    # Олон хүн дээр гарсан тушаалын хавсралт
    def get_print_lines(self, ids):
        headers = [
            u'<p style="text-align: center;font-weight: bold; font-size: 17px" >''№'u'</p>',
            u'<p style="text-align: center;font-weight: bold; font-size: 17px">''Ажилтны овог'u'</p>',
            u'<p style="text-align: center;font-weight: bold; font-size: 17px">''Ажилтны нэр'u'</p>',
            u'<p style="text-align: center;font-weight: bold; font-size: 17px">''Department'u'</p>',
            u'<p style="text-align: center;font-weight: bold; font-size: 17px" >''Position'u'</p>',
        ]
        datas = []
        report_id = self.browse(ids)
        i = 1

        in_sel = ''
        for line in report_id.order_lines:
            if line.employee_id:
                temp = [
                    u'<p style="text-align: center; font-size: 17px">' +
                    str(i)+u'</p>',
                    u'<p style="text-align: left;font-size: 17px">' +
                    str(line.employee_id.last_name) or '' + u'</p>',
                    u'<p style="text-align: left;font-size: 17px">' +
                    str(line.employee_id.name) or '' + u'</p>',
                    u'<p style="text-align: center; font-size: 17px">' +
                    str(line.department_id.name) or '' + u'</p>',
                    u'<p style="text-align: center;font-size: 17px">' +
                    str(line.job_id.name) or '' + u'</p>',
                ]
                datas.append(temp)
                i += 1
        res = {'header': headers, 'data': datas}
        return res

class HrOrderLine(models.Model):
    _name = 'hr.order.line'
    _description = 'Employee order'
    _order = 'employee_id'

    order = fields.Many2one('hr.order', string='Order')
    employee_id = fields.Many2one('hr.employee', 'Ажилтан')
    department_id = fields.Many2one('hr.department', 'Хэлтэс')
    job_id = fields.Many2one('hr.job', 'Албан тушаал')
    wage = fields.Float(string='Үндсэн цалин')
    new_wage = fields.Integer('Цалин')
    new_job_id = fields.Many2one('hr.job', u'Шинэ албан тушаал')
    new_department_id = fields.Many2one('hr.department', u'Шинэ хэлтэс')

    duple_job_id = fields.Many2one('hr.job', 'Хавсрах албан тушаал')
    duple_department_id = fields.Many2one(
        'hr.department', 'Хавсрах алба хэлтэс')

    discipline_name = fields.Char('Сахилгын нэр')
    start_date = fields.Date('Эхлэх огноо')
    end_date = fields.Date('Дуусах огноо')

    desc = fields.Char('Шалтгаан')
    prize_desc = fields.Char('Тайлбар')
    deduct = fields.Float('Суутгалын хувь')

    prize_name_id = fields.Many2one('hr.prize.name', string='Шагналын нэр')
    prize_date = fields.Date('Шагналын огноо')
    begin_date = fields.Date('Ажлаас гарсан огноо')

    allowance = fields.Integer('Олгох тэтгэмж')
    allowance_name = fields.Char('Олгох тэтгэмжийн нэр')
    contract_id = fields.Many2one(
        'hr.contract', 'Contract', readonly=True)
    res_currency_id = fields.Many2one('res.currency', 'Валют', default=111)
    wage_mnt = fields.Float(u'Үндсэн цалин MNT', digits=(
        0, 0), compute='_compute_one_day_wage', tracking=True)

    def _compute_one_day_wage(self):
        self.wage_mnt = self.res_currency_id.rate * self.wage

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        self.department_id = self.employee_id.department_id.id
        self.job_id = self.employee_id.job_id.id
        # self.company_year = self.employee_id.natural_compa_work_year
        # self.long_year = self.employee_id.natural_compa_year

    new_wage_ch = fields.Char(string='Нэмэгдэл цалин/хэвлэх/')
    new_wage_str = fields.Char(
        string='Нэмэгдэл цалин/үсгээр/', compute='_new_wage_str')
    wage_ch = fields.Char(string='Үндсэн цалин/хэвлэх/')
    wage_str = fields.Char(
        string='Нэмэгдэл цалин/үсгээр/', compute='_wage_str')

    # нэмэгдэл цалин хэвлэхэд

    @api.depends('new_wage')
    def _new_wage_str(self):
                for line in self:
                    if line.new_wage:
                        line.new_wage_str = verbose_format(abs(line.new_wage))
                    else:
                        line.new_wage_str = ''

    @api.depends('wage')
    def _wage_str(self):
                for line in self:
                    if line.wage:
                        line.wage_str = verbose_format(abs(line.wage))
                    else:
                        line.wage_str = ''
    # ONCHANGE
    @api.onchange('new_wage')
    def onchange_new_wage(self):
            if self.new_wage:
                self.new_wage_ch = '{0:,.2f}'.format(self.new_wage).split('.')[0]

    @api.onchange('wage')
    def onchange_wage(self):
            if self.wage:
                self.wage_ch = '{0:,.2f}'.format(self.wage).split('.')[0]
class HrOrderType(models.Model):
    _name = 'hr.order.type'
    _description = 'Hr order type'
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = 'name'

    name = fields.Char('Тушаалын төрөл')
    type = fields.Selection([('type1', u'Ажилд авах - Үндсэн ажилтан төлөв'),
                             ('type2', u'Ажилд авах - Туршилтын ажилтан төлөв'),
                             ('type3', u'Үндсэн цалин өөрчлөгдөх'),
                             ('type4', u'Албан тушаал өөрчлөх'),
                             ('type5', u'Шагнал'),
                             ('type6', u'Ажлаас чөлөөлөх - Ажлаас гарсан төлөв'),
                             ('type7', u'Жирэмсний амралт - Жирэмсний чөлөө'),
                             ('type8', u'Хүүхэд асрах чөлөө - Хүүхэд асрах чөлөө чөлөө'),
                             ('type9', u'Чөлөө олгох - Урт хугацааны чөлөө'),
                             ('type10', u'Сахилга'),
                             ('type11', u'Тэтгэмж'),
                             ('type12', u'Бусад'),
                             ('type13', u'Ээлжийн амралт'),
                             ('type14', u'Ээлжийн амралтын олговор олгох'),
                             ('type16', u'Цалинтай чөлөө, тэтгэмж олгох'),
                             ('type17', u'Чөлөө'),
                             ], u'Type', tracking=True, required=True)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    order_count = fields.Integer(
        string='Холбоотой тушаалын тоо', compute="_compute_order_count")
    disc_count = fields.Integer(
        string='Холбоотой сахилга тоо', compute="_compute_discipline_count")
    start_days = fields.Integer(string='Амарсан хоног')
    end_days = fields.Integer(string='Үлдсэн хоног')

    def _compute_order_count(self):
        order = self.env['hr.order'].search(
            [('order_employee_id', '=', self.id), ('state', '=', 'done')])
        order_line = self.env['hr.order.line'].search(
            [('employee_id', '=', self.id), ('order.state', '=', 'done')])
        for emp in self:
            emp.order_count = len(order) + len(order_line)

    def _compute_discipline_count(self):
        for emp in self:
            disc = self.env['hr.order'].search_count([
                ('order_employee_id', '=', emp.id), 
                ('state', '=', 'done'), 
                ('type', '=', 'type10')
            ])
            disc_order_line = self.env['hr.order.line'].search_count([
                ('employee_id', '=', emp.id), 
                ('order.state', '=', 'done'),
                ('order.type', '=', 'type10')
            ])
            emp.disc_count = disc_order_line


    def action_hr_order(self):
        self.ensure_one()

        employee_ids = self.env['hr.order.line'].search([('employee_id', '=', self.id)])
        employee_order = self.env['hr.order'].search([('order_employee_id', '=', self.id)])

        if employee_ids:
            action = self.env["ir.actions.actions"]._for_xml_id('mw_hr_order.hr_order_action')
            action['domain'] = ['|', ('order_lines.employee_id', '=', self.id), ('order_employee_id', '=', self.id),('state', '=', 'done')]
            action['res_id'] = self.id if employee_ids else employee_order.ids  
        else:
            action = self.env["ir.actions.actions"]._for_xml_id('mw_hr_order.hr_order_action')
            action['domain'] = ['|',('employee_id', '=', self.id), ('order_employee_id', '=', self.id),('state', '=', 'done')
            ]
            action['res_id'] = self.id

        return action

    def action_hr_order_disc(self):
        self.ensure_one()

        employee_ids = self.env['hr.order.line'].search([('employee_id', '=', self.id)])
        employee_order = self.env['hr.order'].search([('order_employee_id', '=', self.id)])

        if employee_ids:
            action = self.env["ir.actions.actions"]._for_xml_id('mw_hr_order.hr_order_action')
            action['domain'] = ['|', ('order_lines.employee_id', '=', self.id), ('order_employee_id', '=', self.id),('state', '=', 'done'), ('type', '=', 'type10')]
            action['res_id'] = self.id if employee_ids else employee_order.ids  
        else:
            action = self.env["ir.actions.actions"]._for_xml_id('mw_hr_order.hr_order_action')
            action['domain'] = ['|',('employee_id', '=', self.id), ('order_employee_id', '=', self.id),('state', '=', 'done'),('type', '=', 'type10')
            ]
            action['res_id'] = self.id
        return action
    
class HrCompanyHistory(models.Model):
	_inherit = 'hr.company.history'

	order = fields.Many2one('hr.order', string='Тушаал')