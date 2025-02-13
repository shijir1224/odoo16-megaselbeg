# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	request_id = fields.Many2one('purchase.request', 'Purchase request', ondelete='cascade', index=True)

class PurchaseRequest(models.Model):
	_name = 'purchase.request'
	_description = 'Purchase request'
	_inherit = ['mail.thread','mail.activity.mixin']
	_order = 'name desc'

	@api.model
	def create(self, val):
		res = super(PurchaseRequest, self).create(val)
		for item in res:
			if item.flow_id:
				search_domain = [('flow_id', '=', item.flow_id.id)]
				re_flow = self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
				item.flow_line_id = re_flow
		return res

	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = [('model_id.model', '=', 'purchase.request')]
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	name = fields.Char('Дугаар', readonly=True, copy=False)
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id)
	branch_id = fields.Many2one('res.branch', 'Салбар', default=lambda self: self.env.user.branch_id)
	date = fields.Date('Хэрэгцээт огноо', required=True, default=fields.Date.context_today)
	approved_date = fields.Datetime(string=u'Батлагдсан огноо')
	employee_id = fields.Many2one('hr.employee', 'Ажилтан')
	partner_id = fields.Many2one('res.partner', 'Ажилтан', domain="[('employee','=',True)]", default=lambda self: self.env.user.partner_id)
	department_id = fields.Many2one('hr.department', 'Хэлтэс', compute='_compute_department', store=True, readonly=True, tracking=True)
	line_ids = fields.One2many('purchase.request.line', 'request_id', 'Product request line', copy=True)
	desc = fields.Text('Тайлбар')
	desc_done = fields.Char('Батлагчийн тайлбар')
	purchase_ids = fields.Many2many('purchase.order', 'purchase_order_purchase_request_rel', 'pur_id', 'rec_id', 'Худалдан Авалт')
	refund_ids = fields.One2many('request.refund.history', 'request_id', 'Refund')
	internal_ids = fields.Many2many('stock.picking', 'purchase_request_stock_rel', 'stock_id', 'rec_id', 'Баримтууд')

	flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
							  default=_get_default_flow_id, copy=False, required=True, 
							  domain="[('model_id.model', '=', 'purchase.request')]")
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
								   default=_get_dynamic_flow_line_id, copy=False,
								   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'purchase.request'),('id', 'in', visible_flow_line_ids)]")
	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Visible state')
	state_type = fields.Selection(related='flow_line_id.state_type', string='Төлөвийн төрөл', 
						#   compute='_compute_state_type', 
						  store=True
						  )
	is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)

	next_state_type = fields.Selection(related='flow_line_next_id.state_type', string='Дараагийн төлөв', 
							#    compute='_compute_next_state_type', 
							store=True
							   )
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах')
	categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
	visible_categ_ids = fields.Many2many('product.category', compute='_compute_visible_categ_ids', string='Харагдах ангилал')
	product_id = fields.Many2one('product.product', related='line_ids.product_id')
	purchase_order_ids = fields.One2many('purchase.order', string='Худалдан авалтын захиулгууд', compute='compute_purchase_order')
	history_ids = fields.One2many('dynamic.flow.history', 'request_id', 'Түүхүүд')
	history_flow_ids = fields.One2many('dynamic.flow.history', 'request_id', 'Урсгалын түүхүүд')
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True)

	is_view_expense = fields.Boolean(compute='_compute_is_view_expense')
	expense_picking_id = fields.Many2one('stock.picking', string='Зарлагын хөдөлгөөн', copy=False)
	warning_messages = fields.Html('Анхааруулга', compute='_compute_wc_messages')
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True)
	confirm_count = fields.Integer(string='Батлах хэрэглэгчийн тоо', compute='_compute_user_ids')
	priority = fields.Selection([('need1', '1. НЭН ЯАРАЛТАЙ'), ('need2', '2. ЯАРАЛТАЙ'), ('need3', '3. ШААРДЛАГАТАЙ')], string='Зэрэглэл')
	use_price = fields.Boolean(string='Үнэ ашиглах', default=False)
	currency_id = fields.Many2one(string='Валют', related='company_id.currency_id', store=True)
	amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=True)
	amount_tax = fields.Monetary(string='Татвар', store=True, readonly=True, compute='_amount_all')
	amount_total = fields.Monetary(string='Нийт', store=True, readonly=True, compute='_amount_all')
	comparison_ids = fields.One2many('purchase.order.comparison', string='Харьцуулалтууд', compute='compute_comparison_order')

	@api.depends('line_ids.price_total')
	def _amount_all(self):
		for order in self:
			amount_untaxed = amount_tax = 0.0
			for line in order.line_ids:
				line._compute_amount()
				amount_untaxed += line.price_subtotal
				amount_tax += line.price_tax
			currency = self.env.company.currency_id
			order.update({
				'amount_untaxed': currency.round(amount_untaxed),
				'amount_tax': currency.round(amount_tax),
				'amount_total': amount_untaxed + amount_tax,
			})

	@api.depends('flow_line_id', 'flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			user = self.env['res.users']
			user_id = self.env['res.users'].search([('partner_id','=',item.partner_id.id)])
			user = user_id if user_id else item.create_uid
			next_flow_line_id = item.flow_line_next_id
			if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = next_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					temp_stage = check_next_flow_line_id._get_next_flow_line()
					if temp_stage:
						if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
							break
						check_next_flow_line_id = temp_stage
					else:
						break
				next_flow_line_id = check_next_flow_line_id
			ooo = next_flow_line_id._get_flow_users(self.branch_id, False, item.create_uid)
			temp_users = ooo.ids if ooo else []
			item.confirm_user_ids = [(6, 0, temp_users)]
			item.confirm_count = len(item.sudo().confirm_user_ids)

	@api.depends('line_ids.product_id', 'line_ids.qty')
	def _compute_wc_messages(self):
		for item in self:
			message = []
			product_ids = item.line_ids.mapped('product_id').ids
			if item.id and product_ids and item.branch_id:
				if len(product_ids) > 1:
					p_ids = str(tuple(product_ids))
				else:
					p_ids = "(" + str(product_ids[0]) + ")"

				sql_query = """
					SELECT prl.product_id,pr.date,pr.partner_id,sum(prl.qty) as qty,pr.name
					FROM purchase_request_line prl
					left join purchase_request pr on (pr.id=prl.request_id)
					left join product_product pp on (prl.product_id=pp.id)
					left join product_template pt on (pt.id=pp.product_tmpl_id)
					WHERE prl.product_id in %s and pr.id!=%s and pr.state_type='done' and pr.branch_id=%s
					and pr.company_id=%s and pr.date<='%s' and pt.type!='service'
					GROUP BY 1,2,3,5""" % (p_ids, item.id, item.branch_id.id, item.company_id.id, item.date)
				self.env.cr.execute(sql_query)
				query_result = self.env.cr.dictfetchall()

				for qr in query_result:
					val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>""" % (
						self.env['product.product'].browse(qr['product_id']).display_name, qr['date'],
						self.env['res.partner'].browse(qr['partner_id']).name, qr['qty'], qr['name'])
					message.append(val)
			if not message:
				message = False
			else:
				message = u'<table style="width: 100%;"><tr><td colspan="4" style="text-align: center;">ӨМНӨ ЗАХИАЛГА ХИЙСЭН</td></tr><tr style="width: 40%;"><td>Бараа</td><td style="width: 15%;">Огноо</td><td style="width: 20%;">Ажилтан</td><td style="width: 10%;">Тоо Хэмжээ</td><td style="width: 15%;">Дугаар</td></tr>' + u''.join(
					message) + u'</table>'
			item.warning_messages = message

	@api.depends('partner_id')
	def _compute_department(self):
		for item in self:
			if self.partner_id.user_ids:
				user_id = self.partner_id.user_ids[0]
				item.department_id = user_id.department_id.id
			else:
				raise UserError(u'%s ажилтан дээр хэрэглэгч алга байна.' % self.partner_id.name)

	@api.depends('line_ids.diff_qty')
	def _compute_is_view_expense(self):
		for item in self:
			if item.line_ids.filtered(lambda r: r.diff_qty > 0):
				item.is_view_expense = True
			else:
				item.is_view_expense = False

	@api.depends('flow_id.categ_ids')
	def _compute_visible_categ_ids(self):
		for item in self:
			cat_ids = self.env['product.category'].search([('id', 'child_of', item.flow_id.categ_ids.ids)])
			item.visible_categ_ids = cat_ids.ids
			if not cat_ids:
				item.visible_categ_ids = self.env['product.category'].search([]).ids

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	@api.depends('flow_line_id.is_not_edit')
	def _compute_is_not_edit(self):
		for item in self:
			item.is_not_edit = item.flow_line_id.is_not_edit

	# @api.depends('flow_line_id.state_type', 'flow_line_id')
	# def _compute_state_type(self):
	# 	for item in self:
	# 		if item.flow_line_id:
	# 			item.state_type = item.flow_line_id.state_type
	# 		else:
	# 			item.state_type = False

	# @api.depends('flow_line_next_id.state_type','flow_line_next_id')
	# def _compute_next_state_type(self):
	# 	for item in self:
	# 		if item.flow_line_next_id:
	# 			item.next_state_type = item.flow_line_next_id.state_type
	# 		else:
	# 			item.next_state_type = False

	def flow_find(self, domain=None, order='sequence'):
		if domain is None:
			domain = []
		if self.flow_id:
			domain.append(('flow_id', '=', self.flow_id.id))
		domain.append(('flow_id.model_id.model', '=', 'purchase.request'))
		return self.env['dynamic.flow.line'].search(domain, order=order, limit=1).id

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False

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
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'purchase.request')])
			else:
				item.visible_flow_line_ids = []

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
				if self.flow_line_id.state_type == 'done':
					self.approved_date = datetime.now()
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'request_id', self)
				self.send_chat_employee(self.sudo().partner_id)
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(False, False, self.create_uid)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
				if self.flow_line_id.state_type != 'done':
					self.update_available_qty()
					# self.product_warning()
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id, False, self.create_uid)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

	def action_back_stage(self):
		if not self.partner_id.user_ids:
			raise UserError(u'%s ажилтан дээр хэрэглэгч алга байна.' % self.partner_id.name)
		user_id = self.partner_id.user_ids[0]
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		if back_flow_line_id:
			if self.visible_flow_line_ids and back_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = back_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					temp_stage = check_next_flow_line_id._get_back_flow_line()
					if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
						break
					check_next_flow_line_id = temp_stage
				back_flow_line_id = check_next_flow_line_id
			if back_flow_line_id._get_check_ok_flow(self.branch_id, user_id.department_id, user_id):
				self.flow_line_id = back_flow_line_id
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'request_id', self)
				self.send_chat_employee(self.sudo().partner_id)
			else:
				raise UserError(_('You are not back user'))

	def action_cancel_stage(self):
		# if not self.partner_id.user_ids:
		# 	raise UserError(u'%s ажилтан дээр хэрэглэгч алга байна.' % self.partner_id.name)
		user_id = self.create_uid
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(self.branch_id, user_id.department_id, user_id):
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'request_id', self)
			self.send_chat_employee(self.sudo().partner_id)
		else:
			raise UserError(_('You are not cancel user'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if self.line_ids.filtered(lambda r: r.po_line_ids):
			raise UserError(u'Худалдан авалтын захиалга үүссэн тул буцаах боломжгүй!')
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'request_id', self)
		else:
			raise UserError(_('You are not draft user'))

	@api.depends('line_ids.po_line_ids')
	def compute_purchase_order(self):
		for item in self:
			item.purchase_order_ids = item.line_ids.mapped('po_line_ids.order_id')

	@api.depends('line_ids.comp_line_ids')
	def compute_comparison_order(self):
		for item in self:
			item.comparison_ids = item.line_ids.mapped('comp_line_ids.comparison_id')

	def action_to_print(self):
		model_id = self.env['ir.model'].search([('model', '=', 'purchase.request')], limit=1)
		template = self.env['pdf.template.generator'].search(
			[('model_id', '=', model_id.id), ('name', '=', 'purchase_request')], limit=1)
		if template:
			res = template.print_template(self.id)
			return res
		else:
			raise UserError(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!')

	@api.model
	def create(self, vals):
		if vals.get('name', 'New') == 'New':
			vals['name'] = self.env['ir.sequence'].next_by_code('purchase.request') or '/'
		return super(PurchaseRequest, self).create(vals)

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

	def unlink(self):
		for item in self:
			if item.state_type != 'draft':
				raise UserError(u'Ноорог биш баримтыг устгахгүй !!!')
		return super(PurchaseRequest, self).unlink()

	def send_chat_next_users(self, partner_ids):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_purchase_request.action_purchase_request_view').id
		html = u'<b>Худалдан авалтын хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (self.partner_id.name)
		html += u"""<b><a target="_blank" href=%s/web#action=%s&id=%s&view_type=form&model=purchase.request>%s</a></b>, дугаартай Худалдан авалтын хүсэлтийг батлана уу""" % (
			base_url, action_id, self.id, self.name)

		# +start activity
		users = self.env['res.users'].search([('partner_id', 'in', partner_ids.ids)])
		if users and self.flow_line_id.flow_id.activity_ok:
			self.env['dynamic.flow.history'].done_activity('purchase.request', self.id)
			self.env['dynamic.flow.history'].create_activity(html, users, 'purchase.request', self.id)
		# -end activity
		self.flow_line_id.send_chat(html, partner_ids)

	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_purchase_request.action_purchase_request_view').id
		html = u'<b>Худалдан авалтын хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (self.partner_id.name)
		html += u"""<b><a target="_blank"  href=%s/web#action=%s&id=%s&view_type=form&model=purchase.request>%s</a></b>, дугаартай Худалдан авалтын хүсэлт <b>%s</b> төлөвт орлоо""" % (base_url, action_id, self.id, self.name, state)
		self.flow_line_id.send_chat(html, partner_ids)

	def get_user_signature(self, ids):
		report_id = self.browse(ids)
		html = '<table>'
		print_flow_line_ids = report_id.flow_id.line_ids.filtered(lambda r: r.is_print)
		history_obj = self.env['dynamic.flow.history']
		for item in print_flow_line_ids:
			his_id = history_obj.search([('flow_line_id', '=', item.id), ('request_id', '=', report_id.id)], limit=1)
			image_str = '________________________'
			if his_id.user_id.digital_signature:
				image_buf = his_id.user_id.digital_signature.decode('utf-8')
				image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />' % image_buf
			user_str = '________________________'
			if his_id.user_id:
				user_str = his_id.user_id.name
			html += u'<tr><td><p>%s</p></td><td>%s</td><td> <p>/%s/</p></td></tr>' % (item.name, image_str, user_str)
		html += '</table>'
		return html

	def get_line_ids(self, ids):
		headers = [
			u'Бараа',
			u'Тайлбар',
			u'Хэмжих нэгж',
			u'Тоо',
			u'Үлдэгдэл',
		]
		datas = []
		report_id = self.browse(ids)

		lines = report_id.line_ids

		sum1 = 0
		nbr = 1
		for line in lines:
			sum1 += line.qty
			pp_code = u'[' + line.product_id.product_code + ']' if line.product_id.product_code else u''
			def_code = u'[' + line.product_id.default_code + ']' if line.product_id.default_code else u''
			p_name = line.product_id.name if line.product_id else u''
			uom_name = line.uom_id.name if line.product_id else u''
			temp = [
				u'<p style="text-align: left;">' + def_code + pp_code + u' ' + p_name + u'</p>',
				u'<p style="text-align: center;">' + line.name + u'</p>',
				u'<p style="text-align: center;">' + uom_name + u'</p>',
				"{0:,.0f}".format(line.qty) or '',
				"{0:,.0f}".format(line.available_qty) or '',
			]
			nbr += 1
			datas.append(temp)
		temp = [
			u'',
			u'<p style="text-align: center; font-weight: bold; ">Нийт дүн</p>',
			u'',
			"{0:,.0f}".format(sum1) or '',
		]
		if not datas:
			return False
		datas.append(temp)
		res = {'header': headers, 'data': datas}
		return res

	def create_expense_picking(self):
		if self.expense_picking_id:
			raise UserError(u'Зарлагын хөдөлгөөн байна')
		picking_obj = self.env['stock.picking']
		move_obj = self.env['stock.move']
		if not self.warehouse_id:
			raise UserError(u'Агуулахаа сонгоно уу')
		location_id = self.warehouse_id.lot_stock_id
		location_dest_id = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
		name = self.desc or ''
		picking_id = picking_obj.create({
			'picking_type_id': self.warehouse_id.out_type_id.id,
			'location_id': location_id.id,
			'location_dest_id': location_dest_id.id,
			'scheduled_date': self.date,
			'move_ids': [],
			'origin': self.name + name
		})
		for item in self.line_ids.filtered(lambda r: r.diff_qty > 0):
			move = {
				'name': name + u' ' + item.product_id.name,
				'product_id': item.product_id.id,
				'product_uom': item.product_id.uom_id.id,
				'product_uom_qty': item.qty,
				'picking_type_id': self.warehouse_id.out_type_id.id,
				'location_id': location_id.id,
				'location_dest_id': location_dest_id.id,
				'date': self.date,
				'picking_id': picking_id.id,
			}
			move_obj.create(move)
		self.expense_picking_id = picking_id.id

	def product_warning(self):
		warning = {}
		title = False
		message = False

		if self.line_ids:
			warning['title'] = 'eee'
			warning['message'] = message
		for item in self.line_ids:
			message='<html>asdfasdfasdf</html>'
		warning['message'] = message
		if message:
			return {'warning': warning}
		# if product_info.purchase_line_warn != 'no-message':
		#	 title = _("Warning for %s") % product_info.name
		#	 message = product_info.purchase_line_warn_msg
		#	 warning['title'] = title
		#	 warning['message'] = message
		#	 if product_info.purchase_line_warn == 'block':
		#		 self.product_id = False
		#	 return {'warning': warning}
		return {}

	def get_company_logo(self, ids):
		report_id = self.browse(ids)
		image_buf = report_id.company_id.logo_web.decode('utf-8')
		image_str = ''
		if len(image_buf) > 10:
			image_str = '<img alt="Embedded Image" width="400" src="data:image/png;base64,%s" />' % image_buf
		return image_str

	def set_partner(self):
		requests = self.env['purchase.request'].sudo().search([('id', '!=', False)])
		for item in requests:
			item.partner_id = item.employee_id.partner_id

class PurchaseRequestLine(models.Model):
	_name = 'purchase.request.line'
	_description = 'Purchase request line'
	_inherit = ['mail.thread']

	name = fields.Char('Нэр', compute='_compute_name')
	product_id = fields.Many2one('product.product', 'Бараа', required=True, index=True)
	desc = fields.Char('Тайлбар зориулалт')
	uom_id = fields.Many2one('uom.uom', related='product_id.uom_id', string='Хэмжих нэгж', readonly=True)
	qty = fields.Float('Тоо хэмжээ', default=1)
	po_qty = fields.Float('PO үүссэн тоо', default=0, copy=False, compute='_compute_po_diff_qty', store=True)
	comparison_qty = fields.Float('Харьцуулалт үүссэн тоо', default=0, copy=False, compute='_compute_po_diff_qty')
	po_diff_qty = fields.Float('PO үүсгэх тоо', compute='_compute_po_diff_qty', store=True, copy=False)
	request_id = fields.Many2one('purchase.request', 'Хүсэлтийн дугаар', ondelete='cascade', index=True)
	price_unit = fields.Float('Нэгж үнэ')
	company_id = fields.Many2one('res.company', related='request_id.company_id', string='Компани', store=True, index=True)
	categ_id = fields.Many2one(related='product_id.categ_id', string='Ангилал', store=True)
	purchase_order_id = fields.Many2one('purchase.order', related='purchase_order_line_id.order_id', string='PO',
										readonly=True, copy=False, store=True)
	purchase_order_line_id = fields.Many2one('purchase.order.line', string='Худалдан авалтын захиалгын мөр', readonly=True, copy=False)
	purchase_order_ids = fields.Many2many('purchase.order', compute='_compute_purchase_order_ids', string='POs')
	comparison_ids = fields.Many2many('purchase.order.comparison', string='POCs', compute='_compute_purchase_order_ids')
	po_line_ids = fields.Many2many('purchase.order.line', 'purchase_order_line_purchase_request_line_rel', 'pr_line_id',
								   'po_line_id', string='ХА-н мөр', copy=False)
	comp_line_ids = fields.Many2many('purchase.order.comparison.line', 'purchase_comparison_line_purchase_request_line_rel',
									 'pr_line_id', 'comp_line_id', string='Харьцуулалтын мөрүүд', copy=False)
	available_qty = fields.Float(string='Үлдэгдэл', readonly=True, store=True, copy=False, compute='compute_available_qty')
	is_product_edit = fields.Boolean(string='Барааг засаж оруулах', compute='_compute_is_product_edit')
	user_id = fields.Many2one('res.users', string='Хангамжийн ажилтан')
	is_expense = fields.Boolean(string='Зарлага болох эсэх')
	diff_qty = fields.Float('Зөрүү', readonly=True, compute='_compute_diff_qty')
	internal_stock_move_id = fields.Many2one('stock.move', string='Дотоод хөдөлгөөн', readonly=True)
	internal_picking_id = fields.Many2one('stock.picking', related='internal_stock_move_id.picking_id',
										  string='Дотоод хөдөлгөөн баримт', readonly=True)
	branch_id = fields.Many2one('res.branch', related='request_id.branch_id', readonly=True, store=True, index=True)
	employee_id = fields.Many2one('hr.employee', related='request_id.employee_id', readonly=True, store=True)
	partner_id = fields.Many2one('res.partner', related='request_id.partner_id', readonly=True, store=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', related='request_id.stage_id', readonly=True, store=True)
	date = fields.Date(related='request_id.date', readonly=True, store=True, index=True)
	desc_req = fields.Text(related='request_id.desc', string='Үндсэн тайлбар', readonly=True, )
	department_id = fields.Many2one('hr.department', related='request_id.department_id', readonly=True, store=True)
	is_over = fields.Boolean('Цаашид авахгүй', default=False, copy=False, tracking=True)
	priority = fields.Selection(related='request_id.priority', store=True, readonly=True)
	flow_id = fields.Many2one('dynamic.flow', related='request_id.flow_id', readonly=True, store=True)
	remained_qty_new = fields.Float(compute='_compute_remain_qty', string="PO үүсэх тооноос үлдсэн", store=True, readonly=True)
	outstanding_qty_new = fields.Float(compute='_compute_remain_qty', string="Хүлээн авахад үлдсэн", store=True, readonly=True)
	po_date_planned_new = fields.Char(compute='_compute_remain_qty', string="Төлөвлөсөн огноо", readonly=True)
	pol_received_qty_new = fields.Float(compute='_compute_remain_qty', string="Хүлээн авсан тоо хэмжээ", store=True, readonly=True)
	taxes_id = fields.Many2many('account.tax', string='Татвар', domain=['|', ('active', '=', False), ('active', '=', True)])
	currency_id = fields.Many2one(related='request_id.currency_id', store=True)
	price_subtotal = fields.Monetary(compute='_compute_amount', string='Дэд дүн', store=True)
	price_total = fields.Monetary(compute='_compute_amount', string='Нийт', store=True)
	price_tax = fields.Float(compute='_compute_amount', string='Татвар', store=True)

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
	def product_id_change(self):
		if not self.product_id:
			return
		self.price_unit = self.qty = 0.0
		self._product_id_change()

	def _product_id_change(self):
		if not self.product_id:
			return
		self._compute_tax_id()
		self.uom_id = self.product_id.uom_po_id or self.product_id.uom_id

	def _compute_tax_id(self):
		for line in self:
			line = line.with_company(line.company_id)
			line.taxes_id = line.product_id.supplier_taxes_id.filtered(lambda r: r.company_id == line.env.company)

	@api.depends('qty', 'price_unit', 'taxes_id')
	def _compute_amount(self):
		for line in self:
			taxes = line.taxes_id.compute_all(line.price_unit, currency=line.currency_id, quantity=line.qty, product=line.product_id)
			line.update({
				'price_tax': taxes['total_included'] - taxes['total_excluded'],
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})

	def write(self, values):
		if 'qty' in values:
			for line in self:
				if line.request_id.state_type != 'draft':
					line.request_id.message_post_with_view('mw_purchase_request.track_po_line_template',
														   values={'line': line, 'qty': values['qty']},
														   subtype_id=self.env.ref('mail.mt_note').id)
		if 'price_unit' in values:
			for line in self:
				if line.request_id.state_type != 'draft':
					line.request_id.message_post_with_view('mw_purchase_request.track_po_line_price_template',
														   values={'line': line, 'price_unit': values['price_unit']},
														   subtype_id=self.env.ref('mail.mt_note').id)
		return super(PurchaseRequestLine, self).write(values)

	def get_po_line(self):
		return self.po_line_ids

	def update_all_line_remain_qty(self):
		for item in self.env['purchase.request.line'].search([]):
			item._compute_po_diff_qty()
			item._compute_remain_qty()

	@api.depends('qty', 'po_line_ids.product_qty', 'po_line_ids.qty_received', 'po_qty')
	def _compute_remain_qty(self):
		for item in self:
			po_line_ids = item.get_po_line()
			po_qty = item.po_qty
			po_receive_qty = sum(po_line_ids.mapped('qty_received'))
			ttd = item.qty - po_qty
			if ttd < 0:
				ttd = 0
			item.remained_qty_new = po_qty - po_receive_qty
			item.pol_received_qty_new = po_receive_qty
			item.outstanding_qty_new = ttd
			item.po_date_planned_new = ', '.join([str(x.date_planned) for x in po_line_ids])

	@api.depends()
	def _compute_purchase_order_ids(self):
		for item in self:
			item.purchase_order_ids = item.po_line_ids.mapped('order_id')
			if item.comp_line_ids:
				item.comparison_ids = item.comp_line_ids.mapped('comparison_id')
			else:
				item.comparison_ids = False

	@api.depends('po_line_ids.product_qty', 'qty', 'po_line_ids.state', 'comp_line_ids.product_qty')
	def _compute_po_diff_qty(self):
		for item in self:
			item.po_qty = sum(item.po_line_ids.filtered(lambda r: r.state != 'cancel').mapped('product_qty'))
			item.comparison_qty = sum(item.comp_line_ids.mapped('product_qty'))
			po_created_qty = item.qty - item.po_qty - item.comparison_qty
			item.po_diff_qty = po_created_qty if po_created_qty > 0 else 0

	@api.onchange('po_diff_qty', 'qty')
	def _onchange_default_compute(self):
		self.po_qty = self.po_diff_qty

	@api.depends('available_qty', 'qty')
	def _compute_diff_qty(self):
		for item in self:
			if item.available_qty > item.qty:
				item.diff_qty = item.available_qty - item.qty
			else:
				item.diff_qty = 0

	def unlink(self):
		for item in self:
			if item.request_id.state_type != 'draft':
				item.request_id.message_post_with_view('mw_purchase_request.track_po_line_template_delete',
													   values={'line': item},
													   subtype_id=self.env.ref('mail.mt_note').id)
			if item.po_line_ids:
				if 'cancel' not in item.po_line_ids.mapped('state'):
					raise UserError(u'ХУДАЛДАН АВАЛТ үүссэн хүсэлтийн мөрийн устгахгүй !!!')

		return super(PurchaseRequestLine, self).unlink()

	@api.depends('request_id.state_type', 'product_id')
	def _compute_is_product_edit(self):
		for item in self:
			if item.request_id.state_type == 'draft':
				item.is_product_edit = True
			elif item.request_id.state_type in ['done', 'cancel']:
				item.is_product_edit = False
			else:
				item.is_product_edit = True

	# @api.depends('product_id','request_id.warehouse_id')
	# def _compute_available_qty(self):
	# 	 for item in self:
	# 		 item.available_qty = self.env['stock.quant']._get_available_quantity(item.product_id, item.request_id.warehouse_id.lot_stock_id, lot_id=False, package_id=False, owner_id=False, strict=True)

	@api.depends('product_id', 'request_id')
	def _compute_name(self):
		for item in self:
			if item.product_id:
				item.name = item.request_id.name + u' | ' + item.product_id.name + u' | ' + (item.desc or '')
			else:
				item.name = item.request_id.name + ' | ' + (item.desc or '')

	@api.onchange('product_id')
	def onchange_product_id(self):
		if self.product_id:
			self.desc = self.product_id.name
		else:
			self.desc = False


class RequestRefundHistory(models.Model):
	_name = 'request.refund.history'
	_description = "request refund history"

	company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)
	refund_user_id = fields.Many2one('res.users', 'Refund users', required=True)
	refund_desc = fields.Char('Refund desc', required=True)
	refund_date = fields.Date('Refund date', required=True)
	request_id = fields.Many2one('purchase.request', 'Purchase request', ondelete='cascade')
