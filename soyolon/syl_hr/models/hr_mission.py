# -*- coding: utf-8 -*-
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class HrMission(models.Model):
	_inherit = 'hr.mission'

	

	sequence = fields.Char('Дугаар')
	date_come = fields.Datetime(string='Явах огноо,цаг', tracking=True)
	attach_file = fields.Binary(string='Хавсралт')
	line_ids = fields.One2many('hr.mission.line','parent_id',string='Гүйцэтгэх ажил')
	technic_id = fields.Many2one('technic.equipment',string='Машин')
	cost_desc = fields.Char('Албан томилолтын зардлын лимит"-ээс хэтэрсэн эсэх, тийм бол үндэслэлийг тодорхой бичнэ үү')
	done_work = fields.Char('Хийж гүйцэтгэсэн ажлууд', tracking=True)
	result = fields.Char('Хүрсэн үр дүн', tracking=True)
	done_desc= fields.Char('Нэмэлт тэмдэглэл', tracking=True)
	hr_employee_id = fields.Many2one('hr.employee',string='Томилолтын удирдамжийг хүлээн авсан')
	hr_melen = fields.Char('hr melen')
	emp_melen = fields.Char('emp melen')
	pr_attach = fields.Many2many('ir.attachment', 'hr_mission_pr_attach_rel', 'item_id', 'mi_attach_id',
										  string='Удирдамж')
	
	
	partner_ids = fields.Many2many('res.partner', string='Гадаад ажилчид')
	confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгч', compute='_compute_user_ids', store=True, readonly=True)
	
	confirm_all_user_ids = fields.Many2many('res.users', 'all_users_hr_mission_rel',string='Батлах хэрэглэгчид бүгд', compute='_compute_all_user_ids', store=True, readonly=True)

	@api.depends('flow_line_id','flow_id.line_ids')
	def _compute_user_ids(self):
		for item in self:
			temp_users = []
			users = item.flow_line_next_id._get_flow_users(item.branch_id,item.sudo().employee_id.department_id, item.sudo().employee_id.user_id)
			temp_users = users.ids if users else []
			item.confirm_user_ids = [(6,0,temp_users)]

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


	def write(self, values):
		res = super(HrMission,self).write(values)
		no1 = 0
		no2 = 0
		no3 = 0
		if not self.sequence:
			self.sequence = self.env['ir.sequence'].next_by_code('hr.mission')
		for line in self.line_ids:
			no1 +=1
			line.sequence = no1
		for line in self.mission_ids:
			no2 +=1
			line.sequence = no2
		for line in self.cost_ids:
			no3 +=1
			line.sequence = no3
		return res

		
	# def action_next_stage(self):
	# 	res = super(HrMission, self).action_next_stage()
	# 	next_flow_line_id = self.flow_line_id._get_next_flow_line()
	# 	if next_flow_line_id:
	# 		if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
	# 			check_next_flow_line_id = next_flow_line_id
	# 			while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
	# 				temp_stage = check_next_flow_line_id._get_next_flow_line()
	# 				if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
	# 					break
	# 				check_next_flow_line_id = temp_stage
	# 			next_flow_line_id = check_next_flow_line_id
				
	# 		if next_flow_line_id._get_check_ok_flow(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id):
				
	# 			self.flow_line_id = next_flow_line_id
	# 			if next_flow_line_id.state_type == 'sent':
	# 				self.action_sent()
	# 			if self.flow_line_id.state_type == 'done':
	# 				self.action_done()
	# 			# if next_flow_line_id:
	# 				# send_users = self.flow_line_next_id._get_flow_users(self.branch_id,self.employee_id.sudo().department_id, self.sudo().employee_id.user_id).ids
	# 				# if send_users:
	# 				# 	self.send_chat_next_users(send_users.mapped('partner_id'))
	# 			# History uusgeh
	# 			self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'mission_id', self)
	# 		else:
	# 			con_user = next_flow_line_id._get_flow_users(False, False)
	# 			confirm_usernames = ''
	# 			if con_user:
	# 				confirm_usernames = ', '.join(con_user.mapped('display_name'))
	# 			raise UserError(
	# 				u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)
	# 	return res
			
	@api.onchange('hr_employee_id')
	def onchange_hr_employee_id(self):
		if self.hr_employee_id:
			self.hr_melen = self.hr_employee_id.last_name[:1]
			
	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.emp_melen = self.employee_id.last_name[:1]
		

class HrMissionline(models.Model):
	_name = 'hr.mission.line'

	employee_id = fields.Many2one('hr.employee',string='Гүйцэтгэх ажилтан')
	date = fields.Date(string='Гүйцэтгэх хугацаа')
	period = fields.Char(string='Гүйцэтгэх хугацаа')
	mission = fields.Char(string='Томилолтоор гүйцэтгэх ажил үүрэг')
	parent_id = fields.Many2one('hr.mission',string='Mission')
	sequence = fields.Integer('Дугаарлалт')
	parent_id = fields.Many2one('hr.mission',string='Parent')
	employee_ids = fields.Many2many('hr.employee', string='Ажилчид')

	

class MissionEmployee(models.Model):
	_inherit = 'mission.employee'
	 
	department_id = fields.Many2one('hr.department',string='Харьяалагдах алба нэгж')
	approve = fields.Boolean(string='Зөвшөөрөл',default=False)
	melen = fields.Char('melen')
	sequence = fields.Integer('Дугаарлалт')
	
	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.melen = self.employee_id.last_name[:1]
	
	

class MissionCostLine(models.Model):
	_inherit = 'mission.cost.line'
	 
	norm = fields.Float(string='Норм/удаа',default=1)
	sequence = fields.Integer('Дугаарлалт')
	amount = fields.Float(string='Нэгж дүн')
	count = fields.Integer(string='Тоо хэмжээ')
	sum = fields.Float(string='Дүн', digits=(2, 0))
	parent_id = fields.Many2one('hr.mission',string='Parent')
		
	@api.onchange('amount','count','cost_name_id','norm')
	def sum_amount(self):
		if self.norm>0:
			if self.cost_name_id.is_norm==True:
				self.sum = round(((self.amount * self.count * self.norm)),1)
			else:
				self.sum = round((self.amount * self.count * self.norm),1)
		else:   
			self.sum = round((self.amount * self.count),1)
	
	
class CostName(models.Model):
	_inherit = 'cost.name'
	
	is_norm = fields.Boolean('Норм')
