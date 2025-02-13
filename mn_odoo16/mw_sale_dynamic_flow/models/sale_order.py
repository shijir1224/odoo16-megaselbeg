# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	@api.model
	def create(self, val):
		res = super(SaleOrder, self).create(val)
		for item in res:
			if item.flow_id:
				search_domain = [('flow_id', '=', item.flow_id.id)]
				re_flow = self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
				item.flow_line_id = re_flow
		return res

	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		return self.env['dynamic.flow'].search([('model_id.model', '=', 'sale.order')], order='sequence', limit=1).id

	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Visible state')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв SO', tracking=True, index=True,  default=_get_dynamic_flow_line_id, domain="[('id','in',visible_flow_line_ids)]", copy=False)
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал тохиргоо', tracking=True, default=_get_default_flow_id, copy=True, required=True, domain="[('model_id.model', '=', 'sale.order')]")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True)
	categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True)

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
						if fl.amount_price_min <= item.amount_total:
							flow_line_ids.append(fl.id)
					item.visible_flow_line_ids = flow_line_ids
				else:
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'sale.order')])
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
		domain.append(('flow_id.model_id.model', '=', 'sale.order'))
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
			if next_flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, self.sudo().user_id):
				self.flow_line_id = next_flow_line_id
				if self.flow_line_id.state_type == 'done':
					self.action_confirm()
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'so_id', self)
				# chat ilgeeh
    # for item in self.mapped('user_id.partner_id'):
    # 	self.send_chat_employee(item)
    # if self.flow_line_next_id:
    # 	send_users = self.flow_line_next_id._get_flow_users(self.branch_id, self.user_id.department_id, self.sudo().user_id)
     # if send_users:
     # 	self.send_chat_next_users(send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id, self.user_id.department_id, self.sudo().user_id)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

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
			if back_flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, False):
				self.flow_line_id = back_flow_line_id
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'so_id', self)
				# chat ilgeeh
    # for item in self.mapped('user_id.partner_id'):
    # 	self.send_chat_employee(item)
			else:
				raise UserError(_('You are not back user'))

	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('sale.action_quotations_with_onboarding').id
		html = u'<b>Борлуулалтын захиалга</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (self.partner_id.name)
		html += u"""<b><a target="_blank"  href=%s/web#action=%s&id=%s&view_type=form&model=sale.order>%s</a></b>, дугаартай борлуулалт <b>%s</b> төлөвт орлоо""" % (base_url, action_id, self.id, self.name, state)
		self.flow_line_id.send_chat(html, partner_ids)

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, False):
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'so_id', self)
			# chat ilgeeh
   # for item in self.mapped('user_id.partner_id'):
   # 	self.send_chat_employee(item)
			self.action_cancel()
		else:
			raise UserError(_('You are not cancel user'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.action_draft()
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'so_id', self)
		else:
			raise UserError(_('You are not draft user'))

	# ------------------------------flow------------------
	history_flow_ids = fields.One2many('dynamic.flow.history', 'so_id', 'Урсгалын түүхүүд')

	def send_chat_next_users(self, partner_ids):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('sale.action_quotations_with_onboarding').id
		html = u'<b>Борлуулалтын захиалга</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
			self.user_id.name)
		''
		html += u"""<b><a target="_blank" href=%s/web#id=%s&action=%s&model=sale.order&view_type=form>%s</a></b>, дугаартай борлуулалтын захиалгыг батлана уу""" % (
			base_url, self.id, action_id, self.name)
		self.flow_line_id.send_chat(html, partner_ids)

		# +start activity
		users = self.env['res.users'].search([('partner_id', 'in', partner_ids.ids)])
		if users and self.flow_line_id.flow_id.activity_ok:
			self.env['dynamic.flow.history'].done_activity('sale.order', self.id)
			self.env['dynamic.flow.history'].create_activity(html, users, 'sale.order', self.id)
		# -end activity

class SaleOrderLine(models.Model):
	_inherit = 'sale.order.line'

	flow_id = fields.Many2one('dynamic.flow', related='order_id.flow_id', readonly=True, store=True)
