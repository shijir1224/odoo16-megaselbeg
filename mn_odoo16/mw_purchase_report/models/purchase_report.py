# -*- coding: utf-8 -*-
from odoo import fields, models, tools

class PurchaseStockReport(models.Model):
	_name = "purchase.stock.report"
	_description = "Purchase Stock Report"
	_auto = False

	order_id = fields.Many2one('purchase.order', string='PO дугаар', readonly=True)
	product_id = fields.Many2one('product.product', string='Бараа', readonly=True)
	picking_id = fields.Many2one('stock.picking', string='Агуулах баримт', readonly=True)
	partner_id = fields.Many2one('res.partner', string='Нийлүүлэгч', readonly=True)
	date = fields.Datetime(string='Агуулах огноо', readonly=True)
	default_code = fields.Char(string='Бараа код', readonly=True)
	product_qty = fields.Float(string='Тоо хэмжээ', readonly=True)
	price_unit = fields.Float(string='Нэгж дүн', group_operator='avg', readonly=True)
	sub_total = fields.Float(string='Нийт дүн', readonly=True)
	currency_id = fields.Many2one('res.currency', string='Валют', readonly=True)
	doned_user_id = fields.Many2one('res.users', string='Батласан хэрэглэгч', readonly=True)

	def _select(self):
		return """
			SELECT
				sm.id,
				sp.partner_id,
				po.id as order_id,
				pp.default_code,
				sm.product_id,
				CASE WHEN sl.usage = 'internal' THEN -sm.product_qty ELSE sm.product_qty END as product_qty,
				pol.price_unit,
				po.currency_id,
				sm.date,
				((CASE WHEN sl.usage='internal' THEN -sm.product_qty else sm.product_qty END)*abs(pol.price_unit)) as sub_total,
				sm.picking_id,
				sp.doned_user_id
		"""

	def _from(self):
		return """
			FROM stock_move AS sm
			left join stock_picking sp on (sp.id = sm.picking_id)
			left join purchase_order_line pol on (pol.id = sm.purchase_line_id)
			left join purchase_order po on (po.id = pol.order_id)
			left join product_product pp on (pp.id = sm.product_id)
			left join product_template pt on (pt.id = pp.product_tmpl_id)
			left join stock_location sl on (sl.id = sm.location_id)
		"""

	def _where(self):
		return """
			WHERE sm.state='done' and sm.purchase_line_id is not null
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE OR REPLACE VIEW {_table} AS (
				{_select}
				{_from}
				{_where}
			)
		""".format(_table=self._table, _select=self._select(), _from=self._from(), _where=self._where())
		)

class PurchaseReportInvoice(models.Model):
	_name = "purchase.report.invoice"
	_description = "Purchase Report Invoice"
	_auto = False

	order_id = fields.Many2one('purchase.order', string='PO number', readonly=True)
	partner_id = fields.Many2one('res.partner', string='Vendor name', readonly=True)
	invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
	date = fields.Date(string='Invoice date', readonly=True)
	due_date = fields.Date(string='Due date', readonly=True)
	currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
	amount = fields.Float(string='Total cost', readonly=True)
	amount_residual = fields.Float(string='Residual amount', readonly=True)
	amount_paid = fields.Float(string='Paid amount', readonly=True)
	company_id = fields.Many2one('res.company', string="Company",readonly=True)

	def _select(self):
		return """
			SELECT
				am.id,
				am.id as invoice_id,
				po.partner_id,
				po.id as order_id,
				am.date,
				am.invoice_date_due as due_date,
				po.currency_id,
				am.amount_total as amount,
				am.amount_residual,
				(am.amount_total-am.amount_residual) as amount_paid,
				am.company_id
		"""
	def _from(self):
		return """
			FROM account_move AS am
			left join account_move_purchase_order_rel rel on (rel.account_move_id=am.id)
			left join purchase_order po on (po.id=rel.purchase_order_id)
					"""
	def _where(self):
		return """
			WHERE am.state='posted' and rel.account_move_id is not null
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE OR REPLACE VIEW {_table} AS (
				{_select}
				{_from}
				{_where}
			)
		""".format(_table=self._table, _select=self._select(), _from=self._from(), _where=self._where())
		)
