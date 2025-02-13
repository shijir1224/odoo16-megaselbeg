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
from operator import itemgetter, attrgetter
from lxml import etree
from odoo.tools.misc import logged, profile
import time, odoo.netsvc, odoo.tools, re
import odoo.addons.decimal_precision as dp
import logging
from odoo.tools import float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID, api
_logger = logging.getLogger(__name__)
import itertools
from lxml import etree
import collections
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from odoo.tools.safe_eval import safe_eval as eval
from tempfile import NamedTemporaryFile
import os

from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
import base64
from odoo.exceptions import UserError, ValidationError
from odoo.addons.auth_signup.models.res_partner import SignupError, now
import odoo
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF

import xlrd
from odoo.osv import osv
import pdfkit

DATE_FORMAT = "%Y-%m-%d"

class Department(models.Model):
	_inherit = "hr.department"

	analytic_account_id = fields.Many2one('account.analytic.account', 'Аналитик данс')
	account_expense_id = fields.Many2one('account.account', 'Цалингийн зардлын данс')
	account_allounce_expense_id = fields.Many2one('account.account', 'Нэмэгдэл цалингийн зардлын данс')
	account_shi_expense_id = fields.Many2one('account.account', 'НДШ зардлын данс')
	report_number = fields.Integer('Тайлангийн дараалал')

# class hour_balance_line(models.Model):
# 	_inherit = 'hour.balance.line'
		
# 	order_balance_line_id = fields.Many2one('salary.order.line', string='Setup line',
# 		index=True)
	
class payroll_fixed_allounce_deduction(models.Model):
	_name = "payroll.fixed.allounce.deduction"
	_description = "allounce deduction"
	
	def unlink(self):
		for obj in self:
			if obj.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(payroll_fixed_allounce_deduction, self).unlink()

	@api.depends('year','month')
	def _name_write(self):
		month=0
		for obj in self:
			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month
			if obj.year and obj.month:
				obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u'сар'
			else:
				obj.name=0

	name = fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8,required=True)
	# period_id = fields.Many2one('account.period', string='Period')
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар',required=True)
	department_id = fields.Many2one('hr.department', string='Хэлтэс')
	company_id= fields.Many2one('res.company', "Компани",required=True)
	employee_id = fields.Many2one('hr.employee', string='Нэмэх ажилтан')
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')

	setup_line = fields.One2many('payroll.fixed.allounce.deduction.line', 'setup_id', string='Setup Lines',
		readonly=True, states={'draft': [('readonly', False)]}, copy=True)	

	state = fields.Selection([
			('draft','Ноорог'),
			('confirm','Баталсан'),
			('cancel','Цуцалсан'),
		], string='Төлөв', index=True, readonly=True, default='draft',
		tracking=True, copy=False,)
	
	employee_type = fields.Selection([
		('employee', 'Үндсэн ажилтан'),
		('student', 'Цагийн ажилтан'),
		('trainee', 'Туршилтын ажилтан'),
		('contractor', 'Гэрээт'),
		('longleave', 'Урт хугацааны чөлөөтэй'),
		('maternity', 'Хүүхэд асрах чөлөөтэй'),
		('pregnant_leave', 'Жирэмсний амралт'),
		('resigned', 'Ажлаас гарсан'),
		('freelance', 'Бусад'),
		], string='Ажилтны төлөв',tracking=True)

	
	allounce_categ_id = fields.Many2one('hr.allounce.deduction.category', string='Нэмэгдэл, Суутгал')
	allounce_categ_ids = fields.One2many('hr.allounce.deduction.category', 'allounce_deduction_id', string='Нэмэгдэл, Суутгалууд')
	data = fields.Binary('Эксел файл')
	
	def add_allounce(self):
		cont = self.env['hr.contract']
		cont_ids=cont.search([]) 
		deduction_line = self.env['payroll.fixed.allounce.deduction.line.line'] 
		categ_pool = self.env['hr.allounce.deduction.category'] 
		ctx = dict(self._context)

		for emp in self.setup_line:
			vals = {
				'name':self.allounce_categ_id.name,
				'number':self.allounce_categ_id.number,
				'category_id':self.allounce_categ_id.id,
				'type':self.allounce_categ_id.type,
				'setup_line_id':emp.id
				}  
			move = deduction_line.with_context(ctx).create(vals)
		return True  

	def confirm_variable_create(self):
		cont = self.env['hr.contract']
		cont_ids=cont.search([]) 
		deduction_line = self.env['payroll.fixed.allounce.deduction.line'] 
		categ_pool = self.env['hr.allounce.deduction.category'] 
		categ_ids3=categ_pool.search([('fixed_type','in',('variable','hour_balance','tomyo','depend','fixed')),('salary_type','!=','tsag')]) 
		categ_ids=categ_pool.search([('fixed_type','in',('variable','hour_balance','tomyo','depend','fixed')),('salary_type','!=','tsag'),('work_location_id', '=', False)]) 
		categ_ids1=categ_pool.search([('salary_type','in',('turshilt','all'))]) 
		categ_ids2=categ_pool.search([('salary_type','in',('tsag','all'))]) 
		ctx = dict(self._context)
		if self.setup_line:
			self.setup_line.unlink()
			if self.setup_line.setup_line_line:
				self.setup_line.setup_line_line.unlink()
		for cont_id in cont_ids:
			if cont_id.employee_id.employee_type !='resigned':
				if cont_id.employee_id.company_id.id==self.company_id.id:
					line=[]
					if cont_id.employee_id.employee_type=='student':
						for categ_id in categ_ids2:
							line.append((0,0,{'name':categ_id.name,
								'number':categ_id.number,
													  'category_id':categ_id.id,
													  'is_advance':categ_id.is_advance,
													  'type':categ_id.type}))
					elif cont_id.employee_id.employee_type =='trainee':
						for categ_id in categ_ids1:
							line.append((0,0,{'name':categ_id.name,
								'number':categ_id.number,
													  'category_id':categ_id.id,
													  'is_advance':categ_id.is_advance,
													  'type':categ_id.type}))
					else:
						for categ_id in categ_ids:
							line.append((0,0,{'name':categ_id.name,
								'number':categ_id.number,
													  'category_id':categ_id.id,
													  'is_advance':categ_id.is_advance,
													  'type':categ_id.type}))
						# for categ_id in categ_ids3:
						# 	line.append((0,0,{'name':categ_id.name,
						# 		'number':categ_id.number,
						# 							  'category_id':categ_id.id,
						# 							  'is_advance':categ_id.is_advance,
						# 							  'type':categ_id.type}))
					vals = {
						'name': cont_id.employee_id.name,
						'ident_id': cont_id.employee_id.identification_id,
						'last_name': cont_id.employee_id.last_name,
						'setup_line_line': line,
						'employee_id': cont_id.employee_id.id,
						'setup_id': self.id,
					}		
					move = deduction_line.with_context(ctx).create(vals)
		return True	   
		
	def add_employee(self):
		cont = self.env['hr.contract']
		cont_ids=cont.search([]) 
		deduction_line = self.env['payroll.fixed.allounce.deduction.line'] 
		categ_pool = self.env['hr.allounce.deduction.category'] 
		categ_ids3=categ_pool.search([('fixed_type','in',('variable','hour_balance','tomyo','depend','fixed'))])	
		categ_ids=categ_pool.search([('fixed_type','in',('variable','hour_balance','tomyo','depend','fixed')),('work_location_id','=',False)])		
		categ_ids1=categ_pool.search([('salary_type','in',('turshilt','all'))]) 
		categ_ids2=categ_pool.search([('salary_type','in',('tsag','all'))])  

		ctx = dict(self._context)
		line=[]
		if self.employee_id.employee_type=='student':
			for categ_id in categ_ids2:
				line.append((0,0,{'name':categ_id.name,
									'number':categ_id.number,
									  'category_id':categ_id.id,
									  'type':categ_id.type}))
		elif self.employee_id.employee_type =='trainee':
			for categ_id in categ_ids1:
				line.append((0,0,{'name':categ_id.name,
					'number':categ_id.number,
									  'category_id':categ_id.id,
									  'type':categ_id.type}))
		else:
			for categ_id in categ_ids3:
				line.append((0,0,{'name':categ_id.name,
					'number':categ_id.number,
									  'category_id':categ_id.id,
									  'type':categ_id.type}))

		vals = {
			'ident_id': self.employee_id.identification_id,
			'last_name': self.employee_id.last_name,
			'name': self.employee_id.name,
			'setup_line_line': line,
			'employee_id': self.employee_id.id,
			'setup_id': self.id,
		}		
		move = deduction_line.with_context(ctx).create(vals)

	def action_import_inventory(self):
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
		
		rowi = 2
		data = []
		r=3
		for allounce in self.allounce_categ_ids:
			for item in range(1,nrows):
				row = sheet.row(item)
				default_code = row[0].value
				hour_to_work = row[3].value
				employee_id = self.env['hr.employee'].search([('identification_id','=',default_code)])
				for line in self.setup_line:
					if employee_id==line.employee_id:
						
						balance_data_pool =  self.env['payroll.fixed.allounce.deduction.line.line'].search([('setup_line_id','=',line.id)])
						
						for ll in balance_data_pool:

							if ll.category_id.id==allounce.id:
								balance_data_pool_update =  self.env['payroll.fixed.allounce.deduction.line.line'].search([('setup_line_id','=',line.id),('category_id','=',allounce.id)])
								balance_data_pool_update = balance_data_pool_update.update({'amount':hour_to_work})
			r+=1
		
		return True

	# def action_import_inventory(self):
	# 	fileobj = NamedTemporaryFile('w+b')
	# 	fileobj.write(base64.decodebytes(self.data))
	# 	fileobj.seek(0)
	# 	if not os.path.isfile(fileobj.name):
	# 		raise osv.except_osv(u'Aldaa')
	# 	book = xlrd.open_workbook(fileobj.name)
		
	# 	try :
	# 		sheet = book.sheet_by_index(0)
	# 	except:
	# 		raise osv.except_osv(u'Aldaa')
	# 	nrows = sheet.nrows
		
	# 	rowi = 2
	# 	data = []
	# 	r=0
		
	# 	for item in range(1,nrows):
	# 		row = sheet.row(item)
	# 		default_code = row[0].value
	# 		hour_to_work = row[3].value
	# 		employee_id = self.env['hr.employee'].search([('identification_id','=',default_code)])
	# 		for line in self.setup_line:
	# 			if employee_id==line.employee_id:
					
	# 				balance_data_pool =  self.env['payroll.fixed.allounce.deduction.line.line'].search([('setup_line_id','=',line.id)])
					
	# 				for ll in balance_data_pool:

	# 					if ll.category_id.id==self.allounce_categ_id.id:
	# 						balance_data_pool_update =  self.env['payroll.fixed.allounce.deduction.line.line'].search([('setup_line_id','=',line.id),('category_id','=',self.allounce_categ_id.id)])
	# 						balance_data_pool_update = balance_data_pool_update.update({'amount':hour_to_work})
		
	# 	return True		
	
	def confirm_action(self):
		return self.write({'state': 'confirm'})

	def action_draft(self):
		return self.write({'state': 'draft'})

	def action_cancel(self):
		return self.write({'state': 'cancel'})

	# ашиглахгүй агула дээр ахивал устгах
	status = fields.Selection([
			('employee','Үндсэн'),
			('trainee','Туршилтын'),
		], string='Ажилтны төлөв', index=True, tracking=True)
	
			
class payroll_fixed_allounce_deduction_line(models.Model):
	_name = "payroll.fixed.allounce.deduction.line"
	_description = "allounce deduction line"
	
	name = fields.Char(string='Нэр')
	last_name = fields.Char('Овог')
	ident_id = fields.Char('Хувийн дугаар')
	employee_location = fields.Selection([('office', u'Оффис'),('project',u'Уурхай'),('project_china',u'Уурхайн гадаад ажилтан'),('contract',u'Гэрээт')],'Ажлын байрны байршил')
	employee_id = fields.Many2one('hr.employee', string='Ажилтан',)
	setup_id = fields.Many2one('payroll.fixed.allounce.deduction', string='Setup',
		ondelete='cascade', index=True)
	
	setup_line_line = fields.One2many('payroll.fixed.allounce.deduction.line.line', 'setup_line_id', string='Setup Line Lines',copy=True)	
	
	def onchange_employee_id(self):
		self.name = self.employee_id.name
		self.ident_id = self.employee_id.identification_id
		self.last_name = self.employee_id.last_name
		self.employee_location = self.employee_id.employee_location
		
class payroll_fixed_allounce_deduction_line_line(models.Model):
	_name = "payroll.fixed.allounce.deduction.line.line"
	_description = "allounce deduction line line"
	_order = "number"
		
	number = fields.Integer('Дугаар')
	is_ndsh = fields.Boolean('НДШ тооцох эсэх')
	name = fields.Char(string='Нэр',required=True)
	category_id = fields.Many2one('hr.allounce.deduction.category', string='Ангилал',)
	setup_line_id = fields.Many2one('payroll.fixed.allounce.deduction.line', string='Setup line',
		ondelete='cascade', index=True)
	amount = fields.Float(string='Бодогдсон дүн', digits= dp.get_precision('Discount'),
		default=0.0)
	type = fields.Selection([
			('allounce','Нэмэгдэл'),
			('deduction','Суутгал'),
			('payroll','Бусад'),
			('debt','Өр'),
			('hour','Цаг'),
			('tootsson','Тооцсон'),
			('pitt','Хөнгөлөлт'),
			('ded_net','Гарт олгохоос хасах'),
			('add_net','гарт олгох нэмэгдүүлэх'),
			('no_shi','НДШ тооцохгүй'),
		], string='Төрөл', 
		default=lambda self: self._context.get('allounce'),
		tracking=True)
	every_month = fields.Boolean(string='Сарынх эсэх', default=True)
		
	order_line_id = fields.Many2one('salary.order.line', string='Order line',
		 index=True)
	order_line_id1 = fields.Many2one('salary.order.line', string='Order line',
		 index=True)
	is_advance = fields.Boolean(string='Урьдчилгааных эсэх')
	is_tree = fields.Boolean('Багана харагдах эсэх')

	def onchange_category_id(self):
		self.type = self.category_id.type
		self.name = self.category_id.name
		
class salary_order(models.Model):
	_name = "salary.order"
	_inherit = ['mail.thread']
	_description = "Salary"
	_order = "create_date desc"


	def download_data(self, data):
		print ('datadatadata ',data)
		html = data
		file_name = u"%s оны %s-р сар" % ( self.year, self.month)
		options = {
				'margin-top': '20mm',
				'margin-right': '1mm',
				'margin-bottom': '8mm',
				'margin-left': '1mm',
				'encoding': "UTF-8",
				'header-spacing': 2,
				'orientation': 'Landscape',
				'page-size': 'A3',  
				}
		html = self.encode_for_xml(html, 'ascii')
		output = BytesIO(pdfkit.from_string(html.decode('utf-8'), False, options=options))
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({
					'data': out,
					'name': file_name
		})
		return {
					'type':'ir.actions.act_url',
					'url':"web/content/?model=report.excel.output&id=" + str(excel_id.id) +"&filename_field=filename&download=true&field=data&filename=" +excel_id.name,
					'target':'new',
		}		
  # return self.export_report_pdf(data)

	def export_report_pdf(self,data):
		html = data #self.export_report_html_value()
		file_name = u"%s оны %s-р сар" % ( self.year, self.month)
		options = {
				'margin-top': '20mm',
				'margin-right': '1mm',
				'margin-bottom': '8mm',
				'margin-left': '1mm',
				'encoding': "UTF-8",
				'header-spacing': 2,
				'orientation': 'Landscape',
				'page-size': 'A3',  
				}
		html = self.encode_for_xml(html, 'ascii')
		output = BytesIO(pdfkit.from_string(html.decode('utf-8'), False, options=options))
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({
					'data': out,
					'name': file_name
		})
		return {
					'type':'ir.actions.act_url',
					'url':"web/content/?model=report.excel.output&id=" + str(excel_id.id) +"&filename_field=filename&download=true&field=data&filename=" +excel_id.name,
					'target':'new',
		}
			
	def encode_for_xml(self, unicode_data, encoding='ascii'):
		try:
			return unicode_data.encode(encoding, 'xmlcharrefreplace')
		except ValueError:
			return self._xmlcharref_encode(unicode_data, encoding)
			
	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(salary_order, self).unlink()

	def _compute_amount(self):
		self.amount_total = sum(line.amount_tootsson for line in self.order_line)

	@api.depends('year','month')
	def _name_write(self):
		month=0
		for obj in self:
			if obj.month=='90':
				month='10'
			elif obj.month=='91':
				month='11'
			elif obj.month=='92':
				month='12'
			else:
				month=obj.month
			if obj.year and obj.month:
				if obj.type=='advance':
					obj.name=obj.year+' ' + u'оны'+' '+month+u'-р сарын урьдчилгаа цалин'
				else:
					obj.name=obj.year+' ' + u'оны'+' '+month+u'-р сарын сүүл цалин'
			else:
				obj.name=''


	name = fields.Char(string=u'Нэр', index=True, readonly=True, store=True, compute=_name_write)
	type = fields.Selection([
			('advance','Урьдчилгаа цалин'),
			('final','Сүүл цалин'),
		], string='Төрөл', required=True,index=True, change_default=True, default='final',)

	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8, required=True, states={'draft': [('readonly', False)]})
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар', required=True, states={'draft': [('readonly', False)]})
	state = fields.Selection([
			('draft','Ноорог'),
			('send','НЯБО Илгээсэн'),
			('confirm_ez','ЭЗ Хянасан'),
			('confirm','Санхүү ГЗ баталсан'),
			('done','ГЗ баталсан'),
			('cancel','Цуцалсан'),
		], string='Төлөв', index=True, readonly=True, default='draft', tracking=True, copy=False)
	date_invoice = fields.Date(string='Огноо', readonly=True, required=True, states={'draft': [('readonly', False)]})
	branch_id= fields.Many2one('res.branch', "Салбар")
	company_id = fields.Many2one('res.company', string='Компани', change_default=True,
		required=True, readonly=True, states={'draft': [('readonly', False)]},
		default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
	# hr_company_id = fields.Many2one('hr.company','Байршил')

	order_line = fields.One2many('salary.order.line', 'order_id', string='Salary Lines',
		readonly=True, states={'draft': [('readonly', False)]}, copy=True)
	order_line_net = fields.One2many('salary.order.line.net', 'order_id', string='Salary Lines Net',
		readonly=True, states={'draft': [('readonly', False)]}, copy=True)
	
# so_line_line_rltd = fields.One2many('salary.order.line.line',string='Setup Line Lines',related="order_line.so_line_line", related_sudo=True)
	so_line_line_rltd = fields.Char('HA')
	
	# def _compute_so_lines(self):
	# 	for item in self:
	# 		ids=self.env['salary.order.line.line']
	# 		for l in item.order_line:
	# 			for ll in l.so_line_line:
	# 				ids+=ll
	# 		item.so_line_line_rltd = ids
	
 # before_crm_call_ids = fields.One2many('crm.call', related='partner_id.crm_call_ids', string='Дуудлагууд', readonly=True, related_sudo=True)
	
	amount_total = fields.Float(string='Нийлбэр', digits=(0, 0),
		readonly=True, compute='_compute_amount')

	journal_id = fields.Many2one('account.journal', string='Журнал')
	
	account_id = fields.Many2one('account.account', string='Зардлын данс')
	account_payable_id = fields.Many2one('account.account', string='Өглөгийн данс')
	account_clearing_id = fields.Many2one('account.account', string='Clearing Account')
	account_partner_id = fields.Many2one('res.partner', string='Accounting partner')

	account_ndsh_id = fields.Many2one('account.account', string='НДШ өглөгийн данс')
	account_ndsh1_id = fields.Many2one('account.account', string='ХХОАТ өглөгийн данс')
	account_pit_payable_id =fields.Many2one('account.account', string='ХХОАТ өглөгийн данс')
	ndsh_partner_id = fields.Many2one('res.partner', string='НДШ Харилцагч')
	pit_partner_id = fields.Many2one('res.partner', string='ХХОАТ Харилцагч')
	salary_conf_id=fields.Many2one('salary.account.conf', 'Дансны тохиргоо')


	# invoice_id = fields.Many2one('account.invoice', string='Invoice',readonly=True)

	bndsh_move_id = fields.Many2one('account.move', string='БНДШ бичилт',readonly=True)
	partner_id = fields.Many2one('res.partner', string='Харилцагч')
	move_id = fields.Many2one('account.move', string='Цалингийн бичилт',)
	ndsh_move_id = fields.Many2one('account.move', string='НДШ бичилт', readonly=True)
	lag_move_id = fields.Many2one('account.move', string='Lag move', readonly=True)
	or_move_id = fields.Many2one('account.move', string='Авлага, өглөгийн бичилт',readonly=True)
	move_id = fields.Many2one('account.move', string='Цалингийн бичилт',readonly=True)
	uram_move_id = fields.Many2one('account.move', string='Урамшууллын бичилт',readonly=True)
	zorchil_move_id = fields.Many2one('account.move', string='Зөрчлийн бичилт',readonly=True)
	unaa_move_id = fields.Many2one('account.move', string='Унааны бичилт',readonly=True)
	department_id = fields.Many2one('hr.department', 'Хэлтэс')
	salary_type = fields.Selection([('month','Сараар'),('day','Өдрөөр'),('hour','Цагаар'),('garaa','Гараагаар')],'Цалингийн төрөл')

	done_director = fields.Many2one('hr.employee', 'Батлах')
	compute_controller = fields.Many2one('hr.employee', 'Хянах')
	preparatory = fields.Many2one('hr.employee', 'Бодох')
	employee_count = fields.Integer(u'Ажилтны тоо', compute='_count_employee', store=True, readonly=True)
	mail_department_id = fields.Many2one('hr.department','Хэлтэс')
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
	tree_month_date = fields.Date('3 сарын дундаж бодох огноо')
	year_sum_date = fields.Date('Жилийн цалин бодох огноо', default=time.strftime('%Y-01-01'))
	data = fields.Binary("Эксел файл")
	is_resgister = fields.Boolean('Регистрээр импортлох')


	@api.onchange('work_location_id', 'type')
	def _onchange_account(self):
		obj=[]
		if self.work_location_id:
			obj = self.env['salary.account.conf'].search([('company_id', '=', self.company_id.id), ('work_location_id','=', self.work_location_id.id)], limit=1)
		else:
			obj = self.env['salary.account.conf'].search([('company_id', '=', self.company_id.id)], limit=1)

		if obj:
			self.journal_id = obj.journal_id.id
			self.partner_id = obj.partner_id.id
			self.account_payable_id = obj.account_payable_id.id
			self.account_ndsh_id = obj.account_ndsh_id.id
			self.account_pit_payable_id = obj.account_pit_payable_id.id
			self.ndsh_partner_id = obj.ndsh_partner_id.id
			self.pit_partner_id = obj.pit_partner_id.id
		else:
			self.journal_id = False
			self.partner_id = False
			self.account_payable_id = False
			self.account_ndsh_id =False
			self.account_pit_payable_id = False
			self.ndsh_partner_id = False
			self.pit_partner_id = False


	def action_import_salary(self):
		salary_pool =  self.env['salary.order.line']
		salary_line_pool =  self.env['salary.order.line.line']
		salary_line1_pool =  self.env['salary.order.line.line1']

		
		if self.order_line:
			self.order_line.unlink()
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
		ncols = sheet.ncols
		for item in range(5,nrows):
			row = sheet.row(item)
			default_code = row[1].value
			day_to_work_month = row[5].value
			hour_to_work_month = row[6].value
			
			if self.is_resgister==True:
				employee_register_ids = self.env['hr.employee'].search([('passport_id','=',default_code)])
				if employee_register_ids:
					salary_data_ids = salary_pool.create({'employee_id':employee_register_ids.id,
								'name':employee_register_ids.name,
								'ident_id':employee_register_ids.identification_id,
								'last_name':employee_register_ids.last_name,
								'year':self.year,
								'month':self.month,
								'order_id': self.id,
								})
					for dd in salary_data_ids:
						# дугаарлалт авах 7 буюу H багана
						col = 9
						#  дугаарлалт авах 5 мөр
						rowh = sheet.row(4)
						for ncol in range(9,ncols):
							number = rowh[col].value
							conf_pool =  self.env['hr.allounce.deduction.category'].search([('number','=',number)],limit=1)
							if conf_pool:
								salary_line_pool = salary_line_pool.create({
										'order_line_id1':dd.id,
										'category_id':conf_pool.id,
										'amount':row[col].value,
										})
								salary_line1_pool = salary_line1_pool.create({
										'order_line_id2':dd.id,
										'name':row[col].value,
										})
								number = []
								col +=1
								item +=1
							else:
								raise UserError(_('%s дугаартай цагийн тохиргоо хийгдээгүй байна.')%(number))
						net = 0	
						for sll in salary_line_pool:
							if sll.category_id.code in ('NETU','NET'):
								net += sll.amount
						dd.amount_net = net
				else:
					raise UserError(_('%s регистрийн дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))
			else:
				employee_ids = self.env['hr.employee'].search([('id','=',default_code)])
				if employee_ids:
					salary_data_ids = salary_pool.create({'employee_id':employee_ids.id,
								'name':employee_ids.name,
								'ident_id':employee_ids.identification_id,
								'last_name':employee_ids.last_name,
								'year':self.year,
								'month':self.month,
								'order_id': self.id,
								# 'employee_type':employee_ids.employee_type,
								# 'day_to_work_month':day_to_work_month,
								# 'hour_to_work_month':hour_to_work_month,
								})
					for dd in salary_data_ids:
						# дугаарлалт авах 7 буюу H багана
						col = 9
						#  дугаарлалт авах 5 мөр
						rowh = sheet.row(4)
						for ncol in range(9,ncols):
							number = rowh[col].value
							conf_pool =  self.env['hr.allounce.deduction.category'].search([('number','=',number)],limit=1)
							if conf_pool:
								salary_line_pool = salary_line_pool.create({
										'order_line_id1':dd.id,
										'category_id':conf_pool.id,
										'amount':row[col].value,
										})
								salary_line1_pool = salary_line1_pool.create({
										'order_line_id2':dd.id,
										'name':row[col].value,
										})
								number = []
								col +=1
								item +=1
							else:
								raise UserError(_('%s дугаартай цагийн тохиргоо хийгдээгүй байна.')%(number))
						net = 0	
						for sll in salary_line_pool:
							if sll.category_id.code in ('NETU','NET'):
								net += sll.amount
						dd.amount_net = net

						
						# toots = 0	
						# for sll in salary_line_pool:
						# 	if sll.category_id.code in ('URID','TOOTS'):
						# 		toots += sll.amount
						# dd.amount_tootsson = toots
				else:
					raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))
	

	# @api.depends('amount_tootsson','amount_deduction')
	# def _compute_amount_net(self):
	
	# 	for obj in self:
	# 		avlaga=0
	# 		for line in obj.so_line_line:
	# 			if line.category_id.code=='OR':
	# 				avlaga+=line.amount
	# 		obj.amount_net=obj.amount_tootsson-obj.amount_deduction+avlaga

	def action_salary_employee_create(self):
		line_line_pool=self.env['employee.salary.mine'].sudo()
		query='''SELECT 
					hj.name,
					he.id as he_id, 
					line.basic as basic,
					line.amount_tootsson as amount_tootsson,
					line.amount_net as amount_net,
					line.amount_deduction as amount_deduction,
					line.id as line_id,
					hc.wage as wage,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='DTW') as dtw,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='HTW') as htw,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='DAY') as day,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='HOUR') as hour,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PAY') as pay,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='URAM') as uram,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PHONE') as phone,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SOOA') as sooa,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='FOOD') as food,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='OVER') as over,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='OVERALL') as overall,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='YEARALL') as yearall,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='OTHER') as other,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SUMOTHER') as sumother,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SHI') as shi,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PITDIS') as pitdis,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PIT') as pit,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='URDISU') as urdisu,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SUU') as suu,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PHONESUU') as phonesuu,
					(select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='OTERSUU') as othersuu
					FROM salary_order so
					LEFT JOIN salary_order_line line ON line.order_id=so.id
					LEFT JOIN hr_employee he ON he.id=line.employee_id
					LEFT JOIN hr_job hj ON hj.id=he.job_id
					LEFT JOIN hr_contract hc ON hc.employee_id=he.id
					WHERE so.id=%s
					ORDER BY so.id'''%(self.id)
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		for rec in records:
			line_line_conf = line_line_pool.create({
					'employee_id':rec['he_id'],
					'year':self.year,
					'month':self.month,
					'wage':rec['wage'],
					'day_to_work':rec['dtw'],
					'hour_to_work':rec['htw'],
					'worked_day':rec['day'],
					'worked_hour':rec['hour'],
					'irts_tootsson':rec['pay'],
					'guitsetgel_tootsson':rec['uram'],
					'phone_allounve':rec['phone'],
					'vacation':rec['sooa'],
					'food':rec['food'],
					'overtime_hour':rec['over'],
					'overtime_wage':rec['overall'],
					'long_wage':rec['yearall'],
					'other_nemegdel':rec['other'],
					'sum_nemegdel':rec['sumother'],
					'amount_tootsson':rec['amount_tootsson'],
					'shi':rec['shi'],
					'pit_discount':rec['pitdis'],
					'pit':rec['pit'],
					'uridchilgaa_suutgal':rec['urdisu'],
					'niit_suutgal':rec['amount_deduction'],
					'phone':rec['phonesuu'],
					'avlaga':rec['suu'],
					'other_suutgal':rec['othersuu'],
					'jinhene_olgoh':rec['amount_net'],				
				})

		return True

	def action_send_mail(self):
		for obj in self:
			obj.order_line.action_send_mail_emp()
		return True

	def _count_employee(self):
		for item in self.order_line:
			self.employee_count+=1

	def send_action(self):
		return self.write({'state': 'send'})

	def confirm_ez_action(self):
		return self.write({'state': 'confirm_ez'})

	def confirm_action(self):
		return self.write({'state': 'confirm'})
	
	def done_action(self):
		return self.write({'state': 'done'})

	def draft_action(self):
		return self.write({'state': 'draft'})

	def compute_create(self, context=None):
		def _sum_salary_category(tomyo, code, line):
			localdict2 = {}
			for l in line.so_line_line:
				localdict2[code] = l.amount

			return localdict2

		cont = self.env["hr.contract"]
		order_line = self.env["salary.order.line"]
		salary_order = self.env["salary.order"]
		line_line_pool = self.env["payroll.fixed.allounce.deduction.line.line"]
		line_pool = self.env["payroll.fixed.allounce.deduction.line"]
		allounce_deduction_pool = self.env["payroll.fixed.allounce.deduction"]
		balance_pool = self.env["hour.balance.dynamic.line.line"]
		balance_vacation_pool = self.env["vacation.salary.line"]
		employee_pool = self.env["hr.employee"]
		iswrite = False
		if self.order_line:
			self.order_line.unlink()
			if self.order_line.so_line_line:
				self.order_line.so_line_line.unlink()
		if self.type == "final":
			if self.company_id:
				allounce_deductions = allounce_deduction_pool.search([("year", "=", self.year), ("month", "=", self.month)])
				setups = []
				allounce_deduction_ids = allounce_deductions.mapped("id")
				self_ads = self.search([("month", "=", self.month)])
				self_ad_ids = self_ads.mapped("id")
				

				ctx = dict(self._context)

				if self.work_location_id:
					recs_balance_id = self.env["hour.balance.dynamic.line"].search([("parent_id.year", "=", self.year),("parent_id.month", "=", self.month),
									("parent_id.type", "=", 'final'),("parent_id.state", "=", 'done'),
									("parent_id.work_location_id", "=", self.work_location_id.id)])
				else:
					recs_balance_id = self.env["hour.balance.dynamic.line"].search([("parent_id.year", "=", self.year),
									("parent_id.type", "=", 'final'),("parent_id.month", "=", self.month)])
				n=1
				for balance in recs_balance_id:
					balance_id = self.env["hour.balance.dynamic.line"].search([("id", "=", balance.id)])
					balance_line_ids = self.env["hour.balance.dynamic.line.line"].search([("parent_id", "=", balance.id)])
					cont_ids = cont.search([("employee_id", "=", balance.employee_id.id)])
					punishment_id = self.env["hr.order"].search([("order_employee_id", "=", balance.employee_id.id),("start_date", "<=", self.date_invoice),
								("end_date", ">=", self.date_invoice),("deduct", ">", 0)],limit=1)

					if len(cont_ids) == 1:
						cont_id = cont_ids[0]
					else:
						raise Warning(("%s кодтой ажилтны гэрээ байхгүй эсвэл олон бүртгэгдсэн байна"% (balance.employee_id.identification_id)))
					rate_id = self.env["res.currency.rate"].search([("currency_id", "=", cont_id.res_currency_id.id),("name", "<=", self.date_invoice),],order="name desc",)
					rate = 0
					if rate_id:
						rate = rate_id[0].rate
						basic = cont_id.wage * rate
					else:
						basic = cont_id.wage
					insured_id = cont_id.insured_type_id
					query = """select 
						sum(ll.amount)
						from payroll_fixed_allounce_deduction_line l
						left join payroll_fixed_allounce_deduction_line_line ll on ll.setup_line_id=l.id
						left join payroll_fixed_allounce_deduction al on al.id=l.setup_id
						where ll.type='debt' and l.employee_id=%s and al.year='%s' and al.month='%s'""" % (cont_id.employee_id.id,self.year,self.month,)
					self.env.cr.execute(query)
					records = self.env.cr.fetchall()
					pit_disc = records[0][0]

					query = """SELECT sum(amount) as tree_wage 
						FROM salary_order_line_line ll 
						LEFT JOIN salary_order_line sol ON sol.id=ll.order_line_id1  
						LEFT JOIN salary_order so ON so.id=sol.order_id 
						LEFT JOIN hr_allounce_deduction_category conf ON conf.id=ll.category_id 
						WHERE sol.employee_id=%s AND  so.date_invoice >= '%s' and so.date_invoice<'%s' AND conf.is_average =True AND so.type ='final'   
						GROUP BY sol.employee_id """ % (cont_id.employee_id.id, self.tree_month_date, self.date_invoice,)
					self.env.cr.execute(query)
					self.env.cr.execute(query)
					treemonth = self.env.cr.dictfetchall()
					tree_wage = 0
					for tr in treemonth:
						tree_wage = tr["tree_wage"]

					query = """SELECT sum(amount) as tree_hour 
						FROM salary_order_line_line ll 
						LEFT JOIN salary_order_line sol ON sol.id=ll.order_line_id1  
						LEFT JOIN salary_order so ON so.id=sol.order_id 
						LEFT JOIN hr_allounce_deduction_category conf ON conf.id=ll.category_id 
						WHERE sol.employee_id=%s AND so.date_invoice >= '%s' and so.date_invoice<'%s' AND conf.is_average_hour =True AND so.type ='final'   
						GROUP BY sol.employee_id """ % (cont_id.employee_id.id, self.tree_month_date, self.date_invoice,)
					self.env.cr.execute(query)
					self.env.cr.execute(query)
					treemonth = self.env.cr.dictfetchall()
					tree_hour = 0
					for tr in treemonth:
						tree_hour = tr["tree_hour"]

					tree_average_wage = 0
					if tree_wage and tree_hour:
						tree_average_wage = tree_wage/tree_hour

					vals = {
						"name": cont_id.employee_id.name,
						"number": n,
						"last_name": cont_id.employee_id.last_name,
						"ident_id": cont_id.employee_id.identification_id,
						"year": self.year,
						"month": self.month,
						"day_to_work": balance_id.day_to_work_month,
						"hour_to_work": balance_id.hour_to_work_month,
						"date": self.date_invoice,
						"type": self.type,
						"insured_type_id": insured_id.id,
						"employee_id": cont_id.employee_id.id,
						"basic": basic,
						"pit_discount": pit_disc,
						"pit_procent": cont_id.insured_type_id.shi_procent,
						"order_id": self.id,
						"contract_id": cont_id.id,
						"email_address": cont_id.employee_id.work_email,
						'punishment_procent':punishment_id.deduct,
						# 'tree_month_average_wage': cont_id.average_wage,
						"tree_month_average_wage": tree_average_wage,
						"tree_month_sum_hour": tree_hour,
						"tree_month_sum_wage": tree_wage,
						"is_pit": cont_id.is_pit,
					}
					if not iswrite:
						move = order_line.with_context(ctx).create(vals)
					else:
						move = iswrite
					balance_id.write({"balance_line_id": move.id})
					for bal_l_l in balance_line_ids:
						balance_line_id = self.env[
							"hour.balance.dynamic.line.line"
						].search([("id", "=", bal_l_l.id)])
						balance_line_id.write({"order_balance_line_id": move.id})
					# Нэмэгдэл суутгал
					lines = line_pool.search([("employee_id", "=", cont_id.employee_id.id),
							("setup_id", "in", allounce_deduction_ids),])
					line_line_ids = []
					for cl in lines:
						for l in cl.setup_line_line:
							if not l.category_id.is_advance:
								v = {"order_line_id1": move.id}
								v["name"] = l.name
								v["is_tree"] = l.category_id.is_tree
								v["category_id"] = l.category_id.id
								v["every_month"] = l.every_month
								v["type"] = l.type
								
								if l.category_id.fixed_type == "hour_balance":
									all_conf = self.env['hr.allounce.deduction.category'].search([('id','=',l.category_id.id)])
									conf_ids = all_conf.mapped('hour_ids')
									all_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																	('parent_id.parent_id.month','=',self.month),
																	('parent_id.parent_id.type','=','final'),
																	('parent_id.employee_id','=',balance.employee_id.id),
																	('conf_id','in',conf_ids.ids)])
									conf_min_ids = all_conf.mapped('hour_minus_ids')
									all_min_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																	('parent_id.parent_id.month','=',self.month),
																	('parent_id.parent_id.type','=','final'),
																	('parent_id.employee_id','=',balance.employee_id.id),
																	('conf_id','in',conf_min_ids.ids)])
									conf_is_ids = all_conf.mapped('hour_is_ids')
									all_is_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																	('parent_id.parent_id.month','=',self.month),
																	('parent_id.parent_id.type','=','final'),
																	('parent_id.employee_id','=',balance.employee_id.id),
																	('conf_id','in',conf_is_ids.ids)])

									hour_ids = all_hours.mapped('conf_id')
									hour_sum = sum(all_hours.mapped('hour'))
									is_hour = sum(all_is_hours.mapped('hour'))
									hour_minus = sum(all_min_hours.mapped('hour'))
									localdict={'move':move,'hour':hour_sum,'is_hour':is_hour,'hour_minus':hour_minus,'result':None}
									tomyo=l.category_id.tomyo.replace(u'үндсэн цалин','move.basic')
									if '/' in tomyo:
										try:
											eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  
										except ValueError:
											raise Warning((u'%s ажилтны %s ийн цагийн балансын мэдээлэл дээр 0 өгөгдөл орсоноос алдаа гарлаа'%(cl.employee_id.name,l.category_id.name)))
									else:
										eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  

									v['amount']=localdict['result']

								if l.category_id.fixed_type == "tomyo":
									localdict = {"cl": cl, "move": move, "result": None}
									"resutl=basic*0.1 гм байна"
									tomyo = l.category_id.tomyo.replace("үндсэн цалин", "move.basic")
									if "/" in tomyo:
										try:
											eval("%s" % (tomyo), localdict, mode="exec", nocopy=True,)
										except ValueError:
											raise Warning(("%s ажилтны %s ийн томъёонд 0 өгөгдөл орсоноос алдаа гарлаа."% (cl.employee_id.name,l.category_id.name,)))
									else:
										eval("%s" % (tomyo),localdict,mode="exec",nocopy=True,)
									v["amount"] = localdict["result"]
								if l.category_id.fixed_type == "depend":
									depend_ids = []
									for i in l.category_id.depend_ids:
										depend_ids.append(i.id)

									line_lines = order_line.search([("order_id.year", "=", self.year),
											("order_id.month", "=", self.month),
											("order_id.type", "=", "advance"),
											("employee_id", "=", move.employee_id.id),])
									v["amount"] = line_lines.amount_net
								if l.category_id.fixed_type == "fixed":
									v["amount"] = l.amount

								if l.category_id.code == "SOOA":
									balance_vacation_lines = (balance_vacation_pool.search([("vacation_id.e_date","=",self.date_invoice,),
												("employee_id", "=", cl.employee_id.id),]))
									for balance_vacation in balance_vacation_lines:
										v["amount"] = balance_vacation.wage_amount

								if l.category_id.code == "XCTA":
									list_lines = self.env['list.wage.line'].search([("parent_id.year","=",self.year),("parent_id.month","=",self.month),("employee_id", "=", cl.employee_id.id)])
									for lis in list_lines:
										if lis.nd_wage!=0:
											v["amount"] = lis.nd_wage
										else:
											v['amount'] = 0

								if l.category_id.code == "XCTACOM":
									list_lines_com = self.env['list.wage.line'].search([("parent_id.year","=",self.year),("parent_id.month","=",self.month),("employee_id", "=", cl.employee_id.id)])
									for lisc in list_lines_com:
										if lisc.company_wage!=0:
											v["amount"] = lisc.company_wage
										else:
											v['amount'] = 0

								if l.category_id.code == "UJ":
									v["amount"] = cont_id.long_year_wage
								line_ids = order_line.search([("employee_id", "=", cont_id.employee_id.id),
										("order_id.month", "=", self.month),],limit=1,)

								move.so_line_line.create(v)

								v1 = {"order_line_id2": move.id}
								v1['name']=v["amount"]
								v1['display_name']=self.too(v["amount"])
								move.so_line_line1.create(v1)
								l.write(v)
					n+=1
			else:
				raise Warning(("Компани сонгоно уу!"))
		elif self.type == "advance":
			allounce_deductions = allounce_deduction_pool.search([("year", "=", self.year), ("month", "=", self.month)])
			setups = []
			allounce_deduction_ids = allounce_deductions.mapped("id")
			self_ads = self.search([("month", "=", self.month)])
			self_ad_ids = self_ads.mapped("id")

			ctx = dict(self._context)

			if self.work_location_id:
				recs_balance_id = self.env["hour.balance.dynamic.line"].search([("parent_id.year", "=", self.year),("parent_id.month", "=", self.month),
								("parent_id.type", "=", 'advance'),("parent_id.state", "=", 'done'),
								("parent_id.work_location_id", "=", self.work_location_id.id)])
			else:
				recs_balance_id = self.env["hour.balance.dynamic.line"].search([("parent_id.year", "=", self.year),
								("parent_id.type", "=", 'advance'),("parent_id.month", "=", self.month)])
			n=1
			for balance in recs_balance_id:
				balance_id = self.env["hour.balance.dynamic.line"].search([("id", "=", balance.id)])
				balance_line_ids = self.env["hour.balance.dynamic.line.line"].search([("parent_id", "=", balance.id)])
				cont_ids = cont.search([("employee_id", "=", balance.employee_id.id)])
				punishment_id = self.env["hr.order"].search([("order_employee_id", "=", balance.employee_id.id),("start_date", "<=", self.date_invoice),
								("end_date", ">=", self.date_invoice),("deduct", ">", 0)],limit=1)

				if len(cont_ids) == 1:
					cont_id = cont_ids[0]
				else:
					raise Warning(("%s кодтой %s ажилтны гэрээ байхгүй эсвэл олон бүртгэгдсэн байна"% (balance.employee_id.identification_id, balance.employee_id.name)))
				rate_id = self.env["res.currency.rate"].search([("currency_id", "=", cont_id.res_currency_id.id),
								("name", "<=", self.date_invoice),],order="name desc",)
				rate = 0
				if rate_id:
					rate = rate_id[0].rate
					basic = cont_id.wage * rate
				else:
					basic = cont_id.wage
				insured_id = cont_id.insured_type_id
				query = """select 
						sum(ll.amount)
						from payroll_fixed_allounce_deduction_line l
						left join payroll_fixed_allounce_deduction_line_line ll on ll.setup_line_id=l.id
						left join payroll_fixed_allounce_deduction al on al.id=l.setup_id
						where ll.type='debt' and l.employee_id=%s and al.year='%s' and al.month='%s'""" % (
					cont_id.employee_id.id,
					self.year,
					self.month,
				)
				self.env.cr.execute(query)
				records = self.env.cr.fetchall()
				pit_disc = records[0][0]
				vals = {
					"name": cont_id.employee_id.name,
					"number": n,
					"last_name": cont_id.employee_id.last_name,
					"ident_id": cont_id.employee_id.identification_id,
					"year": self.year,
					"month": self.month,
					"day_to_work": balance_id.day_to_work_month,
					"hour_to_work": balance_id.hour_to_work_month,
					"date": self.date_invoice,
					"type": self.type,
					"insured_type_id": insured_id.id,
					"employee_id": cont_id.employee_id.id,
					"basic": basic,
					"pit_discount": pit_disc,
					"pit_procent": cont_id.insured_type_id.shi_procent,
					"order_id": self.id,
					"contract_id": cont_id.id,
					"email_address": cont_id.employee_id.work_email,
					"tree_month_average_wage": cont_id.average_wage,
					"is_pit": cont_id.is_pit,
					'punishment_procent':punishment_id.deduct,
				}
				if not iswrite:
					move = order_line.with_context(ctx).create(vals)
				else:
					move = iswrite
				balance_id.write({"balance_line_id": move.id})
				for bal_l_l in balance_line_ids:
					balance_line_id = self.env["hour.balance.dynamic.line.line"].search([("id", "=", bal_l_l.id)])
					balance_line_id.write({"order_balance_line_id": move.id})
				# Нэмэгдэл суутгал
				lines = line_pool.search([("employee_id", "=", cont_id.employee_id.id),("setup_id", "in", allounce_deduction_ids),])
				line_line_ids = []
				for cl in lines:
					for l in cl.setup_line_line:
						if l.category_id.is_advance:
							v = {"order_line_id1": move.id}
							v["name"] = l.name
							v["is_tree"] = l.category_id.is_tree
							v["category_id"] = l.category_id.id
							v["every_month"] = l.every_month
							v["type"] = l.type
							if l.category_id.fixed_type == "hour_balance":
								all_conf = self.env['hr.allounce.deduction.category'].search([('id','=',l.category_id.id)])
								conf_ids = all_conf.mapped('hour_ids')
								all_hours = self.env['hour.balance.dynamic.line.line'].search([('parent_id.parent_id.year','=',self.year),
																('parent_id.parent_id.month','=',self.month),
																('parent_id.parent_id.type','=','advance'),
																('parent_id.employee_id','=',balance.employee_id.id),
																('conf_id','in',conf_ids.ids)])

								hour_ids = all_hours.mapped('conf_id')
								hour_sum = sum(all_hours.mapped('hour'))
								localdict={'move':move,'hour':hour_sum,'result':None}
								tomyo=l.category_id.tomyo.replace(u'үндсэн цалин','move.basic')
								if '/' in tomyo:
									try:
										eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  
									except ValueError:
										raise Warning((u'%s ажилтны %s ийн цагийн балансын мэдээлэл дээр 0 өгөгдөл орсоноос алдаа гарлаа'%(cl.employee_id.name,l.category_id.name)))
								else:
									eval('%s'%(tomyo), localdict, mode='exec', nocopy=True)#  

								v['amount']=localdict['result']
								# v["amount"] = hour_sum
										
							if l.category_id.fixed_type == "tomyo":
								localdict = {"cl": cl, "move": move, "result": None}
								"resutl=basic*0.1 гм байна"
								tomyo = l.category_id.tomyo.replace("үндсэн цалин", "move.basic")
								if "/" in tomyo:
									try:
										eval("%s" % (tomyo), localdict, mode="exec", nocopy=True,)
									except ValueError:
										raise Warning(( "%s ажилтны %s ийн томъёонд 0 өгөгдөл орсоноос алдаа гарлаа."% (cl.employee_id.name,l.category_id.name,)))
								else:
									eval( "%s" % (tomyo), localdict, mode="exec", nocopy=True,)
								v["amount"] = localdict["result"]
							if l.category_id.fixed_type == "depend":
								depend_ids = []
								for i in l.category_id.depend_ids:
									depend_ids.append(i.id)

								line_lines = order_line.search([
										("order_id.year", "=", self.year),
										("order_id.month", "=", self.month),
										("order_id.type", "=", "advance"),
										("employee_id", "=", move.employee_id.id),])
								v["amount"] = line_lines.amount_net
							if l.category_id.fixed_type == "fixed":
								v["amount"] = l.amount

							if l.category_id.code == "SOOAU":
								balance_vacation_lines = (balance_vacation_pool.search([("vacation_id.e_date","=",self.date_invoice,),
											("employee_id", "=", cl.employee_id.id),]))
								for balance_vacation in balance_vacation_lines:
									v["amount"] = balance_vacation.wage_amount

							if l.category_id.code == "UJ":
								v["amount"] = cont_id.long_year_wage
							line_ids = order_line.search([("employee_id", "=", cont_id.employee_id.id),
									("order_id.month", "=", self.month),],limit=1,)
							move.so_line_line.create(v)
							v1 = {"order_line_id2": move.id}
							v1['name']=v["amount"]
							move.so_line_line1.create(v1)
							l.write(v)
				n+=1
		return True

	def compute_net_create(self,context=None):
		line_net_pool =  self.env['salary.order.line.net']
		order_id = None
		employee_id = None
		amount_allounce = None
		amount_deduction = None
		amount_net = None
		amount_tootsson=None
		if self.order_line_net:
			self.order_line_net.unlink()
		query="""
			SELECT 
				sum(sol.amount_tootsson) as amount_tootsson,
				sum(sol.amount_allounce) as amount_allounce,
				sum(sol.amount_deduction) as amount_deduction,
				sum(sol.amount_net) as amount_net,
				sol.employee_id as employee_id ,
				so.id as id,
				min(sol.ndsh_basic) as ndsh_basic,
				pit_procent as pit_procent,
				sol.is_not_ndsh as is_not_ndsh,
				MAX(sol.branch_id) as branch_id,
				sol.insured_type_id as it_id
				FROM salary_order_line sol
				LEFT JOIN salary_order so ON so.id=sol.order_id
				WHERE so.id=%s 
				GROUP BY sol.employee_id,so.id, pit_procent,is_not_ndsh,sol.insured_type_id
				"""%(self.id)
		# print query
		self.env.cr.execute(query)
		records = self.env.cr.dictfetchall()
		ndsh_basic=0
		for rec in records:
			it_pool = self.env['insured.type'].search([('id','=',rec['it_id'])])
			if rec['amount_tootsson']>5500000:
				shi=5500000*it_pool.shi_procent/100
			else:
				shi=rec['amount_tootsson']*it_pool.shi_procent/100

			if rec['amount_tootsson']:
				o_shi=rec['amount_tootsson']*it_pool.o_shi_procent/100
			else:
				o_shi=0

			if rec['ndsh_basic']==0:
				ndsh_basic=rec['amount_tootsson']
			else:
				ndsh_basic=rec['ndsh_basic']
			if not rec['is_not_ndsh']:
				balance_data_id = line_net_pool.create({
					'pit_basic': rec['amount_tootsson'],
					'shi': shi,
					'o_shi': o_shi,
					'amount_tootsson': rec['amount_tootsson'],
					'employee_id':rec['employee_id'],
					'pit_procent':rec['pit_procent'],
					'branch_id':rec['branch_id'],
					'order_id':rec['id']
				})
		return True

	def too(self, x):
		if x%1 == 0:
			return "{0:,.2f}".format(x)
		else:
			return "{0:,.2f}".format(x)

	def get_salary_js(self):
		print(self)
		result = {
			'line_ids': [],
		}
		tal = []
		n=1

		so_l_pool = self.env['salary.order.line'].search([('order_id','=',self.id)],limit=1)
		conf = []
		for c in so_l_pool.so_line_line:
			conf.append({
					'conf_id': c.category_id.id,
					'name':c.category_id.name,
					'record':c
					})
		if self:
			query = """SELECT
					cat.number as number,
					sum(ll.amount) as amount
					FROM salary_order so
					LEFT JOIN salary_order_line sol ON sol.order_id=so.id
					LEFT JOIN salary_order_line_line ll ON ll.order_line_id1=sol.id
					LEFT JOIN hr_allounce_deduction_category cat ON cat.id=ll.category_id
					WHERE so.id=%s and ll.is_tree=True
					GROUP BY ll.category_id,cat.number
					ORDER BY cat.number
					"""%(self.id)
			self.env.cr.execute(query)
			recs = self.env.cr.dictfetchall()
			sum_wage = []
			for rec in recs:
				sum_wage.append({
						'sum':self.too(rec['amount'])
						})
			result['sum_foot'] = sum_wage

		for item in self.order_line:
			causes = []
			amount=0
			for res in item.so_line_line:
				amoun=res.amount
				if res.is_tree==True:
					causes.append({
						'tt_id': res.id,
						'hour': self.too(res.amount),
						'is_tree': res.is_tree,
						})
			tal.append({
					'motohour': item.id,
					'employee_id': item.employee_id.id,
					'is_new_employee': item.is_new_employee,
					'is_update_salary': item.is_update_salary,
					'job': item.employee_id.job_id.name,
					'employee_name': item.employee_id.last_name[:1]+'.'+item.employee_id.name,
					'ident_id': item.employee_id.identification_id,
					'wage': self.too(item.basic),
					'causes':causes,
					'n':n,
					})
			n+=1
		result['line_ids'] = tal
		result['conf_line'] = conf
		print('-=-=-==9',result['conf_line'])
		
		return result

	def print_salary(self,context={}):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		
		file_name = 'salary_order'

		# CELL styles тодорхойлж байна
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(11)
		h1.set_font('Times new roman')
		h1.set_align('center')
		h1.set_align('vcenter')

		left_h1 = workbook.add_format({'bold': 1})
		left_h1.set_font_size(10)
		left_h1.set_font('Times new roman')
		left_h1.set_align('left')

		h2 = workbook.add_format()
		h2.set_font_size(11)
		h2.set_font('Times new roman')
		h2.set_align('left')

		theader = workbook.add_format({'bold': 1})
		theader.set_font_size(10)
		theader.set_text_wrap()
		theader.set_font('Times new roman')
		theader.set_align('center')
		theader.set_align('vcenter')
		theader.set_border(style=1)
		theader.set_bg_color('#c4d79b')

		content_right = workbook.add_format()
		content_right.set_text_wrap()
		content_right.set_font('Times new roman')
		content_right.set_font_size(9)
		content_right.set_border(style=1)
		content_right.set_align('right')

		content_left = workbook.add_format({'num_format': '###,###,###.##'})
		content_left.set_text_wrap()
		content_left.set_font('Times new roman')
		content_left.set_font_size(9)
		content_left.set_border(style=1)
		content_left.set_align('left')
		
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
		

		fooder = workbook.add_format({'bold': 1})
		fooder.set_font_size(10)
		fooder.set_text_wrap()
		fooder.set_font('Times new roman')
		fooder.set_align('center')
		fooder.set_align('vcenter')
		fooder.set_border(style=1)
		fooder.set_bg_color('#c4d79b')

		sheet = workbook.add_worksheet(u'Цалин')


		month_code=0
		if self.month=='1':
			month_code=1
		if self.month=='2':
			month_code=2
		if self.month=='3':
			month_code=3
		if self.month=='4':
			month_code=4
		if self.month=='5':
			month_code=5
		if self.month=='6':
			month_code=6
		if self.month=='7':
			month_code=7
		if self.month=='8':
			month_code=8 
		if self.month=='9':
			month_code=9
		if self.month=='90':
			month_code=10
		if self.month=='91':
			month_code=11
		if self.month=='92':
			month_code=12 

		sheet.merge_range(0,0,0,3, u'Байгууллагын нэр:'+ ' ' + self.company_id.name, content_right),
		if self.type=='advance':
			sheet.merge_range(3, 0, 3, 8, u'%s ОНЫ %s-р САРЫН УРЬДЧИЛГАА ЦАЛИНГИЙН ХҮСНЭЛТ'%(self.year,month_code), h1)
			# sheet.merge_range(5, 0, 5, 3, u'Хэлтэс: %s / %s'%(self.department_id.parent_id.name,self.department_id.name), left_h1)
		elif self.type=="final":
			sheet.merge_range(3, 0, 3, 8, u'%s ОНЫ %s-р САРЫН СҮҮЛ ЦАЛИНГИЙН ХҮСНЭЛТ'%(self.year,month_code), h1)
			# sheet.merge_range(2, 25, 2, 28, u"БАТЛАВ:",h2)
			# sheet.merge_range(3, 22, 3, 30,u"ГҮЙЦЭТГЭХ ЗАХИРАЛ..........................................",h2)

		rowx=6
		save_row=7
		sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
		sheet.merge_range(rowx,1,rowx+2,1, u'Код', theader),
		sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
		sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),
		sheet.merge_range(rowx,4,rowx+2,4, u'Алба нэгж', theader),
		sheet.merge_range(rowx,5,rowx+2,5, u'Албан тушаал', theader),
		sheet.merge_range(rowx,6,rowx+2,6, u'Даатгуулагчийн төрөл', theader),
		sheet.merge_range(rowx,7,rowx+2,7, u'Регистрийн дугаар', theader),
		sheet.merge_range(rowx,8,rowx+2,8, u'Татвар төлөгчийн дугаар', theader),
		# sheet.merge_range(rowx,5,rowx,6, u'АЗ', theader),
		# sheet.merge_range(rowx+1,5,rowx+2,5, u'Хоног', theader),
		# sheet.merge_range(rowx+1,6,rowx+2,6, u'Цаг', theader),
		# if self.type=='final':
		# 	confs = self.env['hr.allounce.deduction.category'].search([('is_advance','!=',True)])
		# else:
		# 	confs = self.env['hr.allounce.deduction.category'].search([('is_advance','=',True)])

		so_l_pool = self.env['salary.order.line'].search([('order_id','=',self.id)],limit=1)
		col=9
		for c in so_l_pool.so_line_line:
			sheet.merge_range(rowx,col,rowx+2,col, c.category_id.name, theader),
			col+=1

		n=1
		rowx+=3
		sheet.set_column('A:A', 5)
		sheet.set_column('B:B', 6)
		sheet.set_column('C:C', 15)
		sheet.set_column('D:D', 15)
		sheet.set_column('E:E', 25)
		sheet.set_column('F:F', 25)
		# if self.department_id:
		# 	if self.salary_type:
		# 		order_line = self.env['salary.order.line'].search([('order_id','=',self.id),('employee_id.department_id','=',self.department_id.id),('contract_id.salary_type','=',self.salary_type)])
		# 	else:
		# 		order_line = self.env['salary.order.line'].search([('order_id','=',self.id),('employee_id.department_id','=',self.department_id.id)])
		# else:
		# if self.salary_type:
		# 	order_line = self.env['salary.order.line'].search([('order_id','=',self.id)])
		for data in self.order_line:
			sheet.write(rowx, 0, n,content_left)
			sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
			sheet.write(rowx, 2,data.employee_id.last_name,content_left)
			sheet.write(rowx, 3,data.employee_id.name,content_left)
			sheet.write(rowx, 4,data.employee_id.department_id.name,content_left)
			sheet.write(rowx, 5,data.employee_id.job_id.name,content_left)
			sheet.write(rowx, 6,data.insured_type_id.code,center)
			sheet.write(rowx, 7,data.employee_id.passport_id,content_left)
			sheet.write(rowx, 8,data.employee_id.ttd_number,content_left)
			# sheet.write(rowx, 5,data.day_to_work or 0 ,center)
			# sheet.write(rowx, 6,data.hour_to_work  or 0,center)
			colx=9
			for line in data.so_line_line:
				sheet.write(rowx, colx,line.amount,center)
				colx+=1
			rowx+=1
			n+=1

		sheet.merge_range(rowx, 0, rowx, 7, u'НИЙТ', fooder)
		l=4
		while l <= colx-1:
			sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row-1, l) +':'+ self._symbol(rowx-1, l)+')}', fooder)
			l+=1
		# 	sheet.write_formula(rowx, 5, "{=SUM(F%d:F%d)}" % (5, rowx), center_bold)

		# rowx += 1

		rowx+=2
		sheet.write(rowx, 2, u'Бэлтгэсэн:', h2)
		sheet.merge_range(rowx, 3, rowx, 5, u'Нягтлан бодогч:......................../%s.%s/'%(self.preparatory.last_name[:1],self.preparatory.name), h2)

		sheet.write(rowx+1, 2, u'Хянасан:', h2)
		sheet.merge_range(rowx+1, 3, rowx+1, 5, u'%s:....................../%s.%s/'%(self.compute_controller.job_id.name,self.compute_controller.last_name[:1],self.compute_controller.name), h2)
		
		sheet.write(rowx+2, 2, u'Баталсан:', h2)
		sheet.merge_range(rowx+2, 3, rowx+2, 5, u'Гүйцэтгэх захирал:.................../%s.%s/'%(self.done_director.last_name[:1],self.done_director.name), h2)
		
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

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)

	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol

class salary_order_line_net(models.Model):
	_name = "salary.order.line.net"
	_description = "Salary Line"

	def _compute_day(self):
		shi=0
		pit=0
		oshi=0
		self.amount_net_shi=self.amount_tootsson-self.amount_deduction-self.shi-self.pit
		# if self.pit_basic>4200000:
		# 	shi=4200000*self.pit_procent/100
		# else:
		# 	shi=self.pit_basic*self.pit_procent/100
		# print('==-=-=-=',shi)
		# if self.pit_basic>149810:
		# 	if self.pit_basic<561797:
		# 		pit=(self.pit_basic-self.pit_basic*0.11)*0.1-13333 
		# 	if self.pit_basic>561797:
		# 		if self.pit_basic<1123595:
		# 			pit=(self.pit_basic-self.pit_basic*0.11)*0.1-11667
		
		# 	if self.pit_basic>1123595:
		# 		if self.pit_basic<1685392:
		# 			pit=(self.pit_basic-self.pit_basic*0.11)*0.1-10000 
		
		# 	if self.pit_basic>1685392:
		# 		if self.pit_basic<2247190:
		# 			pit=(self.pit_basic-self.pit_basic*0.11)*0.1-8333 
		
		# 	if self.pit_basic>2247190:
		# 		if self.pit_basic<2763999:
		# 			if(self.pit_basic*0.11)>263999: 
		# 				pit=(self.pit_basic-264000)*0.1-6667 
		# 			else: 
		# 				pit=(self.pit_basic-self.pit_basic*0.11)*0.1-6667 
		
		# 	if self.pit_basic>2763999:
		# 		if self.pit_basic<3263999:
		# 			pit=(self.pit_basic-264000)*0.1-5000 
		
		# 	if self.pit_basic>3264000:
		# 		pit=(self.pit_basic-264000)*0.1
		# else:  
		# 	pit=0
		# oshi=(self.pit_basic*12)/100
		# self.shi=shi
		# self.pit=pit
		# self.oshi=oshi
		

	employee_id = fields.Many2one('hr.employee', string='Employee',index=True)
	branch_id = fields.Many2one('res.branch', string='Branch',index=True)
	amount_tootsson = fields.Float(string='Amount tootsson', digits=(16, 2),)
	amount_net_shi = fields.Float(string='Amount net',digits=(16, 2),store=True, readonly=True, compute='_compute_day')
	amount_net = fields.Float(string='Amount net',digits=(16, 2))
	amount_allounce = fields.Float(string='Amount allounce', digits=(16, 2),)
	amount_deduction = fields.Float(string='Amount deduction', digits=(16, 2),)
	pit_basic=fields.Float('НДШ цалин', digits=(16, 2))
	shi=fields.Float(string='НДШ')
	oshi=fields.Float(string='БНДШ')
	pit=fields.Float(string='ХАОАТ')
	pit_procent=fields.Float(u'НДШ тооцоолох хувь')
	pitt_procent=fields.Float(u'БНДШ тооцоолох хувь')
	order_id = fields.Many2one('salary.order', u'Цалин', ondelete='cascade', index=True)
	order_line_id = fields.Many2one('salary.order.line.net', u'Цалин', ondelete='cascade', index=True)

class salary_order_line(models.Model):
	_name = "salary.order.line"
	_description = "Salary Line"
 
	@api.depends('so_line_line','so_line_line.type','so_line_line.amount')
	def _amount_not_ndsh(self):
		
		for obj in self:
			amount_not_ndsh=0
			for line in obj.so_line_line:
				if line.is_ndsh==True:
					amount_not_ndsh+=line.amount
			obj.update({
				'amount_not_ndsh': amount_not_ndsh
			})

	amount_not_ndsh = fields.Float(string='НДШ тооцохгүй дүн', digits=(0, 0), store=True, readonly=True, compute=_amount_not_ndsh)

	def action_send_mail(self, template_xmlid, force_send=False):
		for line in self:
			if line.email_address:
				line._send_mail_to_salary('mw_salary.salary_email')
		return True
	@api.model

	# def _send_mail_to_salary(self, template_xmlid, with_mail=False, subject_mail=False, html_mail=False, attachment_ids=[]):
	# def _send_mail_to_salary(self,template):
	# 	template = False

	# 	if not template:
	# 		template = self.env.ref('mw_salary.salary_email')
	# 	assert template._name == 'mail.template'

	# 	email_values = {
	# 		'email_cc': False,
	# 		'auto_delete': True,
	# 		'recipient_ids': [],
	# 		'partner_ids': [],
	# 		'scheduled_date': False,
	# 	}

	# 	for line in self:
	# 		if not line.email_address:
	# 			raise UserError(_("Cannot send email: user %s has no email address.", user.name))
	# 		email_values['email_to'] = line.email_address
	# 		# TDE FIXME: make this template technical (qweb)
	# 		with self.env.cr.savepoint():
	# 			# force_send = not(self.env.context.get('import_file', False))
	# 			template.send_mail(line.id,  raise_exception=True, email_values=email_values)

	def _send_mail_to_salary(self,template):
		template = False
		month=False
		if self.order_id:
			if self.order_id.month=='90':
				month='10'
			elif self.order_id.month=='91':
				month='11'
			elif self.order_id.month=='92':
				month='12'
			else:
				month=self.order_id.month
		# print('======month', month)
		html ="""
			<table border="0" cellpadding="0" cellspacing="0" width="510px"
				style="padding: 16px; background-color: white; color: #454748; border-collapse:separate;">
				<tbody>
				<!-- HEADER -->
					<tr>
						<td align="center" style="min-width: 590px;">
						<table border="0" cellpadding="0" cellspacing="0" width="510px"
							style="min-width: 590px; background-color: white; padding: 0px 8px 0px 8px; border-collapse:separate;">
							<tr>
							<td valign="middle">
								<span style="font-size: 20px; font-weight: bold;">Сайн байна уу?</span>
								<br />
								<span style="font-size: 17px;">
								<t>Таны</t>
								<t t-out="object.year or ''"></t>
								<t>оны</t>
								<t t-out="{0} or ''"></t>
								<t>сарын цалингийн мэдээ илгээж байна.</t>
								</span>
								<br />
								<span style="font-size: 17px;">
								<t t-out="object.ident_id or ''">0001</t>
								<t t-out="object.last_name or ''">Marc</t>
								<t t-out="object.name or ''">Demo</t>
								</span>
							</td>
							<td valign="middle" align="right">
								<img t-attf-src="/logo.png?company={1}"
								style="padding: 0px; margin: 0px; height: auto; width: 80px;"
								t-att-alt="object.order_id.company_id.name" />
							</td>
							</tr>
							
						</table>
						</td>
					</tr>
				</tbody>
			</table>
		
		""".format(month,self.order_id.company_id.id)
		html+= """<table style="border-collapse: collapse; width: 510px;">
				<tbody>
		"""
		
		for line in self.so_line_line:
			if line.is_mail==False:
				if line.amount>0:
					formatted_amount = "{:,.2f}".format(line.amount)
					html += """
						<tr>
							<td style="border: 1px solid; border-collapse: collapse; text-align: left;">{0}</td>
							<td style="border: 1px solid; border-collapse: collapse; text-align: left;">{1}</td>
						</tr>
						
					""".format(line.name, formatted_amount)
		html += """<tbody></table></html>"""
		
		if not template:
			template = self.env.ref('mw_salary.salary_email')
			template['body_html'] = html
		assert template._name== 'mail.template'

		email_values = {
			'email_cc': False,
			'email_from': self.order_id.company_id.email,
			'auto_delete': True,
			'recipient_ids': [],
			'partner_ids': [],
			'scheduled_date': False,
		}

		for line in self:
			if line.email_address:
				# raise UserError(_("Cannot send email: user %s has no email address.", user.name))
				email_values['email_to'] = line.email_address
				# TDE FIXME: make this template technical (qweb)
				with self.env.cr.savepoint():
					# force_send = not(self.env.context.get('import_file', False))
					template.send_mail(line.id,  raise_exception=True, email_values=email_values)


	def action_send_mail_emp(self):
		for obj in self:
			obj._send_mail_to_salary('self')
		return True
		# invitation_template = self.env.ref('mw_salary.salary_email', raise_if_not_found=False)
		# for line in self:
		# 	email = line.email_address or False
			
		# 	if email:
		# 		vals = {
		# 			'body_html': invitation_template.body_html,
		# 			'subject': '%s' % (subject_mail or ''),
		# 			# 'email_to': email,
		# 			'auto_delete': False,
		# 			'state': 'outgoing',
		# 		}
		# 		mail_id = self.env['mail.mail'].sudo().create(vals)
		# 		mail_id.sudo().send()

		# return True

	def compute_create_line(self,context=None):
		if self.so_line_line:
			self.so_line_line.unlink()
		context.update({'employee_id':self.employee_id.id})
		self.order_id.compute_create(context)
		return True

	# def _final_compute_day(self):
	# 	day_to_work=0
	# 	worked_day=0
	# 	for line in self.balance_data_line:
	# 		day_to_work+=line.day_to_work
	# 		worked_day+=line.worked_day
	# 	self.day_to_work=day_to_work
	# 	self.worked_day=worked_day

	@api.depends('so_line_line','so_line_line.type','so_line_line.amount')
	def _compute_vacation_salary(self):
		for obj in self:
			vacation_salary=0
			for line in obj.so_line_line:
				if line.category_id.code == 'SOOA':
					vacation_salary+=line.amount
			obj.update({
				'vacation_salary': vacation_salary,
			})

	
	is_new_employee = fields.Boolean('Шинэ ажилтан эсэх', default=False)
	is_update_salary = fields.Boolean('Цалин өөрчлөгдсөн эсэх', default=False)
	amount_allounce = fields.Float(string='Нийт нэмэгдэл', digits=(16, 2), store=True,  compute='_compute_amount_all', tracking=True)
	amount_deduction = fields.Float(string='Нийт суутгал', digits=(16, 2), store=True, compute='_compute_amount_all')

	amount_net = fields.Float(string='Гарт олгох',digits=(16, 2), store=True,  compute='_compute_amount_net')

	amount_tootsson = fields.Float(string='Бодогдсон цалин', digits=(16, 2), store=True, readonly=True, compute='_compute_amount_toot')
	bndsh = fields.Float(string='БНДШ', digits=(16, 2),store=True, readonly=True, compute='_compute_amount_toot')
	shi = fields.Float(string='НДШ', digits=(16, 2),store=True, readonly=True, compute='_compute_shi')
	pit_amount = fields.Float(string='PIT Amount', digits=(16, 2), store=True, readonly=True, compute='_compute_amount_toot')
	sequence = fields.Integer(string='Sequence', default=10, help="Gives the sequence of this line when displaying the invoice.")
	year_sum_basic = fields.Float(string='Жилийн нийт цалин', digits=(16, 2))
	year_sum_shi = fields.Float(string='Жилийн нийт НДШ', digits=(16, 2))
	year_sum_pit = fields.Float(string='ХАОАТ тооцох дүн', digits=(16, 2))
	year_amount_pit = fields.Float(string='Суутгасан ХАОАТ дүн', digits=(16, 2))

	@api.depends('so_line_line','so_line_line.type','so_line_line.amount')
	def _compute_amount_all(self):
		
		for obj in self:
			amount_all=0
			amount_ded=0
			pay=0
			for line in obj.so_line_line:
				if line.category_id.code in ('PAY','PAYALL'):
					pay+=line.amount
				if line.type=='allounce':
					amount_all+=line.amount
				elif line.type=='deduction':
					amount_ded+=line.amount
			obj.update({
				'amount_allounce': amount_all-pay,
				'amount_deduction': amount_ded,
			})

	@api.depends('amount_tootsson','amount_deduction', 'so_line_line','so_line_line.type','so_line_line.amount')
	def _compute_amount_net(self):
	
		for obj in self:
			avlaga=0
			ded_net = 0
			add_net = 0
			for line in obj.so_line_line:
				if line.category_id.code=='OR':
					avlaga+=line.amount
				if line.category_id.type=='ded_net':
					ded_net+=line.amount
				if line.category_id.type=='add_net':
					add_net+=line.amount
			obj.amount_net=obj.amount_tootsson-obj.amount_deduction+add_net+avlaga

	@api.depends('so_line_line','so_line_line.type','so_line_line.amount')
	def _compute_amount_toot(self):
	
		for obj in self:
			amount_toot=0
			pit_amount=0
			bndsh=0
			for line in obj.so_line_line:
				if line.type =='allounce':
					amount_toot+=line.amount

			if obj.insured_type_id.code=='221':
				pit_amount=0
			else:
				pit_amount=amount_toot

			if obj.insured_type_id.code=='20' or obj.insured_type_id.code=='06' or obj.insured_type_id.code=='17' or obj.insured_type_id.code=='21':
				if amount_toot==0:
					bndsh=(660000 * obj.pitt_procent) / 100
				elif amount_toot>0:
					bndsh=(amount_toot * obj.pitt_procent) / 100
			else:
				bndsh=(amount_toot * obj.pitt_procent) / 100

			obj.amount_tootsson = amount_toot
			obj.pit_amount = pit_amount
			obj.bndsh = bndsh

	@api.depends('so_line_line','so_line_line.type','so_line_line.amount')
	def _compute_shi(self):
		for obj in self:
			shi=0
			for line in obj.so_line_line:
				if line.category_id.code in ('SHI','SHIU'):
					shi+=line.amount
			obj.update({
				'shi': shi,
			})
	is_pit = fields.Boolean('ХХОАТ бодох эсэх', default=True)
	email_address = fields.Char('Имэйл хаяг')
	pit_discount = fields.Float('Татварын хөнгөлөлт', readonly=True)
	insured_type_id = fields.Many2one('insured.type', u'Даатгуулагчийн төрөл')
	grade_procent = fields.Float(u'Зэргийн нэмэгдлийн хувь')
	vacation_amount = fields.Float(u'ЭА тооцох дүн')
	vacation_salary = fields.Float(string='ЭА авсан дүн',digits=(16, 2), store=True,  compute=_compute_vacation_salary)
	vacation_day = fields.Float(u'Ажилласан хоног')
	vacation_day_to_work = fields.Float(u'АЗ хоног')
	hour_to_work = fields.Float(u'АЗ цаг')
	vacation_worked_day = fields.Float(u'Ажилласан хоног')
	worked_hour = fields.Float(u'Ажилласан цаг')
	vac_day = fields.Float(u'ЭА хоног')
	type = fields.Selection([
				('advance','Урьдчилгаа'),
				('final','Сүүл'),
			], string='Төрөл', required=True,index=True, change_default=True,
			default='final',)

	punishment_procent = fields.Float('Сахилгын шийтгэлийн хувь')
	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8)
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
	name = fields.Text(string='Нэр', required=True)
	number = fields.Integer('Дугаар')
	pit_procent=fields.Float(u'НДШ тооцоолох хувь')
	pitt_procent=fields.Float(u'БНДШ тооцоолох хувь')
	date=fields.Date('Огноо')
	order_id = fields.Many2one('salary.order', u'Цалин',ondelete='cascade', index=True)
	last_name = fields.Char('Овог')
	ident_id = fields.Char('Хувийн дугаар')
	employee_id = fields.Many2one('hr.employee', string='Ажилтан',index=True)
	contract_id = fields.Many2one('hr.contract', string='Гэрээ',index=True)
	branch_id = fields.Many2one('res_branch', string='Branch',index=True)
	basic = fields.Float(string='Үндсэн цалин', digits= (16, 2),required=True, default=1)
	
	ndsh_basic = fields.Float(u'НДШ Цалин', digits= dp.get_precision('Product Unit of Measure'), required=True, default=0)

	vac_ssum = fields.Float(string='Vac ssm', digits= dp.get_precision('Product Unit of Measure'), default=0)
	so_line_line = fields.One2many('salary.order.line.line', 'order_line_id1', string='Setup Line Lines',)
	setup2_line_line = fields.One2many('payroll.fixed.allounce.deduction.line.line', 'order_line_id', string='Setup Line Lines',)
	# day_to_work=fields.Float(string='Day to work', digits=(16, 2), readonly=True, compute=_final_compute_day)
	# worked_day=fields.Float(string='Worked Day', readonly=True, compute=_final_compute_day)
	# final_day_to_work=fields.Float(string='Sum day to work', digits=(16, 2), readonly=True, compute=_final_compute_day)
	# final_worked_day=fields.Float(string='Sum worked Day', digits=(16, 2),readonly=True, compute=_final_compute_day)
	day_to_work=fields.Float(string='Day to work', digits=(16, 2))
	worked_day=fields.Float(string='Worked Day')
	final_day_to_work=fields.Float(string='Sum day to work', digits=(16, 2))
	final_worked_day=fields.Float(string='Sum worked Day')
	order_line_net = fields.One2many('salary.order.line.net', 'order_line_id', string='Hour balance',)
	# balance_data_line = fields.One2many('hour.balance.line', 'order_balance_line_id', string='Hour balance',)
	is_not_ndsh = fields.Boolean(string='Is not SHI ?',default=False)
	pit_id = fields.Many2one('personal.income.tax.configure','PIT')

	so_line_line1 = fields.One2many('salary.order.line.line1', 'order_line_id2', string='Setup Line Lines')

	tree_month_average_wage = fields.Float(string='3 сарын дундаж цалин', digits= (16, 2),required=True, default=1)
	tree_month_sum_hour = fields.Float(string='3 сарын нийлбэр цаг', digits= (16, 2),required=True, default=1)
	tree_month_sum_wage = fields.Float(string='3 сарын нийлбэр цалин', digits= (16, 2),required=True, default=1)
	
	# tree_month_average_wage_cr = fields.Float(string='Дундаж цалин', digits= (16, 2),store=True, compute='_compute_tree_month_sum')
	# tree_month_sum_hour_cr = fields.Float(string='Нийлбэр цаг', digits= (16, 2),store=True, compute='_compute_tree_month_sum')
	# tree_month_sum_wage_cr = fields.Float(string='Нийлбэр цалин', digits= (16, 2),store=True, compute='_compute_tree_month_sum')

	tree_month_average_wage_cr = fields.Float(string='Дундаж цалин', digits= (16, 2))
	tree_month_sum_hour_cr = fields.Float(string='Нийлбэр цаг', digits= (16, 2))
	tree_month_sum_wage_cr = fields.Float(string='Нийлбэр цалин', digits= (16, 2))

	# @api.depends("so_line_line", "so_line_line.type", "so_line_line.amount")
	# def _compute_tree_month_sum(self):
	# 	for obj in self:
	# 		tree_month_average_wage_cr = 0 
	# 		tree_month_sum_hour_cr = 0
	# 		tree_month_sum_wage_cr = 0
	# 		for line in obj.so_line_line:
	# 			if line.category_id.is_average == True:
	# 				tree_month_sum_wage_cr += line.amount
	# 			if line.category_id.is_average_hour == True:
	# 				tree_month_sum_hour_cr += line.amount
	# 			if tree_month_sum_wage_cr and tree_month_sum_hour_cr:
	# 				tree_month_average_wage_cr = tree_month_sum_wage_cr/tree_month_sum_hour_cr
	# 		obj.update(
	# 			{
	# 				"tree_month_average_wage_cr": tree_month_average_wage_cr,
	# 				"tree_month_sum_hour_cr": tree_month_sum_hour_cr,
	# 				"tree_month_sum_wage_cr": tree_month_sum_wage_cr,
	# 			})
	def print_salary_order(self, cr, uid, ids, context={}):
		''' 
		'''
		datas = {
			'ids': ids
		}
		context.update({'active_id':ids[0]})
		return {
			'type'		 : 'ir.actions.report.xml',
			'report_name'   : 'print.salary.order',
			'datas'		 : datas,
			'context'	   : context,
			'nodestroy': True
		 }
	dyn_balance_data_line = fields.One2many("hour.balance.dynamic.line.line","order_balance_line_id",string="Hour balance",)
	dyn_balance_data_ids = fields.One2many("hour.balance.dynamic.line","balance_line_id",string="Hour balance",)
	day_to_work = fields.Integer("АЗ өдөр")
	hour_to_work = fields.Float("АЗ цаг")

class hour_balance_line(models.Model):
	_inherit = "hour.balance.dynamic.line.line"

	order_balance_line_id = fields.Many2one("salary.order.line", string="Setup line", index=True)

class hour_balance_line(models.Model):
	_inherit = "hour.balance.dynamic.line"

	balance_line_id = fields.Many2one("salary.order.line", string="Setup line", index=True)


class salary_order_line_line1(models.Model):
	_name = "salary.order.line.line1"
	_description = "line line"

	order_line_id2 = fields.Many2one('salary.order.line', string='Order line', index=True, ondelete='cascade')
	name = fields.Float(string='Бодогдсон дүн', digits= (16, 2), default=0.0)

class salary_order_line_line(models.Model):
	_name = "salary.order.line.line"
	_description = "line line"
	
	category_id = fields.Many2one('hr.allounce.deduction.category', string='Нэмэгдэл суутгал',)
	name = fields.Char("Нэр", related="category_id.name", store=True)
	code = fields.Char("Код", related="category_id.code", store=True)
	is_mail = fields.Boolean("Email явуулахгүй эсэх", related="category_id.is_mail", store=True)

	setup_line_id = fields.Many2one('payroll.fixed.allounce.deduction.line', string='Setup line', ondelete='cascade', index=True)
	amount = fields.Float(string='Бодогдсон дүн', digits= (16, 2), default=0.0)
	type = fields.Selection([
			('allounce','Нэмэгдэл'),
			('deduction','Суутгал'),
			('payroll','Цалин'),
			('debt','Өр'),
			('hour','Цаг'),
			('tootsson','Тооцсон'),
			('pitt','Хөнгөлөлт'),
			('ded_net','Гарт олгохоос хасах'),
			('add_net','гарт олгох нэмэгдүүлэх'),
			('no_shi','НДШ тооцохгүй'),
		], string='Төрөл',  default=lambda self: self._context.get('allounce'), tracking=True)
	every_month = fields.Boolean(string='Сар', default=True)
	order_line_id1 = fields.Many2one('salary.order.line', string='Order line', index=True, ondelete='cascade')
	
	is_tree = fields.Boolean('Багана харагдах эсэх')
	is_ndsh = fields.Boolean('НДШ тооцох эсэх')
	employee_id = fields.Many2one("hr.employee", related="order_line_id1.employee_id", store=True)

	def onchange_category_id(self):
		self.type = self.category_id.type
		self.name = self.category_id.name

class EmployeeSalaryMine(models.Model):
	_name = "employee.salary.mine"
	_description = "employee salary mine"

	employee_id = fields.Many2one('hr.employee', 'Ажилтан')
	wage = fields.Float('Үндсэн цалин')
	
	list = fields.Float('ХЧТАТ')
	day_to_work = fields.Float('АЗ өдөр')
	hour_to_work = fields.Float('АЗ цаг')
	worked_day = fields.Float('Ажилласан өдөр')
	worked_hour = fields.Float('Ажилласан өдөр')
	irts_tootsson = fields.Float('Ажилласан цагт ногдох цалин')
	guitsetgel_tootsson = fields.Float('Урамшуулал цалин')
	phone_allounve = fields.Float('Утасны төлбөр')
	vacation = fields.Float('Амралтын цалин')
	food = fields.Float('Хоолны мөнгө')
	overtime_hour = fields.Float('Илүү цаг')
	overtime_wage = fields.Float('Илүү цагийн нэмэгдэл')
	long_wage = fields.Float('Удаан жилийн нэмэгдэл')
	other_nemegdel = fields.Float('Бусад нэмэгдэл')
	sum_nemegdel = fields.Float('Нийт нэмэгдэл')
	amount_tootsson = fields.Float('Олговол зохих')
	shi = fields.Float('НДШ')
	shi_22 = fields.Float('2022 оны татварын хөнгөлөлт')
	pit_discount = fields.Float('ХХОАТ хөнгөлөлт')
	pit = fields.Float('ХХОАТ')
	uridchilgaa_suutgal = fields.Float('Урьдчилгаа суутгал')
	uridchilgaa_belen = fields.Float('Бэлэн авсан урьдчилгаа')
	phone = fields.Float('Утасны лимит хэтэрсэн')
	avlaga = fields.Float('Авлага')

	other_nemegdel_wage = fields.Float('Бусад нэмэгдэл цалин')
	
	bonus = fields.Float('Бонус')
	
	niit_suutgal = fields.Float('Нийт суутгал')
	other_suutgal = fields.Float('Бусад суутгал')
	jinhene_olgoh = fields.Float('Гарт олгох')
	ashig_dun = fields.Float('Ашиг тооцох дүн')
	zuruu = fields.Float('Цалингийн зөрүү')
	
	month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
			('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
			('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
	year= fields.Char(method=True, store=True, type='char', string='Жил', size=8)
