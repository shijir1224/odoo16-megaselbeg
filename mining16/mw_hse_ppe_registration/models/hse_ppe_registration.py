# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"


class HrJob(models.Model):
	_inherit = 'hr.job'

	hse_type = fields.Selection([('dir','Удирдлага'),
		('ingener','Инженер'),
		('manager','Менежер'),
		('driver','Жолооч'),
		('technic','Техникч')],'Төрөл')
	# user_company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)

class product_product(models.Model):
	_inherit = 'product.product'

	norm_ids = fields.One2many('norm.conf','product_id','Lines')

class NormConf(models.Model):
	_name = 'norm.conf'
	_description = u'Norm'
	_inherit = ['mail.thread']

	product_id = fields.Many2one('product.product','Product')
	type = fields.Selection([('dir','Удирдлага'),
		('ingener','Инженер'),
		('manager','Менежер'),
		('driver','Жолооч'),
		('technic','Техникч')],'Төрөл')
	day = fields.Integer('Норм хугацаа/хоног/')

class PpeName(models.Model):
	_name = 'ppe.name'
	_description = u'PPE Name'
	_inherit = ['mail.thread']

	name = fields.Char('Хамгаалах хэрэгсэл')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)

class PpeRegistration(models.Model):
	_name = 'ppe.registration'
	_description = u'PPE registration'
	_inherit = ['mail.thread']
	_rec_name = 'employee_id'

	image_1920 = fields.Image(string='Image')
	employee_image= fields.Image(related='employee_id.image_1920')
	employee_id = fields.Many2one('hr.employee', 'Ажилтан', required=True)
	job_id = fields.Many2one('hr.job','Албан тушаал', related='employee_id.job_id')
	department_id = fields.Many2one('hr.department','Хэлтэс', related='employee_id.department_id')
	branch_id = fields.Many2one('res.branch', string='Салбар', tracking=True, default=lambda self: self.env.user.branch_id)
	company_id = fields.Many2one('res.company','Компани', related='employee_id.company_id')
	user_company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id)
	phone = fields.Char('Утас', related='employee_id.work_phone')
	line_ids = fields.One2many('ppe.registration.line', 'parent_id', 'Lines', readonly=True)
	status = fields.Selection('Ажилтны төлөв', related='employee_id.employee_type', store=True)
	engagement_in_company = fields.Date(string='Компанид ажилд орсон огноо', related='employee_id.engagement_in_company')


	def line_create(self):
		ppe_line_pool =  self.env['ppe.registration.line']
		for obj in self:
			query = """SELECT 
				el.res_partner_id as partner_id,
				el.last_date as last_date,
				el.product_id as p_id,
				el.qty as qty,
				ex.id as ex_id,
				ex.name as ex_name
				FROM stock_product_other_expense_line as el 
				LEFT JOIN stock_product_other_expense ex ON ex.id = el.parent_id 
				LEFT JOIN product_product pp ON el.product_id = pp.id 
				LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id 
				LEFT JOIN product_category pc ON pt.categ_id=pc.id 
				WHERE pp.is_registration = true and el.res_partner_id=%s"""%(self.employee_id.partner_id.id)
			self.env.cr.execute(query)
			records = self.env.cr.dictfetchall()
			for record in records:
				if record['last_date']:
					end_dt = datetime.strptime(str(record['last_date']), DATE_FORMAT).date()
					norm_pool = self.env['norm.conf'].search([('product_id','=',record['p_id']),('type','=',obj.employee_id.job_id.hse_type)])
					if norm_pool:
						step = timedelta(days=norm_pool.day)
						end_dt += step
					ppe_line_id = ppe_line_pool.create({
						'employee_id': self.employee_id.id,
						'parent_id': self.id,
						'date': record['last_date'],
						'end_date': end_dt,
						'norm': norm_pool.day,
						'product_id': record['p_id'],
						'qty': record['qty'],
						'product_expense_id': record['ex_id'],
					})
				else:
					raise UserError((u'%s дугаартай шаардах хуудсанд сүүлд авсан огноо хоосон байна.')%(record['ex_name']))
		   
		return True

class PpeRegistrationLine(models.Model):
	_name = 'ppe.registration.line'
	_description = u'PPE registration line'
	_inherit = ['mail.thread']

	parent_id = fields.Many2one('ppe.registration','Parent',ondelete='cascade',)
	employee_id = fields.Many2one('hr.employee','Ажилтан',related='parent_id.employee_id')
	ppe_id = fields.Many2one('ppe.name','Нэг бүрийн хамгаалах хэрэгсэл')
	product_id = fields.Many2one('product.product', 'Нэг бүрийн хамгаалах хэрэгсэл',required=True, domain="[('categ_id', '=', 95)]")
	date = fields.Date('Олгосон огноо',required=False)
	qty = fields.Float('Тоо хэмжээ')
	end_date = fields.Date('Нормын хугацаа дуусах огноо')
	description = fields.Text('Тайлбар')
	data = fields.Binary('Файл')
	file_fname = fields.Char(string='File name')
	norm = fields.Integer('Норм')
	product_expense_id = fields.Many2one('stock.product.other.expense', 'Холбоотой шаардах')

	def send_notif_ppe_director(self):
		partner_ids = []
		res_model = self.env['ir.model.data'].search([
			('module', '=', 'ttct_hse'),
			('name', 'in', ['group_ttct_ppe_send_chat'])])
		groups = self.env['res.groups'].search(
			[('id', 'in', res_model.mapped('res_id'))], limit=1)
		base_url = self.env['ir.config_parameter'].sudo(
		).get_param('web.base.url')
		action_id = self.env['ir.model.data'].get_object_reference(
			'ttct_hse', 'ppe_registration_form_view')[1]
		html = u'<b>Ажилтан.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=ppe.registration.line&action=%s>%s</a></b> ажилтны PPE хугацаа дуусч байна!""" % (
			base_url, self.id, action_id, self.employee_id.name)
		for receiver in groups.users:
			self.env['res.users'].send_chat(html, receiver.partner_id,True)

	def _registration_not_date(self):
		today = date.today()
		if self.end_date:
			not_day = self.end_date - timedelta(days=14)
			dates = self.env['ppe.registration.line'].search([('end_date','>=',today)])
			for item in dates:
				if today == not_day:
					item.send_notif_ppe_director()
	
	def button_registration_not_date(self):
		today = date.today()
		if self.end_date:
			not_day = self.end_date - timedelta(days=14)
			dates = self.env['ppe.registration.line'].search([('end_date','>=',today)])
			for item in dates:
				if today == not_day:
					item.send_notif_ppe_director()

	@api.onchange('date')
	def onchange_date(self):
		if self.product_id:
			end_dt = datetime.strptime(str(self.date), DATE_FORMAT).date()
			norm_pool = self.env['norm.conf'].search([('product_id','=',self.product_id.id),('type','=',self.employee_id.job_id.hse_type)])
			if norm_pool:
				self.norm = norm_pool.day
				step = timedelta(days=norm_pool.day)
				end_dt += step
				self.end_date = end_dt
		else:
			raise UserError(_(u'Анхааруулга!, Барааг сонгоно уу.'))
		   

	@api.onchange('product_id')
	def onchange_product_id(self):
		if self.date:
			end_dt = datetime.strptime(str(self.date), DATE_FORMAT).date()
			norm_pool = self.env['norm.conf'].search([('product_id','=',self.product_id.id),('type','=',self.employee_id.job_id.hse_type)])
			if norm_pool:
				self.norm = norm_pool.day
				step = timedelta(days=norm_pool.day)
				end_dt += step
				self.end_date = end_dt
		else:
			raise UserError(('Анхааруулга!!! Олгосон огноог оруулна уу.'))


# Ajiltnii medeelel deer hangamj haruulahiin tuld nemev
class HrEmployee(models.Model):
	_inherit = "hr.employee"

	def create_user(self):
		res = super(HrEmployee, self).create_user()
		if self.name:
			self.env['ppe.registration'].sudo().create({
				'employee_id': self.id
		})
		return res
	
	def action_ppe_registration(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id('mw_hse_ppe_registration.action_ppe_registration_view')
		action['domain'] = [('employee_id', '=', self.id)]
		action['res_id'] = self.id
		return action
	

class ProductProduct(models.Model):
	_inherit = "product.product"

	is_registration = fields.Boolean('ХАБ-ийн хувцас хэрэглэл', default=False)