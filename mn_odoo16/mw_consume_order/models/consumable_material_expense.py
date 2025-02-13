# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
# import math
import logging
_logger = logging.getLogger(__name__)


class ConsumableMaterialExpense(models.Model):
	_name = 'consumable.material.expense'
	_description = "consumable material expense"
	_inherit = ['analytic.mixin','mail.thread']
	_order = 'date DESC'
	
	doc_number = fields.Char(
		'Document number', copy=False, readonly=True,default=lambda x: _('New'), tracking=True)
	date = fields.Date('Transaction Date',default=fields.Datetime.now, required=True, tracking=True) 
	state = fields.Selection([('draft','Draft'),
							  ('progress','Progress'),
							  ('confirm','Confirmed'),
							  ('reject','Reject'),
							  ('done','Done')], string='Status',default='draft', tracking=True)
	product_id = fields.Many2one('product.product', related='expense_product_list_ids.product_id', string='Product', readonly=False)
	note = fields.Char(related='expense_product_list_ids.note', string='Note', readonly=False, tracking=True)
	owner_id = fields.Many2one('res.partner', related='expense_product_list_ids.owner_id', string='Owner', readonly=False)
	is_project_partner = fields.Boolean(string="Төслийн харилцагч", default=False)
	expense_product_list_ids = fields.One2many('consumable.material.expense.line', 'consumable_material_id','Product list')
	consume_count = fields.Integer(compute='_compute_workorder_count')
	warehouse_id = fields.Many2one('stock.warehouse', 'Deliver To')
	other_expense_id = fields.Many2one('stock.product.other.expense', tracking=True)
	branch_id = fields.Many2one('res.branch','Branch', default=lambda self: self.env.user.branch_id)
	department_id = fields.Many2one('hr.department', tracking=True)
	company_id = fields.Many2one(comodel_name="res.company",string="Company",default=lambda self: self.env.company, tracking=True)
	categ_id = fields.Many2one('consumable.material.category', string=u'Category')
	account_id = fields.Many2one('account.account', string='Зардлын данс', tracking=True)
	analytic_account_id = fields.Many2one('account.analytic.account', string='Шинжилгээний данс', tracking=True)
	disposal_date = fields.Date(string='Disposal date', readonly=True, tracking=True)

	def _compute_workorder_count(self):
		qty = 0
		for line in self:
			res = self.env['consumable.material.in.use'].search([('expense_line_id', 'in', line.expense_product_list_ids.ids)])
			for i in res:
				qty += 1
		self.consume_count = qty or 0
		
	@api.model
	def create(self, vals):
		if not vals.get('doc_number'):
			vals['doc_number'] = self.env['ir.sequence'].next_by_code('consumable.material.expense') or _('New')
		return super(ConsumableMaterialExpense, self).create(vals)

	def unlink(self):
		for expense in self:
			if expense.state not in ['draft']:
				raise UserError(u'Батлагдсан АБХМ-н зарлага устгахгүй!!!')
		super(ConsumableMaterialExpense, self).unlink()
	
	def force_doc_number(self):
		expense_ids = self.env['consumable.material.expense'].search([('name','in',['Шинэ','New'])], order="create_date")
		for item in expense_ids:
			item.doc_number = self.env['ir.sequence'].next_by_code('consumable.material.expense')

	def action_set_to_close(self):
		""" Returns an action opening the asset pause wizard."""
		self.ensure_one()
		new_wizard = self.env['consumable.material.sell'].create({
			'consumable_id': self.id,
		})
		return {
			'name': _('Sell Consumable Material'),
			'view_mode': 'form',
			'res_model': 'consumable.material.sell',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': new_wizard.id,
		}

	def button_consume_order(self):
		res = []
		for line in self:
			res = self.env['consumable.material.in.use'].search([('expense_line_id', 'in', line.expense_product_list_ids.ids)])
			return{
				'type': 'ir.actions.act_window',
				'name': _('Consumable Material'),
				'res_model': 'consumable.material.in.use',
				'view_type': 'form',
				'view_mode': 'tree,form',
				'view_id': False,
				'domain':[('id', 'in', res.ids)],
				}


	@api.onchange('analytic_distribution')
	def onchange_analytic_distribution(self):
		for line in self.expense_product_list_ids:
			if self.analytic_distribution:
				line.analytic_distribution = self.analytic_distribution
			else:
				line.analytic_distribution=False

	@api.onchange('account_id')
	def onchange_account_id(self):
		for line in self.expense_product_list_ids:
			if self.account_id:
				line.account_id = self.account_id
			else:
				line.account_id=False

	def button_confirm(self):
		check = False
		end_date = '2015-08-14'
#         for line in self.expense_product_list_ids:#барааны үлдэгдэл нь боломжит тоо хэмжээнээс бага байгаа эсэхийг шалгах 
#             if line.quantity_available < line.quantity:
#                check = True 
		if self.other_expense_id:
			picking_ids = self.env['stock.picking'].search([('id','in',self.other_expense_id.expense_picking_ids.ids)])
			account_moves = self.env['account.move'].search([('stock_move_id', 'in', picking_ids.mapped('move_ids.id'))]) if picking_ids else False
			if not account_moves or not picking_ids:
				raise UserError(u'Агуулахын баримт эсвэл санхүү бичилтээ шалгана уу!!!')
			if len(account_moves) != len(account_moves.filtered(lambda r: r.state == 'posted')):
				raise UserError(u'Агуулахын баримт дээр батлагдаагүй санхүү бичилт байна!!!')

		if check == False:#бага байгаа тохиолдолд ашиглалтанд байгаа хангамжийн материал, барааны хөдөлгөөн үүснэ.
			
			self.state = 'confirm'
			consume_obj = self.env['consumable.material.in.use']
			for line in self.expense_product_list_ids:
				if line.is_depreciate == True:
					end_date = line.end_date
				else:
					end_date = False
				if not line.related_product_move_id or (line.related_product_move_id and not line.related_product_move_id.account_move_ids):
					raise UserError(u'{0} Зардлын барааны мөр дээрх холбоотой санхүү бичилт хоосон байна!!!'.format(line.product_id.name))
				account_move_id = line.related_product_move_id.account_move_ids[-1]
				for row in range(int(line.quantity)):
					consume = consume_obj.create({
						'doc_number':self.doc_number,
						'product_id':line.product_id.id or False,
						'owner_id':line.owner_id.id or False,
						'transaction_date':self.date,
						'is_project_partner': self.is_project_partner,
						'date':line.start_date,
						'end_date':end_date,
						'is_depreciate':line.is_depreciate,
						'state':'draft',
						'expense_line_id':line.id,
						'note':line.note,
						'price':line.price,
						'category_id':line.category_id.id or False,
						'life':line.category_id.method_num,
						'type_id':line.type_id.id or False,
						'lot_id':line.lot_id and line.lot_id.id or False,
						'branch_id':line.branch_id and line.branch_id.id or False,
						'department_id':line.department_id and line.department_id.id or False ,
						'depr_amount':0,
						'amount':line.price,
						'account_id': line.account_id.id if line.account_id else line.category_id.ex_account_id.id if line.category_id and line.category_id.ex_account_id else False,
						# 'analytic_account_id': line.consumable_material_id.analytic_account_id.id,
						'analytic_distribution': line.analytic_distribution,
						'related_product_move_id': line.related_product_move_id.picking_id.id,
						'related_move_id': account_move_id.id,
						})
					line.life = consume.life
					# line.analytic_account_id = consume.analytic_account_id.id
					consume.button_progress()
					# consume.compute_depreciation_board()
		else:
			raise UserError(_(u'Not enough product quantity!'))

		
	def button_reject(self):
		check_value = False
		for line in self:
			res = self.env['consumable.material.in.use'].search([('doc_number', '=', line.doc_number)])
			for i in res:
				if i.state != 'draft':
					check_value = True
		if check_value == False:
			for i in res:
				i.unlink()
			self.state = 'reject'
		else:
			raise UserError(_(u'Please, draft related consume order!'))
	
	def button_draft(self):
		self.state = 'draft'

	def set_lines_categ(self):
		for item in self:
			item.expense_product_list_ids.filtered(lambda r: not r.category_id).category_id = item.categ_id.id
			item.expense_product_list_ids.filtered(lambda r: not r.account_id).account_id = item.account_id.id
			# item.expense_product_list_ids.filtered(lambda r: not r.analytic_account_id).analytic_account_id = item.analytic_account_id.id

	@api.onchange('categ_id','account_id')
	def _onchange_categ(self):
		for item in self:
			if item.categ_id:
				if not item.account_id:
					item.account_id = item.categ_id.ex_account_id.id
				item.set_lines_categ()

	# @api.onchange('category_id')
	# def _onchange_life(self):
	# 	for using in self.filtered(lambda using: using.state in ['draft','progress']):
	# 		if using.category_id and using.category_id.method_num <= 0:
	# 			raise UserError(_("Ангилалын элэгдүүлэх хугацаагаа шалгана уу! {0}".format(using.category_id.name)))
	# 		if using.life == 0:
	# 			using.life = using.category_id.method_num
	# 		if not using.account_id:
	# 			using.account_id = using.category_id.ex_account_id.id

class ConsumableMaterialExpenseLine(models.Model):  
	_name = 'consumable.material.expense.line'
	_inherit = ['analytic.mixin']

	_description = "consumable material expense line"
	
	@api.onchange('product_id')
	def onchange_check_start(self):
		i = 0
		stock_quant = []
		quantity_available=0
		for product in self:
			i
			stock_quant = self.env['stock.quant'].search([('product_id.name','=',self.product_id.name)])
			if stock_quant:
				for line in stock_quant:
					quantity_available += line.quantity
			i += 1
			
		if self.product_id:
			quant_obj = self.env['stock.quant']
			domain = [('product_id','=',self.product_id.id),('location_id.usage','=','internal')]
			if self.consumable_material_id.warehouse_id:
				domain.append(('location_id.set_warehouse_id','=',self.consumable_material_id.warehouse_id.id))
			quant_ids = quant_obj.sudo().search(domain)
			qty = 0
			for item in quant_ids:
				qty += item.quantity
			self.quantity_available = qty

	product_id = fields.Many2one('product.product', 'Product')
	quantity_available = fields.Float('Quantity Available')
	quantity = fields.Float('Quantity')
	owner_id = fields.Many2one('res.partner','Owner')
	is_depreciate = fields.Boolean('Is Depreciate', related='product_id.is_depreciate', readonly=True)
	consumable_material_id = fields.Many2one('consumable.material.expense','consumable material', ondelete='cascade')
	start_date = fields.Date('Start Date', default=fields.Datetime.now)
	end_date = fields.Date('End Date')  
	owner_ids = fields.Many2many('res.partner','consum_exp_owner_rel','exp_id','owner_id','Owner')
	note = fields.Char('Note')
	related_product_move_id = fields.Many2one('stock.move', string='Барааны хөдөлгөөн')
	price = fields.Float('Price')
	category_id = fields.Many2one('consumable.material.category')
	type_id = fields.Many2one('consumable.material.type')
	lot_id = fields.Many2one('consumable.material.lot')
	branch_id = fields.Many2one('res.branch','Branch')
	department_id = fields.Many2one('hr.department',)
	account_id = fields.Many2one('account.account', string='Зардлын данс')
	analytic_account_id = fields.Many2one('account.analytic.account', string="Шинжилгээний данс")
	life = fields.Integer(string="Ашиглагдах хугацаа /сараар/", default=0)

	@api.onchange('consumable_material_id','consumable_material_id.account_id')
	def _onchange_expense_account(self):
		for item in self:
			if item.consumable_material_id and not item.account_id:
				item.acccount_id = item.consumable_material_id.account_id.id

class StockProductOtherExpense(models.Model):
	_inherit = 'stock.product.other.expense'
	_description = 'Stock Product Other Expense'

	consumable_expense_ids = fields.One2many('consumable.material.expense', 'other_expense_id', string='Consume Material Expense')
	count_consumable = fields.Integer(string='Total number Consume Material Expense', compute='_compute_consumable_count')
	is_consume_product = fields.Boolean(related='transaction_value_id.is_consume_product', string=u'АБХМ үүсэх?', store=True)

	@api.depends('consumable_expense_ids')
	def _compute_consumable_count(self):
		for item in self:
			item.count_consumable =  len(self.consumable_expense_ids)

	# def action_to_confirm(self):
	# 	res = super(StockProductOtherExpense, self).action_to_confirm()
	# 	if self.transaction_value_id and self.transaction_value_id.is_consume_product:
	# 		self.action_to_consumable()
	# 	return res

	def action_to_consumable(self):
		consumable_ex=self.env['consumable.material.expense']
		consumable_ex_line=self.env['consumable.material.expense.line']
		emp_obj = self.env['hr.employee']
		if self.transaction_value_id.is_consume_product:
			con_id = consumable_ex.create({'date':self.date_required,'warehouse_id':self.warehouse_id.id,'branch_id':self.branch_id.id})
		products = []
		for line in self.product_expense_line:
			if line.product_id.is_consum or self.transaction_value_id.is_consume_product:
				for picking in self.expense_picking_ids.filtered(lambda r: r.picking_type_id.code == 'outgoing' and r.state == 'done'):
					sm = picking.move_ids.search([('product_id','=',line.product_id.id),('picking_id','in',self.expense_picking_ids.filtered(lambda r: r.picking_type_id.code == 'outgoing' and r.state == 'done').ids)],limit=1)
					price_unit = sm.price_unit or sm.product_id.standard_price
					if not sm:
						raise UserError(_(u'Зарлага батлагдаагүй байна!'))
					if not line.res_partner_id and self.transaction_value_id.is_employee:
						raise UserError(_(u'Эзэмшигч сонгоогүй байна!'))
					lines=consumable_ex_line.search([('related_product_move_id','=',sm.id)],limit=1)
					_logger.info(u'------------consumable_ex_line- / lines: %s!'%(lines))
					if len(lines)>0 and line.product_id.id not in products:
						raise UserError(_(u'Already created!'))
					products.append(line.product_id.id)#1 барааг 2 с олон бичих
					vals = {
						'product_id':line.product_id.id,
						'quantity':line.qty,
						'owner_id': line.res_partner_id.id,
						'is_depreciate':False,
						'note':self.name,
						'related_product_move_id':sm.id,
						'price':abs(price_unit),
						'consumable_material_id':con_id.id,
						'department_id': self.department_id.id,
						'branch_id': self.branch_id.id
					}
					consumable_ex_line.create(vals)
					con_id.write({'other_expense_id':self.id})
		return True

	def view_consumable_expense(self):
		self.ensure_one()
		action = self.env.ref('mw_consume_order.action_consume_material_expense_view').read()[0]
		action['domain'] = [('id','in',self.consumable_expense_ids.ids)]
		return action

class MnTransactionValue(models.Model):
	_inherit = 'mn.transaction.value'
	
	is_consume_product = fields.Boolean(string=u'АБХМ үүсэх?', default=False)    

class ConsumableMaterialLot(models.Model):
	_name = 'consumable.material.lot'
	_description = 'CMLOT'

	name = fields.Char('Name')  
	date = fields.Date('Date',default=fields.Datetime.now)