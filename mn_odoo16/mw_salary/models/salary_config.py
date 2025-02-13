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

DATE_FORMAT = "%Y-%m-%d"

class PersonalIncomeTaxConfigure(models.Model):
	_name = "personal.income.tax.configure"
	_description = "Personal Income tax Configure"
	_inherit = ['mail.thread']

	name = fields.Char('Нэр')
	amount_wage_top = fields.Char('Албан татвар ногдуулах орлогын хэмжээ/Дээд/')
	amount_wage_down = fields.Char('Албан татвар ногдуулах орлогын хэмжээ/Доод/')
	discount = fields.Char('Албан татвар хөнгөлөх хэмжээ')

class InsuredType(models.Model):
	_name = "insured.type"
	_description = "insured type"
	_inherit = ['mail.thread']

	def name_get(self):
		res = []
		for obj in self:
			if obj.code and obj.name:
				res.append((obj.id, '/'+obj.code+'/'+'-'+obj.name))
			else:
				res.append((obj.id, obj.name))
				
		return res

	name =fields.Char(u'Нэр', tracking=True)
	code =fields.Char(u'Код', tracking=True)
	tetgever = fields.Float(u'Тэтгэвэр/даатгуулагч/', tracking=True)
	o_tetgever = fields.Float(u'Тэтгэвэр/АО/', tracking=True)
	tetgemj = fields.Float(u'Тэтгэмж/даатгуулагч/', tracking=True)
	o_tetgemj = fields.Float(u'Тэтгэмж/АО/', tracking=True)
	eruul_mend = fields.Float(u'Эрүүл мэнд/даатгуулагч/', tracking=True)
	o_eruul_mend = fields.Float(u'Эрүүл мэнд/АО/', tracking=True)
	ajilguidel = fields.Float(u'Ажилгүйдэл/даатгуулагч/', tracking=True)
	o_ajilguidel = fields.Float(u'Ажилгүйдэл/АО/', tracking=True)
	uo_procent = fields.Float(u'ҮОНШҮ/даатгуулагч/', tracking=True)
	uo_shi_procent = fields.Float(u'ҮОНШҮ/АО/', tracking=True)
	shi_procent = fields.Float(u'НДШ хувь/даатгуулагч/',  readonly=True, compute='_compute_amount')
	o_shi_procent = fields.Float(u'НДШ хувь/АО/', readonly=True, compute='_compute_amount')
	state = fields.Selection([('draft','Ноорог'),('done','Баталсан')],'Төлөв',default='draft')
	lower_limit = fields.Float('Доод лимит')
	is_compute_pitt = fields.Boolean('Хөнгөлөлт бодох эсэх', tracking=True)
	is_compute_pit = fields.Boolean('ХХОАТ бодох эсэх', tracking=True)

	def done_action(self):
		return self.write({'state': 'done'})

	def draft_action(self):
		return self.write({'state': 'draft'})

	def _compute_amount(self):
		for obj in self:
			obj.shi_procent=obj.tetgever+obj.tetgemj+obj.eruul_mend+obj.ajilguidel+obj.uo_procent
			obj.o_shi_procent=obj.o_tetgever+obj.o_tetgemj+obj.o_eruul_mend+obj.o_ajilguidel+obj.uo_shi_procent

class Contract(models.Model):
	_inherit = 'hr.contract'

	salary_type = fields.Selection([('month','Сараар'),('day','Өдрөөр'),('hour','Цагаар'),('garaa','Гараагаар')],'Цалингийн төрөл',default='month')
	insured_type_id = fields.Many2one('insured.type', u'Даатгуулагчийн төрөл', required=True)
	employee_type= fields.Selection('Ажилтны төлөв', related='employee_id.employee_type', readonly=True, store=True)
	department_id = fields.Many2one('hr.department','Хэлтэс', related='employee_id.department_id', readonly=True, store=True)
	job_id = fields.Many2one('hr.job','Албан тушаал', related='employee_id.job_id', readonly=True)
	identification_id = fields.Char('Код', related='employee_id.identification_id', readonly=True,store=True)
	res_currency_id = fields.Many2one('res.currency', 'Валют', default=False)
	wage_mnt = fields.Float(u'Үндсэн цалин MNT', digits=(0, 0), compute='_one_day_wage', tracking=True)
	advance_procent = fields.Monetary(u'Урьдчилгаа бодох хувь', digits=(16, 2), help="Employee's monthly gross wage.")
	is_pit = fields.Boolean('ХХОАТ бодох эсэх', default=True)
	average_wage = fields.Float('3 сарын дундаж цалин')
	is_not_long_year = fields.Boolean('Удаан жил тооцохгүй', default=True)
	employee_id = fields.Many2one('hr.employee', string='Employee', tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", index=True)
	date_end = fields.Date('End Date', tracking=True,
		help="End date of the contract (if it's a fixed-term contract).", index=True)
	state = fields.Selection([
		('draft', 'New'),
		('open', 'Running'),
		('close', 'Expired'),
		('cancel', 'Cancelled')
	], string='Status', group_expand='_expand_states', copy=False,
		tracking=True, help='Status of the contract', default='draft', index=True)
	kanban_state = fields.Selection([
		('normal', 'Grey'),
		('done', 'Green'),
		('blocked', 'Red')
	], string='Kanban State', default='normal', tracking=True, copy=False, index=True)


	@api.onchange('insured_type_id')
	def _onchange_insured_type_id(self):
		if self.insured_type_id:
			if self.insured_type_id.code=='70':
				self.is_pit = False
	
	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			self.job_id = self.employee_id.job_id
			self.department_id = self.employee_id.department_id
			self.resource_calendar_id = self.employee_id.resource_calendar_id
			self.company_id = self.employee_id.company_id
			self.name = self.employee_id.identification_id

	@api.depends('res_currency_id', 'wage')
	def _one_day_wage(self):
		for item in self:
			item.wage_mnt= item.res_currency_id.rate * item.wage

class AllounceDeductionCategory(models.Model):
	_name = "hr.allounce.deduction.category"
	_inherit ='mail.thread'
	_description = "Allounce deduction category"
	_order = "number"

	number = fields.Integer(string='Дугаар', tracking=True)
	name = fields.Char(string='Нэр',required=True, tracking=True)
	code = fields.Char(string='Код',required=True, tracking=True)
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
		], string='Төрөл', 
		default=lambda self: self._context.get('allounce'),
		tracking=True,required=True)
	fixed_type = fields.Selection([
			('fixed','Тогтмол'),
			('variable','Хувьсах'),
			('hour_balance','Цагийн балансаас хамаарах'),
			('tomyo','Томьёо'),
			('query','Query'),
			('depend','Бусдаас хамаарах'),
		], string='Хамаарал', 
		default=lambda self: self._context.get('fixed'),
		tracking=True,required=True)
	salary_type = fields.Selection([
			('undsen','Үндсэн'),
			('turshilt','Туршилт'),
			('contract','Contract'),
			('tsag','Цагийн'),
			('all','Бүх ажилтанд'),
		], string=u'Цалингийн төрөл', 
		default=lambda self: self._context.get('fixed'),
		tracking=True,required=True)
	tomyo = fields.Text(string='Томьёо', tracking=True)
	raw_query = fields.Text(string='Query')
	res_company_id = fields.Many2one('res.company', 'Компаний нэр', tracking=True)
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил', tracking=True)
	precent = fields.Float(string='Хувь', digits= dp.get_precision('Product Unit of Measure'),
		default=1, tracking=True)
	
	is_advance = fields.Boolean(string='Урьдчилгааных эсэх', tracking=True)
	is_average = fields.Boolean(string='Дундаж цалинд хамаарах эсэх', tracking=True)
	is_average_hour = fields.Boolean(string='Дундаж цагт хамаарах эсэх', tracking=True)
	depend_ids = fields.Many2many('hr.allounce.deduction.category',
		'categ_to_categ_rel', 'categ_id', 'child_id', string='Хамаарлууд',tracking=True )
	is_hour = fields.Boolean('Цаг', tracking=True)
	is_tree = fields.Boolean('Багана харагдах эсэх', default=True, tracking=True)
	is_ndsh = fields.Boolean('НДШ тооцох эсэх', tracking=True)
	allounce_deduction_id = fields.Many2one('payroll.fixed.allounce.deduction', string='Нэмэгдэл, Суутгал', tracking=True)
	hour_ids = fields.Many2many('hour.balance.dynamic.configuration', 'categ_to_conf_rel', 'categ_id', 'conf_id', string='Нэмэх Цагууд', tracking=True)
	hour_minus_ids = fields.Many2many('hour.balance.dynamic.configuration', 'categ_min_to_conf_rel', 'min_categ_id', 'min_conf_id', string='Хасах цагууд', tracking=True)
	hour_is_ids = fields.Many2many('hour.balance.dynamic.configuration', 'categ_is_to_conf_rel', 'is_categ_id', 'is_conf_id', string='Нөхцөл шалгах', tracking=True)
	work_location_ids = fields.Many2many('hr.work.location', string='Ажлын байршлууд', tracking=True)
# цалин данс
	property_account_salary_expenses_id = fields.Many2one('account.account', company_dependent=True,
        string="Үндсэн цалингийн зардал",
        domain="[('deprecated', '=', False), ('company_id', '=', current_company_id)]", tracking=True)
	property_account_salary_add_expenses_id = fields.Many2one('account.account', company_dependent=True,
        string="Нэмэгдэл цалингийн зардал",
        domain="[('deprecated', '=', False), ('company_id', '=', current_company_id)]", tracking=True)
	property_account_shi_expenses_id = fields.Many2one('account.account', company_dependent=True,
        string="НДШ зардал",
        domain="[('deprecated', '=', False), ('company_id', '=', current_company_id)]", tracking=True)
	ex_type = fields.Char('Зардлын төрөл', tracking=True)
	expense_type = fields.Selection([('expense','Үндсэн цалингийн зардал'),
					('allounce','Нэмэгдэл цалингийн зардал'),
					('shi','НДШ зардал')],'Зардлын төрөл', tracking=True)
	is_mail=fields.Boolean('Email илгээхгүй эсэх', default=False)

class confbalancesalary(models.Model):
	_name = "conf.balance.salary"

	name = fields.Char('1')

class SalaryAccountConf(models.Model):
	_name = "salary.account.conf"
	_inherit ='mail.thread'


	company_id=fields.Many2one('res.company', 'Компани')
	work_location_id=fields.Many2one('hr.work.location', 'Ажлын байршил')
	journal_id = fields.Many2one('account.journal', string='Журнал')
	
	account_payable_id = fields.Many2one('account.account', string='Өглөгийн данс')
	partner_id = fields.Many2one('res.partner', string='Харилцагч')

	account_ndsh_id = fields.Many2one('account.account', string='НДШ өглөгийн данс')
	account_pit_payable_id =fields.Many2one('account.account', string='ХХОАТ өглөгийн данс')
	ndsh_partner_id = fields.Many2one('res.partner', string='НДШ Харилцагч')
	pit_partner_id = fields.Many2one('res.partner', string='ХХОАТ Харилцагч')




