
from urllib.parse import uses_fragment
from odoo import  api, fields, models

from datetime import datetime, timedelta

class HseLandPermitRegistration(models.Model):
	_name ='hse.land.permit.registration'
	_description = 'Hse Land Permit Registration'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	state = fields.Selection([('draft', 'Ноорог'),('sent', 'Илгээсэн'),('done', 'Дууссан')], 'Төлөв', readonly=True, default='draft')
	name = fields.Char(string='Нэр', tracking=True)
	create_date = fields.Date(string='Үүсгэсэн огноо', default=fields.Date.context_today, tracking=True, required=True)
	company_id = fields.Many2one('res.partner', string=' Компани', tracking=True)
	land_type = fields.Selection([
		('topsoil stripping','Шимт хөрс  хуулах'),
		('earthquake','Газар хөндөх'),
  		('topsoil_loosening','Шимт хөрс актлах')], string='Зөвшөөрлийн төрөл', required=True, tracking=True)
	date = fields.Date(string='Зөвшөөрөл авсан', default=fields.Date.context_today, tracking=True, required=True)
	end_date = fields.Date(string='Дуусах огноо', tracking=True, required=True)
	unloading_stockpile = fields.Char(string='Буулгах овоолгын дугаар')
	earthquake_location = fields.Char(string='Газар хөндөх зөвшөөрлийн байрлал', )
	employee_id = fields.Many2one('hr.employee', string='Зөвшөөрөл авсан ажилтан', tracking=True)
	job_id = fields.Many2one(related='employee_id.job_id', string="Албан тушаал")
	respon_employee_id = fields.Many2one('hr.employee', string="Хариуцсан ажилтан", tracking=True, required=True)
	respon_job_id = fields.Many2one(related='respon_employee_id.job_id', string="Хариуцсан ажилтны албан тушаал")
	mail_line = fields.One2many('hse.land.permit.mail.line', 'permit_id', 'Майлын мөр')
	mail_text = fields.Text('Майл текст')
	attachment_ids_1 = fields.Many2many('ir.attachment', 'hse_land_ir_attachment_rel_1', 'land_id', 'attach_id', string='Хавсралт 1', copy=False)
	attachment_ids_2 = fields.Many2many('ir.attachment', 'hse_land_ir_attachment_rel_2', 'land_id', 'attach_id', string='Хавсралт 2', copy=False)


	def action_to_done(self):
		self.write({'state': 'done'})
		x = self.env['hr.employee'].search([('user_id','=',self.env.user.id)]).id
		self.write({'respon_employee_id': x})
		
	def action_to_draft(self):
		self.write({'state': 'draft'})

	def action_to_sent(self):
		self.write({'state': 'sent'})

	def action_to_sent_mail(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse_dangerous_waste', 'action_hse_land_permit_registration')[1]
		html = u'<b>Газрын зөвшөөрөл.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.land.permit.registration&action=%s>%s</a></b>,Газар хөндөх зөвшөөрөл ирлээ!"""% (base_url,self.id,action_id,self.name)
		if self.respon_employee_id:
			self.env.user.send_chat(html,[self.respon_employee_id.partner_id], with_mail=True, attachment_ids=self.attachment_ids_1.id)
			self.write({'state': 'sent'})

class HseLandPermitMailLine(models.Model):
	_name ='hse.land.permit.mail.line'
	_description = 'Mail line'
   
	permit_id = fields.Many2one('hse.land.permit.registration','Permit ID', required=True, ondelete='cascade')
	mail = fields.Char('Майл', required=True)
