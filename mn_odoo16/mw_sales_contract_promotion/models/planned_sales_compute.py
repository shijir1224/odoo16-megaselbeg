# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

import logging
_logger = logging.getLogger(__name__)

class PlannedSalesCompute(models.Model):
	_name = 'planned.sales.compute'
	_description = 'Planned sales compute'
	_inherit = 'mail.thread'
	_order = 'date_start desc, partner_id'

	@api.model
	def _get_user(self):
		return self.env.user.id

	@api.depends('date_start','partner_id')
	def set_name(self):
		for obj in self:
			if obj.partner_id and obj.date_start:
				obj.name = obj.date_start.strftime("%Y-%m-%d")[:7]+' : '+obj.partner_id.name
			else:
				obj.name = "Temp"

	# Columns
	name = fields.Char('Name', compute='set_name', copy=False,
		readonly=True, )
	date = fields.Datetime('Created date', readonly=True, default=fields.Datetime.now(), copy=False)
	date_start = fields.Date('Start date', copy=True, required=True,
		states={'confirmed': [('readonly', True)],'cancelled': [('readonly', True)],'done': [('readonly', True)]}, tracking=True)
	date_end = fields.Date('End date', copy=True, required=True,
		states={'confirmed': [('readonly', True)],'cancelled': [('readonly', True)],'done': [('readonly', True)]}, tracking=True)

	partner_id = fields.Many2one('res.partner', 'Partner', required=True,
		states={'confirmed': [('readonly', True)],'cancelled': [('readonly', True)],'done': [('readonly', True)]}, copy=True)
	contract_id = fields.Many2one('mw.sales.contract', 'Contract', readonly=True, copy=False)
	contract_type = fields.Selection(related='contract_id.contract_type', string='Contract type', readonly=True, store=True)

	discount_percent = fields.Float(string='Discount %', 
		readonly=True, tracking=True)
	description = fields.Char(u'Description', copy=True, required=True, 
		states={'confirmed': [('readonly', True)],'cancelled': [('readonly', True)],'done': [('readonly', True)]})
	is_include_percent = fields.Boolean(u'Хувь хасаж шилжүүлсэн эсэх', copy=False, 
		states={'confirmed': [('readonly', True)],'cancelled': [('readonly', True)],'done': [('readonly', True)]})
	
	user_id = fields.Many2one('res.users', string='User', default=_get_user, readonly=True)
	sale_manager_id = fields.Many2one('res.users', string='Sales man', readonly=True)
	accountant_id = fields.Many2one('res.users', string='Accountant', readonly=True)

	line_ids = fields.One2many('planned.sales.compute.line', 'parent_id', 'SO lines', copy=False,
		readonly=True, tracking=True)

	# Нийт төлөлт, борлуулалт
	@api.depends('line_ids')
	def _compute_total_amount(self):
		for obj in self:
			obj.total_amount = sum(obj.line_ids.mapped('amount'))
	total_amount = fields.Float(string='Total amount', compute='_compute_total_amount', 
		store=True, readonly=True, tracking=True)
	total_payment = fields.Float(string='Total payment', readonly=True, tracking=True)

	@api.depends('line_ids','line_ids.discount_amount')
	def _compute_total_discount_amount(self):
		for obj in self:
			obj.total_discount_amount = sum(obj.line_ids.mapped('discount_amount'))
	total_discount_amount = fields.Float(string='Total discount', compute='_compute_total_discount_amount', 
		store=True, readonly=True, )

	state = fields.Selection([
			('draft', 'Draft'), 
			('confirmed', 'Confirmed'),
			('done', 'Done'),
			('cancelled', 'Cancelled'),
		], default='draft', required=True, string='State', tracking=True)

	move_id = fields.Many2one('account.move', string='Account move',
		readonly=True)
	account_id = fields.Many2one('account.account', string='Account',
		)
	journal_id = fields.Many2one('account.journal', string='Journal',)
	account_debit_id = fields.Many2one('account.account', string='Debit Account',
		)

	# --------- OVERRIDED ----------
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('In order to delete a record, it must be draft first!'))
		return super(PlannedSalesCompute, self).unlink()

	# ---------- CUSTOM ------------
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_cancel(self):
		self.state = 'cancelled'

	# Гэрээн дээрээс нөхцлүүд авч тооцоолох
	def compute_contract_total_sales(self):
		_logger.info(u'-***********-contract -- total sales-COMPUTE--*************--------\n')
		# Хамрагдах гэрээ олох
		contract = self.env['mw.sales.contract'].search([
			('partner_id','=',self.partner_id.id),
			('state','=','confirmed'),
			('contract_type','in',['total_sales','total_payments']),
			('date_start','<=',self.date_end),
			('date_end','>=',self.date_end)], limit=1)

		if len(contract)>1:
			raise UserError(_('Олон гэрээ тохируулсан байна!\n %s'% ','.join(contract.mapped('name'))))

		payment_obj = self.env['sale.payment.info']

		if contract:
			# General ---
			self.contract_id = contract.id
			sos = self.env['sale.order'].search([
				('partner_id','=',self.partner_id.id),
				('state','in',['sale','done']),
				('picking_date','>=',self.date_start),
				('picking_date','<=',self.date_end)])
			# Line бэлдэх 
			self.line_ids.unlink()
			payment_obj = self.env['sale.payment.info']
			for so in sos:
				vals = {
					'parent_id': self.id,
					'so_id': so.id,
				}
				# Борлуулсан
				tot = sum([ l.price_unit * l.qty_delivered for l in so.order_line ])
				vals['amount'] = tot
				self.env['planned.sales.compute.line'].create(vals)
			# Толгой компаниар татах
			sos = self.env['sale.order'].search([
				('partner_id.parent_id','=',self.partner_id.id),
				('state','in',['sale','done']),
				('picking_date','>=',self.date_start),
				('picking_date','<=',self.date_end)])
			for so in sos:

				vals = {
					'parent_id': self.id,
					'so_id': so.id,
				}
				# Борлуулсан
				tot = sum([ l.price_unit * l.qty_delivered for l in so.order_line ])
				vals['amount'] = tot
				self.env['planned.sales.compute.line'].create(vals)

			# Нийт нийлүүлэлтээс
			if contract.contract_type == 'total_sales':
				# Хувь Шатлал бодох
				line = contract.pricelist_line.filtered(lambda l: l.condition_min <= self.total_amount and self.total_amount <= l.condition_max)
				if line:
					# % аар хөнгөлөх эсэх
					new_discount_percent = 0
					if line.discount_type == 'percent':
						new_discount_percent = line.discount_percent
					# Мөнгөн дүнгээр хөнгөлөх бол Дүнгийн хувийг олох
					else:
						new_discount_percent = (line.discount_amount*100)/self.total_amount
					
					for ll in self.line_ids:
						ll.discount_percent = new_discount_percent
					self.discount_percent = new_discount_percent
					self.description = line.name
					_logger.info(u'-***********-contract -- total sales- Computed discount -----%d---\n', line.discount_percent)
				else:
					_logger.info(u'-***********-contract -- total sales- no lines --------\n')
			# Нийт төлөлтөөс
			else:
				# Төлөлтийг олох, SET хийх
				payments = self.env['sale.payment.info']._compute_partner_sale_payment(self.partner_id.id,self.date_start,self.date_end)
				tot = 0
				for x in payments:
					tot += x['amount']
					ll = self.line_ids.filtered(lambda l: l.so_id.id == x['so_id'])
					if ll:
						ll.payment_amount += x['amount']
				self.total_payment = tot

				# New - Хувь хасаж шилжүүлсэнг тооцох
				for line in contract.pricelist_line:
					temp_min = line.condition_min
					temp_max = line.condition_max
					temp_total_payment = self.total_payment
					
					# % аар хөнгөлөх эсэх
					new_discount_percent = 0
					if line.discount_type == 'percent':
						new_discount_percent = line.discount_percent
					# Мөнгөн дүнгээр хөнгөлөх бол Дүнгийн хувийг олох
					else:
						new_discount_percent = (line.discount_amount*100)/self.total_amount
					
					if self.is_include_percent:
						if line.discount_type == 'percent':
							temp_min = (line.condition_min*(100-line.discount_percent))/100
							temp_max = (line.condition_max*(100-line.discount_percent))/100
							temp_total_payment = (self.total_payment*100)/(100-new_discount_percent)
						else:
							temp_min = line.condition_min - line.discount_amount
							temp_max = line.condition_max - line.discount_amount 
							temp_total_payment = self.total_payment

					_logger.info(u'-***********-contract -- total payments- condition -%d-%d-----%d-\n', temp_min, temp_max, self.total_payment)
					
					if temp_min <= self.total_payment and self.total_payment <= temp_max:
						for ll in self.line_ids:
							ll.discount_percent = new_discount_percent
							temp_per = (ll.amount*100)/self.total_amount
							temp_payment = (temp_per*temp_total_payment)/100
							ll.payment_amount = temp_payment
							ll._compute_discount_amount()

						self.discount_percent = new_discount_percent
						self.description = line.name
						_logger.info(u'-***********-contract -- total payments- Computed discount --%d----\n', line.discount_percent)
						break
		else:
			raise UserError(_('Not found Sales contract!'))

	def action_to_confirm(self):
		if not self.line_ids:
			raise UserError(_("Click 'Compute discount' button!"))
		self.state = 'confirmed'
		self.sale_manager_id = self.env.user.id
		self.message_post(body="Confirmed by %s" % self.sale_manager_id.name)

	def action_to_done(self):
		# Хөнгөлөлтийн дүнгийн оронд ЭРХИЙН БИЧИГ өгөх
		if self.contract_id.get_gift_cart_amount:
			bonus_amount = self.total_discount_amount
			vals = {
				'name': str(self.date_end)+': '+self.partner_id.display_name,
				'date_start': self.date_end,
				'date_end': self.date_end+timedelta(days=30),
				'partner_id': self.partner_id.id or False,
				'bonus_amount': bonus_amount,
				'description': self.contract_id.name +': Гэрээний хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
			}
			gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
			gift.sudo().action_to_confirm()
			_logger.info(u'--contract--- created GIFT CART id %d %d+++++++++++' % (gift.id, bonus_amount))
		# Хөнгөлөлтийг SET хийх
		else:
			for ll in self.line_ids:
				for oline in ll.so_id.order_line:
					if not oline.is_reward_product:
						if self.contract_type == 'total_sales':
							oline.discount_percent_contract_month = self.discount_percent
							sub_discount = ((oline.price_unit * oline.qty_delivered)*self.discount_percent)/100
							oline.discount_contract_month_amount = sub_discount
						else:
							if ll.amount > 0:
								temp_per = ((oline.price_unit * oline.qty_delivered)*100)/ll.amount
								sub_discount = (temp_per*ll.discount_amount)/100
								oline.discount_percent_contract_month = self.discount_percent
								oline.discount_contract_month_amount = sub_discount

			_logger.info(u'-***********-contract -- total sales- SET discount on SOL --------\n')
		
		self.state = 'done'
		self.accountant_id = self.env.user.id
		self.message_post(body="Done by %s" % self.accountant_id.name)

	def action_to_account(self):
#		if not self.account_id:
#			raise UserError(_(u'Данс сонгож өгнө үү.'))
		if not self.journal_id:
			raise UserError(_(u'Журнал сонгож өгнө үү.'))
		if not self.partner_id.property_account_receivable_id:
			raise UserError(_(u'харилцагчийн данс сонгож өгнө үү.'))

		move_pool = self.env['account.move']
		
		for cmp in self:
			order_line = []
			move = {
				'date': cmp.date_end,
				'ref': cmp.name,
				'journal_id': cmp.journal_id.id,
			}

			debit_line = (0, 0, {
			'name': cmp.name+u' хөнгөлөлт',
			'date': cmp.date_end,
			'account_id': cmp.account_debit_id.id,
#			'account_id': cmp.partner_id.property_account_receivable_id.id,
			'journal_id': cmp.journal_id.id,
			'partner_id': cmp.partner_id.id,
			'debit': cmp.total_discount_amount,
			'credit': 0,
			})
			order_line.append(debit_line)
			credit_line = (0, 0, {
			'name': cmp.name+u' хөнгөлөлт',
			'date': cmp.date_end,
#			'account_id': cmp.account_id.id,
			'account_id': cmp.partner_id.property_account_receivable_id.id,
			'journal_id': cmp.journal_id.id,
			'partner_id': cmp.partner_id.id,
			'credit': cmp.total_discount_amount,
			'debit': 0,
			})
			order_line.append(credit_line)
			move.update({'line_ids': order_line})
			move_id = move_pool.create(move)
			self.write({'move_id': move_id.id,})		

		_logger.info(u'-***********-account create --------\n')

class PlannedSalesComputeLine(models.Model):
	_name = 'planned.sales.compute.line'
	_description = 'Planned sales compute line'
	_order = 'so_id'

	# Columns
	parent_id = fields.Many2one('planned.sales.compute', 'Parent ID', ondelete='cascade')
	state = fields.Selection(related='parent_id.state', string="State", store=True)

	so_id = fields.Many2one('sale.order', string='Sale order', )
	# warehouse_id = fields.Many2one(related='so_id.warehouse_id', string='Warehouse', 
	#	readonly=True, store=True)

	amount = fields.Float(string='Sales amount', copy=False,  default=0)
	payment_amount = fields.Float(string='Payment amount', copy=False,  default=0)
	discount_percent = fields.Float(string='Discount %', copy=False, default=0)

	@api.depends('amount','discount_percent')
	def _compute_discount_amount(self):
		for obj in self:
			if obj.parent_id.contract_id.contract_type == 'total_sales':
				obj.discount_amount = (obj.discount_percent*obj.amount)/100
			else:
				obj.discount_amount = (obj.discount_percent*obj.payment_amount)/100
	discount_amount = fields.Float(string='Discount Amount', compute='_compute_discount_amount',
		readonly=True, store=True)
