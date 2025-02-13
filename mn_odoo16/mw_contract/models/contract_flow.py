

import datetime
from datetime import  datetime,timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import numpy as np

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

class ContractFlowHistory(models.Model):
	_name = 'contract.real.flow.history'
	_description = 'contract real flow history'
	_order = 'date desc'

	request_id = fields.Many2one('contract.document.real','Хүсэлт', ondelete='cascade')
	user_id = fields.Many2one('res.users','Өөрчилсөн Хэрэглэгч')
	date = fields.Datetime('Огноо', default=fields.Datetime.now)
	flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв')
	cont_history_not_date = fields.Datetime('Мэдэгдэл ирэх огноо', compute = "_compute_date")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', 'Дараагийн төлөв')
	duration =fields.Float('Төлөв шилжсэн хугацаа')
	duration_ch =fields.Char('Төлөв шилжсэн хугацаа')

	@api.depends('date')
	def _compute_date(self):
		delta = timedelta(days=2)
		for item in self:
			if item.date:
				item.cont_history_not_date = item.date + delta
			return item.cont_history_not_date

	def create_history(self, flow_line_id,request_id,duration,duration_ch):
		self.env['contract.real.flow.history'].create({
			'request_id': request_id.id,
			'user_id': self.env.user.id,
			'date': datetime.now(),
			'flow_line_id': flow_line_id.id,
			'duration':duration,
			'duration_ch':duration_ch
			})
		

class ContractDocumentReal(models.Model):
	_inherit = "contract.document.real"
	

# Dynamic flow
	def _get_dynamic_flow_line_id(self):
		return self.flow_find().id
	
	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','contract.document.real'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	
	next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
	state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type',store=True)
	is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
	flow_id = fields.Many2one('dynamic.flow', string='Гэрээний урсгал тохиргоо', tracking=True,
		compute='compute_flow_id', default=_get_default_flow_id, copy=True, domain="[('model_id.model', '=', 'contract.document.real'),'|',('branch_ids','in',[branch_id]),('branch_ids','in',False)]",store=True)
	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
		default=_get_dynamic_flow_line_id, copy=True, domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'contract.document.real')]")
	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id',  store=True)
	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
	branch_id = fields.Many2one('res.branch','Салбар', default=lambda self: self.env.user.branch_id)
	history_ids = fields.One2many('contract.real.flow.history', 'request_id', 'Түүхүүд')
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)
	back_user_ids = fields.Many2many('res.users','back_users_cont_rel', string='Буцаасан Хэрэглэгчид', store=True, readonly=True)

	@api.depends('flow_line_id')
	def _compute_state_type(self):
		for item in self:
			if item.flow_line_id:
				item.state_type = item.flow_line_id.state_type
			else:
				item.state_type = 'draft'


	@api.depends('payment_sum')
	def compute_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','contract.document.real'))
		search_domain.append(('branch_ids','in',[self.branch_id.id]))
		flow = self.env['dynamic.flow'].search(search_domain, order='sequence')
		for item in self:
			for i in flow:
				f=False
				if i.is_amount == True:
					if i.amount_price_max <= item.payment_sum:
						f = i.id
					elif i.amount_price_min >= item.payment_sum:
						f = i.id
				else:
					f=i.id
				item.flow_id = f

	@api.depends('flow_line_id.is_not_edit')
	def _compute_is_not_edit(self):
		for item in self:
			item.is_not_edit = item.flow_line_id.is_not_edit


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

	@api.depends('flow_line_next_id.state_type')
	def _compute_next_state_type(self):
		for item in self:
			item.next_state_type = item.flow_line_next_id.state_type


	@api.depends('flow_line_id.stage_id')
	def _compute_flow_line_id_stage_id(self):
		for item in self:
			item.stage_id = item.flow_line_id.stage_id


	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		else:
			search_domain.append(('flow_id.model_id.model','=','contract.document.real'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)


	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find()
		else:
			self.flow_line_id = False

	def set_number(self):
		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('contract.document.real')

	def _set_duration(self):
		days=0
		hours=0
		minutes=0
		duration=0
		if self.history_ids:
			if self.history_ids[0].date:
				from_d = datetime.strptime(str(self.history_ids[0].date), DATETIME_FORMAT)
				today = datetime.strptime(str(datetime.now()), DATETIME_FORMAT)
				time_delta = today - from_d
				duration_o = time_delta.total_seconds()
				duration = divmod(duration_o, 60)[0]
				seconds=time_delta.days * 8 * 3600 + time_delta.seconds
				minutes, seconds = divmod(seconds, 60)
				hours, minutes = divmod(minutes, 60)
				days, hours = divmod(hours, 8)
		return days,hours,minutes,duration

	def action_next_stage(self):
		confirm_usernames=''
		if self.state_type == 'chief':
			self.set_number()
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id):
				self.flow_line_id = next_flow_line_id	
				days,hours,minutes,duration = self._set_duration()
				duration_ch = str(days) + 'өдөр' + '   ' + str(hours) + 'цаг' + '   ' + str(minutes) + '   ' + 'минут'
				self.env['contract.real.flow.history'].create_history(next_flow_line_id, self,duration,duration_ch)		
				if self.flow_line_next_id:
					send_users = self.flow_line_next_id._get_flow_users(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id)
					# if send_users:
					# 	self.send_chat_next_users(send_users.mapped('partner_id'))
			else:
				con_user = next_flow_line_id._get_flow_users(self.branch_id,False)
				confirm_usernames = ''
				if con_user:
					confirm_usernames = ', '.join(con_user.mapped('display_name'))
				raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
	

	
	def action_back_stage(self):
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if back_flow_line_id:
			if next_flow_line_id:
				if next_flow_line_id._get_check_ok_flow(self.employee_id.department_id, self.employee_id.user_id):
					self.flow_line_id = back_flow_line_id
					# History uusgeh
					days,hours,minutes,duration = self._set_duration()
					duration_ch = str(days) + 'өдөр' + '   ' + str(hours) + 'цаг' + '   ' + str(minutes) + '   ' + 'минут'
					self.env['contract.real.flow.history'].create_history(next_flow_line_id, self,duration,duration_ch)		
					self.back_user_ids = [(4, self.env.user.id)]
					# self.send_chat_employee(self.employee_id.user_id.partner_id)
				else:
					raise UserError(_('Буцаах хэрэглэгч биш байна!'))
			else:
				raise UserError(_('Батлагдсан гэрээ тул админд хандаж буцаалгана уу!'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()

		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
		else:
			raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))


	def _get_flow_users(self, branch_id=False, department_id=False, user_id=False):
		ret_users = False
		if self.type in ['fixed', 'user']:
			ret_users = self.user_ids
		elif self.type == 'group':
			ret_users = self.group_id.users
		elif self.type == 'all':
			ret_users = self.user_ids + self.group_id.users
		if ret_users and self.check_type:
			if self.check_type == 'manager':
				if user_id:
					ret_users = ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
					if self.env.user.id in ret_users.ids:
						return self.env.user
				if not user_id:
					raise (u'Та %s урсгалд батлах эрхгүй байна !' % self.name)
				if not ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids):
					raise ValidationError(
						u'"%s" төлөвийн %s Хэрэглэгч дээр менежер сонгогдоогүй байна !' % (self.name, user_id.name))
				return ret_users.filtered(lambda r: r.id in user_id.manager_user_ids.ids)
		return ret_users


	# def send_chat_employee(self, partner_ids):
	# 	state = self.flow_line_id.name
	# 	base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
	# 	action_id = self.env.ref('mw_contract.action_contract_document_real_view').id
	# 	html = u'<b>Гэрээний бүртгэл</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.employee_id.name)
	# 	html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=contract.document.real&action=%s>%s</a></b>,  гэрээний бүртгэл <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,self.contract_name,state)
	# 	self.flow_line_id.send_chat(html, partner_ids,True)

	# def send_chat_next_users(self, partner_ids):
	# 	state = self.flow_line_id.name
	# 	base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
	# 	action_id = self.env.ref('mw_contract.action_contract_document_real_view').id
	# 	html = u'<b>Гэрээний бүртгэл</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.employee_id.name)
	# 	html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=contract.document.real&action=%s>%s</a></b>,  гэрээний бүртгэл  <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,self.contract_name,state)
	# 	self.flow_line_id.send_chat(html, partner_ids,True)
	
	
	# onchange 
	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.job_id = self.employee_id.job_id.id
			self.department_id = self.employee_id.department_id.id
			self.l_name = self.employee_id.last_name[:1] if self.employee_id.last_name else self.employee_id.last_name

	@api.onchange('partner_id') 
	def _onchange_type(self):
		self.company_type1 = self.partner_id.company_type
		self.partner_register = self.partner_id.vat
		

	def action_end_notification_send(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_contract.action_contract_document_real_view').id
		html = u'<b>Гэрээний бүртгэл.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=contract.document.real&action=%s>%s</a></b>- нэртэй гэрээг дүгнэнэ үү!"""% (base_url,self.id,action_id,self.contract_name)
		for receiver in self.employee_id:
			self.env['res.users'].send_chat(html, receiver.partner_id,True)
		


	def action_act_notification_send(self):
		partner_ids = []
		for receiver in self.employee_id:
			if receiver.partner_id:
				partner_ids.append(receiver.partner_id.id)
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_contract.action_contract_document_real_view').id
		html = u'<b>Гэрээний бүртгэл.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=contract.document.real&action=%s>%s</a></b>- нэртэй батлагдсан гэрээг оруулна уу!"""% (base_url,self.id,action_id,self.contract_name)
		for receiver in self.employee_id:
			self.env['res.users'].send_chat(html, receiver.partner_id,True)