# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from odoo.tools.translate import _
from odoo.exceptions import UserError


class EnvGasApproved(models.Model):
	_name = 'env.gas.approved'
	_description = "БО Хүлэмжийн хий Баталгаажуулалт"
	_inherit = ["mail.thread", "mail.activity.mixin"]

	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','env.gas.approved'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Урсгал Төлөв', tracking=True, index=True, default=_get_dynamic_flow_line_id, copy=False, domain="[('id','in',visible_flow_line_ids)]")
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True, default=_get_default_flow_id, copy=True, domain="[('model_id.model','=','env.gas.approved')]", index=True)
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)	
	state = fields.Char(string='Төлөв', compute='_compute_state', store=True, index=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True, index=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	history_ids = fields.One2many('env.gas.approved.history', 'gas_approved_id', 'Түүхүүд')
	last_state_time = fields.Datetime(string='Сүүлийн цаг', readonly=True)
	
	def action_cancel(self):
		self.write({'state': 'cancel'})
		self.last_state_time = datetime.now()

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	@api.depends('flow_id.line_ids', 'flow_id.is_amount')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'env.gas.approved')])
			else:
				item.visible_flow_line_ids = []

	@api.depends('flow_line_id')
	def _compute_state(self):
		for item in self:
			item.state = item.flow_line_id.state_type

	def flow_find(self, order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		search_domain.append(('flow_id.model_id.model','=','env.gas.approved'))
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
					if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
						break;
					check_next_flow_line_id = temp_stage
				next_flow_line_id = check_next_flow_line_id

			if next_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = next_flow_line_id
				if self.flow_line_id.state_type=='done':
					self.action_done()
				# History uusgeh
				self.env['env.gas.approved.history'].create_history(next_flow_line_id, self)
			else:
				con_user = next_flow_line_id._get_flow_users(False, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
	
	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		if back_flow_line_id:
			if self.visible_flow_line_ids and back_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = back_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					
					temp_stage = check_next_flow_line_id._get_back_flow_line()
					if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
						break;
					check_next_flow_line_id = temp_stage
				back_flow_line_id = check_next_flow_line_id
				
			if back_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = back_flow_line_id
				# History uusgeh
				self.env['env.gas.approved.history'].create_history(back_flow_line_id, self)
				self.last_state_time = datetime.now()
			else:
				raise UserError('Та буцаах хэрэглэгч биш байна.')
			

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(False, False):
			self.flow_line_id = flow_line_id
			self.env['env.gas.approved.history'].create_history(flow_line_id, self)
			self.state='cancel'
			return self.action_cancel()
		else:
			raise UserError(_('Та цуцлах хэрэглэгч биш байна.'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state='draft'
			self.env['env.gas.approved.history'].create_history(flow_line_id, self)
			self.last_state_time = datetime.now()
		else:
			raise UserError(_('Та ноороглох хэрэглэгч биш байна.'))

	def _default_name(self):
		name = self.env['ir.sequence'].next_by_code('env.gas.approved')
		if name:
			return name
		else:
			False

	name = fields.Char(string='Нэр', readonly=True, default=_default_name)
	mining_location = fields.Many2one(related='flow_id.mining_location_id', string='Үйлдвэр, Уурхай', readonly=True, store=True)
	start_date = fields.Date(string=u'Эхлэх огноо', required=True, tracking=True, readonly=True)
	end_date = fields.Date(string=u'Дуусах огноо', required=True, tracking=True, readonly=True, default=fields.Date.context_today)
	state = fields.Selection([
		('draft', 'Ноорог'),
		('done', 'Батлагдсан'),
		('cancel', 'Цуцлагдсан')
	], 'Төлөв', readonly=True, tracking=True, default='draft')
	technic_ids = fields.One2many('env.technic', 'gas_approved_id', string='Түлшний хэрэглээний мөрүүд')
	mining_quant_ids = fields.One2many('env.mining.quant', 'gas_approved_id', string='Олборлолтын хэмжээний мөрүүд')
	contract_shipping_ids = fields.One2many('env.contract.shipping', 'gas_approved_id', string='Гэрээт тээврийн мөрүүд')
	heat_ids = fields.One2many('env.heat', 'gas_approved_id', string='Дулааны хэрэглээний мөрүүд',)
	tseh_ids = fields.One2many('env.tseh', 'gas_approved_id', string='Цахилгаан эрчим хүчний хэрэглээний мөрүүд')
	attachment_ids = fields.Many2many('ir.attachment', 'env_gas_approved_rel', 'gas_approved_id', 'attachment_id', string=u'Хавсралт', tracking=True)

	def sent_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_environment', 'env_gas_approved_form')[1]
		html = u'<b>Дараах Хүлэмжий хийн баталгаажуулалтай танилцана уу!!! Доорх линкээр орно уу.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=env.gas.approved&action=%s>%s</a></b>!!!"""% (base_url, self.id, action_id, self.mining_location.name)
		users = self.flow_line_next_id._get_next_flow_line().user_ids
		for user in users:
			if user:
				self.env.user.send_chat(html, user.partner_id, with_mail=True)

	def action_done(self):
		technics = self.technic_ids.filtered(lambda r: r.is_not_approve==False)
		mining_quants = self.mining_quant_ids.filtered(lambda r: r.is_not_approve==False)
		shippings = self.contract_shipping_ids.filtered(lambda r: r.is_not_approve==False)
		heats = self.heat_ids.filtered(lambda r: r.is_not_approve==False)
		tsehs = self.tseh_ids.filtered(lambda r: r.is_not_approve==False)

		if technics:
			for item in technics:
				item.action_to_done()
		if mining_quants:
			for item in mining_quants:
				item.action_to_done()
		if shippings:
			for item in shippings:
				item.action_to_done()
		if heats:
			for item in heats:
				item.action_to_done()
		if tsehs:
			for item in tsehs:
				item.action_to_done()
		self.write({'state': 'done'})
		self.last_state_time = datetime.now()

	def unlink(self):
		for line in self:
			if line.flow_line_id.state_type != 'draft':
				raise UserError('Устгах боломжгүй зөвхөн ноорог төлөвтэйг устгана!')
		return super(EnvGasApproved, self).unlink()

	def find(self):
		technics = self.env['env.technic'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if technics:
			self.technic_ids = technics.ids
		mining_quants = self.env['env.mining.quant'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if mining_quants:
			self.mining_quant_ids = mining_quants.ids
		shippings = self.env['env.contract.shipping'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if shippings:
			self.contract_shipping_ids = shippings.ids
		heats = self.env['env.heat'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if heats:
			self.heat_ids = heats.ids
		tsehs = self.env['env.tseh'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if tsehs:
			self.tseh_ids = tsehs.ids


	def action_next_stage(self):
		if self.flow_line_next_id:
			self.sent_mail()
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
				check_next_flow_line_id = next_flow_line_id
				while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
					
					temp_stage = check_next_flow_line_id._get_next_flow_line()
					if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
						break;
					check_next_flow_line_id = temp_stage
				next_flow_line_id = check_next_flow_line_id

			if next_flow_line_id._get_check_ok_flow(False, False):
				self.flow_line_id = next_flow_line_id
				if self.flow_line_id.state_type=='done':
					self.action_done()
				# History uusgeh
				self.env['env.gas.approved.history'].create_history(next_flow_line_id, self)
			else:
				con_user = next_flow_line_id._get_flow_users(False, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)


class EnvTechnic(models.Model):
	_inherit = 'env.technic'

	gas_approved_id = fields.Many2one('env.gas.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvMiningQuant(models.Model):
	_inherit = 'env.mining.quant'

	gas_approved_id = fields.Many2one('env.gas.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvContractShipping(models.Model):
	_inherit = 'env.contract.shipping'

	gas_approved_id = fields.Many2one('env.gas.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvHeat(models.Model):
	_inherit = 'env.heat'

	gas_approved_id = fields.Many2one('env.gas.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvTseh(models.Model):
	_inherit = 'env.tseh'

	gas_approved_id = fields.Many2one('env.gas.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)


class EnvGasApprovedHistory(models.Model):
	_name = 'env.gas.approved.history'
	_description = u'Урсгалын түүх'
	_order = 'date desc'

	gas_approved_id = fields.Many2one('env.gas.approved', string='Баталгаажуулах', ondelete='cascade', index=True)
	user_id = fields.Many2one('res.users', 'Өөрчилсөн Хэрэглэгч')
	date = fields.Datetime('Огноо', default=fields.Datetime.now, index=True)
	flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв', index=True)
	spend_time = fields.Float(string='Зарцуулсан цаг', compute='_compute_spend_time', store=True, readonly=True, digits=(16, 2))

	@api.depends('date', 'gas_approved_id')
	def _compute_spend_time(self):
		for obj in self:
			domains = []
			if obj.gas_approved_id:
				domains = [('gas_approved_id', '=', obj.gas_approved_id.id), ('id', '!=', obj.id)]
			if domains and isinstance(obj.id, int):
				ll = self.env['env.gas.approved.history'].search(
					domains, order='date desc', limit=1)
				if ll:
					secs = (obj.date-ll.date).total_seconds()
					obj.spend_time = secs/3600
				else:
					obj.spend_time = 0
			else:
				obj.spend_time = 0

	def create_history(self, flow_line_id, gas_approved_id):
		self.env['env.gas.approved.history'].create({
			'gas_approved_id': gas_approved_id.id,
			'user_id': self.env.user.id,
			'date': datetime.now(),
			'flow_line_id': flow_line_id.id
		})