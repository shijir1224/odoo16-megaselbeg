
from odoo import  api, fields, models, _
from datetime import datetime
from io import BytesIO
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
import os,xlrd
from odoo.exceptions import UserError

	
class HseWorkplaceIspection(models.Model):
	_name ='hse.workplace.inspection'
	_description = 'Workplace inspection'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'date desc'

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('hse.workplace.inspection')
		return name

	name = fields.Char(string='Дугаар', readonly=True, default=_default_name)
	date = fields.Date(string='Үүсгэсэн огноо', required=True, readonly=True, states={'draft':[('readonly',False)]}, default=fields.Date.context_today)
	company_id = fields.Many2one('res.company', string="Компани", readonly=True, required=True, default=lambda self: self.env.user.company_id, states={'draft':[('readonly',False)],'sent':[('readonly',False)]})
	state = fields.Selection([
		('draft', 'Ноорог'),
		('sent_mail', 'Илгээсэн'),
		('repaired', 'Зассан'),
		('done', 'Дууссан')], 'Төлөв', readonly=True, default='draft', tracking=True)
	branch_id = fields.Many2one('res.branch', string='Салбар', required=True, readonly=True, states={'draft':[('readonly',False)]}, default=lambda self: self.env.user.branch_id, domain="[('company_id','=',company_id)]")
	made_place = fields.Char('Хийгдсэн газар', readonly=True, states={'draft':[('readonly',False)]})
	part = fields.Selection([
		('day','Өдөр'),
		('night','Орой')], 'Ээлж', required=True, readonly=True, states={'draft':[('readonly',False)]})
	department_id = fields.Many2one('hr.department','Хэлтэс', readonly=True, states={'draft':[('readonly',False)]})
	captian_id = fields.Many2one('hr.employee', string='Ахлагч', required=True, 
							#   readonly=True, states={'draft':[('readonly',False)]}, 
							  domain=[('employee_type', 'in', ['employee','student'])])
	employee_ids = fields.Many2many('hr.employee', 'hse_workplace_inspection_employee_rel', 'employee_id', 'workplace_inspection_id', string='Гишүүд', readonly=True, states={'draft':[('readonly',False)]})
	partner_ids = fields.Many2many('hse.partner', 'hse_workplace_inspection_partner_rel', 'wo_is_id','partner_id', 'Гадны компани ажилтан', readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', 'hse_workplace_inspection_ir_attachments_rel','worplace_id', 'attachment_id', string='Хавсралт', readonly=True, states={'draft':[('readonly',False),]})
	cor_act_attach_ids = fields.Many2many('ir.attachment', 'hse_workplace_inspection_cor_act_attach_rel','worplace_id', 'attachment_id', 'Арга хэмжээ авсан зураг', readonly=True, states={'sent_mail':[('readonly',False),]})
	wo_is_line = fields.One2many('hse.workplace.inspection.line', 'workplace_is_id', string='Workplace inspection lines', readonly=False, states={'repaired':[('readonly',True)],'done':[('readonly',True)]})
	good_job = fields.Text('Сайшаалтай зүйлс',  readonly=True, states={'draft':[('readonly',False)]})
	offer = fields.Text('Дүгнэлт', readonly=True, states={'draft':[('readonly',False)]})
	mail_line = fields.One2many('hse.workplace.inspection.mail.line', 'workplace_is_id', string='Майлын мөр')
	mail_text = fields.Text('Майл текст')
	hazard_type = fields.Selection([
		('1', 'Ноцтой'),
		('2', 'Их'),
		('3', 'Дунд'),
		('4', 'Бага'),
	], string='Илэрсэн зөрчлийн аюул эрсдлийн зэрэг',)
	employee_id = fields.Many2one('hr.employee', 'Хариуцсан ажилтан')
	excel_data = fields.Binary(string='Импорт файл')

	def date_value(self,dd):
		if dd:
			try:
				if type(dd)==float:
					serial = dd
					seconds = (serial - 25569) * 86400.0
					date=datetime.utcfromtimestamp(seconds)
				else:
					date = datetime.strptime(dd, '%Y-%m-%d')
			except ValueError:
				raise UserError(_('Date error %s row! \n \
				format must \'YYYY-mm-dd\'' % dd))
		else:
			date=''
		return date
	
	def get_field_value(self, f_id, f_value):
		if f_id.ttype=='date':
			if type(f_value) in [float, int]:
				f_value = (f_value - 25569) * 86400.0
				date_time = datetime.utcfromtimestamp(f_value)
				return str(date_time)
			else:
				return f_value
		elif f_id.ttype=='many2one':
			obj = self.env[f_id.relation]
			if type(f_value) in [float, int]:
				f_value = str(int(f_value))
			value_ids = obj.sudo()._name_search(f_value, operator='=',limit=100)
			if len(value_ids)>1:
				raise UserError('%s Талбарын утга %s 1-ээс олон ирээд байна'%(f_id.display_name, f_value))
			if value_ids:
				if not type(value_ids) == list:
					query = value_ids
					query_str, params = query.select("*")
					self._cr.execute(query_str, params)
					res = self._cr.fetchone()
					if res:
						value_ids = res
				return value_ids[0]
				# return value_ids[0][0]
			elif f_id.relation == 'res.partner':
				value_ids = obj.sudo().search([('vat','=',f_value)], limit=1)
				if not value_ids:
					raise UserError('%s талбарын %s регистр-тэй Харицлагч олдсонгүй'%(f_value,f_id.display_name))
				return value_ids.id
			else:
				return False
		elif f_id.ttype in ['char','text'] and type(f_value) in [float, int]:
			f_value = str(int(f_value))
			return f_value
		elif f_id.ttype == 'selection':
			if not f_id.selection_ids:
				raise UserError('%s Selection утга оруулаагүй байна',f_id.display_name)
			found_it = False
			if type(f_value) in [float, int]:
				f_value = str(int(f_value))
			for sel in f_id.selection_ids:
				if sel.value==f_value or sel.name==f_value:
					found_it = sel.value
					break
			if not found_it and f_value:
				raise UserError('%s ТАЛБАРЫН %s Selection field-ийн утга буруу байна олдсонгүй %s'%(f_id.display_name, f_value,', '.join(f_id.selection_ids.mapped('name'))))
			return found_it
		else:
			return f_value

	def import_from_excel(self):
		line_pool =  self.env['hse.workplace.inspection.line']

		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(u'Aldaa')
		book = xlrd.open_workbook(fileobj.name)
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(u'Aldaa')
		nrows = sheet.nrows

		rowi = 2
		data = []
		r=0
		for item in range(2,nrows):
			row = sheet.row(item)
			location = row[0].value
			hazard_zorchil = str(row[1].value)
			hazard_rating = row[2].value
			corrective_action_instructions = str(row[3].value)
			default_code = int(row[4].value)
			when_start = self.date_value(row[5].value)

			employee_id = self.env['hr.employee'].search([('identification_id','=',default_code)])
			if employee_id:
				raise UserError(u'Холбоотой ажилтан олдсонгүй. Зөвхөн ажилтны код оруулна уу!!!') 
			location_id = self.env['hse.location'].search([('name','=',location)], limit=1)
			if employee_id:
				line_id = line_pool.create({
					'location_id':location_id.id,
					'hazard_zorchil':hazard_zorchil,
					'hazard_rating':hazard_rating,
					'corrective_action_instructions':corrective_action_instructions,
					'when_start':when_start,
					'taken_employee_id':employee_id.id,
					'workplace_is_id':self.id,
				})

	def export_template(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Темплати.xlsx'
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)
		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#6495ED')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(9)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		header_wrap.set_bg_color('#6495ED')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		# Борлуулагчаар харуулах sheet
		worksheet = workbook.add_worksheet(u'Темплати')
		worksheet.write(0,1, u"Темплати", h1)
		# TABLE HEADER
		row = 1
		worksheet.write(row, 0, u"Байршил", header_wrap)
		worksheet.write(row, 1, u"Илэрсэн зөрчил", header_wrap)
		worksheet.write(row, 2, u"Аюулын зэрэг", header_wrap)
		worksheet.write(row, 3, u"Авагдсан арга хэмжээ", header_wrap)
		worksheet.write(row, 4, u"Арга хэмжээ авсан ажилтан", header_wrap)
		worksheet.write(row, 5, u"Хугацаа", header_wrap)
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
				'type' : 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				'target': 'new',
		}

	def unlink(self):
		for item in self:
			if item.state !='draft':
				raise UserError(_('Төлөв НООРОГ биш байна!!!'))
		return super(HseWorkplaceIspection, self).unlink()

	'''Ажлын байрны үзлэг засагдаагүйг автоматаар мэдэгдэх'''
	def get_mail_notice_workplace_inspection(self):
		workplace_ids = self.env['hse.workplace.inspection'].search([('state','=','sent_mail')])
		for item in workplace_ids:
			item._get_mail(item)

	def _get_email_employee(self, taken_employee_id, user_mails):
		emp_mail = None
		if taken_employee_id.work_email:
			if taken_employee_id.work_email not in user_mails:
				emp_mail = taken_employee_id.work_email
			else:
				return False
		else:
			if taken_employee_id.parent_id.work_email and taken_employee_id.parent_id.work_email not in user_mails:
				emp_mail = taken_employee_id.parent_id.work_email
			else:
				return False
		return {'email': emp_mail}
	
	def _get_email_captian_id_employee(self, captian_id, user_mails):
		emp_mail = None
		if captian_id.work_email:
			if captian_id.work_email not in user_mails:
				emp_mail = captian_id.work_email
			else:
				return False
		else:
			if captian_id.parent_id.work_email and captian_id.parent_id.work_email not in user_mails:
				emp_mail = captian_id.parent_id.work_email
			else:
				return False
		return {'email': emp_mail}
	

	def send_emails(self, subject, body):
		mail_mail = self.env['mail.mail']
		obj = self
		mail_ids = []
		for item in obj.mail_line:
			mail_id = mail_mail.create( {
				'email_from': self.company_id.email,
				'email_to': item.mail,
				'subject': subject,
				'body_html': '%s' % body
			})
			mail_id.send()
			mail_id.state='sent'
			mail_ids.append(mail_id.id)
		mail_mail.send(mail_ids)
		for item in mail_mail:
			item.state = 'sent'

	def _get_mail(self, obj):
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse', 'action_hse_workplace_inspection')[1]
		body = u'<p>Танд Ажлын Байрны Үзлэгээс'
		body += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.workplace.inspection&action=%s>%s</a> дугаартай хариу арга хэмжээ авах шаардлагатай дутагдал </b>"""%(base_url, obj.id, action_id, obj.name)
		if obj.state =='draft':
			body += u'ирлээ.</p>'
		if obj.state =='sent_mail':
			body += u'засагдсан төлөвт орлоо.</p>'
		if obj.state =='draft':
			body += u'<table> <tr> <td style="font-weight: bold;">'+u'</td></tr><tr><td>Огноо</td>'
			body += u'<td style="font-weight: bold;">'+str(obj.date)+u'</td></tr><tr><td>Дугаар</td>'
			body += u'<td style="font-weight: bold;">'+str(obj.name)+u'</td></tr><tr><td>Төсөл</td>'
			body += u'<td style="font-weight: bold;">'+str(obj.branch_id.name)+u'</td></tr><tr><td>Ээлж</td>'
			body += u'<td style="font-weight: bold;">'+(dict(obj._fields['part'].selection).get(obj.part) if obj.part else '')+u'</td></tr>'
			body += u'<table cellspacing="1" border="1" cellpadding="4"><tr style="background-color: #4CAF50; color: white;">'
			body += u'<th>Аюулын зэрэг</th><th>Илэрсэн зөрчил</th><th>Авагдсан арга хэмжээ, зааварчилгаа</th><th>Байршил</th><th>Хариуцагч</th><th>Албан тушаал</th><th>Дуусах огноо</th></tr>'
			for item in obj.wo_is_line:
				# body += u'<tr><td>'+item.hazard_rating.title()+u'</td><td>'
				# +item.failure_and_hazard+u'</td>'
				body += u'<tr><td>'+str(dict(item._fields['hazard_rating'].selection).get(item.hazard_rating) or '')+u'</td><td>'+str(item.hazard_zorchil or '')+u'</td><td>'+str(item.corrective_action_instructions or '')+u'</td><td>'+str(item.location_id.name or '')+'</td><td>'+str(item.taken_employee_id.name or '')+'</td><td>'+str(item.job_id.name or '')+'</td><td>'+str(item.when_start or '')+'</td></tr>'
		if obj.state=='sent_mail':
			self.env['hse.workplace.inspection.line'].search([
			('workplace_is_id','=',self.id),
			('is_repaired','=',False)]).write({
				'is_repaired': True, 
				'repair_date': datetime.now().strftime('%Y-%m-%d'),
				'repair_user_id': self.env.user.id
			})
			body += u'<table cellspacing="1" border="1" cellpadding="6"><tr style="background-color: #4CAF50; color: white;">'
			for item in obj.wo_is_line:
				body += u'<th>Засагдсан эсэх</th><th>Авсан арга хэмжээ</th><th>Арга хэмжээ авсан ажилтан</th><th>Арга хэмжээ авсан огноо</th></tr>'
				body += u'<tr><td>'+'Тийм'+u'</td><td>'+str(item.corrective_action_taken or '')+u'</td><td>'+str(item.repair_user_id.name or '')+'</td><td>'+str(item.repair_date or '')+'</td></tr>'
		body += u'</table>'
		mail_text=''
		if obj.mail_text:
			mail_text=obj.mail_text
		self.send_emails(u'Ажлын байрны үзлэг '+str(obj.name), str(body)+u'<br/>'+str(mail_text))
		sent_mail_users = ''
		for item in obj.mail_line:
			sent_mail_users += item.mail+'<br/>'
		message_post = u'Хариу арга хэмжээ авах'
		if obj.state =='repaired':
			message_post = u'Засагдсан'
		obj.message_post(body=(message_post+u':<br/>Дараах хүмүүст майл илгээгдэв:<br/>'+sent_mail_users), message_type='notification', subtype_xmlid="mail.mt_comment", parent_id=False)
		return True

	def mail_sent(self):
		self._get_mail(self)
		if self.state =='draft':
			self.write({'state': 'sent_mail'})
		elif self.state =='sent_mail':
			self.write({'state': 'repaired'})
		return True

	def action_to_sent_mail(self):
		if self.wo_is_line:
			for line in self.wo_is_line:
				if not line.attachment_ids:
					raise UserError(_('Мөрөн дээр хавсралт файл алга!!! Хавсралт оруулна уу'))
				else: ''
		else: ''
		obj = self
		user_obj = []
		if obj.wo_is_line:
			obj.mail_line = False
			user_mails = []
			if obj.wo_is_line:
				for item in obj.wo_is_line:
					user_obj = self._get_email_employee(item.taken_employee_id, user_mails)
					if user_obj:
						user_mails.append(user_obj['email'])	
				for item in user_mails:
					data = { 
						'workplace_is_id': obj.id,
						'mail': item,
					}
					line_id = self.env['hse.workplace.inspection.mail.line'].create(data)
			view_id = self.env['ir.ui.view'].search( [('model','=','hse.workplace.inspection'), ('name','=','hse.workplace.inspection.mail.form')] , limit=1)
			return {
				'name':_("Дараах хүмүүст майл илгээж мэдэгдэх"),
				'view_mode': 'form',
				'view_id': view_id.id,
				'view_type': 'form',
				'res_model': 'hse.workplace.inspection',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'res_id': obj.id,
				'context': self._context
			}
		else:
			raise UserError(_('Ажлын байрны үзлэгийн мөр хоосон байна!!!'))


	def action_to_repaired(self):
		if self.wo_is_line:
			for line in self.wo_is_line:
				if not line.attachment_repair_ids:
					raise UserError(_('Зассан хавсралт файл алга байна!!! Хавсралт оруулна уу'))
				else: ''
		else: ''
		user_obj = []
		user_mails = []
		for obj in self.wo_is_line:
			self.mail_line = False
			user_obj = self._get_email_captian_id_employee(self.captian_id, user_mails)
			if user_obj:
				user_mails.append(user_obj['email'])	
			for item in user_mails:
				data = { 
					'workplace_is_id': self.id,
					'mail': item,
				}
				line_id = self.env['hse.workplace.inspection.mail.line'].create(data)
			if len(self.env['hse.workplace.inspection.line'].search([('workplace_is_id','=',obj.workplace_is_id.id),('is_repaired','=',False)]))==1:
				print('cre  te te te t ete')
				view_id = self.env['ir.ui.view'].search( [('model','=','hse.workplace.inspection'), ('name','=','hse.workplace.inspection.mail.form')] , limit=1)
				return {
					'name':_("Дараах хүмүүст майл илгээж мэдэгдэх"),
					'view_mode': 'form',
					'view_id': view_id.id,
					'view_type': 'form',
					'res_model': 'hse.workplace.inspection',
					'type': 'ir.actions.act_window',
					'target': 'new',
					'res_id': self.id,
					'context': self._context
				}
			else:
				self.action_to_done()
	
	def action_to_draft(self):
		self.write({'state': 'draft'})
		return True
	
	def action_back_sent_mail(self):
		self.write({'state': 'sent_mail'})
		return True
	
	def action_to_done(self):
		self.write({'state': 'done'})
		return True


class HseWorkplaceIspectionMailLine(models.Model):
	_name ='hse.workplace.inspection.mail.line'
	_description = 'Mail line'
   
	workplace_is_id = fields.Many2one('hse.workplace.inspection', 'Workplace ID', required=True, ondelete='cascade')
	mail = fields.Char('Mail', required=True)
	

class HseWorkplaceIspectionLine(models.Model):
	_name ='hse.workplace.inspection.line'
	_description = 'Workplace inspection line'
   
	state = fields.Selection(related='workplace_is_id.state',readonly=True, store=True)
	workplace_is_id = fields.Many2one('hse.workplace.inspection', 'Workplace ID', required=True, ondelete='cascade')
	branch_id = fields.Many2one(related='workplace_is_id.branch_id', string='Салбар', readonly=True)
	location_id = fields.Many2one('hse.location', string='Байршил', readonly=True, states={'draft':[('readonly',False)]}, domain="[('branch_id','=',branch_id)]")
	hazard_zorchil = fields.Char('Илэрсэн зөрчил', readonly=True, states={'draft':[('readonly',False)]})
	hazard_rating = fields.Selection([('a', 'Ноцтой'),('b', 'Их'),('c', 'Дунд'),('d', 'Бага')], 'Аюулын зэрэг',  readonly=True, states={'draft':[('readonly',False)]})
	corrective_action_instructions = fields.Char('Авах арга хэмжээ', readonly=True, states={'draft':[('readonly',False)]})
	taken_employee_id = fields.Many2one('hr.employee', string='Хариуцах ажилтан', readonly=True, states={'draft':[('readonly',False)]})
	job_id = fields.Many2one(related='taken_employee_id.job_id', string='Албан тушаал', store=True)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', readonly=True, states={'draft':[('readonly',False)]})
	when_start = fields.Date('Дуусах Хугацаа',  readonly=True, states={'draft':[('readonly',False)]})
	corrective_action_taken = fields.Char('Авагдсан арга хэмжээ', readonly=True, states={'sent_mail':[('readonly',False)]})
	repair_user_id = fields.Many2one('res.users', string='Зассан хэрэглэгч', readonly=True)
	is_repaired = fields.Boolean('Засагдсан эсэх', default=False, readonly=True)
	repair_date = fields.Date('Засагдсан огноо', readonly=True)
	attachment_repair_ids = fields.Many2many('ir.attachment', 'hse_workplace_inspection_line_ir_attachments_rel','workplace_line_id', 'attachment_id', string='Засагдсан хавсралт', readonly=True, states={'sent_mail':[('readonly',False)]})
