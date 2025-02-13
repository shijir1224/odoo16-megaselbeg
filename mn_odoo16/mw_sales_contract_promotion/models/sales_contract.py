# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta, date

from tempfile import NamedTemporaryFile
import base64
import xlrd

import collections

import logging
_logger = logging.getLogger(__name__)


class MWSalesContract(models.Model):
	_name = 'mw.sales.contract'
	_description = 'Sales contract'
	_inherit = 'mail.thread'
	_order = 'date_start desc, partner_id'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	name = fields.Char('Number', required=True, copy=True,
		states={'confirmed': [('readonly', True)]})
	date = fields.Datetime('Created date', readonly=True, default=fields.Datetime.now(), copy=False)
	date_contract = fields.Date(u'Гэрээ хийсэн огноо', copy=True, 
		states={'confirmed': [('readonly', True)]}, tracking=True)
	date_start = fields.Date('Start date', copy=True, required=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)
	date_end = fields.Date('End date', copy=True, required=False,
		states={'confirmed': [('readonly', True)]}, tracking=True)
	active = fields.Boolean(default=True, help="Set active to false to hide the contract without removing it.")
	partner_id = fields.Many2one('res.partner', 'Partner', required=True,
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)
	description = fields.Char(u'Description', copy=True, required=True, 
		states={'confirmed': [('readonly', True)]})

	# Хөнгөлөлтийн дүнгийн оронд бараа авах
	get_gift_cart_amount = fields.Boolean(string=u'Хөнгөлөлтийн дүнгийн оронд эрхийн бичиг авах', default=False,
		help=u'Хөнгөлөлтийн хувь бодсон дүнгийн оронд бараа авах үед сонгоно. Өөрөөр хэлбэл бараа авах "Эрхийн бичих" үүсгэнэ.', 
		states={'confirmed': [('readonly', True)]}, tracking=True)
	
	user_id = fields.Many2one('res.users', string='User', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', string='Confirmed by', readonly=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Attackments', 
		states={'confirmed': [('readonly', True)]})

	contract_type = fields.Selection([
			('total_payments','Total payments'),
			('total_sales','Total sales'), 
			('per_payment','Per payment'),
			('per_sales','Per sales'),
			('loan_contract',u'Зээлийн гэрээ'),
		], required=True, string='Contract type', copy=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)
	discount_percent = fields.Float(string='Discount %', copy=True, required=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)
	pricelist_line = fields.One2many('mw.sales.pricelist.line', 'parent_id', 'Pricelist line', copy=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)

	state = fields.Selection([
			('draft', 'Draft'), 
			('confirmed', 'Confirmed'),
		], default='draft', required=True, string='State', tracking=True)

	excel_data = fields.Binary(string='Excel file')

	# --------- OVERRIDED ----------
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('In order to delete a record, it must be draft first!'))
		return super(MWSalesContract, self).unlink()

	# ---------- CUSTOM ------------
	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		# if self.contract_type not in ['total_sales','total_payments'] and self.discount_percent <= 0:
		# raise UserError(_('Please insert discount %!'))
		self.ensure_one()
		contracts = self.partner_id.sale_contract_ids.filtered(lambda l: l.id != self.id and l.check_active() is True)
		if contracts:
			raise UserError('Хэрэглэгчид идэвхтэй гэрээ байна. Хэрэвээ тухайн гэрээг ашиглахгүй бол архивлана уу.')
		self.state = 'confirmed'
		self.validator_id = self.env.user.id
		self.message_post(body="Confirmed by %s" % self.validator_id.name)

	# Excel ээс мөр үүсгэх
	def import_from_excel(self):
		if not self.excel_data:
			raise UserError(_(u'Choose import excel file!'))

		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		book = xlrd.open_workbook(fileobj.name)
		try:
			sheet = book.sheet_by_index(0)
		except:
			raise UserError('Wrong Sheet number.')

		nrows = sheet.nrows
		for i in range(0, nrows):
			row = sheet.row(i)
			default_code = False
			barcode = False
			product = False
			# Барааны кодоор
			if row[0].value:
				if row[0].ctype in [2, 3]:
					default_code = int(row[0].value)
				else:
					default_code = row[0].value
				product = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
			# Баркодоор
			if row[1].value:
				if row[3].ctype in [2, 3]:
					barcode = int(row[1].value)
				else:
					barcode = row[1].value
				product = self.env['product.product'].search([('barcode', '=', barcode)], limit=1)

			discount_type = row[2].value
			percent_amount = row[3].value
			_logger.info(u'-*************-Import plan-***************--%s %s %s %d------\n', default_code, barcode, discount_type, percent_amount)
			if product:
				vals = {
					'parent_id': self.id,
					'condition_type': 'no_limit',
					'pricelist_type': 'product',
					'discount_type': discount_type,
					'product_id': product.id,
					'condition_min': 0,
					'condition_max': 0,
				}
				if discount_type == 'percent':
					vals['discount_percent'] = percent_amount
				else:
					vals['fixed_price'] = percent_amount
				line = self.env['mw.sales.pricelist.line'].create(vals)
		return True

	# Гэрээний хугацаа шалгах - Крон метод
	@api.model
	def _check_expire_date(self):
		# Дуусч байгаа Гэрээ шалгах
		today = datetime.now()
		date_stop = today + timedelta(days=5)
		# print '=============', today, date_stop
		contracts = self.env['mw.sales.contract'].search([
			('state','=','confirmed'),
			('date_end','>=',today),
			('date_end','<=',date_stop)])
		msg = []
		for line in contracts:
			msg.append(line.name)

		if msg:
			# Get group
			res_model = self.env['ir.model.data'].search([
				('module','=','mw_sales_contract_promotion'),
				('name','=','group_sale_contract_manager')], limit=1)
			group = self.env['res.groups'].search([('id','=',res_model.res_id)])
			for receiver in group.users:
				if receiver.partner_id:
					if self.env.user.partner_id.id != receiver.partner_id.id:
						channel_ids = self.env['mail.channel'].search([
						   ('channel_partner_ids', 'in', receiver.partner_id.ids),
						   ('channel_partner_ids', 'in', self.env.user.partner_id.ids),
						   ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
						if not channel_ids:
							vals = {
								'channel_type': 'chat', 
								'name': u''+receiver.partner_id.name+u', '+self.env.user.name, 
								'public': 'private', 
								'channel_partner_ids': [(4, receiver.partner_id.id), (4, self.env.user.partner_id.id)], 
								#'email_send': False
							}
							new_channel = self.env['mail.channel'].create(vals)
							notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
							new_channel.message_post(body=notification, message_type="notification", subtype_xmlid='mail.mt_note')
							channel_info = new_channel.channel_info()[0]
							self.env['bus.bus']._sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info, {
								'id': self.id, 
								'model':'mw.sales.contract'})
							channel_ids = [new_channel.id]
						# MSG илгээх
						self.env['mail.message'].create({
								   'message_type': 'comment', 
								   'subtype_id': 1,
								   'body': u"<span style='font-size:12pt; font-weight:bold; color:red;'>Дуусах гэж буй борлуулалтын гэрээнүүд:<br/>" + ','.join(msg)+'</span>',
								   'channel_ids':  [(6, 0, channel_ids),]
								   })

	# ================ Захиалга хийгдэх бүр дээр тооцоолох - on PER SALES ==================
	def compute_contract_per_sales(self, partner_id, validity_date, order_line):
		_logger.info(u'-***********- SELF - contract -- per sales-COMPUTE--*************--------\n')
		# Хамрагдах гэрээ олох
		partner = self.env['res.partner'].search([('id','=',partner_id)], limit=1)
		contract = self.env['mw.sales.contract'].search([
			('partner_id','in',[partner.id, partner.parent_id.id]),
			('state','=','confirmed'),
			('contract_type','=','per_sales'),
			('date_start','<=',validity_date),
			('date_end','>=',validity_date)], limit=1)

		computed_contract = False
		if contract:
			_logger.info(u'-***********-contract -- per sales-COMPUTE-- FOUND contract %s --------\n', contract.name)
			# 1. Хэрэв шууд % хөнгөлөлт бол ===================
			if contract.discount_percent > 0 and not contract.pricelist_line:
				_logger.info(u'-***********-contract -- per sales-COMPUTE-- direct percent % --------\n')
				for o_line in order_line:
					if not o_line['is_reward_product']:
						old_price = o_line['price_unit']
						o_line['discount_percent_contract'] = contract.discount_percent
						o_line['main_price_unit'] = old_price
						new_price = ((100-contract.discount_percent)*old_price)/100
						o_line['price_unit'] = new_price
						# Хөнгөлөлтийн дүнг бодох
						sub_discount = (old_price-new_price)*o_line['product_uom_qty']
						o_line['discount_contract_amount_sales'] = sub_discount
						o_line['name'] = contract.name

				computed_contract = True
			# 2. Шатлалтай гэрээний заалт =================================
			elif contract.pricelist_line:
				_logger.info(u'-***********-contract -- per sales-COMPUTE-- with LEVEL lines --------\n')
				for line in contract.pricelist_line:
					_logger.info(u'-***********-contract -- LEVEL line name-%s----\n', line.name)
					condition_ok = False
					# Нөхцөл шалгах - Мөнгөн дүнгээр ===========
					if line.condition_type == 'amount':
						# Захиалгын дүн авах
						product_amount = 0
						if line.pricelist_type == 'all':
							product_amount = product_amount = sum([ l['product_uom_qty'] * l['price_unit'] for l in order_line ])
						elif line.pricelist_type == 'category':
							product_amount = sum([ l['product_uom_qty'] * l['price_unit'] for l in order_line if l['categ_id'] in line.category_ids.ids ])
						elif line.pricelist_type == 'product':
							product_amount = sum([ l['product_uom_qty'] * l['price_unit'] for l in order_line if l['product_id'] == line.product_id.id ])
						elif line.pricelist_type == 'product_template':
							product_amount = sum([ l['product_uom_qty'] * l['price_unit'] for l in order_line if l['product_tmpl_id'] == line.product_tmpl_id.id ])
						elif line.pricelist_type == 'brand':
							product_amount = sum([ l['product_uom_qty'] * l['price_unit'] for l in order_line if l['brand_id'] in line.brand_ids.ids ])
						# Нөхцөл шалгах
						if line.condition_min <= product_amount and product_amount <= line.condition_max:
							_logger.info(u'-***********-contract - BY AMOUNT condition OK ----%d < %d < %d---\n',line.condition_min,  product_amount, line.condition_max)
							condition_ok = True
					# Нөхцөл шалгах - Тоо ширхэгээр ===========
					elif line.condition_type == 'qty':
						# Захиалгын тоо авах
						product_qty = 0
						if line.pricelist_type == 'all':
							product_qty = product_amount = sum([ l['product_uom_qty'] for l in order_line ])
						elif line.pricelist_type == 'category':
							product_qty = sum([ l['product_uom_qty'] for l in order_line if l['categ_id'] in line.category_ids.ids ])
						elif line.pricelist_type == 'product':
							product_qty = sum([ l['product_uom_qty'] for l in order_line if l['product_id'] == line.product_id.id ])
						elif line.pricelist_type == 'product_template':
							product_qty = sum([ l['product_uom_qty'] for l in order_line if l['product_tmpl_id'] == line.product_tmpl_id.id ])
						elif line.pricelist_type == 'brand':
							product_qty = sum([ l['product_uom_qty'] for l in order_line if l['brand_id'] in line.brand_ids.ids ])
						# Нөхцөл шалгах 
						if line.condition_min <= product_qty and product_qty <= line.condition_max:
							_logger.info(u'-***********-contract - BY QTY ------%d < %d < %d---\n',line.condition_min,  product_qty, line.condition_max)
							condition_ok = True
					# Шатлалгүй бол ===========
					elif line.condition_type == 'no_limit':
						_logger.info(u'-***********-contract - BY NO LIMIT -------\n')
						condition_ok = True

					# Нөхцөл хангасан бол хөнгөлөлт өгөх ==============================
					if condition_ok:	
						computed_contract = True
						# Бүх барааны хөнгөлөлт ---------------
						if line.pricelist_type == 'all':
							for o_line in order_line:
								if line.discount_type == 'percent':
									o_line['discount_percent_contract'] = line.discount_percent
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = ((100-line.discount_percent)*old_price)/100
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -ALL-Computed discount -----%d---\n', line.discount_percent)
								else:
									o_line['fixed_price_contract'] = line.fixed_price
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = line.fixed_price
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -ALL-Computed fixed -----%d---\n', line.fixed_price)
						
						# Ангилалаар байвал --------------------
						elif line.pricelist_type == 'category':
							lll = [ l for l in order_line if l['categ_id'] in line.category_ids.ids ]
							for o_line in lll:
								if line.discount_type == 'percent':
									o_line['discount_percent_contract'] = line.discount_percent
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = ((100-line.discount_percent)*old_price)/100
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -CATEG-Computed discount -----%d---\n', line.discount_percent)
								else:
									o_line.fixed_price_contract = line.fixed_price
									old_price = o_line.price_unit
									o_line.main_price_unit = old_price
									new_price = line.fixed_price
									o_line.price_unit = new_price
									# 
									sub_discount = (old_price-new_price)*o_line.product_uom_qty
									o_line.discount_contract_amount_sales = sub_discount
									o_line.name = contract.name
									_logger.info(u'-***********-contract -CATEG-Computed fixed -----%d---\n', line.fixed_price)
						
						# Бараагаар байвал ----------------------
						elif line.pricelist_type == 'product':
							lll = [ l for l in order_line if l['product_id'] == line.product_id.id ]
							for o_line in lll:
								if line.discount_type == 'percent':
									o_line['discount_percent_contract'] = line.discount_percent
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = ((100-line.discount_percent)*old_price)/100
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -PRODUCT-Computed discount -----%d---\n', line.discount_percent)
								else:
									o_line['fixed_price_contract'] = line.fixed_price
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = line.fixed_price
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -PRODUCT-Computed fixed -----%d---\n', line.fixed_price)
						
						# Brand байвал ----------------------
						elif line.pricelist_type == 'brand':
							lll = [ l for l in order_line if l['brand_id'] in line.brand_ids.ids ]
							for o_line in lll:
								if line.discount_type == 'percent':
									o_line['discount_percent_contract'] = line.discount_percent
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = ((100-line.discount_percent)*old_price)/100
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -BRAND-Computed discount -----%d---\n', line.discount_percent)
								else:
									o_line['fixed_price_contract'] = line.fixed_price
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = line.fixed_price
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -BRAND-Computed fixed -----%d---\n', line.fixed_price)
						
						# Template байвал ------------------------
						elif line.pricelist_type == 'product_template':
							lll = [ l for l in order_line if l['product_tmpl_id'] == line.product_tmpl_id.id ]
							for o_line in lll:
								if line.discount_type == 'percent':
									o_line['discount_percent_contract'] = line.discount_percent
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = ((100-line.discount_percent)*old_price)/100
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -TEMPLATE-Computed discount -----%d---\n', line.discount_percent)
								else:
									o_line['fixed_price_contract'] = line.fixed_price
									old_price = o_line['price_unit']
									o_line['main_price_unit'] = old_price
									new_price = line.fixed_price
									o_line['price_unit'] = new_price
									# 
									sub_discount = (old_price-new_price)*o_line['product_uom_qty']
									o_line['discount_contract_amount_sales'] = sub_discount
									o_line['name'] = contract.name
									_logger.info(u'-***********-contract -TEMPLATE-Computed fixed -----%d---\n', line.fixed_price)

				#  Хэрэв бүх барааны хөнгөлөлтийн % заасан бол шалгах ##################################################
				if contract.discount_percent > 0:
					_logger.info(u'-***********-contract -- per sales-COMPUTE-- direct percent % with LINES--------\n')
					for o_line in order_line:
						if not o_line['is_reward_product'] and o_line['discount_contract_amount_sales'] == 0:
							old_price = o_line['price_unit']
							o_line['discount_percent_contract'] = contract.discount_percent
							o_line['main_price_unit'] = old_price
							new_price = ((100-contract.discount_percent)*old_price)/100
							o_line['price_unit'] = new_price
							# Хөнгөлөлтийн дүнг бодох
							sub_discount = (old_price-new_price)*o_line['product_uom_qty']
							o_line['discount_contract_amount_sales'] = sub_discount
							o_line['name'] = contract.name
				
				_logger.info(u'-***********-contract -- PER sales - with pricelist_line --------\n')

			# =====DONE=======================================
			if computed_contract:
				result = {
					'order_line': order_line,
					'is_compute_contract': True,
					'contract_id': contract.id,
					'note': contract.name,
				}
				_logger.info(u'--contract compute--RESULT-%s', str(result))
				return result
			else:
				False
		return False

	def check_active(self):
		"""
		:return: Гэрээ идэвхтэй бол True идэвхгүй бол (хугацаа дууссан, ноорог г.м) False
		"""
		self.ensure_one()
		if self.state == 'confirmed' and self.active is True and (not self.date_end or self.date_end >= datetime.today()):
			return True
		return False


class SalesPricelistLine(models.Model):
	_name = 'mw.sales.pricelist.line'
	_description = 'Sales pricelist line'
	_order = 'name'

	# Columns
	parent_id = fields.Many2one('mw.sales.contract', 'Parent ID', ondelete='cascade')
	state = fields.Selection(related='parent_id.state', string="State", store=True)

	@api.depends('pricelist_type','category_ids','product_id','brand_ids')
	def _methods_compute(self):
		for obj in self:
			obj.name = "---"
			if obj.pricelist_type == 'all':
				obj.name = "All products"
			elif obj.pricelist_type == 'category':
				obj.name = ','.join(obj.category_ids.mapped('name'))
			elif obj.pricelist_type == 'brand':
				obj.name = ','.join(obj.brand_ids.mapped('name'))
			elif obj.pricelist_type == 'product':
				obj.name = obj.product_id.display_name
	name = fields.Char(string='Name', compute=_methods_compute )

	condition_type = fields.Selection([
			('amount', 'Amount'), 
			('qty', 'Quantity'),
			('no_limit', u'Нөхцөлгүй'),
		], default='amount', required=True, string='Condition type', copy=True)
	condition_min = fields.Float(string='Min', copy=True, required=True,)
	condition_max = fields.Float(string='Max', copy=True, required=True,)

	pricelist_type = fields.Selection([
			('all', 'All'),
			('category', 'Category'), 
			('brand', 'Brand'),
			('product', 'Product'),
		], default='all', required=True, string='Type', copy=True)
	category_ids = fields.Many2many('product.category', string='Categories', copy=True)
	brand_ids = fields.Many2many('product.brand', string='Brands', copy=True)
	product_id = fields.Many2one('product.product', string='Product', copy=True)

	discount_type = fields.Selection([
			('percent','Percent'),
			('amount',u'Fixed amount'),
		], required=True, string='Discount type', default='percent')
	discount_percent = fields.Float(string='Discount %', copy=True,)
	fixed_price = fields.Float(string='Fixed price', copy=True,)
