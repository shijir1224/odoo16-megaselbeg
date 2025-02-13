# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class PurchaseOrderComparison(models.Model):
	_inherit = 'purchase.order.comparison'

	@api.model
	def create(self, val):
		res = super(PurchaseOrderComparison, self).create(val)
		for item in res:
			if item.flow_id:
				search_domain = [('flow_id', '=', item.flow_id.id)]
				re_flow = self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
				item.flow_line_id = re_flow
		return res

	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		return self.env['dynamic.flow'].search([('model_id.model', '=', 'purchase.order.comparison')], order='sequence',
											   limit=1).id

	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids',
											 string='Visible state')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
								   default=_get_dynamic_flow_line_id, domain="[('id','in',visible_flow_line_ids)]",
								   copy=False)
	flow_id = fields.Many2one('dynamic.flow', string='Workflow config', tracking=True,
							  default=_get_default_flow_id,
							  copy=True, required=True, domain="[('model_id.model', '=', 'purchase.order.comparison')]")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True)
	categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
							   string='Төлөв stage', store=True)
	history_flow_ids = fields.One2many('dynamic.flow.history', 'comparison_id', 'Урсгалын түүхүүд')
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True)
	confirm_count = fields.Integer(string='Батлах хэрэглэгчийн тоо')

	@api.depends('flow_line_id', 'flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			next_flow_line_id = item.flow_line_next_id
			ooo = next_flow_line_id._get_flow_users(False, False)
			temp_users = ooo.ids if ooo else []
			item.confirm_user_ids = [(6, 0, temp_users)]
			item.confirm_count = len(item.sudo().confirm_user_ids)

	def end_vote(self):
		self.ensure_one()
		self.write({'state': 'vote_ended'})

	def end_comparison(self):
		"""
		:return: OVERRIDED METHOD
		"""
		self.ensure_one()
		winning_order = self.related_po_ids.filtered(lambda l: l.partner_id == self.winning_partner)
		losing_orders = self.related_po_ids - winning_order
		if self.user_id != self.env.user:
			raise UserError(_('Only the Comparison Representative can end the comparison.'))
		try:
			for obj in losing_orders:
				obj.action_cancel_stage()
		except Exception as e:
			_logger.info(self, 'losing_orders', losing_orders, e)
		winning_order.button_draft()
		winning_order.action_next_stage()
		self.write({'state': 'ended',
					'winning_po_id': winning_order.id})

	@api.depends('flow_id.line_ids', 'flow_id.is_amount')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				if item.flow_id.is_amount:
					flow_line_ids = []
					for fl in item.flow_id.line_ids:
						if fl.state_type == 'draft':
							flow_line_ids.append(fl.id)
						elif fl.amount_price_min == 0 and fl.amount_price_max == 0:
							flow_line_ids.append(fl.id)
					item.visible_flow_line_ids = flow_line_ids
				else:
					item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),
																					   ('flow_id.model_id.model', '=', 'purchase.order.comparison')])
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
		domain.append(('flow_id.model_id.model', '=', 'purchase.order.comparison'))
		return self.env['dynamic.flow.line'].search(domain, order=order, limit=1).id

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False

	def start_vote(self):
		res = super(PurchaseOrderComparison, self).start_vote()
		users = self.flow_id.line_ids.mapped('user_ids')
		for obj in users:
			self.env['purchase.order.comparison.vote'].create({'comparison_id': self.id,
															   'user_id': obj.id})
		return res

	def action_next_stage(self):
		if not self.line_ids:
			raise UserError(_('Please create lines'))
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
			if self.flow_line_id._get_check_ok_flow(self.branch_id, self.user_id.department_id, self.sudo().user_id):
				if self.flow_line_id.state_type == 'draft':
					self.create_purchase_orders()
				elif self.flow_line_id.state_type == 'start_vote':
					self.start_vote()
				elif self.flow_line_id.state_type == 'vote':
					return self.vote()
				elif self.flow_line_id.state_type == 'vote_ended':
					self.end_comparison()
				# History uusgeh
				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'comparison_id', self)
				# chat ilgeeh
				for item in self.mapped('user_id.partner_id'):
					self.send_chat_employee(item)
				if self.flow_line_id:
					send_users = self.flow_line_id._get_flow_users(self.branch_id, self.user_id.department_id,
																   self.sudo().user_id)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
			else:
				con_user = self.flow_line_id._get_flow_users(self.branch_id, self.user_id.department_id,
															 self.sudo().user_id)
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
				if back_flow_line_id.state_type in ['draft', 'vote_started']:
					self.revert_start_vote()
				elif self.flow_line_id.state_type == 'vote_started':
					raise(_('Voting has ended so it is not possible to back.'))
				self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'comparison_id', self)
				# chat ilgeeh
				for item in self.mapped('user_id.partner_id'):
					self.send_chat_employee(item)
			else:
				raise UserError(_('You are not back user'))

	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_purchase_comparison.action_purchase_order_comparison').id
		html = u'<b>Худалдан авалтын харьцуулалт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
			self.user_id.name)
		html += u"""<b><a target="_blank"  href=%s/web#action=%s&id=%s&view_type=form&model=purchase.order.comparison>%s</a></b>, дугаартай Худалдан авалтын харьцуулалт <b>%s</b> төлөвт орлоо""" % (
			base_url, action_id, self.id, self.name, state)
		self.flow_line_id.send_chat(html, partner_ids)

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.to_draft()
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'comparison_id', self)
		else:
			raise UserError(_('You are not draft user'))
	# ------------------------------flow------------------

	def send_chat_next_users(self, partner_ids):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_purchase_comparison.action_purchase_order_comparison').id
		html = u'<b>Худалдан авалтын харьцуулалт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
			self.user_id.name)
		''
		html += u"""<b><a target="_blank" href=%s/web#id=%s&action=%s&model=purchase.order.comparison&view_type=form>%s</a></b>, дугаартай Худалдан авалтын харьцуулалтыг батлана уу""" % (
			base_url, self.id, action_id, self.name)
		self.flow_line_id.send_chat(html, partner_ids)

		# +start activity
		users = self.env['res.users'].search([('partner_id', 'in', partner_ids.ids)])
		if users and self.flow_line_id.flow_id.activity_ok:
			self.env['dynamic.flow.history'].done_activity('purchase.order.comparison', self.id)
			self.env['dynamic.flow.history'].create_activity(html, users, 'purchase.order.comparison', self.id)
		# -end activity


class PurchaseOrderComparisonLine(models.Model):
	_inherit = 'purchase.order.comparison.line'

	flow_id = fields.Many2one('dynamic.flow', related='comparison_id.flow_id', readonly=True, store=True)


class PurchaseOrderComparisonVote(models.Model):
	_inherit = 'purchase.order.comparison.vote'

	def vote(self, partner_id, comment):
		res = super(PurchaseOrderComparisonVote, self).vote(partner_id, comment)
		comp = self.comparison_id
		next_flow_line_id = comp.flow_line_id._get_next_flow_line()
		if next_flow_line_id.state_type == 'vote_ended':
			comp.with_context(base_wizard_confirmed=True).end_vote()
		comp.flow_line_id = next_flow_line_id
		self.env['dynamic.flow.history'].create_history(comp.flow_line_id, 'comparison_id', comp)
		# chat ilgeeh
		for item in comp.mapped('user_id.partner_id'):
			comp.send_chat_employee(item)
		if comp.flow_line_id:
			send_users = comp.flow_line_id._get_flow_users(comp.branch_id, comp.user_id.department_id,
														   comp.sudo().user_id)
			if send_users:
				comp.send_chat_next_users(send_users.mapped('partner_id'))
		return res
