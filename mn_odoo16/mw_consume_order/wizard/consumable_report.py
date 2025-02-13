# -*- coding: utf-8 -*-

import calendar

import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo import api, models, fields, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import AccessError, UserError
import time

D_LEDGER = {'general': {'name': _('General Ledger'),
						'group_by': 'account_id',
						'model': 'account.account',
						'short': 'code',
						},
			'partner': {'name': _('Partner Ledger'),
						'group_by': 'partner_id',
						'model': 'res.partner',
						'short': 'name',
						},
			'journal': {'name': _('Journal Ledger'),
						'group_by': 'journal_id',
						'model': 'account.journal',
						'short': 'code',
						},
			'open': {'name': _('Open Ledger'),
					 'group_by': 'account_id',
					 'model': 'account.account',
					 'short': 'code',
					 },
			'aged': {'name': _('Aged Balance'),
					 'group_by': 'partner_id',
					 'model': 'res.partner',
					 'short': 'name',
					 },
			'analytic': {'name': _('Analytic Ledger'),
						 'group_by': 'analytic_account_id',
						 'model': 'account.analytic.account',
						 'short': 'name',
						 },

			}

class AccountAssetStandardLedgerReport(models.TransientModel):
	_name = 'consumable.report.standard.ledger.report'
	_description = "consumable report standard ledger report"

	name = fields.Char()
	report_ids = fields.One2many('consumable.report.standard.ledger', 'report_id')
	report_name = fields.Char()
	print_time = fields.Char()
	date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
	date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.')
	report_object_ids = fields.One2many('consumable.report.standard.object', 'report_id')

class AccountAssetStandardObject(models.TransientModel):
	'''Тайлангийн ангилал буюу Ажилтнаар, ангилалаар, агуулахаар, байрлалаар гм бүлэглэх
	'''
	_name = 'consumable.report.standard.object'
	_description = "consumable report standard object"
	_order = 'name, id'

	name = fields.Char()
	object_id = fields.Integer()
	report_id = fields.Many2one('consumable.report.standard.ledger.report')
	category_id = fields.Many2one('product.category', 'Category')
	partner_id = fields.Many2one('res.partner', 'Partner')
	branch_id = fields.Many2one('res.branch', 'Branch')


class ConsumableReportStandardLedger(models.TransientModel):
	_name = 'consumable.report.standard.ledger'
	_description = 'Account Standard Ledger'

	name = fields.Char(default=u'Ашиглагдаж байгаа хангамжийн материалын дэлгэрэнгүй тайлан')
	company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
	date_from = fields.Date(string='Start Date', help='Use to compute initial balance.')
	date_to = fields.Date(string='End Date', help='Use to compute the entrie matched with futur.')
	report_name = fields.Char('Report Name')
	old_temp = fields.Boolean('Old template.', default=True)
	report_id = fields.Many2one('consumable.report.standard.ledger.report')
	branch_ids = fields.Many2many('res.branch', relation='table_standard_report_branches')
	owner_emp_id = fields.Many2one('hr.employee', 'Owner')

	owner_id = fields.Many2one('res.partner', 'Owner')
	category_ids = fields.Many2many('consumable.material.category','report_category_rel','ledger_id','categ_id')

	department_id = fields.Many2one('hr.department',)
	branch_id = fields.Many2one('res.branch','Branch')
	is_short = fields.Boolean('Is short')
	is_posted = fields.Boolean('Одоо Ажиллаж буй?' ,default=True)
	
	def action_view_lines(self):
		self.ensure_one()
		self._pre_compute()
		context = dict(self._context)

		mod_obj = self.env['ir.model.data']

		# INIT query
		# Орлого зарлага хамтдаа
		search_res = mod_obj._xmlid_lookup('mw_consumable_order.view_consumable_standard_data_filter')[2]
		search_id = search_res and search_res[1] or False
		pivot_res = mod_obj._xmlid_lookup('mw_consumable_order.view_consumable_standard_data_pivot_view')[2]
		pivot_id = pivot_res and pivot_res[1] or False
		tree_res = mod_obj._xmlid_lookup('mw_consumable_order.view_consumable_standard_data_tree_view')[2]
		tree_id = tree_res and tree_res[1] or False
		graph_res = mod_obj._xmlid_lookup('mw_consumable_order.consumable_standard_data_graph_view')[2]
		graph_id = tree_res and graph_res[1] or False

		return {
				'name': _('Report'),
				'view_type': 'form',
				'view_mode': 'pivot,tree,graph',
				'res_model': 'consumable.standard.data',
				'view_id': False,
				'views': [(pivot_id, 'pivot'),(tree_id, 'tree'),(graph_id, 'graph')],
				'search_view_id': search_id,
				'domain': [('report_id','=',self.report_id.id),
						   ],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}                         

	def print_excel_report(self):
		self.ensure_one()
		self._pre_compute()
		return self.env.ref('mw_consume_order.action_consumable_standard_excel').report_action(self)

	def _get_name_report(self):
		report_name = 'asset detail report'
		return report_name

	def _owner_where(self):
		where=''
		if self.owner_emp_id:
			query = """select asset_id from asset_owner_emp_rel where emp_id = {0}""".format(self.owner_emp_id.id)
			self.env.cr.execute(query)
			ids=[]
			for line in self.env.cr.dictfetchall():
				ids.append(line['asset_id'])
			if len(ids)>1:
				where += ' WHERE asset_id in ('+','.join(map(str, ids))+') '
			elif len(ids)==1:
				where += ' WHERE asset_id = '+str(ids[0])+' '
		return where


	def _owner_select(self):
		query = """,(SELECT 
								array_agg(name) 
							 FROM hr_employee where id in (select emp_id from asset_owner_emp_rel where asset_id=report_data.asset_id )
							) as owners """
		return query
	

	def _job_select(self):
		query = """,(select name from hr_job where id =aca.job_id
							) as job """
		return query
	

	def _dep_select(self):
		query = """,(select name from hr_department where id =aca.owner_dep_id
							) as department """
		return query
		
	def _serial_select(self):
		query = """,aca.serial, aca.number,aca.internal_code """
		return query    
	

	def _date_select(self):
		query = """,CASE WHEN aca.purchase_date notnull then aca.purchase_date else aca.date end as idate """
		return query    
		
	
	def _pre_compute(self):
		vals = {'report_name': self._get_name_report(),
				'name': self._get_name_report(),
				'date_to': self.date_to if self.date_to else "2099-01-01",
				'date_from': self.date_from if self.date_from else "1970-01-01",
				}
		self.report_id = self.env['consumable.report.standard.ledger.report'].create(vals)
		
		first_capital_dict={}
		con_pool=self.env['consumable.material.in.use']
		con_line_obj=self.env['consumable.material.in.use.deprecaition.line']
		if self.owner_id:
			cons=con_pool.search([('owner_id','=',self.owner_id.id),('date','<=',self.date_to),('product_id','!=',False)])
		else:
			cons=con_pool.search([('date','<=',self.date_to),('product_id','!=',False)])
		
			
		if self.department_id:
			dep_ids = self.env['hr.department'].search([('parent_id','child_of',self.department_id.id)])
			if dep_ids:
				cons=con_pool.search([('department_id','in',dep_ids.ids),('date','<=',self.date_to),('product_id','!=',False)])
			else:
				cons=con_pool.search([('department_id','=',self.department_id.id),('date','<=',self.date_to),('product_id','!=',False)])
		if self.branch_id:

			if self.department_id:
				dep_ids = self.env['hr.department'].search([('parent_id','child_of',self.department_id.id)])
				if dep_ids:
					cons=con_pool.search([('department_id','in',dep_ids.ids),('branch_id','=',self.branch_id.id),('date','<=',self.date_to),('product_id','!=',False)])
				else:
					cons=con_pool.search([('department_id','=',self.department_id.id),('branch_id','=',self.branch_id.id),('date','<=',self.date_to),('product_id','!=',False)])
			else:
				cons=con_pool.search([('branch_id','=',self.branch_id.id),('date','<=',self.date_to),('product_id','!=',False)])
		categ_ids=[]
		for c in cons:
			categ_ids.append(c.product_id.categ_id)
		categ_ids=list(set(categ_ids))
		def key_get(p,o):
			res=str(p)+':'+o
			return res
		
		for category in categ_ids:
			obj_vals = {
				'name':'categ',
				'object_id':category.id,
				'category_id':category.id,
				'report_id':self.report_id.id
				}
			obj_id=self.env['consumable.report.standard.object'].create(obj_vals)
			if self.is_posted:
				cons_ids=con_pool.search([('id','in',cons.ids),('product_id.product_tmpl_id.categ_id','=',category.id),('state','=','progress'),('date','<=',self.date_to),('product_id','!=',False)])
			else:
				cons_ids=con_pool.search([('id','in',cons.ids),('product_id.product_tmpl_id.categ_id','=',category.id),('date','<=',self.date_to),('product_id','!=',False)])
			if self.is_short:
				cons_grouped_ids={}
				for line in cons_ids:
					init_val=0
					inc_val=0
					ex_val=0
					move_ex_val=0
					qty=0
					department=''        
					internal_code=''
					job=''
					branch_name=''
					type=''
					categ=''
					state=''
					owners=''
					price=1
					init_depr=0
					ex_depr=0
					for  dep in line.depreciation_line_ids:
						if dep.move_id:
							if dep.depreciation_date<self.date_from:
								init_depr+=dep.amount
							else:
								ex_depr+=dep.amount
					if line.state=='progress':
						state=u'Ашиглаж буй'
					elif line.state=='draft':
						state=u'Ноорог'
					elif line.state=='progress_done':
						state=u'Дууссан'
					if line.type_id:
						type=line.type_id.name
					if line.category_id:
						categ=line.category_id.name
					# if line.rest_amount>0:
					# 	price=line.rest_amount
					# if line.product_id.standard_price and price==1:
					# 	price=line.product_id.standard_price
					depended_lines = line.depreciation_line_ids.filtered(lambda r: r.depreciation_date < self.date_from)
					if depended_lines:
						price = depended_lines.sorted(key=lambda r: r.depreciation_date, reverse=True)[0].balance
					else:
						if line.rest_amount>0:
							price=line.amount
						# if line.product_id.standard_price and price==1:
						# 	price=line.product_id.standard_price
					if line.date<self.date_from:
						init_val=price
					elif line.date>=self.date_from:
						inc_val=price
					if line.type_id:
						type=line.type_id.name
					if line.category_id:
						categ=line.sudo().category_id.name
					qty=line.qty
					if len(line.owner_ids.ids)==1:
						o=line.owner_ids[0].name
					elif len(line.owner_ids.ids)>1:
						owners=''
						for l in line.owner_ids:
							owners+=l.name+', '
						o=owners
					else:
						o='null'
					key=key_get(line.product_id.id,o)
					if cons_grouped_ids.get(key):
									cons_grouped_ids[key]['init_val']+=init_val
									cons_grouped_ids[key]['inc_val']+=inc_val
									cons_grouped_ids[key]['ex_val']+=ex_val
									cons_grouped_ids[key]['move_ex_val']+=move_ex_val
									cons_grouped_ids[key]['qty']+=qty
									cons_grouped_ids[key]['init_depr']+=init_depr
									cons_grouped_ids[key]['ex_depr']+=ex_depr
									
					else:
									cons_grouped_ids[key]={
														'date':line.date,
														'owners':o,
														'branch_name':branch_name,
														'job':job,
														'department':department,
														'internal_code':internal_code,
														'line':line,
														'init_val':init_val,
														'inc_val':inc_val,
														'ex_val':ex_val,
														'move_ex_val':move_ex_val,
														'qty':qty,
														'init_depr':init_depr,
														'ex_depr':ex_depr,
														'state':state,
														'categ':categ,
														'type':type
														}
				for line in cons_grouped_ids:
					owners=cons_grouped_ids[line]['owners']
					branch_name=cons_grouped_ids[line]['branch_name']
					init_val=cons_grouped_ids[line]['init_val']-cons_grouped_ids[line]['init_depr']
					inc_val=cons_grouped_ids[line]['inc_val']
					ex_val=cons_grouped_ids[line]['ex_val']+cons_grouped_ids[line]['ex_depr']
					move_ex_val=cons_grouped_ids[line]['move_ex_val']
					qty=cons_grouped_ids[line]['qty']
					department=cons_grouped_ids[line]['department']
					internal_code=cons_grouped_ids[line]['internal_code']
					doc_number=cons_grouped_ids[line]['doc_number']
					job=cons_grouped_ids[line]['job']
					type=cons_grouped_ids[line]['type']
					categ=cons_grouped_ids[line]['categ']
					state=cons_grouped_ids[line]['state']
					l=cons_grouped_ids[line]['line']
					result=[]
					ex_list=[]
					query = """INSERT INTO  consumable_standard_data
					(wizard_id, create_uid, create_date, asset_id,  qty, date, initial_value,
					income_value,expense_value,final_value,report_id,report_obj_id,owner,branch,
					job,department,doc_number,internal_code,type,category,state)
					VALUES({0},{1},'{2}',{3},{4},'{5}',{6},{7},{8},{9},{10},{11},'{12}','{13}','{14}','{15}','{16}','{17}','{18}','{19}','{20}')
					""".format(self.id,1,time.strftime('%Y-%m-%d'),l.product_id.id,qty,l.date,init_val,
								inc_val,ex_val+move_ex_val+ex_depr,init_val+inc_val-(ex_val+move_ex_val+ex_depr),
								self.report_id.id,obj_id.id
								,owners,branch_name,job,department,doc_number,internal_code,type,categ,state
								)
					if self.category_ids:
						if categ in self.category_ids.mapped('name'):
							self.env.cr.execute(query)
					else:
						self.env.cr.execute(query)
			else:
				for line in cons_ids:
					owners=''
					branch_name=''
					init_val=0
					inc_val=0
					ex_val=0
					move_ex_val=0
					init_val=0
					inc_val=0
					ex_val=0
					move_ex_val=0
					qty=0
					department=''
					internal_code=''
					job=''
					type=''
					categ=''
					state=''
					if line.branch_id.name:
						branch_name = line.branch_id.name
					if line.state=='progress':
						state=u'Ашиглаж буй'
					elif line.state=='draft':
						state=u'Ноорог'
					elif line.state=='progress_done':
						state=u'Дууссан'
					if line.owner_id:
						owners=line.owner_id.name
					for l in line.owner_ids:
						owners+=l.name+', '
					doc_number=line.doc_number
					if line.type_id:
						type=line.type_id.name
					if line.category_id:
						categ=line.category_id.name
					qty=line.qty

					# Эхний өртөг
					init_value=0 
					# Орлогын өртөг
					income_value=0
					# Зарлага өртөг
					expense_value=0
					# Эцсийн өртөг
					final_value=0

					# Тайлант хугацаанд элэгдсэн мөрүүд
					report_lines = line.depreciation_line_ids.filtered(lambda r: r.move_id and r.depreciation_date <= self.date_to)
					depreciated_lines = report_lines.filtered(lambda r: r.move_id and r.depreciation_date >= self.date_from)
					# Тайлант хугацаанаас гадуурх элэгдсэн мөрүүд
					none_depreciation_lines = report_lines.filtered(lambda r: r.move_id and (r.depreciation_date < self.date_from))
					none_depreciation_lines = none_depreciation_lines.sorted(key=lambda r: r.depreciation_date)
					is_depreciated = False
					if none_depreciation_lines and none_depreciation_lines[-1].balance == 0:
						is_depreciated = True
					balance = line.rest_amount_import - sum(none_depreciation_lines.mapped('amount')) if line.rest_amount_import > 0 else line.amount - sum(none_depreciation_lines.mapped('amount'))
					# cost = depreciated_lines[0].balance + depreciated_lines[0].amount if depreciated_lines else line.amount - line.depr_amount + sum(none_depreciation_lines.mapped('amount')) + sum(depreciated_lines.mapped('amount'))
					cost = balance
					if is_depreciated:
						cost = 0
					if line.date<self.date_from:
						init_value = cost
					elif line.date>=self.date_from:
						income_value = cost
	
					# if line.id == 111199:
					# 	print('amount: ', line.amount, ' depr_amount: ',line.depr_amount, ' depreciated: ',sum(depreciated_lines.mapped('amount')), ' rest_amount: ',line.rest_amount)
					expense_value = sum(depreciated_lines.mapped('amount')) if depreciated_lines else line.depr_amount - sum(none_depreciation_lines.mapped('amount'))
					if not depreciated_lines or is_depreciated:
						expense_value = 0
					final_value = init_value + income_value - expense_value

					# init_depr=line.depr_amount
					# ex_depr=0
					# for  dep in line.depreciation_line_ids.filtered(lambda r: r.depreciation_date <= self.date_to):
					# 	print(line.owner_id.name,line.depreciation_line_ids.mapped('amount'))
					# 	if dep.move_id:
					# 		if dep.depreciation_date<self.date_from:
					# 			init_depr+=dep.amount
					# 		else:
					# 			ex_depr+=dep.amount
						
					# price=1
					# # if line.rest_amount>0:
					# # 	price=line.rest_amount
					# # if line.product_id.standard_price and price==1:
					# # 	price=line.product_id.standard_price
					# depended_lines = line.depreciation_line_ids.filtered(lambda r: r.depreciation_date < self.date_from)
					# if depended_lines:
					# 	price = depended_lines.sorted(key=lambda r: r.depreciation_date, reverse=True)[0].balance
					# else:
					# 	if line.rest_amount>0:
					# 		# price=line.amount
					# 		price=line.rest_amount_import if line.rest_amount_import > 0 else line.amount
					# 	else:
					# 		price=line.rest_amount_import if line.rest_amount_import > 0 else line.amount
					# internal_code=line.product_id.default_code
					# if line.date<self.date_from:
					# 	init_val=price
					# elif line.date>=self.date_from:
					# 	inc_val=price
					# if line.type_id:
					# 	type=line.type_id.name
					# if line.category_id:
					# 	categ=line.category_id.name
					# qty=line.qty
					# result=[]
					# ex_list=[]
					# if line.id in [11688]:
					# 	print(line.id,'init_val: ',init_val, ' init_depr: ',init_depr, ' ex_depr: ', ex_depr, ' line.depr_amount: ', line.depr_amount, ' inc_val: ', inc_val,' ex_val: ', ex_val, 'move_ex_val: ', move_ex_val)
					# 	# print(aa)
					query = """INSERT INTO  consumable_standard_data
					(wizard_id, create_uid, create_date, asset_id,  qty, date, initial_value,
					income_value,expense_value,final_value,report_id,report_obj_id,owner,branch,
					job,department,doc_number,internal_code,type,category,state)
					VALUES({0},{1},'{2}',{3},{4},'{5}',{6},{7},{8},{9},{10},{11},'{12}','{13}','{14}','{15}','{16}','{17}','{18}','{19}','{20}')
					""".format(self.id,1,time.strftime('%Y-%m-%d'),line.product_id.id,qty,line.date,
							init_value, # Эхний
							income_value, # Орлого
							expense_value, # Зарлага
							final_value, # Эцсийн
							self.report_id.id,obj_id.id
							,owners,branch_name,job,department,doc_number,internal_code,type,categ,state
							)
					if line.product_id.id == 1394:
						print(init_val, '+',inc_val ,'-(',ex_val,'+',move_ex_val,')')
					if self.category_ids:
						if categ in self.category_ids.mapped('name'):
							self.env.cr.execute(query)
					else:
						self.env.cr.execute(query)

	def _sql_get_line_for_report(self, type_l, report_object=None):
		query = """SELECT
				d.*,t.default_code as code,t.name       
			FROM
				consumable_standard_data d 
				left join 
				product_product p on d.asset_id=p.id
				left join 
				product_template t on p.product_tmpl_id=t.id
			WHERE
				report_id = %s
			ORDER BY
				asset_id
			"""
		params = [self.report_id.id]

		self.env.cr.execute(query, tuple(params))
		result = self.env.cr.dictfetchall()
		return result
	
	def _sql_get_total_for_report(self, type_l, report_object=None):
		query = """SELECT
					sum(income_value) as income_value,
					sum(income_depr) as income_depr,
					sum(final_value) as final_value,
					sum(initial_value) as initial_value,
					sum(capital_value) as capital_value,
					sum(initial_depr) as initial_depr,
					sum(expense_depr) as expense_depr,
					sum(expense_value) as expense_value,
					sum(final_depr) as final_depr,
					sum(income_value) as income_value,
					sum(income_value) as income_value,
					'' as date,
					'' as code,
					'Total' as name
				FROM
					consumable_standard_data 
				WHERE
					report_id = %s
				"""
		params = [self.report_id.id]

		self.env.cr.execute(query, tuple(params))
		result  = self.env.cr.dictfetchall()   
		return result   

	def _format_total(self):
		if not self.company_currency_id:
			return
		lines = self.report_id.line_total_ids + self.report_id.line_super_total_id
		for line in lines:
			line.write({
				'debit': self.company_currency_id.round(line.debit) + 0.0,
				'credit': self.company_currency_id.round(line.credit) + 0.0,
				'balance': self.company_currency_id.round(line.balance) + 0.0,
				'current': self.company_currency_id.round(line.current) + 0.0,
				'age_30_days': self.company_currency_id.round(line.age_30_days) + 0.0,
				'age_60_days': self.company_currency_id.round(line.age_60_days) + 0.0,
				'age_90_days': self.company_currency_id.round(line.age_90_days) + 0.0,
				'age_120_days': self.company_currency_id.round(line.age_120_days) + 0.0,
				'older': self.company_currency_id.round(line.older) + 0.0,
			})
