# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	@api.model
	def create(self, val):
		res = super(PurchaseOrder, self).create(val)
		for item in res:
			if item.flow_id:
				search_domain = [('flow_id', '=', item.flow_id.id)]
				re_flow = self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
				item.flow_line_id = re_flow
			item.onchange_partner_id()
		return res

	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		return self.env['dynamic.flow'].search([('model_id.model', '=', 'purchase.order')], order='sequence', limit=1).id

	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Visible state')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв PO', tracking=True, index=True,  default=_get_dynamic_flow_line_id, domain="[('id','in',visible_flow_line_ids)]", copy=False)
	flow_id = fields.Many2one('dynamic.flow', string='Workflow config', tracking=True, default=_get_default_flow_id, copy=True, required=True, domain="[('model_id.model', '=', 'purchase.order')]")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True)
	categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True)
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True)
	confirm_count = fields.Integer(string='Батлах хэрэглэгчийн тоо', compute='_compute_user_ids')

	@api.depends('flow_line_id', 'flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
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
			ooo = next_flow_line_id._get_flow_users(self.branch_id, False, self.create_uid)
			temp_users = ooo.ids if ooo else []
			item.confirm_user_ids = [(6, 0, temp_users)]
			item.confirm_count = len(item.sudo().confirm_user_ids)

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
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'purchase.order')])
			else:
				item.visible_flow_line_ids = []

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	@api.depends('flow_line_id')
	def _compute_state_type(self):
		for item in self:
			item.state_type = item.flow_line_id.state_type

	def flow_find(self, domain=None, order='sequence'):
		if domain is None:
			domain = []
		if self.flow_id:
			domain.append(('flow_id', '=', self.flow_id.id))
		domain.append(('flow_id.model_id.model', '=', 'purchase.order'))
		return self.env['dynamic.flow.line'].search(domain, order=order, limit=1).id

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False

	def action_next_stage(self):
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
			if next_flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, self.create_uid):
				self.flow_line_id = next_flow_line_id
				if self.flow_line_id.state_type == 'done':
					self.button_confirm()
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'po_id', self)
				# chat ilgeeh
				for item in self.mapped('user_id.partner_id'):
					self.send_chat_employee(item)
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id, self.user_id.department_id, self.create_uid)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id, self.user_id.department_id, self.create_uid)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна!\n Батлах хэрэглэгчид %s' % confirm_usernames)

	def action_back_stage(self):
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
			if back_flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, self.create_uid):
				self.flow_line_id = back_flow_line_id
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'po_id', self)
				# chat ilgeeh
				for item in self.mapped('user_id.partner_id'):
					self.send_chat_employee(item)
			else:
				raise UserError(_('Та буцаах хэрэглэгч биш байна!'))

	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('purchase.purchase_form_action').id
		html = u'<b>Худалдан авалтын захиалга</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (self.partner_id.name)
		html += u"""<b><a target="_blank"  href=%s/web#action=%s&id=%s&view_type=form&model=purchase.order>%s</a></b>, дугаартай Худалдан авалтын хүсэлт <b>%s</b> төлөвт орлоо""" % (base_url, action_id, self.id, self.name, state)
		_logger.info('base_url: %s\n %s' % (base_url, html))
		self.flow_line_id.send_chat(html, partner_ids)

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, self.create_uid):
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'po_id', self)
			# chat ilgeeh
			for item in self.mapped('user_id.partner_id'):
				self.send_chat_employee(item)
			self.button_cancel()
		else:
			raise UserError(_('Та цуцлах хэрэглэгч биш байна!'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state = 'draft'
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'po_id', self)
		else:
			raise UserError(_('Та ноороглох хэрэглэгч биш байна!'))

	# ------------------------------flow------------------
	history_flow_ids = fields.One2many('dynamic.flow.history', 'po_id', 'Урсгалын түүхүүд')

	def send_chat_next_users(self, partner_ids):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('purchase.purchase_form_action').id
		html = u'<b>Худалдан авалтын захиалга</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
			self.user_id.name)
		''
		html += u"""<b><a target="_blank" href=%s/web#id=%s&action=%s&model=purchase.order&view_type=form>%s</a></b>, дугаартай Худалдан авалтын захиалгыг батлана уу""" % (
			base_url, self.id, action_id, self.name)
		_logger.info('base_url: %s\n %s' % (base_url, html))
		self.flow_line_id.send_chat(html, partner_ids)

		# +start activity
		users = self.env['res.users'].search([('partner_id', 'in', partner_ids.ids)])
		if users and self.flow_line_id.flow_id.activity_ok:
			self.env['dynamic.flow.history'].done_activity('purchase.order', self.id)
			self.env['dynamic.flow.history'].create_activity(html, users, 'purchase.order', self.id)
		# -end activity

	def get_company_logo(self, ids):
		report_id = self.browse(ids)
		image_buf = report_id.company_id.logo_web.decode('utf-8')
		image_str = ''
		if len(image_buf) > 10:
			image_str = '<img alt="Embedded Image" width="400" src="data:image/png;base64,%s" />' % image_buf
		return image_str

	def get_order_line(self, ids):
		headers = [
			u'Бар код',
			u'Барааны нэр',
			u'Хэмжих нэгж',
			u'Тоо хэмжээ',
			u'Нэгж үнэ',
			u'Нийт үнэ',
			u'Хөнгөлөлт %',
			u'Хөнгөлөлтийн дүн',
			u'Төлөх дүн',
		]
		datas = []
		report_id = self.browse(ids)

		i = 1

		lines = report_id.order_line

		for line in lines:
			p_name = line.product_id.default_code or line.product_id.product_code or ''
			b_name = line.product_id.barcode
			u_name = line.product_uom.name
			discount_amount = line.price_total * line.discount / 100
			temp = [
				b_name,
				p_name,
				u_name,
				"{0:,.0f}".format(line.product_qty) or '',
				u'<p style="text-align: right;">' + (
						"{0:,.2f}".format(line.price_unit_without_discount) or '') + u'</p>',
				u'<p style="text-align: right;">' + (
						"{0:,.2f}".format(line.price_unit_without_discount * line.product_qty) or '') + u'</p>',
				u'<p style="text-align: right;">' + ("{0:,.2f}".format(line.discount) or '') + u'</p>',
				u'<p style="text-align: right;">' + ("{0:,.2f}".format(discount_amount) or '') + u'</p>',
				u'<p style="text-align: right;">' + ("{0:,.2f}".format(line.price_total) or '') + u'</p>',
			]
			datas.append(temp)
			i += 1

		# datas.append(temp)
		res = {'header': headers, 'data': datas}
		return res

	def get_user_signature(self, ids):
		report_id = self.browse(ids)
		html = '<table>'
		print_flow_line_ids = report_id.flow_id.line_ids.filtered(lambda r: r.is_print)
		history_obj = self.env['dynamic.flow.history']
		for item in print_flow_line_ids:
			his_id = history_obj.search([('flow_line_id', '=', item.id), ('po_id', '=', report_id.id)], limit=1)
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

class PurchaseOrderLine(models.Model):
	_inherit = 'purchase.order.line'

	flow_id = fields.Many2one('dynamic.flow', related='order_id.flow_id', readonly=True, store=True)
