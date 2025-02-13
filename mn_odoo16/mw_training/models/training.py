
# -*- coding: utf-8 -*-
import datetime
from datetime import datetime
from odoo import api, fields, models, _
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
month = [('jan', '1 сар'), ('feb', '2 сар'), ('march', '3 сар'), ('april', '4 сар'),
         ('may', '5 сар'), ('june', '6 сар'), ('july',
                                               '7 сар'), ('aug', '8 сар'), ('sept', '9 сар'),
         ('octo', '10 сар'), ('nov', '11 сар'), ('dec', '12 сар')]


class TrainingType(models.Model):
    _name = 'training.type'
    _description = 'Traing type'
    _inherit = ['mail.thread']

    type = fields.Char('Төрөл', tracking=True)

    def name_get(self):
        res = []
        for item in self:
            if item.type:
                res.append((item.id, item.type))
        return res


class TrainingRegister(models.Model):
    _name = "training.register"
    _inherit = ['mail.thread']
    _description = "Training register"

    name = fields.Char('Сургалтын нэр', tracking=True)
    type_id = fields.Many2one('training.type', 'Бүлэг', tracking=True)


class TrainingRequest(models.Model):
    _name = "training.request"
    _inherit = ['mail.thread']
    _description = "Training Request"

    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    name_id = fields.Many2one(
        'training.register', 'Сургалтын нэр', tracking=True)
    employee_id = fields.Many2one('hr.employee',string='Ажилтан',default=_default_employee)
    year = fields.Char('Жил', tracking=True)
    exigency = fields.Text('Хэрэгцээ шаардлага', tracking=True)
    sum_payment = fields.Float('Сургалтын төлбөр')
    department_id = fields.Many2one('hr.department', 'Хэлтэс', tracking=True)
    create_date = fields.Date(
        'Үүсгэсэн огноо', default=fields.Datetime.now(), copy=False, tracking=True)
    company_id = fields.Many2one('res.company', string='Компани')
    type = fields.Selection([('in', 'Дотоод'), ('out', 'Гадаад'),
                            ('abroad', 'Гадаад улсын')], 'Төрөл', tracking=True)
    employee_ids = fields.Many2many('hr.employee', string='Ажилчид')
    month = fields.Selection(month, 'Сар', tracking=True)
    emp_count = fields.Char('Хүний тоо')

    state = fields.Selection([('draft', 'Ноорог'),
                              ('sent', u'Илгээсэн'),
                              ('done', u'Хүлээж авсан')], 'Төлөв', readonly=True, default='draft', tracking=True, copy=False)

    def action_to_sent(self):
        self.write({'state': 'sent'})

    def action_to_done(self):
        self.write({'state': 'done'})

    def action_to_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('create_date')
    def _onchange_create_date(self):
        if self.create_date:
            self.year = self.create_date.year
            # self.month = self.create_date.month


class TrainingPlan(models.Model):
    _name = "training.plan"
    _inherit = ['mail.thread']
    _description = "Training plan"

    name_id = fields.Many2one(
        'training.register', 'Сургалтын нэр', tracking=True)
    year = fields.Char('Жил', tracking=True)
    create_date = fields.Date(
        'Үүсгэсэн огноо', default=fields.Datetime.now(), copy=False)
    month = fields.Selection(month, 'Сар', tracking=True)
    line_ids = fields.One2many('training.plan.line', 'parent_id', 'Lines')
    company_id = fields.Many2one('res.company', string='Компани',
                                 default=lambda self: self.env.user.company_id, readonly=True)
    state = fields.Selection([('draft', 'Ноорог'),
                              ('sent', u'Илгээсэн'),
                              ('done', u'Баталсан')], 'Төлөв', readonly=True, default='draft', tracking=True, copy=False)

    def action_to_sent(self):
        self.write({'state': 'sent'})

    def action_to_done(self):
        self.write({'state': 'done'})

    def action_to_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('create_date')
    def _onchange_create_date(self):
        if self.create_date:
            self.year = self.create_date.year

    def create_plan_line(self):
        if self.line_ids:
            self.line_ids.unlink()
        requests = self.env['training.request'].search([])
        records = requests.filtered(lambda line: line.month == self.month and line.year ==
                                    self.year and line.company_id.id == self.company_id.id)
        for rec in records:
            line_line_id = self.env['training.plan.line'].create({
                'parent_id': self.id,
                'department_id': rec.department_id.id,
                'name_id': rec.name_id.id,
                'budget': rec.sum_payment,
                'company_id': rec.company_id.id,
                'emp_count': rec.emp_count
            })


class TrainingPlanLine(models.Model):
    _name = "training.plan.line"
    _inherit = ['mail.thread']
    _description = "training plan line"
    _order = 'department_id'

    parent_id = fields.Many2one('training.plan', 'Parent')
    name_id = fields.Many2one(
        'training.register', 'Сургалтын нэр', tracking=True)
    company_id = fields.Many2one('res.company', string='Компани',
                                 default=lambda self: self.env.user.company_id, readonly=True)
    department_id = fields.Many2one('hr.department', 'Хэлтэс', tracking=True)
    budget = fields.Float('Төсөв')
    emp_count = fields.Char('Хүний тоо')


class TrainingRegistration(models.Model):
    _name = "training.registration"
    _inherit = ['mail.thread']
    _description = "Training registration"

    name_id = fields.Many2one(
        'training.register', 'Сургалтын нэр', tracking=True)
    subject = fields.Char('Тайлбар', tracking=True)
    start_date = fields.Datetime('Эхлэх огноо', tracking=True)
    end_date = fields.Datetime('Дуусах огноо', tracking=True)
    create_date = fields.Date(
        'Үүсгэсэн огноо', default=fields.Datetime.now(), copy=False)
    cost = fields.Float('Нийт зардал', tracking=True)
    evaluation = fields.Float('Үнэлгээ', tracking=True)
    employee_cost = fields.Float(
        'Нэг хүнд ноогдох зардал', tracking=True, compute='_compute_cost', store=True)
    plan_employee_count = fields.Integer(
        'Сургалтанд хамрагдах хүний тоо', tracking=True, compute='_compute_plan_count', store=True)
    study_employee_count = fields.Integer(
        'Сургалтанд хамрагдсан хүний тоо', tracking=True, compute='_compute_count', store=True)
    teacher_evaluation = fields.Char('Сургалтын багш', tracking=True)
    time = fields.Char('Хугацаа', tracking=True)
    organization = fields.Char('Байгууллага', tracking=True)
    meaning = fields.Char('Агуулга', tracking=True)
    result = fields.Char('Үр дүн', tracking=True)
    country_name = fields.Char('Улс')
    is_plan = fields.Boolean('Төлөвлөгөөт эсэх ?')
    type = fields.Selection([('in', 'Дотоод'), ('out', 'Гадаад'),
                            ('abroad', 'Гадаад улсын')], 'Төрөл', tracking=True)
    department_id = fields.Many2one('hr.department', 'Хэлтэс', tracking=True)
    employee_id = fields.Many2one(
        'hr.employee', 'Бүртгэсэн ажилтан', tracking=True)
    plan_id = fields.Many2one('training.plan', 'Төлөвлөгөө', tracking=True)
    t_employee_ids = fields.Many2one('hr.employee', 'Ажилтнууд')
    not_employee_count = fields.Integer(
        'Тасалсан хүний тоо', readonly=True, compute='_compute_count', store=True)
    company_id = fields.Many2one('res.company', string='Компани')
    teacher_ids = fields.Many2many('hr.employee', string='Багш нар')
    line_ids = fields.One2many(
        'training.registration.line', 'parent_id', 'Ирц')
    state = fields.Selection([('draft', 'Ноорог'),
                              ('sent', u'Явагдаж буй'),
                              ('done', u'Дууссан'), ('cancel', u'Цуцлагдсан'),], 'Төлөв', readonly=True, default='draft', tracking=True, copy=False)

    def action_to_sent(self):
        self.write({'state': 'sent'})

    def action_to_done(self):
        self.write({'state': 'done'})

    def action_to_draft(self):
        self.write({'state': 'draft'})

    def action_to_cancel(self):
        self.write({'state': 'cancel'})

    @api.depends('line_ids')
    def _compute_plan_count(self):
        for obj in self:
            if obj.line_ids:
                obj.plan_employee_count = len(obj.line_ids)
            else:
                obj.plan_employee_count = 0

    @api.depends('line_ids')
    def _compute_count(self):
        for obj in self:
            if obj.line_ids:
                obj.study_employee_count = len(
                    obj.line_ids.filtered(lambda r: r.attendance == 'yes'))
                obj.not_employee_count = len(
                    obj.line_ids.filtered(lambda r: r.attendance == 'no'))
            else:
                obj.study_employee_count = 0
                obj.not_employee_count = 0

    @api.depends('cost', 'line_ids')
    def _compute_cost(self):
        for obj in self:
            if obj.cost and obj.line_ids:
                obj.employee_cost = obj.cost/len(obj.line_ids)
            else:
                obj.employee_cost = 0


class TrainingRegistrationLine(models.Model):
    _name = 'training.registration.line'
    _description = 'training registration line'

    parent_id = fields.Many2one('training.registration', 'Parent')
    t_employee_id = fields.Many2one('hr.employee', 'Ажилтны нэр')
    reason = fields.Char('Шалтгаан')
    score = fields.Float('Үнэлгээ')
    came = fields.Boolean('Ирсэн')
    dnt_come = fields.Boolean('Ирээгүй')
    job_id = fields.Many2one('hr.job', 'Албан тушаал')
    attendance = fields.Selection(
        [('yes', 'Тийм'), ('no', 'Үгүй')], 'Сургалтанд суусан эсэх')

    @api.onchange('t_employee_id')
    def _onchange_t_employee_id(self):
        if self.t_employee_id:
            self.job_id = self.t_employee_id.job_id.id


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    training_count = fields.Integer(
        string='Холбоотой сургалтын тоо', compute='_compute_train_count')

    def _compute_train_count(self):
        train = self.env['training.registration.line'].search(
            [('t_employee_id', '=', self.id),('attendance', '=', 'yes')])
        for emp in self:
            emp.training_count = len(train)

    def action_hr_training(self):
        train = self.env['training.registration.line'].search(
            [('t_employee_id', '=', self.id), ('attendance', '=', 'yes')])
        action = self.env["ir.actions.actions"]._for_xml_id(
            'mw_training.action_training_registration')
        action['domain'] = [('line_ids.t_employee_id', '=', self.id)]
        action['res_id'] = self.id
        if train:
            return action
