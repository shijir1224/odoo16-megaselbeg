# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

# INHERIT PLAN
class SalePlanPivotReport(models.Model):
	_inherit = "sale.plan.pivot.report"

	brand_id = fields.Many2one('product.brand',string=u'Brand', readonly=True )

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
			SELECT  
				spl.id as id,
				sp.id as plan_id,
				sp.year::int as year,
				sp.plan_type as plan_type,
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
				sp.state as state,
				-- INHERTI ---
				pt.brand_id as brand_id
			FROM sales_master_plan_line as spl
			LEFT JOIN sales_master_plan as sp on (sp.id = spl.parent_id)
			LEFT JOIN product_product as pp on (pp.id = spl.product_id)
			LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
			WHERE sp.state in ('confirmed','done','company')
		)""" % self._table)

class SalePivotReport(models.Model):
	_inherit = "sale.pivot.report"

	picking_date = fields.Date(u'Хүргэх огноо', readonly=True, )

	brand_id = fields.Many2one('product.brand',string=u'Brand', readonly=True )
	barcode = fields.Char(string=u'BARCODE', readonly=True,  )
	default_code = fields.Char(string=u'Дотоод код', readonly=True)
	tin_type = fields.Selection([
		('person', 'Person'),
		('company', 'Company'),
		('none', 'None')], 
		string=u'Tin type', readonly=True, )

	with_e_tax = fields.Boolean(string=u'НӨАТ авах эсэх', readonly=True)
	ebarimt_type = fields.Selection([
		('none','None'),
		('person','Person'),
		('company','Company')], string='Ebarimt type', )
	ebarimt_state = fields.Selection([
		('draft','Draft'),
		('sent','Sent'), 
		('return','Returned')],
		'E-баримт төлөв', default='draft', copy=False)

	amount_free_product = fields.Float(u'Урамшуулал бараа дүн', readonly=True, digits=(16,1), )
	main_amount_delivered = fields.Float(u'Хүргэгдсэн үндсэн дүн', readonly=True, digits=(16,1), )
	
	discount_coupon_amount = fields.Float(string=u'Урамшуулалын хөнгөлөлт', readonly=True, default=0, digits=(16,2) )
	discount_contract_amount_sales = fields.Float(string=u'Гэрээний хөнгөлөлт/борлуулалт бүр/', readonly=True, default=0, digits=(16,2) )
	discount_contract_amount_payment = fields.Float(string=u'Гэрээний хөнгөлөлт/төлөлт бүр/', readonly=True, default=0, digits=(16,2) )
	discount_contract_month_amount = fields.Float(string=u'Төлөвлөгөөт хөнгөлөлтийн дүн', readonly=True, default=0, digits=(16,2) )
	discount_total = fields.Float(u'Нийт хөнгөлөлт', readonly=True, digits=(16,1), )
	
	discount_percent_coupon = fields.Float(string=u'Discount promotion %', readonly=True, default=0, digits=(16,2),copy=False )
	discount_percent_contract = fields.Float(string=u'Discount %', readonly=True, default=0, digits=(16,2),copy=False )
	discount_percent_contract_month = fields.Float(string=u'Discount month %', readonly=True, default=0, digits=(16,2),copy=False )

	is_gift_sale = fields.Boolean(string=u'Gift, Эрхийн бичгээр', default=False,)
	is_reward_product = fields.Selection([
			('yes', u'Урамшууллын бараа'), 
			('no', u'Борлуулсан бараа'),
		], readonly=True, string=u'Урамшууллын бараа эсэх')

	supplier_partner_id = fields.Many2one('res.partner',string=u'Нийлүүлэгч', readonly=True )

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
				sol.main_amount as main_amount,
				(CASE WHEN sol.main_price_unit != 0 THEN sol.main_price_unit * sol.qty_delivered ELSE sol.price_unit * sol.qty_delivered END) as main_amount_delivered,
				(sol.qty_invoiced) * sol.price_unit as amount_invoiced,
				(sol.product_uom_qty) * sol.price_unit as amount_order,

				so.user_id as user_id,
				so.team_id as crm_team_id,
				sol.invoice_status as invoice_status,
				so.state as state,
				sol.return_reason as return_reason,
				so.id as so_id,
				so.company_id as company_id,
				-- НЭМЭЛТ --
				so.picking_date as picking_date,
				pt.brand_id as brand_id,
				pp.barcode as barcode,
				rp.tin_type as tin_type,
				so.with_e_tax as with_e_tax,
				so.ebarimt_type as ebarimt_type,
				so.ebarimt_state as ebarimt_state,
				(CASE WHEN sol.is_reward_product = 't' THEN sol.qty_delivered*sol.main_price_unit ELSE 0 END) as amount_free_product,
				sol.discount_coupon_amount as discount_coupon_amount,
				sol.discount_contract_amount_sales as discount_contract_amount_sales,
				sol.discount_contract_amount_payment as discount_contract_amount_payment,
				sol.discount_contract_month_amount as discount_contract_month_amount,
				sol.total_discount as discount_total,
				sol.discount_percent_coupon as discount_percent_coupon,
				sol.discount_percent_contract as discount_percent_contract,
				sol.discount_percent_contract_month as discount_percent_contract_month,
				so.is_gift_sale as is_gift_sale,
				(CASE WHEN sol.is_reward_product = 't' THEN 'yes' ELSE 'no' END) as is_reward_product,
				pp.default_code as default_code,
				pt.supplier_partner_id as supplier_partner_id

			FROM sale_order_line as sol
			LEFT JOIN sale_order as so on (so.id = sol.order_id)
			LEFT JOIN res_partner as rp on (rp.id = so.partner_id)
			LEFT JOIN product_product as pp on (pp.id = sol.product_id)
			LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
			LEFT JOIN crm_team as crm on (crm.id = so.team_id)
			WHERE so.state in ('sale','done')
		"""

# # Захиалсан тоог хүргэсэн тоотой харьцуулах тайлан
# class SaleOrderDeliveredQtysTemp(models.TransientModel):
# 	_name = "sale.order.delivered.qty.temp"

# 	report_id = fields.Integer(u'Report ID', readonly=True, default=0)

# 	picking_id = fields.Many2one('stock.picking', string=u'Агуулахын баримт', readonly=True )
# 	partner_id = fields.Many2one('res.partner', string=u'Харилцагч', readonly=True )
# 	so_id = fields.Many2one('sale.order', string=u'Sale order', readonly=True,  )
# 	warehouse_id = fields.Many2one('stock.warehouse', string=u'Агуулах', readonly=True, )
# 	order_date = fields.Date(u'Баталсан огноо', readonly=True, index=True)
# 	validity_date = fields.Date(u'Захиалсан огноо', readonly=True, index=True)
# 	picking_date = fields.Date(u'Хүргэх огноо', readonly=True, index=True)
	
# 	product_id = fields.Many2one('product.product', string=u'Бараа', readonly=True,)
# 	categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True, )
# 	brand_id = fields.Many2one('product.brand', u'Бренд', readonly=True, )

# 	qty_ordered = fields.Float(u'Захиалсан тоо', readonly=True, digits=(16,1), )
# 	qty_delivered = fields.Float(u'Хүргэгдсэн тоо', readonly=True, digits=(16,1), )

# 	user_id = fields.Many2one('res.users', u'Борлуулагч', readonly=True, )
# 	crm_team_id = fields.Many2one('crm.team', string=u'Суваг', readonly=True, )

# class SaleOrderDeliveredQtysReport(models.Model):
# 	_name = "sale.order.delivered.qty.report"
# 	_auto = False
# 	_order = 'so_id, partner_id, product_id'

# 	report_id = fields.Integer(u'Report ID', readonly=True, default=0)

# 	picking_id = fields.Many2one('stock.picking', string=u'Агуулахын баримт', readonly=True )
# 	partner_id = fields.Many2one('res.partner', string=u'Харилцагч', readonly=True )
# 	so_id = fields.Many2one('sale.order', string=u'Sale order', readonly=True,  )
# 	warehouse_id = fields.Many2one('stock.warehouse', string=u'Агуулах', readonly=True, )
# 	order_date = fields.Date(u'Баталсан огноо', readonly=True, index=True)
# 	validity_date = fields.Date(u'Захиалсан огноо', readonly=True, index=True)
# 	picking_date = fields.Date(u'Хүргэх огноо', readonly=True, index=True)
	
# 	product_id = fields.Many2one('product.product', string=u'Бараа', readonly=True,)
# 	categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True, )
# 	brand_id = fields.Many2one('product.brand', u'Бренд', readonly=True, )

# 	qty_ordered = fields.Float(u'Захиалсан тоо', readonly=True, digits=(16,1), )
# 	qty_delivered = fields.Float(u'Хүргэгдсэн тоо', readonly=True, digits=(16,1), )

# 	user_id = fields.Many2one('res.users', u'Борлуулагч', readonly=True, )
# 	crm_team_id = fields.Many2one('crm.team', string=u'Суваг', readonly=True, )

# 	def init(self):
# 		tools.drop_view_if_exists(self.env.cr, self._table)
# 		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
# 			SELECT  
# 				ll.id as id,
# 				ll.report_id as report_id,
# 				ll.picking_id as picking_id,

# 				ll.so_id as so_id,
# 				ll.order_date as order_date,
# 				ll.validity_date as validity_date,
# 				ll.picking_date as picking_date,

# 				ll.partner_id as partner_id,
# 				ll.product_id as product_id,
# 				ll.categ_id as categ_id,
# 				ll.brand_id as brand_id,

# 				ll.qty_ordered as qty_ordered,
# 				ll.qty_delivered as qty_delivered,

# 				ll.warehouse_id as warehouse_id,
# 				ll.crm_team_id as crm_team_id,
# 				ll.user_id as user_id
# 			FROM sale_order_delivered_qty_temp as ll
# 		)""" % self._table)