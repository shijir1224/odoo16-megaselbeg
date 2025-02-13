# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class dynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	pricelist_id = fields.Many2one('product.pricelist.confirm', string=u'PriceList ID')

class PricelistItem(models.Model):
	_inherit = "product.pricelist.item"

	pricelist_confirm_id = fields.Many2one('product.pricelist.confirm', 'Pricelist', ondelete='cascade', required=True)

	@api.model
	def create(self, vals):
		if vals.get('pricelist_confirm_id', False):
			vals['pricelist_id'] = self.env['product.pricelist.confirm'].browse(int(vals['pricelist_confirm_id'])).pricelist_id.id
		return super(PricelistItem, self).create(vals)

class SalePricelistConfirm(models.Model):
	_name = "product.pricelist.confirm"
	_description = "Pricelist confirm"
	_order = "sequence asc, id desc"

	def _get_default_currency_id(self):
		return self.env.company.currency_id.id
	
	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(
			('model_id.model', '=', 'product.pricelist.confirm'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id
	
	@api.model
	def create(self, vals):
		if vals.get('name',False):
			pricelist_id = self.env['product.pricelist'].sudo().create({'name': vals['name'],'company_id':vals['company_id'],'active':False})
			vals['pricelist_id'] = pricelist_id.id
		return super(SalePricelistConfirm, self).create(vals)

	name = fields.Char('Үнийн хүснэгтийн Нэр', required=True, translate=True)
	currency_id = fields.Many2one('res.currency', 'Валют', default=_get_default_currency_id, required=True, tracking=True)
	company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id.id, required=True, tracking=True)
	# active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the pricelist without removing it.")
	pricelist_id = fields.Many2one('product.pricelist', string='Price List', copy=False)
	item_ids = fields.One2many('product.pricelist.item', 'pricelist_confirm_id', 'Pricelist Items', domain=[('active','=',False)], copy=False, context={'active_test':False})
	sequence = fields.Integer(default=16)
	user_id = fields.Many2one('res.users', ' Үүсгэсэн ажилтан', default=lambda self: self.env.user.id, tracking=True)
	date = fields.Date(string='Үүсгэсэн огноо', default=lambda self: fields.Datetime.now(), tracking=True)
	visible_flow_line_ids = fields.Many2many( 'dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True, default=_get_dynamic_flow_line_id, copy=False, domain="[('id','in', visible_flow_line_ids)]")
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
							  default=_get_default_flow_id, copy=True, domain="[('model_id.model', '=', 'product.pricelist.confirm')]", index=True)
	flow_line_next_id = fields.Many2one(related='flow_line_id.flow_line_next_id', readonly=True)
	flow_line_back_id = fields.Many2one(related='flow_line_id.flow_line_back_id', readonly=True)
	state = fields.Char(string='Төлөв', compute='_compute_state', store=True, index=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	stage_id = fields.Many2one(
		'dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True, index=True)
	history_ids = fields.One2many('dynamic.flow.history', 'pricelist_id', 'Түүхүүд')

	@api.depends('flow_id.line_ids', 'flow_id.is_amount')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				item.visible_flow_line_ids = self.env['dynamic.flow.line'].search(
					[('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'product.pricelist.confirm')])
			else:
				item.visible_flow_line_ids = []

	@api.depends('flow_line_id.stage_id')
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
		search_domain.append(
			('flow_id.model_id.model', '=', 'product.pricelist.confirm'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

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

			if next_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = next_flow_line_id
				if self.flow_line_id.state_type == 'done':
					self.action_done()
					self.pricelist_id.active = True

				# History uusgeh
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'pricelist_id', self)

				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(
						False, False)
					if send_users:
						self.send_chat_next_users(
							send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(False, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(
						con_user.mapped('display_name'))
				raise UserError(
					u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

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

			if back_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = back_flow_line_id
				# History uusgeh
				self.env['dynamic.flow.history'].create_history(
					back_flow_line_id, 'pricelist_id', self)

			else:
				raise UserError('You are not back user')

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(False, False):
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'pricelist_id', self)
			self.state = 'cancel'
			self.pricelist_id.active = False
			# return self.action_cancel()
		else:
			raise UserError(_('You are not cancel user'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state = 'draft'
			self.env['dynamic.flow.history'].create_history(flow_line_id, 'pricelist_id', self)
		else:
			raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

	def send_chat_next_users(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('mw_sale_pricelist_confirm', 'product_sale_pricelist_action')[1]
		html = u'<b>Үнийн хүснэгт</b><br/><i style="color: red">%s</i> ажилтны үүсгэсэн </br>'%(self.create_uid.partner_id.name or self.partner_id.name)
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=product.pricelist.confirm&action=%s>%s</a></b> үнийн хүснэгт батална уу!"""% (base_url,self.id,action_id,self.name)
		self.flow_line_id.send_chat(html, partner_ids)

	# dynamic stage
	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError('Ноорог төлөвтэй биш бол устгах боломжгүй.')
		return super(SalePricelistConfirm, self).unlink()

	def action_draft(self):
		self.state = 'draft'

	def action_sent(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code(
				'product.pricelist.confirm')
		self.state = 'sent'

	def action_done(self):
		self.state = 'done'
