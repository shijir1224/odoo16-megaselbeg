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
	_inherit = "hr.leave.mw"
	
	def _get_dynamic_flow_line_id(self):
		return self.flow_find().id
	
	history_flow_ids = fields.One2many('dynamic.flow.history', 'leave_id', 'Урсгалын түүхүүд')
	flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True, copy=False, domain="[('model_id.model','=','hr.leave.mw'),'|',('branch_ids','in',branch_id),('branch_ids','=',False)]", required=True, store=True)
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
		default=_get_dynamic_flow_line_id, copy=False,
		domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'hr.leave.mw')]")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True,default='draft')
	next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
	is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	branch_id = fields.Many2one('res.branch','Салбар', default=lambda self: self.env.user.branch_id)
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгч', compute='_compute_user_ids', store=True, readonly=True)
	confirm_all_user_ids = fields.Many2many('res.users', 'all_users_hr_leave_mw_rel',string='Батлах хэрэглэгчид бүгд', compute='_compute_all_user_ids', store=True, readonly=True)
	back_user_leave_ids = fields.Many2many('res.users','back_users_hr_leave_mw_rel', string='Буцаасан Хэрэглэгчид', store=True, readonly=True)
	
	# def check_duplicated_leave(self):
	# 	find_leave = """
	# 		SELECT 
	# 				hr.employee_id as emp_id,
	# 				hr.date_from as date_from,
	# 				hr.state_type as state_type,
	# 				hr.is_work as is_work,
	# 		FROM 
	# 				hr_leave_mw hr
	# 				LEFT JOIN hr_employee emp ON hr.employee_id = emp.id
	# 		WHERE 
	# 				hr.date_from >= '%s' AND hr.state_type != 'draft' AND hr.is_work = '%s' AND hr.employee_id = '%s'
	# 		GROUP BY 
	# 				ma.employee_id, ma.date, ma.day_shift
	# 	"""%(self.date_from, self.is_work, self.employee_id.id)
	# 	self.env.cr.execute(find_leave)
	# 	find_leave = self.env.cr.dictfetchall()
	# 	if find_leave:
	# 		raise UserError(_(u'"%s" кодтой ажилтаны %s огноонд %s хүсэлт давхардаж байна. %s!') %(self.employee_id.identification_id, self.date_from,self.state_type, hr.id))
	
	def action_send(self):
		total_year = timedelta(days=0)
		year = 0
		month = 0
		# if self.employee_id.before_shift_vac_date:
		# 	s_date = datetime.strptime(
		# 		str(self.employee_id.before_shift_vac_date),DATE_FORMAT)
		# 	e_date = datetime.strptime(str(self.date_from), DATETIME_FORMAT)
		# 	dur = e_date - s_date
		# 	total_year += dur
		# 	year = (total_year.days/365)
		# 	month = ((total_year.days-(total_year.days/365*365))/30)
		# 	months = year * 12 + month
		# 	if months < 6:
		# 		raise UserError(_('%s кодтой ажилтан өмнө жил ээлжийн амралт эдлээд 11 сар болоогүй учир ээлжийн амралт "%s" огноонд авах боломжгүй.Хүний нөөц-д хандана уу!!') %(self.employee_id.identification_id, self.date_from))
		if self.employee_id.engagement_in_company and not self.employee_id.before_shift_vac_date:
			s_date = datetime.strptime(
				str(self.employee_id.engagement_in_company),DATE_FORMAT)
			e_date = datetime.strptime(str(self.date_from), DATETIME_FORMAT)
			dur = e_date - s_date
			total_year += dur
			year = (total_year.days/365)
			month = ((total_year.days-(total_year.days/365*365))/30)
			months = year * 12 + month
			if months < 6:
				raise UserError(_(u'"%s" кодтой ажилтан өмнө жил ээлжийн амралт эдлээд 6 сар болоогүй учир ээлжийн амралт "%s" огноонд авах боломжгүй.Хүний нөөц-д хандана уу!!') %
								(self.employee_id.identification_id, self.date_from))
		# else:
		# 	raise UserError(_(
		# 					u'"%s" кодтой ажилтан өмнө жил ээлжийн амралт эдэлсэн огноог оруулна уу!!') % (self.employee_id.identification_id))

	@api.depends('flow_desc')
	def _compute_flow_id(self):
		for item in self:
			if item.flow_desc:
				item.flow_id = self.env['dynamic.flow'].search([('model_id.model','=','hr.leave.mw'),('description','=',item.flow_desc)], limit=1).id
			else:
				item.flow_id = self.env['dynamic.flow'].search([('model_id.model','=','hr.leave.mw')], order='sequence', limit=1).id

	def action_next_stage(self):
		# self.check_duplicated_leave()
		if self.is_work == 'vacation':
			self.action_send()
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id):
				self.flow_line_id = next_flow_line_id
				self.env['dynamic.flow.history'].create_history(next_flow_line_id,'leave_id', self)	
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id)
					if send_users:
						self.send_chat_next_users(send_users.mapped('partner_id'))
				return True
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id,False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
	

	def send_chat_next_users(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_timetable.open_hr_leave_mw_action').id
		html = u'<b>Цагийн хүсэлт</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.sudo().employee_id.name)
		html = u"""<span style='font-size:10pt; color:green;'><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.leave.mw&action=%s>%s</a></b> - ажилтан цагийн хүсэлт <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,self.employee_id.name,state)
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
				self.env['dynamic.flow.history'].create_history(back_flow_line_id,'leave_id', self)	
				self.back_user_leave_ids = [(4, self.env.user.id)]
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
			search_domain.append(('flow_id.model_id.model','=','hr.leave.mw'))
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
					temp = w._get_flow_users(item.branch_id,item.sudo().employee_id.department_id, item.sudo().employee_id.user_id).ids
				except:
					pass
				temp_users+=temp
			item.confirm_all_user_ids = temp_users

	@api.depends('flow_line_id','flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			temp_users = []
			users = item.flow_line_next_id._get_flow_users(item.branch_id,item.sudo().employee_id.department_id, item.sudo().employee_id.user_id)
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

	def _get_flow_users(self, branch_id=False, department_id=False, user_id=False):
		ret_users = False
		if self.type in ['fixed', 'user']:
			ret_users = self.user_ids
		elif self.type == 'group':
			ret_users = self.group_id.users
		elif self.type == 'all':
			ret_users = self.user_ids + self.group_id.users
		if ret_users and self.check_type:
			# if self.check_type == 'manager':
				# if user_id:
				# 	ret_users = ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
				# 	if self.env.user.id in ret_users.ids:
				# 		return self.env.user
				# print('-=-=-=', user_id, ret_users)
				# if not user_id:
				# 	raise ValidationError(u'Та %s урсгалд батлах эрхгүй байна !' % self.name)
				# if not ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids):
				# 	raise ValidationError(
				# 		u'"%s" төлөвийн %s Хэрэглэгч дээр менежер сонгогдоогүй байна !' % (self.name, user_id.name))
				# return ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
			if self.check_type == 'manager':
				# TODO тухайн төлөв дээр байгаа хэн ч баталж болоод байгаа учир дарлаа
				# if self.env.user.id in ret_users.ids:
				# 	return self.env.user
				if not user_id:
					raise ValidationError(u'%s Урсгалд хэрэглэгч явуулаагүй байна' % self.name)
				if not ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids):
					raise ValidationError(
						u'"%s" төлөвийн %s Хэрэглэгч дээр менежер сонгогдоогүй байна' % (self.name, user_id.name))
				return ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
			elif self.check_type == 'department':
				if not department_id:
					raise ValidationError(
						u'%s Урсгалд хэлтэс явуулаагүй байна %s %s %s' % (self.name, branch_id, department_id, user_id))
				if not ret_users.filtered(lambda r: r.id in department_id.manager_ids.ids):
					raise ValidationError(u'"%s" төлөвийн Хэлтэсийн менежер сонгогдоогүй байна' % self.name)
				return ret_users.filtered(lambda r: r.id in department_id.manager_ids.ids)
		return ret_users
class DynamicFlowHistory(models.Model):
	_inherit = 'dynamic.flow.history'

	leave_id = fields.Many2one('hr.leave.mw', 'Leave ', ondelete='cascade', index=True)
