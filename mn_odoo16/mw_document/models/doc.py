# -*- coding: utf-8 -*-
import os
import datetime
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class ReceivedDocument(models.Model):
	_name = "received.document"
	_inherit = ['mail.thread']
	_description = u'Ирсэн бичиг'
	_order = 'registered_date desc'

	def name_get(self):
		res = []
		for obj in self:
			res_name = super().name_get()
			if obj.number:
				res_name = obj.number
				res.append((obj.id, res_name))
			else:
				res.append(res_name[0])
		return res
	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	
	amount=fields.Float(string='Зардлын дүн')
	number= fields.Char(string='Баримтын дугаар', size=32, required=True)
	name = fields.Many2one('document.type', string='Баримтын төрөл')
	created_date= fields.Date(string='Баримтын огноо', required=True)
	partner_id= fields.Many2one('res.partner', string='Хаанаас ирсэн', size=64)
	has_reply= fields.Selection([('Yes','Тийм'),('No','Үгүй')],'Хариутай эсэх?')
	reply_date= fields.Date(string='Хариуг илгээх огноо')
	caption= fields.Text(string='Агуулга', required=False)
	data_decide= fields.Binary(string='Шийдвэрлэхтэй холбоотой баримт')
	date_receive= fields.Date(string='Шийдвэрлэх огноо')
	pages= fields.Integer(string='Хуудасны тоо', required=False)
	registered_date= fields.Date(string='Огноо', required=True, default=fields.Date.context_today)
	department_id=fields.Many2one('hr.department', string='Хэлтэс')
	employee_id = fields.Many2many('hr.employee', 'employee_id', 'docu_id', 'empl_id', string='Ажилтан')
	employee = fields.Many2one('hr.employee',string='Ажилтан',default=_default_employee)
	job_id = fields.Many2one('hr.job',string='Албан тушаал')
	indicate= fields.Text('Тайлбар', size=256,required=False)
	decided_date= fields.Date(string='Шийдвэрлэсэн огноо')
	decided_info= fields.Char(string='Хэрхэн шийдвэрлэсэн', size=196)
	decided_caption= fields.Text(string='Шийдвэрлэхэд гарсан асуудал',size=196)
	
	data_applicant = fields.Binary('Data applicant')
	file_fname = fields.Char(string='File name')
	emp_yariltslaga = fields.Text(' ')
	send_doc_id= fields.Many2one('send.document', string='Холбоотой явсан баримт')
	send_document_id= fields.Many2many('send.document', 'received_document_doc', 'rec_id', 'received_doc_id', string='Холбоотой явсан баримтууд')
	draft_date = fields.Date(string='Буцаах огноо')
	draft_discription = fields.Text(string='Буцаах тайлбар')
	active = fields.Boolean('Active', default=True, store=True, readonly=False)
	res_company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	state= fields.Selection([('draft','Ноорог'),('send','Илгээсэн'),('accept','Хүлээн авсан'),('done','Хариу илгээсэн')],'Төлөв', default='draft', tracking=True)

	def set_number(self):
		if not self.number:
			self.name = self.env['ir.sequence'].next_by_code('contract.document.real')

	def notification_send(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('mw_document', 'action_received_document_tree_view')[1]
		html = u'<b>Ирсэн албан бичиг.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=received.document&action=%s>%s</a></b>,Ирсэн албан бичиг ирлээ!"""% (base_url,self.id,action_id,self.employee.name)
		for receiver in self.employee:
			self.env['res.users'].send_chat(html, receiver.partner_id)

	# def _send_doc_change(self):
	# 	today = datetime.now()
	# 	dates = self.env['received.document'].search(
	# 		[('reply_date', '=', today)])
	# 	for item in dates:
	# 		if item.has_reply == 'Yes':
	# 			item.write({'state': 'end'})
	# 		item.notification_send()
			
	# onchange
	@api.onchange('employee')
	def onchange_employee(self):
		self.department_id = self.employee.department_id.id
		self.job_id = self.employee.job_id.id
		

	@api.onchange('data_applicant')
	@api.depends('data_applicant','file_fname')
	def check_file_type(self):
		if self.data_applicant:
			filename,filetype = os.path.splitext(self.file_fname)

	def action_done(self):
		self.write({'state':'done'})
	
	def action_send(self):
		self.write({'state':'send'})

	def action_draft(self):
		self.write({'state':'draft'})

	def action_accept(self):
		self.write({'state':'accept'})
		
	def unlink(self):
		for bl in self:
			if bl.state !='draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(ReceivedDocument, self).unlink()

class DocumentType(models.Model):
	_name = 'document.type'
	_description = u'Document type'
	_order='name'
	
	name= fields.Char('Нэр', required=True, size=64)
		
class SendDocument(models.Model):
	_name = 'send.document'
	_description = u'Send document'
	_order = "created_at desc, document_no desc"
	_inherit = ['mail.thread']

	def document_default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	
	document_no= fields.Char(string='Дугаар')
	partner_id=fields.Many2one('res.partner',string='Хаана хэнд',size=64)
	name = fields.Many2one('document.type', string='Баримтын төрөл')
	department_id=fields.Many2one('hr.department', string='Хүсэлт илгээсэн ажилтны хэлтэс')
	company_id=fields.Many2one('res.company', string='Компани',default=lambda self: self.env.user.company_id,)
	created_date= fields.Date(string='Үүсгэсэн огноо', required=True, default=fields.Date.context_today)
	receiver=fields.Char('Receiver', size=100)
	data=fields.Binary('Хавсралт')
	pages= fields.Integer(string='Хуудасны тоо')
	caption1=fields.Text(string='Тайлбар')
	caption=fields.Text(string='Агуулга')
	has_reply=fields.Boolean(string='Хариутай эсэх?')
	created_at=fields.Date('Created at')
	registered_date= fields.Date(string=u'Албан бичгийн огноо')
	employee_id= fields.Many2one('hr.employee', string="Хүсэлт илгээсэн ажилтан", default=document_default_employee)
	job_id = fields.Many2one('hr.job',string='Хүсэлт илгээсэн ажилтны албан тушаал')
	
	is_hariu= fields.Boolean(string='Хариутай эсэх')
	date_hariu= fields.Date(string='Хариу ирүүлэх хугацаа')
	dates_hariu=fields.Date(string='Ирсэн хариуны огноо')
	number_hariu=fields.Char(string='Хариуны дугаар')
	desc_hariu= fields.Char(string='Тайлбар')
	page_number= fields.Float(string='Хуудасны дугаар')
	received_document_id= fields.Many2one('received.document', string='Холбоотой ирсэн баримт')
	received_doc_id= fields.Many2many('received.document', 'send_document_doc', 'send_id', 'send_document_id', string='Холбоотой явуулсан баримтууд')
	active = fields.Boolean('Active', default=True, store=True, readonly=False)
	in_contract = fields.Boolean('Гэрээтэй холбогдох эсэх ?')

	employee_ids = fields.Many2many('hr.employee', 'send_document_employee_rel','send_document_id', 'employee_id', string='Мэдэгдэх ажилчид')

	num_user_id = fields.Many2one('res.users', string='Хүлээн авах ажилтан', readonly=True)
	num_employee_id = fields.Many2one('hr.employee', string='Хүлээн авах ажилтан')
	num_department_id = fields.Many2one('hr.department', string='Хүлээн авсан ажилтан алба хэлтэс')
	num_job_id = fields.Many2one('hr.job', string='Хүлээн авсан ажилтан албан тушаалs')
	res_company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	state= fields.Selection([('draft','Ноорог'),('send','Илгээсэн')],'Төлөв', default='draft', tracking=True)

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id.id
			self.job_id = self.employee_id.job_id.id

	@api.onchange('num_employee_id')
	def _onchange_num_employee_id(self):
		if self.num_employee_id:
			self.num_department_id = self.num_employee_id.department_id.id
			self.num_job_id = self.num_employee_id.job_id.id

	
	def	send_doc_notif_send(self):
		partner_ids = []
		res_model = self.env['ir.model.data'].search([
			('module','=','mw_document'),
			('name','in',['group_document_manager'])])
		groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))], limit=1)		
		for group in groups:
			for receiver in group.users:
				if receiver.partner_id:
					partner_ids.append(receiver.partner_id.id)

		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference('mw_document', 'action_send_document_tree_view')[1]
		html = u'<b>Явуулсан албан бичиг.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=send.document&action=%s>%s</a></b>,Явуулсан албан бичиг ирлээ!"""% (base_url,self.id,action_id,self.created_date)

	# Явуулсан албан бичгийн хариу хугацаандаа ирээгүй бол кроноор мэдэгдэл очино хугацаа дууссан төлөвт шилжинэ.
	# def _update_send_doc_change(self):
	# 	today = datetime.now()
	# 	dates = self.env['send.document'].search(
	# 		[('date_hariu', '<', today)])
	# 	for item in dates:
	# 		if item.is_hariu == True:
	# 			item.send_doc_notif_send()

	# def action_done(self):
	# 	self.write({'state':'done'})
	
	def action_send(self):
		self.write({'state':'send'})

	def action_draft(self):
		self.write({'state':'draft'})
		
	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(SendDocument, self).unlink()
	# def action_accept(self):
	# 	self.write({'state':'accept'})
class ComplaintDocument(models.Model):
	_name = 'complaint.document'
	_description = 'Complaint Document'
	_inherit = ['mail.thread']

	def document_default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	type = fields.Selection([('out','Гадаад'),('in','Дотоод')], string='Төрөл')
	direction = fields.Selection([('application','Өргөдөл'),
							('demand','Хүсэлт'),
							('complaint','Гомдол')],string='Чиглэл')

	employee_id = fields.Many2one('hr.employee',string='Бүртгэсэн ажилтны нэр', default=document_default_employee, tracking=True)
	job_id = fields.Many2one('hr.job', string='Бүртгэсэн ажилтны албан тушаал')
	department_id = fields.Many2one('hr.department',string='Бүртгэсэн ажилтны Алба хэлтэс')
	date = fields.Date('Бүртгэсэн огноо ')
	complaint_type = fields.Selection([('1','Ажлаас чөлөөлөгдөх тухай'),('2','Ажилд орох тухай'),('3','Тэтгэмж хүсэх тухай'),('4','Урд хугацааны чөлөө хүсэх'),('5','Хүүхэд асрах чөлөө хүсэх'),('6','Хүүхэд асрах чөлөөнөөс эргэж орох')],'Өргөдлийн төрөл')
	
	complaint_type_ids = fields.Many2one('complaint.type', string='Өргөдлийн төрөл')

	complaint_employee_id = fields.Many2one('hr.employee', string='Ажилтны нэр')
	complaint_job_id = fields.Many2one('hr.job', string='Албан тушаал')
	complaint_department_id = fields.Many2one('hr.department',string='Алба хэлтэс')

	num_employee_id = fields.Many2one('hr.employee',string='Ажилтаны нэр')
	num_job_id = fields.Many2one('hr.job', string='Албан тушаал')
	num_department_id = fields.Many2one('hr.department',string='Алба хэлтэс')
	res_company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)


	complaint_received = fields.Selection([('talk','Амаар'),('phone','Утсаар'),('write','Бичгээр')],'Шийдвэрлэсэн өргөдлийн хариу илгээсэн байдал')
	complaint_idea = fields.Char(string='Өргөдлийн товч утга')
	complaint_date = fields.Date(string='Өргөдлийн огноо',default=fields.Date.context_today)
	complaint_received_date = fields.Date(string='Хүлээж авсан огноо')
	complaint_decide_date = fields.Date(string='Шийдвэрлэсэн огноо')
	complaint_description = fields.Text(string='Шийдвэрлэсэн тайлбар')
	in_decide = fields.Boolean(string='Шийдвэрлэсэн эсэх')
	reply_date = fields.Date(string='Хариу илгээсэн огноо')
	complaint_end_date = fields.Date(string='Шийдвэрлэх огноо')

	state = fields.Selection([('draft','Ноорог'),('send','Илгээсэн'),('confirm','Шийдвэрлэсэн'),('end','Хугацаа хэтэрсэн'),('archive','Архивласан'),('_end','Дууссан')],string='Төлөв',default='draft', tracking=True)

	def _end_doc_change(self):
		today = datetime.now()
		dates = self.env['complaint.document'].search(
			[('complaint_end_date', '=', today)])
		for item in dates:
			item.write({'state': 'end'})

	@api.onchange('complaint_employee_id')
	def onchange_complaint_employee_id(self):
		self.complaint_department_id = self.complaint_employee_id.department_id.id
		self.complaint_job_id = self.complaint_employee_id.job_id.id

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		self.department_id = self.employee_id.department_id.id
		self.job_id = self.employee_id.job_id.id

	@api.onchange('num_employee_id')
	def onchange_num_employee_id(self):
		self.num_department_id = self.num_employee_id.department_id.id
		self.num_job_id = self.num_employee_id.job_id.id


	def action_send(self):
		self.write({'state': 'send'})
	
	def action_draft(self):
		self.write({'state': 'draft'})

	def action_confirm(self):
		self.write({'state': 'confirm'})

	def action_end(self):
		self.write({'state': '_end'})


class ComplaintType(models.Model):
	_name = 'complaint.type'
	_description = 'Complaint type'

	name = fields.Char('Нэр')