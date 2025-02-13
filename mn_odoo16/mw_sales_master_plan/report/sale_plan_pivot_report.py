# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class SalePlanPivotReport(models.Model):
	_name = "sale.plan.pivot.report"
	_description = "Sale pivot report"
	_auto = False
	_order = 'product_id'

	plan_id = fields.Many2one('sales.master.plan', string='Plan', readonly=True,)
	partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, index=True )
	branch_id = fields.Many2one('res.branch', string=u'Салбар', readonly=True, index=True )
	warehouse_id = fields.Many2one('stock.warehouse', u'Агуулах', readonly=True, )
	crm_team_id = fields.Many2one('crm.team', string=u'Team', readonly=True, )
	salesman_id = fields.Many2one('res.users', string=u'Salesman', readonly=True, )

	plan_type = fields.Selection([
		('branch', u'By Branch'),
		('partner', u'By Partner'),
		('company', u'Компаны нийт'),
		], string=u'Plan type', copy=True, default='branch', required=True,)

	year = fields.Char(string=u'Year', readonly=True, )
	month = fields.Selection([
			('1', u'January'), 
			('2', u'February'), 
			('3', u'March'), 
			('4', u'April'), 
			('5', u'May'), 
			('6', u'June'), 
			('7', u'July'), 
			('8', u'August'), 
			('9', u'September'), 
			('10', u'October'), 
			('11', u'November'), 
			('12', u'December'), 
		], string=u'Month', readonly=True, )

	state = fields.Selection([
			('confirmed', 'Confirmed'),
			('done', 'Done'),
			('company', 'Компани')
		], readonly=True, string='State',)


	product_id = fields.Many2one('product.product', string=u'Product', readonly=True, index=True )
	categ_id = fields.Many2one('product.category', 'Categoty', readonly=True, )
	price_unit = fields.Float(u'Price unit', readonly=True, digits=(16,1), group_operator='avg')
	barcode_name = fields.Char(string=u'Баркод / Нэр',)
	
	qty = fields.Float(u'Plan qty', readonly=True, digits=(16,1), )
	amount = fields.Float(u'Amount', readonly=True, digits=(16,1), )

	package = fields.Float(string=u'Хайрцаг', readonly=True, )
	package_fixed = fields.Float(string=u'Хайрцаг.Тод', readonly=True, )

	qty_fixed = fields.Float(u'Qty fixed', readonly=True, digits=(16,1), )
	amount_fixed = fields.Float(u'Amount fixed', readonly=True, digits=(16,1), )

	def _select(self):
		return """
			SELECT  
				spl.id as id,
				sp.id as plan_id,
				sp.plan_type as plan_type,
				sp.year::int as year,
				sp.month::int as month,
				sp.partner_id as partner_id,
				sp.branch_id as branch_id,
				sp.warehouse_id as warehouse_id,
				sp.crm_team_id as crm_team_id,
				sp.salesman_id as salesman_id,
				spl.categ_id as categ_id,
				pp.barcode||' / '||pt.name as barcode_name,
				spl.product_id as product_id,
				spl.price_unit as price_unit,
				spl.qty as qty,
				spl.qty_fixed as qty_fixed,
				spl.package as package,
				spl.package_fixed as package_fixed,
				spl.amount as amount,
				spl.amount_fixed as amount_fixed,
				sp.state as state
			FROM sales_master_plan_line as spl
			LEFT JOIN sales_master_plan as sp on (sp.id = spl.parent_id)
			LEFT JOIN product_product as pp on (pp.id = spl.product_id)
			LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
			WHERE sp.state in ('confirmed','done','company')
		"""

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			%s 
			)""" % (self._table, self._select())
		)

# Борлуулалтын төлөвлөгөө гүйцэтгэлийн пивот
class SalePlanPerformanceTempPivot(models.TransientModel):
	_name = "sale.plan.performance.temp.pivot"
	_description = "sale plan performance temp pivot"

	report_id = fields.Integer(u'Report', readonly=True, )
	plan_id = fields.Many2one('sales.master.plan', string='Plan', readonly=True,)
	partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, index=True )
	branch_id = fields.Many2one('res.branch', string=u'Салбар', readonly=True, index=True )
	crm_team_id = fields.Many2one('crm.team', string=u'Team', readonly=True, )
	salesman_id = fields.Many2one('res.users', string=u'Salesman', readonly=True, )
	
	year = fields.Char(string=u'Year', readonly=True, )
	month = fields.Selection([
			('1', u'January'), 
			('2', u'February'), 
			('3', u'March'), 
			('4', u'April'), 
			('5', u'May'), 
			('6', u'June'), 
			('7', u'July'), 
			('8', u'August'), 
			('9', u'September'), 
			('10', u'October'), 
			('11', u'November'), 
			('12', u'December'), 
		], string=u'Month', readonly=True, )

	product_id = fields.Many2one('product.product', string=u'Product', readonly=True, index=True )
	categ_id = fields.Many2one('product.category', 'Categoty', readonly=True, )
	
	plan_price_unit = fields.Float(u'Plan Price unit', readonly=True, digits=(16,1), group_operator='avg')
	price_unit = fields.Float(u'Price unit', readonly=True, digits=(16,1), group_operator='avg')

	plan_qty = fields.Float(u'Plan Quantity', readonly=True, digits=(16,1), )
	plan_amount = fields.Float(u'Plan Amount', readonly=True, digits=(16,1), )

	qty = fields.Float(u'Sale Quantity', readonly=True, digits=(16,1), )
	amount = fields.Float(u'Sale Amount', readonly=True, digits=(16,1), )

	percent_qty = fields.Float(u'Quantity %', readonly=True, digits=(16,1), )
	percent = fields.Float(u'Amount %', readonly=True, digits=(16,1), )

class SalePlanPerformancePivotReport(models.Model):
	_name = "sale.plan.performance.pivot.report"
	_description = "Sale plan, performance pivot report"
	_auto = False
	_order = 'product_id'

	report_id = fields.Integer(u'Report', readonly=True, )
	plan_id = fields.Many2one('sales.master.plan', string='Plan', readonly=True,)
	partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, index=True )
	branch_id = fields.Many2one('res.branch', string=u'Салбар', readonly=True, index=True )
	crm_team_id = fields.Many2one('crm.team', string=u'Team', readonly=True, )
	salesman_id = fields.Many2one('res.users', string=u'Salesman', readonly=True, )

	year = fields.Char(string=u'Year', readonly=True, )
	month = fields.Selection([
			('1', u'January'), 
			('2', u'February'), 
			('3', u'March'), 
			('4', u'April'), 
			('5', u'May'), 
			('6', u'June'), 
			('7', u'July'), 
			('8', u'August'), 
			('9', u'September'), 
			('10', u'October'), 
			('11', u'November'), 
			('12', u'December'), 
		], string=u'Month', readonly=True, )

	product_id = fields.Many2one('product.product', string=u'Product', readonly=True, index=True )
	categ_id = fields.Many2one('product.category', 'Categoty', readonly=True, )

	plan_price_unit = fields.Float(u'Plan Price unit', readonly=True, digits=(16,1), group_operator='avg')
	price_unit = fields.Float(u'Price unit', readonly=True, digits=(16,1), group_operator='avg')
	
	plan_qty = fields.Float(u'Plan Quantity', readonly=True, digits=(16,1), )
	plan_amount = fields.Float(u'Plan Amount', readonly=True, digits=(16,1), )

	qty = fields.Float(u'Sale Quantity', readonly=True, digits=(16,1), )
	amount = fields.Float(u'Sale Amount', readonly=True, digits=(16,1), )

	percent_qty = fields.Float(u'Quantity %', readonly=True, digits=(16,1), )
	percent = fields.Float(u'Amount %', readonly=True, digits=(16,1), )

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT  
				ll.id as id,
				ll.report_id as report_id,
				ll.id as plan_id,
				ll.year::int as year,
				ll.month::int as month,
				ll.partner_id as partner_id,
				ll.branch_id as branch_id,
				ll.crm_team_id as crm_team_id,
				ll.salesman_id as salesman_id,
				ll.categ_id as categ_id,
				ll.product_id as product_id,
				ll.plan_price_unit as plan_price_unit,
				ll.price_unit as price_unit,
				ll.plan_qty as plan_qty,
				ll.plan_amount as plan_amount,
				ll.qty as qty,
				ll.amount as amount,
				ll.percent_qty as percent_qty,
				ll.percent as percent
			FROM sale_plan_performance_temp_pivot as ll
		)""" % self._table)
