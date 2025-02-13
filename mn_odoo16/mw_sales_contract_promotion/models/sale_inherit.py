# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections
import pandas

import logging
_logger = logging.getLogger(__name__)

class res_partner(models.Model):
	_inherit = 'res.partner'
	tin_type = fields.Selection([('company','Company'),('person','Person'),('none','none')], default='person', string='Tin type')

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	picking_date = fields.Date(u'Хүргэх огноо', copy=False,
		states={'sale':[('readonly',True)],'done':[('readonly',True)],'cancel':[('readonly',True)]})
	with_e_tax = fields.Boolean(string=u'НӨАТ авах эсэх',
		states={'done':[('readonly',True)],'cancel':[('readonly',True)]})

	is_compute_coupon = fields.Boolean(string=u'Set promotion', default=False , copy=False)
	is_compute_contract = fields.Boolean(string=u'Set contract', default=False, copy=False )

	promotion_ids = fields.Many2many('mw.sales.promotion', string=u'Хамрагдсан урамшуулал', 
		readonly=True, tracking=True, copy=False)
	contract_id = fields.Many2one('mw.sales.contract',string=u'Хамрагдсан гэрээ', 
		readonly=True, tracking=True, copy=False)
	
	payment_type = fields.Selection([
		('cash','Бэлэн'),
		('loan','Зээлээр'),
		('cash_bank','Сардаа тэглэх')], 
		string='Төлбөрийн Хэлбэр', default='cash')

	ebarimt_type = fields.Selection([
			('none','None'),
			('person','Person'),
			('company','Company')], 
		'Ebarimt type', states={'draft': [('readonly', False)]})	
	ebarimt_state = fields.Selection([
		('draft','Draft'),
		('sent','Sent'), 
		('return','Returned')],
		string='Ebarimt State', default='draft', copy=False, tracking=True)

	@api.depends('order_line.main_amount')
	def _main_amount_all(self):
		for obj in self:
			for ll in obj.order_line:
				ll._main_amount_all()

			obj.update({
				'main_amount_total': sum(obj.order_line.mapped('main_amount')),
				'total_discount': sum(obj.order_line.mapped('total_discount')),
			})

	main_amount_total = fields.Monetary(string='Main Total', store=True, readonly=True, compute='_main_amount_all',)
	total_discount = fields.Monetary(string='Хөнгөлөлт', store=True, readonly=True, compute='_main_amount_all',)

	custom_promotion_product_id = fields.Many2one('product.product', string=u'Урамшууллын бараа', 
		states={'done':[('readonly',True)],'cancel':[('readonly',True)],'sale':[('readonly',True)]})
	custom_promotion_id = fields.Many2one('mw.sales.promotion', string=u'Урамшуулал сонгох',
		domain=[('can_be_selected','=',True)], 
		states={'done':[('readonly',True)],'cancel':[('readonly',True)],'sale':[('readonly',True)]})
	
	# Хүргэх огноогоор үүсгэх
	def _prepare_invoice(self):
		invoice_vals = super(SaleOrder, self)._prepare_invoice()
		if self.picking_date:
			invoice_vals['invoice_date'] = self.picking_date
		return invoice_vals

	# Үнэ дахин бодуулах
	def button_dummy(self):
		for line in self.order_line:
			# line.product_id_change()
			line.main_price_unit = 0
		_logger.info('-------- SO Button dummy -----')

	# Урамшууллын бараа гараар нэмэх
	def add_promotion_product(self):
		if self.state not in ['sale','done','cancel'] and self.custom_promotion_product_id:
			promo_line = self.env['sale.order.line'].search([
				('order_id','=',self.id),
				('product_id','=',self.custom_promotion_product_id.id),
				('is_reward_product','=',True)
				])
			if not promo_line:
				vals = {
					'order_id': self.id,
					'product_id': self.custom_promotion_product_id.id,
					'product_uom_qty': 100,
					'price_unit': 0,
					'is_reward_product': True,
				}
				self.env['sale.order.line'].create(vals)
			else:
				promo_line.product_uom_qty += 1
				promo_line.price_unit = 0

	def re_compute_dummy(self):
		# Хөнгөлөлт өмнө нь бодсон бол тэглэх
		for line in self.order_line:
			line.price_unit = line.main_price_unit
			line.discount_percent_coupon = 0
			line.discount_coupon_amount = 0
			line.discount_contract_amount_sales = 0
			line.discount_contract_amount_payment = 0
			line.discount_contract_month_amount = 0
			line.is_not_set_amount = False
			# if line.is_reward_product:
			# 	line.unlink()

		self.contract_id = False
		self.promotion_ids = [(6, 0, [])]
		self.is_compute_coupon = False
		self.is_compute_contract = False
		
		self.button_dummy()
		self._main_amount_all()
		self._amount_all()

	def force_cancel_saleorder(self):
		self.state = 'cancel'

	# Gift cart, эрхийн бичгээр борлуулалт хийх
	is_gift_sale = fields.Boolean(string=u'Gift, Эрхийн бичгээр', default=False,
		help=u'Gift болон эрхийн бичгийн борлуулалт бол сонгоно', copy = False,
		states={'sale':[('readonly',True)],'done':[('readonly',True)],'cancel':[('readonly',True)]})

	def action_cancel(self):
		# Борлуулалт цуцлавал урамшуулалтай холбоотой 
		# мэдээллүүдийг буцаах тэглэх
		for line in self.order_line:
			if line.main_price_unit > 0:
				line.price_unit = line.main_price_unit
				line.discount_coupon_amount = 0
				line.discount_contract_amount_sales = 0
				line.discount_contract_amount_payment = 0
				line.discount_contract_month_amount = 0
			
			line.is_not_set_amount = False
			# Урамшуулалын бараа байвал устгах
			# if line.is_reward_product:
				# line.unlink()

			# Bayasaa nemev
			# line.product_id_change()

		self.contract_id = False
		self.promotion_ids = [(6, 0, [])]
		self.is_compute_coupon = False
		self.is_compute_contract = False
		self.note = 'Cancelled'
		res = super(SaleOrder, self).action_cancel()
		return res

	# Эрхийн бичгээр борлуулалт хийх үед 
	# бодолт тооцоолох
	def action_confirm(self):
		for so in self:
			# Эрхийн бичгээр авсан эсэх
			if so.is_gift_sale:
				_logger.info(u'-***********-----gift--*************--------\n')
				gifts = self.env['mw.sales.gift.cart'].search([
					('partner_id','=',so.partner_id.id),
					('state','=','confirmed'),
					('bonus_amount','>',0),
					('date_start','<=',so.validity_date),
					('date_end','>=',so.validity_date)], order='bonus_amount')
				if gifts:
					desc = ""
					total_bonus = sum(gifts.mapped('bonus_amount'))
					so_amount = so.amount_total
					# Үнийг 0 болгох
					for ll in so.order_line:
						old_price = ll.price_unit
						ll.discount_coupon_amount = old_price * ll.product_uom_qty
						ll.main_price_unit = old_price
						ll.price_unit = 0
						ll.is_reward_product = True
					# Нийт бонуснаас авсан нь бага бол
					if total_bonus > so_amount:
						so_vld = so_amount
						desc = u" (%d) хөнгөлөлт үлдсэн." % (total_bonus-so_amount)
						# Үлдсэн бонусыг GIFT рүү SET хийх
						# Эхэлж дуусах GIFT ээс эхэлж шахна 
						for gf in gifts:
							if so_vld > gf.bonus_amount:
								gf.message_post(body=u"Хөнгөлөлт авсан %s" % so.name)
								tt = gf.bonus_amount
								gf.bonus_amount = 0
								so_vld -= tt
								gf.state = 'done'
							else:
								gf.message_post(body=u"Хөнгөлөлт авсан %s" % so.name)
								vld = gf.bonus_amount - so_vld
								gf.bonus_amount = vld
								break
					else:
						# Бонуснаас илүү бол 
						# Илүү дүнгээр Захиалгыг SET хийнэ
						min_qty = min(so.order_line.mapped('product_uom_qty'))
						ll = so.order_line.filtered(lambda l: l.product_uom_qty == min_qty)[0]
						diff_amount = so_amount-total_bonus
						ll.price_unit = (diff_amount)/ll.product_uom_qty
						old_promo = ll.discount_coupon_amount
						ll.discount_coupon_amount = (old_promo - diff_amount) if old_promo - diff_amount > 0 else 0
						desc = u" - Бүх хөнгөлөлтөө авсан"
						for gf in gifts:
							gf.message_post(body=u"Хөнгөлөлт авсан %s" % so.name)
							tt = gf.bonus_amount
							gf.bonus_amount = 0
							gf.state = 'done'

					t = so.note +u"\n * Gift, Эрхийн бичиг: "+','.join(gifts.mapped('name'))
					t = t+"\n"+desc
					so.note = t
				else:
					raise UserError(_(u'Хүчинтэй Gift, эрхийн бичиг хөнгөлөлт олдсонгүй!'))
			else:
				# *********************** Гэрээний бодолт ============================
				if not so.is_compute_contract:
					# Гэрээ шалгахад - Захиалгын мөрийг бэлдэх
					o_lines = []
					for l in so.order_line:
						temp = {
							'line_id': l.id,
							'product_id': l.product_id.id,
							'price_unit': l.price_unit,
							'product_uom_qty': l.product_uom_qty,
							'is_not_set_amount': False,
							'is_reward_product': l.is_reward_product,
							'brand_id': l.product_id.brand_id.id,
							'categ_id': l.product_id.categ_id.id,
							'product_tmpl_id': l.product_id.product_tmpl_id.id,
							'discount_contract_amount_sales': 0,
							'discount_percent_contract': 0,
							'fixed_price_contract': 0,
						}
						o_lines.append(temp)
					# Гэрээний нөхцөл шалгах
					result = self.env['mw.sales.contract'].compute_contract_per_sales(so.partner_id.id, so.validity_date, o_lines)
					if result:
						if 'order_line' in result: 
							# Үнэ өөрчлөх
							for l in result['order_line']:
								if 'main_price_unit' in l and l['discount_contract_amount_sales'] > 0:
									ll = self.env['sale.order.line'].browse(l['line_id'])
									ll.main_price_unit = l['main_price_unit']
									ll.price_unit = l['price_unit']
									ll.discount_contract_amount_sales = l['discount_contract_amount_sales']
									ll.discount_percent_contract = l['discount_percent_contract']
									ll.name += l['name']
									ll.fixed_price_contract = l['fixed_price_contract']

						if 'is_compute_contract' in result and result['is_compute_contract']:
							so.note += result['note']+', '
							so.contract_id = result['contract_id']
							so.is_compute_contract = result['is_compute_contract']
				# -----------------------------------------------------------------------
				if not so.is_compute_coupon:
					# ***************** Урамшуулал бодох *******************************
					# Урамшуулал шалгахад - Захиалгын мөрийг бэлдэх
					o_lines = []
					for l in so.order_line:
						temp = {
							'line_id': l.id,
							'product_id': l.product_id.id,
							'price_unit': l.price_unit,
							'product_uom_qty': l.product_uom_qty,
							'is_not_set_amount': False,
						}
						o_lines.append(temp)
					result = self.env['mw.sales.promotion'].compute_coupon_promotion(False, so.validity_date, so.partner_id.id, o_lines, warehouse_id=so.warehouse_id.id, custom_promo_id=so.custom_promotion_id.id, payment_type=so.payment_type)
					if result:
						if 'order_line' in result: 
							so.note += '- '+','.join(result['promotion_names']) if result['promotion_names'] else '-'
							so.promotion_ids = [(6,0,result['promotion_ids'])]
							# Үнэ өөрчлөх
							for l in result['order_line']:
								if 'main_price_unit' in l and l['discount_coupon_amount'] > 0:
									ll = self.env['sale.order.line'].browse(l['line_id'])
									ll.main_price_unit = l['main_price_unit']
									ll.price_unit = l['price_unit']
									ll.discount_coupon_amount = l['discount_coupon_amount']
									ll.discount_percent_coupon = l['discount_percent_coupon']
						# FREE product үүсгэх
						if 'free_product' in result and result['free_product']:
							for l in result['free_product']:
								vals = {
									'order_id': so.id,
									'product_id': int(l['product_id']),
									'product_uom_qty': l['product_uom_qty'],
									'price_unit': 0,
									'is_reward_product': True,
								}
								self.env['sale.order.line'].create(vals)
						if result['promotion_ids']:
							so.is_compute_coupon = True
				# ===================================================================
			# # Нэгж үнэ 0 эсэхийг шалгах
			so._check_zero_price_unit()
		res = super(SaleOrder, self).action_confirm()
		# Хүргэх огноогоор SET хийх
		for so in self:
			if so.commitment_date:
				dt = datetime.now()
				time = dt.strftime("%Y-%m-%d %H:%M:%S")
				for sp in so.picking_ids:
					sp.scheduled_date = so.commitment_date.strftime("%Y-%m-%d")+time[10:]
		return res

	def _check_zero_price_unit(self):
		for line in self.order_line:
			if line.main_price_unit == 0 and line.price_unit == 0 and not line.is_reward_product:
				raise UserError(_(u'(%s) Нэгж үнэ тэг байна, шалгана уу!' % line.product_id.display_name)) 

	# Борлуулалт захиалга хийгдэх бүр дээр тооцоолох - on PER SALES
	def action_compute_contract_per_sales(self):
		if not self.is_compute_contract:
			# *********************** Гэрээний бодолт ============================
			# Гэрээ шалгахад - Захиалгын мөрийг бэлдэх
			o_lines = []
			for l in self.order_line:
				temp = {
					'line_id': l.id,
					'product_id': l.product_id.id,
					'price_unit': l.price_unit,
					'product_uom_qty': l.product_uom_qty,
					'is_not_set_amount': False,
					'is_reward_product': l.is_reward_product,
					'brand_id': l.product_id.brand_id.id,
					'categ_id': l.product_id.categ_id.id,
					'product_tmpl_id': l.product_id.product_tmpl_id.id,
					'discount_contract_amount_sales': 0,
					'discount_percent_contract': 0,
					'fixed_price_contract': 0,
				}
				o_lines.append(temp)
			# Гэрээний нөхцөл шалгах
			result = self.env['mw.sales.contract'].compute_contract_per_sales(self.partner_id.id, self.validity_date, o_lines)
			if result:
				if 'order_line' in result: 
					# Үнэ өөрчлөх
					for l in result['order_line']:
						if 'main_price_unit' in l and l['discount_contract_amount_sales'] > 0:
							ll = self.env['sale.order.line'].browse(l['line_id'])
							ll.main_price_unit = l['main_price_unit']
							ll.price_unit = l['price_unit']
							ll.discount_contract_amount_sales = l['discount_contract_amount_sales']
							ll.discount_percent_contract = l['discount_percent_contract'] if 'discount_percent_contract' in l else 0
							ll.name += l['name']
							ll.fixed_price_contract = l['fixed_price_contract']

				if 'is_compute_contract' in result and result['is_compute_contract']:
					self.note += result['note']+', '
					self.contract_id = result['contract_id']
					self.is_compute_contract = result['is_compute_contract']
			# -----------------------------------------------------------------------
		else:
			_logger.info(u'-***********-contract -- per sales-COMPUTE--IGNORE*************--------\n')
	
	# Урамшуулал шалгах
	def action_compute_coupon_promotion(self):
		# Урамшуулал шалгах
		o_lines = []
		for l in self.order_line:
			temp = {
				'line_id': l.id,
				'product_id': l.product_id.id,
				'price_unit': l.price_unit,
				'product_uom_qty': l.product_uom_qty,
				'is_not_set_amount': False,
			}
			o_lines.append(temp)

		result = self.env['mw.sales.promotion'].compute_coupon_promotion(False, self.validity_date, self.partner_id.id, o_lines, warehouse_id=self.warehouse_id.id, custom_promo_id=self.custom_promotion_id.id, payment_type=self.payment_type)
		if result:
			if 'order_line' in result:
				self.note += '- '+','.join(result['promotion_names']) if result['promotion_names'] else '-'
				self.promotion_ids = [(6,0,result['promotion_ids'])]
				# Үнэ өөрчлөх
				for l in result['order_line']:
					if 'main_price_unit' in l and l['discount_coupon_amount'] > 0:
						ll = self.env['sale.order.line'].browse(l['line_id'])
						ll.main_price_unit = l['main_price_unit']
						ll.price_unit = l['price_unit']
						ll.discount_coupon_amount = l['discount_coupon_amount']
						ll.discount_percent_coupon = l['discount_percent_coupon']
					else:
						_logger.info(u'\n-***********-----Vne, xungulult deer asuudal garsan--*************-----%s---', str(l))
			# FREE product үүсгэх
			if 'free_product' in result and result['free_product']:
				for l in result['free_product']:
					vals = {
						'order_id': self.id,
						'product_id': int(l['product_id']),
						'product_uom_qty': l['product_uom_qty'],
						'price_unit': 0,
						'is_reward_product': True,
					}
					_logger.info(u'-***********-----FREE PRODUCT create--*************--------%s %d \n', str(l),int(l['product_id']))
					self.env['sale.order.line'].create(vals)
			if result['promotion_ids']:
				self.is_compute_coupon = True
				
	@api.depends('state',
				 'invoice_ids',
				 'invoice_ids.state',
				 'invoice_ids.amount_total',
				 'invoice_ids.amount_residual')
	def _compute_invoice_paid_amount(self):
		for order in self:
			invoices = order.invoice_ids.filtered(lambda l: l.state in ('open', 'paid'))
			invoice_amount_total = sum(invoices.mapped('amount_total'))
			invoice_residual_total = sum(invoices.mapped('amount_residual'))

			order.amt_invoice_paid = invoice_amount_total - invoice_residual_total

	amt_invoice_paid = fields.Monetary(string='Amount Paid', compute='_compute_invoice_paid_amount', compute_sudo=True, store=True)

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	# Columns
	is_reward_product = fields.Boolean(string=u'Reward product', default=False, copy=False )
	is_not_set_amount = fields.Boolean(string=u'Үнийн дүнд нөлөөлөх эсэх', default=False, copy=False)
	main_price_unit = fields.Float(string=u'Main price unit', readonly=True, default=0, digits=(16,2) , copy=False)
	fixed_price_contract = fields.Float(string=u'Fixed price', readonly=True, default=0, digits=(16,2) )
	# Хөнгөлөлт урамшуулалын багана - Хувь
	discount_percent_coupon = fields.Float(string=u'Discount promotion %', readonly=True, default=0, digits=(16,2),copy=False )
	discount_percent_contract = fields.Float(string=u'Discount %', readonly=True, default=0, digits=(16,2),copy=False )
	discount_percent_contract_month = fields.Float(string=u'Discount month %', readonly=True, default=0, digits=(16,2),copy=False )
	# Хөнгөлөлт урамшуулалын багана - Дүн
	discount_coupon_amount = fields.Float(string=u'Урамшуулалын дүн', readonly=True, default=0, digits=(16,2),copy=False )
	discount_contract_amount_sales = fields.Float(string=u'Гэрээний хөнгөлөлт/борлуулалт бүр/', readonly=True, default=0, digits=(16,2),copy=False )
	discount_contract_amount_payment = fields.Float(string=u'Гэрээний хөнгөлөлт/төлөлт бүр/', readonly=True, default=0, digits=(16,2),copy=False )
	discount_contract_month_amount = fields.Float(string=u'Төлөвлөгөөт хөнгөлөлтийн дүн', readonly=True, default=0, digits=(16,2),copy=False )

	@api.depends('qty_delivered','product_uom_qty','main_price_unit','price_unit')
	def _main_amount_all(self):
		for obj in self:
			price = obj.main_price_unit if obj.main_price_unit else obj.price_unit
			obj.update({
				'main_amount': price * obj.product_uom_qty,
			})
			obj._compute_amount()

	@api.depends('discount_coupon_amount','discount_contract_amount_sales','discount_contract_amount_payment','discount_contract_month_amount')
	def _compute_discount(self):
		for obj in self:
			obj.update({
				'total_discount': obj.discount_contract_amount_sales+obj.discount_contract_amount_payment+obj.discount_contract_month_amount+obj.discount_coupon_amount,
			})

	main_amount = fields.Monetary(string=u'Үндсэн үнэ', store=True, readonly=True, compute='_main_amount_all',copy=False)
	total_discount = fields.Monetary(string=u'Нийт хөнгөлөлт', store=True, readonly=True, compute='_compute_discount',copy=False)

	# Урамшууллын мөр дээр тоо засахад үнэнийг хэвээр нь байлгах
	@api.onchange('product_uom', 'product_uom_qty')
	def product_uom_change(self):
		if not self.product_uom or not self.product_id:
			self.price_unit = 0.0
			return
		if self.order_id.pricelist_id and self.order_id.partner_id:
			product = self.product_id.with_context(
				lang=self.order_id.partner_id.lang,
				partner=self.order_id.partner_id,
				quantity=self.product_uom_qty,
				date=self.order_id.date_order,
				pricelist=self.order_id.pricelist_id.id,
				uom=self.product_uom.id,
				fiscal_position=self.env.context.get('fiscal_position')
			)
			if self.is_reward_product:
				return
			self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(), product.taxes_id, self.tax_id, self.company_id)

class SelectedSaleReCompute(models.TransientModel):
	_name = "selected.sale.re.compute"
	_description = "selected sale re compute"

	def get_active_orders(self):
		order_ids = self.env['sale.order'].search([('id','in',self._context['active_ids'])])
		return order_ids

	active_order_ids = fields.Many2many('sale.order', string='Борлуулалтын захиалгууд', default=get_active_orders, readonly=True)

	def action_re_compute(self):
		obj_ids = self.env['sale.order'].search([('id','in',self._context['active_ids'])])
		for item in obj_ids:
			item.re_compute_dummy()
