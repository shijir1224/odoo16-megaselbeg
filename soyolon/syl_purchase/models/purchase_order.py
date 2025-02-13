from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.http import request
import json

import logging
_logger = logging.getLogger(__name__)

class PurchaseOrderComparison(models.Model):
	_inherit = 'purchase.order.comparison'

	done_date = fields.Date(string='Дууссан огноо')
	product_ids = fields.Many2many('product.product', string='Бараа', compute='compute_product_ids', store=True)
	state = fields.Selection(selection_add=[('cancelled', 'Цуцлагдсан')])
	# request_department_id = fields.Many2many('hr.department', string='Хүсэлт гаргасан хүсэлт', compute='_compute_request_department_id', store=True)

	# @api.depends('line_ids')
	# def _compute_request_department_id(self):
	# 	for item in self:
	# 		print('--------------', item.line_ids)
	# 		item.request_department_id = item.line_ids.mapped('request_line_ids.request_id.pr_department_id').ids

	@api.depends('line_ids')
	def compute_product_ids(self):
		for item in self:
			item.product_ids = item.line_ids.mapped('product_id').ids

	def action_next_stage(self):
		res = super(PurchaseOrderComparison, self).action_next_stage()
		if self.flow_line_id.state_type == 'ended':
			self.done_date = datetime.now()
		return res

	def end_vote(self):
		self.ensure_one()
		self.write({'state': 'vote_ended'})
		duplicates = []
		unique_elements = set()
		for result in self.vote_result_ids:
			if result.vote_points in unique_elements:
				duplicates.append(result.vote_points)
			else:
				unique_elements.add(result.vote_points)
		if len(duplicates) == 0:
			max_point = max(self.vote_result_ids.mapped('vote_points'))
			self.winning_partner = self.vote_result_ids.filtered(lambda r: r.vote_points == max_point).partner_id

	def end_comparison(self):
		"""
		:return: OVERRIDED METHOD
		"""
		self.ensure_one()
		winning_order = self.related_po_ids.filtered(lambda l: l.partner_id == self.winning_partner)
		losing_orders = self.related_po_ids - winning_order
		try:
			for obj in losing_orders:
				obj.action_cancel_stage()
		except Exception as e:
			_logger.info(self, 'losing_orders', losing_orders, e)
		winning_order.button_draft()
		# winning_order.action_next_stage()
		winning_order.flow_line_id = self.env['dynamic.flow.line'].search([('flow_id','=',winning_order.flow_id.id),('state_type','=','sent')], limit=1).id
		winning_order.state_type = 'sent'
		self.write({'state': 'ended', 'winning_po_id': winning_order.id})

	@api.depends('flow_line_id', 'flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			flow_line_id = item.flow_line_id
			ooo = flow_line_id._get_flow_users(False, False)
			temp_users = ooo.ids if ooo else []
			item.confirm_user_ids = [(6, 0, temp_users)]
			item.confirm_count = len(item.sudo().confirm_user_ids)

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if not flow_line_id:
			raise UserError('Урсгал тохиргоо буруу байна. Системийн админд хандана уу!')
		if flow_line_id._get_check_ok_flow(False, False):
			self.check_comparison_cancel()
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'comparison_id', self)
			self.state = 'cancelled'
		else:
			cancel_user = flow_line_id._get_flow_users(False, False)
			raise UserError(_('Цуцлах хэрэглэгч биш байна!\nЦуцлах хэрэглэгчид: %s' %', '.join(cancel_user.mapped('display_name'))))

	def check_comparison_cancel(self):
		if self.related_po_ids:
			self.related_po_ids.update({'state': 'cancel'})
			self.related_po_ids.with_context(from_comparison=True).unlink()

class PurchaseOrderStatus(models.Model):
	_name = 'purchase.order.status'
	_description = 'Purchase order status'

	name = fields.Char(string='Нэр', required=True)
	type = fields.Selection([
		('waiting_for_payment','Waiting for payment'),
		('production','Production'),
		('packing','Packing'),
		('ready_for_shipment','Ready for shipment'),
		('transporting_to_Mongolia','Transporting to Mongolia'),
		('arrived','Arrived'),
		('trans_uildwer_ereen','Тээвэрлэлт Үйлдвэр-Эрээн'),
		('trans_ereen_zamuud','Тээвэрлэлт Эрээн-Замын үүд'),
		('trans_ereen_ub','Тээвэрлэлт Эрээн-УБ'),
		('trans_zamuud_salhit','Тээвэрлэлт Замын үүд-Салхит'),
		('trans_zamuud_ub','Тээвэрлэлт Замын үүд-УБ'),
		('trans_ub_salhit','Тээвэрлэлт УБ-Салхит'),
		('production_started','Үйлдвэрлэл эхэлсэн'),
		('production_done','Үйлдвэрлэл дууссан'),
		('office_done','Оффис агуулахад хүлээн авсан'),
		('not_qty_received','Тоо ширхэг дутуу ирсэн'),
		('zut_done','ЗҮТ агуулахад хүлээн авсан'),
		('end_user','Эцсийн хэрэглэгчид хүрсэн'),
		('returned','Буцаалт хийгдсэн')
		], string='Төрөл', required=True)
	is_fulfillment = fields.Boolean(string='Биелэлт тооцох')

class PurchaseInitialInvoiceLine(models.Model):
	_inherit = 'purchase.initial.invoice.line'

	pre_percent = fields.Float(string='Дүн (хувиар)')
	amount = fields.Float(string='Валютаарх дүн')

	@api.onchange('pre_percent', 'order_id.amount_total')
	def onchange_amount(self):
		for item in self:
			item.amount = round(item.order_id.amount_total * item.pre_percent / 100, 2)

	def get_payment_request_vals(self):
		if self.amount > self.order_id.possible_invoice_amount_currency:
			raise UserError('Төлбөр хүсэх дүн их байх боломжгүй.')
		return {
			'flow_id': self.env['dynamic.flow'].search([('model_id.model', '=', 'payment.request')], order='sequence', limit=1).id,
			'amount': self.amount,
			'currency_id': self.currency_id.id,
			'partner_id': self.order_id.partner_id.id,
			'purchase_ids': [(4, self.order_id.id)],
			'purchase_initial_invoice_line': self.id,
			'payment_ref': self.order_id.name + ' ' + self.name
		}

	def button_create_payment_request(self):
		self.check_initial_invoice_line()
		payment_request_id = self.env['payment.request'].create(self.get_payment_request_vals())
		self.env['payment.request.desc.line'].create(self.get_payment_request_line_vals(payment_request_id))
		self.write({'payment_request_id': payment_request_id.id,
					'payment_state': 'created'})
		payment_request_id.write({'currency_id': self.currency_id.id,
								'current_rate': self.currency_rate,
								'date_currency': self.date})

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	order_status_id = fields.Many2one('purchase.order.status', string='Order status', tracking=True)
	country_origin = fields.Char(string='Гарал үүсэл')
	merge_po = fields.Char(string='Нэгтгэсэн ХА', readonly=True)
	merge_comparison = fields.Char(string='Нэгтгэсэн ХА-ын харьцуулалт', readonly=True)
	user_emp_id = fields.Many2one('hr.employee', string='Холбоотой ажилтан', compute='_compute_user_emp_id', store=True)
	supplier_desc = fields.Char(string='Нийлүүлэгч хүлээн авсан тайлбар')
	supplier_attach_ids = fields.Many2many('ir.attachment', string='Хавсралт')
	total_discount = fields.Float(string='Нийт хөнгөлөлт', compute='compute_total_discount')
	real_name = fields.Char(string='Жииинкэн нэр', compute='compute_real_name', store=True)
	file_type = fields.Selection([('pdf','PDF'), ('excel','Excel')], default='pdf', string='Хавсралтын төрөл', required=True)
	lang_type = fields.Selection([('english','Англи'), ('mongolian','Монгол')], default='mongolian', string='Хэлний сонголт', required=True)
	partner_mail = fields.Char(string='Бүртгэлгүй мэйл', readonly=False)
	mail_title = fields.Char(string='Гарчиг')
	mail_html = fields.Html(string='Мэйл загвар')
	payment_term_id = fields.Many2one('account.payment.term', string='Төлбөрийн нөхцөл', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", store=True)
	deliver_day = fields.Integer(string='Нийлүүлэх хугацаа')
	delivered_day = fields.Integer(string='Нийлүүлсэн хугацаа')
	delivered_date = fields.Date(string='Нийлүүлэгч хүлээн авсан огноо')
	quality_qty = fields.Integer(string='Чанартай ирсэн тоо хэмжээ')
	sum_mnt_total_price = fields.Float(string='Нийт дүн/төгрөгөөр/', compute='_compute_sum_mnt_total_price', store=True)

	@api.depends('order_line.price_unit_product')
	def _compute_sum_mnt_total_price(self):
		for item in self:
			if item.order_line:
				item.sum_mnt_total_price = sum([line.price_unit_product * line.product_uom_qty for line in item.order_line])
			else:
				item.sum_mnt_total_price = 0

	def write(self, vals):
		if vals.get('order_status_id', False):
			if self.user_id.id != self.env.uid:
				if not self.env.user.has_group('syl_purchase.group_order_status_edit_user'):
					raise UserError("Order status өөрчлөх эрхгүй байна!")
		res = super(PurchaseOrder, self).write(vals)
		return res

	# override
	@api.onchange('partner_id', 'company_id')
	def onchange_partner_id(self):
		return

	@api.depends('name')
	def compute_real_name(self):
		for item in self:
			item.real_name = item.name

	@api.depends('order_line.discount')
	def compute_total_discount(self):
		for item in self:
			item.total_discount = sum(item.order_line.mapped('discount'))

	@api.depends('user_id')
	def _compute_user_emp_id(self):
		for item in self:
			item.user_emp_id = item.env['hr.employee'].search([('user_id','=',item.user_id.id)], limit=1).id if item.user_id else False

	def set_order_status(self):
		if not self.order_status_id:
			raise UserError("Order status сонгоно уу!")
		for line in self.order_line:
			line.order_status_id = self.order_status_id

	def action_next_stage(self):
		res = super(PurchaseOrder, self).action_next_stage()
		if self.flow_line_id.state_type == 'done':
			for line in self.order_line:
				if line.pr_line_many_ids:
					line.pr_line_many_ids.update({'po_date_order': self.date_order})
			self.picking_ids.write({'eh_barimt_user_id': self.create_uid.id})
		return res

	def expense_per_line(self, line):
		portion_methods = list(set(self.expenses_line.mapped('portion_method')))
		sum_for_line = 0
		product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
		for method in portion_methods:
			method_lines = self.expenses_line.filtered(lambda r: not r.is_without_cost and r.portion_method == method and (not r.purchase_lines or line.id in r.purchase_lines.ids))
			for expense_line in method_lines:
				current_amount = expense_line.current_amount
				lines = expense_line.purchase_lines if expense_line.purchase_lines else self.order_line
				if method == 'price':
					sum_for_line += current_amount * line.price_unit / sum(lines.mapped('price_unit'))
				elif method == 'subtotal':
					sum_for_line += (current_amount / self.get_total_amount_currency(lines)) * self.get_total_amount_currency(line)
				elif method == 'volume':
					for po_line in lines:
						if po_line.volume <= 0:
							raise UserError("Эзлэхүүн 0-ээс их байх ёстой!")
					total_volume = sum([(line.volume or 1) * line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id) for line in lines])
					line_res = ((current_amount / total_volume) * ((line.volume or 1) * product_uom_qty)) / product_uom_qty
					sum_for_line += line_res * product_uom_qty
				elif method == 'weight':  # weight
					for po_line in lines:
						if po_line.subtotal_weight <= 0:
							raise UserError("Жин 0-ээс их байх ёстой!")
					tot_w = sum(lines.mapped('subtotal_weight'))
					tot_w_amount = current_amount * line.subtotal_weight / tot_w if tot_w else 1
					sum_for_line += tot_w_amount
				elif method == 'qty':
					sum_for_line += expense_line.current_amount * line.product_uom_qty / sum(lines.mapped('product_uom_qty'))
		line.cost_unit = sum_for_line / product_uom_qty

	@api.depends('flow_id.line_ids', 'flow_id.is_amount', 'amount_total')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				if item.flow_id.is_amount:
					flow_line_ids = []
					for fl in item.flow_id.line_ids:
						if fl.state_type in ['draft', 'cancel']:
							flow_line_ids.append(fl.id)
						elif fl.amount_price_min == 0 and fl.amount_price_max == 0:
							flow_line_ids.append(fl.id)
						elif fl.amount_price_min <= item.amount_total <= fl.amount_price_max:
							flow_line_ids.append(fl.id)
					item.visible_flow_line_ids = flow_line_ids
				else:
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search(
						[('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'purchase.order'), ('state_type', '!=', 'supplier_received')])
			else:
				item.visible_flow_line_ids = []

	def action_supplier_received_view(self):
		view_id = self.env.ref('syl_purchase.purchase_order_supplier_received_form')
		return {
			'name': u'Нийлүүлэгч PO хүлээж авсан',
			'type': 'ir.actions.act_window',
			'res_model': 'purchase.order',
			'res_id': self.id,
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': view_id.id,
			'target':'new'
		}

	def action_supplier_received_stage(self):
		supplier_received_flow_line_id = self.env['dynamic.flow.line'].search([
			('flow_id', '=', self.flow_id.id),
			('id', '!=', self.id),
			('state_type', '=', 'supplier_received'),
		], limit=1)
		self.flow_line_id = supplier_received_flow_line_id
		self.env['dynamic.flow.history'].create_history(supplier_received_flow_line_id, 'po_id', self)
		self.supplier_desc = self.supplier_desc
		self.supplier_attach_ids = self.supplier_attach_ids
		self.delivered_date = datetime.now().date()

	def action_partner_send_mail(self):
		view_id = self.env.ref('syl_purchase.purchase_order_partner_mail_form_view')
		return {
			'name': u'Нийлүүлэгч рүү мэйл илгээх',
			'type': 'ir.actions.act_window',
			'res_model': 'purchase.order',
			'res_id': self.id,
			'view_mode': 'form',
			'view_type': 'form',
			'view_id': view_id.id,
			'target':'new'
		}

	def action_to_sent_mail(self):
		if self.file_type == 'pdf':
			reportname = 'purchase.purchase_order_mn' if self.lang_type == 'mongolian' else 'purchase.purchase_order_en'
			report = request.env['ir.actions.report']._get_report_from_name(reportname)
			context = dict(request.env.context)
			data = self.env.context
			docids = self.id
			if report.populating_ms_word_template:
				if data.get('options'):
					data.update(json.loads(data.pop('options')))
				if data.get('context'):
					data['context'] = json.loads(data['context'])
					if data['context'].get('lang'):
						del data['context']['lang']
					context.update(data['context'])
				datas = request.env[report.model].search([('id', '=', docids)])
				if report.type_export == 'pdf':
					pdf = report.with_context(context).render_doc_doc(datas, data=data)[0]
					pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]

					attachment_id = self.env['ir.attachment'].search([('res_id','=',docids),('res_model','=',report.model)], limit=1)
					if not self.partner_mail:
						# self.env.user.send_chat(self.mail_html, [self.partner_id], with_mail=True, subject_mail=self.mail_title, attachment_ids=[attachment_id.id])
						self.send_emails(subject=self.mail_title, body=self.mail_html, attachment_ids=[attachment_id.id], is_partner_mail=False)
					else:
						self.send_emails(subject=self.mail_title, body=self.mail_html, attachment_ids=[attachment_id.id], is_partner_mail=True)

					return request.make_response(pdf, headers=pdfhttpheaders)

	def send_emails(self, subject, body, attachment_ids, is_partner_mail):
		mail_obj = self.env['mail.mail'].sudo().create({
			'email_from': self.company_id.email,
			'email_to': self.partner_mail if is_partner_mail else self.partner_id.email,
			'reply_to': self.env.user.email_formatted,
			'subject': subject,
			'body_html': '%s' % body,
			'attachment_ids': attachment_ids
		})
		mail_obj.send()

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	order_status_id = fields.Many2one('purchase.order.status', string='Order status')
	is_fulfillment = fields.Boolean(related='order_status_id.is_fulfillment', string='Биелэлт тооцох', store=True)
	po_type = fields.Selection(related='order_id.po_type', string='Төрөл', store=True)
	volume = fields.Float(string='Эзлэхүүн')
	lead_time = fields.Char(string='Leadtime')
	warranty_period = fields.Char(string='Баталгаат хугацаа')
	partner_spec = fields.Char(string='Нийлүүлэгчийн үзүүлэлт')
	product_specification = fields.Char(related='product_id.product_specification', string='Барааны үзүүлэлт')
	desc = fields.Char(string='Тайлбар')
	price_total_stock_move = fields.Float(string='Нийт өртөг', compute='_compute_price_total_stock_move')

	def _compute_tax_id(self):
		for line in self:
			# line.taxes_id = line.order_id.taxes_id
			line = line.with_company(line.company_id)
			fpos = line.order_id.fiscal_position_id or line.order_id.fiscal_position_id._get_fiscal_position(line.order_id.partner_id)
			taxes = line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == line.env.company)
			line.taxes_id = fpos.map_tax(taxes)

	def write(self, vals):
		if vals.get('order_status_id', False):
			if self.order_id.user_id.id != self.env.uid:
				raise UserError("Зөвхөн хариуцсан ХА ажилтан Order status өөрчлөх боломжтой!")
		res = super(PurchaseOrderLine, self).write(vals)
		return res
	
	@api.onchange('discount', 'price_unit_without_discount')
	def onchange_discount_price_unit(self):
		self.price_unit = self.price_unit_without_discount - self.discount

	@api.depends('price_unit_stock_move', 'product_uom_qty')
	def _compute_price_total_stock_move(self):
		for item in self:
			item.price_total_stock_move = item.price_unit_stock_move * item.product_uom_qty

class PurchaseAddCost(models.Model):
	_inherit = 'purchase.add.cost'

	def expense_per_line(self, line):
		portion_methods = list(set(self.expenses_line.mapped('portion_method')))
		sum_for_line = 0
		product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
		for method in portion_methods:
			method_lines = self.expenses_line.filtered(lambda r: not r.is_without_cost and r.portion_method == method and (not r.purchase_lines or line.id in r.purchase_lines.ids))
			for expense_line in method_lines:
				current_amount = expense_line.current_amount
				lines = expense_line.purchase_lines if expense_line.purchase_lines else self.po_line_ids
				if method == 'price':
					sum_for_line += current_amount * line.price_unit / sum(lines.mapped('price_unit'))
				elif method == 'subtotal':
					sum_for_line += (current_amount / self.get_total_amount_currency(lines)) * self.get_total_amount_currency(line)
				elif method == 'volume':
					for po_line in lines:
						if po_line.volume <= 0:
							raise UserError("Хуваарилах арга эзлэхүүн үед эзлэхүүн заавал 0-ээс их байх ёстой!")
					total_volume = sum([(line.volume or 1) * line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id) for line in lines])
					line_res = ((current_amount / total_volume) * ((line.volume or 1) * product_uom_qty)) / product_uom_qty
					sum_for_line += line_res * product_uom_qty
				elif method == 'weight':
					for po_line in lines:
						if po_line.subtotal_weight <= 0:
							raise UserError("Хуваарилах арга жин үед жин заавал 0-ээс их байх ёстой!")
					tot_w = sum(lines.mapped('subtotal_weight'))
					tot_w_amount = current_amount * line.subtotal_weight / tot_w if tot_w else 1
					sum_for_line += tot_w_amount
				elif method == 'qty':
					sum_for_line += expense_line.current_amount * line.product_uom_qty / sum(lines.mapped('product_uom_qty'))
		line.cost_unit = sum_for_line / product_uom_qty

	def action_done(self):
		res = super(PurchaseAddCost, self).action_done()
		if not self.expenses_line.mapped('invoice_id'):
			raise UserError("Зардлын нэхэмжлэх үүсээгүй байна!")
		return res

class SelectedPoMerge(models.TransientModel):
	_name = "selected.po.merge"
	_description = "Чеклэсэн PO нэгтгэх"

	def get_domain_orders(self):
		order_ids = self.env['purchase.order'].search([('id', 'in', self.env.context.get('active_ids'))])
		return [('id', 'in', order_ids.ids)]

	merge_order_id = fields.Many2one('purchase.order', string='Нэгтгэх худалдан авалт', domain=get_domain_orders)

	def action_merge_po(self):
		if not self.merge_order_id:
			raise UserError("Нэгтгэх худалдан авалтын дугаар сонгоно уу!")
		po_ids = self.env['purchase.order'].search([('id','in',self._context['active_ids'])])
		if len(set(po_ids.partner_id)) == 1:
			inactive_po_ids = po_ids.filtered(lambda r: r.id != self.merge_order_id.id)
			for po_id in inactive_po_ids:
				for line in po_id.order_line:
					copy_line = line.with_context(from_comparison=True).copy()
					self.merge_order_id.order_line = [(4, copy_line.id)]
				cancel_line_id = po_id.flow_id.line_ids.filtered(lambda r: r.state_type == 'cancel')
				po_id.write({'flow_line_id': cancel_line_id.id, 'state': 'cancel'})

			if not self.merge_order_id.merge_comparison:
				self.merge_order_id.merge_comparison = ''
			if not self.merge_order_id.merge_po:
				self.merge_order_id.merge_po = ''
			self.merge_order_id.merge_comparison += ', '.join(inactive_po_ids.mapped('comparison_id.name'))
			self.merge_order_id.merge_po += ', '.join(inactive_po_ids.mapped('name'))
		else:
			raise UserError("Сонгосон ХА-уудын харилцагч ялгаатай байна! \nХарилцагч ижил байх ёстой!")

class DynamicFlowLine(models.Model):
	_inherit = 'dynamic.flow.line'

	state_type = fields.Selection(selection_add=[('supplier_received', 'Нийлүүлэгч хүлээн авсан')])

class AccountIncoterms(models.Model):
	_inherit = 'account.incoterms'

	def name_get(self):
		res = []
		for item in self:
			if item.code:
				name = item.code
			res.append((item.id, name))
		return res