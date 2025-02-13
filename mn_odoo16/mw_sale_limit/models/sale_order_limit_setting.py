# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class SaleOrderLimitSetting(models.Model):
	_name = 'sale.order.limit.setting'
	_order = 'name'
	_description = 'Sale Order Limit Setting'

	@api.model
	def _get_user(self):
		return self.env.user

	# Columns
	name = fields.Char(u'Name', readonly=True, copy=False,)
	user_id = fields.Many2one('res.users', string='User', default=_get_user, readonly=True)
	state = fields.Selection([
			('draft', 'Draft'), 
			('confirmed', u'Confirmed'), 
		], default='draft', required=True, string=u'State', tracking=True, readonly=True, )
	warehouse_ids = fields.Many2many('stock.warehouse', string='Limiting warehouse', help=u"Хязгаарлалт хийх агуулахыг сонгоно уу",
		states={'confirmed': [('readonly', True)]}, required=True,)
	product_ids = fields.Many2many('product.product', string='Limiting products',
		states={'confirmed': [('readonly', True)]}, required=True,)
	partner_ids = fields.Many2many('res.partner', string='Approved partners',
		states={'confirmed': [('readonly', True)]}, )
	categ_ids = fields.Many2many('product.category', string='Limiting category',
		states={'confirmed': [('readonly', True)]}, )
	min_qty = fields.Integer(string='Lower limit', required=True, default=0, 
		states={'confirmed': [('readonly', True)]})
	description = fields.Text(string='Discription', 
		states={'confirmed': [('readonly', True)]})

	# --------- OVERRIDED ----------
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('In order to delete a record, it must be draft first!'))
		return super(SaleOrderLimitSetting, self).unlink()

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('sale.order.limit.setting')
		self.state = 'confirmed'
		self.user_id = self.env.user.id

	def _check_limit(self, warehouse, partner, product, qty):
		setting = self.env['sale.order.limit.setting'].search(
			[('state','=','confirmed'),
			 ('warehouse_ids','in',warehouse.id),
			 ('product_ids','in',product.id)], limit=1)
		_logger.info(u'-***********-----SO_check_limit--*************---ID-----\n')
		if setting:
			# Эхлээд тоог шалгана, дараа нь харилцагч шалгана
			# Үлдэгдэлээр хязгаарлалт хийсэн бол шалгах
			if setting.min_qty > 0:
				total_available_qty = self._get_available(product, warehouse)
				if total_available_qty <= setting.min_qty:
					# Зөвшөөрөгдсөн харилцагч дотор байгаа эсэхийг шалгах
					if setting.partner_ids and partner.id not in setting.partner_ids.ids:
						raise UserError(_(u'(%s) агуулах дээр (%s) барааны хязгаарлалт хийсэн байна!'%(warehouse.name, product.name)))
				return True
			else:
				# Зөвшөөрөгдсөн харилцагч дотор байгаа эсэхийг шалгах
				if setting.partner_ids and partner.id not in setting.partner_ids.ids:
					raise UserError(_(u'(%s) агуулах дээр (%s) барааны хязгаарлалт хийсэн байна!'%(warehouse.name, product.name)))
			return True

	# Барааны үлдэгдэл авах
	def _get_available(self, product_id, warehouse_id):
		total_available_qty = 0
		quant_obj = self.env['stock.quant']
		quant_ids = quant_obj.search([('product_id','=',product_id.id),('location_id','=',warehouse_id.lot_stock_id.id)])
		for qq in quant_ids:
			total_available_qty += (qq.quantity-qq.reserved_quantity)
		return total_available_qty