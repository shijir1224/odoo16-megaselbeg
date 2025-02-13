
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning,UserError
from odoo.tools import float_compare, float_is_zero, float_round
from calendar import monthrange
from odoo.tools import float_compare
from math import copysign

class ConsumableMaterialInUse(models.Model):
	_name = 'consumable.material.in.use'
	_description = "consumable material in use"
	_order = 'date DESC'
	_rec_name = 'doc_number'
	_inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin','analytic.mixin']
	
	doc_number = fields.Char('Document number')
	product_id = fields.Many2one('product.product','Product', required=True)
	owner_id = fields.Many2one('res.partner','Owner')
	owner_ids = fields.Many2many('res.partner','consum_use_owner_rel','use_id','owner_id','Олон эзэшигч')
	related_product_move_id = fields.Many2one('stock.picking', string='Зарлагын баримт')
	transaction_date = fields.Date('Transaction Date') 
	date = fields.Date('Date', tracking=True, required=True)
	purchase_date = fields.Date(string='Худалдаж авсан огноо')
	end_date = fields.Date('End Date', tracking=True) 
	state = fields.Selection([('draft','Draft'),
							  ('progress','Progress'),
							  ('progress_done','Progress Done')],string='Status',default='draft')
	is_depreciate = fields.Boolean('Is Depreciate',default=False)
	depreciation_line_ids = fields.One2many('consumable.material.in.use.deprecaition.line','parent_id','History')
	account_count = fields.Integer(compute='_compute_account_count')
	expense_line_id = fields.Many2one('consumable.material.expense.line')
	note = fields.Char('Note')
	active = fields.Boolean(string='Active', default=True)
	is_project_partner = fields.Boolean(string="Төслийн харилцагч", default=False)

	price = fields.Float('Price')
	life = fields.Integer(string='Ашиглагдах хугацаа /сараар/', tracking=True)
	
	category_id = fields.Many2one('consumable.material.category')
	account_id = fields.Many2one('account.account', string='Зардлын данс')
	analytic_account_id = fields.Many2one('account.analytic.account', string='Шинжилгээний данс')
	type_id = fields.Many2one('consumable.material.type')
	depreciation_type = fields.Selection([('month','A Month'),('days','3 Times in a month')], string='Элэгдүүлэх хугацааны төрөл', default='month', tracking=True)
	depreciation_method_type = fields.Selection([('by_day','Өдрөөр'),('equal','Тэнцүү')], string='Элэгдүүлэлт бодох төрөл', default='by_day', tracking=True)
	date_type = fields.Selection([('tomorrow','Маргаашнаас сар бүрийн нийт хоногоор'),('first_date','Сар болгон тэнцүү')], string='Элэгдүүлэлт эхлэх өдөр', default='tomorrow', tracking=True)

	note_close = fields.Char('Note close')
	lot_id = fields.Many2one('consumable.material.lot')

	department_id = fields.Many2one('hr.department',)
	branch_id = fields.Many2one('res.branch','Branch')
	location_id = fields.Many2one('consumable.material.location','Location')

	qty = fields.Float('QTY',default=1, tracking=True)
	unit_price = fields.Float('Unit Price', default=1, tracking=True)
	amount = fields.Float('Өртөг',default=1, tracking=True)

	rest_amount_import = fields.Float('Үлдэгдэл өртөг /Import/')
	depr_amount_import = fields.Float('Х/Э /Import/')
	rest_amount = fields.Float('Үлдэгдэл өртөг', compute="_compute_depreciation", store=True)
	depr_amount = fields.Float('Х/Э', compute="_compute_depreciation")

	company_id = fields.Many2one(comodel_name="res.company",string="Company",default=lambda self: self.env.company,)
	history_ids = fields.One2many('consume.order.history', 'use_id','History')
	move_id = fields.Many2one('account.move')
	related_move_id = fields.Many2one('account.move',compute='_compute_am', store=True)
	is_allow_edit = fields.Boolean(string='Is Edit?', compute='_compute_allow_edit', readonly=1)

	@api.model
	def create(self, vals):
		if not vals.get('doc_number'):
			vals['doc_number'] = self.env['ir.sequence'].next_by_code('consumable.material.in.use') or _('New')
		return super(ConsumableMaterialInUse, self).create(vals)

	def force_doc_number(self):
		expense_ids = self.env['consumable.material.in.use'].search([('name','in',['Шинэ','New'])], order="create_date")
		for item in expense_ids:
			item.doc_number = self.env['ir.sequence'].next_by_code('consumable.material.in.use')

	@api.depends('depreciation_line_ids', 'depreciation_line_ids.move_id')
	def _compute_allow_edit(self):
		for item in self:
			depreciated_lines = item.depreciation_line_ids.mapped('move_id')
			if not depreciated_lines:
				item.is_allow_edit = True
			else:
				item.is_allow_edit = False

	@api.onchange('category_id')
	def _onchange_life(self):
		for using in self.filtered(lambda using: using.state in ['draft','progress']):
			if using.category_id and using.category_id.method_num <= 0:
				raise UserError(_("Ангилалын элэгдүүлэх хугацаагаа шалгана уу! {0}".format(using.category_id.name)))
			if using.life == 0:
				using.life = using.category_id.method_num
				using.expense_line_id.life = using.category_id.method_num
			if not using.account_id:
				using.account_id = using.category_id.ex_account_id.id
	
	@api.onchange('qty','unit_price')
	def onchange_amount(self):
		for item in self:
			item.write({'amount': item.qty * item.unit_price})

	def total_days(self, date, months=1):
		self.ensure_one()
		days = 0
		for month in range(months):
			month += 1
			date = date+relativedelta(months=month)
			days += monthrange(date.year,date.month)[1]

	@api.depends('depreciation_line_ids','depreciation_line_ids.move_id','rest_amount','depr_amount','depr_amount_import')
	def _compute_depreciation(self):
		for item in self:
			if item.depreciation_line_ids:
				item.depr_amount = item.depr_amount_import+sum(item.depreciation_line_ids.filtered(lambda r: r.move_id).mapped('amount'))
				item.rest_amount = item.amount - item.depr_amount
			else:
				if item.rest_amount_import or item.depr_amount_import:
					item.depr_amount = item.depr_amount_import
					item.rest_amount = item.amount - item.depr_amount
				else:
					if item.date and item.amount and item.depr_amount and item.life:
						item.total_days(item.date+relativedelta(days=1), item.life)
						date = item.date+relativedelta(months=item.life)
						days = monthrange(date.year,date.month)[1]

						item.depr_amount = item.depr_amount
						item.rest_amount = abs(item.amount - item.depr_amount)
					else:
						item.depr_amount = item.depr_amount
						item.rest_amount = abs(item.amount - item.depr_amount)

	def _compute_account_count(self):
		res = []
		for line in self:
			res = self.env['account.move'].search_count([('ref','=',line.id)])
			line.account_count = res
	

	def _compute_am(self):
		res = []
		for line in self:
			move_id=False
			if line.move_id:
				move_id=line.move_id.id
			elif line.expense_line_id and line.expense_line_id.related_product_move_id:
				res = self.env['account.move'].search([('stock_move_id','=',line.expense_line_id.related_product_move_id.id)],limit=1)
				if res:
					move_id=res.id
			line.related_move_id = move_id    

	@api.depends('owner_ids')
	def _compute_dep(self):
		dep=False
		if self.owner_ids:
			emp = self.env['hr.employee'].search([('partner_id','=',self.owner_ids[0].id)])
			dep=emp and emp.department_id and emp.department_id.id or False
		self.department_id = dep
		
	def button_account_move(self):
		res = []
		for line in self:
			res = self.env['account.move'].search([('ref','=',line.id)])
			return{
				'type': 'ir.actions.act_window',
				'name': _('Mrp Workorder '),
				'res_model': 'account.move',
				'view_type': 'form',
				'view_mode': 'tree,form',
				'view_id': False,
				'domain':[('id', 'in', res.ids)],
				}

	def edit_depreciation_board_amount(self):
		obj_ids = self.env['consumable.material.in.use'].search([('id','in',self._context['active_ids'])])
		for obj in obj_ids:
			obj.compute_depreciation_board(edit_only_amount=True)
  
	def compute_depreciation_board(self, edit_only_amount=None):
		self.ensure_one()
		# 1 болон бага дүнтэй үлдэгдэл өртөгтэй АБХМ элэгдүүлэхгүй.
		if self.rest_amount <= 1:
			return
		amount_change_ids = self.depreciation_line_ids.filtered(lambda x: not x.move_id).sorted(key=lambda l: l.depreciation_date)
		posted_depreciation_move_ids = self.depreciation_line_ids.filtered(lambda x: x.move_id).sorted(key=lambda l: l.depreciation_date)
		already_depreciated_amount = sum([m.amount for m in posted_depreciation_move_ids])
		depreciation_number = self.life
		starting_sequence = 0
		invoiced_lines = self.depreciation_line_ids.filtered(lambda r: r.move_id).sorted(key='depreciation_date')
		amount_to_depreciate = self.amount

		depreciation_date = invoiced_lines[-1].depreciation_date if invoiced_lines else self.date+relativedelta(days=1)
		# элэгдүүлэх сарын тоог авах
		depreciation_months = self.life - len(invoiced_lines) if invoiced_lines else self.life
		# нийт өдөрийг авах
		# Түр дарлаа алдаа заагаад байна Purchase date hooson         #    
		if self.purchase_date:
			depreciation_number = ((self.purchase_date + relativedelta(months=self.life)) - self.purchase_date).days
		else:
			depreciation_number = ((self.date + relativedelta(months=self.life)) - self.date).days
		# if we already have some previous validated entries, starting date is last entry + method period
		if posted_depreciation_move_ids and posted_depreciation_move_ids[-1].depreciation_date:
			last_depreciation_date = fields.Date.from_string(posted_depreciation_move_ids[-1].depreciation_date)
			# in case we unpause the asset darmaa = nemev
			if last_depreciation_date >= depreciation_date:  
				depreciation_date = last_depreciation_date + relativedelta(months=1)
		commands = [(2, line_id.id, False) for line_id in self.depreciation_line_ids.filtered(lambda x: not x.move_id)]
		dpr_amount=amount_to_depreciate/depreciation_number
		newlines=[]
		balance=self.rest_amount
		month = 0 if invoiced_lines else 0
		
		depreciation_months = depreciation_months - 1 if invoiced_lines else depreciation_months
		# self.depreciation_method_type
		sequence = 1
		while balance>0:
			if self.depreciation_type == 'month' or self.depreciation_method_type == 'equal':
				number_of_month = 1
				date = depreciation_date+relativedelta(months=month)
				days = monthrange(date.year,date.month)[1]
				if self.date_type == 'tomorrow' and  depreciation_date.month == date.month and depreciation_date.year == date.year:
					days = monthrange(date.year,date.month)[1] - depreciation_date.day + 1
				# if self.date_type == 'hybrid' and depreciation_date.month == date.month and depreciation_date.year == date.year:
				# 	days = monthrange(date.year,date.month)[1] - depreciation_date.date + 1
				monthly_amount = self.amount/self.life if self.depreciation_method_type == 'equal' and not (depreciation_date.month == date.month and depreciation_date.year == date.year) else dpr_amount * days
				if self.depreciation_method_type == 'equal' and self.date_type == 'first_date':
					monthly_amount = self.amount/self.life
				if balance <= monthly_amount:
					monthly_amount  = balance
				balance -= monthly_amount
				if self.life < month + 1:
					monthly_amount += balance
				percent = monthly_amount*100/self.amount
				if monthly_amount > 0:
					newlines.append({'amount':monthly_amount,
									'depreciated_percent':percent,
									'depreciation_date':'{0}-{1}-{2}'.format(date.year, date.month, monthrange(date.year,date.month)[1]),
									'balance': balance,
									'owner_id':self.owner_id and self.owner_id.id or False,
									'analytic_distribution': self.analytic_distribution if self.analytic_distribution else False,
									'sequence': sequence,
									})
					sequence += 1
					amount_to_depreciate-=monthly_amount
			else:
				date = depreciation_date+relativedelta(months=month)
				if depreciation_date.day > 20 and depreciation_date.year == date.year and depreciation_date.month == date.month:
					number_of_month = 1
				elif depreciation_date.day > 10 and depreciation_date.year == date.year and depreciation_date.month == date.month:
					number_of_month = 2
				else:
					number_of_month = 3
				for i in range(number_of_month):
					date = depreciation_date+relativedelta(months=month)
					if i == number_of_month-1:
						last_day = monthrange(date.year,date.month)[1]
						days = monthrange(date.year,date.month)[1] - i*10
					elif number_of_month == 2 and i == 0:
						last_day = number_of_month*10
						days = 10
					else:
						last_day = (i+1)*10
						days = 10
					if date.year == depreciation_date.year and date.month == depreciation_date.month and depreciation_date.day == date.day and i == 0:
						days = abs(last_day - depreciation_date.day + 1)
					##############################
					# Forece days fix !!!
					if days > 11:
						days = 10
					##############################
					monthly_amount = dpr_amount * days
					if balance <= monthly_amount:
						monthly_amount  = balance
					balance -= monthly_amount
					percent = monthly_amount*100/self.amount
					newlines.append({'amount':monthly_amount,
									'depreciated_percent':percent,
									'depreciation_date':'{0}-{1}-{2}'.format(date.year,date.month,last_day),
									'balance':balance,
									'owner_id':self.owner_id and self.owner_id.id or False,
									'analytic_distribution': analytic_distribution if analytic_distribution else False,
									'sequence': sequence,
									})
					sequence += 1
					amount_to_depreciate-=monthly_amount
					if balance == 0:
						break
			month += 1

		newline_vals_list = []
		for newline_vals in newlines:
			newline_vals_list.append(newline_vals)
		if edit_only_amount:
			index = 0
			for line_id in self.depreciation_line_ids.sorted(key= lambda r: r.depreciation_date):
				line_id.amount = newline_vals_list[index]['amount']
				line_id.balance = newline_vals_list[index]['balance']
				index += 1
		else:
			new_moves = self.env['consumable.material.in.use.deprecaition.line'].create(newline_vals_list)
			for move in new_moves:
				commands.append((4, move.id))
			return self.with_context(force_delete=True).write({'depreciation_line_ids': commands})

	def button_create_move(self,entry_date,src_account_id):
		move_obj = self.env['account.move']
		for asset in self:
			if asset.move_id:
				raise UserError(u'Хөрөнгийн гүйлгээ үүссэн (%s)..' % asset.doc_number)
			if not asset.category_id:
				raise UserError(u'Хөрөнгө дээр ангилал сонгоогүй байна (%s)..' % asset.doc_number)
			if not asset.category_id.account_id:
				raise UserError(u'Хөрөнгийн ангилал дээр данс сонгоогүй байна (%s)..' % asset.category_id.name)
			if not asset.category_id.journal_id:
				raise UserError(u'Хөрөнгийн ангилал дээр журнал сонгоогүй байна (%s)..' % asset.category_id.name)

			year=entry_date.year
			asset_amount = asset.rest_amount
			line_ids = [(0,0,{
				'name': asset.doc_number and asset.doc_number or (asset.product_id and asset.product_id.name)+':'+str(asset.id),
				'ref': asset.doc_number,
				'account_id': asset.category_id.account_id.id,
				'debit': asset_amount,
				'credit': 0.0,
				'journal_id': asset.category_id.journal_id.id,
				'date': entry_date,
			}),(0,0,{
				'name': asset.doc_number and asset.doc_number or (asset.product_id and asset.product_id.name)+':'+str(asset.id),
				'ref': asset.doc_number,
				'account_id': src_account_id,
				'debit': 0.0,
				'credit': asset_amount,
				'journal_id': asset.category_id.journal_id.id,
				'date': entry_date,
			})]
			move_vals = {
				'name': '/',
				'date': entry_date,
				'ref': asset.doc_number,
				'journal_id': asset.category_id.journal_id.id,
				'line_ids': line_ids
			}
			if asset.is_project_partner:
				move_vals.update({'partner_id': asset.branch_id.partner_id.id})
			move_id = move_obj.create(move_vals)
			move_id.action_post()
			asset.write({'move_id':move_id.id})
				
	def button_progress(self):
		context = self.env.context
		if context is None:
			context = self._context or {}
		print ('aa')
		for line in self:
			consume = line.env['consumable.material.expense'].search([('doc_number','=',line.doc_number)],limit=1)
			
			stock_picking = self.env['stock.picking']
			stock_move = self.env['stock.move']
			stock_picking_type = self.env['stock.picking.type']
			
			picking_obj = self.env['stock.picking.type'].search([('warehouse_id.id','=',consume.warehouse_id.id),('code','=','outgoing')],limit=1)
			desc_obj = self.env['stock.location'].search([('usage','=','customer')],limit=1)

			if context and context.get('create_aml',False) and context.get('src_account_id', False):
				entry_date = context.get('entry_date', line.date)
				self.button_create_move(entry_date,context['src_account_id'])

			#Элэгдэл тооцох хэсэг
			if line.is_depreciate == True: 
					if line.life and not line.depreciation_line_ids:
						line.compute_depreciation_board()

					if line.depreciation_line_ids:
						line.state = 'progress'
					if not line.life:
						raise UserError(_(u'Ашиглах хугацаа оруулана уу.'))
			line.state = 'progress'

	def action_doned_consumable_view(self):
		action = self.env.ref('mw_consume_order.action_doned_consumable_continue').read()[0]
		action['target'] = 'new'
		return action

	def button_done(self):
		for consume_material in self:
			view = consume_material.env.ref('mw_consume_order.view_consumable_material_in_use_wizard')
			return {
				'name': _('Account?'),
				'type': 'ir.actions.act_window',
				'view_type': 'form',
				'view_mode': 'form',
				'res_model': 'consumable.material.in.use.wizard',
				'views': [(view.id, 'form')],
				'view_id': view.id,
				'target': 'new'
			}
			
	def button_draft(self):
		for line in self:
			line.state = 'draft'
	
	@api.model
	def create(self, vals):
		return super(ConsumableMaterialInUse, self).create(vals)

	def unlink(self):
		for expense in self:
			if expense.state not in ['draft']:
				raise UserError(u'Батлагдсан АБХМ-н элэгдүүлэлт устгахгүй!!!')
		super(ConsumableMaterialInUse, self).unlink()

	def compute_selected_in_use_depreciation(self):
		obj_ids = self.env['consumable.material.in.use'].search([('id','in',self._context['active_ids'])])
		for item in obj_ids.filtered(lambda r: r.state in ('draft','progress')):
			item.compute_depreciation_board()

	def action_set_to_close(self):
		""" Returns an action opening the asset pause wizard."""
		self.ensure_one()
		new_wizard = self.env['consumable.material.sell'].create({
			'using_id': self.id,
		})
		return {
			'name': _('Sell Consumable Material'),
			'view_mode': 'form',
			'res_model': 'consumable.material.sell',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': new_wizard.id,
		}

	# def set_to_close_v2(self, invoice_line_id, date=None, account_id=None, analytic_distribution=None, sell_type=None):
	# 	self.ensure_one()
	# 	disposal_date = date or fields.Date.today()
	# 	delete_lines = self.depreciation_line_ids.filtered(lambda r: r.depreciation_date > date)
	# 	delete_lines.unlink()
	# 	post_lines = self.depreciation_line_ids.filtered(lambda r: r.depreciation_date.year <= date.year and r.depreciation_date.month < date.month and r.move_id is null)
	# 	current_line = self.depreciation_line_ids.filtered(lambda r: r.depreciation_date.year == date.year and r.depreciation_date.month == date.month)
	# 	if post_lines:
	# 		post_lines.action_post()
	# 	sequence = max(self.depreciation_line_ids.mapped('sequence'))+1 if self.depreciation_line_ids else 1
	# 	if current_line.depreciation_date == date:
	# 		current_line.amount = self.res_amount
	# 		current_line.depreciated_percent = self.res_amount*100/self.amount
	# 		current_line.balance = 0
	# 		current_line.sequence = current_line
	# 		current_line.analytic_distribution = analytic_distribution if analytic_distribution else False,
	# 		current_line.owner_id = self.owner_id.id if self.owenr_id else False

	def set_to_close(self, invoice_line_id, date=None, account_id=None, analytic_distribution=None, sell_type=None):
		self.ensure_one()
		disposal_date = date or fields.Date.today()
		undepreciated_lines = self.depreciation_line_ids.filtered(lambda r: not r.move_id)
		board_dates = self.depreciation_line_ids.mapped('depreciation_date')
		if self.depreciation_type == 'days':
			close_date = disposal_date
			days = monthrange(close_date.year,close_date.month)[1]
			if close_date.day <= 10:
				day = 10
			elif close_date.day <= 20:
				day = 20
			elif close_date.day <= 31:
				day = days
			match_lines = undepreciated_lines.filtered(lambda r: r.depreciation_date.year == close_date.year and r.depreciation_date.month == close_date.month and r.depreciation_date.day == day)
			future_lines = undepreciated_lines - match_lines
		else:
			close_date = disposal_date
			days = monthrange(close_date.year,close_date.month)[1]
			future_lines = undepreciated_lines.filtered(lambda r: r.depreciation_date > close_date)
		current_line = self.depreciation_line_ids.filtered(lambda r: r.depreciation_date.year == disposal_date.year and r.depreciation_date.month == disposal_date.month and not r.move_id)
		future_lines = future_lines - current_line if current_line else future_lines
		future_lines.unlink()
		for item in (self.depreciation_line_ids - current_line).filtered(lambda r: not r.move_id):
			item.action_post()

		full_asset = self
		move_ids = full_asset._get_disposal_moves([invoice_line_id] * len(full_asset), disposal_date)

		# ###
		is_create = True if [disposal_date for b_day in board_dates if b_day.year == disposal_date.year and b_day.month == disposal_date.month] else False
		depr_amount = self.depr_amount_import+sum(self.depreciation_line_ids.filtered(lambda r: r.move_id).mapped('amount'))
		umnukh_lines = self.depreciation_line_ids.filtered(lambda r: r.depreciation_date.year <= disposal_date.year and r.depreciation_date.month < disposal_date.month)
		rest_amount = umnukh_lines[-1].balance if umnukh_lines else self.rest_amount
		if current_line and is_create:
			# current_line.unlink()
			depr_amount = self.depr_amount_import+sum(self.depreciation_line_ids.filtered(lambda r: r.move_id).mapped('amount'))
			# rest_amount = self.amount - self.depr_amount
			amount_to_depreciate = self.amount
			if self.purchase_date:
				depreciation_number = ((self.purchase_date + relativedelta(months=self.life)) - self.purchase_date).days
			else:
				depreciation_number = ((self.date + relativedelta(months=self.life)) - self.date).days
			dpr_amount=amount_to_depreciate/depreciation_number
			days = disposal_date.day - 1
			sequence = max(self.depreciation_line_ids.mapped('sequence'))+1 if self.depreciation_line_ids else 1
			vals = {
				'amount': dpr_amount*days,
				'depreciated_percent': dpr_amount*days*100/self.amount,
				'depreciation_date':'{0}-{1}-{2}'.format(disposal_date.year,str(disposal_date.month).zfill(2),str(disposal_date.day-1 if disposal_date.day>1 else disposal_date.day).zfill(2)),
				'balance': rest_amount - dpr_amount*days,
				'owner_id':self.owner_id and self.owner_id.id or False,
				'analytic_distribution': analytic_distribution if analytic_distribution else False,
				'sequence': sequence,
			}
			print('current_linecurrent_line: ')
			print(self.depreciation_line_ids.mapped('depreciation_date'))
			print(self.depreciation_line_ids.mapped('amount'))
			print(dpr_amount, days, self.rest_amount)
			current_amount = dpr_amount*days
			vldegdel_amount = self.rest_amount
			is_pass = False
			if vldegdel_amount <= current_amount:
				is_pass = True
				current_amount = self.rest_amount
			print({
				'amount': current_amount,
				'depreciated_percent': current_amount*100/self.amount,
				'depreciation_date':'{0}-{1}-{2}'.format(disposal_date.year,str(disposal_date.month).zfill(2),str(disposal_date.day-1 if disposal_date.day>1 else disposal_date.day).zfill(2)),
				'balance': rest_amount - current_amount,
				'owner_id':self.owner_id and self.owner_id.id or False,
				'analytic_distribution': analytic_distribution if analytic_distribution else False,
				'sequence': sequence,
			})
			current_line.write(vals)
			last = current_line
			# last = self.depreciation_line_ids.create(vals)
			# last.parent_id = self.id
			last.depreciation_date = '{0}-{1}-{2}'.format(disposal_date.year,str(disposal_date.month).zfill(2),str(disposal_date.day-1 if disposal_date.day>1 else disposal_date.day).zfill(2))
			print('last.depreciation_date', last.depreciation_date)
			last.action_post()
			if is_pass:
				return self._return_disposal_view(move_ids)
		# ###
		res_amount = self.amount - depr_amount + sum(self.depreciation_line_ids.mapped('amount'))
		# last = self.depreciation_line_ids.create({
		# 	'depreciation_date': close_date,
		# 	'amount': res_amount,
		# 	'owner_id':self.owner_id and self.owner_id.id or False,
		# 	'analytic_distribution': analytic_distribution if analytic_distribution else False,
		# })
		# last.parent_id = self.id
		# for item in self.depreciation_line_ids.filtered(lambda r: not r.move_id):
		# 	item.action_post()
		self.state = 'progress_done'
		self.end_date = disposal_date
		self.note_close = sell_type
		note = 10000 + int(self.id)
		stock_obj = self.env['stock.picking'].search([('note','=',note)],limit=1)
		check_value = False
		res = []
		consume_obj = self.env['consumable.material.expense'].search([('doc_number', '=', self.doc_number)])
		res = self.env['consumable.material.in.use'].search([('doc_number', '=', self.doc_number)])
		for i in res:
			if i.state != 'progress_done':
				check_value = True
		if check_value == False:
			consume_obj.state = 'done'
		if stock_obj and stock_obj.state not in ['done','cancel']:
			stock_obj.action_confirm()
			stock_obj.force_assign()
			wiz = self.env['stock.immediate.transfer'].create({'pick_id': stock_obj.id})
			wiz.force_date = self.date
			wiz.process()
			if stock_obj.state == 'done':
				self.state = 'progress_done'
				self.note_close = sell_type
		full_asset = self
		# move_ids = full_asset._get_disposal_moves([invoice_line_id] * len(full_asset), disposal_date)
		full_asset.write({'state': 'progress_done', 'end_date': disposal_date})
		context=dict(self._context)
		context.update({'src_account_id': full_asset.category_id.account_id.id,
						'entry_date': disposal_date
						})
		move_obj = self.env['account.move']
		year=disposal_date.year
		src_account_id = full_asset.category_id.account_id if not account_id else account_id
		debit_account_id = False
		credit_account_id = False
		print('full_asset.rest_amount', full_asset.rest_amount)
		asset_amount = full_asset.rest_amount
		if sell_type == 'sell':
			debit_account_id = full_asset.category_id.account_id
			credit_account_id = src_account_id
		elif sell_type == 'dispose':
			debit_account_id = src_account_id
			credit_account_id = full_asset.category_id.account_id
		if debit_account_id and credit_account_id:
			line_ids = [(0,0,{
				'name': full_asset.doc_number or '' if full_asset.doc_number else full_asset.product_id.name or '' + ':'+str(full_asset.id),
				'ref': full_asset.doc_number,
				'account_id': debit_account_id.id,
				'analytic_distribution': analytic_distribution if analytic_distribution else False,
				'debit': asset_amount,
				'credit': 0.0,
				'journal_id': full_asset.category_id.journal_id.id,
				'date': disposal_date,
			}),(0,0,{
				'name': full_asset.doc_number or '' if full_asset.doc_number else full_asset.product_id.name or '' + ':'+str(full_asset.id),
				'ref': full_asset.doc_number,
				'account_id': credit_account_id.id,
				'analytic_distribution': analytic_distribution if analytic_distribution else False,
				'debit': 0.0,
				'credit': asset_amount,
				'journal_id': full_asset.category_id.journal_id.id,
				'date': disposal_date,
			})]
			move_vals = {
				'name': '/',
				'date': disposal_date,
				'ref': full_asset.doc_number,
				'partner_id': full_asset.owner_id.id,
				'journal_id': full_asset.category_id.journal_id.id,
				'line_ids': line_ids
			}
			if self.is_project_partner:
				move_vals.update({'partner_id': self.branch_id.partner_id.id})
			move_id = move_obj.create(move_vals)
			move_id.action_post()
			if not self.depreciation_line_ids.filtered(lambda r: not r.move_id):
				print(res_amount,'\n', {
					'parent_id': self.id,
					'depreciation_date': disposal_date,
					'owner_id': self.owner_id.id,
					'amount': res_amount,
					'analytic_distribution': analytic_distribution if analytic_distribution else False,
				})
				self.env['consumable.material.in.use.deprecaition.line'].create({
					'parent_id': self.id,
					'depreciation_date': disposal_date,
					'owner_id': self.owner_id.id,
					'amount': res_amount,
					'analytic_distribution': analytic_distribution if analytic_distribution else False,
				})
			if not self.depreciation_line_ids.filtered(lambda r: not r.move_id):
				raise UserError(('Сүүлийн элэгдүүлэлтийн мөр олдохгүй байна.'))
			last_line =  self.depreciation_line_ids.filtered(lambda r: not r.move_id)
			last_line.move_id = move_id.id
			last_line.amount = asset_amount
			print('last_line',last_line.depreciation_date, asset_amount)
   # print(aa)
			last_line.balance = 0
			last_line.depreciated_percent = asset_amount/self.amount*100
			last_line._compute_percent_name()
			if move_ids:
				return self._return_disposal_view(move_ids)
		else:
			raise UserError(('Данс олдсонгүй'))

	def _get_disposal_moves(self, invoice_line_ids, disposal_date):
		def get_line(asset, amount, account):
			return (0, 0, {
				'name': asset.name,
				'account_id': account.id,
				'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
				'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
				'analytic_account_ids': [account_analytic_id.id] if asset.asset_type == 'sale' else False,
				'currency_id': company_currency != current_currency and current_currency.id or False,
				'amount_currency': company_currency != current_currency and - 1.0 * asset.value_residual or 0.0,
			})

		move_ids = []
		assert len(self) == len(invoice_line_ids)
		for asset, invoice_line_id in zip(self, invoice_line_ids):
			move_ids = asset.depreciation_line_ids.mapped('move_id')
			account_analytic_id = asset.analytic_account_id
			company_currency = asset.company_id.currency_id
			current_currency = asset.analytic_account_id.currency_id
			prec = company_currency.decimal_places
			unposted_depreciation_move_ids = move_ids.filtered(lambda x: x.state == 'draft')
			if unposted_depreciation_move_ids:
				old_values = {
					'method_number': asset.method_number,
				}

				# Remove all unposted depr. lines
				commands = [(2, line_id.id, False) for line_id in unposted_depreciation_move_ids]

				# Create a new depr. line with the residual amount and post it
				asset_sequence = len(asset.depreciation_move_ids) - len(unposted_depreciation_move_ids) + 1

				initial_amount = asset.original_value
				initial_account = asset.original_move_line_ids.account_id if len(asset.original_move_line_ids.account_id) == 1 else asset.account_asset_id
				depreciated_amount = copysign(sum(asset.depreciation_move_ids.filtered(lambda r: r.state == 'posted').mapped('amount_total')), -initial_amount)
				depreciation_account = asset.account_depreciation_id
				invoice_amount = copysign(invoice_line_id.price_subtotal, -initial_amount)
				invoice_account = invoice_line_id.account_id
				difference = -initial_amount - depreciated_amount - invoice_amount
				difference_account = asset.company_id.gain_account_id if difference > 0 else asset.company_id.loss_account_id
				line_datas = [(initial_amount, initial_account), (depreciated_amount, depreciation_account), (invoice_amount, invoice_account), (difference, difference_account)]
				if not invoice_line_id:
					del line_datas[2]
				vals = {
					'amount_total': current_currency._convert(asset.value_residual, company_currency, asset.company_id, disposal_date),
					'asset_id': asset.id,
					'ref': asset.name + ': ' + (_('Disposal') if not invoice_line_id else _('Sale')),
					'asset_remaining_value': 0,
					'asset_depreciated_value': max(asset.depreciation_move_ids.filtered(lambda x: x.state == 'posted'), key=lambda x: x.date, default=self.env['account.move']).asset_depreciated_value,
					'date': disposal_date,
					'journal_id': asset.journal_id.id,
					'line_ids': [get_line(asset, amount, account) for amount, account in line_datas if account],
				}
				commands.append((0, 0, vals))
				asset.write({'depreciation_move_ids': commands, 'method_number': asset_sequence})
				tracked_fields = self.env['account.asset'].fields_get(['method_number'])
				changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
				if changes:
					asset.message_post(body=_('Asset sold or disposed. Accounting entry awaiting for validation.'), tracking_value_ids=tracking_value_ids)
				move_ids += self.env['account.move'].search([('asset_id', '=', asset.id), ('state', '=', 'draft')]).ids

		return move_ids

	def _return_disposal_view(self, move_ids):
		name = _('Disposal Move')
		view_mode = 'form'
		if len(move_ids) > 1:
			name = _('Disposal Moves')
			view_mode = 'tree,form'
		return {
			'name': name,
			'view_mode': view_mode,
			'res_model': 'account.move',
			'type': 'ir.actions.act_window',
			'target': 'current',
			'res_id': move_ids[-1].id,
			'domain': [('id', 'in', move_ids.ids)]
		}

class ConsumableMaterialInUseDeprecaitionLine(models.Model):
	_name = 'consumable.material.in.use.deprecaition.line'
	_description = "consumable material in use deprecaition line"
	_inherit = ['analytic.mixin']
	  
	@api.model
	def _get_employee(self):
		print ('self ',self)
		employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
		partner=False
		if partner:
			return partner.id
		elif employee:
			if employee[0].partner_id:
				return employee[0].partner_id.id
		else:
			return False
			
	sequence = fields.Integer(string='Created sequence', readonly=True)
	amount = fields.Float('Amount')
	depreciation_date = fields.Date('Depreciation Date')#,default=lambda self: fields.Datetime.now()
	limit_date = fields.Date('Limit Date', readonly=True)
	balance = fields.Float('Balance')
	owner_id = fields.Many2one('res.partner', string='Employee',default=_get_employee)
	depreciated_percent = fields.Float('Depreciated Percent', default=0)
	percent_name = fields.Char('Depreciated Percent', compute='_compute_percent_name')
	parent_id = fields.Many2one('consumable.material.in.use', string='Parent')
	move_id = fields.Many2one('account.move', string='Move')
	account_id = fields.Many2one(related="parent_id.account_id", string='Зардлын данс')
	analytic_account_id = fields.Many2one(related="parent_id.analytic_account_id", string='Шинжилгээний данс')
	product_id = fields.Many2one(related="parent_id.product_id", string='Product')

	@api.depends('depreciation_date')
	def onchange_depreciation_date(self):
		for item in self:
			brother_id = self.env['consumable.material.in.use.deprecaition.line'].search([('parent_id.id','=',item.parent_id.id),('sequence','<', item.sequence)], limit=1, order="sequence desc")
			item.limit_date = brother_id.depreciation_date if brother_id else item.parent_id.date
			if item.limit_date >= item.depreciation_date:
				raise UserError(('{0} өдрөөс хойшоо сонгоно уу!').format(limit_date))

	def write(self, vals):
		if vals.get('depreciation_date', False):
			limit_date = self.limit_date or vals.get('limit_date', False)
			if limit_date and vals['depreciation_date'] <= limit_date:
				raise UserError(('{0} өдрөөс хойшоо сонгоно уу!').format(limit_date))
		return super(ConsumableMaterialInUseDeprecaitionLine, self).write(vals)
 
	@api.depends('depreciated_percent')
	def _compute_percent_name(self):
		for item in self:
			item.percent_name = str(round(item.depreciated_percent,2)) + ' %'

	def compute_selected_action_post(self):
		obj_ids = self.env['consumable.material.in.use.deprecaition.line'].search([('id','in',self._context['active_ids'])])
		for item in obj_ids.filtered(lambda r: r.parent_id.state in ('progress')):
			item.action_post()

	def action_post(self):
		print('action_postaction_postaction_post')
		move_obj=self.env['account.move']
		for asset in self:
			print('asset.move_id', asset.move_id, asset.move_id)
			if asset.move_id:
				continue
			asset_amount=asset.amount
			entry_date=asset.depreciation_date
			print('entry_date!!!!!!:', entry_date)
			if not asset.parent_id.related_move_id:
				raise UserError(u'Хөрөнгийн гүйлгээ үүсээгүй байна (%s)..' % asset.parent_id.doc_number)
			if not asset.parent_id.product_id:
				raise UserError(u'Бараа сонгоогүй байна (%s)..' % asset.parent_id.doc_number)
			if not asset.parent_id.category_id:
				raise UserError(u'Бараан дээр ангилал сонгоогүй байна (%s)..' % asset.parent_id.doc_number)
			account_id = asset.parent_id.account_id
			if not account_id:
				raise UserError(u'Зардлын данс сонгоогүй байна (%s)..' % asset.parent_id.category_id.name)
				
			parent_analytic_id = asset.parent_id.analytic_account_id if asset.parent_id else False
			analytic_account_id = parent_analytic_id if parent_analytic_id else asset.parent_id.department_id.analytic_account_id if asset.parent_id.department_id else False
			line_ids = [(0,0,{
				'product_id': asset.parent_id.product_id.id,
				'name': asset.parent_id.product_id.name + '| зардал тооцов',
				'ref': asset.parent_id.doc_number,
				'account_id': account_id.id,
				'debit': asset_amount,
				'credit': 0.0,
				'journal_id': asset.parent_id.related_move_id.journal_id.id,
				'branch_id': asset.parent_id.branch_id.id if asset.parent_id.branch_id else False,
				'date': entry_date,
				'analytic_account_ids':[analytic_account_id.id] if analytic_account_id else False,
				'analytic_distribution': asset.analytic_distribution if asset.analytic_distribution else False
			}),(0,0,{
				'product_id': asset.parent_id.product_id.id,
				'name': asset.parent_id.product_id.name + '| зардал тооцов',
				'ref': asset.parent_id.doc_number,
				'account_id': asset.parent_id.related_move_id.line_ids.filtered(lambda x: not x.credit>0).account_id.id,
				'debit': 0.0,
				'credit': asset_amount,
				'journal_id': asset.parent_id.related_move_id.journal_id.id,
				'branch_id': asset.parent_id.branch_id.id if asset.parent_id.branch_id else False,
				'date': entry_date,
				'analytic_distribution': asset.analytic_distribution if asset.analytic_distribution else False
			})]
			move_vals = {
				'name': '/',
				'date': entry_date,
				'ref': asset.parent_id.doc_number + '| зардал тооцов',
				'journal_id': asset.parent_id.related_move_id.journal_id.id,
				'branch_id': asset.parent_id.branch_id.id if asset.parent_id.branch_id else False,
				'partner_id': asset.parent_id.owner_id.id if asset.parent_id.owner_id else False,
				'line_ids': line_ids
			}
			if asset.parent_id.is_project_partner:
				move_vals.update({'partner_id': asset.parent_id.branch_id.partner_id.id})
			move_id = move_obj.create(move_vals)   
			asset.write({'move_id':move_id.id})         
			move_id.action_post()       
				 
	def unlink(self):
		for depreciation in self:
			if depreciation.move_id:
				raise UserError(u'Санхүү бичилт үүссэн элэгдүүлэлтийн мөр устгахгүй!!!')
		super(ConsumableMaterialInUseDeprecaitionLine, self).unlink()
	
class DepreciationPeriod(models.Model):
	_name = 'depreciation.period'
	_description = "depreciation period"
	
	name = fields.Char('Name')
	fiscal_year = fields.Char('Fiscal Year')
	date_start =fields.Date('Duration Time')
	date_stop =fields.Date('Duration Time')
	
	

class ConsumableMaterialType(models.Model):
	_name = 'consumable.material.type'
	_description = "consumable material type"
	_order = 'name DESC'
		
	name = fields.Char('Name')
		
		
class ConsumableMaterialCategory(models.Model):
	_name = 'consumable.material.category'
	_description = "consumable material category"
	_inherit = ['analytic.mixin']
	_order = 'name DESC'
		
	name = fields.Char('Name')
	account_id = fields.Many2one('account.account','АБХМ данс',required=True)
	ex_account_id = fields.Many2one('account.account','Зардлын данс',required=True)
	analytic_account_id = fields.Many2one('account.analytic.account', string='Шинжилгээний данс')
	journal_id = fields.Many2one('account.journal','Журнал', required=True)    
	company_id = fields.Many2one(comodel_name="res.company",string="Компани",default=lambda self: self.env.company,)
	method_num = fields.Integer('Ашиглагдах хугацаа /сараар/', required=True)

class ConsumableMaterialLocation(models.Model):
	_name = 'consumable.material.location'
	_description = "consumable material location"
	_order = 'name'
		
	name = fields.Char('Name')

class ConsumeOrderHistory(models.Model):
	_name = 'consume.order.history'
	_inherit = ['analytic.mixin']
	_description = "Consume order history"
	
	name = fields.Char('Name')
	qty = fields.Float('QTY')
	date =fields.Date('Date')
	
	use_id = fields.Many2one('consumable.material.in.use','Use')    
	branch_id = fields.Many2one('res.branch','Old branch')    
	dep_id = fields.Many2one('hr.department','Old department')    
	owner_ids = fields.Many2many('res.partner','consum_use_history_owner_rel','use_id','owner_id','Owner', domain="[('employee','=',True)]")
	new_owner_id = fields.Many2one('res.partner', string='New owner')
	account_id = fields.Many2one('account.account', 'Хуучин Зардлын данс')
	analytic_account_id = fields.Many2one('account.analytic.account', 'Хуучин Шинжилгээний данс')


	type = fields.Selection([('close','Close'),
							  ('move','Move'),
							  ],String='Type',default='close')

class DonedConsumableContinue(models.TransientModel):
	_name = 'doned.consumable.continue'
	_description = 'Doned consumable continue'

	date = fields.Date(string='Огноо', required=True, default=date.today())
	account_id = fields.Many2one('account.account', string='Орлогын данс', required=True)
	tax_id = fields.Many2one('account.tax', string='Татвар', required=True)
	journal_id = fields.Many2one('account.journal', string='Журнал', required=True)
	consumable_ids = fields.Many2many('consumable.material.in.use', string='Consumable materials', default=lambda self: self.env.context.get('active_ids', []))
	info_message = fields.Text(string='Мэдээлэл')

	def doned_consumable_create_move(self):
		for item in self.consumable_ids.filtered(lambda r: r.state in ['progresss'] and r.rest_amount == 0):
			move_obj = self.env['account.move']
			asset_amount = item.rest_amount
			line_ids = [(0,0,{
				'name': item.doc_number and item.doc_number or (item.product_id and item.product_id.name)+':'+str(item.id),
				'ref': item.doc_number,
				'account_id': self.account_id.id,
				'debit': 1,
				'credit': 0.0,
				'journal_id': self.journal_id.id,
				'date': self.date,
				'tax_ids': [(4,self.tax_id.id)],
			}),(0,0,{
				'name': item.doc_number and item.doc_number or (item.product_id and item.product_id.name)+':'+str(item.id),
				'ref': item.doc_number,
				'account_id': self.account_id.id,
				'debit': 0.0,
				'credit': 1,
				'journal_id': self.journal_id.id,
				'date': self.date,
				'tax_ids': [(4,self.tax_id.id)],
			})]
			move_vals = {
				'name': item.doc_number and item.doc_number or (item.product_id and item.product_id.name)+':'+str(item.id),
				'date': self.date,
				'ref': item.doc_number,
				'journal_id': self.journal_id.id,
				'line_ids': line_ids
			}
			if item.is_project_partner:
				move_vals.update({'partner_id': item.branch_id.partner_id.id})
			move_id = move_obj.create(move_vals)
			move_id.action_post()
		if self.consumable_ids.filtered(lambda r: r.state not in ['progresss'] or r.rest_amount != 0):
			self.info_message = '\t|\t'.join(self.consumable_ids.filtered(lambda r: r.state not in ['progresss'] or r.rest_amount != 0).mapped('product_id.name')) + ' \nэдгээр АБХМ дахин ашиглах болоогүй байна!'
		action = self.env.ref('mw_consume_order.action_doned_consumable_continue').read()[0]
		action['target'] = 'new'
		action['res_id'] = self.id
		return action
