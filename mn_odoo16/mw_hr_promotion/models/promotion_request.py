# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class PromotionRequest(models.Model):
	_name = "promotion.request"
	_description = "Promotion Request"
	_inherit = ['mail.thread']

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	company_id = fields.Many2one('res.company', string='Компани',
								 default=lambda self: self.env.user.company_id, readonly=True)
	department_id = fields.Many2one(related='employee_id.department_id', string='Хаьяалагдах нэгж')
	employee_id = fields.Many2one('hr.employee', string="Ажилтан", required=True, default=_default_employee)
	job_id = fields.Many2one(related='employee_id.job_id', string="Албан тушаал")
	job_degree = fields.Char(related='job_id.job_degree', string="Ажлын байрны зэрэглэл")
	lead_job_id = fields.Many2one(related='name_leader.job_id',string="ШУ албан тушаал")
	name_leader = fields.Many2one('hr.employee',string="ШУ нэр", )
	job_date = fields.Date(related='employee_id.engagement_in_company', string="Ажилд орсон огноо")
	ch_company_id = fields.Many2one('res.company', string="Компани")
	ch_department_id = fields.Many2one('hr.department', string='Хаьяалагдах нэгж')
	ch_job_id = fields.Many2one('hr.job', string="Албан тушаал")
	ch_job_degree = fields.Char( related="ch_job_id.job_degree", string="Ажлын байрны зэрэглэл")
	cause = fields.Text(string="Тайлбар")

	# Dynamic flow
	def _get_dynamic_flow_line_id(self):
		return self.flow_find().id

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','promotion.request'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	@api.onchange('holiday_status_id')
	def _onchange_holiday_status_id(self):
		if self.holiday_status_id.type=='non_shift':
			self.is_non = True
		else:
			self.is_non = False

	is_non = fields.Boolean('Is non', default=False)
	history_ids = fields.One2many('dynamic.flow.history', 'promotion_id', 'Түүхүүд')
	flow_id = fields.Many2one('dynamic.flow', string='Урсгал тохиргоо', track_visibility='onchange',
		default=_get_default_flow_id, copy=False,
		domain="[('model_id.model', '=', 'promotion.request')]", required=True)

	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', track_visibility='onchange', index=True,
		default=_get_dynamic_flow_line_id, copy=False,
		domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'promotion.request')]")

	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True)
	next_state_type = fields.Char(string='Next status', compute='_compute_next_state_type')
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	branch_id = fields.Many2one('res.branch','Branch', default=lambda self: self.env.user.branch_id)
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)
	
	@api.depends('flow_line_id','flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			temp_users = []
			for w in item.flow_id.line_ids:
				temp = []
				try:
					temp = w._get_flow_users(item.branch_id,item.sudo().employee_id.department_id, item.sudo().employee_id.user_id).ids
				except:
					pass
				temp_users+=temp
			item.confirm_user_ids = temp_users


	def action_next_stage(self):
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.employee_id.sudo().department_id, self.employee_id.user_id):
				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(next_flow_line_id,'promotion_id',self)	
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id,False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
	
	def send_chat_next_users(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_hr_promotion.action_promotion_request_view').id
		html = u'<b>Request of promotion </b><br/><i style="color: red">%s</i> created by an employee </br>'%(self.sudo().employee_id.name)
		html = u"""<span style='font-size:10pt; color:green;'><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=promotion.request&action=%s>%s</a></b> - request of description for employee <b>%s</b> into status"""% (base_url,self.id,action_id,self.employee_id.name,state)
		self.flow_line_id.send_chat(html, partner_ids)

	
	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_hr_promotion.action_promotion_request_view').id
		html = u'<b>Request of promotion </b><br/><i style="color: red">%s</i> created by an employee </br>'%(self.employee_id.name)
		html += u"""<b><a target="_blank"  href=%s/web#id=%s&view_type=form&model=promotion.request&action=%s></a></b>Request of description is returned <b>%s</b> into status"""% (base_url,self.id,action_id,state)
		self.flow_line_id.send_chat(html,partner_ids)

	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if back_flow_line_id and next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.employee_id.department_id, self.employee_id.user_id):
				self.flow_line_id = back_flow_line_id
				self.env['dynamic.flow.history'].create_history(back_flow_line_id,'promotion_id', self)
				self.send_chat_employee(self.employee_id.user_id.partner_id)
			else:
				raise UserError(_('Буцаах хэрэглэгч биш байна!'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
		else:
			raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

	@api.depends('flow_line_next_id.state_type')
	def _compute_next_state_type(self):
		for item in self:
			item.next_state_type = item.flow_line_next_id.state_type

	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id

	@api.depends('flow_line_id')
	def _compute_state_type(self):
		for item in self:
			item.state_type = item.flow_line_id.state_type

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		else:
			search_domain.append(('flow_id.model_id.model','=','promotion.request'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find().id
		else:
			self.flow_line_id = False
			
class DynamicFlowHistory(models.Model):
    _inherit = 'dynamic.flow.history'

    promotion_id = fields.Many2one('promotion.request', 'Promotion request', ondelete='cascade', index=True)
