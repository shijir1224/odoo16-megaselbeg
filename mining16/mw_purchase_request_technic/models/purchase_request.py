
# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api
from odoo.exceptions import UserError, Warning

from datetime import datetime
class purchase_request(models.Model):
	_inherit = 'purchase.request'

	@api.depends('line_ids.product_id','line_ids.qty')
	def _compute_wc_messages(self):
		for item in self:
			message = []
			product_ids = item.line_ids.mapped('product_id').ids
			if item.id and product_ids:
				if len(product_ids)>1:
					p_ids = str(tuple(product_ids))
				elif len(product_ids)==1:
					p_ids = "("+str(product_ids[0])+")"

				sql_query = """SELECT prl.product_id,prl.technic_id,pr.date,pr.employee_id,sum(prl.qty) as qty,pr.name
						FROM purchase_request_line prl
						left join purchase_request pr on (pr.id=prl.request_id)
						left join product_product pp on (prl.product_id=pp.id)
						left join product_template pt on (pt.id=pp.product_tmpl_id)
						WHERE prl.product_id in %s and pr.id!=%s and pr.state_type='done' and pr.branch_id=%s
						and pr.company_id=%s and pr.date<='%s' and pt.type!='service'
						group by 1,2,3,4,6
						order by 3 desc
				"""% (p_ids,item.id, item.branch_id.id, item.company_id.id, item.date)
				self.env.cr.execute(sql_query)
				query_result = self.env.cr.dictfetchall()

				for qr in query_result:
					technic_name =''
					if qr['technic_id']:
						technic_name = self.env['technic.equipment'].sudo().browse(qr['technic_id']).display_name
					val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"""%(self.env['product.product'].browse(qr['product_id']).display_name,technic_name,qr['date'],self.env['hr.employee'].browse(qr['employee_id']).display_name,qr['qty'],qr['name'])
					message.append(val)

			if message==[]:
				message = False
			else:
				message = u'<table style="width: 100%;"><tr><td colspan="4" style="text-align: center;">ӨМНӨ ЗАХИАЛГА ХИЙСЭН</td></tr><tr style="width: 40%;"><td>Бараа</td><td>Техник</td><td style="width: 15%;">Огноо</td><td style="width: 20%;">Ажилтан</td><td style="width: 10%;">Тоо Хэмжээ</td><td style="width: 15%;">Дугаар</td></tr>'+u''.join(message)+u'</table>'
			item.warning_messages = message

	def action_next_stage(self):
		user_id = self.env['res.users'].search([('partner_id','=',self.partner_id.id)])
		# if not user_id:
		# 	raise UserError(u'%s ажилтан дээр хэрэглэгч алга байна.' % self.partner_id.name)
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = next_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					temp_stage = check_next_flow_line_id._get_next_flow_line()
					if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
						break
					check_next_flow_line_id = temp_stage
				next_flow_line_id = check_next_flow_line_id
			if next_flow_line_id._get_check_ok_flow(self.branch_id, False, self.create_uid):
				self.flow_line_id = next_flow_line_id
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'request_id', self)
				self.send_chat_employee(self.sudo().partner_id)
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id, False, self.create_uid)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
				if self.flow_line_id.state_type == 'sent':
					if self.flow_id.is_technic == True:
						no_technic_lines = self.line_ids.filtered(lambda r: not r.technic_id)
						if no_technic_lines:
							raise Warning('"%s" урсгал тохиргоо нь дээр техник сонгох шаардлагатай. \nДоорх бараанууд дээр техник сонго!\n\n%s'%(self.flow_id.name, ', '.join(no_technic_lines.mapped('product_id.display_name'))))
				if self.flow_line_id.state_type != 'done':
					self.update_available_qty()
					# self.product_warning()
				if self.flow_line_id.state_type == 'done':
					self.approved_date = datetime.now()
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id, False, self.create_uid)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

class purchase_request_line(models.Model):
	_inherit = 'purchase.request.line'

	technic_id = fields.Many2one('technic.equipment','Техник')

	# def get_po_line(self):
	#     if self.technic_id:
	#         return self.po_line_ids.filtered(lambda r: r.technic_id==self.technic_id)
	#     return self.po_line_ids

class purchase_request_line_po_create(models.TransientModel):
	_inherit = 'purchase.request.line.po.create'

	def get_pr_po_line(self, product_id, re_lines, date, po_id, uom_id):
		with_technic = re_lines.filtered(lambda r: r.technic_id)
		technic_ids = with_technic.mapped('technic_id')
		not_with_technic = re_lines.filtered(lambda r: not r.technic_id)
		po_line_vals = []
		if not_with_technic:
			po_line_vals.append({
				'product_id': product_id.id,
				'name': '%s'%(', '.join(set(not_with_technic.mapped('name')))),
				'date_planned': date,
				'product_qty': sum(not_with_technic.mapped('po_qty')) if self.is_po_qty_edit else sum(not_with_technic.mapped('qty')),
				'price_unit': 1,
				'product_uom': uom_id.id,
				'order_id': po_id.id,
				'pr_line_many_ids': [(6,0,not_with_technic.ids)],
			})
		for item in technic_ids:
			pr_ls = with_technic.filtered(lambda r: r.technic_id==item)
			print ('----', pr_ls)
			po_line_vals.append({
				'product_id': product_id.id,
				'name': '%s'%(', '.join(set(pr_ls.mapped('name')))),
				'date_planned': date,
				'product_qty': sum(pr_ls.mapped('po_qty')) if self.is_po_qty_edit else sum(pr_ls.mapped('qty')),
				'price_unit': 1,
				'product_uom': uom_id.id,
				'order_id': po_id.id,
				'pr_line_many_ids': [(6,0,pr_ls.ids)],
			})
		return  po_line_vals

class purchase_order_line(models.Model):
	_inherit = 'purchase.order.line'

	technic_id = fields.Many2one('technic.equipment', 'Техник')

	def _create_stock_moves(self, picking):
		res = super(purchase_order_line, self)._create_stock_moves(picking)

		for stock in res:
			if stock.purchase_line_id.technic_id:
				stock.technic_id2 = stock.purchase_line_id.technic_id.id

		return res

# class purchase_request_line_po_create(models.TransientModel):
# 	_inherit = 'purchase.request.line.po.create'

# 	def action_done(self):
# 		res = super(purchase_request_line_po_create, self).action_done()
# 		for item in res:
# 			if item.technic_id:
# 				item.po_line_ids.write({'technic_id': item.technic_id.id })
# 				# .technic_id =
# 				# item.purchase_order_line_id.technic_id = item.technic_id.id

# 				if item.internal_stock_move_id:
# 					item.internal_stock_move_id.technic_id2 = item.technic_id.id

class PurchaseRequestLinePOCreateline(models.TransientModel):
	_inherit = 'purchase.request.line.po.create.line'

	pr_line_id = fields.Many2one('purchase.request.line', string='Request line')

	def get_pr_po_line(self, po_id):
		res = super(PurchaseRequestLinePOCreateline, self).get_pr_po_line(po_id)
		res['technic_id'] = self.pr_line_id.technic_id.id if self.pr_line_id.technic_id else False
		return res

class PrReport(models.Model):
	_inherit = "pr.report"

	technic_id = fields.Many2one('technic.equipment','Техник', readonly=True)

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE OR REPLACE VIEW %s AS (
				SELECT
					product_id,
					product_id_pr,
					product_id_po,
					product_id_st,
					default_code,
					product_code,
					categ_id,
					id,
					pr_line_id,
					request_id,
					po_id,

					stage_id,
					flow_line_id,
					state_type,
					stage_id_po,
					state_type_po,
					branch_id,
					date,
					warehouse_id,
					employee_id,
					department_id,
					description,
					name,
					po_user_id,
					po_date,
					po_date_in,
					stock_date,
					partner_id,
					picking_id,
					warehouse_id_po,
					po_date_count,
					qty as qty,
					qty_po as qty_po,
					qty_received as qty_received,
					qty_invoiced as qty_invoiced,
					price_unit_po as price_unit_po,
					price_total as price_total,
					0 as actual_percent,
					technic_id

				FROM
				(SELECT
					prl.id,
					prl.id as pr_line_id,
					prl.product_id,
					pp.default_code,
					pt.product_code,
					pt.categ_id,
					pr.flow_line_id,
					pr.stage_id,
					pr.state_type,
					pr.branch_id,
					pr.date,
					pr.warehouse_id,
					pr.employee_id,
					pr.department_id,
					pr.desc as description,
					pr.name,
					pr.id as request_id,
					po.id as po_id,
					po.user_id as po_user_id,
					po.date_planned as po_date,
					po.date_planned as po_date_in,
					po.partner_id as partner_id,
					spt.warehouse_id as warehouse_id_po,
					po.stage_id as stage_id_po,
					po.state_type as state_type_po,
					prl.product_id as product_id_pr,
					null::int as product_id_po,
					null::int as product_id_st,
					prl.technic_id,
					max(sm.picking_id) as picking_id,
					max(sm.date) as stock_date,
					max(prl.qty) as qty,
					0 as qty_received,
					0 as qty_po,
					0 as qty_invoiced,
					0 as price_unit_po,
					0 as price_total,
					0 as po_date_count
				FROM purchase_request_line AS prl
					LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.pr_line_id=prl.id)
					LEFT JOIN purchase_order_line AS pol on (pol.id=po_pr_rel.po_line_id)
					LEFT JOIN product_product pp on (pp.id=prl.product_id)
					LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)
					LEFT JOIN purchase_order AS po on (po.id=pol.order_id)
					LEFT JOIN stock_picking_type spt on (po.picking_type_id=spt.id)
					LEFT JOIN purchase_request AS pr on (pr.id=prl.request_id)
				   left join stock_move as sm on (pol.id=sm.purchase_line_id)

				where pr.state_type!='cancel'
				group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27
				UNION ALL
				SELECT
					pol.id*-1 as id,
					prl.id as pr_line_id,
					pol.product_id,
					pp.default_code,
					pt.product_code,
					pt.categ_id,
					pr.flow_line_id,
					pr.stage_id,
					pr.state_type,
					pr.branch_id,
					pr.date,

					pr.warehouse_id,
					pr.employee_id,
					pr.department_id,
					pr.desc as description,
					pr.name,
					prl.request_id as request_id,

					po.id as po_id,
					po.user_id as po_user_id,
					po.date_planned as po_date,
					po.date_planned as po_date_in,
					po.partner_id,
					spt.warehouse_id as warehouse_id_po,
					po.stage_id as stage_id_po,
					po.state_type as state_type_po,
					null::int as product_id_pr,
					pol.product_id as product_id_po,
					null::int as product_id_st,
					prl.technic_id,
					0 as picking_id,
					null::timestamp as stock_date,
					0 as qty,
					pol.qty_received,
					pol.product_qty as qty_po,
					pol.qty_invoiced,
					pol.price_unit as price_unit_po,
					pol.price_total as price_total,
			CASE WHEN po.date_planned is not null and pr.date  is not null and po.date_planned>pr.date THEN po.date_planned::DATE-  pr.date::DATE ELSE 0 END as po_date_count
				FROM purchase_order_line as pol
				LEFT JOIN purchase_order AS po on (po.id=pol.order_id)
					LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.po_line_id=pol.id)
					LEFT JOIN purchase_request_line AS prl on (prl.id=po_pr_rel.pr_line_id)
					LEFT JOIN product_product pp on (pp.id=pol.product_id)
					LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)

					LEFT JOIN stock_picking_type spt on (po.picking_type_id=spt.id)
					LEFT JOIN purchase_request AS pr on (pr.id=prl.request_id)
		where po.state!='cancel'
				UNION ALL
				SELECT
					sm.id*-100 as id,
					prl.id as pr_line_id,
					sm.product_id,

					pp.default_code,
					pt.product_code,
					pt.categ_id,
					pr.flow_line_id,
					pr.stage_id,
					pr.state_type,
					pr.branch_id,
					pr.date,

					pr.warehouse_id,
					pr.employee_id,
					pr.department_id,
					pr.desc as description,
					pr.name,
					prl.request_id as request_id,

					po.id as po_id,
					po.user_id as po_user_id,
					po.date_planned as po_date,
					po.date_planned as po_date_in,
					po.partner_id,
					spt.warehouse_id as warehouse_id_po,
					po.stage_id as stage_id_po,
					po.state_type as state_type_po,
					null::int as product_id_pr,
					null::int as product_id_po,
					sm.product_id as product_id_st,
					prl.technic_id,

					sm.picking_id as picking_id,
					sm.date as stock_date,
					0 as qty,
					0 as qty_received,
					0 as qty_po,
					0 as qty_invoiced,
					0 as price_unit_po,
					0 as price_total,
					0 as po_date_count
				FROM stock_move AS sm
					LEFT JOIN purchase_order_line AS pol on (pol.id=sm.purchase_line_id)
					LEFT JOIN purchase_order AS po on (po.id=pol.order_id)
					LEFT JOIN purchase_order_line_purchase_request_line_rel AS po_pr_rel on (po_pr_rel.po_line_id=pol.id)
					LEFT JOIN stock_picking_type spt on (po.picking_type_id=spt.id)
					LEFT JOIN purchase_request_line AS prl on (prl.id=po_pr_rel.pr_line_id)
					LEFT JOIN purchase_request AS pr on (pr.id=prl.request_id)
					LEFT JOIN product_product pp on (pp.id=sm.product_id)
					LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)

				where sm.state='done' and sm.purchase_line_id is not null


) as temp_pr_report

			)
		""" % (self._table)
		)


class PrReportExcel(models.TransientModel):
	_inherit = 'pr.report.excel'

	def get_tech_name(self, pr_line_id):

		if pr_line_id and pr_line_id.technic_id:
			return pr_line_id.technic_id.program_code or pr_line_id.technic_id.park_number
		return super(PrReportExcel, self).get_tech_name(pr_line_id)

# Тениктэй холбоотой худалдан авалтын хүсэлтийг харуулах
class TechnicEquipmentInherit(models.Model):
	_inherit = 'technic.equipment'

	pr_request_line = fields.One2many('purchase.request.line', 'technic_id',
		string='Худалдан авалтийн мөр', readonly=True,
		domain=['|',('po_line_ids.qty_received','=',0),('po_line_ids','=',False)]
		)

	pr_request_line_po = fields.One2many('purchase.request.line', 'technic_id',
		string='Худалдан авалтийн мөр', readonly=True,
		domain=[('po_line_ids.qty_received','>',0)]
		)