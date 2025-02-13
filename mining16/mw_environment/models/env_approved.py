# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime
from odoo.tools.translate import _
from odoo.exceptions import UserError


class EnvApproved(models.Model):
	_name = 'env.approved'
	_description = "БО Баталгаажуулалт"
	_inherit = ["mail.thread", "mail.activity.mixin"]

	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','env.approved'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Урсгал Төлөв', tracking=True, index=True, default=_get_dynamic_flow_line_id, copy=False, domain="[('id','in',visible_flow_line_ids)]")
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True, default=_get_default_flow_id, copy=True, domain="[('model_id.model','=','env.approved')]", index=True)
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)	
	state = fields.Char(string='Төлөв', compute='_compute_state', store=True, index=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True, index=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	history_ids = fields.One2many('env.approved.history', 'approved_id', 'Түүхүүд')
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
				item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'env.approved')])
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
		search_domain.append(('flow_id.model_id.model','=','env.approved'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False
	
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
				self.env['env.approved.history'].create_history(back_flow_line_id, self)
				self.last_state_time = datetime.now()
			else:
				raise UserError('Та буцаах хэрэглэгч биш байна.')
			

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(False, False):
			self.flow_line_id = flow_line_id
			self.env['env.approved.history'].create_history(flow_line_id, self)
			self.state='cancel'
			return self.action_cancel()
		else:
			raise UserError(_('Та цуцлах хэрэглэгч биш байна.'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state='draft'
			self.env['env.approved.history'].create_history(flow_line_id, self)
			self.last_state_time = datetime.now()
		else:
			raise UserError(_('Та ноороглох хэрэглэгч биш байна.'))

	def _default_name(self):
		name = self.env['ir.sequence'].next_by_code('env.approved')
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
	training_ids = fields.One2many('env.training', 'approved_id', string='Сургалтын мөрүүд')
	inspection_ids = fields.One2many('env.inspection', 'approved_id', string='Үл тохиролын мөрүүд')
	water_ids = fields.One2many('env.water', 'approved_id', string='Ус ашиглалтын мөрүүд')
	waste_ids = fields.One2many('env.waste', 'approved_id', string='Хог хаягдалын мөрүүд',)
	rehab_line_ids = fields.One2many('env.rehab.line', 'approved_id', string='Нөхөн сэргээлтийн мөрүүд')
	rehab_land_ids = fields.One2many('env.rehab.land', 'approved_id', string='Газар хөндөлтийн мөрүүд')
	animal_ids = fields.One2many('env.animal', 'approved_id', string='Амьтны үзэгдэл мөрүүд')
	expense_ids = fields.One2many('env.expense', 'approved_id', string='Бараа мат мөрүүд')
	garden_ids = fields.One2many('env.garden.line', 'approved_id', string='Арчилгаа мөрүүд')
	tree_ids = fields.One2many('env.tree.line', 'approved_id', string='Мод бутны мөрүүд')
	attachment_ids = fields.Many2many('ir.attachment', 'env_approved_rel', 'approved_id', 'attachment_id', string=u'Хавсралт', tracking=True)

	def sent_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_environment', 'env_approved_form')[1]
		html = u'<b>Дараах баталгаажуулалтай танилцана уу!!! Доорх линкээр орно уу.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=env.approved&action=%s>%s</a></b>!!!"""% (base_url, self.id, action_id, self.mining_location)
		users = self.flow_line_next_id._get_next_flow_line().user_ids
		for user in users:
			if user:
				self.env.user.send_chat(html, user.partner_id, with_mail=True)

	def action_done(self):
		trainings = self.training_ids.filtered(lambda r: r.is_not_approve==False)
		inspections = self.inspection_ids.filtered(lambda r: r.is_not_approve==False)
		waters = self.water_ids.filtered(lambda r: r.is_not_approve==False)
		wastes = self.waste_ids.filtered(lambda r: r.is_not_approve==False)
		rehab_lines = self.rehab_line_ids.filtered(lambda r: r.is_not_approve==False)
		rehab_lands = self.rehab_land_ids.filtered(lambda r: r.is_not_approve==False)
		animals = self.animal_ids.filtered(lambda r: r.is_not_approve==False)
		expenses = self.expense_ids.filtered(lambda r: r.is_not_approve==False)
		gardens = self.garden_ids.filtered(lambda r: r.is_not_approve==False)
		trees = self.tree_ids.filtered(lambda r: r.is_not_approve==False)

		if trainings:
			for item in trainings:
				item.action_to_done()
		if inspections:
			for item in inspections:
				item.action_to_done()
		if waters:
			for item in waters:
				item.action_to_done()
		if wastes:
			for item in wastes:
				item.action_to_done()
		if rehab_lines:
			for item in rehab_lines:
				item.action_to_done()
		if rehab_lands:
			for item in rehab_lands:
				item.action_to_done()
		if animals:
			for item in animals:
				item.action_to_done()
		if expenses:
			for item in expenses:
				item.action_to_done()
		if gardens:
			for item in gardens:
				item.action_to_done()
		if trees:
			for item in trees:
				item.action_to_done()
		self.write({'state': 'done'})
		self.last_state_time = datetime.now()

	def unlink(self):
		for line in self:
			if line.flow_line_id.state_type != 'draft':
				raise UserError('Устгах боломжгүй зөвхөн ноорог төлөвтэйг устгана!')
		return super(EnvApproved, self).unlink()

	def find(self):
		trainings = self.env['env.training'].search([('training_date','>=',self.start_date),('training_date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if trainings:	
			self.training_ids = trainings.ids
		inspections = self.env['env.inspection'].search([('inspection_date','>=',self.start_date),('inspection_date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if inspections:	
			self.inspection_ids = inspections.ids
		waters = self.env['env.water'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if waters:	
			self.water_ids = waters.ids
		wastes = self.env['env.waste'].search([('waste_date','>=',self.start_date),('waste_date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if wastes:
			self.waste_ids = wastes.ids
		rehab_lines = self.env['env.rehab.line'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if rehab_lines:
			self.rehab_line_ids = rehab_lines.ids
		rehab_lands = self.env['env.rehab.land'].search([('used_date','>=',self.start_date),('used_date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if rehab_lands:	
			self.rehab_land_ids = rehab_lands.ids
		animals = self.env['env.animal'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if animals:	
			self.animal_ids = animals.ids
		expenses = self.env['env.expense'].search([('expense_date','>=',self.start_date),('expense_date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if expenses:	
			self.expense_ids = expenses.ids
		gardens = self.env['env.garden.line'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if gardens:	
			self.garden_ids = gardens.ids
		trees = self.env['env.tree.line'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','=',self.mining_location.id),('state','=','draft')])
		if trees:	
			self.tree_ids = trees.ids
	
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
				self.env['env.approved.history'].create_history(next_flow_line_id, self)
			else:
				con_user = next_flow_line_id._get_flow_users(False, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)


class EnvTraining(models.Model):
	_inherit = 'env.training'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvInspection(models.Model):
	_inherit = 'env.inspection'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvWater(models.Model):
	_inherit = 'env.water'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvWaste(models.Model):
	_inherit = 'env.waste'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvRehabLine(models.Model):
	_inherit = 'env.rehab.line'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvRehabLand(models.Model):
	_inherit = 'env.rehab.land'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvAnimal(models.Model):
	_inherit = 'env.animal'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvExpense(models.Model):
	_inherit = 'env.expense'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)
	
class EnvGardenLine(models.Model):
	_inherit = 'env.garden.line'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)

class EnvTreeLine(models.Model):
	_inherit = 'env.tree.line'

	approved_id = fields.Many2one('env.approved', string='Approved ID', index=True)
	is_not_approve = fields.Boolean(string='Батлахгүй', default=False)


class EnvApprovedHistory(models.Model):
	_name = 'env.approved.history'
	_description = u'Урсгалын түүх'
	_order = 'date desc'

	approved_id = fields.Many2one('env.approved', string='Баталгаажуулах', ondelete='cascade', index=True)
	user_id = fields.Many2one('res.users', 'Өөрчилсөн Хэрэглэгч')
	date = fields.Datetime('Огноо', default=fields.Datetime.now, index=True)
	flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв', index=True)
	spend_time = fields.Float(string='Зарцуулсан цаг', compute='_compute_spend_time', store=True, readonly=True, digits=(16, 2))

	@api.depends('date', 'approved_id')
	def _compute_spend_time(self):
		for obj in self:
			domains = []
			if obj.approved_id:
				domains = [('approved_id', '=', obj.approved_id.id), ('id', '!=', obj.id)]
			if domains and isinstance(obj.id, int):
				ll = self.env['env.approved.history'].search(
					domains, order='date desc', limit=1)
				if ll:
					secs = (obj.date-ll.date).total_seconds()
					obj.spend_time = secs/3600
				else:
					obj.spend_time = 0
			else:
				obj.spend_time = 0

	def create_history(self, flow_line_id, approved_id):
		self.env['env.approved.history'].create({
			'approved_id': approved_id.id,
			'user_id': self.env.user.id,
			'date': datetime.now(),
			'flow_line_id': flow_line_id.id
		})

class DynamicFlow(models.Model):
	_inherit = 'dynamic.flow'

	mining_location_id = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай')