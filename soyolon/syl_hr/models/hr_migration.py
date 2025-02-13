
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class hrMigration(models.Model):
	_name = 'hr.migration'
	_description = 'hr migration'

	name = fields.Char('Ажил хүлээлцэх акт №20')
	line_ids = fields.One2many('hr.migration.line', 'parent_id')
	line_id2 = fields.One2many('hr.migration.line2', 'parent_id')
	line_id3 = fields.One2many('hr.migration.line3', 'parent_id')
	accept_employee_id = fields.Many2one('hr.employee', 'Ажилтан')
	employee_id = fields.Many2one('hr.employee', 'Ажилтан')
	doc_employee_id = fields.Many2one('hr.employee', 'Ажилтан')
	review_employee_id = fields.Many2one('hr.employee', 'Хэлтсийн удирдлага', tracking=True)
	re_desc = fields.Char('Хэлтсийн удирдлагын санал', tracking=True)
	is_trial = fields.Boolean('Туршилтын хугацааг сунгах', tracking=True)
	is_accept = fields.Boolean('Үндсэн ажилтан болгох', tracking=True)
	is_migrate = fields.Boolean('Шилжилт хөдөлгөөн хийх', tracking=True)
	is_fire = fields.Boolean('Туршилтын хугацаанд ажилд тэнцээгүй ажилтныг ажлаас чөлөөлөх', tracking=True)
	compute_type = fields.Char('Төрөл',compute='_compute_type',store=True)
	is_up = fields.Boolean('Албан тушаал дэвшүүлэх', tracking=True)
	is_down = fields.Boolean('Албан тушаал бууруулах', tracking=True)
	is_job_migrate = fields.Boolean('Албан тушаал шилжүүлэх', tracking=True)
	migrate_type = fields.Char('Шилжилт Төрөл',compute='_compute_migrate',store=True)
	job_id = fields.Many2one('hr.job', string='Одоогийн албан тушаал', tracking=True)
	up_job_id = fields.Many2one('hr.job', string='Өөрчилөх албан тушаал', tracking=True)
	down_job_id = fields.Many2one('hr.job', string='Бууруулах албан тушаал', tracking=True)
	migrate_job_id = fields.Many2one('hr.job', string='Шилжүүлэх албан тушаал', tracking=True)
	salary_code = fields.Many2one('salary.level', string='Цалингийн шатлал')

	date = fields.Date('Огноо')
	date_two = fields.Date('Огноо')
	date_thr = fields.Date('Огноо')
	department_id = fields.Many2one(
		'hr.department', string='Хэлтэс', tracking=True)

	acc_department_id = fields.Many2one(
		'hr.department', string='Хэлтэс', tracking=True)
	acc_job_id = fields.Many2one(
		'hr.job', string='Албан тушаал', tracking=True)
	doc_department_id = fields.Many2one(
		'hr.department', string='Хэлтэс', tracking=True)
	doc_job_id = fields.Many2one(
		'hr.job', string='Албан тушаал', tracking=True)

	@api.depends('is_trial','is_accept','is_migrate','is_fire')
	def _compute_type(self):
		for item in self:
			compute_type=''
			if item.is_trial==True:
				compute_type = 'Туршилтын хугацааг сунгах'
			elif item.is_accept==True:
				compute_type = 'Үндсэн ажилтан болгох'
			elif item.is_migrate==True:
				compute_type = 'Шилжилт хөдөлгөөн хийх'
			elif item.is_fire==True:
				compute_type = 'Туршилтын хугацаанд ажилд тэнцээгүй ажилтныг ажлаас чөлөөлөх'
			item.compute_type = compute_type
	
	@api.depends('is_migrate','is_up','is_down','is_job_migrate')
	def _compute_migrate(self):
		for item in self:
			migrate_type=''
			if item.is_migrate==True:
				if item.is_up==True:
					migrate_type = 'Албан тушаал дэвшүүлэх'
				elif item.is_down==True:
					migrate_type = 'Албан тушаал  бууруулах'
				elif item.is_job_migrate==True:
					migrate_type = 'Албан тушаал шилжүүлэх'
			item.migrate_type = migrate_type



	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id.id
			self.job_id = self.employee_id.job_id.id

	@api.onchange('accept_employee_id')
	def onchange_accept_employee_id(self):
		if self.accept_employee_id:
			self.acc_department_id = self.accept_employee_id.department_id.id
			self.acc_job_id = self.accept_employee_id.job_id.id

	@api.onchange('doc_employee_id')
	def onchange_doc_employee_id(self):
		if self.doc_employee_id:
			self.doc_department_id = self.doc_employee_id.department_id.id
			self.doc_job_id = self.doc_employee_id.job_id.id


# dynamic flow

	def _get_dynamic_flow_line_id(self):
		return self.flow_find().id

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(
			('model_id.model', '=', 'hr.migration'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	visible_flow_line_ids = fields.Many2many(
		'dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Урсгал Төлөв', tracking=True,
								   index=True, default=_get_dynamic_flow_line_id, copy=False, domain="[('id','in', visible_flow_line_ids)]")
	history_ids = fields.One2many(
		'dynamic.flow.history', 'migration_id', 'Түүхүүд')
	flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True, default=_get_default_flow_id,
							  copy=True, required=True, domain="[('model_id.model', '=', 'hr.migration')]")

	flow_line_next_id = fields.Many2one(
		'dynamic.flow.line', related='flow_line_id.flow_line_next_id',  store=True)

	stage_id = fields.Many2one(
		'dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)

	flow_line_back_id = fields.Many2one(
		'dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	next_state_type = fields.Char(
		string='Дараагийн төлөв', compute='_compute_next_state_type')
	state_type = fields.Char(string='Төлөвийн төрөл',
							 compute='_compute_state_type', store=True)
	is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
	state = fields.Char(
		string='Төлөв', compute='_compute_state', store=True, index=True)
	confirm_user_ids = fields.Many2many(
		'res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)
	branch_id = fields.Many2one(
		'res.branch', 'Салбар', default=lambda self: self.env.user.branch_id)

	@api.depends('flow_line_id')
	def _compute_state(self):
		for item in self:
			item.state = item.flow_line_id.state_type

	@api.depends('flow_id.line_ids', 'flow_id.is_amount')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				item.visible_flow_line_ids = self.env['dynamic.flow.line'].search(
					[('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'hr.migration')])
			else:
				item.visible_flow_line_ids = []

	@api.depends('flow_line_id.is_not_edit')
	def _compute_is_not_edit(self):
		for item in self:
			item.is_not_edit = item.flow_line_id.is_not_edit

	@api.depends('flow_line_id', 'flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			temp_users = []
			for w in item.flow_id.line_ids:
				temp = []
				try:
					temp = w._get_flow_users(item.branch_id, item.sudo(
					).employee_id.department_id, item.sudo().employee_id.user_id).ids
				except:
					pass
				temp_users += temp
			item.confirm_user_ids = temp_users

	@api.depends('flow_line_id')
	def _compute_state_type(self):
		for item in self:
			item.state_type = item.flow_line_id.state_type

	@api.depends('flow_line_next_id.state_type')
	def _compute_next_state_type(self):
		for item in self:
			item.next_state_type = item.flow_line_next_id.state_type

	api.depends('flow_line_id.stage_id')

	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id', '=', self.flow_id.id))
		else:
			search_domain.append(
				('flow_id.model_id.model', '=', 'hr.migration'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

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
				
			if next_flow_line_id._get_check_ok_flow(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id):
				self.flow_line_id = next_flow_line_id
				if next_flow_line_id:
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id).ids
				
				self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'migration_id', self)
			else:
				con_user = next_flow_line_id._get_flow_users(False, False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(
					u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)

	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		if back_flow_line_id:
			if back_flow_line_id._get_check_ok_flow(self.employee_id.department_id, self.employee_id.user_id):
				self.flow_line_id = back_flow_line_id
				self.env['dynamic.flow.history'].create_history(
					back_flow_line_id, 'migration_id', self)
			else:
				raise UserError(_('Буцаах хэрэглэгч биш байна!'))

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.env['dynamic.flow.history'].create_history(
				flow_line_id, 'migration_id', self)
			self.state_type = 'cancel'
		else:
			self.state_type = 'draft'

			# raise UserError(_('Цуцлах хэрэглэгч биш байна.'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state_type = 'draft'
			self.env['dynamic.flow.history'].create_history(
				flow_line_id, 'migration_id', self)
		else:
			raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

	def send_chat_employee(self, partner_ids):
		state_type = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo(
		).get_param('web.base.url')
		action_id = self.env['ir.model.data'].id
		html = u'<b>Шилжин дэвших хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
			self.employee_id.name)
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.migration&action=%s>%s</a></b>, томилолтын хүсэлт <b>%s</b> төлөвт орлоо""" % (
				base_url, self.id, action_id, self.name, state_type)
		self.flow_line_id.send_chat(html, partner_ids)

	def send_chat_next_users(self, partner_ids):
		state_type = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo(
		).get_param('web.base.url')
		action_id = self.env['ir.model.data'].id
		html = u'<b>Шилжин дэвших хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
			self.employee_id.name)
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.migration&action=%s>%s</a></b>,томилолтын хүсэлт  <b>%s</b> төлөвт орлоо""" % (
				base_url, self.id, action_id, self.name, state_type)
		self.flow_line_id.send_chat(html, partner_ids)

	def unlink(self):
		for bl in self:
			if bl.state_type != 'draft':
				raise UserError('Ноорог төлөвтэй биш бол устгах боломжгүй.')
		return super(hrMigration, self).unlink()

	def action_sent(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code(
				'hr.migration')
		self.state_type = 'sent'

	def action_done(self):
		self.state_type = 'done'


class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	act_id = fields.Many2one(
		'hr.migration', string='Хүсэлт', ondelete='cascade', index=True)
	desc = fields.Char('Санал')


class hrMigrationLine(models.Model):
	_name = 'hr.migration.line'
	_description = 'hr migration line'

	folder_name = fields.Char('Бичиг баримт,файл, эд зүйлсийн нэр')
	data = fields.Binary('Файлаар авах шаардлагатай')
	desc = fields.Char('Хэвлэмлээр авах шаардлагатай')
	parent_id = fields.Many2one('hr.migration')


class hrMigrationLine2(models.Model):
	_name = 'hr.migration.line2'
	_description = 'hr migration line2'

	doc_meaning = fields.Char(
		'Хийгдэж байгаад дуусаагүй үлдсэн ажлуудын талаар')
	doc_number = fields.Float('Хавтас /тоо ширхэг/')
	desc = fields.Char('Тайлбар')
	parent_id = fields.Many2one('hr.migration')


class hrMigrationLine3(models.Model):
	_name = 'hr.migration.line3'
	_description = 'hr migration line3'

	employee_id = fields.Many2one('hr.employee', 'Ажилтан')
	date = fields.Date('Огноо')
	desc = fields.Char('Санал')
	parent_id = fields.Many2one('hr.migration')

	department_id = fields.Many2one(
		'hr.department', string='Хэлтэс', tracking=True)
	job_id = fields.Many2one(
		'hr.job', string='Албан тушаал', tracking=True)

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id.id
			self.job_id = self.employee_id.job_id.id

class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	migration_id = fields.Many2one('hr.migration', string='Хүсэлт', ondelete='cascade', index=True)
	desc = fields.Char('Санал')
