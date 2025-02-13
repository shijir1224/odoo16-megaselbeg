#  -*- coding: utf-8 -*-
import datetime
from datetime import date, datetime,timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,date

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
	

class ContractDocumentReal(models.Model):
	_name = "contract.document.real"
	_description = 'Contracts'
	_inherit = ['mail.thread']
	_order = 'date_from ASC'
			
	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	def _default_department_id(self):
		return self.env['hr.department'].search([('id', '=', self.env.user.department_id.id)], limit=1)

	def name_get(self):
		res = []
		for obj in self:
			if obj.name and obj.contract_name and obj.date_to:
				res.append((obj.id, obj.name+' - '+'/'+obj.contract_name+'/'+str(obj.date_to)+'/'))
			elif obj.name and obj.contract_name:
				res.append((obj.id, obj.name+' - '+'/'+obj.contract_name+'/'))
			elif obj.name and obj.date_to:
				res.append((obj.id, obj.name+' - '+'/'+str(obj.date_to)+'/'))
			elif obj.contract_name and obj.date_to:
				res.append((obj.id, obj.contract_name+' - '+'/'+str(obj.date_to)+'/'))
			elif obj.name:
				res.append((obj.id, obj.name))
			elif obj.contract_name:
				res.append((obj.id, obj.contract_name))	
			else:
				res.append((obj.id, str(obj.date_to)))	
		return res
			


	name = fields.Char('Гэрээний дугаар',tracking=True,copy=False)
	contract_name = fields.Char('Гэрээний нэр',tracking=True)
	contract_idea = fields.Char('Гэрээний агуулга',tracking=True)
	date_from = fields.Date('Эхлэх огноо',tracking=True)
	date_to = fields.Date('Дуусах огноо',tracking=True)
	period = fields.Char('Хугацаа',readonly=True, compute='_compute_period',store=True)
	partner_id = fields.Many2one('res.partner','Харилцагч',tracking=True)
	partner_register = fields.Char('Харилцагчийн РД',tracking=True )
	partner_c_number = fields.Char('Харилцагч талын гэрээний дугаар',tracking=True )
	company_type1 = fields.Selection([('person','Хувь хүн'),('company','Компани'), ('goverment','Төрийн байгууллага')], 'Харилцагчийн төрөл',   tracking=True)
	payment_type = fields.Selection([('type1','Үнийн дүнтэй'),('type2','Үнийн дүнгүй'),('type3','Тооцоо нийлснээр'),('type4','Бартераар')],'Төлбөрийн хэлбэр',tracking=True)
	process_type = fields.Selection([('processing','Хэрэгжиж буй'),('closed','Хаагдсан'),('canceled','Цуцлагдсан'),('warrenty','Баталгаат хугацаа')],'Гэрээний явцын төлөв',tracking=True)
	pay_sel = fields.Selection([('yes','Нийлүүлэгч'),('no','Захиалагч')],'Гэрээнд оролцох хэлбэр',tracking=True)
	in_breach = fields.Selection([('yes','Тийм'),('no','Үгүй')],'Сонирхлын зөрчилтэй хэлцэл эсэх',tracking=True)
	in_deal = fields.Selection([('yes','Тийм'),('no','Үгүй')],'Их хэмжээний хэлцэл эсэх',tracking=True)
	type_in = fields.Selection([('type1','Хөрөнгө оруулалт'),('type2','Даатгалын зуучлал'),('type3','Даатгалын төлөөлөгч'),('type4','Эмнэлэг хамтын ажиллагаа'),('type5','Арга хэмжээний зориулалт'),('type6','Сургалт'),('type7','Ажил гүйцэтгэх'),('type8','Хөлсөөр ажиллах '),('type9','Хамтран ажиллах'),('type10','Зөвлөх үйлчилгээ'),('type11','Худалдах худалдан авах'),('type12','Түрээс'),('type13','Бартер'),('type14','Хөдөлмөрийн'),('type15','Нууцын'),('type16','Банкны үйлчилгээний '),('type17','Бусад')],'Төрөл')
	type_id = fields.Many2one('contract.type', 'Гэрээний төрөл',tracking=True, store=True) 
	res_currency_id = fields.Many2one('res.currency', 'Валют',tracking=True) 
	payment_sum=fields.Float(u'Гэрээний төлбөр',tracking=True)
	in_end = fields.Boolean('Гэрээ дүгнэх эсэх',tracking=True)
	in_foreign = fields.Boolean('Гадаад гэрээ эсэх',tracking=True)
	in_warrenty = fields.Boolean('Баталгаат хугацаатай эсэх',tracking=True)
	warrenty_date = fields.Integer('Баталгаат хугацаа/сараар/',tracking=True)
	res_company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id, readonly=True)
	employee_id = fields.Many2one('hr.employee','Гэрээ байгуулж буй ажилтан', default=_default_employee)
	department_id = fields.Many2one('hr.department', 'Алба, хэлтэс',tracking=True)
	job_id = fields.Many2one('hr.job', 'Албан тушаал',tracking=True)
	create_date = fields.Date('Бүртгэсэн огноо',readonly = True, default=fields.Date.context_today)
	date = fields.Date('Гэрээ хийсэн огноо')
	employee_ids  = fields.Many2many('hr.employee',string= 'Харагдах ажилтнууд')
	file = fields.Many2many('ir.attachment', 'contract_real_ir_attachment_rel','contract_id', 'attach_id', string='Гэрээний төслийн файл', tracking=True,inverse='_inverse_contract_attachment_ids')

	# Гэрээ дүгнэлт
	in_normal = fields.Selection([('yes','Тийм'),('no','Үгүй')],'Гэрээний дагуу ажил үйлчилгээ хэвийн явагдсан эсэх',tracking=True)
	in_create = fields.Selection([('yes','Тийм'),('no','Үгүй')],'Өглөг авлага үүссэн эсэх')
	act_contract_file = fields.Many2many('ir.attachment', 'act_contract_real_ir_attachment_rel','act_contract_id', 'attach_id', string='Акт файл',tracking=True,inverse='_inverse_act_file_attachment_ids')
	act_description = fields.Text('Тайлбар',tracking=True)
	not_date = fields.Date('Мэдэгдэл ирэх огноо',compute ='_compute_date_to', store=True)
	in_notif = fields.Boolean('Гэрээг дүгнэх мэдэгдэл очисон', readonly=True)
	in_notif_act = fields.Boolean('Батлагдсан гэрээг оруулах мэдэгдэл очисон', readonly=True)
	print_name = fields.Char('print name')
	print_number = fields.Char('Гэрээний дугаар хэвлэх')
	type = fields.Selection(related='type_id.type',store=True)


	def _inverse_act_file_attachment_ids(self):
		for obj in self:
			obj.act_contract_file.write({
				'res_id': obj.id,
			})

	def _inverse_contract_attachment_ids(self):
		for obj in self:
			obj.file.write({
				'res_id': obj.id,
			})

	# Харилцагчийн түүх
	history_line_ids = fields.Many2many('contract.document.real', 'contract_document_real_rel','contract_document_real_id', 'contract_id' , u'Өмнөх түүх', compute ="before_contracts_view")
	
	# Эцсийн батлагдсан гэрээ 
	contract_line_ids = fields.One2many('done.contract.reg','contract_real_id',string = 'Батлагдсан гэрээ')

	# Төлбөр төлөлт
	payment_line_ids = fields.One2many('contract.real.payment.line','contract_amount_graph_id',string = 'Төлбөр төлөлт')
	start_date = fields.Date('Эхлэх огноо')
	end_date = fields.Date('Дуусах огноо')
	amount = fields.Float('Дүн')

	# Гэрээний нэмэлт өөрчлөлт
	new_contract_ids = fields.Many2many('contract.document.real','contract_document_real_relation', 'contract_id', 'new_id',string='Нэмэлт гэрээнүүд',compute='new_contract_ids_view')
	old_contract_id = fields.Many2one('contract.document.real','Үндсэн гэрээ',readonly=True,tracking=True)


	# Хэвлэх тохиргоо
	l_name = fields.Char('last_name')

	@api.onchange('name')
	def _onchange_name(self):
		if self.name:
			self.print_number = self.name
	
	
	
	@api.depends('date_from','date_to')
	def _compute_period(self):
		for obj in self:
			if obj.date_from and obj.date_to:
				date_from = datetime.strptime(str(obj.date_from), "%Y-%m-%d")
				date_to = datetime.strptime(str(obj.date_to), "%Y-%m-%d")
				if date_from.year == date_to.year:
					if date_to.month > date_from.month:
						obj.period= str(date_to.month - date_from.month) + ' сар'
					else:
						obj.period='1 сар'
				else:
					obj.period= str(date_to.year - date_from.year) + ' жил'
			else:
				obj.period=''

	def new_contract_ids_view(self):
		for item in self:
			new_contracts = item.env['contract.document.real'].search([('old_contract_id','=',item.id)])
			item.new_contract_ids = new_contracts.ids
	
	def action_create_contract(self):
		new_contract = self.env['contract.document.real']
		new = new_contract.create({
			'name': str(self.env['ir.sequence'].next_by_code('contract.document.real.new')),
			'contract_name': self.contract_name,
			'partner_id': self.partner_id.id,
			'partner_register':self.partner_register,
			'company_type1':self.company_type1,
			'date_from':self.date_from,
			'date_to':self.date_to,
			'pay_sel': self.pay_sel,
			'type_id': self.type_id.id,
			'res_currency_id': self.res_currency_id.id,
			'employee_id':self.employee_id.id,
			'in_foreign': self.in_foreign,
			'old_contract_id':self.id
			})
	


	def line_create(self):
		line_data_pool =  self.env['contract.real.payment.line']
		if self.payment_line_ids:
			self.payment_line_ids.unlink()
		from_dt = datetime.strptime(str(self.start_date), DATE_FORMAT).date()
		to_dt = datetime.strptime(str(self.end_date), DATE_FORMAT).date()
		step = relativedelta(months=1)
		for obj in self:
			while from_dt <= to_dt:
				line_line_conf = line_data_pool.create({
								'contract_amount_graph_id':obj.id,
								'paid_date':from_dt,
								'paid_amount':obj.amount,		
							})
				paid_amount_map=sum(self.payment_line_ids.mapped('paid_amount'))
				if self.payment_sum<paid_amount_map:
					raise UserError(('Гэрээний дүнгээс хэтэрсэн байна.'))
				from_dt += step

	@api.onchange('payment_line_ids')
	def onchange_line_amount(self):
		amount_map=sum(self.payment_line_ids.mapped('paid_amount'))
		if self.payment_sum<amount_map:
			raise UserError(('Гэрээний дүнгээс хэтэрсэн байна.'))



	def before_contracts_view(self):
		for item in self:
			before_contracts = item.env['contract.document.real'].search([('partner_id','=',item.partner_id.id)])
			item.history_line_ids = before_contracts.ids

# Хэвлэлт
	def date_year(self,ids):
		line=self.browse(ids)
		sheet_year = str(line.date).split('-')[0]
		return sheet_year
	
	def date_month(self,ids):
		line=self.browse(ids)
		sheet_month = str(line.date).split('-')[1]
		return sheet_month
	
	def date_day(self,ids):
		line=self.browse(ids)
		sheet_day = str(line.date).split('-')[2]
		return sheet_day

	def date_from_year(self,ids):
		line=self.browse(ids)
		sheet_year = str(line.date_from).split('-')[0]
		return sheet_year
	
	def date_from_month(self,ids):
		line=self.browse(ids)
		sheet_month = str(line.date_from).split('-')[1]
		return sheet_month
	
	def date_from_day(self,ids):
		line=self.browse(ids)
		sheet_day = str(line.date_from).split('-')[2]
		return sheet_day

	def date_to_year(self,ids):
		line=self.browse(ids)
		sheet_year = str(line.date_to).split('-')[0]
		return sheet_year
	
	def date_to_month(self,ids):
		line=self.browse(ids)
		sheet_month = str(line.date_to).split('-')[1]
		return sheet_month
	
	def date_to_day(self,ids):
		line=self.browse(ids)
		sheet_day = str(line.date_to).split('-')[2]
		return sheet_day

	
	# гэрээ дуусахаас нэг хоногийн өмнө мэдэлдэл ирнэ
	@api.depends('date_to')
	def _compute_date_to(self):
		day = timedelta(14)
		for item in self:
			if item.date_to:
				item.not_date = item.date_to - day

	def _update_contract_end_change(self):
		today = date.today()
		not_contract = self.env['contract.document.real'].search([('not_date', '=', today),('state_type', '=', 'sent')])
		for item in not_contract:
			item.action_end_notification_send()
			item.in_notif = True

	def _cron_contract_end_date(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_contract.action_contract_document_real_view').id
	
		advance_day = date.today()-timedelta(days=31)
		contract = self.env['contract.document.real'].sudo().search([('date_to','=',advance_day )])
		for item in contract:
			html = u'<b>Гэрээний хугацаа дуусах мэдэгдэл.</b><br/>'
			html += u'<p>Сайн байна уу.</br></p><p>%s дугаартай гэрээний хугацаа дуусахад 15 хоног үлдлээ  байна.<a href=%s/web#id=%s&view_type=form&model=mak.contract.checklist&action=%s>''Энд дарж </a> <span> шалгана уу? </span></p>'%(item.name, base_url,self.id,action_id)
			self.env.user.send_chat(html, item.employee_id.partner_id)
		
		

	# Батлагдсан боловч батлагдсан хувилбар оруулаагүй гэрээн дээр
	# def _not_contract_act(self):
	# 	act_contracts = self.env['contract.document.real'].search([('contract_line_ids', '=', False),('state_type', '=', 'done')])
	# 	for item in act_contracts:
	# 		item.action_act_notification_send()
	# 		item.in_notif_act = True


	def _payment_late_contract(self):
		today = datetime.now().date()
		contract_lines = self.env['contract.real.payment.line'].search([('paid_date','=',today)])
		for item in contract_lines:
			item.action_pay_notification_send()


	def action_to_contract_intro(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','contract.document.real')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','intro')], limit=1)
		if template:
			res = template.sudo().print_template(self.id)
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

# Print function
	def get_user_signature(self, ids):
		report_id = self.browse(ids)
		html = '<table>'
		print_flow_line_ids = report_id.flow_id.line_ids.filtered(
			lambda r: r.is_print)
		history_obj = self.env['contract.real.flow.history']
		for item in print_flow_line_ids:
			his_id = history_obj.search(
				[('flow_line_id', '=', item.id), ('request_id', '=', report_id.id)], limit=1)
			image_str = '________________________'
			if his_id.user_id.digital_signature_from_file:
				image_buf = (his_id.user_id.digital_signature_from_file).decode('utf-8')
				image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />' % (
					image_buf)
			user_str = '________________________'
			if his_id.user_id:
				user_str = his_id.user_id.name
			html += u'<tr><td><p>%s</p></td><td>%s</td><td> <p>/%s/</p></td></tr>' % (
					item.name, image_str, user_str)
		html += '</table>'
		return html

	def get_print_lines(self, ids):
		headers = [
			u'<p style="text-align: center;font-weight: bold; font-size: 15px" >''№'u'</p>',
			u'<p style="text-align: center;font-weight: bold; font-size: 15px">''Төлөх огноо'u'</p>',
			u'<p style="text-align: center;font-weight: bold; font-size: 15px">''Төлөх үнийн дүн'u'</p>',
		]
		datas = []
		report_id = self.browse(ids)
		i = 1
	
		for line in report_id.payment_line_ids:
			temp = [
					u'<p style="text-align: center; font-size: 15px">' + str(i)+u'</p>',
					u'<p style="text-align: center;font-size: 15px">' + str(line.paid_date) or '' + u'</p>',
					u'<p style="text-align: center;font-size: 15px">' + str(line.paid_amount) or '' + u'</p>',
			]
			datas.append(temp)
			i += 1
		res = {'header': headers, 'data': datas}
		return res

# Гэрээний загвар
class ContractTemplate(models.Model):
	_name = 'contract.template'
	_description = 'Гэрээний загвар'
	

	name = fields.Char('Нэр')
	file = fields.Many2many('ir.attachment', 'contract_template_ir_attachment_rel','contract_template_id', 'attach_id', string='Загвар файл', required=True,inverse='_inverse_template_file_attachment_ids')
	
	def _inverse_template_file_attachment_ids(self):
		for obj in self:
			obj.file.write({
				'res_id': obj.id,
			})



class ContractType(models.Model):
	_name = 'contract.type'
	_description = 'Гэрээний төрөл'
	
	name = fields.Char('Нэр')
	type = fields.Selection([('training','Сургалт')],'Төрөл',tracking=True)


class NotificationAlarmManager(models.Model):
	_name = 'done.contract.reg'
	_description = 'Батлагдсан гэрээний мэдээлэл'

	employee_id = fields.Many2one('hr.employee','Ажилтан')
	
	contract_file = fields.Binary('Батлагдсан гэрээ')
	file = fields.Many2many('ir.attachment', 'contract_ir_attachment_rel',
		'contract_id', 'attach_id', string='Батлагдсан гэрээ', inverse='_inverse_done_c_file_attachment_ids')
	
	def _inverse_done_c_file_attachment_ids(self):
		for obj in self:
			obj.file.write({
				'res_id': obj.id,
			})

	contract_real_id = fields.Many2one('contract.document.real','Contract')

class ContractRealPaymentLine(models.Model):
	_name = 'contract.real.payment.line'
	_description = 'Contract Payment Line'

	
	contract_amount_graph_id = fields.Many2one('contract.document.real','Төлбөр')
	paid_amount = fields.Float('Дүн')
	paid_date = fields.Date('Огноо')
	amount_total = fields.Float('Гэрээний дүн')
	amount_balance = fields.Float('Төлбөрийн үлдэгдэл')



	def action_pay_notification_send(self):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env.ref('mw_contract.action_contract_document_real_view').id
		html = u'<b>Гэрээний бүртгэл төлбөр төлөх хуваарь болсон байна.</b><br/>'
		html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=contract.document.real&action=%s>%s</a></b>- нэртэй гэрээний төлбөр төлөх хуваарь болсон байн уу!"""% (base_url,self.id,action_id,self.contract_amount_graph_id.contract_name)
		if self.contract_amount_graph_id.employee_id.user_partner_id:
			self.env['res.users'].send_chat(html, self.contract_amount_graph_id.employee_id.user_partner_id,True)