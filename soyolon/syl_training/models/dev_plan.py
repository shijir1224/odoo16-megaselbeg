from odoo import api, fields, models, _

class PersonalDevPlan(models.Model):
    _name = 'personal.dev.plan'
    _descrition = 'Personal dev plan'
    _inherit = ['mail.thread']

    employee_id = fields.Many2one('hr.employee',string='Ажилтан')
    company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True, required=True)
    job_id = fields.Many2one('hr.job',string='Албан тушаал')
    department_id = fields.Many2one('hr.department',string='Хэлтэс')
    line_ids = fields.One2many('personal.dev.plan.line','parent_id',string='Төлөвлөгөө')

    @api.onchange('employee_id')
    def onchange_employee(self):
        self.department_id = self.employee_id.department_id.id
        self.job_id = self.employee_id.job_id.id

class PersonalDevPlanLine(models.Model):
    _name = 'personal.dev.plan.line'
    _descrition = 'Personal dev plan line'

    name = fields.Char(string='Хөгжүүлэх шаардлагатай ур чадвар')
    train_id = fields.Many2one(
        'training.register', 'Сургалтын сэдэв,чиглэл')
    date = fields.Char(string='Хугацаа')
    result = fields.Char(string='Гарах үр дүн')
    parent_id = fields.Many2one('personal.dev.plan',string='parent')
    
    