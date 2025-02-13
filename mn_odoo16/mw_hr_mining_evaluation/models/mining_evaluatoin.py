# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class HrMiningEvaluation(models.Model):
    _name = "hr.mining.evaluation"
    _descrition = 'KPI'
    _inherit = ['mail.thread']
    
    
    def unlink(self):
        for bl in self:
            if bl.state != 'draft':
                raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
        return super(HrMiningEvaluation, self).unlink()
    
    active = fields.Boolean(string='Active',default=True)
    name = fields.Char(string='Нэр')
    company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
    year = fields.Char('Жил',required=True)
    month = fields.Selection(
        [("1", "1 сар"),("2", "2 сар"),("3", "3 сар"),("4", "4 сар"),("5", "5 сар"),("6", "6 сар"),("7", "7 сар"),("8", "8 сар"),("9", "9 сар"),("90", "10 сар"),("91", "11 сар"),("92", "12 сар")],"Сар",required=True,)
    state = fields.Selection([('draft','Ноорог'),('sent','Илгээсэн'),('confirm','Хянасан'),('done_hr','Батласан'),('done','Нябо хүлээж авсан')],'Төлөв',default='draft',tracking=True)
    data = fields.Binary('Эксел файл')
    line_ids = fields.One2many('hr.mining.evaluation.line','parent_id',string='Үнэлгээ')
    mining_percent = fields.Float('Гүйцэтгэлд харгалзах урамшууллын хувь',required=True)
    hab_percent = fields.Float('ХАБЭАБО-ны урамшуулал тооцох хувь',required=True)
    subcontract_percent = fields.Float('Туслан гүйцэтгэгчийн хувь',required=False)

    def line_create(self):
        line_line_pool =  self.env['hr.mining.evaluation.line']
        if self.line_ids:
            self.line_ids.unlink()
        employee =  self.env['hr.employee'].search([('employee_type','!=','resigned')])
        for rec in employee:
            obj = self.env['hour.balance.dynamic.line'].search([('month', '=', self.month ), ('year', '=', self.year ),('parent_id.type', '=', 'final'), ('employee_id','=', rec.id), ('state', '=', 'confirm_ahlah')])
            line_line_id = line_line_pool.create({
                'employee_id':rec.id,
                'identification_id':rec.identification_id,
                'parent_id':self.id,
                'department_id':rec.department_id.id,
                'job_id':rec.job_id.id,
                'hour_to_work_month': self.hour_to_work_month,
            })

    def action_send(self):
        self.write({'state': 'sent'})
        
    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_done_hr(self):
        self.write({'state': 'done_hr'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})

class HrProjectEvaluationLine(models.Model):
    _name = "hr.mining.evaluation.line"
    _descrition = 'Hr Project Evaluation Line'
    _order = 'employee_id'

    employee_id = fields.Many2one('hr.employee','Ажилтан')
    identification_id = fields.Char(string='Ажилтны код')
    parent_id = fields.Many2one('hr.mining.evaluation','Parent')
    job_id = fields.Many2one('hr.job','Албан тушаал')
    department_id = fields.Many2one('hr.department','Хэлтэс')
    hour_to_work_month = fields.Float('Ажиллавал зохих цаг')
    kpi = fields.Float('KPI цаг')
    year = fields.Char('Жил',related='parent_id.year',store=True)
    month = fields.Selection("Сар",related='parent_id.month',store=True)
    mining_percent = fields.Float('Урамшуулал тооцох хувь (уул)')
    mining_kpi = fields.Float('Урамшуулал тооцох хувь',compute='compute_percent',store=True)
    hab_percent = fields.Float('ХАБЭАБО-ны урамшуулал тооцох хувь')
    hab_kpi = fields.Float('ХАБЭАБО-ны гүйцэтгэлд харгалзах хувь',compute='compute_percent',store=True)
    subcontract_percent = fields.Float('Туслан гүйцэтгэгчийн хувь')
    subcontract_kpi = fields.Float('Туслан гүйцэтгэгчийн хувь',compute='compute_percent',store=True)
    total_kpi = fields.Float('KPI',compute='compute_total',store=True)
    
    @api.depends('parent_id.mining_percent','parent_id.hab_percent','parent_id.subcontract_percent','mining_percent', 'hab_percent','subcontract_percent')
    def compute_percent(self):
        for item in self:
            if item.mining_percent:
                item.mining_kpi = item.mining_percent*(item.parent_id.mining_percent)/100
            if item.hab_percent:
                item.hab_kpi = item.hab_percent*(item.parent_id.hab_percent)/100
            if item.subcontract_percent:
                item.subcontract_kpi = item.subcontract_percent*(item.parent_id.subcontract_percent)/100
    
    @api.depends('mining_kpi', 'hab_kpi','subcontract_kpi')
    def compute_total(self):
        for item in self:
            item.total_kpi = item.subcontract_kpi + item.hab_kpi + item.mining_kpi