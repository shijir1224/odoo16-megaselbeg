
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError


class DisciplineAction(models.Model):
	_name ='hse.discipline.action'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_description = 'ХАБ Зөрчлийн хуудас'

	@api.model
	def _default_name(self):
		return self.env['ir.sequence'].next_by_code('hse.discipline.action')
	
	def _get_dynamic_flow_line_id(self):
		return self.flow_find()

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','hse.discipline.action'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Урсгал Төлөв', tracking=True, index=True, default=_get_dynamic_flow_line_id, copy=False, domain="[('id','in',visible_flow_line_ids)]")
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True, default=_get_default_flow_id, copy=True, domain="[('model_id.model', '=', 'hse.discipline.action')]", index=True)
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)	
	state = fields.Char(string='Төлөв', compute='_compute_state', store=True, index=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True, index=True)
	is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
	history_ids = fields.One2many('hse.discipline.history', 'hse_id', 'Түүхүүд')
	name = fields.Char(string='Дугаар', copy=False, default=_default_name, readonly=True)
	branch_id = fields.Many2one('res.branch', string='Салбар', tracking=True, default=lambda self: self.env.user.branch_id, domain="[('company_id','=',company_id)]")
	employee_id = fields.Many2one('hr.employee', string='Ажилтны овог нэр')
	department_id = fields.Many2one('hr.department', related='employee_id.department_id', string='Харьяалагдах нэгж', readonly=True, store=True)
	employee_position = fields.Many2one('hr.job', related='employee_id.job_id', string='Албан тушаал', readonly=True, store=True)
	prev_discipline_check = fields.Boolean(string='Шийтгэл авсан эсэх?', default=False)
	prev_discipline_type = fields.Char('Өмнөх шийтгэлийн төрөл', readonly=True)
	prev_discipline_date = fields.Char('Өмнөх шийтгэлийн хугацаа', readonly=True)
	prev_discipline_datetime = fields.Date('Өмнөх шийтгэлийн огноо', default=fields.Date.context_today, readonly=True)
	now_discipline_date = fields.Datetime('Зөрчил гарсан огноо/цаг')
	discipline_location = fields.Char('Зөрчил гарсан байршил')
	discipline_type = fields.Many2many('hse.discipline.type', string='Зөрчлийн төрөл')
	discipline_level = fields.Selection([('a', 'Хөнгөн'),('b', 'Ноцтой'),('c', 'Маш ноцтой')], string='Зөрчлийн түвшин')
	discipline_content = fields.Text(string='Зөрчлийн агуулга')
	punishment_type = fields.Selection([('a', 'Аман сануулга'),('b', 'Бичгэн сануулга'),('c', 'Цалин бууруулах'),('d', 'Ажлаас чөлөөлөх')], string='Шийтгэлийн төрөл')
	punishment_time = fields.Selection([('3', '3 сар'),('6', '6 сар'),('9', '9 сар'),('12', '12 сар')], string='Шийтгэлийн хугацаа')
	taniltssan_employee = fields.Many2one('hr.employee', related='employee_id', string='Танилцсан ажилтан', readonly=True)
	taniltssan_employee_date = fields.Date('танилцсан огноо', required=True, default=fields.Date.context_today)
	shuud_udirdlaga = fields.Many2one('hr.employee', related='employee_id.coach_id', string='Харьяалагдах нэгжийн шууд удирдлага', readonly=True, store=True)
	shuud_udirdlaga_date = fields.Date('Шууд удирдлага огноо', required=True, default=fields.Date.context_today)
	hr_employee = fields.Many2one('hr.employee', string='Хүний нөөцийн ажилтан', readonly=True)
	hr_employee_date = fields.Date('ХН огноо', required=True, default=fields.Date.context_today)
	heltes_udirdlaga = fields.Many2one('hr.employee', string='Хэлтсийн удирдлага')
	heltes_udirdlaga_date = fields.Date('Хэлтэс огноо', required=True, default=fields.Date.context_today)
	discipline_categ = fields.Many2one('discipline.categ', string='Зөрчлийн ангилал')
	attachment_ids = fields.Many2many('ir.attachment', string=u'Зөрчлийн хуудас/Баталгаажсан/')
	create_user_id = fields.Many2one('res.users', string=u'Үүсгэсэн ажилтан', required=True, default=lambda self: self.env.user, readonly=True)
	discipline_attachment_ids = fields.Many2many('ir.attachment', 'discipline_attachment_rel', 'discipline_id', string=u'Зөрчлийн зураг')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)


	def action_done(self):
		self.write({'state': 'done'})
	
	def action_cancel(self):
		self.write({'state': 'cancel'})

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	@api.depends('flow_id.line_ids', 'flow_id.is_amount')
	def _compute_visible_flow_line_ids(self):
		for item in self:
			if item.flow_id:
				item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'hse.discipline.action')])
			else:
				item.visible_flow_line_ids = []

	@api.depends('flow_line_id')
	def _compute_state(self):
		for item in self:
			item.state = item.flow_line_id.state_type

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		search_domain.append(('flow_id.model_id.model','=','hse.discipline.action'))
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
				self.env['hse.discipline.history'].create_history(next_flow_line_id, self)

				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(False, False)
					if send_users:
						html = self.flow_line_id.send_chat_html(self)
						self.flow_line_id.send_chat(html, send_users.mapped('partner_id'))
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
				self.env['hse.discipline.history'].create_history(back_flow_line_id, self)
				
			else:
				raise UserError('Та буцаах хэрэглэгч биш байна.')

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow(False, False):
			self.flow_line_id = flow_line_id
			self.env['hse.discipline.history'].create_history(flow_line_id, self)
			self.state='cancel'
			return self.action_cancel()
		else:
			raise UserError(_('Та цуцлах хэрэглэгч биш байна.'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			self.state='draft'
			self.env['hse.discipline.history'].create_history(flow_line_id, self)
		else:
			raise UserError(_('Та ноороглох хэрэглэгч биш байна.'))

	def unlink(self):
		for s in self:
			if s.flow_line_id.state_type != 'draft':
				raise UserError('Устгах боломжгүй зөвхөн ноорог төлөвтэйг устгана!')
		return super(DisciplineAction, self).unlink()