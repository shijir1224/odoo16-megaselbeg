# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import AccessError, UserError, ValidationError
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
import base64

# цалин өөрчлөх
class SalaryUpdate(models.Model):
	_name = 'salary.update'
	_description = "salary update"

	@api.depends('year','month')
	def _name_write(self):
		for obj in self:
			if obj.month=='90':
				month = '10'
			elif obj.month=='91':
				month = '11'
			elif obj.month=='92':
				month = '12'
			else:
				month = obj.month

			if obj.year and obj.month:
				obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u'сарын kpi урамшуулал'
			else:
				obj.name=''

	name = fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
	date = fields.Date('Огноо')
	end_date = fields.Date('Дуусах огноо')
	year = fields.Char('Жил')
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
	line_ids = fields.One2many('salary.update.line','parent_id','Lines')
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
	data = fields.Binary('Exsel file')
	file_fname = fields.Char(string='File name')
	state= fields.Selection([('draft','Ноорог'),
		('confirm_hr_director',u'Баталсан')], 'Төлөв',readonly=True, default = 'draft', tracking=True, copy=False)

	def action_confirm_hr_director(self):

		for line in self.line_ids:
			contract_id = self.env['hr.contract'].search([('employee_id', '=', line.employee_id.id)])
			contract_id.update({'wage':line.new_wage})
			line.write({'state':'confirm_hr_director'})
			
		self.write({'state': 'confirm_hr_director'})


	def create_update_line(self):
		line_pool =  self.env['salary.update.line']
		if self.line_ids:
			self.line_ids.unlink()
		for obj in self:
			query = """SELECT 
				hr.id as hr_id,
				hd.id as hd_id,
				ho.id as ho_id,
				ho.prize_date as prize_date,
				ho.wage as wage,
				hj.id as hj_id
				FROM hr_order ho
				LEFT JOIN hr_employee hr ON hr.id=ho.order_employee_id
				LEFT JOIN hr_department hd ON hd.id=hr.department_id
				LEFT JOIN hr_job hj ON hj.id=hr.job_id
				WHERE ho.starttime >='%s' and ho.starttime <='%s' and ho.is_wage_change =True"""%(obj.date,obj.end_date)
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			desc={}
			amount=0
			for rec in records:
				contract_id = self.env['hr.contract'].search([('employee_id','=',rec['hr_id'])],limit=1)
				line_data_id = line_pool.create({
					'department_id' : rec['hd_id'],
					'job_id' : rec['hj_id'],
					'employee_id' : rec['hr_id'],
					'date' : rec['prize_date'],
					'order_id' : rec['ho_id'],
					'old_wage':contract_id.wage,
					'new_wage':rec['wage'],
					'parent_id': obj.id,
					# 'description': desc
				})

class SalaryUpdateLine(models.Model):
	_name = 'salary.update.line'
	_description = " salary Line"

	# @api.depends('uramshuulal','evaluation')
	# def _compute_amount(self):
	#     for obj in self:
	#         obj.amount = obj.uramshuulal*obj.evaluation/100

	# @api.depends('amount')
	# def _compute_shi_pit(self):
	#     for obj in self:
	#         obj.shi = obj.amount*11.5/100
	#         obj.pit = (obj.amount-obj.amount*11.5/100)*0.1

	# @api.depends('amount','shi','pit')
	# def _compute_amounnet(self):
	#     for obj in self:
	#         obj.amount_net = obj.amount-obj.shi-obj.pit
	#         obj.amount_net_round = (obj.amount-obj.shi-obj.pit)//1000*1000

	parent_id = fields.Many2one('salary.update','Parent', ondelete='cascade')
	date = fields.Date('Огноо')
	employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
	department_id = fields.Many2one('hr.department','Хэлтэс')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	order_id = fields.Many2one('hr.order','Тушаал')
	old_wage = fields.Float('Хуучин цалин', digits=(16, 2))
	new_wage = fields.Float('Шинэ цалин', digits=(16, 2))
	state= fields.Selection([('draft','Ноорог'),
		('confirm_hr_director',u'Баталсан')], 'Төлөв',readonly=True, default = 'draft', tracking=True, copy=False)
	# evaluation = fields.Float('Үнэлгээ', digits=(16, 2))
	# amount = fields.Float('Тооцсон урамшууллын хэмжээ', digits=(16, 2), readonly=True, compute=_compute_amount)
	# shi = fields.Float('НДШ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
	# pit = fields.Float('ХХОАТ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
	# amount_net = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)
	# amount_net_round = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id.id
			self.job_id = self.employee_id.job_id.idd