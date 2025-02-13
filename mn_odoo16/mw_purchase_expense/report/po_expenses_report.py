# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class PoExpensesReport(models.Model):
	_name = "po.expenses.report"
	_auto = False
	_description = "Po expense report"
	_rec_name = 'id'

	order_id = fields.Many2one('purchase.order', 'Purchase order', readonly=True)
	product_id = fields.Many2one('product.product', 'Product', readonly=True)
	partner_id = fields.Many2one('res.partner', 'Customer Cost')
	po_partner_id = fields.Many2one('res.partner', 'Partner PO')
	amount = fields.Float('Amount of expenses Currency', readonly=True)
	current_amount = fields.Float('Cost ₮', readonly=True)
	currency_id = fields.Many2one('res.currency', 'Currency', readonly=True)
	portion_method = fields.Selection([
		('weight', 'Weight'),
		('volume', 'Volume'),
		('price', 'Unit Price'),
		('subtotal', 'SubTotal')
	], 'Allocation Method', readonly=True)
	notes = fields.Text('Notes', readonly=True)
	invoice_id = fields.Many2one('account.move', 'Invoice', readonly=True)
	is_without_cost = fields.Boolean('Not included in the cost /VAT../', readonly=True)
	date_cur = fields.Date('Exchange rate date', readonly=True)
	invoice_ref = fields.Char('Invoice number', readonly=True)
	date = fields.Datetime('Order Date', readonly=True)
	po_amount = fields.Float('PO Total amount currency', readonly=True)
	po_current_amount = fields.Float('PO total amount ₮', readonly=True)
	qty_ordered = fields.Float('Ordered quantity', readonly=True)
	po_product_id = fields.Many2one('product.product', 'PO product', readonly=True)
	product_uom = fields.Many2one('uom.uom', 'PO unit of measure', readonly=True)
	cost_unit = fields.Float('Absorbed Cost Unit', readonly=True, group_operator='avg')
	total_cost_unit = fields.Float('Total cost unit', readonly=True)

	def _select(self):
		return """
			SELECT
				ex.id,
				ex.order_id,
				ex.product_id,
				ex.partner_id,
				(ex.amount * COALESCE(cr.rate, 1.0) )::decimal(16,2) as current_amount,
				ex.amount,
				ex.currency_id,
				ex.portion_method,
				ex.notes,
				ex.invoice_id,
				ex.is_without_cost,
				ex.date_cur,
				ex.invoice_ref,
				po.date_planned as date,
				po.partner_id as po_partner_id,
				0 as po_current_amount,
				0 as po_amount,
				null as po_product_id,
				null as product_uom,
				0 as qty_ordered,
				0 as cost_unit,
				0 as total_cost_unit
		"""

	def _from(self):
		return """
			FROM purchase_order_expenses AS ex
		"""

	def _join(self):
		return """
			LEFT JOIN purchase_order AS po ON (po.id=ex.order_id)
			left join currency_rate cr on (cr.currency_id = ex.currency_id and
						cr.company_id = po.company_id and
						cr.date_start <= coalesce(ex.date_cur, now()) and
						(cr.date_end is null or cr.date_end > coalesce(ex.date_cur, now())))
		"""

	def _where(self):
		return """
			WHERE po.state!='cancel'
		"""

	def _select2(self):
		return """
			SELECT
				pol.id,
				pol.order_id,
				null as product_id,
				null partner_id,
				0 as current_amount,
				0 as amount,
				null as currency_id,
				null as portion_method,
				null as notes,
				null as invoice_id,
				null as is_without_cost,
				null as date_cur,
				null as invoice_ref,
				po.date_planned as date,
				po.partner_id as po_partner_id,
				(pol.price_total * COALESCE(cr.rate, 1.0) )::decimal(16,2) as po_current_amount,
				(pol.price_total)::decimal(16,2) as po_amount,
				pol.product_id as po_product_id,
				pt.uom_id as product_uom,
				pol.product_qty / line_uom.factor * product_uom.factor as qty_ordered,
				pol.cost_unit,
				pol.cost_unit*(pol.product_qty / line_uom.factor * product_uom.factor) as total_cost_unit
		"""

	def _from2(self):
		return """
			FROM purchase_order_line AS pol
		"""

	def _join2(self):
		return """
			LEFT JOIN purchase_order AS po ON (po.id=pol.order_id)
			left join currency_rate cr on (cr.currency_id = po.currency_id and
						cr.company_id = po.company_id and
						cr.date_start <= coalesce(po.date_currency, now()) and
						(cr.date_end is null or cr.date_end > coalesce(po.date_currency, now())))
			left join product_product pp on (pol.product_id=pp.id)
			left join product_template pt on (pp.product_tmpl_id=pt.id)
			left join uom_uom line_uom on (line_uom.id=pol.product_uom)
			left join uom_uom product_uom on (product_uom.id=pt.uom_id)
		"""

	def _where2(self):
		return """
			WHERE po.state!='cancel' and pol.cost_unit>0
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE OR REPLACE VIEW %s AS (
			WITH currency_rate as (%s)
				%s
				%s
				%s
				%s
				union all
				%s
				%s
				%s
				%s
			)
		""" % (self._table, self.env['res.currency']._select_companies_rates(), self._select(), self._from(), self._join(), self._where(), 
		self._select2(), self._from2(), self._join2(), self._where2())
		)

class PurchaseReport(models.Model):
	_inherit = "purchase.report"

	current_rate = fields.Float('Exchange Rate', readonly=True, group_operator='avg')
	
	def _select(self):
		res = super(PurchaseReport, self)._select()
		res+="""
		,avg(po.current_rate)::decimal(16,2) as current_rate
		"""
		return res
