# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
# from odoo.tools import float_compare, float_is_zero

class dynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	scrap_id = fields.Many2one('stock.scrap.multi', string='Scrap', ondelete='cascade', index=True)

class StockPicking(models.Model):
	_inherit = 'stock.picking'

	scrap_multi_ids = fields.One2many('stock.scrap.multi', 'picking_id', string='Scraps')

	def view_scraps(self):
		self.ensure_one()
		action = self.env.ref('mw_stock.action_stock_scrap_multi').read()[0]
		action['domain'] = [('id','in',self.scrap_multi_ids.ids)]
		return action

class StockScrap(models.Model):
	_inherit = 'stock.scrap'

	parent_id = fields.Many2one('stock.scrap.multi', string='Parent ID')
	description = fields.Char(string='Тайлбар')
	attachment_ids = fields.Many2many('ir.attachment','scrap_attachment_rel','scrap_id','attachment_id', string='Хавсралт')

	# def print_context(self):
	# 	print('context', self.env.context)

class StockScrapMulti(models.Model):
	_name = 'stock.scrap.multi'
	_inherit = ['mail.thread']
	_order = 'id desc'
	_description = 'Multi Scrap'

	def _get_name(self):
		return self.env['ir.sequence'].sudo().next_by_code('stock.scrap.multi')

	name = fields.Char(string='Name', readonly=True)
	date = fields.Date(string='Date', default=fields.Date.context_today)
	picking_id = fields.Many2one('stock.picking', string='Picking')
	scrap_lines = fields.One2many('stock.scrap', 'parent_id', string='Scrap lines')
	company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True, default=lambda self: self.env.company)
	branch_id = fields.Many2one('res.branch', string='Branch', required=True, readonly=True, default=lambda self: self.env.user.branch_id)
	resolution_period = fields.Integer(string='Шийдвэрлэх хоног', default=7)
	product_ids = fields.Many2many('product.product', string='Products', compute="_compute_products")

	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = [('model_id.model', '=', 'stock.scrap.multi'), ('company_id', '=', self.env.company.id)]
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids',
		string='Харагдах төлөв')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
		default=_get_dynamic_flow_line_id, copy=False)
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал тохиргоо', tracking=True,
		default=_get_default_flow_id, copy=True, required=True, domain="[('model_id.model', '=', 'stock.scrap.multi')]")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
	state_type = fields.Char(string='State')
	# categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
		string='Төлөв stage', store=True)
	history_ids = fields.One2many('dynamic.flow.history', 'scrap_id', 'Түүхүүд')

	@api.model
	def create(self, vals):
		vals.update({'name': self._get_name()})
		res = super(StockScrapMulti, self).create(vals)
		return res

	@api.depends('picking_id')
	def _compute_products(self):
		for item in self:
			if item.picking_id:
				item.product_ids = [(6,0,item.picking_id.move_line_ids_without_package.mapped('product_id.id'))]
			else:
				item.product_ids = False

	@api.depends('flow_id')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				item.visible_flow_line_ids = self.env['dynamic.flow.line'].search(
					[('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'stock.scrap.multi')])
			else:
				item.visible_flow_line_ids = []

	@api.depends('flow_line_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	# ------------------------------flow------------------
	@api.depends('flow_line_id')
	def _compute_state(self):
		for item in self:
			item.state = item.flow_line_id.state_type

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id', '=', self.flow_id.id))

		search_domain.append(('flow_id.model_id.model', '=', 'stock.scrap.multi'))
		# print(self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id)
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False
			self.state_type = ''

	@api.depends('flow_id', 'visible_flow_line_ids', 'flow_line_id')
	def _compute_flow_line_id(self):
		for item in self:
			item.flow_line_next_id = item._get_next_flow_line(item.visible_flow_line_ids)
			item.flow_line_back_id = item._get_back_flow_line(item.visible_flow_line_ids)

	def _get_next_flow_line(self, flow_line_ids=False):
		if self.id:
			if flow_line_ids:
				next_flow_line_id = self.env['dynamic.flow.line'].search([
					('flow_id', '=', self.flow_id.id),
					('id', '!=', self.flow_line_id.id),
					('sequence', '>', self.flow_line_id.sequence),
					('sequence', 'in', flow_line_ids.mapped('sequence')),
					('state_type', 'not in', ['cancel']),
				], limit=1, order='sequence')
				return next_flow_line_id
			else:
				next_flow_line_id = self.env['dynamic.flow.line'].search([
					('flow_id', '=', self.flow_id.id),
					('id', '!=', self.flow_line_id.id),
					('sequence', '>', self.flow_line_id.sequence),
					('state_type', 'not in', ['cancel']),
				], limit=1, order='sequence')
				return next_flow_line_id
		else:
			return False

	def _get_back_flow_line(self, flow_line_ids=False):
		if self.id:
			if flow_line_ids:
				back_flow_line_id = self.env['dynamic.flow.line'].search([
					('flow_id', '=', self.flow_id.id),
					('id', '!=', self.flow_line_id.id),
					('sequence', '<', self.flow_line_id.sequence),
					('sequence', 'in', flow_line_ids.mapped('sequence')),
					('state_type', 'not in', ['cancel']),
				], limit=1, order='sequence desc')
				return back_flow_line_id
			else:
				back_flow_line_id = self.env['dynamic.flow.line'].search([
					('flow_id', '=', self.flow_id.id),
					('id', '!=', self.flow_line_id.id),
					('sequence', '<', self.flow_line_id.sequence),
					('state_type', 'not in', ['cancel']),
				], limit=1, order="sequence desc")
			return back_flow_line_id
		return False

	def action_next_stage(self):
		cdc
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

			if next_flow_line_id._get_check_ok_flow(self.branch_id, False):
				self.flow_line_id = next_flow_line_id
				if self.flow_line_id.state_type == 'done':
					self.action_done()

				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'scrap_id', self)
				if self.flow_line_next_id:
					self.env.user
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id, False, self.env.user)
					# if send_users:
					# 	self.send_chat_employee(send_users.mapped('partner_id'))
			else:
				self.env.user
				con_user = next_flow_line_id._get_flow_users(self.branch_id, False, self.env.user)
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

			if back_flow_line_id:
				self.flow_line_id = back_flow_line_id
				self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'scrap_id', self)

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(self.branch_id, False):
			return self.action_cancel()
		else:
			raise UserError(_('You are not cancel user'))

	def set_stage_cancel(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(self.branch_id, False):
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'scrap_id', self)
		else:
			raise UserError(_('You are not cancel user'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state = 'draft'
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'scrap_id', self)
		else:
			raise UserError(_('You are not draft user'))
		
	def action_done(self):
		self.ensure_one()
		self.state_type = 'done'
		for scrap_line in self.scrap_lines:
			scrap_line.action_validate()

	@api.model
	def notfication_resolution_period(self):
		unchecked_scrap_ids = self.env['stock.scrap.multi'].search([('state_type','in',['done'])])
		for scrap_id in unchecked_scrap_ids:
			today = date.today()
			due_date = scrap_id.date + relativedelta(days=scrap_id.resolution_period)

			if due_date > today:
				hassan_date = due_date - today
				if hassan_date.days <= 14 and hassan_date.days >= 0:
					base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
					action_id = self.env.ref('mw_stock.action_stock_scrap_multi').id
					html = """
						<center><b>Гологдол бараа хянах мэдэгдэл</b><br/><center/>
						<br/>
						<p><b><a target="_blank" href={0}/web#id={1}&action={2}&model=purchase.order&view_type=form>{3}</a></b> дугаартай гологдлыг хянана уу!<p/>
						<p>{4} хоног үлдлээ<p/>
						""".format(base_url, scrap_id.id, action_id, scrap_id.name, hassan_date.days)
					partner_ids = self.env['res.partner']
					partner_ids += scrap_id.create_uid.partner_id
					self.env.user.send_emails(partners=partner_ids, subject='Гологдол бараа хянах мэдэгдэл', body=html, attachment_ids=False)
			else:
				hassan_date = today - due_date
				if hassan_date.days <= 14 and hassan_date.days > 0:
					base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
					action_id = self.env.ref('mw_stock.action_stock_scrap_multi').id
					html = """
						<center><b>Гологдол бараа хэтэрсэн мэдэгдэл</b><br/><center/>
						<br/>
						<p><b><a target="_blank" href={0}/web#id={1}&action={2}&model=purchase.order&view_type=form>{3}</a></b> дугаартай гологдлыг хянана уу!<p/>
						<p>{4} хоног хэтэрсэн байна<p/>
						""".format(base_url, scrap_id.id, action_id, scrap_id.name, hassan_date.days)
					partner_ids = self.env['res.partner']
					partner_ids += scrap_id.create_uid.partner_id
					self.env.user.send_emails(partners=partner_ids, subject='Гологдол бараа хэтэрсэн мэдэгдэл', body=html, attachment_ids=False)
		return 