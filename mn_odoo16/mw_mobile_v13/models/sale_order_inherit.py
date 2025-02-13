# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging
import datetime

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
	_inherit = "product.template"
	
	see_mobile = fields.Boolean('Утсанд харагдах', default=False)

class SaleOrder(models.Model):
	_inherit = 'sale.order'
	
	mobile_id = fields.Integer('Mobile ID')
	driver_id = fields.Many2one('res.users', string='Driver', 
		domain=[('team_type','=','driver')],)
	with_e_tax = fields.Boolean(string=u'НӨАТ авах эсэх',
		states={'done':[('readonly',True)],'cancel':[('readonly',True)]})
	# Хүргэх огноо
	picking_date = fields.Date(u'Хүргэх огноо', copy=False,
		states={'sale':[('readonly',True)],'done':[('readonly',True)],'cancel':[('readonly',True)]})
	@api.depends('order_line.price_unit','order_line.qty_invoiced')
	def _invoice_amount_all(self):
		for obj in self:
			obj.invoice_amount_total = sum([x.price_unit*x.qty_invoiced for x in obj.order_line])
	invoice_amount_total = fields.Monetary(string='Нэхэмжилсэн нийт дүн', store=True, readonly=True, compute='_invoice_amount_all',)
	
	# Үнэ дахин бодуулах
	def button_dummy(self):
		for line in self.order_line:
			# line.product_id_change()
			line.main_price_unit = 0
		_logger.info('-------- SO Button dummy -----')

	# Хүргэх огноогоор хойшлуулах =====================
	def _days_between(self, d1, d2):
		return abs((d2 - d1).days)
	def action_confirm(self): 
		res = super(SaleOrder, self).action_confirm()
		for so in self:
			dt = datetime.datetime.now()
			time = dt.strftime("%Y-%m-%d %H:%M:%S")
			for sp in so.picking_ids:                          
				sp.scheduled_date = self.picking_date.strftime("%Y-%m-%d")+time[10:]
		return res

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	@api.depends('move_ids','move_ids.picking_id.return_reason','move_ids.state')
	def _compute_get_delivered_qty(self):
		for item in self:
			qty = 0.0
			for move in item.move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and r.location_dest_id.usage!='customer'):
				qty += move.product_uom._compute_quantity(move.product_uom_qty, item.product_uom)
			item.return_qty_non_store = qty

			qty = 0.0
			for move in item.move_ids.filtered(lambda r: r.state == 'done' and not r.scrapped and r.location_dest_id.usage!='customer' and r.picking_id.return_reason):
				qty += move.product_uom._compute_quantity(move.product_uom_qty, item.product_uom)
				item.return_reason = move.picking_id.return_reason
			item.return_qty = qty

	# Columns
	return_qty_non_store = fields.Float(string=u'Буцах ёстой', readonly=True, compute='_compute_get_delivered_qty')
	return_qty = fields.Float(string=u'Return qty', readonly=True, default=0, digits=(16,2) ,compute='_compute_get_delivered_qty', store=True)
	total_return_qty = fields.Float(string=u'Нийт буцаалтын тоо', readonly=True, default=0, digits=(16,2) )
	return_reason = fields.Selection([
			('return_closed', u'Буцаалт - Дэлгүүр хаалттай'),
			('return_complaints', u'Буцаалт - Хэрэглэгчийн гомдол'),
			('return_event_back', u'Буцаалт - Event-ийн буцаан таталт'),
			('return_nuuts_ikhtei', u'Буцаалт - Нөөц ихтэй'),
			('return_expired', u'Буцаалт - Хугацаа дөхсөн'),
			('return_no_shop', u'Буцаалт - Татан буугдсан'),
			('return_wrong_data', u'Буцаалт - Буруу мэдээлэл, өгөгдөлтэй'),
			('return_back', u'Буцаан татсан'),
		], string='Буцаалтын шалтгаан', compute='_compute_get_delivered_qty', store=True )