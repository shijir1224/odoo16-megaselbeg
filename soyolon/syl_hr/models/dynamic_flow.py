import logging
from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError
import logging
import datetime
from datetime import date, datetime, timedelta

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

class HrLeaveRequestMw(models.Model):
	_inherit = "discipline.document"
	
	def _get_dynamic_flow_line_id(self):
		return self.flow_find().id
	
	history_flow_ids = fields.One2many('dynamic.flow.history', 'discipline_id', 'Урсгалын түүхүүд')
	flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True, copy=False, domain="[('model_id.model','=','discipline.document'),'|',('branch_ids','in',branch_id),('branch_ids','=',False)]", required=True, store=True)
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
		default=_get_dynamic_flow_line_id, copy=False,
		domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'discipline.document')]")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True,default='draft')
	next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
	is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	branch_id = fields.Many2one('res.branch','Салбар', default=lambda self: self.env.user.branch_id)
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгч', compute='_compute_user_ids', store=True, readonly=True)
	confirm_all_user_ids = fields.Many2many('res.users', 'all_users_discipline_doc_mw_rel',string='Батлах хэрэглэгчид бүгд', compute='_compute_all_user_ids', store=True, readonly=True)
	back_user_discipline_ids = fields.Many2many('res.users','back_users_discipline_doc_mw_rel', string='Буцаасан Хэрэглэгчид', store=True, readonly=True)
	


	@api.depends('flow_desc')
	def _compute_flow_id(self):
		for item in self:
			if item.flow_desc:
				item.flow_id = self.env['dynamic.flow'].search([('model_id.model','=','discipline.document'),('description','=',item.flow_desc)], limit=1).id
			else:
				item.flow_id = self.env['dynamic.flow'].search([('model_id.model','=','discipline.document')], order='sequence', limit=1).id

	def action_next_stage(self):
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id):
				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(next_flow_line_id,'discipline_id', self)	
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users_syl(self.branch_id,self.sudo().employee_id.department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
				return True
			else:
				con_user = next_flow_line_id._get_flow_users_syl(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
			

	def send_chat_next_users(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_hr_discipline.action_discipline_document_tree_view').id
		html = u'<b>Сахилгийн шийтгэл</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.sudo().employee_id.name)
		html = u"""<span style='font-size:10pt; color:green;'><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=discipline.document&action=%s>%s</a></b> - ажилтан сахилгын шийтгэл <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,self.employee_id.name,state)
		self.flow_line_id.send_chat(html, partner_ids)

	def action_cancel_stage(self):
		flow_line_id = self.flow_line_id._get_cancel_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			return True
		else:
			raise UserError(_('Цуцлах хэрэглэгч биш байна.'))
		
	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		if back_flow_line_id:
			if back_flow_line_id._get_check_ok_flow():
				self.flow_line_id = back_flow_line_id
				self.env['dynamic.flow.history'].create_history(back_flow_line_id,'discipline_id', self)	
				self.back_user_discipline_ids = [(4, self.env.user.id)]
				return True
			else:
				raise UserError(_('Буцаах хэрэглэгч биш байна!'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()
		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
			return True
		else:
			raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		else:
			search_domain.append(('flow_id.model_id.model','=','discipline.document'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

	@api.depends('flow_line_id.is_not_edit')
	def _compute_is_not_edit(self):
		for item in self:
			item.is_not_edit = item.flow_line_id.is_not_edit

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
			if item.flow_line_id:
				item.state_type = item.flow_line_id.state_type
			else:
				item.state_type = 'draft'

	@api.depends('flow_line_id','flow_id.line_ids')
	def _compute_all_user_ids(self):
		for item in self:
			temp_users = []
			for w in item.flow_id.line_ids:
				temp = []
				try:
					temp = w._get_flow_users_syl(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id).ids
				except:
					pass
				temp_users+=temp
			item.confirm_all_user_ids = temp_users

	@api.depends('flow_line_id','flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			temp_users = []
			users = item.flow_line_next_id._get_flow_users_syl(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id, self.sudo().employee_id.job_id)
			temp_users = users.ids if users else []
			item.confirm_user_ids = [(6,0,temp_users)]

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find().id
		else:
			self.flow_line_id = False
class DynamicFlowLine(models.Model):
	_inherit = 'dynamic.flow.line'

	check_type = fields.Selection([('department', 'Хэлтэсийн менежер'), ('branch', 'Салбар менежер'), ('manager', 'Тухайн хүний менежер'),('job_manager', 'АБ шууд удирдлага')],string='Шалгах төрөл')
	# job дээр батлах удирдлага тохируулах шаардлага гарсан
	def _get_flow_users_syl(self, branch_id=False, department_id=False, user_id=False, job_id=False):
		ret_users = False
		if self.type in ['fixed', 'user']:
			ret_users = self.user_ids
		elif self.type == 'group':
			ret_users = self.group_id.users
		elif self.type == 'all':
			ret_users = self.user_ids + self.group_id.users
		print('\n\n=jret_usersob_id=',ret_users,job_id)
		if ret_users and self.check_type:
			
			if self.check_type == 'manager':
				if user_id:
					ret_users = ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
					if self.env.user.id in ret_users.ids:
						return self.env.user
				if not user_id:
					raise ValidationError(u'Та %s урсгалд батлах эрхгүй байна !' % self.name)
				if not ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids):
					raise ValidationError(
						u'"%s" төлөвийн %s Хэрэглэгч дээр менежер сонгогдоогүй байна !' % (self.name, user_id.name))
				return ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
			elif self.check_type == 'department':
				if not department_id:
					raise ValidationError(
						u'%s Урсгалд хэлтэс явуулаагүй байна %s %s %s' % (self.name, branch_id, department_id, user_id))
				if not ret_users.filtered(lambda r: r.id in department_id.manager_ids.ids):
					raise ValidationError(u'"%s" төлөвийн Хэлтэсийн менежер сонгогдоогүй байна' % self.name)
				return ret_users.filtered(lambda r: r.id in department_id.manager_ids.ids)
			elif self.check_type == 'job_manager':
				print('\n\n=job_id=',job_id)
				if not job_id:
					raise ValidationError(
						u'%s Урсгалд албан тушаал явуулаагүй байна %s %s %s' % (self.name, branch_id, job_id, user_id))
				if not ret_users.filtered(lambda r: r.id in job_id.interviewer_ids.ids):
					raise ValidationError(u'"%s" төлөвийн албан тушаал дээр удирдлага сонгогдоогүй байна' % self.name)
				return ret_users.filtered(lambda r: r.id in job_id.interviewer_ids.ids)
			print('\n\n======',self.check_type,ret_users,job_id.interviewer_ids.ids)
		return ret_users
	
class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	discipline_id = fields.Many2one('discipline.document', ' discipline', ondelete='cascade', index=True)
