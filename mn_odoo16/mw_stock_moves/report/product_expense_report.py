# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api

class ProductExpenseReport(models.Model):
	_name = "product.expense.report"
	_description = "Product expense report"
	_auto = False

	expense_id = fields.Many2one('stock.product.other.expense', string='Дугаар')
	date = fields.Date(string='Үүсгэсэн огноо')
	branch_id = fields.Many2one('res.branch', string='Салбар')
	warehouse_id = fields.Many2one('stock.warehouse', string='Агуулах')
	partner_id = fields.Many2one('res.partner', string='Хариуцагч')
	department_id = fields.Many2one('hr.department', string='Хэлтэс')
	transaction_value_id = fields.Many2one('mn.transaction.value', string='Зарлага гүйлгээний төрөл')
	product_id = fields.Many2one('product.product', string='Бараа')
	categ_id = fields.Many2one('product.category', string='Барааны ангилал')
	qty = fields.Float(string='Тоо хэмжээ')
	delivered_qty = fields.Float(string='Хүргэгдсэн тоо хэмжээ')
	product_standard_price = fields.Float(string='Нэгж өртөг')
	product_total_price = fields.Float(string='Нийт өртөг')
	res_partner_id = fields.Many2one('res.partner', string='Хүлээн авсан ажилтан')
	# picking_id = fields.Many2one('stock.picking', string='Зарлага')
	description = fields.Char(string='Тайлбар')
	# state_type = fields.Char(string='Төлөвийн төрөл')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв')
	scheduled_date = fields.Date(string='Товлосон огноо')



	def _select(self):
		return """
			SELECT
				(expense.id::text||expense.company_id::text)::bigint as id,
				expense.id as expense_id,
				expense.date AS date,
				expense.date_required AS scheduled_date,
				expense.branch_id AS branch_id,
				expense.warehouse_id AS warehouse_id,
				expense.partner_id AS partner_id,
				expense.department_id AS department_id,
				expense.transaction_value_id AS transaction_value_id,
				line.product_id AS product_id,
				pc.id AS categ_id,
				line.qty AS qty,
				line.delivered_qty AS delivered_qty,
				line.product_standard_price AS product_standard_price,
				line.product_total_price AS product_total_price,
				line.res_partner_id AS res_partner_id,
				--sp.id AS picking_id,
				expense.description AS description,
				expense.flow_line_id AS flow_line_id
		"""

	def _from(self):
		return """
			FROM stock_product_other_expense_line AS line
				LEFT JOIN stock_product_other_expense AS expense ON (expense.id = line.parent_id)
				LEFT JOIN product_product AS pp ON (pp.id = line.product_id)
				LEFT JOIN product_template AS pt ON (pt.id = pp.product_tmpl_id)
				LEFT JOIN product_category AS pc ON (pc.id = pt.categ_id)
				--LEFT JOIN stock_picking AS sp ON (sp.other_expense_id = expense.id)
		"""

	def _where(self):
		return '''
			WHERE expense.state_type = 'done'
		'''

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE OR REPLACE VIEW %s AS (%s %s %s)
		""" %(self._table, self._select(), self._from(), self._where())
		)