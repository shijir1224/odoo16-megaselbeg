# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

from tempfile import NamedTemporaryFile
import base64
import xlrd

import pandas
import logging
_logger = logging.getLogger(__name__)

class MWSalesPromotionChangeDate(models.TransientModel):
	_name = "mw.sales.promotion.change.date"
	_description = "mw sales promotion change date"

	date_to = fields.Date(string=u'Дуусах огноо', required=True)

	def action_change_date(self):
		obj_ids = self.env['mw.sales.promotion'].search([('id','in',self._context['active_ids'])])
		for promo in obj_ids:
			if promo.date_start < self.date_to:
				promo.date_end = self.date_to
			else:
				raise UserError(_(u'Дуусах огноо эхлэх өдрөөс бага байна!'))

class MWSalesPromotion(models.Model):
	_name = 'mw.sales.promotion'
	_description = 'Sales promotion'
	_inherit = 'mail.thread'
	_order = 'date_start desc, name'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	name = fields.Char('Name', required=True, copy=True,
		states={'confirmed': [('readonly', True)]})
	date = fields.Datetime('Created date', readonly=True, default=fields.Datetime.now(), copy=False)
	date_start = fields.Date('Start date', copy=True, required=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)
	date_end = fields.Date('End date', copy=True, required=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)

	user_id = fields.Many2one('res.users', string='User', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', string='Confirmed by', readonly=True)

	warehouse_ids = fields.Many2many('stock.warehouse', string=u'Агуулах',
		states={'confirmed': [('readonly', True)]}, tracking=True)

	partner_category_ids = fields.Many2many('res.partner.category', string=u'Partner category', 
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)
	description = fields.Text(u'Description', copy=False, 
		states={'confirmed': [('readonly', True)]})
	
	priority = fields.Integer(string=u'Priority', required=True, default=3,
		states={'confirmed': [('readonly', True)]}, tracking=True)

	condition_type = fields.Selection([
			('product', 'By product'), 
			('brand', 'By brand'),
			('category', 'By category'),
			('amount', 'By amount'),
		], default='product', required=True, string='Condition type',
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)

	filter_product_ids = fields.Many2many('product.product', string=u'Бараанууд',
		states={'confirmed': [('readonly', True)]}, copy=True)

	is_even_level = fields.Boolean(string=u'Тэгш шатлалтай эсэх', 
		states={'confirmed': [('readonly', True)]}, tracking=True)
	is_not_set_amount = fields.Boolean(string=u'Дараагийн хөнгөлөлт % авахгүй', 
		help=u'Урамшуулалд хамрагдсан бол дараагийн хөнгөлөлт дээр үнийн дүнгийн хөнгөлөлт авахгүй байх',
		states={'confirmed': [('readonly', True)]}, tracking=True)
	
	no_balance = fields.Boolean(string=u'Паданы үлдэгдэлээс хасахгүй', default=False,
		help=u'Check хийвэл үнийн дүнд орно.\nУрамшуулалд орсон мөрийн тоог паданы үлдэгдэлээс хасахгүй үед сонгоно',
		states={'confirmed': [('readonly', True)]}, tracking=True)

	# Бараагаар үнийн дүн заах
	products_condition_type = fields.Selection([
			('qty', u'Тоо ширхэгээр'), 
			('amount', u'Мөнгөн дүнгээр'),
		], default='qty', string=u'Нөхцлийн төрөл',
		states={'confirmed': [('readonly', True)]},
		help=u"Хэрэв мөнгөн дүнгээр заасан бол барааны тоо хэмжээг тооцохгүй", tracking=True)
	products_amount = fields.Float(string=u'Барааны дүн', default=0, copy=True, 
		states={'confirmed': [('readonly', True)]}, digits=(16, 2), tracking=True)
	# -----------------------
	condition_condition = fields.Selection([
			('and', u'Бүх нөхцөл'), 
			('or', u'Аль нэг нь'),
		], default='or', string='Нөхцлийн бодох арга',
		states={'confirmed': [('readonly', True)]}, tracking=True)

	category_id = fields.Many2one('product.category', string='Category', 
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)
	brand_id = fields.Many2one('product.brand', string='Brand', 
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)
	
	qty_type = fields.Selection([
			('unit', u'Тоо ширхэгээр'), 
			('package', u'Хайрцагаар'),
			('amount', u'Мөнгөн дүнгээр'),
		], default='unit', string='Тоо хэмжээний төрөл',
		states={'confirmed': [('readonly', True)]}, tracking=True)
	condition_qty = fields.Float(string=u'Quantity', default=0, copy=True, 
		states={'confirmed': [('readonly', True)]}, digits=(16, 2), tracking=True)
	condition_amount = fields.Float(string=u'Amount', default=0, copy=True,
		states={'confirmed': [('readonly', True)]}, digits=(16, 2), tracking=True)

	condition_product_line = fields.One2many('condition.product.line', 'parent_id', 'Condition line', copy=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)

	reward_type = fields.Selection([
			('free_product', 'Free product'), 
			('fixed_price', 'Fixed price'), 
			('amount_discount', u'Дүнгээр'),
			('discount', 'Discount'),
		], default='free_product', required=True, string='Reward type',
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)
	is_limit_free_product = fields.Boolean(string=u'Барааны хязгаар', default=False,
		help="Хэрэв үнэгүй барааг өгөх үед хязгаарлалт хийх бол сонгоно уу",
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)
	amount_discount = fields.Float(string=u'Хөнгөлөлтийн дүн')
	discount_percent = fields.Float(string=u'Discount %', required=True, default=0,
		states={'confirmed': [('readonly', True)]}, digits=(16, 2), copy=True, tracking=True)
	discount_percent_all_lines = fields.Boolean(string=u'Бүх барааг хөнгөлөх эсэх', default=False,
		help=u'Хэрэв сонгох юм бол падааны бүх бараан дээр хөнгөлөлт үзүүлнэ, Үгүй бол зөвхөн нөхцөл хангаж бараан дээр хөнгөлнө', 
		states={'confirmed': [('readonly', True)]}, tracking=True)

	# Хөнгөлөлтийн дүнгийн оронд бараа авах
	get_gift_cart_amount = fields.Boolean(string=u'Хөнгөлөлтийн дүнгийн оронд бараа авах', default=False,
		help=u'Хөнгөлөлтийн хувь бодсон дүнгийн оронд бараа авах үед сонгоно. Өөрөөр хэлбэл бараа авах "Эрхийн бичих" үүсгэнэ.', 
		states={'confirmed': [('readonly', True)]}, tracking=True)
	
	free_product_type = fields.Selection([
			('no_choose_all', u'Бүгдийг өгөх'), 
			('choose', u'Сонголтоор'),
		], default='no_choose_all', string=u'Урамшууллын барааны сонголт',
		states={'confirmed': [('readonly', True)]}, tracking=True,
		help=u"Бүглийг өгөх сонгосон бол урамшууллын бараануудыг өгнө, Үгүй бол сонгосон бараануудаас өгнө", )

	reward_product_line = fields.One2many('reward.product.line', 'parent_id', 'Reward line', copy=True,
		states={'confirmed': [('readonly', True)]}, tracking=True)

	state = fields.Selection([
			('draft', 'Draft'), 
			('confirmed', 'Confirmed'),
		], default='draft', required=True, string='State', tracking=True)

	# Давхар гэрээтэй байсан ч урамшуулал өгөх эсэх
	is_double_promotion = fields.Boolean(string=u'Гэрээтэй урамшуулал өгөх эсэх',
		help=u"Сонгосон бол давхар гэрээтэй байсан ч урамшуулал өгнө", 
		states={'confirmed': [('readonly', True)]}, default=False, tracking=True)
	double_promotion_partner_id = fields.Many2many('res.partner', string=u'Давхар урамшуулал авах харилцагч', 
		help=u'Гэрээтэй харилцагчид давхар урамшуулал өгөхгүй үед онцгой нэг харилцагчид өгөх үед сонгоно',
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)
	# Давхар урамшуулал өгч болох эсэх
	# Ижил төрлийн урамшуулал ар араасаа өгөх бол сонгоно
	set_same_promos = fields.Boolean(string=u'Ижил төрлийн урамшуулал бодох эсэх', default=False, 
		help='Ижил төрлийн урамшууллыг давхардуулж өгөх үед сонгоно',
		states={'confirmed': [('readonly', True)]}, tracking=True)

	# IMPORT бараа
	excel_data = fields.Binary(string='Excel file', )
	
	# POS or Sale Order
	@api.model
	def _get_pos_or_saleorder(self):
		context = dict(self._context)
		if 'is_pos' in context and context['is_pos'] == True:
			return True
		return False
	is_pos = fields.Boolean(string='POS урмшуулал эсэх', default=_get_pos_or_saleorder, 
		states={'confirmed': [('readonly', True)]}, tracking=True)

	# Сонгож боддог урамшуулал эсэх
	can_be_selected = fields.Boolean(string=u'Сонгох боломжтой эсэх', default=False,
		help=u'Хэрэв сонгосон бол уг урамшууллыг захиалга дээр гараар сонгож бодох боломжтой болно.', 
		states={'confirmed': [('readonly', True)]}, tracking=True)

	# Төлбөрийн хэлбэрээс хамаарч бодох эсэх
	only_payment_cash = fields.Boolean(string=u'Зөвхөн бэлэнгийн айлд', default=True,
		help=u'Хэрэв сонгосон бол уг урамшууллыг Бэлэнгийн айлд өгнө. Сонгохгүй бол төлбөрийн хэлбэр хамаарахгүй өгнө.', 
		states={'confirmed': [('readonly', True)]}, tracking=True)

	# Гарагийн хягаар
	is_limit_weekday = fields.Boolean(string=u'7хоногийн хязгаартай эсэх', default=False,
		help=u'Урамшуулалыг 7хоногийн хязгаартай зарлах үед сонгоно.', 
		states={'confirmed': [('readonly', True)]}, tracking=True)
	monday = fields.Boolean(string=u'Даваа гараг', default=False,)
	tuesday = fields.Boolean(string=u'Мягмар гараг', default=False,)
	wednesday = fields.Boolean(string=u'Лхагва гараг', default=False,)
	thursday = fields.Boolean(string=u'Пүрэв гараг', default=False,)
	friday = fields.Boolean(string=u'Баасан гараг', default=False,)
	saturday = fields.Boolean(string=u'Бямба гараг', default=False,)
	sunday = fields.Boolean(string=u'Ням гараг', default=False,)

	# Цагийн хязгаар
	is_limit_time = fields.Boolean(string=u'Цагийн хязгаартай эсэх', default=False,
		help=u'Урамшуулалыг цагийн хязгаартай зарлах үед сонгоно.', 
		states={'confirmed': [('readonly', True)]}, tracking=True)
	start_time = fields.Integer(string='Эхлэх цаг', default=0, 
		states={'confirmed': [('readonly', True)]}, tracking=True)
	finish_time = fields.Integer(string='Дуусах цаг', default=0, 
		states={'confirmed': [('readonly', True)]}, tracking=True)

	# Харилцагчийн ангилалаас гадна зөвхөн хамрагдах харилцагчийг зааж өгч болно
	allowed_partner_ids = fields.Many2many('res.partner', 'rel_promo_allowed_partner', 'promo_id', 'partner_id',
		string=u'Зөвшөөрөгдсөн харилцагчид', 
		help=u'Харилцагчийн ангилалаас гадна зөвхөн хамрагдах харилцагчийг зааж өгч болно',
		states={'confirmed': [('readonly', True)]}, copy=True, tracking=True)

	@api.onchange('reward_type')
	def onchange_reward_type(self):
		for obj in self:
			if obj.reward_type == 'amount_discount' and obj.amount_discount > 0:
				obj.amount_discount = 0
			elif obj.reward_type == 'discount' and obj.discount_percent > 0:
				obj.discount_percent = 0
			elif obj.reward_type == 'fixed_price' and (obj.amount_discount > 0 or obj.discount_percent > 0) :
				obj.discount_percent = 0
			elif obj.reward_type == 'free_product' and (obj.amount_discount > 0 or obj.discount_percent > 0) :
				obj.discount_percent = 0
				
	# ---------- OVERRIDED METHODs --------
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('In order to delete a record, it must be draft first!'))
		return super(MWSalesPromotion, self).unlink()
	
	# ---------- CUSTOM METHODs --------
	def action_to_draft(self):
		self.state = 'draft'

	
	def action_to_confirm(self):
		self.state = 'confirmed'
		self.validator_id = self.env.user.id
		self.message_post(body="Confirmed by %s" % self.validator_id.name)

	# Урамшуулалын хугацаа шалгах - Крон метод
	@api.model
	def _check_expire_date(self):
		# Дуусч байгаа Урамшуулал шалгах
		today = datetime.now()
		date_stop = today + timedelta(days=2)
		promotions = self.env['mw.sales.promotion'].search([
			('state','=','confirmed'),
			('date_end','>=',today),
			('date_end','<=',date_stop)], order='priority')

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_sales_contract_promotion.action_sales_promotion').id
		
		for line in promotions:
			users = [line.user_id]
			if line.user_id.id != line.validator_id.id:
				users.append(line.validator_id)

			for receiver in users:
				if receiver.partner_id:
					if self.env.user.partner_id.id != receiver.partner_id.id:
						channel_ids = self.env['mail.channel'].search([
						   ('channel_partner_ids', 'in', receiver.partner_id.id),
						   ('channel_partner_ids', 'in', self.env.user.partner_id.id),
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
							self.env['bus.bus']._sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info)
							channel_ids = [new_channel.id]
						# MSG илгээх
						html = u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=mw.sales.promotion&action=%s>%s</a></b> урамшуулал хугацаа дуусч байна! %s """% (base_url,line.id,action_id,line.name, line.date_end)
						self.env['mail.message'].create({
								   'message_type': 'comment', 
								   'subtype_id': 1,
								   'body': html,
								   'channel_ids':  [(6, 0, channel_ids),]
								   })
	
	# TIME ZONE авах
	def _get_tz(self):
		return 8

	# order_lines --- FORMAT
	# order_lines = [
	# 	{'line_id':1,
	# 	 'product_id': 11,
	# 	 'price_unit': 12343,
	# 	 'product_uom_qty': 11,
	# 	 'is_not_set_amount': False,
	# 	},
	# 	{'line_id':1,
	# 	 'product_id': aa,
	# 	 'price_unit': 12343,
	# 	 'product_uom_qty': 11,
	# 	 'is_not_set_amount': False,
	# 	},
	# ]
	# ================== Урамшуулал бодох ==================================
	def compute_coupon_promotion(self, is_pos, validity_date, partner_id, order_lines, warehouse_id=False, custom_promo_id=False, payment_type=False):
		_logger.info(u'\n-**************-SELF promotion-COMPUTE--***************--------\n')
		products_qty = []
		package_setting = {}
		for line in order_lines:
			temp = {}
			product = self.env['product.product'].browse(line['product_id'])
			temp['line_id'] = line['line_id']
			temp['product_id'] = line['product_id']
			temp['price_unit'] = line['price_unit']
			temp['qty'] = line['product_uom_qty']
			temp['amount'] = line['price_unit'] * line['product_uom_qty']
			temp['brand_id'] = product.brand_id.id
			temp['categ_id'] = product.categ_id.id
			# ---
			line['brand_id'] = product.brand_id.id
			line['categ_id'] = product.categ_id.id
			# ---Хайрцагны тоо---------------------------------
			package_qty = 1
			if product.uom_po_id and product.uom_po_id.factor > 0:
				package_qty = product.uom_po_id.factor
			temp['package'] = line['product_uom_qty'] / package_qty
			package_setting[product.id] = package_qty
			products_qty.append(temp)

		df = pandas.DataFrame(products_qty)
		_logger.info(u'\n\n--*********PROMO QTYS***************---\n%s'%(str(df)))
		# Бараа болон үнийн дүнгийн үлдэгдэл тооцолж хадгалах
		if df.empty:
			return False
		so_amount = df['amount'].sum()
		first_so_amount = so_amount

		# Урамшуулалын DOMAIN бэлдэх
		domains = [
			('can_be_selected','=',False),
			('state','=','confirmed'),
			('date_start','<=',validity_date),
			('date_end','>=',validity_date),
			('is_pos','=',is_pos)]
		# Харилцагч байвал шүүлтэд нэмэх
		partner_obj = False
		partner_categs = False
		if partner_id:
			partner_obj = self.env['res.partner'].browse(partner_id)
			partner_categs = partner_obj.mapped('category_id.id')
			domains.append(('partner_category_ids','in',partner_categs))
		# Хамрагдах хөнгөлөлт урамшуулалыг олох
		promotions = self.env['mw.sales.promotion'].search(domains, order="priority")
		if custom_promo_id:
			_logger.info(u'\n\n--*********CUSTOM PROMOs***************---\n Promo ID %d' % custom_promo_id)
			promotions = self.env['mw.sales.promotion'].search([
				('id','=',custom_promo_id),
				('state','=','confirmed')], order="priority")
		_logger.info(u'\n\n--*********Find PROMOs***************---\n Promo %s, P.categ %s' % (str(promotions.ids), str(partner_categs)))

		# ================================
		promotion_names = []
		promotion_types = []
		free_product_lines = []
		promotion_ids = []
		# Үнийн дүнгийн хөнгөлөлт хадгалах
		amount_diff = 0

		for line in promotions:
			# Харилцагчийн ангилалыг зэрэг хангаж байгаа эсэхийг шалгах
			if not partner_obj or (line.partner_category_ids and set(line.partner_category_ids.mapped('id')).issubset(partner_categs)):
				_logger.info(u'\n-||||||||||||||||||||||-promotion-NAME----- %s-----' % (line.name))
				
				# Гэрээтэй хамт урамшуулал өгөх эсэх
				if not line.is_double_promotion:
					# Давхар гэрээ байгаа эсэхийг шалгах
					if partner_obj:
						contracts = self.env['mw.sales.contract'].search([
							('partner_id','in',[partner_obj.id, partner_obj.parent_id.id]),
							('state','=','confirmed'),
							('contract_type','!=','loan_contract'),
							('date_start','<=',validity_date),
							('date_end','>=',validity_date)])

						if contracts:
							# Хэрэв давхар өгнө гэж Харилцагч сонгосон бол шалгах
							if line.double_promotion_partner_id:
								partner_ids = line.double_promotion_partner_id.ids
								childs = self.env['res.partner'].search([('parent_id','in',partner_ids)]).mapped('id')
								partner_ids += childs
								# Давхар өгнө
								if partner_obj.id in partner_ids:
									_logger.info(u'\n--promotion--CHECK---- Contracts--Gereetei ontsgoi zaasan xariltsagch uramshuulald xamragdana---')
								else:
									_logger.info(u'\n--promotion--CHECK---- Contracts--Gereetei ontsgoi zaasan xariltsagch uramshuulald xamragdaxgvi---')
									continue
							else:
								_logger.info(u'\n--promotion--CHECK---- Contracts-tai -uramshuulald xamragdaxgvi---')
								continue
				
				# PROMO дээр зоосон агуулахыг шалгах ============================================
				if line.warehouse_ids and warehouse_id and warehouse_id not in line.warehouse_ids.ids: 
					_logger.info(u'\n--promotion--CHECK---- WAREHOUSEs - INGNORE ************  %d -  %s---' % (warehouse_id, line.warehouse_ids.ids))
					continue

				# Харилцагчийн ангилал дотор нь зөвхөн зөвшөөрөгдсөн харилцагч мөн эсэхийг шалгах
				if line.allowed_partner_ids and partner_obj and partner_obj.id not in line.allowed_partner_ids.ids:
					_logger.info(u'\n--promotion--CHECK---- Allowed Partners - INGNORE ************  %d -  %s---' % (partner_obj.id, line.allowed_partner_ids.ids))
					continue

				# Төлбөрийн хэлбэр шалгах ============================================
				if line.only_payment_cash and payment_type and payment_type != 'cash': 
					_logger.info(u'\n--promotion--CHECK---- payment_type - IGNORE ************ %s---' % (payment_type))
					continue
				
				# Төлбөрийн хэлбэр шалгах ============================================
				if not line.only_payment_cash and payment_type and payment_type == 'cash': 
					_logger.info(u'\n--promotion--CHECK---- payment_type - BELEN UYED algasnaa IGNORE ************ %s---' % (payment_type))
					continue

				# 7хоногийн гараг шалгах ============================================
				if line.is_limit_weekday: 
					now = datetime.now()
					week_number = now.weekday()+1
					if line.monday and week_number == 1:
						_logger.info(u'\n--promotion--CHECK---- WEEKDAY LIMIT - ************ Monday %s---' % (week_number))
					elif line.tuesday and week_number == 2:
						_logger.info(u'\n--promotion--CHECK---- WEEKDAY LIMIT - ************ Tuesday %s---' % (week_number))
					elif line.wednesday and week_number == 3:
						_logger.info(u'\n--promotion--CHECK---- WEEKDAY LIMIT - ************ Wednesday %s---' % (week_number))
					elif line.thursday and week_number == 4:
						_logger.info(u'\n--promotion--CHECK---- WEEKDAY LIMIT - ************ Thursday %s---' % (week_number))
					elif line.friday and week_number == 5:
						_logger.info(u'\n--promotion--CHECK---- WEEKDAY LIMIT - ************ Friday %s---' % (week_number))
					elif line.saturday and week_number == 6:
						_logger.info(u'\n--promotion--CHECK---- WEEKDAY LIMIT - ************ Saturday %s---' % (week_number))
					elif line.sunday and week_number == 7:
						_logger.info(u'\n--promotion--CHECK---- WEEKDAY LIMIT - ************ Sunday %s---' % (week_number))
					else:
						_logger.info(u'\n--promotion--CHECK---- WEEKDAY LIMIT - IGNORE ************')
						continue

				# Цагийн хязгаар шалгах ============================================
				if line.is_limit_time and line.start_time and line.finish_time: 
					now = datetime.now()
					hour = now.hour + self._get_tz()
					_logger.info(u'\n--promotion--CHECK---- TIME LIMIT - times ************ %d <= %d < %d ---' % (line.start_time, hour, line.finish_time))
					# Заасан цагийн хооронд бол бодно
					if line.start_time <= hour < line.finish_time:
						_logger.info(u'\n--promotion--CHECK---- TIME LIMIT - times ************ OK :)' )
					# Үгүй бол алгасна
					else:
						_logger.info(u'\n--promotion--CHECK---- TIME LIMIT - IGNORE ************---')
						continue

				condition_ok = False
				price_unit = 0
				reward_multipler = 1
				# Нөхцөл - Үнийн дүнгээр
				print('\nahahhahhahah', line.condition_type, line)
				if line.condition_type == 'amount':
					_logger.info(u'\n--promotion----- AMOUNT CONDITION---%f =%f--' % (so_amount, line.condition_amount))
					if so_amount >= line.condition_amount:
						condition_ok = True
						# Тэгш шатлал бодох
						if line.reward_type == 'free_product' and line.is_even_level:
							reward_multipler = so_amount // line.condition_amount
						# Сүүлд нэмсэн - Мөнгөн дүн барааны үлдэгдэл тусдаа бодож байгаа
						# Яалтчгүй
						amount_diff += line.condition_amount * reward_multipler

				# Нөхцөл - Брэндээр шалгах
				elif line.condition_type == 'brand':
					brand_id = line.brand_id.id
					_logger.info(u'\n--promotion------condition BRAND----%d %d-' % (brand_id, line.id))
					brand_qty = 0

					# Хэрэв брендийн бараа заасан бол шалгах
					if line.filter_product_ids:
						# Хэрэв хайрцагаар заасан бол
						if line.qty_type == 'package':
							tot = sum(df.loc[ df['product_id'].isin(line.filter_product_ids.mapped('id')) ]['package'])
							brand_qty = tot
						# Мөнгөн дүн заасан бол
						elif line.qty_type == 'amount':
							tot = sum(df.loc[ df['product_id'].isin(line.filter_product_ids.mapped('id')) ]['amount'])
							brand_qty = tot
						# Тоо ширхэг заасан бол
						else:
							tot = sum(df.loc[ df['product_id'].isin(line.filter_product_ids.mapped('id')) ]['qty'])
							brand_qty = tot

					# Бараа заагаагүй бол
					# Тухайн брендийн бүх барааны нийлбэр
					else:
						# Хэрэв хайрцагаар заасан бол
						if line.qty_type == 'package':
							result = dict(df.groupby('brand_id')['package'].sum())
							if brand_id in result:
								brand_qty = result[brand_id]
						# Мөнгөн дүн заасан бол
						elif line.qty_type == 'amount':
							result = dict(df.groupby('brand_id')['amount'].sum())
							if brand_id in result:
								brand_qty = result[brand_id]
						# Тоо ширхэг заасан бол
						else:
							result = dict(df.groupby('brand_id')['qty'].sum())
							if brand_id in result:
								brand_qty = result[brand_id]

					_logger.info(u'\n\n--promotion***********---BRAND CONDITION %d %d %s====='%(brand_qty, line.condition_qty, line.qty_type))
					# Нөхцөл шалгах
					if brand_qty >= line.condition_qty:
						condition_ok = True
						# Тэгш шатлал бодох
						if line.reward_type == 'free_product' and line.is_even_level:
							reward_multipler = brand_qty // line.condition_qty

						# Брендийн үлдэгдлийг хасах
						conf_qty = line.condition_qty * reward_multipler
						if line.qty_type != 'amount':
							# Тоо ширхэгийн үлдэгдэл хасах
							for index, row in df.iterrows():
								# Бараа заасан заасан барааны үлдэгдэл хасах
								if line.filter_product_ids:
									if row['product_id'] in line.filter_product_ids.ids and conf_qty > 0:
										old_qty = df.loc[ df['product_id'] == row['product_id'] ]['qty'][index]
										price_unit = df.loc[ df['product_id'] == row['product_id'] ]['price_unit'][index]
										# Хайрцаг руу хөрвүүлэх
										if line.qty_type == 'package':
											old_qty = old_qty / package_setting[row['product_id']]
										new_qty = 0
										if old_qty >= conf_qty:
											new_qty = old_qty - conf_qty
											conf_qty = 0
										else:
											conf_qty -= old_qty
											new_qty = 0

										# Тоо руу хөрвүүлэх
										if line.qty_type == 'package':
											new_qty = new_qty * package_setting[row['product_id']]

										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type == 'discount':
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'package'] = 0
											else:
												# Хайрцаг, тоог шинэчлэх
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = new_qty
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = new_qty * price_unit
												df.loc[ df['product_id'] == row['product_id'], 'package'] = new_qty / package_setting[row['product_id']]
										
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id = int(df.loc[ df['product_id'] == row['product_id'] ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break
										_logger.info(u'\n\n--promotion---************************---BRAND QTY yes filter product remove-%d---\n%s'%(conf_qty, str(df)))
								else:
									if row['brand_id'] == brand_id and conf_qty > 0:
										old_qty = df.loc[ df['product_id'] == row['product_id'] ]['qty'][index]
										price_unit = df.loc[ df['product_id'] == row['product_id'] ]['price_unit'][index]
										# Хайрцаг руу хөрвүүлэх
										if line.qty_type == 'package':
											old_qty = old_qty / package_setting[row['product_id']]
										new_qty = 0
										if old_qty >= conf_qty:
											new_qty = old_qty - conf_qty
											conf_qty = 0
										else:
											conf_qty -= old_qty
											new_qty = 0

										# Тоо руу хөрвүүлэх
										if line.qty_type == 'package':
											new_qty = new_qty * package_setting[row['product_id']]

										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type == 'discount':
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'package'] = 0
											else:
												# Хайрцаг, тоог шинэчлэх
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = new_qty
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = new_qty * price_unit
												df.loc[ df['product_id'] == row['product_id'], 'package'] = new_qty / package_setting[row['product_id']]
										
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id = int(df.loc[ df['product_id'] == row['product_id'] ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break
										_logger.info(u'\n\n--promotion---************************---BRAND QTY no filter products remove-%d---\n%s'%(conf_qty, str(df)))
						else:
							# Брендийн Мөнгөн дүнгийн үлдэгдэл хасах
							conf_amt = conf_qty
							for index, row in df.iterrows():
								# Бараа заасан заасан барааны үлдэгдэл хасах
								if line.filter_product_ids:
									if row['product_id'] in line.filter_product_ids.ids and conf_qty > 0:
										old_amt = df.loc[ df['product_id'] == row['product_id'] ]['amount'][index]
										price_unit = df.loc[ df['product_id'] == row['product_id'] ]['price_unit'][index]
										new_amt = 0
										if old_amt >= conf_amt:
											new_amt = old_amt - conf_amt
											conf_amt = 0
										else:
											conf_amt -= old_amt
											new_amt = 0

										new_qty = new_amt / price_unit
										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type == 'discount':
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'package'] = 0
											else:
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = new_qty
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = new_amt
												df.loc[ df['product_id'] == row['product_id'], 'package'] = new_qty / package_setting[row['product_id']]
										
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id =  int(df.loc[ df['product_id'] == row['product_id'] ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break
									_logger.info(u'\n\n--promotion---************************---BRAND AMOUNT yes filter products remove-%d---\n%s'%(conf_qty, str(df)))
								else:
									if row['brand_id'] == brand_id and conf_qty > 0:
										old_amt = df.loc[ df['product_id'] == row['product_id'] ]['amount'][index]
										price_unit = df.loc[ df['product_id'] == row['product_id'] ]['price_unit'][index]
										new_amt = 0
										if old_amt >= conf_amt:
											new_amt = old_amt - conf_amt
											conf_amt = 0
										else:
											conf_amt -= old_amt
											new_amt = 0

										new_qty = new_amt / price_unit
										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type == 'discount':
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'package'] = 0
											else:
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = new_qty
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = new_amt
												df.loc[ df['product_id'] == row['product_id'], 'package'] = new_qty / package_setting[row['product_id']]
										
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id =  int(df.loc[ df['product_id'] == row['product_id'] ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break
									_logger.info(u'\n\n--promotion---************************---BRAND AMOUNT no filter products remove-%d---\n%s'%(conf_qty, str(df)))

				# Нөхцөл - Ангилалаар
				elif line.condition_type == 'category':
					# category_ids = self.env['product.category'].search([('id','child_of',line.category_id.id)]).mapped('id')
					category_qty = 0
					categ_id = line.category_id.id

					# Хэрэв брендийн бараа заасан бол шалгах
					if line.filter_product_ids:
						# Хэрэв хайрцагаар заасан бол
						if line.qty_type == 'package':
							tot = sum(df.loc[ df['product_id'].isin(line.filter_product_ids.mapped('id')) ]['package'])
							category_qty = tot
						# Мөнгөн дүн заасан бол
						elif line.qty_type == 'amount':
							tot = sum(df.loc[ df['product_id'].isin(line.filter_product_ids.mapped('id')) ]['amount'])
							category_qty = tot
						# Тоо ширхэг заасан бол
						else:
							tot = sum(df.loc[ df['product_id'].isin(line.filter_product_ids.mapped('id')) ]['qty'])
							category_qty = tot
					else:
						# Хэрэв хайрцагаар заасан бол
						if line.qty_type == 'package':
							result = dict(df.groupby('categ_id')['package'].sum())
							if categ_id in result:
								category_qty = result[categ_id]
						# Мөнгөн дүн заасан бол
						elif line.qty_type == 'amount':
							result = dict(df.groupby('categ_id')['amount'].sum())
							if categ_id in result:
								category_qty = result[categ_id]
						# Тоо ширхэг заасан бол
						else:
							result = dict(df.groupby('categ_id')['qty'].sum())
							if categ_id in result:
								category_qty = result[categ_id]

					_logger.info(u'\n\n--promotion***********---CATEGORY CONDITION %d %d ====='%(category_qty, line.condition_qty))
					# Нөхцөл шалгах
					if category_qty >= line.condition_qty:
						condition_ok = True
						# Тэгш шатлал бодох
						if line.reward_type == 'free_product' and line.is_even_level:
							reward_multipler = category_qty // line.condition_qty

						# Ангилал үлдэгдлийг хасах
						conf_qty = line.condition_qty * reward_multipler
						if line.qty_type != 'amount':
							# Тоо ширхэгийн үлдэгдэл хасах
							for index, row in df.iterrows():
								# Бараа заасан заасан барааны үлдэгдэл хасах
								if line.filter_product_ids:
									if row['product_id'] in line.filter_product_ids.ids and conf_qty > 0:
										old_qty = df.loc[ df['product_id'] == row['product_id'] ]['qty'][index]
										price_unit = df.loc[ df['product_id'] == row['product_id'] ]['price_unit'][index]
										# Хайрцаг руу хөрвүүлэх
										if line.qty_type == 'package':
											old_qty = old_qty / package_setting[row['product_id']]
										new_qty = 0
										if old_qty >= conf_qty:
											new_qty = old_qty - conf_qty
											conf_qty = 0
										else:
											conf_qty -= old_qty
											new_qty = 0

										# Тоо руу хөрвүүлэх
										if line.qty_type == 'package':
											new_qty = new_qty * package_setting[row['product_id']]

										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type in ('discount', 'amount_discount'):
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'package'] = 0
											else:
												# Хайрцаг, тоог шинэчлэх
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = new_qty
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = new_qty * price_unit
												df.loc[ df['product_id'] == row['product_id'], 'package'] = new_qty / package_setting[row['product_id']]
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id =  int(df.loc[ df['product_id'] == row['product_id'] ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break
										_logger.info(u'\n\n--promotion---************************---CATEG yes filter products remove-%d---\n%s'%(conf_qty, str(df)))
								# Хэрэв бараа заагаагүй бол ангилалаас хасах
								else:
									if row['categ_id'] == categ_id and conf_qty > 0:
										old_qty = df.loc[ df['product_id'] == row['product_id'] ]['qty'][index]
										price_unit = df.loc[ df['product_id'] == row['product_id'] ]['price_unit'][index]
										# Хайрцаг руу хөрвүүлэх
										if line.qty_type == 'package':
											old_qty = old_qty / package_setting[row['product_id']]
										new_qty = 0
										if old_qty >= conf_qty:
											new_qty = old_qty - conf_qty
											conf_qty = 0
										else:
											conf_qty -= old_qty
											new_qty = 0

										# Тоо руу хөрвүүлэх
										if line.qty_type == 'package':
											new_qty = new_qty * package_setting[row['product_id']]

										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type in ('discount', 'amount_discount'):
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'package'] = 0
											else:
												# Хайрцаг, тоог шинэчлэх
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = new_qty
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = new_qty * price_unit
												df.loc[ df['product_id'] == row['product_id'], 'package'] = new_qty / package_setting[row['product_id']]
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id =  int(df.loc[ df['product_id'] == row['product_id'] ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break
										_logger.info(u'\n\n--promotion---************************---CATEG no filter products remove-%d---\n%s'%(conf_qty, str(df)))
						else:
							# Ангилал Мөнгөн дүнгийн үлдэгдэл хасах
							conf_amt = conf_qty
							for index, row in df.iterrows():
								# Бараа заасан заасан барааны үлдэгдэл хасах
								if line.filter_product_ids:
									if row['product_id'] in line.filter_product_ids.ids and conf_qty > 0:
										old_amt = df.loc[ df['product_id'] == row['product_id'] ]['amount'][index]
										price_unit = df.loc[ df['product_id'] == row['product_id'] ]['price_unit'][index]
										new_amt = 0
										if old_amt >= conf_amt:
											new_amt = old_amt - conf_amt
											conf_amt = 0
										else:
											conf_amt -= old_amt
											new_amt = 0

										new_qty = new_amt / price_unit
										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type in ('discount', 'amount_discount'):
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'package'] = 0
											else:
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = new_qty
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = new_amt
												df.loc[ df['product_id'] == row['product_id'], 'package'] = new_qty / package_setting[row['product_id']]
										
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id =  int(df.loc[ df['product_id'] == row['product_id'] ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break
									_logger.info(u'\n\n--promotion---************************---CATEG AMOUNT no filter product remove-%d---\n%s'%(conf_qty, str(df)))
								# Хэрэв барааны заагаагүй бол ангилалаас хасах
								else:
									if row['categ_id'] == categ_id and conf_qty > 0:
										old_amt = df.loc[ df['product_id'] == row['product_id'] ]['amount'][index]
										price_unit = df.loc[ df['product_id'] == row['product_id'] ]['price_unit'][index]
										new_amt = 0
										if old_amt >= conf_amt:
											new_amt = old_amt - conf_amt
											conf_amt = 0
										else:
											conf_amt -= old_amt
											new_amt = 0

										new_qty = new_amt / price_unit
										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type in ('discount', 'amount_discount'):
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = 0
												df.loc[ df['product_id'] == row['product_id'], 'package'] = 0
											else:
												df.loc[ df['product_id'] == row['product_id'], 'qty'] = new_qty
												df.loc[ df['product_id'] == row['product_id'], 'amount'] = new_amt
												df.loc[ df['product_id'] == row['product_id'], 'package'] = new_qty / package_setting[row['product_id']]
										
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id =  int(df.loc[ df['product_id'] == row['product_id'] ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break
									_logger.info(u'\n\n--promotion---************************---CATEG AMOUNT no filter product remove-%d---\n%s'%(conf_qty, str(df)))

				# Нөхцөл - Заасан бараагаар
				elif line.condition_type == 'product':
					plug = True
					temp = {}

					# Хасах барааны тоо
					remove_qty = {}
					# Барааны Тоо хэмжээ, хайрцагаар нөхцөл шалгах
					print('\nahahhahhahah', line.products_condition_type, line)
					if line.products_condition_type == 'qty':
						_logger.info(u'\n--promotion------condition PRODUCT--QTY---')
						for condition_line in line.condition_product_line:
							result = dict(df.groupby('product_id')['qty'].sum())
							product_qty = result[condition_line.product_id.id] if condition_line.product_id.id in result else 0
							_logger.info(u'\n--promotion------condition PRODUCT--QTY2-- %d %d', product_qty, condition_line.qty)
							if product_qty >= condition_line.qty:
								condition_ok = True
								remove_qty[ condition_line.product_id.id ] = condition_line.qty
								# Тэгш шатлал бодох
								if line.reward_type == 'free_product' and line.is_even_level:
									temp[condition_line.product_id.id] = product_qty // condition_line.qty
									_logger.info(u'\n----------------------------%d-%d----'%(product_qty,condition_line.qty))
								elif line.reward_type == 'free_product':
									temp[condition_line.product_id.id] = 1
							else:
								plug = False

						# And бүх нөхцөл биелэсэн эсэх
						if line.condition_condition == 'and':
							if condition_ok and plug:
								condition_ok = True
								if line.reward_type == 'free_product' and line.is_even_level:
									reward_multipler = temp[min(temp.keys(), key=(lambda k: temp[k]))]
								_logger.info(u'\n--promotion------product ok AND----%s-'%str(temp))
							else:
								condition_ok = False
								_logger.info(u'\n--promotion------PRODUCT fuck AND-----')
						else:
							if line.reward_type == 'free_product':
								reward_multipler = temp
								_logger.info(u'\n--promotion------PRODUCT OR----%s-'%str(reward_multipler))
						
						# Барааны үлдэгдлийг хасах
						if condition_ok:
							for key in remove_qty:
								old_qty =  df.loc[ df['product_id'] == key ]['qty']
								price_unit =  df.loc[ df['product_id'] == key ]['price_unit']
								multipler = reward_multipler[key] if isinstance(reward_multipler, dict) else reward_multipler
								new_qty = old_qty - remove_qty[key]*multipler
								# Үлдэгдлээс хасах үгүйг шалгах
								if not line.no_balance:
									# Хувиар хөнгөлөх бол бүгдийг нь хасах
									if line.reward_type in ('discount', 'amount_discount'):
										# new_qty = old_qty-(old_qty*line.discount_percent)/100
										df.loc[ df['product_id'] == key, 'qty'] = 0
										df.loc[ df['product_id'] == key, 'amount'] = 0
										df.loc[ df['product_id'] == key, 'package'] = 0
									else:
										df.loc[ df['product_id'] == key, 'qty'] = new_qty
										df.loc[ df['product_id'] == key, 'amount'] = new_qty * price_unit
										df.loc[ df['product_id'] == key, 'package'] = new_qty / package_setting[key]
								# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
								# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
								if line.is_not_set_amount:
									sol_id =  int(df.loc[ df['product_id'] == key ]['line_id'])
									sol = self.env['sale.order.line'].browse(sol_id)
									sol.is_not_set_amount = True

							_logger.info(u'\n--promotion---************************---PRODUCT remove----\n%s'%str(df))
							
					# Заасан бараануудын мөнгөн дүнгээр нөхцөл шалгах
					else:
						_logger.info(u'\n--promotion------condition PRODUCT--AMOUNT---')
						tot = sum(df.loc[ df['product_id'].isin(line.condition_product_line.mapped('product_id.id')) ]['amount'])
						if tot >= line.products_amount:
							# AND, OR нөхцөл хангаж байгааг шалгах
							if line.condition_condition == 'and':
								# Барааг зэрэг хангаж байгааг шалгах
								conf_p_ids = line.condition_product_line.mapped('product_id.id')
								order_p_ids = [ l['product_id'] for l in order_lines ]
								if set(conf_p_ids).issubset(order_p_ids):
									condition_ok = True
								else:
									condition_ok = False
							else:
								condition_ok = True

							# Нөхцөл хангасан бол
							if condition_ok:
								# Тэгш шатлал бодох
								if line.reward_type == 'free_product' and line.is_even_level:
									reward_multipler = tot // line.products_amount
									_logger.info(u'\n----------------------------%d-%d----'%(tot,line.products_amount))
								elif line.reward_type == 'free_product':
									reward_multipler = 1

								# Барааны дүн хасах
								conf_amt = line.products_amount * reward_multipler
								for p_id in line.condition_product_line.mapped('product_id.id'):
									if conf_amt > 0:
										_logger.info(u'\n\n--*********TEST QTYS***************---\n %s'%(str(df)))
										if df.loc[ df['product_id'] == p_id ].empty:
											continue
										old_amt = float(df.loc[ df['product_id'] == p_id ]['amount'])
										price_unit = float(df.loc[ df['product_id'] == p_id ]['price_unit'])
										new_amt = 0
										if old_amt >= conf_amt:
											new_amt = old_amt - conf_amt
											conf_amt = 0
										else:
											conf_amt -= old_amt
											new_amt = 0
										
										new_qty = new_amt / price_unit
										# Үлдэгдлээс хасах үгүйг шалгах
										if not line.no_balance:
											# Хувиар хөнгөлөх бол бүгдийг нь хасах
											if line.reward_type == 'discount':
												df.loc[ df['product_id'] == p_id, 'qty'] = 0
												df.loc[ df['product_id'] == p_id, 'amount'] = 0
												df.loc[ df['product_id'] == p_id, 'package'] = 0
											else:
												df.loc[ df['product_id'] == p_id, 'qty'] = new_qty
												df.loc[ df['product_id'] == p_id, 'amount'] = new_amt
												df.loc[ df['product_id'] == p_id, 'package'] = new_qty / package_setting[p_id] or 0
										# Хэрэв үнийн дүнд нөлөөлөхгүй сонгосон бол
										# Урамшуулал авсан мөр дээр тэмдэглэл хийнэ
										if line.is_not_set_amount:
											sol_id =  int(df.loc[ df['product_id'] == p_id ]['line_id'])
											for l in order_lines:
												if l['line_id'] == sol_id:
													l['is_not_set_amount'] = True
													break

				# Барааны үлдэгдлийн хассаны дараа
				# Нийт үнийн дүнг дахин бодох
				so_amount = df['amount'].sum()
				so_amount -= amount_diff
				
				# Урамшуулал бодох
				_logger.info(u'\n--promotion------condition %s---multipler -- %s %s' % (condition_ok,str(reward_multipler), str(so_amount)))
				if condition_ok:
					# Барааны урамшуулал =================================
					if line.reward_type == 'free_product':
						# Бүх бараануудыг өгөх =========================================
						if line.free_product_type == 'no_choose_all':
							# AND нөхцөлтэй бол
							if line.condition_condition == 'and' and line.condition_type == 'product':
								for reward_line in line.reward_product_line:
									# Хэрэв үнэгүй барааны хязгаартай бол шалгах
									if line.is_limit_free_product:
										if reward_line.available_limit < reward_line.qty * reward_multipler:
											_logger.info(u'\n--promotion------REWARD free product---IGNORE is_limit_free_product available = %d', reward_line.available_limit)
											continue
										else:
											reward_line.sudo().available_limit -= reward_line.qty * reward_multipler
									vals = {
										'product_id': reward_line.product_id.id,
										'product_uom_qty': reward_line.qty * reward_multipler,
										'price_unit': 0,
										'is_reward_product': True,
									}
									free_product_lines.append(vals)
								_logger.info(u'\n--promotion------REWARD free product---AND--')
								promotion_names.append(line.name)
								promotion_ids.append(line.id)
							# OR нөхцөлтэй бол
							elif line.condition_condition == 'or' and line.condition_type == 'product' and line.products_condition_type == 'qty':
								for condition_line in line.condition_product_line:
									product_qty = sum([ l['product_uom_qty'] for l in order_lines if l['product_id']==condition_line.product_id.id ])
									if product_qty >= condition_line.qty:
										for reward_line in line.reward_product_line:
											# Хэрэв үнэгүй барааны хязгаартай бол шалгах
											if line.is_limit_free_product:
												if reward_line.available_limit < reward_line.qty * reward_multipler[condition_line.product_id.id]:
													_logger.info(u'\n--promotion------REWARD free product---IGNORE is_limit_free_product available = %d', reward_line.available_limit)
													continue
												else:
													reward_line.sudo().available_limit -= reward_line.qty * reward_multipler[condition_line.product_id.id]
											vals = {
												'product_id': reward_line.product_id.id,
												'product_uom_qty': reward_line.qty * reward_multipler[condition_line.product_id.id],
												'price_unit': 0,
												'is_reward_product': True,
											}
											free_product_lines.append(vals)
										_logger.info(u'\n--promotion------REWARD free product---OR--')
										promotion_names.append(line.name)
										promotion_ids.append(line.id)
							else:
								for reward_line in line.reward_product_line:
									# Хэрэв үнэгүй барааны хязгаартай бол шалгах
									if line.is_limit_free_product:
										if reward_line.available_limit < reward_line.qty * reward_multipler:
											_logger.info(u'\n--promotion------REWARD free product---IGNORE is_limit_free_product available = %d', reward_line.available_limit)
											continue
										else:
											reward_line.sudo().available_limit -= reward_line.qty * reward_multipler
									vals = {
										'product_id': reward_line.product_id.id,
										'product_uom_qty': reward_line.qty * reward_multipler,
										'price_unit': 0,
										'is_reward_product': True,
									}
									free_product_lines.append(vals)
								_logger.info(u'\n--promotion------REWARD free product---OTHER--%d -multi %d' % (so_amount,reward_multipler))
								promotion_names.append(line.name)
								promotion_ids.append(line.id)
						# Сонгосон бараануудаас өгөхийг сонгосон бол ============
						# context дотор бараа нь байх ёстой =====================
						else:
							context = dict(self._context)
							_logger.info(u'\n--promotion------REWARD free product---CHOOSE- %s ', str(context))
							if 'reward_line' in context and context['reward_line']:
								for lll in context['reward_line']:
									vals = {
										'product_id': lll['product_id'],
										'product_uom_qty': lll['qty'],
										'price_unit': 0,
										'is_reward_product': True,
									}
									free_product_lines.append(vals)
								promotion_names.append(line.name)
								promotion_ids.append(line.id)
					
					# Үнийн дүгийн урамшуулалт =====================================
					elif line.reward_type == 'discount':
						# Давхар хөнгөлөлт буюу ижил төрлийн урамшуулал авч байгааг шалгах
						is_set_discount = [prm['condition_type'] for prm in promotion_types if prm['condition_type']==line.condition_type and prm['reward_type']==line.reward_type]
						_logger.info(u'\n--promotion---DAWXARDAL shalgax data:%s', str(is_set_discount))
						# Хэрэв нэг төрлийн Хөнгөлөлт, урамшуулалт биш бол хөнгөлөнө
						# Давхардаж байвал зүгээр алгасна
						if not is_set_discount or line.set_same_promos:
							# Нийт паданы дүнгээс хөнгөлөх
							if line.condition_type == 'amount':
								# Хэрэв хөнгөлөлтийн дүнгийн оронд GIFT cart авах бол
								if line.get_gift_cart_amount:
									bonus_amount = (first_so_amount * line.discount_percent)/100
									vals = {
										'name': (str(validity_date)+': '+partner_obj.display_name) if partner_obj else 'Хөнгөлөлтийн оронд бараа авах',
										'date_start': validity_date,
										'date_end': validity_date+timedelta(days=30),
										'partner_id': partner_obj.id or False,
										'bonus_amount': bonus_amount,
										'description': line.name +': Урамшууллын хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
									}
									gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
									gift.sudo().action_to_confirm()
									_logger.info(u'\n--promotion--- created GIFT CART id %d, SO %d, xuwi %d, bonus %d+++++++++++' % (gift.id, first_so_amount, line.discount_percent, bonus_amount))
								# Зүгээр хөнгөлөлтөө авах бол
								else:
									for o_line in order_lines:
										if not o_line['is_not_set_amount']:
											old_price = o_line['price_unit']
											o_line['discount_percent_coupon'] = line.discount_percent
											o_line['main_price_unit'] = old_price
											new_price = ((100-line.discount_percent)*old_price)/100
											o_line['price_unit'] = new_price
											# Хөнгөлөлтийн дүн бодох
											sub_discount = (old_price-new_price)*o_line['product_uom_qty']
											o_line['discount_coupon_amount'] = sub_discount

							# Заасан Барааны мөр дээр хөнгөлөх
							elif line.condition_type == 'product':
								lll = False
								# Падааны бүх бараа эсэх
								if line.discount_percent_all_lines:
									lll = [ l for l in order_lines ]
								# Үгүй бол нөхцөл хангаж байгаа мөр дээр хөнгөлөлт бодох
								else:
									lll = [ l for l in order_lines if l['product_id'] in line.condition_product_line.mapped('product_id.id') ]
								# Хэрэв хөнгөлөлтийн дүнгийн оронд GIFT cart авах бол
								if line.get_gift_cart_amount:
									bonus_amount = 0
									for ll in lll:
										old_price = ll['price_unit']
										new_price = ((100-line.discount_percent)*old_price)/100
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										bonus_amount += sub_discount
									vals = {
										'name': (str(validity_date)+': '+partner_obj.display_name) if partner_obj else 'Хөнгөлөлтийн оронд бараа авах',
										'date_start': validity_date,
										'date_end': validity_date+timedelta(days=30),
										'partner_id': partner_obj.id or False,
										'bonus_amount': bonus_amount,
										'description': line.name +': Урамшууллын хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
									}
									gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
									gift.sudo().action_to_confirm()
									_logger.info(u'\n--promotion--PRODUCT- created GIFT CART id %d, SO %d, xuwi %d, bonus %d+++++++++++' % (gift.id, first_so_amount, line.discount_percent, bonus_amount))
								# Зүгээр хөнгөлөлтөө авах бол
								else:
									for ll in lll:
										old_price = ll['price_unit']
										ll['discount_percent_coupon'] = line.discount_percent
										ll['main_price_unit'] = old_price
										new_price = ((100-line.discount_percent)*old_price)/100
										ll['price_unit'] = new_price
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										ll['discount_coupon_amount'] = sub_discount
							
							# Заасан Брэнд мөр дээр хөнгөлөх
							elif line.condition_type == 'brand':
								lll = False
								# Падааны бүх бараа эсэх
								if line.discount_percent_all_lines:
									lll = [ l for l in order_lines ]
								# Үгүй бол нөхцөл хангаж байгаа мөр дээр хөнгөлөлт бодох
								else:
									lll = [ l for l in order_lines if l['brand_id'] == line.brand_id.id]
								# Хэрэв хөнгөлөлтийн дүнгийн оронд GIFT cart авах бол
								if line.get_gift_cart_amount:
									bonus_amount = 0
									for ll in lll:
										old_price = ll['price_unit']
										new_price = ((100-line.discount_percent)*old_price)/100
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										bonus_amount += sub_discount
									vals = {
										'name': (str(validity_date)+': '+partner_obj.display_name) if partner_obj else 'Хөнгөлөлтийн оронд бараа авах',
										'date_start': validity_date,
										'date_end': validity_date+timedelta(days=30),
										'partner_id': partner_obj.id or False,
										'bonus_amount': bonus_amount,
										'description': line.name +': Урамшууллын хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
									}
									gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
									gift.sudo().action_to_confirm()
									_logger.info(u'\n--promotion--PRODUCT- created GIFT CART id %d, SO %d, xuwi %d, bonus %d+++++++++++' % (gift.id, first_so_amount, line.discount_percent, bonus_amount))
								# Зүгээр хөнгөлөлтөө авах бол
								else:
									for ll in lll:
										old_price = ll['price_unit']
										ll['discount_percent_coupon'] = line.discount_percent
										ll['main_price_unit'] = old_price
										new_price = ((100-line.discount_percent)*old_price)/100
										ll['price_unit'] = new_price
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										ll['discount_coupon_amount'] = sub_discount
							
							# Заасан Ангилал мөр дээр хөнгөлөх
							elif line.condition_type == 'category':
								category_ids = self.env['product.category'].search([('id','child_of',line.category_id.id)]).mapped('id')
								lll = False
								# Падааны бүх бараа эсэх
								if line.discount_percent_all_lines:
									lll = [ l for l in order_lines ]
								# Үгүй бол нөхцөл хангаж байгаа мөр дээр хөнгөлөлт бодох
								else:
									lll = [ l for l in order_lines if l['categ_id'] in category_ids]
								# Хэрэв хөнгөлөлтийн дүнгийн оронд GIFT cart авах бол
								if line.get_gift_cart_amount:
									bonus_amount = 0
									for ll in lll:
										old_price = ll['price_unit']
										new_price = ((100-line.discount_percent)*old_price)/100
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										bonus_amount += sub_discount
									vals = {
										'name': (str(validity_date)+': '+partner_obj.display_name) if partner_obj else 'Хөнгөлөлтийн оронд бараа авах',
										'date_start': validity_date,
										'date_end': validity_date+timedelta(days=30),
										'partner_id': partner_obj.id or False,
										'bonus_amount': bonus_amount,
										'description': line.name +': Урамшууллын хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
									}
									gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
									gift.sudo().action_to_confirm()
									_logger.info(u'\n--promotion--PRODUCT- created GIFT CART id %d, SO %d, xuwi %d, bonus %d+++++++++++' % (gift.id, first_so_amount, line.discount_percent, bonus_amount))
								# Зүгээр хөнгөлөлтөө авах бол
								else:
									for ll in lll:
										old_price = ll['price_unit']
										ll['discount_percent_coupon'] = line.discount_percent
										ll['main_price_unit'] = old_price
										new_price = ((100-line.discount_percent)*old_price)/100
										ll['price_unit'] = new_price
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										ll['discount_coupon_amount'] = sub_discount

							promotion_names.append(line.name)
							promotion_ids.append(line.id)
						else:
							_logger.info(u'\n--promotion---DAWXARDAJ bna--%d-%s', line.id, line.name)
					
					# Үнийн дүгийн урамшуулалт =====================================
					elif line.reward_type == 'amount_discount':
						# Давхар хөнгөлөлт буюу ижил төрлийн урамшуулал авч байгааг шалгах
						is_set_discount = [prm['condition_type'] for prm in promotion_types if prm['condition_type']==line.condition_type and prm['reward_type']==line.reward_type]
						_logger.info(u'\n--promotion---DAWXARDAL shalgax data:%s', str(is_set_discount))
						# Хэрэв нэг төрлийн Хөнгөлөлт, урамшуулалт биш бол хөнгөлөнө
						# Давхардаж байвал зүгээр алгасна
						if not is_set_discount or line.set_same_promos:
							# Нийт паданы дүнгээс хөнгөлөх
							if line.condition_type == 'amount':
								# Хэрэв хөнгөлөлтийн дүнгийн оронд GIFT cart авах бол
								if line.get_gift_cart_amount:
									bonus_amount = (first_so_amount * line.discount_percent)/100
									vals = {
										'name': (str(validity_date)+': '+partner_obj.display_name) if partner_obj else 'Хөнгөлөлтийн оронд бараа авах',
										'date_start': validity_date,
										'date_end': validity_date+timedelta(days=30),
										'partner_id': partner_obj.id or False,
										'bonus_amount': bonus_amount,
										'description': line.name +': Урамшууллын хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
									}
									gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
									gift.sudo().action_to_confirm()
									_logger.info(u'\n--promotion--- created GIFT CART id %d, SO %d, xuwi %d, bonus %d+++++++++++' % (gift.id, first_so_amount, line.discount_percent, bonus_amount))
								# Зүгээр хөнгөлөлтөө авах бол
								else:
									for o_line in order_lines:
										if not o_line['is_not_set_amount']:
											old_price = o_line['price_unit']
											o_line['main_price_unit'] = old_price
											new_price = old_price - amount_discount
											o_line['price_unit'] = new_price
											# Хөнгөлөлтийн дүн бодох
											sub_discount = (old_price-new_price)*o_line['product_uom_qty']
											o_line['discount_coupon_amount'] = sub_discount

							# Заасан Барааны мөр дээр хөнгөлөх
							elif line.condition_type == 'product':
								lll = False
								# Падааны бүх бараа эсэх
								if line.discount_percent_all_lines:
									lll = [ l for l in order_lines ]
								# Үгүй бол нөхцөл хангаж байгаа мөр дээр хөнгөлөлт бодох
								else:
									lll = [ l for l in order_lines if l['product_id'] in line.condition_product_line.mapped('product_id.id') ]
								# Хэрэв хөнгөлөлтийн дүнгийн оронд GIFT cart авах бол
								if line.get_gift_cart_amount:
									bonus_amount = 0
									for ll in lll:
										old_price = ll['price_unit']
										new_price = old_price - amount_discount
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										bonus_amount += sub_discount
									vals = {
										'name': (str(validity_date)+': '+partner_obj.display_name) if partner_obj else 'Хөнгөлөлтийн оронд бараа авах',
										'date_start': validity_date,
										'date_end': validity_date+timedelta(days=30),
										'partner_id': partner_obj.id or False,
										'bonus_amount': bonus_amount,
										'description': line.name +': Урамшууллын хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
									}
									gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
									gift.sudo().action_to_confirm()
									_logger.info(u'\n--promotion--PRODUCT- created GIFT CART id %d, SO %d, xuwi %d, bonus %d+++++++++++' % (gift.id, first_so_amount, line.discount_percent, bonus_amount))
								# Зүгээр хөнгөлөлтөө авах бол
								else:
									for ll in lll:
										old_price = ll['price_unit']
										ll['main_price_unit'] = old_price
										new_price = old_price - amount_discount
										ll['price_unit'] = new_price
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										ll['discount_coupon_amount'] = sub_discount
							
							# Заасан Брэнд мөр дээр хөнгөлөх
							elif line.condition_type == 'brand':
								lll = False
								# Падааны бүх бараа эсэх
								if line.discount_percent_all_lines:
									lll = [ l for l in order_lines ]
								# Үгүй бол нөхцөл хангаж байгаа мөр дээр хөнгөлөлт бодох
								else:
									lll = [ l for l in order_lines if l['brand_id'] == line.brand_id.id]
								# Хэрэв хөнгөлөлтийн дүнгийн оронд GIFT cart авах бол
								if line.get_gift_cart_amount:
									bonus_amount = 0
									for ll in lll:
										old_price = ll['price_unit']
										new_price = old_price - amount_discount
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										bonus_amount += sub_discount
									vals = {
										'name': (str(validity_date)+': '+partner_obj.display_name) if partner_obj else 'Хөнгөлөлтийн оронд бараа авах',
										'date_start': validity_date,
										'date_end': validity_date+timedelta(days=30),
										'partner_id': partner_obj.id or False,
										'bonus_amount': bonus_amount,
										'description': line.name +': Урамшууллын хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
									}
									gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
									gift.sudo().action_to_confirm()
									_logger.info(u'\n--promotion--PRODUCT- created GIFT CART id %d, SO %d, xuwi %d, bonus %d+++++++++++' % (gift.id, first_so_amount, line.discount_percent, bonus_amount))
								# Зүгээр хөнгөлөлтөө авах бол
								else:
									for ll in lll:
										old_price = ll['price_unit']
										ll['main_price_unit'] = old_price
										new_price = old_price - amount_discount
										ll['price_unit'] = new_price
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										ll['discount_coupon_amount'] = sub_discount
							
							# Заасан Ангилал мөр дээр хөнгөлөх
							elif line.condition_type == 'category':
								category_ids = self.env['product.category'].search([('id','child_of',line.category_id.id)]).mapped('id')
								lll = False
								# Падааны бүх бараа эсэх
								if line.discount_percent_all_lines:
									lll = [ l for l in order_lines ]
								# Үгүй бол нөхцөл хангаж байгаа мөр дээр хөнгөлөлт бодох
								else:
									lll = [ l for l in order_lines if l['categ_id'] in category_ids]
								# Хэрэв хөнгөлөлтийн дүнгийн оронд GIFT cart авах бол
								if line.get_gift_cart_amount:
									bonus_amount = 0
									for ll in lll:
										old_price = ll['price_unit']
										new_price = old_price - amount_discount
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										bonus_amount += sub_discount
									vals = {
										'name': (str(validity_date)+': '+partner_obj.display_name) if partner_obj else 'Хөнгөлөлтийн оронд бараа авах',
										'date_start': validity_date,
										'date_end': validity_date+timedelta(days=30),
										'partner_id': partner_obj.id or False,
										'bonus_amount': bonus_amount,
										'description': line.name +': Урамшууллын хөнгөлөлтийн дүнгээр бараа авах эрх үүслээ',
									}
									gift = self.env['mw.sales.gift.cart'].sudo().create(vals)
									gift.sudo().action_to_confirm()
									_logger.info(u'\n--promotion--PRODUCT- created GIFT CART id %d, SO %d, xuwi %d, bonus %d+++++++++++' % (gift.id, first_so_amount, line.discount_percent, bonus_amount))
								# Зүгээр хөнгөлөлтөө авах бол
								else:
									for ll in lll:
										old_price = ll['price_unit']
										ll['main_price_unit'] = old_price
										new_price = old_price - amount_discount
										ll['price_unit'] = new_price
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										ll['discount_coupon_amount'] = sub_discount

							promotion_names.append(line.name)
							promotion_ids.append(line.id)
						else:
							_logger.info(u'\n--promotion---DAWXARDAJ bna--%d-%s', line.id, line.name)
					
					# Үнийн дүнг зааж хөнгөлөлт үзүүлэх ==== FIXED PRICE ===========================
					elif line.reward_type == 'fixed_price':
						# Давхар хөнгөлөлт буюу ижил төрлийн урамшуулал авч байгааг шалгах
						is_set_discount = [prm['condition_type'] for prm in promotion_types if prm['condition_type']==line.condition_type and prm['reward_type']==line.reward_type]
						_logger.info(u'\n--promotion---DAWXARDAL shalgax data:%s', str(is_set_discount))
						# Хэрэв нэг төрлийн Хөнгөлөлт, урамшуулалт биш бол хөнгөлөнө
						# Давхардаж байвал зүгээр алгасна
						if not is_set_discount or line.set_same_promos:
							# Заасан Барааны мөр дээр хөнгөлөх
							for rline in line.reward_product_line:
								_logger.info(u'\n--promotion---FIXED PRICE--reward product id %d', rline.product_id.id)
								for ll in order_lines:
									_logger.info(u'\n--promotion---FIXED PRICE--orderline product id %d', ll['product_id'])
									if ll['product_id'] == rline.product_id.id:
										old_price = ll['price_unit']
										ll['discount_percent_coupon'] = 1
										ll['main_price_unit'] = old_price
										new_price = rline.fixed_price
										ll['price_unit'] = new_price
										# Хөнгөлөлтийн дүн бодох
										sub_discount = (old_price-new_price)*ll['product_uom_qty']
										ll['discount_coupon_amount'] = sub_discount
									else:
										_logger.info(u'\n--promotion---FIXED PRICE-NOT FOUND product-%d', rline.product_id.id)
							promotion_names.append(line.name)
							promotion_ids.append(line.id)
						else:
							_logger.info(u'\n--promotion---DAWXARDAJ bna FIXED PRICE--%d-%s', line.id, line.name)
					# ======== Авсан урамшууллын төрлийг нэмэх, дараа нь шалгах ===================================================================================
					promotion_types.append({'condition_type':line.condition_type, 'reward_type':line.reward_type})
				
				_logger.info(u'\n--One promotion ENDING---\n\n')	
		# print df, '================END======================'
		if promotion_ids:
			result = {
				'order_line': order_lines,
				'free_product': free_product_lines or [],
				'promotion_ids': promotion_ids or False,
				'promotion_names': promotion_names or False,
			}
			_logger.info(u'\n--promotion--RESULT-%s', str(result))
			return result
		else:
			False

	def import_from_excel(self):
		_logger.info(u'-***********--import_from_excel--*************--')

		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		book = xlrd.open_workbook(fileobj.name)
		try :
			 sheet = book.sheet_by_index(0)
		except:
			 raise UserError(u'Warning', u'Wrong Sheet number.')
		# ДАТА унших
		temp_datas = {}
		nrows = sheet.nrows
		ncols = sheet.ncols
		_logger.info(u'-***********--rows, cols--************* %d %d ', nrows, ncols)
		for r in range(1, nrows):
			row = sheet.row(r)
			search_value = ""
			product = False
			if row[0].value:
				search_value = row[0].value
				if isinstance(search_value, float):
					if (search_value - int(search_value)) == 0:
						search_value = int(search_value)
				product = self.env['product.product'].search([('default_code','=',search_value)], limit=1)
			elif row[1].value:
				search_value = row[1].value
				if isinstance(search_value, float):
					if (search_value - int(search_value)) == 0:
						search_value = int(search_value)
				product = self.env['product.product'].search([('barcode','=',search_value)], limit=1)
			qty = row[2].value if row[2].value else 1
			# Line үүсгэх
			if product:
				vals = {
					'parent_id': self.id,
					'product_id': product.id,
					'qty': qty,
				}
				line = self.env['condition.product.line'].create(vals)
		return True

class PromotionProductLine(models.Model):
	_name = 'condition.product.line'
	_description = 'Promotion product line'
	_order = 'product_id'

	# Columns
	parent_id = fields.Many2one('mw.sales.promotion', 'Parent ID', ondelete='cascade')

	product_id = fields.Many2one('product.product', string='Product', required=True, copy=True)
	qty = fields.Float(string='Quantity', copy=True, default=1)

class RewardProductLine(models.Model):
	_name = 'reward.product.line'
	_description = 'Reward product line'
	_order = 'product_id'

	# Columns
	parent_id = fields.Many2one('mw.sales.promotion', 'Parent ID', ondelete='cascade')

	product_id = fields.Many2one('product.product', string='Product', required=True, copy=True)
	qty = fields.Float(string='Quantity', copy=True, default=1, )
	fixed_price = fields.Float(string='Fixed price', copy=True, default=0, )

	qty_limit = fields.Float(string='Урамшууллын хязгаар', copy=True, default=0, 
		help="Урамшуулалд өгөх барааны хязгаар")
	available_limit = fields.Float(string='Боломжит хязгаар', copy=True, default=0, readonly=True, 
		help="Урамшуулалд өгөх хязгаараас үлдсэн тоо хэмжээ")

	@api.onchange('qty_limit')
	def onchange_qty_limit(self):
		if self.qty_limit:
			self.available_limit = self.qty_limit
		elif self.parent_id.is_limit_free_product and self.qty_limit == 0:
			raise UserError(_(u'Үнэгүй барааны хязрааыг оруулна уу!'))


