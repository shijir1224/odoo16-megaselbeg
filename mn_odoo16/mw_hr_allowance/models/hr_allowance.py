
from datetime import date, timedelta
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

DATE_FORMAT = "%Y-%m-%d"

class HrAllowanceName(models.Model):
    _name = 'hr.allowance.name'

    name = fields.Char(string='Нэр')
    type = fields.Char(string='Тэтгэмжийн төрөл')
    amount = fields.Float(string='Мөнгөн дүн')
    once_in_year = fields.Boolean(string='Жилд нэг удаа эсэх')

class HrAllowance(models.Model):
    _name = 'hr.allowance'
    _description = 'Hr allowance'
    _inherit = ['mail.thread']
    
    def name_get(self):
        res = []
        for item in self:
            if item.allowance_id or item.employee_id:
                res_name = ' [' + \
					item.allowance_id.name+']' + '' + item.employee_id.last_name [:1]+'.'+item.employee_id.name
                res.append((item.id, res_name))
            else:
                res.append(res_name)
        return res
	
    date = fields.Date(string='Огноо')
    amount = fields.Float(string='Мөнгөн дүн',related='allowance_id.amount',store=True)
    employee_id = fields.Many2one('hr.employee',string='Ажилтан')
    company_id = fields.Many2one('res.company',sring='Компани',related='employee_id.company_id')
    job_id = fields.Many2one('hr.job',string='Албан тушаал',related='employee_id.job_id', store=True)
    allowance_id = fields.Many2one('hr.allowance.name',string='Тэтгэмжийн нэр', store=True)
    type = fields.Char(string='Тэтгэмжийн төрөл',related='allowance_id.type', store=True)
    state = fields.Selection([('draft','Ноорог'), ('sent','Илгээсэн'),('done','Дууссан')], default='draft', string='Төлөв')
    request_id = fields.Many2one('payment.request', string='Төлбөрийн хүсэлт',readonly=True)


    def action_done(self):
        self.write({'state':'done'})
        for obj in self:
            payment_pool=self.env['payment.request']
            payment_narration=self.env['payment.request.narration'].search([('name','=','Тэтгэмж')])
            payment_flow = self.env['dynamic.flow'].search([('model_id.model', '=', 'payment.request')], order='sequence',limit=1)
            data_id = payment_pool.create({
                'narration_id': payment_narration.id,
                'description' : obj.type,
                # 'user_id' : obj.employee_id.user_id.id,
                'department_id' : obj.employee_id.department_id.id,
                'amount' : obj.amount,
                'flow_id': payment_flow.id,
                'allowance_id': obj.id
            })
            self.request_id = data_id.id

    def action_send(self):
        self.write({'state':'sent'})

    def action_draft(self):
        self.write({'state':'draft'})

    @api.onchange('employee_id')
    def _onchange_employee(self):
        total_year = timedelta(days=0)
        total_order = timedelta(days=0)
        year = 0
        month = 0
        year_order = 0
        month_order = 0
        today = date.today()
        emp = self.env['hr.employee'].search(
            [('id', '=', self.employee_id.id)], limit=1)
        hr_order = self.env['hr.order'].search(
            [('order_employee_id', '=', self.employee_id.id),('type', '=', 'type10'),('state', '=', 'done')])
        for item in self:
            if item.employee_id.engagement_in_company:
                start_date = emp.engagement_in_company
                dur = today - start_date
                total_year += dur
                year = (total_year.days/365)
                month = ((total_year.days-(total_year.days/365*365))/30)
                months = year * 12 + month
                if months < 6:
                    raise UserError(_('%s кодтой %s ажилтан ажилд ороод 6 сар болоогүй учир "%s" огноонд тэтгэмж авах боломжгүй.') %
                                    (item.employee_id.identification_id, item.employee_id.name, item.date))
            if hr_order.start_date:
                s_date = hr_order.start_date
                dur_order = today - s_date
                total_order += dur_order
                year_order = (total_order.days/365)
                month_order = ((total_order.days-(total_order.days/365*365))/30)
                months_order = year_order * 12 + month_order
                if months_order <6:
                    raise UserError(_('%s кодтой %s ажилтан сахилгын шийтгэлтэй учир "%s" огноонд тэтгэмж авах боломжгүй.') %
                                    (item.employee_id.identification_id, item.employee_id.name, item.date))
            # if months < 6 and months_order <12:
            #     raise UserError(_('%s кодтой %s ажилтан ажилд ороод 6 сар болоогүй мөн сахилгын шийтгэлтэй учир "%s" огноонд тэтгэмж авах боломжгүй.') %
            #                     (item.employee_id.identification_id, item.employee_id.name, item.date))
            
            

class HrEmployee(models.Model):
	_inherit = "hr.employee"

	allowance_count = fields.Integer(string='Холбоотой тэтгэмжийн тоо',compute='_compute_allowance_count' )

	def _compute_allowance_count(self):
		train = self.env['hr.allowance'].search([('employee_id','=',self.id)])
		for emp in self:
			emp.allowance_count = len(train)

	def action_hr_allowance(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id('mw_hr_allowance.hr_allowance_action')
		action['domain'] = [('employee_id','=',self.id)]
		action['res_id'] = self.id
		return action
      
class PaymentRequest(models.Model):
    _inherit = 'payment.request'

    allowance_id = fields.Many2one('hr.allowance', string='Тэтгэмж', readonly=True)