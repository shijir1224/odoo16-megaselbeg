
# -*- coding: utf-8 -*-
import datetime
from datetime import  datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class hr_shift_plan_mine(models.Model):
	_name = 'hr.shift.plan.mine'
	_description = 'Hr Shift Plan'
	_inherit = ['mail.thread']
	


	def unlink(self):
		for bl in self:
			if bl.state_type != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(hr_shift_plan_mine, self).unlink()

	def daterange(self, start_date, end_date):
		for n in range(int ((end_date - start_date).days)+1):
			yield start_date + timedelta(n)

	def date_update(self):
		from_dt = datetime.strptime(str(self.start_date), DATE_FORMAT).date()
		step = timedelta(days=1)
		for l in self.line_ids:
			l.update({'date':from_dt})
			from_dt += step

	def line_update(self):
		for l in self.line_ids:
			if l.is_update == True:
				l.update({'name':self.shift_time_id.id,
					'end_time':self.shift_time_id.end_time,
					'start_time':self.shift_time_id.start_time,
					'lunch_start_time':self.shift_time_id.lunch_start_time,
					'lunch_end_time':self.shift_time_id.lunch_end_time,
					'is_work':self.shift_time_id.is_work,
					'compute_sum_time':self.shift_time_id.compute_sum_time,
					'compute_sum_lunch':self.shift_time_id.compute_sum_lunch,
					'start_time':self.shift_time_id.start_time,
					'is_work':self.shift_time_id.is_work})
	def all_cancel(self):
		for l in self.line_ids:
			l.update({'is_update':False})

	def all_yes(self):
		for l in self.line_ids:
			l.update({'is_update':True})

	def default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	name = fields.Char(string = u'Нэр')
	start_date = fields.Date(string = 'Эхлэх огноо', required=True)   
	line_ids=fields.One2many('hr.shift.plan.mine.line', 'shift_id', u'Мөрүүд')  
	end_date = fields.Date(string =u'Дуусах огноо')	
	employee_id = fields.Many2one('hr.employee', 'Ажилтан', required=True, tracking=True, default=default_employee,readonly=True)
	department_id = fields.Many2one('hr.department',related='employee_id.department_id',string='Хэлтэс',readonly=True)
	job_id = fields.Many2one('hr.job',related='employee_id.job_id',string='Албан тушаал',readonly=True)
	shift_time_id = fields.Many2one('hr.shift.time',string = u'Ээлж')
	is_7_2 =fields.Boolean('Амралтын өдрийг таних')
	parent_id = fields.Many2one('hr.shift.plan.mine.parent','Parent')
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил', domain='',tracking=True)

	def line_create(self):
		line_data_pool =  self.env['hr.shift.plan.mine.line']
		if self.line_ids:
			self.line_ids.unlink()
		if self.is_7_2==True:
			start_date = datetime.strptime(str(self.start_date), DATE_FORMAT)
			end_date = datetime.strptime(str(self.end_date), DATE_FORMAT)
			for single_date in self.daterange(start_date, end_date):
				if single_date.weekday()<5:
					line_line_conf = line_data_pool.create({
								'date':single_date,
								'shift_id':self.id,
								'name':self.shift_time_id.id,
								'end_time':self.shift_time_id.end_time,
								'start_time':self.shift_time_id.start_time,
								'lunch_start_time':self.shift_time_id.lunch_start_time,
								'lunch_end_time':self.shift_time_id.lunch_end_time,
								'is_work':self.shift_time_id.is_work,
								'compute_sum_time':self.shift_time_id.compute_sum_time,
								'compute_sum_lunch':self.shift_time_id.compute_sum_lunch,
								'start_time':self.shift_time_id.start_time,
								
							})
				else:
					shift_pool = self.env['hr.shift.time'].search([('is_work','=','none')],limit=1)
					line_line_conf = line_data_pool.create({
								'date':single_date,
								'shift_id':self.id,
								'name':shift_pool.id,
								'end_time':shift_pool.end_time,
								'start_time':shift_pool.start_time,
								'lunch_start_time':shift_pool.lunch_start_time,
								'lunch_end_time':shift_pool.lunch_end_time,
								'is_work':shift_pool.is_work,
								'compute_sum_time':shift_pool.compute_sum_time,
								'compute_sum_lunch':shift_pool.compute_sum_lunch,
							})
		else:
			from_dt = datetime.strptime(str(self.start_date), DATE_FORMAT).date()
			to_dt = datetime.strptime(str(self.end_date), DATE_FORMAT).date()
			step = timedelta(days=1)
			while from_dt <= to_dt:
				line_line_conf = line_data_pool.create({
					'date':from_dt,
					'shift_id':self.id,
					'name':self.shift_time_id.id,
					'end_time':self.shift_time_id.end_time,
					'start_time':self.shift_time_id.start_time,
					'lunch_start_time':self.shift_time_id.lunch_start_time,
					'lunch_end_time':self.shift_time_id.lunch_end_time,
					'is_work':self.shift_time_id.is_work,
					'compute_sum_time':self.shift_time_id.compute_sum_time,
					'compute_sum_lunch':self.shift_time_id.compute_sum_lunch,
					'start_time':self.shift_time_id.start_time,
				})
				from_dt += step


	# Flow

	def _get_dynamic_flow_line_id(self):
		return self.flow_find().id

	def _get_default_flow_id(self):
		search_domain = []
		search_domain.append(('model_id.model','=','hr.shift.plan.mine'))
		return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

	history_ids = fields.One2many('hr.shift.plan.mine.history', 'request_id', 'Түүхүүд')
	flow_id = fields.Many2one('dynamic.flow', string='Урсгалын тохиргоо', tracking=True,
		default=_get_default_flow_id, copy=False,
		domain="[('model_id.model', '=', 'hr.shift.plan.mine'),'|',('user_ids','in',[uid]),('user_ids','in',False)]", required=True)

	flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
		default=_get_dynamic_flow_line_id, copy=False,
		domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'hr.shift.plan.mine')]")

	flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True, store=True)

	stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='State', store=True)
	state_type = fields.Char(string='State type', compute='_compute_state_type', store=True)
	next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
	is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
	flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)

	branch_id = fields.Many2one('res.branch','Салбар', default=lambda self: self.env.user.branch_id)
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)
	re_desc = fields.Char('Буцаах тайлбар',tracking=True, )




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
		if not self.line_ids:
			raise UserError(u'Мөр хоосон байна!! Мөр үүсгэх товч дарна уу!!')
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.employee_id.sudo().department_id, self.employee_id.user_id):
				self.flow_line_id = next_flow_line_id
				self.env['hr.shift.plan.mine.history'].create_history(next_flow_line_id, self)	
				self.send_chat_employee1(self.sudo().employee_id.user_id.partner_id)
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
		action_id = self.env.ref('mw_timetable.action_hr_shift_plan_mine').id
		html = u'<b>Цагийн төлөвлөгөө</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.sudo().employee_id.name)
		html = u"""<span style='font-size:10pt; color:green;'><b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.shift.plan.mine&action=%s>%s</a></b> - ажилтан Цагийн төлөвлөгөө <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,self.employee_id.name,state)
		self.flow_line_id.send_chat(html, partner_ids)


	def send_chat_employee(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_timetable.action_hr_shift_plan_mine').id
		html = u'<b>Цагийн төлөвлөгөө</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.employee_id.name)
		html += u"""<b><a target="_blank"  href=%s/web#id=%s&view_type=form&model=hr.shift.plan.mine&action=%s></a></b>Цагийн төлөвлөгөө <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,state)
		self.flow_line_id.send_chat(html,partner_ids)
	
	def send_chat_employee1(self, partner_ids):
		state = self.flow_line_id.name
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_timetable.action_hr_shift_plan_mine').id
		html = u'<b>Цагийн төлөвлөгөө</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>'%(self.employee_id.name)
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.shift.plan.mine&action=%s></a></b> Цагийн төлөвлөгөө хүсэлт <b>%s</b> төлөвт орлоо"""% (base_url,self.id,action_id,state)
		self.flow_line_id.send_chat(html, partner_ids)


	def action_back_stage(self):
		if not self.re_desc:
			raise UserError(_('Буцаах тайлбар оруулна уу!'))
		back_flow_line_id = self.flow_line_id._get_back_flow_line()
		next_flow_line_id = self.flow_line_id._get_next_flow_line()
		if back_flow_line_id and next_flow_line_id:
			if next_flow_line_id._get_check_ok_flow(self.employee_id.department_id, self.employee_id.user_id):
				self.flow_line_id = back_flow_line_id
				self.env['hr.shift.plan.mine.history'].create_history(back_flow_line_id, self)
				self.back_user_leave_ids = [(4, self.env.user.id)]
				self.send_chat_employee(self.employee_id.user_id.partner_id)
			else:
				raise UserError(_('Буцаах хэрэглэгч биш байна!'))

	def action_draft_stage(self):
		flow_line_id = self.flow_line_id._get_draft_flow_line()

		if flow_line_id._get_check_ok_flow():
			self.flow_line_id = flow_line_id
		else:
			raise UserError(_('Ноорог болгох хэрэглэгч биш байна.'))

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
			item.state_type = item.flow_line_id.state_type

	def flow_find(self, domain=[], order='sequence'):
		search_domain = []
		if self.flow_id:
			search_domain.append(('flow_id','=',self.flow_id.id))
		else:
			search_domain.append(('flow_id.model_id.model','=','hr.shift.plan.mine'))
		return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1)

	@api.onchange('flow_id')
	def _onchange_flow_id(self):
		if self.flow_id:
			if self.flow_id:
				self.flow_line_id = self.flow_find().id
		else:
			self.flow_line_id = False


class HRLeaveFlowHistoryMn(models.Model):
	_name = 'hr.shift.plan.mine.history'
	_description = 'Цагийн төлөвлөгөө урсгалын түүх'
	_order = 'date desc'

	request_id = fields.Many2one('hr.shift.plan.mine','Өөрийн төлөвлөгөө', ondelete='cascade')
	user_id = fields.Many2one('res.users','Өөрчилсөн Хэрэглэгч')
	date = fields.Datetime('Огноо', default=fields.Datetime.now)
	flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв')

	def create_history(self, flow_line_id,request_id):
		self.env['hr.shift.plan.mine.history'].create({
			'request_id': request_id.id,
			'user_id': self.env.user.id,
			'date': datetime.now(),
			'flow_line_id': flow_line_id.id
			})
		
class HrShiftPlanMineLine(models.Model):
	_name = 'hr.shift.plan.mine.line'
	_description = 'Hr Shift Line'

	is_update = fields.Boolean('Update')

	date = fields.Date('Огноо')
	name = fields.Many2one('hr.shift.time',string = u'Нэр', required=True)
	number = fields.Integer(u'Дугаар')
	start_time = fields.Float(u'Эхлэх цаг')
	end_time = fields.Float(u'Дуусах цаг')
	lunch_start_time = fields.Float(u'Цайны цаг/эхлэх/')
	lunch_end_time = fields.Float(u'Цайны цаг/дуусах/')
	shift_id=fields.Many2one('hr.shift.plan.mine', 'Shift', ondelete='cascade')   
	compute_sum_time = fields.Float(string=u'Нийт цаг',store=True, readonly=True)
	compute_sum_lunch = fields.Float(string=u'Цайны цаг', store=True, readonly=True)
	
	is_work = fields.Selection([('day',u'Өдөр'),('night',u'Шөнө'),('vacation',u'Ээлжийн амралт'),('sick',u'Өвчтэй'),('leave',u'Чөлөөтэй'),('pay_leave',u'Цалинтай чөлөө'),('overtime_hour',u'Илүү цаг'),('outage',u'Сул зогсолт'),('sickness',u'Тасалсан'),('none',u'Амралт'),('in','In'),('out','Out'),('parental',u'Аавын 10 хоног'),('bereavement',u'Ажил явдал'),('business_trip',u'Томилолт'),('training',u'Сургалт'),('out_work',u'Гадуур ажилласан'),('online_work',u'Зайнаас ажилласан'),('accumlated',u'Нөхөж амрах'),('attendance',u'Орсон ирц нөхөн бүртгүүлэх'),('attendance_out',u'Гарсан ирц нөхөн бүртгүүлэх'),('resigned',u'Ажлаас гарсан'),('public_holiday',u'Нийтээр амрах өдөр')], u'Хуваарь') 

	@api.onchange('name')
	def onchange_name(self):
		self.start_time = self.name.start_time
		self.end_time = self.name.end_time
		self.lunch_start_time = self.name.lunch_start_time
		self.lunch_end_time = self.name.lunch_end_time
		self.is_work = self.name.is_work
		self.compute_sum_time = self.name.compute_sum_time
		self.compute_sum_lunch = self.name.compute_sum_lunch