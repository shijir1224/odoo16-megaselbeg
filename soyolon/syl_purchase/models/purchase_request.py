from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date
from io import BytesIO
import base64
import xlsxwriter

import logging
_logger = logging.getLogger(__name__)

class PurchaseRequest(models.Model):
	_inherit = 'purchase.request'

	pr_department_id = fields.Many2one('hr.department', string='Хүсэлт гаргасан хэлтэс')
	product_quality_research_line = fields.Many2many('product.quality.research', string='Барааны чанарын судалгаа шалгах', readonly=True)
	research_start_date = fields.Date(string='Эхлэх огноо')
	research_end_date = fields.Date(string='Дуусах огноо')
	sub_partner_id = fields.Many2one('res.partner', string='Эцсийн хэрэглэгч')
	visible_state_type = fields.Char(string='State type', compute='_compute_visible_flow_line_ids', store=True)
	is_reviewed = fields.Boolean(string='Хянасан тоо харагдах')
	type = fields.Selection([('sale','Борлуулах'), ('internal','Дотоод ҮА-д ашиглах')], string='Төрөл')

	@api.onchange('visible_state_type')
	def onchange_is_reviewed(self):
		for item in self:
			item.is_reviewed = True if 'reviewed' in item.visible_state_type else False

	@api.depends('flow_id.line_ids', 'flow_id.is_amount', 'amount_total')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				if item.flow_id.is_amount:
					flow_line_ids = []
					flow_state_type = []
					for fl in item.flow_id.line_ids:
						if fl.state_type in ['draft', 'cancel']:
							flow_line_ids.append(fl.id)
							flow_state_type.append(fl.state_type)
						elif fl.amount_price_min == 0 and fl.amount_price_max == 0:
							flow_line_ids.append(fl.id)
							flow_state_type.append(fl.state_type)
						elif fl.amount_price_min <= item.amount_total <= fl.amount_price_max:
							flow_line_ids.append(fl.id)
							flow_state_type.append(fl.state_type)
					item.visible_flow_line_ids = flow_line_ids
					item.visible_state_type = flow_state_type
				else:
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'purchase.request')])
					item.visible_state_type = item.visible_flow_line_ids.mapped('state_type')
			else:
				item.visible_flow_line_ids = []
				item.visible_state_type = []

	def create_product_quality_research(self):
		if not self.research_start_date or not self.research_end_date:
			raise UserError('Эхлэх, дуусах огноо оруулна уу!')
		product_ids = [line.product_id.id for line in self.line_ids]
		product_quality_research_obj = self.env['product.quality.research'].search([('state','=','done'),('date','>=',self.research_start_date),('date','<=',self.research_end_date),('product_id','in',list(set(product_ids)))])
		for item in product_quality_research_obj:
			self.product_quality_research_line += item

	def remove_product_quality_research(self):
		self.product_quality_research_line = False

	def update_available_qty(self):
		quant_obj = self.env['stock.quant']
		for item in self.line_ids:
			if item.request_id.warehouse_id:
				quant_ids = quant_obj.search([('product_id', '=', item.product_id.id),
											  ('location_id.set_warehouse_id', '=', item.request_id.warehouse_id.id),
											  ('location_id.usage', '=', 'internal')])
			else:
				quant_ids = quant_obj.search([('product_id', '=', item.product_id.id), ('location_id.usage', '=', 'internal')])
			item.available_qty = sum(quant_ids.mapped('quantity'))
			item._compute_po_diff_qty()

	def action_next_stage(self):
		res = super(PurchaseRequest, self).action_next_stage()
		zero_request_lines = self.line_ids.filtered(lambda r: r.requested_qty <= 0 and r.product_status != 'product_pr_canceled')
		if zero_request_lines:
			raise UserError('Доорх барааны Хүссэн тоо хэмжээ 0 байна!\n\n%s' %('\n'.join(zero_request_lines.mapped('product_id.display_name'))))
		if self.flow_line_id.state_type == 'reviewed':
			if self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled'):
				self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({'product_status': 'product_pr_reviewed'})
		if self.flow_line_id.state_type == 'agreed':
			zero_reviewed_lines = self.line_ids.filtered(lambda r: r.reviewed_qty == 0 and self.is_reviewed == True and r.product_status != 'product_pr_canceled')
			if zero_reviewed_lines:
				raise UserError('Доорх барааны Хянасан тоо хэмжээ 0 байна!\n\n%s' %('\n'.join(zero_reviewed_lines.mapped('product_id.display_name'))))
			if self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled'):
				self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({'product_status': 'product_pr_approved'})
		if self.flow_line_id.state_type == 'allowed':
			zero_approved_lines = self.line_ids.filtered(lambda r: r.approved_qty == 0 and r.product_status != 'product_pr_canceled')
			if zero_approved_lines:
				raise UserError('Доорх барааны Зөвшөөрсөн тоо хэмжээ 0 байна!\n\n%s' %('\n'.join(zero_approved_lines.mapped('product_id.display_name'))))
			if self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled'):
				self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({'product_status': 'product_pr_approved'})
		if self.flow_line_id.state_type == 'decided':
			zero_decided_lines = self.line_ids.filtered(lambda r: r.qty == 0 and r.product_status != 'product_pr_canceled')
			if zero_decided_lines:
				raise UserError('Доорх барааны Шийдвэрлэсэн тоо хэмжээ 0 байна!\n\n%s' %('\n'.join(zero_decided_lines.mapped('product_id.display_name'))))
			nor_create_selection_lines = self.line_ids.filtered(lambda r: not r.create_selection and r.product_status != 'product_pr_canceled')
			if nor_create_selection_lines:
				raise UserError('Доорх бараан дээр шийдвэрийн төрөл сонгоно уу!\n\n%s' %('\n'.join(nor_create_selection_lines.mapped('product_id.display_name'))))
			if self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled'):
				self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({'product_status': 'product_pr_decided'})
		if self.flow_line_id.state_type == 'done':
			if self.line_ids.filtered(lambda r: not r.is_cancel):
				self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({'product_status': 'product_pr_done'})
		return res

	def action_back_stage(self):
		res = super(PurchaseRequest, self).action_back_stage()
		if self.flow_line_id.state_type == 'draft':
			self.line_ids.write({'product_status': False, 'is_cancel': False, 'cancel_desc': ''})
		if self.flow_line_id.state_type == 'reviewed':
			self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({
				'product_status': 'product_pr_reviewed',
				'reviewed_qty': 0
			})
		if self.flow_line_id.state_type == 'agreed':
			self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({
				'product_status': 'product_pr_approved',
				'approved_qty': 0
			})
		if self.flow_line_id.state_type == 'allowed':
			self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({
				'product_status': 'product_pr_approved',
				'qty': 0,
				'create_selection': False
			})
		if self.flow_line_id.state_type == 'decided':
			self.line_ids.filtered(lambda r: r.product_status != 'product_pr_canceled').write({'product_status': 'product_pr_decided'})
		return res
	
	def action_cancel_stage(self):
		res = super(PurchaseRequest, self).action_cancel_stage()
		if self.line_ids.filtered(lambda r: r.po_line_ids):
			raise UserError('Худалдан авалт үүссэн байна!')
		if self.line_ids.filtered(lambda r: r.comp_line_ids):
			raise UserError('ХА харьцуулалт үүссэн байна!')
		self.line_ids.write({
			'product_status': 'product_pr_canceled',
			'reviewed_qty': 0,
			'approved_qty': 0,
			'qty': 0,
			'create_selection': False
		})
		return res

	def action_draft_stage(self):
		res = super(PurchaseRequest, self).action_draft_stage()
		self.line_ids.write({
			'product_status': False, 
			'is_cancel': False, 
			'cancel_desc': '',
			'reviewed_qty': 0,
			'approved_qty': 0,
			'qty': 0,
			'create_selection': False
		})
		return res

	def action_export_excel(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Худалдан авалтын хүсэлтийн хуудас.xlsx'

		header = workbook.add_format({'bold': 1})
		header.set_font_size(14)
		header.set_font('Times new roman')
		header.set_align('center')
		header.set_align('vcenter')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_left_no_border = workbook.add_format()
		contest_left_no_border.set_text_wrap()
		contest_left_no_border.set_font_size(9)
		contest_left_no_border.set_font('Times new roman')
		contest_left_no_border.set_align('left')
		contest_left_no_border.set_align('vcenter')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		contest_center_bold = workbook.add_format({'bold': 1})
		contest_center_bold.set_text_wrap()
		contest_center_bold.set_font_size(9)
		contest_center_bold.set_font('Times new roman')
		contest_center_bold.set_align('center')
		contest_center_bold.set_align('vcenter')
		contest_center_bold.set_border(style=1)
		contest_center_bold.set_bg_color('#D1D0CE')

		sheet = workbook.add_worksheet(u'Sheet1')
		row = 0
		sheet.merge_range(row, 0, row, 15, u'Худалдан авалтын хүсэлтийн хуудас', header)
		sheet.merge_range(row+1, 0, row+1, 15, u'№ %s' %(self.name), header)

		sheet.merge_range(row+2, 0, row+2, 1, u'Хүсэлт гаргасан ажилтан:', contest_left_no_border)
		sheet.merge_range(row+3, 0, row+3, 1, u'Хүсэлт гаргасан хэлтэс:', contest_left_no_border)
		sheet.merge_range(row+4, 0, row+4, 1, u'Дэд хэлтэс:', contest_left_no_border)
		sheet.merge_range(row+5, 0, row+5, 1, u'Тайлбар:', contest_left_no_border)
		sheet.merge_range(row+6, 0, row+6, 1, u'Хүсэлт гаргасан огноо:', contest_left_no_border)
		sheet.write(row+2, 2, self.partner_id.name, contest_left_no_border)
		sheet.write(row+3, 2, self.pr_department_id.name if self.pr_department_id else '', contest_left_no_border)
		sheet.write(row+4, 2, self.sub_partner_id.name if self.sub_partner_id else '', contest_left_no_border)
		sheet.write(row+5, 2, self.desc if self.desc else '', contest_left_no_border)
		sheet.write(row+6, 2, self.date.strftime("%Y-%m-%d") if self.date else '', contest_left_no_border)

		row += 8
		sheet.set_row(row, 30)
		sheet.write(row, 0, u'№', contest_center_bold)
		sheet.set_column('A:A', 3)
		sheet.write(row, 1, u'Нэр', contest_center_bold)
		sheet.write(row, 2, u'Ангилал', contest_center_bold)
		sheet.write(row, 3, u'Үзүүлэлт', contest_center_bold)
		sheet.write(row, 4, u'Бренд', contest_center_bold)
		sheet.write(row, 5, u'Хэрэгцээт огноо', contest_center_bold)
		sheet.write(row, 6, u'Ашиглах хугацаа', contest_center_bold)
		sheet.write(row, 7, u'Зэрэглэл', contest_center_bold)
		sheet.write(row, 8, u'Зориулалт', contest_center_bold)
		sheet.write(row, 9, u'Тайлбар', contest_center_bold)
		sheet.set_column('B:J', 15)
		sheet.write(row, 10, u'Агуулахын үлдэгдэл', contest_center_bold)
		sheet.write(row, 11, u'Хүссэн тоо', contest_center_bold)
		sheet.write(row, 12, u'Хянасан тоо', contest_center_bold)
		sheet.write(row, 13, u'Зөвшөөрсөн тоо', contest_center_bold)
		sheet.write(row, 14, u'Шийдвэрлэсэн тоо', contest_center_bold)
		sheet.write(row, 15, u'Шийдвэр', contest_center_bold)
		sheet.set_column('K:Q', 10)

		i = 1
		for line in self.line_ids:
			row += 1
			sheet.write(row, 0, u'%s' %(i), contest_center)
			sheet.write(row, 1, line.product_id.name, contest_left)
			sheet.write(row, 2, line.categ_id.name, contest_left)
			sheet.write(row, 3, line.product_specification if line.product_specification else '', contest_left)
			sheet.write(row, 4, line.product_brand_id.name if line.product_brand_id else '', contest_left)
			sheet.write(row, 5, line.date_required.strftime("%Y-%m-%d"), contest_center)
			sheet.write(row, 6, line.date_expected if line.date_expected else '', contest_center)
			sheet.write(row, 7, line.priority_line.name if line.priority_line else '', contest_center)
			sheet.write(row, 8, line.dedication if line.dedication else '', contest_left)
			sheet.write(row, 9, line.desc if line.desc else '', contest_left)
			sheet.write(row, 10, line.available_qty, contest_center)
			sheet.write(row, 11, line.requested_qty, contest_center)
			sheet.write(row, 12, line.reviewed_qty, contest_center)
			sheet.write(row, 13, line.approved_qty, contest_center)
			sheet.write(row, 14, line.qty, contest_center)
			sheet.write(row, 15, line.create_selection.name if line.create_selection else '', contest_center)

		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
			'target': 'new',
		}

	def update_po_date_order(self):
		for item in self.env['purchase.request.line'].search([('po_line_ids','!=',False)]):
			item.po_date_order = item.po_line_ids[0].date_order

class PurchaseRequestLine(models.Model):
	_inherit = 'purchase.request.line'

	type = fields.Selection(related='request_id.type', string='Төрөл', store=True)
	state_type = fields.Selection(related='request_id.state_type', string='Төлөвийн төрөл', store=True)
	categ_id = fields.Many2one('product.category', related='product_id.categ_id', string='Барааны ангилал', store=True, copy=False)
	pr_department_id = fields.Many2one(related='request_id.pr_department_id', string='Хүсэлт гаргасан хэлтэс', copy=False, store=True)
	priority_line = fields.Many2one('purchase.request.priority', string='Зэрэглэл', compute='compute_priority_line', store=True, copy=False)
	create_selection = fields.Many2one('purchase.request.create.selection', string='Шийдвэр', copy=False)
	create_selection_type = fields.Selection(related='create_selection.type')
	product_specification = fields.Char(related='product_id.product_specification', string='Барааны үзүүлэлт', copy=False)
	date_required = fields.Date(string='Хэрэгцээт огноо', readonly=False, store=True, copy=False)
	approved_date = fields.Datetime(related='request_id.approved_date', string=u'Батлагдсан огноо', store=True)
	is_late = fields.Boolean(string='Хоцрогдолтой', compute='_compute_is_late', copy=False, store=True)
	date_expected = fields.Char(string='Ашиглах хугацаа', copy=False)
	default_code = fields.Char(related='product_id.default_code', string='Барааны код', copy=False)
	product_name = fields.Char(related='product_id.name', string='Барааны нэр', copy=False)
	transportation_cost = fields.Float(string='Transportation Cost', readonly=True)
	custom_tax = fields.Float(string='Custom Tax', readonly=True)
	internal_shipping = fields.Float(string='Internal Shipping', readonly=True)
	internal_costing = fields.Float(string='Internal Costing', readonly=True)
	order_price_calc = fields.Float(string='Үнэ тооцолол дүн', readonly=True)
	available_qty = fields.Float('Үлдэгдэл', readonly=True, store=True, copy=False, compute='compute_available_qty')
	requested_qty = fields.Float(string='Хүссэн тоо хэмжээ', copy=False)
	reviewed_qty = fields.Float(string='Хянасан тоо хэмжээ', copy=False)
	approved_qty = fields.Float(string='Зөвшөөрсөн тоо хэмжээ', copy=False)
	qty = fields.Float('Тоо Хэмжээ', default=0, copy=False)
	qty_received = fields.Float('Хүлээж авсан тоо', compute='_compute_qty_received')
	product_brand_id = fields.Many2one(related='product_id.product_brand_id', string='Бренд', copy=False)
	dedication = fields.Char(string='Зориулалт', copy=False)
	is_cancel = fields.Boolean(string='Цуцлагдсан', copy=False)
	cancel_desc = fields.Char(string='Цуцлалтын тайлбар', copy=False)
	real_cancel_desc = fields.Char(string='Цуцлалтын тайлбар', copy=False)
	order_status_id = fields.Many2one('purchase.order.status', string='Order status', compute='_compute_order_status_id')
	is_fulfillment = fields.Boolean(string='Биелэлт')
	fulfillment_date = fields.Date(string='Биелэлтийн огноо')
	po_user_date = fields.Date(string='ХА-ын ажилтанд ирсэн огноо')
	po_date_order = fields.Datetime(string='Эцсийн хэрэглэгчид хүргэх огноо')
	product_status = fields.Selection([
		('product_pr_reviewed','PR хянасан'),
		('product_pr_approved','PR зөвшөөрсөн'),
		('product_pr_decided','PR шийдвэрлэсэн'),
		('product_pr_canceled','PR цуцлагдсан'),
		('product_pr_done','PR ХА хүлээн авсан'),
		('product_set_user','PR ХА ажилтанд оноогдсон'),
		('product_comparison','Судалгаа хийгдэж буй'),
		('product_po_done','PO батлагдсан'),
		('product_waiting_for_payment','Waiting for payment'),
		('product_production','Production'),
		('product_packing','Packing'),
		('product_ready_for_shipment','Ready for shipment'),
		('product_transporting_to_Mongolia','Transporting to Mongolia'),
		('product_arrived','Arrived'),
		('product_uildwer_ereen','Тээвэрлэлт Үйлдвэр-Эрээн'),
		('product_ereen_zamuud','Тээвэрлэлт Эрээн-Замын үүд'),
		('product_ereen_ub','Тээвэрлэлт Эрээн-УБ'),
		('product_zamuud_salhit','Тээвэрлэлт Замын үүд-Салхит'),
		('product_zamuud_ub','Тээвэрлэлт Замын үүд-УБ'),
		('product_ub_salhit','Тээвэрлэлт УБ-Салхит'),
		('production_started','Үйлдвэрлэл эхэлсэн'),
		('production_done','Үйлдвэрлэл дууссан'),
		('product_office_done','Оффис агуулахад хүлээн авсан'),
		('product_not_qty_received','Тоо ширхэг дутуу ирсэн'),
		('product_zut_done','ЗҮТ агуулахад хүлээн авсан'),
		('product_done','Эцсийн хэрэглэгчид хүрсэн')], string='Барааны төлөв', readonly=True, compute='_compute_product_status', store=True)

	@api.depends('po_line_ids', 'comp_line_ids')
	def _compute_order_status_id(self):
		for item in self:
			if item.po_line_ids:
				item.order_status_id = item.po_line_ids.order_status_id
				item.is_fulfillment = item.po_line_ids.order_status_id.is_fulfillment
				item.fulfillment_date = date.today() if item.po_line_ids.order_status_id.is_fulfillment else False
			elif item.comp_line_ids:
				item.order_status_id = item.comp_line_ids.comparison_id.winning_po_id.order_line.filtered(lambda r: r.product_id == item.product_id).order_status_id
				item.is_fulfillment = item.po_line_ids.order_status_id.is_fulfillment
				item.fulfillment_date = date.today() if item.po_line_ids.order_status_id.is_fulfillment else False
			else:
				item.order_status_id = False
				item.is_fulfillment = False
				item.fulfillment_date = False

			if item.order_status_id.type == 'waiting_for_payment':
				item.product_status = 'product_waiting_for_payment'
			if item.order_status_id.type == 'production':
				item.product_status = 'product_production'
			if item.order_status_id.type == 'packing':
				item.product_status = 'product_packing'
			if item.order_status_id.type == 'ready_for_shipment':
				item.product_status = 'product_ready_for_shipment'
			if item.order_status_id.type == 'transporting_to_Mongolia':
				item.product_status = 'product_transporting_to_Mongolia'
			if item.order_status_id.type == 'arrived':
				item.product_status = 'product_arrived'
			if item.order_status_id.type == 'trans_uildwer_ereen':
				item.product_status = 'product_uildwer_ereen'
			if item.order_status_id.type == 'trans_ereen_zamuud':
				item.product_status = 'product_ereen_zamuud'
			if item.order_status_id.type == 'trans_ereen_ub':
				item.product_status = 'product_ereen_ub'
			if item.order_status_id.type == 'trans_zamuud_salhit':
				item.product_status = 'product_zamuud_salhit'
			if item.order_status_id.type == 'trans_zamuud_ub':
				item.product_status = 'product_zamuud_ub'
			if item.order_status_id.type == 'trans_ub_salhit':
				item.product_status = 'product_ub_salhit'
			if item.order_status_id.type == 'production_started':
				item.product_status = 'production_started'
			if item.order_status_id.type == 'production_done':
				item.product_status = 'production_done'
			if item.order_status_id.type == 'office_done':
				item.product_status = 'product_office_done'
			if item.order_status_id.type == 'not_qty_received':
				item.product_status = 'product_not_qty_received'
			if item.order_status_id.type == 'zut_done':
				item.product_status = 'product_zut_done'
			if item.order_status_id.type == 'end_user':
				item.product_status = 'product_done'

	@api.depends('date_required')
	def _compute_is_late(self):
		for item in self:
			if item.date_required:
				if datetime.now().date() > item.date_required:
					item.is_late = True
				else:
					item.is_late = False
			else:
				item.is_late = False

	@api.depends('po_line_ids.qty_received')
	def _compute_qty_received(self):
		for item in self:
			if item.po_line_ids:
				item.qty_received = sum(line.qty_received for line in item.po_line_ids)
			else:
				item.qty_received = 0

	@api.depends('po_line_ids.qty_received', 'po_line_ids.order_id.state', 'qty', 'comp_line_ids.comparison_id.state', 'comp_line_ids.comparison_id.winning_po_id.state')
	def _compute_product_status(self):
		for item in self:
			if item.po_line_ids:
				if item.po_line_ids.filtered(lambda r: r.order_id.state == 'purchase'):
					item.product_status = 'product_po_done'
			if item.comp_line_ids:
				if item.comp_line_ids.filtered(lambda r: r.comparison_id.state != 'ended'):
					item.product_status = 'product_comparison'
				if item.comp_line_ids.filtered(lambda r: r.comparison_id.winning_po_id.state == 'purchase'):
					item.product_status = 'product_po_done'

	@api.depends('date_required', 'approved_date')
	def compute_priority_line(self):
		for item in self:
			priority_obj = item.env['purchase.request.priority']
			if item.date_required and item.approved_date:
				zuruu = (item.date_required - item.approved_date.date()).days
				if zuruu <= 2:
					item.priority_line = priority_obj.search([('type','=','less_than_2')], limit=1).id
				elif zuruu >= 3 and zuruu <= 5:
					item.priority_line = priority_obj.search([('type','=','3_to_5')], limit=1).id
				elif zuruu >= 6:
					item.priority_line = priority_obj.search([('type','=','6_and_above')], limit=1).id
			else:
				item.priority_line = False

	def unlink(self):
		if self.request_id.state_type != 'draft':
				raise UserError(u'Зөвхөн ноорог төлөв дээр устгах боломжтой!')
		return super(PurchaseRequestLine, self).unlink()

	def write(self, values):
		if 'create_selection' in values:
			for line in self:
				if values.get('create_selection' , False):
					change_create_selection = self.env['purchase.request.create.selection'].browse(values.get('create_selection' , False)).name
					if line.request_id.state_type != 'draft' and change_create_selection:
						line.request_id.message_post_with_view('syl_purchase.track_po_line_create_selection_template',
															values={'line': line, 'uurchlugdsun': change_create_selection},
															subtype_id=self.env.ref('mail.mt_note').id)
		if 'real_cancel_desc' in values:
			for line in self:
				if values.get('real_cancel_desc' , False):
					change_cancel_desc = values.get('real_cancel_desc' , False)
				if line.request_id.state_type != 'draft':
					line.request_id.message_post_with_view('syl_purchase.track_pr_line_cancel_desc_template',
														   values={'line': line, 'uurchlugdsun': change_cancel_desc},
														   subtype_id=self.env.ref('mail.mt_note').id)
		if 'product_status' in values:
			for line in self:
				if values.get('product_status' , False) and line.product_status != values.get('product_status' , False):
					product_status = values.get('product_status' , False)
					if line.request_id.state_type != 'draft':
						str_product_status = dict(line._fields['product_status'].selection).get(product_status)
						line.request_id.message_post_with_view('syl_purchase.track_pr_line_product_status_template',
															values={'line': line, 'uurchlugdsun': str_product_status},
															subtype_id=self.env.ref('mail.mt_note').id)
		return super(PurchaseRequestLine, self).write(values)

	@api.depends('product_id', 'request_id.warehouse_id')
	def compute_available_qty(self):
		quant_obj = self.env['stock.quant']
		for item in self:
			if item.request_id.warehouse_id:
				quant_ids = quant_obj.search([('product_id', '=', item.product_id.id),
											  ('location_id.set_warehouse_id', '=', item.request_id.warehouse_id.id),
											  ('location_id.usage', '=', 'internal')])
			else:
				quant_ids = quant_obj.search([('product_id', '=', item.product_id.id), ('location_id.usage', '=', 'internal')])
			item.available_qty = sum(quant_ids.mapped('quantity'))

	@api.onchange('product_id')
	def onchange_product_id(self):
		self.desc = False

	def action_cancel_line(self):
		view_id = self.env.ref('syl_purchase.cancel_line_form')
		return {
			'name': u'Бараа цуцлах',
			'type': 'ir.actions.act_window',
			'res_model': 'purchase.request.line',
			'res_id': self.id,
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': view_id.id,
			'target':'new'
		}

	def action_cancel_product(self):
		if self.po_line_ids:
			raise UserError('Худалдан авалт үүссэн барааг цуцлах боломжгүй!')
		if self.comp_line_ids:
			raise UserError('Харьцуулалт үүссэн барааг цуцлах боломжгүй!')
		self.real_cancel_desc = self.cancel_desc
		self.is_cancel = True
		self.product_status = 'product_pr_canceled'
		if len(self.request_id.line_ids) == len(self.request_id.line_ids.filtered(lambda r: r.is_cancel)):
			cancel_flow_line_id = self.request_id.env['dynamic.flow.line'].search([('flow_id', '=', self.request_id.flow_id.id),('id', '!=', self.request_id.id),('state_type', '=', 'cancel')], limit=1)
			if cancel_flow_line_id:
				self.request_id.flow_line_id = cancel_flow_line_id
				self.env['dynamic.flow.history'].create_history(cancel_flow_line_id, 'request_id', self.request_id)
			else:
				raise UserError('Урсгал тохиргоо буруу байна. Системийн админд хандана уу!')

	# TODO номинтой яриад болиулсан
	# @api.depends('po_line_ids.product_qty', 'qty', 'po_line_ids.state')
	# def _compute_po_diff_qty(self):
	# 	for item in self:
	# 		item.po_qty = sum(item.po_line_ids.filtered(lambda r: r.state != 'cancel').mapped('product_qty'))
	# 		item.comparison_qty = sum(item.comp_line_ids.mapped('product_qty'))
	# 		po_created_qty = 0
	# 		if item.available_qty < item.qty:
	# 			po_created_qty = item.qty - item.available_qty - item.po_qty - item.comparison_qty
	# 		# item.po_diff_qty = po_created_qty if po_created_qty > 0 else 0
	# 		item.po_diff_qty = po_created_qty

class PurchaseRequestPOCreate(models.TransientModel):
	_inherit = 'purchase.request.line.po.create'

	def action_done(self):
		res = super(PurchaseRequestPOCreate, self).action_done()
		obj = self.env['purchase.request.line'].browse(self._context['active_ids'])
		if obj.filtered(lambda r: r.create_selection.type == 'comparison' and not self.is_comparison):
			raise ValidationError(_('Харьцуулсан судалгаатай барааг шууд PO болгох боломжгүй!'))
		if obj.filtered(lambda r: r.create_selection.type == 'refused'):
			raise ValidationError(_('Татгалзсан бараа сонгогдсон байна!'))
		if obj.filtered(lambda r: r.is_cancel):
			raise ValidationError(_('Цуцлагдсан бараа сонгогдсон байна!'))
		return res

class PurchaseRequestLineUserSet(models.TransientModel):
	_inherit = 'purchase.request.line.user.set'

	def action_done(self):
		res = super(PurchaseRequestLineUserSet, self).action_done()
		obj = self.env['purchase.request.line'].browse(self._context['active_ids'])
		if obj.filtered(lambda r: r.create_selection.type == 'refused'):
			raise ValidationError(_('Татгалзсан бараа сонгогдсон байна!'))
		if obj.filtered(lambda r: r.is_cancel):
			raise ValidationError(_('Цуцлагдсан бараа сонгогдсон байна!'))
		for item in obj:
			item.product_status = 'product_set_user'
			item.po_user_date = datetime.now()
		return res

class PurchaseRequestPriority(models.Model):
	_name = 'purchase.request.priority'
	_description = 'Purchase request priority'

	name = fields.Char(string='Нэр', required=True)
	type = fields.Selection([('less_than_2','2 болон түүнээс бага'), ('3_to_5','3-аас 5'), ('6_and_above','6 болон түүнээс дээш')], string='Төрөл')

class PurchaseRequestSubDepartment(models.Model):
	_name = 'purchase.request.sub.departnemt'
	_description = 'Purchase request sub departnemt'

	name = fields.Char(string='Нэр', required=True)

class PurchaseRequestCreateSelection(models.Model):
	_name = 'purchase.request.create.selection'
	_description = 'Purchase request create selection'

	name = fields.Char(string='Нэр', required=True)
	type = fields.Selection([
		('comparison','Харьцуулсан судалгаатай'), 
		('refused','Татгалзсан'), 
		('directly','Шууд')], string='Төрөл', required=True)

class SupplierResearch(models.Model):
	_name = 'supplier.research'
	_description = 'Бэлтгэн нийлүүлэгчийн судалгаа'
	_inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

	partner_id = fields.Many2one('res.partner', string='Нийлүүлэгч')

class ProductQualityResearch(models.Model):
	_name = 'product.quality.research'
	_description = 'Product quality research'
	_inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

	display_name = fields.Char('Дэлгэцийн нэр', compute='compute_display_name')
	state = fields.Selection([('draft','Ноорог'), ('done','Батлагдсан')], string='Төлөв', default='draft', tracking=True)
	product_id = fields.Many2one('product.product', string='Бараа', required=True)
	partner_id = fields.Many2one('res.partner', string='Харилцагч')
	pr_id = fields.Many2one('purchase.request', string='RFP дугаар')
	avail_pr_ids = fields.Many2many('purchase.request', string='Avail RFP дугаар', compute='_compute_avail_pr_ids')
	date = fields.Date(string='Огноо', required=True)
	desc = fields.Char(string='Тайлбар')
	quality = fields.Char(string='Чанар')

	def action_to_draft(self):
		self.write({'state': 'draft'})

	def action_to_done(self):
		self.write({'state': 'done'})

	def unlink(self):
		for item in self:
			if item.state != 'draft':
				raise UserError('Ноорог төлөвтэй биш бол устгах боломжгүй!')
		return super(ProductQualityResearch, self).unlink()

	@api.depends('product_id', 'date')
	def compute_display_name(self):
		for record in self:
			display_name = ''
			if record.product_id and record.date:
				if record.product_id.default_code:
					display_name = '[' + record.product_id.default_code + '] / ' + str(record.date)
				else:
					display_name = '[' + record.product_id.name + '] / ' + str(record.date)
			record.display_name = display_name

	@api.depends('product_id')
	def _compute_avail_pr_ids(self):
		if self.product_id:
			self.avail_pr_ids = self.env['purchase.request.line'].search([('product_id','=',self.product_id.id),('request_id.state_type','=','done')]).mapped('request_id')
		else:
			self.avail_pr_ids = False

class DynamicFlowLine(models.Model):
	_inherit = 'dynamic.flow.line'

	state_type = fields.Selection(selection_add=[
		('reviewed', 'Хянасан'),
		('agreed', 'Зөвшөөрсөн'),
		('allowed', 'Хянаж зөвшөөрсөн'),
		('decided', 'Шийдвэрлэсэн')])