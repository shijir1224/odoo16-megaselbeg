# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools

class PrReport(models.Model):
	_name = "pr.report"
	_auto = False
	_description = "Purchase requist report"

	# PR info
	request_id = fields.Many2one('purchase.request', 'PR дугаар', readonly=True)
	date = fields.Date('Хүсэлтийн огноо', readonly=True)
	branch_id = fields.Many2one('res.branch', 'Салбар', readonly=True)
	department_id = fields.Many2one('hr.department', 'Хэлтэс', readonly=True)
	warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', readonly=True)
	pr_partner_id = fields.Many2one('res.partner', 'Хүсэлт гаргасан ажилтан', readonly=True)
	description = fields.Char('PR тайлбар', readonly=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', string='PR төлөв', readonly=True)
	state_type = fields.Char(string='Төлөвийн төрөл', readonly=True)
	product_id = fields.Many2one('product.product', 'Бараа', readonly=True)
	categ_id = fields.Many2one('product.category', 'Барааны ангилал', readonly=True)
	qty = fields.Float('PR тоо хэмжээ', readonly=True)
	pr_line_id = fields.Many2one('purchase.request.line', 'Хүсэлтийн мөр', readonly=True)

	# PO info
	po_id = fields.Many2one('purchase.order', 'PO дугаар', readonly=True)
	# product_id_po = fields.Many2one('product.product', 'Бараа PO', readonly=True)
	po_user_id = fields.Many2one('res.users', 'ХА ажилтан', readonly=True)
	po_date = fields.Datetime('PO огноо', readonly=True)
	partner_id = fields.Many2one('res.partner', 'Нийлүүлэгч', readonly=True)
	qty_po = fields.Float('PO тоо хэмжээ', readonly=True)
	qty_received = fields.Float('PO хүлээж авсан тоо', readonly=True)
	qty_invoiced = fields.Float('PO нэхэмжилсэн тоо', readonly=True)
	price_unit_po = fields.Float('PO нэгж үнэ', readonly=True, group_operator="avg")
	price_total = fields.Float('Худалдан авалт Нийт үнэ', readonly=True)
	warehouse_id_po = fields.Many2one('stock.warehouse', 'Худалдан авалт хийсэн агуулах', readonly=True)
	stage_id_po = fields.Many2one('dynamic.flow.line.stage', string='PO төлөв', readonly=True)
	state_type_po = fields.Char(string='PO төлөвийн төрөл', readonly=True)
	currency_id = fields.Many2one('res.currency', string='Валют', readonly=True)

	# Stock info
	picking_id = fields.Many2one('stock.picking', 'Хүлээн авсан баримт', readonly=True)
	stock_date = fields.Datetime('Агуулахын орлогодсон огноо', readonly=True)
	
	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE OR REPLACE VIEW %s AS (
				SELECT
					prl.id as id,
					prl.product_id as product_id,
					--null::int as product_id_po,
					pt.categ_id as categ_id,
					prl.id as pr_line_id,
					pr.id as request_id,
					po.id as po_id,
					pr.stage_id as stage_id,
					pr.flow_line_id as flow_line_id,
					pr.state_type as state_type,
					po.stage_id as stage_id_po,
					po.state_type as state_type_po,
					pr.branch_id as branch_id,
					pr.date as date,
					pr.warehouse_id as warehouse_id,
					pr.partner_id as pr_partner_id,
					pr.department_id as department_id,
					pr.desc as description,
					po.user_id as po_user_id,
					po.currency_id as currency_id,
					po.date_order as po_date,
					max(sm.date) as stock_date,
					po.partner_id as partner_id,
					max(sm.picking_id) as picking_id,
					spt.warehouse_id as warehouse_id_po,
					prl.qty as qty,
					pol.product_qty as qty_po,
					pol.qty_received as qty_received,
					pol.qty_invoiced as qty_invoiced,
					pol.price_unit as price_unit_po,
					pol.price_total as price_total
				FROM purchase_request_line AS prl
					LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.pr_line_id = prl.id)
					LEFT JOIN purchase_order_line AS pol on (pol.id = po_pr_rel.po_line_id)
					LEFT JOIN product_product pp on (pp.id = prl.product_id)
					LEFT JOIN product_template pt on (pt.id = pp.product_tmpl_id)
					LEFT JOIN purchase_order AS po on (po.id = pol.order_id)
					LEFT JOIN stock_picking_type spt on (po.picking_type_id = spt.id)
					LEFT JOIN purchase_request AS pr on (pr.id = prl.request_id)
					LEFT JOIN stock_move as sm on (pol.id = sm.purchase_line_id)
				WHERE pr.state_type != 'cancel'
				GROUP BY 1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,24,26,27,28,29,30
			)
		""" % (self._table)
		)

# TODO
# SELECT 
# 					id,
# 					product_id,
# 					--product_id_po,
# 					categ_id,
# 					pr_line_id,
# 					request_id,
# 					po_id,
# 					stage_id,
# 					flow_line_id,
# 					state_type,
# 					stage_id_po,
# 					state_type_po,
# 					branch_id,
# 					date,
# 					warehouse_id,
# 					pr_partner_id,
# 					department_id,
# 					description,
# 					po_user_id,
# 					currency_id,
# 					po_date,
# 					stock_date,
# 					partner_id,
# 					picking_id,
# 					warehouse_id_po,
# 					qty as qty,
# 					qty_po as qty_po,
# 					qty_received as qty_received,
# 					qty_invoiced as qty_invoiced,
# 					price_unit_po as price_unit_po,
# 					price_total as price_total
# 				FROM 
# 				(SELECT
# 					prl.id as id,
# 					prl.product_id as product_id,
# 					--null::int as product_id_po,
# 					pt.categ_id as categ_id,
# 					prl.id as pr_line_id,
# 					pr.id as request_id,
# 					po.id as po_id,
# 					pr.stage_id as stage_id,
# 					pr.flow_line_id as flow_line_id,
# 					pr.state_type as state_type,
# 					po.stage_id as stage_id_po,
# 					po.state_type as state_type_po,
# 					pr.branch_id as branch_id,
# 					pr.date as date,
# 					pr.warehouse_id as warehouse_id,
# 					pr.partner_id as pr_partner_id,
# 					pr.department_id as department_id,
# 					pr.desc as description,
# 					po.user_id as po_user_id,
# 					po.currency_id as currency_id,
# 					po.date_order as po_date,
# 					max(sm.date) as stock_date,
# 					po.partner_id as partner_id,
# 					max(sm.picking_id) as picking_id,
# 					spt.warehouse_id as warehouse_id_po,
# 					prl.qty as qty,
# 					0 as qty_po,
# 					0 as qty_received,
# 					0 as qty_invoiced,
# 					0 as price_unit_po,
# 					0 as price_total
# 				FROM purchase_request_line AS prl
# 					LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.pr_line_id = prl.id)
# 					LEFT JOIN purchase_order_line AS pol on (pol.id = po_pr_rel.po_line_id)
# 					LEFT JOIN product_product pp on (pp.id = prl.product_id)
# 					LEFT JOIN product_template pt on (pt.id = pp.product_tmpl_id)
# 					LEFT JOIN purchase_order AS po on (po.id = pol.order_id)
# 					LEFT JOIN stock_picking_type spt on (po.picking_type_id = spt.id)
# 					LEFT JOIN purchase_request AS pr on (pr.id = prl.request_id)
# 				   left join stock_move as sm on (pol.id = sm.purchase_line_id)
# 				WHERE pr.state_type != 'cancel'
# 				GROUP BY 1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,24,26,27,28,29,30
# UNION ALL
# 				SELECT
# 					pol.id*-1 as id,
# 					pol.product_id as product_id,
# 					--pol.product_id as product_id_po,
# 					pt.categ_id as categ_id,
# 					prl.id as pr_line_id,
# 					prl.request_id as request_id,
# 					po.id as po_id,
# 					pr.stage_id as stage_id,
# 					pr.flow_line_id as flow_line_id,
# 					pr.state_type as state_type,
# 					po.stage_id as stage_id_po,
# 					po.state_type as state_type_po,
# 					pr.branch_id as branch_id,
# 					pr.date as date,
# 					pr.warehouse_id as warehouse_id,
# 					pr.partner_id as pr_partner_id,
# 					pr.department_id as department_id,
# 					pr.desc as description,
# 					po.user_id as po_user_id,
# 					po.currency_id as currency_id,
# 					po.date_order as po_date,
# 					null::timestamp as stock_date,
# 					po.partner_id as partner_id,
# 					0 as picking_id,
# 					spt.warehouse_id as warehouse_id_po,
# 					0 as qty,
# 					pol.product_qty as qty_po,
# 					pol.qty_received as qty_received,
# 					pol.qty_invoiced as qty_invoiced,
# 					pol.price_unit as price_unit_po,
# 					pol.price_total as price_total
# 				FROM purchase_order_line as pol
# 				LEFT JOIN purchase_order AS po on (po.id = pol.order_id)
# 				LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.po_line_id = pol.id)
# 				LEFT JOIN purchase_request_line AS prl on (prl.id = po_pr_rel.pr_line_id)
# 				LEFT JOIN product_product pp on (pp.id = pol.product_id)
# 				LEFT JOIN product_template pt on (pt.id = pp.product_tmpl_id)
# 				LEFT JOIN stock_picking_type spt on (po.picking_type_id = spt.id)
# 				LEFT JOIN purchase_request AS pr on (pr.id = prl.request_id)
# 				WHERE po.state != 'cancel'
# 				GROUP BY 1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,24,26,27,28,29,30
# UNION ALL
# 				SELECT
# 					sm.id*-100 as id,
# 					sm.product_id as product_id,
# 					--null::int as product_id_po,
# 					pt.categ_id as categ_id,
# 					prl.id as pr_line_id,
# 					prl.request_id as request_id,
# 					po.id as po_id,
# 					pr.stage_id as stage_id,
# 					pr.flow_line_id as flow_line_id,
# 					pr.state_type as state_type,
# 					po.stage_id as stage_id_po,
# 					po.state_type as state_type_po,
# 					pr.branch_id as branch_id,
# 					pr.date as date,
# 					pr.warehouse_id as warehouse_id,
# 					pr.partner_id as pr_partner_id,
# 					pr.department_id as department_id,
# 					pr.desc as description,
# 					po.user_id as po_user_id,
# 					po.currency_id as currency_id,
# 					po.date_order as po_date,
# 					sm.date as stock_date,
# 					po.partner_id as partner_id,
# 					sm.picking_id as picking_id,
# 					spt.warehouse_id as warehouse_id_po,
# 					0 as qty,
# 					0 as qty_po,
# 					0 as qty_received,
# 					0 as qty_invoiced,
# 					0 as price_unit_po,
# 					0 as price_total
# 				FROM stock_move AS sm
# 				LEFT JOIN purchase_order_line AS pol on (pol.id = sm.purchase_line_id)
# 				LEFT JOIN purchase_order AS po on (po.id = pol.order_id)
# 				LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.po_line_id = pol.id)
# 				LEFT JOIN stock_picking_type spt on (po.picking_type_id = spt.id)
# 				LEFT JOIN purchase_request_line AS prl on (prl.id = po_pr_rel.pr_line_id)
# 				LEFT JOIN purchase_request AS pr on (pr.id = prl.request_id)
# 				LEFT JOIN product_product pp on (pp.id = sm.product_id)
# 				LEFT JOIN product_template pt on (pt.id = pp.product_tmpl_id)
# 				WHERE sm.state='done' and sm.purchase_line_id is not null
# ) as temp_pr_report 