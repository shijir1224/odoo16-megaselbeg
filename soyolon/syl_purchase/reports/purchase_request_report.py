from odoo import api, fields, models, tools

class SoyolonPrReport(models.Model):
	_name = 'soyolon.pr.report'
	_auto = False
	_description = "Soyolon purchase request report"

	request_id = fields.Many2one('purchase.request', string='Хүсэлтийн дугаар')
	date = fields.Date(string='Хүсэлт гаргасан огноо')
	approved_date = fields.Date(string='Батлагдсан огноо')
	product_id = fields.Many2one('product.product', string='Бараа')
	branch_id = fields.Many2one('res.branch', string='Байршил')
	department_id = fields.Many2one('hr.department', string='Хэлтэс')
	pr_department_id = fields.Many2one('hr.department', string='Хүсэлт гаргасан хэлтэс')
	pr_qty = fields.Float(string='Хүсэлтийн тоо хэмжээ')
	requested_qty = fields.Float(string='Барааны тоо хэмжээ')
	product_qty = fields.Float(string='Барааны нэр төрлийн тоо хэмжээ')
	priority_line = fields.Many2one('purchase.request.priority', string='Зэрэглэл')
	create_selection = fields.Many2one('purchase.request.create.selection', string='Шийдвэрийн төрөл')
	fulfillment = fields.Float(string='Биелэлт')
	is_fulfillment = fields.Boolean(string='Биелэлт')
	stage_id = fields.Many2one('dynamic.flow.line.stage', string='Төлөв')

	def _select(self):
		return """
			SELECT
				(prl.id::text||prl.company_id::text)::bigint as id,
				prl.product_id as product_id,
				pr.id as request_id,
				pr.date as date,
				pr.approved_date as approved_date,
				pr.branch_id as branch_id,
				pr.department_id as department_id,
				pr.pr_department_id as pr_department_id,
				(select distinct(count(pr.id)) purchase_request_line where request_id = pr.id) as pr_qty,
				(select distinct(count(product_id)) purchase_request_line where request_id = pr.id) as product_qty,
				CASE
					WHEN prl.is_fulfillment = True THEN 1 
					ELSE 0
				END as fulfillment,
				prl.requested_qty as requested_qty,
				prl.priority_line as priority_line,
				prl.create_selection as create_selection,
				prl.is_fulfillment as is_fulfillment,
				pr.stage_id as stage_id
		"""

	def _from(self):
		return """
			FROM purchase_request_line AS prl 
				LEFT JOIN purchase_request AS pr ON (pr.id = prl.request_id)
		"""

	# def _where(self):
	# 	return """
	# 		WHERE
	# 			sml.is_qualified = 'no'
	# 	"""

	def _groupby(self):
		return """
			GROUP BY
				prl.id,
				pr.id
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
				CREATE OR REPLACE VIEW %s AS (%s %s %s)
			""" % (self._table, self._select(), self._from(), self._groupby())
		)

class PrReport(models.Model):
	_inherit = "pr.report"

	qty = fields.Float('Мөрний тоо хэмжээ', readonly=True)
	po_user_date = fields.Date(string='ХА-ын ажилтанд ирсэн огноо')
	uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж')

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
					pol.price_total as price_total,
					prl.po_user_date as po_user_date,
					pt.uom_id as uom_id
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
				GROUP BY 1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,24,26,27,28,29,30,32
			)
		""" % (self._table)
		)