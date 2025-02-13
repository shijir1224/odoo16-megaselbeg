# -*- coding: utf-8 -*-

from odoo.osv import osv
from odoo import api, fields, models
from datetime import date, datetime, timedelta
from odoo.tools.translate import _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class PaymentRequestCreate(models.TransientModel):
	_name = 'payment.request.create'
	_description = 'Payment Request Create'

	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8,required=True)
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар',required=True)
	type = fields.Selection([
			('advance','Урьдчилгаа цалин'),
			('final','Сүүл цалин'),
		], string='Төрөл', required=True,index=True, change_default=True, default='final',)
	start_date = fields.Date('Эхлэх огноо')
	end_date = fields.Date('Дуусах огноо')
	company_id = fields.Many2one('res.company',string='Компани', default= lambda self: self.env['hr.employee'].sudo().search([("user_id", "=", self.env.user.id)], limit=1).company_id.id)
	sector_id = fields.Many2one('hr.department', string='Сектор', domain=[('type', '=', 'sector')], default= lambda self: self.env['hr.employee'].sudo().search([("user_id", "=", self.env.user.id), ("active", "=", True)], limit=1).sector.id)
	employee_id = fields.Many2one('hr.employee','Ажилтан')
	work_location_id = fields.Many2one('hr.work.location', string='Ажлын байршил')
	# sector_id = fields.Many2one('hr.department','Сектор', domain="[('type', '=', 'sector')]")

	def create_payment_request(self):
		query="""SELECT 
			sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='NETU')) as net
			FROM salary_order so
			LEFT JOIN salary_order_line line ON line.order_id=so.id
			LEFT JOIN hr_employee he ON he.id=line.employee_id
			WHERE so.year='%s' and so.month='%s'"""%(self.year,self.month)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		for rec in records:
			payment_pool=self.env['payment.request']
			payment_flow = self.env['dynamic.flow'].search([('model_id.model', '=', 'payment.request'),('company_id', '=', self.company_id.id),('is_salary', '=', True)], order='sequence',limit=1)
			data_id = payment_pool.create({
				'description' : '1',
				'user_id' : self.env.uid,
				# 'department_id' : self.preparatory.department_id.id,
				'amount' : rec['net'],
				'flow_id': payment_flow.id,
				'payment_type_mak':'7'
			})


