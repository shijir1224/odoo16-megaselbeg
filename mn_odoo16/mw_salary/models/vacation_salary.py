# -*- coding: utf-8 -*-
##############################################################################
#
#	ManageWall, Enterprise Management Solution	
#	Copyright (C) 2007-2014 ManageWall Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#

#	Email : puujee9005@gmail.com
#	Phone : 976 + 95900955
#
##############################################################################
from odoo.tools.translate import _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import logged, profile
import time, odoo.netsvc, odoo.tools, re
import logging
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID, api
_logger = logging.getLogger(__name__)
import itertools
import collections
from odoo import models, fields, api, _
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import UserError, ValidationError
from odoo.addons.auth_signup.models.res_partner import SignupError, now
import odoo
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from lxml import etree
from tempfile import NamedTemporaryFile
import os

import xlrd
from odoo.osv import osv
DATE_FORMAT = "%Y-%m-%d"

class VacationSalary(models.Model):
	_name = "vacation.salary"
	_inherit = ['mail.thread']
	_description = "vacation salary"

	def unlink(self):
		for obj in self:
			if obj.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(VacationSalary, self).unlink()
		
	name= fields.Char('Name', size=150)
	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8,required=True)
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар',required=True)
	s_date=fields.Date('Эхлэх огноо')
	e_date=fields.Date('Дуусах огноо')
	emp_balance_ids= fields.One2many('vacation.salary.line', 'vacation_id', 'Employee vacation')
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
	state= fields.Selection([('draft','Draft'),
				 ('done',u'done')], 'Status',readonly=True, default = 'draft', tracking=True, copy=False)
	type = fields.Selection([
			('advance','Advance'),
			('final','Final'),
		], string='Төрөл', required=True,index=True, change_default=True,
		default='final',)
	data = fields.Binary('Эксел файл')

	def done_action(self):
		for line in self.emp_balance_ids:
			line.employee_id.write({'before_shift_vac_date': self.e_date})
			line.write({'state': 'done'})
		return self.write({'state': 'done'})

	def draft_action(self):
		for line in self.emp_balance_ids:
			line.write({'state': 'draft'})
		return self.write({'state': 'draft'})

	def action_import(self):
		line_pool =  self.env['vacation.salary.line']
		if self.emp_balance_ids:
			self.emp_balance_ids.unlink()
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise osv.except_osv(u'Aldaa')
		book = xlrd.open_workbook(fileobj.name)
		
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise osv.except_osv(u'Aldaa')
		nrows = sheet.nrows
		for item in range(1,nrows):
			
			row = sheet.row(item)

			default_code = row[1].value
			sum_day = row[4].value
			sum_wage = row[5].value
			vacation_day = row[6].value
			
			employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code),('company_id', '=',self.company_id.id),('employee_type', '!=','resigned')])
			if employee_ids:
				line_id = line_pool.create({
							'employee_id':employee_ids.id,
							'vacation_id': self.id,
							'department_id':employee_ids.department_id.id,
							'job_id':employee_ids.job_id.id,
							'sum_day':sum_day,
							'sum_wage':sum_wage,
							'vacation_day':vacation_day,
							})
			else:
				raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))

	def create_plan_line(self):
		balance_data_pool =  self.env['vacation.salary.line']
		line_line_pool =  self.env['vacation.salary.detail']
		dep_pool = self.env['hr.department']
		balance_id = None
		month = None
		if self.emp_balance_ids:
			self.emp_balance_ids.unlink()
			if self.emp_balance_ids.detail_ids:
				self.emp_balance_ids.detail_ids.unlink()
		this_year_day=0
		vac_day=0
		year=0
		for obj in self:
			balance_id = obj.id
			
			query = """SELECT 
				hr.id as hr_id,
				line.department_id as dep_id,
				line.job_id as job_id,
				line.count_day as count_day,
				line.before_shift_vac_date as before_shift_vac_date,
				parent.id as p_id,
				hr.employee_type as employee_type,
				parent.start_date as s_date,
				parent.end_date as e_date
				FROM shift_vacation_schedule parent
				LEFT JOIN shift_vacation_schedule_line line ON line.schedule_id=parent.id
				LEFT JOIN res_company hc ON hc.id=parent.company_id
				LEFT JOIN hr_employee hr ON hr.id=line.employee_id
				WHERE parent.start_date>='%s' and parent.start_date<='%s' and hc.id=%s"""%(obj.s_date,obj.e_date,obj.company_id.id)
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			sum_day=0
			vacation_day=0
			dddd=0
			before_shift_vac_date = 0
			for record in records:
				emp_date_line = self.env['hr.employee'].search([('id','=',record['hr_id'])], limit=1)
				# print('=-=-==-=',sal_line_line)
				querysooa = """SELECT
					so.date_invoice as before_shift_vac_date
					FROM salary_order_line sol
					LEFT JOIN salary_order so on so.id=sol.order_id
					LEFT JOIN salary_order_line_line sll on sol.id=sll.order_line_id1
					WHERE sol.employee_id=%s  and  so.date_invoice<'%s' and sll.code='SOOA' and sll.amount>0
					ORDER BY so.date_invoice"""%(record['hr_id'],self.e_date)
				self.env.cr.execute(querysooa)
				sooa = self.env.cr.dictfetchall()
				if sooa:
					before_shift_vac_date = sooa[0]['before_shift_vac_date']
				else:
					before_shift_vac_date = emp_date_line.engagement_in_company
				query = """SELECT
					sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='WD')) as vacation_worked_day,
					sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='TOOTS')) as amount_tootsson
					FROM salary_order_line sol
					LEFT JOIN salary_order so on so.id=sol.order_id
					WHERE sol.employee_id=%s and sol.type='final' and so.date_invoice>'%s' and so.date_invoice<'%s'"""%(record['hr_id'],before_shift_vac_date,self.e_date)
				self.env.cr.execute(query)
				vacation = self.env.cr.dictfetchall()
				balance_data_id = balance_data_pool.create({
					'employee_id': record['hr_id'],
					'department_id':record['dep_id'],
					'job_id':record['job_id'],
					# 'date':record[''],
					'vacation_day':record['count_day'],
					'sum_day':vacation[0]['vacation_worked_day'],
					'sum_wage':vacation[0]['amount_tootsson'],
					'before_shift_vac_date':before_shift_vac_date,
					'vacation_id': balance_id,
					# 'employee_type':record[7],
					# 's_date':record[8],
					# 'e_date':record[9]
				})
				line_obj=balance_data_pool.browse(balance_data_id)
				for ll in line_obj:
					query1 = """SELECT
						(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='WD') as vacation_worked_day,
						(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=sol.id and cat.code='TOOTS') as amount_tootsson,
						sol.employee_id as employee_id,
						so.year as year,
						so.month as month
						FROM salary_order_line sol
						LEFT JOIN salary_order so ON so.id=sol.order_id
						WHERE sol.employee_id=%s and sol.type='final' and so.date_invoice>'%s' and so.date_invoice<'%s'
						ORDER BY so.year, so.month"""%(record['hr_id'],before_shift_vac_date,self.e_date)
					self.env.cr.execute(query1)
					vac = self.env.cr.dictfetchall()
					total_day=0
					for vc in vac:
							
						line_line_conf = line_line_pool.create({
								'employee_id':vc['employee_id'],
								'amount_tootsson':vc['amount_tootsson'],
								'year':vc['year'],
								'month':vc['month'],
								# 'worked_day':total,
								'worked_day':vc['vacation_worked_day'],
								'parent_id':ll.id.id,
								})

	def print_vacation_report(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'vacation_salary'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#E6E6E6')

		content_left = workbook.add_format()
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')
		
		content_left_no = workbook.add_format()
		content_left_no.set_font('Times new roman')
#		 content_left_no.set_text_wrap()
		content_left_no.set_font_size(9)
#		 content_left_no.set_border(style=1)
		content_left_no.set_align('left')

		center = workbook.add_format({'num_format': '###,###,###.##'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(9)	 
		center.set_align('right')
		center.set_border(style=1)
		
		center_bold = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
		center_bold.set_text_wrap()
		center_bold.set_font('Times new roman')
		center_bold.set_font_size(9)
		center_bold.set_align('right')
		center_bold.set_border(style=1)
		center_bold.set_bg_color('#E6E6E6')

		sheet = workbook.add_worksheet(u'Цалин')
		
		sheet.merge_range(2, 1, 2, 10, u'Амралтын цалин', h1)

		rowx=6
		sheet.merge_range(rowx, 0,rowx+2,0, u'№', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Ажилтны код', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),
		sheet.merge_range(rowx,4,rowx+2,4, u'Хэлтэс', theader),
		sheet.merge_range(rowx,5,rowx+2,5, u'Албан тушаал', theader),
		sheet.merge_range(rowx,6,rowx+2,6, u'Нийт ажилласан хоног', theader),
		sheet.merge_range(rowx,7,rowx+2,7, u'Нийт бодогдсон цалин', theader),
		sheet.merge_range(rowx,8,rowx+2,8, u'Нэг өдөрт ногдох цалин', theader),
		sheet.merge_range(rowx,9,rowx+2,9, u'Амрах хоног', theader),
		sheet.merge_range(rowx,10,rowx+2,10, u'Амралтын цалин', theader),
		sheet.merge_range(rowx,11,rowx+2,11, u'Эхлэх огноо', theader),
		sheet.merge_range(rowx,12,rowx+2,12, u'Дансны дугаар', theader),

		rowx+=3
		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 6)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 20)
		sheet.set_column('F:F', 30)
		sheet.set_column('G:G', 6)
		sheet.set_column('H:H', 10)
		sheet.set_column('I:I', 10)
		sheet.set_column('J:J', 6)
		sheet.set_column('K:K', 10)
		n=1
		for data in self.emp_balance_ids:
			sheet.write(rowx, 0, n,content_left)
			sheet.write(rowx, 1,data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)
			sheet.write(rowx, 4,data.employee_id.department_id.name,content_left) 
			sheet.write(rowx, 5,data.employee_id.job_id.name,content_left)
			sheet.write(rowx, 6,data.sum_day,content_left)
			sheet.write(rowx, 7,data.sum_wage,center)
			sheet.write(rowx, 8,data.one_day_wage,center)
			sheet.write(rowx, 9,data.vacation_day,content_left) 
			sheet.write(rowx, 10,data.wage_amount,center)
			sheet.write(rowx, 11,str(data.date),content_left)
			sheet.write(rowx, 12,data.employee_id.bank_account_number,content_left)
			rowx+=1
			n+=1
		sheet.merge_range(rowx, 0, rowx, 5, u'Нийлбэр', theader)
		sheet.write_formula(rowx, 6, "{=SUM(G%d:G%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 7, "{=SUM(H%d:H%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 8, "{=SUM(I%d:I%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 9, "{=SUM(J%d:J%d)}" % (10, rowx), center_bold)
		sheet.write_formula(rowx, 10, "{=SUM(K%d:K%d)}" % (10, rowx), center_bold)

		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
			'nodestroy': True,
		}


	def print_vacation_detail_report(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'vacation_salary'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		theader = workbook.add_format({'bold': 1,'num_format': '###,###,###.##'})
		theader.set_font_size(9)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')

		content_left = workbook.add_format()
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')
		
		content_right = workbook.add_format({'num_format': '###,###,###.##'})
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(9)
		content_right.set_border(style=1)
		content_right.set_align('center')
		
		center = workbook.add_format({'num_format': '###,###,###.##'})
		center.set_text_wrap()
		center.set_font('Times new roman')
		center.set_font_size(9)	 
		center.set_align('right')
		center.set_border(style=1)
		
		center_bold = workbook.add_format({'num_format': '###,###,###.##','bold': 1})
		center_bold.set_text_wrap()
		center_bold.set_font('Times new roman')
		center_bold.set_font_size(9)
		center_bold.set_align('right')
		center_bold.set_border(style=1)
		center_bold.set_bg_color('#c4d79b')

		sheet = workbook.add_worksheet(u'Амралтын Цалин')
		
		sheet.merge_range(2, 1, 2, 8, u'Амралтын цалин', h1)

		rowx=4
		n=1
		for data in self.emp_balance_ids:

			sheet.write(rowx,1, u'Ажилтны код', theader),
			sheet.write(rowx+1,1, u'Овог, Нэр', theader),
			sheet.write(rowx+2,1, u'Албан тушаал', theader),

			sheet.write(rowx,2, data.employee_id.identification_id, content_left),
			sheet.write(rowx+1,2, data.employee_id.name, content_left),
			sheet.write(rowx+2,2, data.employee_id.job_id.name, content_left),
			rowx += 2

			sheet.write(rowx+2,0, u'№', theader),
			sheet.write(rowx+2,1, u'Огноо', theader),
			sheet.write(rowx+2,2, u'Цалин', theader),
			sheet.write(rowx+2,3, u'Ажилласан хоног', theader),
			sheet.write(rowx+2,4, u'Нэг өдрийн цалин', theader),
			sheet.write(rowx+2,5, u'Амрах хоног', theader),
			sheet.write(rowx+2,6, u'Амралтын цалин', theader),
			month = 0 
			for ll in data.detail_ids:
				if ll.month =='90':
					month = 10
				elif ll.month =='91':
					month = 11
				elif ll.month =='92':
					month = 12
				else:
					month = ll.month

				sheet.write(rowx+3,0, n, content_right),
				sheet.write(rowx+3,1, str(ll.year)+'/'+str(month), content_right),
				sheet.write(rowx+3,2, ll.amount_tootsson, content_right),
				sheet.write(rowx+3,3, ll.worked_day,  content_right),
				
				rowx += 1
			sheet.write(rowx+3,0, '', theader),
			sheet.write(rowx+3,1, '', theader),
			sheet.write(rowx+3,2, data.sum_wage, theader),
			sheet.write(rowx+3,3, data.sum_day, theader),
			sheet.write(rowx+3,4,data.one_day_wage, theader),
			sheet.write(rowx+3,5, data.vacation_day, theader),
			sheet.write(rowx+3,6, data.wage_amount, theader),

			rowx += 5
		sheet.set_column('A:A', 5)
		sheet.set_column('B:C', 15)

		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
		return {
			'name': 'Export Result',
			'view_mode': 'form',
			'res_model': 'report.excel.output',
			'view_id': False,
			'type' : 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
			'nodestroy': True,
		}
class VacationSalaryLine(models.Model):
	_name = "vacation.salary.line"
	_description = "vacation salary line"

	def view_form(self):
		self.ensure_one()
		action = {
			'name':'Ээлжийн амралтын мөрүүд',
			'type':'ir.actions.act_window',
			'view_mode':'form',
			'res_model':'vacation.salary.line',
			'target':'new',
		}
		view = self.env.ref('mw_salary.view_vacation_salary_line_form')
		view_id = view and view.id or False
		action['view_id'] = view_id
		action['res_id'] = self.id
		return action

	employee_type = fields.Selection([
		('employee', 'Үндсэн ажилтан'),
		('student', 'Цагийн ажилтан'),
		('trainee', 'Туршилтын ажилтан'),
		('contractor', 'Гэрээт'),
		('longleave', 'Урт хугацааны чөлөөтэй'),
		('maternity', 'Хүүхэд асрах чөлөөтэй'),
		('resigned', 'Ажлаас гарсан'),
		('freelance', 'Бусад'),
		], string='Ажилтны төлөв',tracking=True)

	vacation_id=fields.Many2one('vacation.salary', 'Vacation',ondelete='cascade')
	year= fields.Integer(store=True, type='char', string='Year',tracking=True)
	employee_id= fields.Many2one('hr.employee', 'Employee', required=True)
	date=fields.Date('Огноо')
	sum_day= fields.Float('Sum day', digits=(3, 2))
	sum_wage= fields.Float('Sum wage', digits=(3, 2))
	vacation_niit_day= fields.Float('Нийт Амрах хоног', digits=(3, 2))
	vacation_day= fields.Float('Амрах хоног', digits=(3, 2))
	vacation_over_day= fields.Float('(1.5)Амрах хоног 1.5 бодох', digits=(3, 2))
	# vacation_day= fields.Float('Амрах хоног', digits=(3, 2))
	job_id= fields.Many2one('hr.job','Job')
	description= fields.Char('Description', size=150)
	balance_id=fields.Many2one('hour.balance', "Department hour balance",ondelete='cascade')
	department_id= fields.Many2one('hr.department', "Department")
	branch_id= fields.Many2one('res.branch', "Branch")
	one_day_wage =fields.Float(u'Нэг өдөрт ногдох цалин', digits=(3, 2),
		readonly=True, store=True, compute='_wage_day', tracking=True)
	wage_amount = fields.Float(u'Амралтын цалин', digits=(3, 2),
		readonly=True, store=True, compute='_wage_amount', tracking=True)
	wage_over_amount = fields.Float(u'(1.5) Амралтын цалин 1.5 бодох', digits=(3, 2),
		readonly=True, store=True, compute='_wage_over_amount', tracking=True)
	wage_sum_amount = fields.Float(u'Нийт амралтын цалин', digits=(3, 2),
		readonly=True, store=True,  tracking=True)
	wage_amount_advance = fields.Float(u'Урьдчилгаанд олгох', digits=(3, 2),tracking=True)
	before_shift_vac_date= fields.Date('Өмнөх ЭА огноо')
	s_date=fields.Date('Ажлын жил эхлэх огноо')
	e_date=fields.Date('Ажлын жил дуусах огноо')
	bier_edleh_date=fields.Date('Биеэр эдлэх огноо')
	detail_ids = fields.One2many('vacation.salary.detail','parent_id','Parent')
	state= fields.Selection([('draft','Draft'),
				('done',u'done')], 'Status',readonly=True, default = 'draft', tracking=True, copy=False)
	shi = fields.Float('НДШ', digits=(16, 2), readonly=True, compute='_compute_shi_pit')
	pit = fields.Float('ХАОАТ', digits=(16, 2), readonly=True, compute='_compute_shi_pit')
	amount_net = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute='_compute_amount_net')

	@api.depends('wage_amount','shi','pit')
	def _compute_amount_net(self):
		for obj in self:
			obj.amount_net = obj.wage_amount-obj.shi-obj.pit

	@api.depends('wage_amount')
	def _compute_shi_pit(self):
		for obj in self:
			cont_id = self.env['hr.contract'].search([('employee_id','=',obj.employee_id.id)],limit=1)
			if obj.wage_amount and cont_id.insured_type_id.shi_procent:
				if obj.wage_amount>6600000:
					obj.shi = 6600000*cont_id.insured_type_id.shi_procent/100
				else:
					obj.shi = obj.wage_amount*cont_id.insured_type_id.shi_procent/100
				if obj.wage_amount>6600000:
					obj.pit = (obj.wage_amount-6600000*cont_id.insured_type_id.shi_procent/100)*0.1
				else:
					obj.pit = (obj.wage_amount-obj.wage_amount*cont_id.insured_type_id.shi_procent/100)*0.1
			else:
				obj.shi = 0
				obj.pit = 0

	@api.depends('sum_wage','sum_day')
	def _wage_day(self):
		for obj in self:
			if obj.sum_day>0:
				obj.one_day_wage = obj.sum_wage/obj.sum_day
			else:
				obj.one_day_wage = 0


	@api.depends('one_day_wage','vacation_day')
	def _wage_amount(self):
		for obj in self:
			obj.wage_amount = obj.one_day_wage*obj.vacation_day

	@api.depends('one_day_wage','vacation_over_day')	
	def _wage_over_amount(self):
		for obj in self:
			obj.wage_over_amount = obj.one_day_wage*1.5*obj.vacation_over_day

	@api.onchange('wage_amount', 'wage_over_amount')
	def _vacation_sum(self):
		for obj in self:
			obj.wage_sum_amount = obj.wage_amount + obj.wage_over_amount

	 

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		self.department_id = self.employee_id.department_id.id
		self.job_id = self.employee_id.job_id.id
		self.date = self.vacation_id.e_date

	# ашиглахгүй real дээр ахивал устгана
	status = fields.Selection([('working','Үндсэн ажилтан'),('experiment','Туршилтын ажилтан'),
									 ('maternity','Хүүхэд асрах чөлөөтэй'),('timer','Цагийн ажилтан'),
									 ('longleave','Урт хугацааны чөлөөтэй'),('contract','Гэрээт'),('other','Бусад'),('resigned','Ажлаас гарсан'),('hire','Хөлсөөр ажиллах')],'Ажилтны төлөв')

class VacationSalaryDetail(models.Model):
	_name = "vacation.salary.detail"
	_description = "Vacation salart detail"

	employee_id = fields.Many2one('hr.employee','Ажилтан')
	year = fields.Char('Жил')
	month=fields.Selection([('1','January'), ('2','February'), ('3','March'), ('4','April'),
			('5','May'), ('6','June'), ('7','July'), ('8','August'), ('9','September'),
			('90','October'), ('91','November'), ('92','December')], u'Сар')
	amount_tootsson = fields.Float('Тооцсон цалин')
	worked_day = fields.Float('Ажилласан хоног')
	parent_id = fields.Many2one('vacation.salary.line','Parent')
