# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class SalePivotReport(models.Model):
	_name = "sale.pivot.report"
	_description = "Sale pivot report"
	_auto = False
	_order = 'product_id'

	name = fields.Char(string=u'Дугаар / Нэр', readonly=True,  )
	partner_id = fields.Many2one('res.partner', string=u'Харилцагч', readonly=True, index=True )
	origin = fields.Char(string=u'Эх баримт', readonly=True,  )
	parent_id = fields.Many2one('res.partner', string=u'Толгой харилцагч', readonly=True,  )
	so_id = fields.Many2one('sale.order', string=u'Sale order', readonly=True,  )
	
	branch_id = fields.Many2one('res.branch', string=u'Салбар', readonly=True, index=True )
	warehouse_id = fields.Many2one('stock.warehouse', string=u'Агуулах', readonly=True, )
	order_date = fields.Date(u'Баталсан огноо', readonly=True, index=True)
	validity_date = fields.Date(u'Захиалсан огноо', readonly=True, index=True)
	product_id = fields.Many2one('product.product', string=u'Бараа', readonly=True, index=True )
	categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True, )
	barcode_name = fields.Char(string=u'Баркод / Нэр',)
	
	main_price_unit = fields.Float(u'Үндсэн үнэ', readonly=True, digits=(16,1), group_operator='avg')
	price_unit = fields.Float(u'Нэгж үнэ', readonly=True, digits=(16,1), group_operator='avg')
	
	return_qty = fields.Float(u'Буцаалт', readonly=True, digits=(16,1), )
	return_amount = fields.Float(u'Буцаалт дүн', readonly=True, digits=(16,1), )

	qty_ordered = fields.Float(u'Захиалсан тоо', readonly=True, digits=(16,1), )
	amount_order = fields.Float(u'Захиалсан дүн', readonly=True, digits=(16,1), )

	qty = fields.Float(u'Хүргэгдсэн тоо', readonly=True, digits=(16,1), )
	amount = fields.Float(u'Хүргэгдсэн дүн', readonly=True, digits=(16,1), )

	package = fields.Float(u'Хайрцаг', readonly=True, digits=(16,1), )

	qty_invoiced = fields.Float(u'Нэхэмжилсэн тоо', readonly=True, digits=(16,1), )
	amount_invoiced = fields.Float(u'Нэхэмжилсэн дүн', readonly=True, digits=(16,1), )

	qty_remaining = fields.Float(u'Үлдсэн тоо', readonly=True, digits=(16,1), )
	main_amount = fields.Float(u'Үндсэн дүн', readonly=True, digits=(16,1), )

	user_id = fields.Many2one('res.users', u'Борлуулагч', readonly=True, index=True )
	crm_team_id = fields.Many2one('crm.team', string=u'Суваг', readonly=True, index=True )
	company_id = fields.Many2one('res.company', u'Компани', readonly=True, index=True )
	
	invoice_status = fields.Selection([
		('upselling', 'Upselling Opportunity'),
		('invoiced', 'Fully Invoiced'),
		('to invoice', 'To Invoice'),
		('no', 'Nothing to Invoice')
		], readonly=True, string=u'Нэхэмжлэхийн төлөв')

	state = fields.Selection([
			('sale', 'Sale'), 
			('done', 'Done'),
		], readonly=True, string=u'Төлөв')

	return_reason = fields.Selection([
		('return_back', u'Буцаан татсан'),
		('return_expired', u'Хугацаа дөхсөн'),
		('return_complaints', u'Хэрэглэгчийн гомдол'),
		('return_closed', u'Дэлгүүр хаалттай'),
		('return_payment', u'Төлбөр бүрэн биш'),], 
		string=u'Буцаалтын шалтгаан', readonly=True, )

	def _select(self):
		return """
			SELECT  
				-sol.id as id,
				so.origin as origin,
				(so.validity_date+interval '8 hour')::date as order_date,
				so.validity_date as validity_date,
				so.name as name,
				so.partner_id as partner_id,
				(CASE WHEN rp.parent_id is not null THEN rp.parent_id else so.partner_id END) as parent_id,
				so.branch_id as branch_id,
				so.warehouse_id as warehouse_id,
				pt.categ_id as categ_id,
				pp.barcode||' / '||pt.name as barcode_name,
				sol.product_id as product_id,
				sol.price_unit as price_unit,
				(CASE WHEN sol.main_price_unit != 0 THEN sol.main_price_unit ELSE sol.price_unit END) as main_price_unit,
				
				sol.return_qty as return_qty,
				sol.qty_delivered as qty,
				(sol.qty_invoiced) as qty_invoiced,
				(sol.product_uom_qty) as qty_ordered,
				(sol.product_uom_qty - sol.qty_delivered) as qty_remaining,
				sol.package_qty as package,

				sol.return_qty * sol.price_unit as return_amount,
				sol.qty_delivered * sol.price_unit as amount,
				0 as main_amount,
				(sol.qty_invoiced) * sol.price_unit as amount_invoiced,
				(sol.product_uom_qty) * sol.price_unit as amount_order,

				so.user_id as user_id,
				so.team_id as crm_team_id,
				sol.invoice_status as invoice_status,
				so.state as state,
				sol.return_reason as return_reason,
				so.id as so_id,
				so.company_id as company_id
			FROM sale_order_line as sol
			LEFT JOIN sale_order as so on (so.id = sol.order_id)
			LEFT JOIN res_partner as rp on (rp.id = so.partner_id)
			LEFT JOIN product_product as pp on (pp.id = sol.product_id)
			LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
			WHERE so.state in ('sale','done')
		"""

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			%s
			)""" % (self._table, self._select())
		)
