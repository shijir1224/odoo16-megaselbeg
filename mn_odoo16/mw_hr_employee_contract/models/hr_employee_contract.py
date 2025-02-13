
# -*- coding: utf-8 -*-


from odoo.exceptions import UserError
from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from dateutil import relativedelta
import logging
from odoo.exceptions import UserError
# import odoo.netsvc, decimal, os, xlrd
from odoo.addons.mw_base.verbose_format import verbose_format

_logger = logging.getLogger(__name__)

class HrEmployeeContract(models.Model):
	_name = "hr.employee.contract"
	_description = "Hr Employee Contract"
	_inherit = ['mail.thread']
	_order = "date desc"

	def _default_employee(self):
		return self.env.context.get('default_create_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	name = fields.Char('Нэр',tracking=True)
	number = fields.Char('Гэрээний дугаар',copy=False,tracking=True)
	employee_id = fields.Many2one('hr.employee','Ажилтан', required=True,tracking=True)
	department_id = fields.Many2one('hr.department','Алба нэгж')
	job_id = fields.Many2one('hr.job','Албан тушаал')
	job_degree = fields.Char(string='Албан тушаалын зэрэглэл', related='job_id.job_degree', store=True)


	create_employee_id = fields.Many2one('hr.employee','Үүсгэсэн ажилтан', default=_default_employee ,required=True)
	create_department_id = fields.Many2one('hr.department','Үүсгэсэн ажилтны хэлтэс')
	create_job_id = fields.Many2one('hr.job','Үүсгэсэн ажилтны албан тушаал')

	hr_employee_id = fields.Many2one('hr.employee','Гэрээ хийсэн ажилтан',tracking=True)
	hr_department_id = fields.Many2one('hr.department','Гэрээ хийсэн ажилтны хэлтэс')
	hr_job_id = fields.Many2one('hr.job','Гэрээ хийсэн ажилтны албан тушаал')
	hr_melen = fields.Char('Овог')

	date = fields.Date('Огноо',tracking=True,required=True)
	
	home_address = fields.Text(related='employee_id.live_address', string='Гэрийн хаяг')
	emp_name_melen = fields.Char(string='Овгийн эхний үсэг')
	wage = fields.Char('Үндсэн цалин/')
	wage_s = fields.Float('Үндсэн цалин',tracking=True,digits=(2, 0))
	
	other_department_id = fields.Many2one('hr.department','Хэлтэс')
	other_job_id = fields.Many2one('hr.job','Албан тушаал')
	company_id= fields.Many2one('res.company', "Компани",readonly=True)
	c_e_date = fields.Date('Дуусах огноо')
	months = fields.Char(compute='_compute_months', string='Туршилтын хугацаа', method=True)

	work_condition = fields.Selection([('in','Хэвийн'),('not','Хэвийн бус хүнд'), ('not2','Хэвийн бус хортой')],'Хөдөлмөрийн нөхцөл', related='job_id.work_condition',store=True)
	work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил',related = 'employee_id.work_location_id',store=True)
	type = fields.Selection([('working','Хөдөлмөрийн гэрээ/хугацаагүй/'),
		('period','Хөдөлмөрийн гэрээ/хугацаатай/'),
		('asset','Эд хөрөнгийн бүрэн хариуцлагын гэрээ'),
		('secret','Нууц хадгалах гэрээ'),
		('other','Гэрээний нэмэлт өөрчлөлт')],'Гэрээний төрөл', required=True,tracking=True)
	state= fields.Selection([
					('draft','Ноорог'),
					('sent','Илгээсэн'),
					('check','Хянасан'),
					('done','Баталсан'),
					],'Төлөв', readonly=True, default='draft',tracking=True)

	working_date = fields.Date('Хөдөлмөрийн гэрээний огноо',compute='_working_contract',store=True)
	working_contract = fields.Char('Хөдөлмөрийн гэрээний дугаар',compute='_working_contract',store=True)
	contract_id = fields.Many2one('hr.contract', 'Contract', readonly=True,tracking=True)
	work_condition_ch = fields.Char('work_condition type',compute='_work_condition_ch')
	year_ch = fields.Char('year ch')
	month_ch = fields.Char('Month ch')
	day_ch = fields.Char('Day ch')
	e_year_ch = fields.Char('Year e ch')
	e_month_ch = fields.Char('Month e ch')
	e_day_ch = fields.Char('Day e ch')
	wage_s_ch = fields.Char('Үндсэн цалин')
	wage_str = fields.Char('Үндсэн цалин',compute='_amount_wage_str')
	attachment_ids = fields.Many2many('ir.attachment','contract_attach_rel','contract_attach_id','attach_id', string='Хавсралт')

	@api.depends('employee_id')
	def _working_contract(self):
		for contract in self:
			cont_pool = self.search([('employee_id','=',contract.employee_id.id),('type','in',('working','period'))],limit=1)
			if contract.type == 'secret':
				contract.working_contract = cont_pool.number
				contract.working_date = cont_pool.date


	def name_get(self):
		res = []
		for d in self:
			name = str(d.number) or ''
			res.append((d.id, name))
		return res
	
	def unlink(self):
		for bl in self:
			if bl.state != 'draft':
				raise UserError(_('Ноорог төлөвтэй биш бол устгах боломжгүй.'))
		return super(HrEmployeeContract, self).unlink()
	
	def _compute_months(self):
		for item in self:
			if item.type == 'period' and item.c_e_date:
				start_date = datetime.strptime(
					str(item.date), "%Y-%m-%d").date()
				end_date = datetime.strptime(
					str(item.c_e_date), "%Y-%m-%d").date()
				delta = relativedelta.relativedelta(end_date,start_date)
				months_sum = delta.years * 12 + delta.months
				self.months = u'%d сар' % months_sum
			else:
				self.months =''


	@api.depends('wage_s')
	def _amount_wage_str(self):
		for line in self:
			if line.wage_s:
				line.wage_str = verbose_format(abs(line.wage_s))
			else:
				line.wage_str =''

	@api.depends('work_condition')
	def _work_condition_ch(self):
		for obj in self:
			if obj.work_condition == 'in':
				obj.work_condition_ch = 'Хэвийн'
			elif obj.work_condition == 'not':
				obj.work_condition_ch = 'Хэвийн бус хүнд'
			elif obj.work_condition == 'not2':
				obj.work_condition_ch = 'Хэвийн бус хортой'
			else:
				obj.work_condition_ch = ''


	# Үндсэн цалин шинэчлэх
	def create_hr_contract(self):
		contract_id = False
		if self.employee_id:
			contract = self.env['hr.contract'].search(
				[('employee_id', '=', self.employee_id.id)], limit=1)
			insured_id = self.env['insured.type'].sudo().search([('code', '=','01')], limit=1)
			if contract:
				contract.update({'wage': self.wage_s})
				self.contract_id = contract.id
			else:
				vals = {
					'employee_id': self.employee_id.id,
					'name': self.employee_id.identification_id,
					'date_start': self.date,
					'wage': self.wage_s,
					'is_pit': True,
					'insured_type_id': insured_id.id
				}
				contract_id = self.env['hr.contract'].create(vals)
				self.contract_id = contract_id.id
		
	def action_draft(self):
		self.write({'state': 'draft'})

	def action_check(self):
		self.write({'state': 'check'})

	def action_sent(self):
		if not self.number:
			self.contract_number()
		self._notification_send()
		self.write({'state':'sent'})

	def action_done(self):
		if self.type not in ('asset','secret'):
			self.create_hr_contract()
		self.write({'state': 'done'})

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.department_id = self.employee_id.department_id.id
			self.company_id = self.employee_id.company_id.id
			self.job_id = self.employee_id.job_id.id
			self.home_address = self.employee_id.live_address
			self.emp_name_melen = self.employee_id.last_name[:1]

	@api.onchange('create_employee_id')
	def onchange_create_employee_id(self):
		if self.create_employee_id:
			self.create_department_id = self.create_employee_id.department_id.id
			self.create_job_id = self.create_employee_id.job_id.id

	@api.onchange('hr_employee_id')
	def onchange_hr_employee_id(self):
		if self.hr_employee_id:
			self.hr_department_id = self.hr_employee_id.department_id.id
			self.hr_job_id = self.hr_employee_id.job_id.id
			self.hr_melen = self.hr_employee_id.last_name[:1]

	@api.onchange('date')
	def onchange_date(self):
		if self.date:
			self.year_ch = str(self.date)[:4]
			self.month_ch = str(self.date).split('-')[1]
			self.day_ch = str(self.date).split('-')[2]

	@api.onchange('c_e_date')
	def onchange_c_e_date(self):
		if self.c_e_date:
			self.e_year_ch = str(self.c_e_date)[:4]
			self.e_month_ch = str(self.c_e_date).split('-')[1]
			self.e_day_ch = str(self.c_e_date).split('-')[2]

	@api.onchange('wage_s')
	def onchange_wage_s(self):
		if self.wage_s:
			self.wage_s_ch = '{0:,.2f}'.format(self.wage_s).split('.')[0]

	
# Төрлөөс хамаарч дугаар оноох
	def contract_number(self):
		if not self.number:
			if self.type == 'working':
				self.number = self.env['ir.sequence'].next_by_code('employee.document.working')
			if self.type == 'period':
				self.number = self.env['ir.sequence'].next_by_code('employee.document.period')
			if self.type == 'asset':
				self.number = self.env['ir.sequence'].next_by_code('employee.document.asset')
			if self.type == 'secret':
				self.number = self.env['ir.sequence'].next_by_code('employee.document.secret')

# TODO Хэвлэх дээр ашиглах функцууд

# 	def get_company_logo(self, ids):
# 		report_id = self.browse(ids)
# 		image_buf = report_id.employee_id.company_id.logo
# 		image_str = """<img alt="Embedded Image" width="130" src='data:image/png;base64,%s""" % image_buf+'/>'
# 		image_str = image_str.replace("base64,b'","base64,",1)
# 		return image_str

# 	def get_company_logo1(self, ids):
# 		report_id = self.browse(ids)
# 		image_buf = report_id.employee_id.hr_company_id.image2
# 		image_str = """<img alt="Embedded Image" width="130" src='data:image/png;base64,%s""" % image_buf+'/>'
# 		image_str = image_str.replace("base64,b'","base64,",1)
# 		return image_str


# 	def action_to_contract(self):
# 		model_id = self.env['ir.model'].sudo().search([('model','=','hr.employee.contract')], limit=1)
# 		if self.type=='working':
# 			template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','working')], limit=1)
# 		else:
# 			template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','period')], limit=1)
# 		if template:
# 			res = template.sudo().print_template(self.id)
# 			return res
# 		else:
# 			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

# 	def action_to_secret_contract(self):
# 		model_id = self.env['ir.model'].sudo().search([('model','=','hr.employee.contract')], limit=1)
# 		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','secret')], limit=1)
# 		if template:
# 			res = template.sudo().print_template(self.id)
# 			return res
# 		else:
# 			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

# 	def action_to_asset_contract(self):
# 		model_id = self.env['ir.model'].sudo().search([('model','=','hr.employee.contract')], limit=1)
# 		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','asset')], limit=1)
# 		if template:
# 			res = template.sudo().print_template(self.id)
# 			return res
# 		else:
# 			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))
	
	def _notification_send(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_hr_employee_contract.action_employee_contract_view').id
		html = u'<b>Ажилтны гэрээ</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.employee.contract&action=%s>%s</a></b> ажилтаны үүсгэсэн гэрээг батлана уу"""% (base_url,self.id,action_id,self.create_employee_id.name)
		partners = self.env.ref('mw_hr.group_hr_confirm').sudo().users.mapped('partner_id')
		for receiver in partners:
			self.env.user.send_chat(html,receiver)

	def cron_end_date_check(self):
		today = date.today() + timedelta(days=14)
		contract_pool = self.env['hr.employee.contract'].sudo().search([('type','=','period')])
		for item in contract_pool:
			if item.c_e_date:
				c_e_date = date(today.year, item.c_e_date.month, item.c_e_date.day)
				days_until_end_contract = (c_e_date-today).days
				if days_until_end_contract == 0:
					item.send_contract_notif_hr()  

	def send_contract_notif_hr(self):
		res_model = self.env['ir.model.data'].search([
			('module','=','hr'),
			('name','in',['group_hr_manager'])])
		groups = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))], limit=1)	   
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_hr_employee_contract.action_employee_contract_view').id
		html = u'<b>Ажилтан.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hr.employee&action=%s>%s</a></b> Ажилтны хөдөлмөрийн гэрээний хугацаа дуусахад 14 хоног үлдсэн байна!"""% (base_url,self.id,action_id,self.name)
		for receiver in groups.users:
			self.env['res.users'].send_chat(html, receiver.partner_id)  

class HrEmployee(models.Model):
	_inherit = "hr.employee"

	contract_count = fields.Integer(string='Холбоотой гэрээний тоо',compute='_compute_contract_count' )

	def _compute_contract_count(self):
		contract = self.env['hr.employee.contract'].search([('employee_id','=',self.id)])
		for emp in self:
			emp.contract_count = len(contract)

	def action_hr_contract(self):
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id('mw_hr_employee_contract.action_employee_contract_view')
		action['domain'] = [('employee_id','=',self.id)]
		action['res_id'] = self.id
		return action

	