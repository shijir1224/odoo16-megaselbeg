from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from odoo.http import request
from odoo.exceptions import UserError
import pytz



class HseInjuryEntry(models.Model):
	_name ='hse.injury.entry'
	_description = 'Injury entry'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'datetime desc, name asc'
   
	# def write(self, vals):
	# 	super(hse_injury_entry, self).write(vals)
	# 	obj = self.browse(cr,uid,ids,context)[0]

	# 	if 'datetime' in vals or 'branch_id' in vals or 'accident_type' in vals:
	# 		vals = {}
	# 		obj = self
	# 		my_id = self.env['ir.model'].search( [('model','=','hse.injury.entry')], limit=1)
	# 		conf_ids = self.env['hse.code.config'].search([('branch_id','=',obj.branch_id.id),('model_id','=',my_id.id)], limit=1)
	# 		if conf_ids:
	# 			num_name = conf_ids.name
	# 			if obj.accident_type.value =='FIRST_AID':
	# 				num_name+=u'АТУ-'
	# 			elif obj.accident_type.value =='SPILL':
	# 				num_name+=u'АСГ-'
	# 			elif obj.accident_type.value =='FIRE':
	# 				num_name+=u'ГАЛ-'
	# 			elif obj.accident_type.value =='NEAR_MISS_INCIDENT':
	# 				num_name+=u'ОДТ-'
	# 			elif obj.accident_type.value =='MEDICAL_AID':
	# 				num_name+=u'ЭТУ-'
	# 			elif obj.accident_type.value =='PROPERTY_DAMAGE':
	# 				num_name+=u'ӨМЧ-'
	# 			max_count = 0
	# 			# self.env.cr.execute('SELECT id FROM hse_injury_entry where id!=%s and branch_id = %s and year= %s and accident_type=%s',(obj.id, obj.branch_id.id, obj.year, obj.accident_type.id))
	# 			obj_ids = self.env['hse.injury.entry'].search([('id','!=',obj.id),('branch_id','=',obj.branch_id.id),('year','=',obj.year),('accident_type','=',obj.accident_type.id)])
	# 			for item in obj_ids:
	# 				s = item.name
	# 				if s and int(s[len(num_name): len(s)]) > max_count:
	# 					max_count = int(s[len(num_name): len(s)])
	# 			vals['name'] = num_name+str(max_count+1).zfill(4)
	# 			return super(hse_injury_entry, self).write(vals)

	@api.model
	def _default_name(self):
		name=self.env['ir.sequence'].next_by_code('hse.injury.entry')
		return name

	name = fields.Char(string='Дугаар', readonly=True, default=_default_name)
	datetime = fields.Datetime(string="Огноо", required=True, readonly=True, states={'draft':[('readonly',False)]})
	date = fields.Date(string='Өдөр', compute='_compute_date', store=True)
	state = fields.Selection([
		('draft', 'Ноорог'),
		('sent_mail', 'Майл илгээгдсэн'),
		('cor_act_closed', 'Хариу арга хэмжээ авагдсан'),
		('closed', 'Хаагдсан')
	], 'Төлөв', readonly=True, default='draft')
	company_id = fields.Many2one('res.company', string=u'Компани', readonly=True, default=lambda self: self.env.user.company_id, states={'draft':[('readonly',False)]})
	branch_id = fields.Many2one('res.branch', 'Салбар', required=True, readonly=True, states={'draft':[('readonly',False)]}, default=lambda self: self.env.user.branch_id, domain="[('company_id','=',company_id)]")
	location_id = fields.Many2one('hse.location', 'Байрлал', readonly=True, states={'draft':[('readonly',False)]}, domain="[('branch_id','=',branch_id)]")
	branch_manager_id = fields.Many2one('hr.employee','Хариуцсан ахлах ажилтан', required=True, readonly=True, states={'draft':[('readonly',False)]})
	part = fields.Selection([('a', 'Өдөр'),('b', 'Шөнө')], 'Ээлж', required=True, readonly=True, states={'draft':[('readonly',False)]})
	consequences = fields.Selection([('a', 'Маш бага'),('b', 'Бага'),('c', 'Дунд зэрэг'),('d', 'Их'),('e', 'Ноцтой')], string='Гарсан үр дагавар', required=True, readonly=True, states={'draft':[('readonly',False)]})
	possible_consequences = fields.Selection([('a', 'Маш бага'),('b', 'Бага'),('c', 'Дунд зэрэг'),('d', 'Их'),('e', 'Ноцтой')], string='Гарч болох үр дагавар', required=True, readonly=True, states={'draft':[('readonly',False)]})
	probability_of_occurrence = fields.Selection([('a', 'Ховор'),('b', 'Хааяа нэг'),('c', 'Боломжтой'),('d', 'Элбэг'),('e', 'Бараг байнга')], string='Тохиолдох магадлал', required=True, readonly=True, states={'draft':[('readonly',False)]})
	risk = fields.Text('Гарч болох эрсдэл:', required=True, readonly=True, states={'draft':[('readonly',False)]})
	location_accident = fields.Char('Товч:', required=True, readonly=True, states={'draft':[('readonly',False)]})
	case_type = fields.Selection([('injury', 'Гэмтэл'),('nature', 'Байгаль орчин'),('property damage', 'Өмчийн эвдрэл ')], string='Тохиолдлын төрөл', required=True, readonly=True, states={'draft':[('readonly',False)]})
	case_desc = fields.Text(string="Тохиолдолын тодорхойлт", states={'draft':[('readonly',False)]})
	injury_type = fields.Char('Гэмтлийн ангилал', readonly=True, states={'draft':[('readonly',False)]})
	description_of_the_injury = fields.Text('Гэмтлийн тодорхойлолт', readonly=True, states={'draft':[('readonly',False)]})
	environmental_damage = fields.Text('Байгаль Орчны хохирол:', readonly=True, states={'draft':[('readonly',False)]}) 
	property_damage = fields.Text('Өмчийн эвдрэл:', readonly=True, states={'draft':[('readonly',False)]})
	subject = fields.Text('Субъект:', required=True, readonly=True, states={'draft':[('readonly',False)]})
	training_conducted = fields.Text('Хийгдсэн сургалт:', required=True, readonly=True, states={'draft':[('readonly',False)]})
	training_attachment_ids = fields.Many2many('ir.attachment', string='Сургалтын материал', readonly=True, states={'draft':[('readonly',False)]})
	on_site_action = fields.Text(string='Газар дээр нь авсан арга хэмжээ', required=True, readonly=True, states={'draft':[('readonly',False)]})
	basic_causes = fields.Text(string='Суурь шалтгаан', readonly=True)
	person_about_line = fields.One2many('hse.injury.person.line', 'injury_id', 'Person about line', readonly=False,)
	research_team_line = fields.One2many('hse.injury.research.team.line', 'injury_id', 'Research team', readonly=False,)
	environment_ids = fields.Many2many('hse.injury.environment', 'parent_id', string='Орчин', readonly=True, states={'draft':[('readonly',False)]})
	equipment_materials_ids = fields.Many2many('hse.injury.equipment.materials', 'parent_id_1', string='Тоног төхөөрөмж/Материал', readonly=True, states={'draft':[('readonly',False)]})
	operating_system_ids = fields.Many2many('hse.injury.operating.system', 'parent_id_2', string='Ажлын систем', readonly=True, states={'draft':[('readonly',False)]})
	person_ids = fields.Many2many('hse.injury.person', 'parent_id_3', string='Хүн', readonly=True, states={'draft':[('readonly',False)]})
	direct_cause = fields.Text('ШУУД ШАЛТГААН ', readonly=True)
	non_standard_ids = fields.Many2many('hse.injury.non.standard', 'parent_id_4', string='Стандарт бус үйлдэл', readonly=True, states={'draft':[('readonly',False)]})
	non_standard_condition_ids = fields.Many2many('hse.injury.non.standard.conditions', 'parent_id_5', string='Стандарт бус нөхцөл', readonly=True, states={'draft':[('readonly',False)]})
	prevention_correction = fields.Text('СЭРГИЙЛЭХ/ЗАЛРУУЛАХ АРГА ХЭМЖЭЭ ', readonly=True)
	injury_report_line = fields.One2many('hse.injury.report.line', 'injury_id', 'Injury report', readonly=False,)
	plan_attachment_ids = fields.Many2many('ir.attachment', 'plans_ir_attachment_rel', 'plans_ir', string='ЗУРАГ/БҮДҮҮВЧ/ГАР ЗУРАГ', readonly=True, states={'draft':[('readonly',False)]})
	witness_explanation_ids = fields.Many2many('ir.attachment', 'witness_explanation_rel', 'witness_ir', string='Гэрчийн тайлбар', readonly=True, states={'draft':[('readonly',False)]})
	connected_person_ids = fields.Many2many('ir.attachment', 'connected_person_rel', 'connected_ir', string='Холбогдсон хүний тайлбар', readonly=True, states={'draft':[('readonly',False)]})
	work_attachment_ids = fields.Many2many('ir.attachment', 'works_ir_attachment_rel', 'works_id', string='Ажлын байрны зураг', readonly=True, states={'draft':[('readonly',False)]})
	work_guide_ids = fields.Many2many('ir.attachment', 'work_guide_rel', 'work_guide', string='Ажлын зааварчилгаа', readonly=True, states={'draft':[('readonly',False)]})
	injury_research = fields.Many2one('res.users',  'Ослын судалгаа хийсэн', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	square_senior_empl= fields.Many2one('res.users', 'Талбай хариуцсан ахлах', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	senior_manager= fields.Many2one('res.users', 'Ахлах мэргэжилтэн', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	is_project_admin = fields.Boolean('Ноцтой осол эсэх', readonly=True, states={'draft':[('readonly',False)]})
	project_admin = fields.Many2one('res.users', 'Төслийн удирдагч', tracking=True, readonly=True, states={'draft':[('readonly',False)]})
	# technic_ids = fields.Many2many('technic.equipment', 'hse_injury_entry_technic_rel','injury_id', 'technic_id', 'Техник')
	accident_name = fields.Char('Accident name', readonly=True, states={'draft':[('readonly',False)]})
	lost_day = fields.Integer('Алдсан ажлын өдөр', readonly=True)
	involved_employee = fields.Many2many('hr.employee', 'hse_injury_entry_involved_employee_rel','injury_id', 'employee_id', 'Холбогдсон ажилтан')
	department_id = fields.Many2one('hr.department','Хэлтэс', readonly=True, states={'draft':[('readonly',False)]})
	dep_manager_id = fields.Many2one('hr.employee','Хэлтсийн менежер', readonly=True, states={'draft':[('readonly',False)]})
	general_master_id = fields.Many2one('hr.employee','Ерөнхий мастер', readonly=True, states={'draft':[('readonly',False)]})
	master_id = fields.Many2one('hr.employee','Ээлжийн мастер', readonly=True, states={'draft':[('readonly',False)]})
	
	# accident_type = fields.Many2one('hse.accident.type', 'Ослын төрөл', readonly=True, states={'draft':[('readonly',False)]})
	# value = fields.Char(related='accident_type.value', store=True, string='Утга')

	# subject = fields.Text('Субъект:', required=True, readonly=True, states={'draft':[('readonly',False)]})
	training_conducted = fields.Text('Хийгдсэн сургалт:', required=True, readonly=True, states={'draft':[('readonly',False)]})
	on_site_action = fields.Text('Газар дээр нь авсан арга хэмжээ', required=True, readonly=True, states={'draft':[('readonly',False)]})
	is_lti = fields.Boolean('ХЧТА эсэх?', readonly=True, states={'draft':[('readonly',False)]})
	accident_line = fields.One2many('hse.injury.accident.line', 'injury_id', 'Ослын мөр', readonly=True, states={'draft':[('readonly',False)]})
	corrective_action_line = fields.One2many('hse.injury.corrective.action.line', 'injury_id', 'Corrective action line', readonly=False, states={'cor_act_closed':[('readonly',True)]})
	audit_line = fields.One2many('hse.injury.audit.line', 'injury_id', 'Шалгалтын мөр', readonly=True, states={'draft':[('readonly',False)]})
	audit_conclusion_line = fields.One2many('hse.injury.audit.conclusion.line', 'injury_id', 'Audit conclusion line', readonly=False, states={'cor_act_closed':[('readonly',True)]})
	factor_line = fields.One2many('hse.injury.factor.line', 'injury_id', 'Factor line', readonly=True, states={'draft':[('readonly',False)]})
	attachment_ids = fields.Many2many('ir.attachment', 'hse_injury_entry_ir_attachments_rel','injury_id', 'attachment_id', 'Хавсралт', readonly=True, states={'draft':[('readonly',False)]})
	cor_act_attach_ids = fields.Many2many('ir.attachment', 'hse_injury_entry_cor_act_attach_rel','injury_id', 'attachment_id', 'Арга хэмжээ авсан зураг', readonly=True, states={'closed':[('readonly',False),]})
	desc_attach_ids = fields.Many2many('ir.attachment', 'hse_injury_entry_desc_attach_rel','injury_id', 'attachment_id', 'Тайлбар зураг', readonly=True, states={'draft':[('readonly',False),]})
	mail_line = fields.One2many('hse.injury.entry.mail.line', 'injury_id', 'Майлын мөр')
	mail_text = fields.Text('Майл текст')
	resource_attachment_ids = fields.Many2many('ir.attachment', 'hse_injury_ir_attachments_rel','injury_id', 'attachment_id', string='Ослын судалгааны тайлан/баталгаажсан/', readonly=True, states={'draft':[('readonly',False)]})	
	
	
	@api.depends('datetime')
	def _compute_date(self):
		for item in self:
			if item.datetime:
				item.date = item.datetime.strftime('%Y-%m-%d')
			else: ''


	# @api.model
	# def create(self,  vals):
	# 	ids = super(hse_injury_entry,self).create( vals)
	# 	obj = ids
	# 	res = {}
	# 	if 'branch_id' in vals or 'accident_type' in vals:
	# 		obj = ids
	# 		my_id = self.env['ir.model'].search( [('model','=','hse.injury.entry')])[0]
	# 		conf_ids = self.env['hse.code.config'].search([('branch_id','=',obj.branch_id.id),('model_id','=',my_id)], limit=1)
	# 		if conf_ids:
	# 			num_name = conf_ids.name
	# 			if obj.accident_type.value =='FIRST_AID':
	# 				num_name+=u'АТУ-'
	# 			elif obj.accident_type.value =='SPILL':
	# 				num_name+=u'АСГ-'
	# 			elif obj.accident_type.value =='FIRE':
	# 				num_name+=u'ГАЛ-'
	# 			elif obj.accident_type.value =='NEAR_MISS_INCIDENT':
	# 				num_name+=u'ОДТ-'
	# 			elif obj.accident_type.value =='MEDICAL_AID':
	# 				num_name+=u'ЭТУ-'
	# 			elif obj.accident_type.value =='PROPERTY_DAMAGE':
	# 				num_name+=u'ӨМЧ-'
	# 			max_count = 0
	# 			self.env.cr.execute('SELECT id FROM hse_injury_entry where branch_id = %s and EXTRACT(YEAR FROM datetime) = %s and accident_type=%s',(obj.branch_id.id, datetime.strptime(obj.datetime, '%Y-%m-%d %H:%M:%S').year, obj.accident_type.id))
	# 			obj_ids = map(lambda x: x[0],self.env.cr.fetchall())
	# 			for item in obj_ids:
	# 				s = item.name
	# 				if s and int(s[len(num_name): len(s)]) > max_count:
	# 					max_count = int(s[len(num_name): len(s)])
	# 			obj.name = num_name+str(max_count+1).zfill(4)
				
	# 	return ids

	def unlink(self):
		for item in self:
			if item.state !='draft':
				raise UserError(_('Төлөв НООРОГ биш байна!!!'))
		
		return super(HseInjuryEntry, self).unlink()
		
	def _get_email_employee(self, employee_id, user_mails):
		obj = self
		emp_mail = None
		if employee_id.work_email:
			if employee_id.work_email not in user_mails:
				emp_mail = employee_id.work_email
			else:
				return False
		else:
			if employee_id.parent_id.work_email and employee_id.parent_id.work_email not in user_mails:
				emp_mail = employee_id.parent_id.work_email
			else:
				return False
		return {'email': emp_mail}

	
	def send_emails(self, subject, body):
		html = body or ''
		for item in self.mail_line:
			mail = self.env['mail.mail'].sudo().create({
				'body_html': html,
				'subject': subject,
				'email_to': item.mail,
				'email_from': self.company_id.email,
				'attachment_ids': self.resource_attachment_ids
			})
			mail.send()
			if mail.state=='sent':
				print('success')

	def _get_mail(self):
		obj = self
		base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
		action_id = self.env['ir.model.data'].check_object_reference('mw_hse', 'action_hse_injury_entry')[1]
		date_time = obj.datetime
		timezone = pytz.timezone(self.env.user.tz)
		date_time = (date_time.replace(tzinfo=pytz.timezone('UTC'))).astimezone(timezone)
		body = u'<b>Дараах Ослын тайлангийн </b><br/>'
		body += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=hse.injury.entry&action=%s>%s</a></b>"""%(base_url, obj.id, action_id, obj.name)
		if obj.state =='draft':
			body += u' мэдээлэлтэй танилцана уу.</p>'
		if obj.state =='sent_mail':
			body += u' хариу арга хэмжээ авагдлаа'
		if obj.state =='cor_act_closed':
			body += u' хаагдлаа'
		if obj.state =='draft':
			body += u'<table cellspacing="1" border="1" cellpadding="10"><tr style="background-color: #4CAF50; color: white;">'
			body += u'<th>Огноо</th><th>Салбар</th><th>Байрлал</th><th>Ээлж</th><th>Ослын тодорхойлт</th>'
			body += u'<tr><td>'+str(date_time)+'</td><td>'+str(obj.branch_id.name)+'</td><td>'+str(obj.location_id.name)+'</td><td>'+dict(obj._fields['part'].selection).get(obj.part)+'</td><td>'+str(obj.case_desc)+'</td></tr></table>'
		elif obj.state =='sent_mail':
			body += u'<table cellspacing="1" border="1" cellpadding="10"><tr style="background-color: #4CAF50; color: white;">'
			body += u'<th>Огноо</th><th>Салбар</th><th>Байрлал</th><th>Ээлж</th><th>Ослын тодорхойлт</th>'
			body += u'<tr><td>'+str(date_time)+'</td><td>'+str(obj.branch_id.name)+'</td><td>'+str(obj.location_id.name)+'</td><td>'+dict(obj._fields['part'].selection).get(obj.part)+'</td><td>'+str(obj.case_desc)+'</td></tr></table>'
		# elif obj.state =='cor_act_closed':
		# 	body += u'хариу арга хэмжээ авна уу'
		# 	body += u'<table cellspacing="1" border="1" cellpadding="4"><tr style="background-color: #4CAF50; color: white;">'
		# 	body += u'<th>Хариу арга хэмжээ юуг?</th><th>Хэн?</th><th>Хэрхэн яаж?</th><th>Хэзээ?</th>'
		# 	body += u'<th>Авагдсан арга хэмжээ</th><th>Арга хэмжээ авсан огноо</th></tr>'
			# for item in obj.person_about_line:
			# 	members_name = ''
			# 	for line in item.employee_id:
			# 		members_name += line.name+'<br/>'
			# 	# for line in item.partner_ids: tur haav
			# 	# 	members_name += line.name+'<br/>' tur haav
			# 	body += u'<tr><td>'+(item.corrective_action if item.corrective_action else '')+u'</td><td>'+members_name+u'</td>'
			# 	body += u'<td>'+item.how+u'</td><td>'+item.when_start+' - '+item.when_end+'</td>'
			# 	body += u'</tr>'
		mail_text=''
		if obj.mail_text:
			mail_text=obj.mail_text
		self.send_emails(u'Осол тохиолдол '+str(obj.name), body+u'<br/>'+str(mail_text))
		sent_mail_users = ''
		for item in obj.mail_line:
			sent_mail_users += item.mail+'<br/>'
		message_post = u'Дүгнэлт бичих'
		if obj.state =='sent_mail':
			message_post = u'Дугнэлт бичих'
		elif obj.state =='cor_act_closed':
			message_post = u'Хариу арга хэмжээ авагдсан'
		obj.message_post(body=(message_post+u':<br/>Дараах хүмүүст майл илгээгдэв:<br/>'+sent_mail_users), message_type='notification', subtype_xmlid="mail.mt_comment", parent_id=False)
		return True
	
	def mail_sent(self):
		obj = self
		self._get_mail()
		if obj.state =='draft':
			self.write({'state': 'sent_mail'})
		elif obj.state =='sent_mail':
			self.write({'state': 'cor_act_closed'})
		elif obj.state =='cor_act_closed':
			self.write({'state': 'closed'})
		taken_employee_id = self.env.user.employee_id.id
		self.env['hse.injury.person.line'].search( [('injury_id','=',obj.id),('is_taken','=',False)]).write({'is_taken': True, 'taken_date': datetime.now().strftime('%Y-%m-%d'), 'taken_employee_id':taken_employee_id})
		   

	def action_to_cor_act_closed(self):
		obj = self
		view_id = self.env['ir.ui.view'].search( [('model', '=', 'hse.injury.entry'), ('name', '=', 'hse.injury.entry.mail.form')])
		return {
			'name':_("Дараах хүмүүст майл илгээж мэдэгдэх"),
			'view_mode': 'form',
			'view_id': view_id.id,
			'view_type': 'form',
			'res_model': 'hse.injury.entry',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': obj.id,
			'context': self._context
		}
		
	def action_to_sent_mail(self):
		obj = self
		user_mails = []
		obj.mail_line = False
		if obj.research_team_line:
			for item in obj.research_team_line:
				user_obj = self._get_email_employee(item.employee_id, user_mails,)
				if user_obj:
					user_mails.append(user_obj['email'])
		else:
			raise UserError(_('Судалгааны багийн гишүүдийн мэдээлэл алга!!!'))
		for item in user_mails:
			data = { 
					'injury_id': obj.id,
					'mail': item,
					}
			line_id = self.env['hse.injury.entry.mail.line'].create(data)
		view_id = self.env['ir.ui.view'].search( [('model','=','hse.injury.entry'), ('name','=','hse.injury.entry.mail.form')])
		return {
			'name':_("Дүгнэлт бичих дараах хүмүүст майл илгээж мэдэгдэх"),
			'view_mode': 'form',
			'view_id': view_id.id,
			'view_type': 'form',
			'res_model': 'hse.injury.entry',
			'type': 'ir.actions.act_window',
			'target': 'new',
			'res_id': obj.id,
			'context': self._context
		}
	def action_to_closed(self):
		obj = self
		user_mails = []
		if obj.research_team_line:
			for item in obj.audit_conclusion_line:
				if not item.conclusion or not item.date:
					raise UserError(_('Дүгнэлт хоосон байна!!!'))

			# for item in obj.corrective_action_line:
			# 		for line in item.employee_ids:
			# 			user_obj = self._get_email_employee(line, user_mails)
			# 			if user_obj:
			# 				user_mails.append(user_obj['email'])
			# 		for line in item.partner_ids:
			# 			if line.email not in user_mails:
			# 				user_mails.append(line.email)
				
			
			emp_obj = self.env['hr.employee'].search( [('user_id','=',obj.branch_manager_id.id)])
			user_obj = self._get_email_employee(emp_obj, user_mails)
			if user_obj:
				user_mails.append(user_obj['email'])

			user_obj = self._get_email_employee(obj.general_master_id, user_mails)
			if user_obj:
				user_mails.append(user_obj['email'])

			user_obj = self._get_email_employee(obj.master_id, user_mails)
			if user_obj:
				user_mails.append(user_obj['email'])

			user_obj = self._get_email_employee(obj.dep_manager_id, user_mails)
			if user_obj:
				user_mails.append(user_obj['email'])

			for item in user_mails:
				data = { 
						'injury_id': obj.id,
						'mail': item,
						}
				self.env['hse.injury.entry.mail.line'].create(data)
			view_id = self.env['ir.ui.view'].search( [('model', '=', 'hse.injury.entry'), ('name', '=', 'hse.injury.entry.mail.form')])
			
			return {
				'name':_("Хариу арга хэмжээ авах дараах хүмүүст майл илгээж мэдэгдэх"),
				'view_mode': 'form',
				'view_id': view_id.id,
				'view_type': 'form',
				'res_model': 'hse.injury.entry',
				'type': 'ir.actions.act_window',
				'target': 'new',
				'res_id': obj.id,
				'context': self._context
			}       
		# else:
		# 	raise UserError(_('Хариу арга хэмжээ авах хүмүүс хоосон байна!!!'))


	def action_to_draft(self):
		self.write({'state': 'draft'})

	def import_cause(self):
		obj = self
		
		if obj.accident_line:
			return {}
		cause_ids = self.env['hse.accident.cause'].search([])
		
		for item in cause_ids:
			data = { 'injury_id': obj.id,
					 'accident_cause_id': item,
					 'type': self.env['hse.accident.factor'].browse([item.factor_id.id]).type
					 }
			line_id = self.env['hse.injury.accident.line'].create(data)
		line_ids = self.env['hse.injury.accident.line'].search( [('injury_id','=',obj.id)])
		return {
				'value': {
				'accident_line':line_ids
			}
		}

class HseInjuryEntryMailLine(models.Model):
	_name ='hse.injury.entry.mail.line'
	_description = 'Mail line'
   
	injury_id = fields.Many2one('hse.injury.entry','Injury ID', required=True, ondelete='cascade')
	mail = fields.Char('Майл', required=True)


class HseInjuryAccidentLine(models.Model):
	_name ='hse.injury.accident.line'
	_description = 'Injury accident line'
	_order = 'sequence asc'

	
	def write(self, vals):
		obj = self
		if 'check' in vals:
			factor_ids = self.env['hse.injury.factor.line'].search([('injury_id','=',obj.injury_id.id), ('factor_id','=',obj.factor_id.id)])
			if not obj.check:
				if not factor_ids:
					data = {
							'injury_id': obj.injury_id.id,
							'factor_id': obj.factor_id.id,
							'notes': obj.accident_cause_id.name
						}
					self.env['hse.injury.factor.line'].create(data)
				else:
					note = obj.accident_cause_id.name+'\n'
					for item in self.search( [('injury_id','=',obj.injury_id.id), ('factor_id','=',obj.factor_id.id), ('check','=',True)]):
						note += item.accident_cause_id.name+'\n'
					factor_ids.write({'notes': note})
			else:
				lines_ids = self.search([('injury_id','=',obj.injury_id.id), ('factor_id','=',obj.factor_id.id), ('check','=',True), ('id','!=',obj.id)])
				if lines_ids:
					note = ''
					for item in self.search( [('injury_id','=',obj.injury_id.id), ('factor_id','=',obj.factor_id.id), ('check','=',True), ('id','!=',obj.id)]):
						note += item.accident_cause_id.name+'\n'
					factor_ids.write({'notes': note})
				else:
					factor_ids.unlink()
					
		return super(HseInjuryAccidentLine, self).write(vals)
   
	injury_id = fields.Many2one('hse.injury.entry','Accident ID', required=True, ondelete='cascade')
	accident_cause_id = fields.Many2one('hse.accident.cause','Ослын шалтгаан', required=True)
	sequence = fields.Integer(related='accident_cause_id.sequence', store=True, readonly=True)
	factor_id = fields.Many2one('hse.accident.factor', related='accident_cause_id.factor_id', store=True, readonly=True)
	# state = fields.Selection(related='injury_id.state')
	type = fields.Char('Төрөл')
	check = fields.Boolean('Чагтлах')


class HseInjuryFactorLine(models.Model):
	_name ='hse.injury.factor.line'
	_description = 'Injury factor line'

   
	injury_id = fields.Many2one('hse.injury.entry', 'Accident ID', required=True, ondelete='cascade')
	notes = fields.Text('Тэмдэглэл')
	factor_id = fields.Many2one('hse.accident.factor', 'Нөлөө')
	state = fields.Selection(related='injury_id.state')
	type = fields.Char('factor_id.type', readonly=True)
	

class HseInjuryCorrectiveActionLine(models.Model):
	_name ='hse.injury.corrective.action.line'
	_description = 'Injury corrective action line'

	def action_to_taken(self):
		obj = self
		if obj.corrective_action_taken:
			if len(self.env['hse.injury.corrective.action.line'].search( [('injury_id','=',obj.injury_id.id),('is_taken','=',False)]))==1:
				view_id = self.env['ir.ui.view'].search( [('model', '=', 'hse.injury.entry'), ('name', '=', 'hse.injury.entry.mail.form')])
				return {
					'name':_("Хариу арга хэмжээ авагдлаа дараах хүмүүст майл илгээж мэдэгдэх"),
					'view_mode': 'form',
					'view_id': view_id,
					'view_type': 'form',
					'res_model': 'hse.injury.entry',
					'type': 'ir.actions.act_window',
					'target': 'new',
					'res_id': obj.injury_id.id,
					'context': context
				}
			else:
				taken_employee_id = self.env.user.id
				self.write({'is_taken': True, 'taken_date': datetime.now().strftime('%Y-%m-%d'), 'taken_employee_id':taken_employee_id})
		else:
			raise UserError(_('Авагдсан арга хэмжээнд тайлбар бичнэ үү!!!!!'))
		

   
	injury_id = fields.Many2one('hse.injury.entry','Accident ID', required=True, ondelete='cascade')
	state = fields.Selection(related='injury_id.state', readonly=True, store=True)
	corrective_action_what = fields.Char('Хариу арга хэмжээ юуг?', required=True, readonly=True, states={'draft':[('readonly',False)]})
	who = fields.Many2one('hr.employee', string='Хэн?', domain=[('employee_type', 'in', ['employee','student'])], readonly=True, states={'draft':[('readonly',False)]})
	# employee_ids = fields.Many2many('hr.employee', 'hse_injury_corrective_action_line_employee_rel', 'injury_id','employee_id', 'Хэн ажилтан', required=False, readonly=True, states={'draft':[('readonly',False)]})
	# partner_ids = fields.Many2many('hse.partner', 'hse_injury_corrective_action_line_partner_rel', 'injury_id','partner_id', 'Хэн харилцагч', required=False, readonly=True, states={'draft':[('readonly',False)]})
	how = fields.Char('Хэрхэн яаж?', required=True, readonly=True, states={'draft':[('readonly',False)]})
	when_start = fields.Date('Хэзээ эхлэх?', required=True, readonly=True, states={'draft':[('readonly',False)]})
	when_end = fields.Date('Хэзээ дуусах?', readonly=True, states={'draft':[('readonly',False)]})
	is_taken = fields.Boolean('Авагдсан эсэх', readonly=True)
	corrective_action_taken = fields.Text('Авагдсан арга хэмжээ', readonly=True, states={'closed':[('readonly',False)]})
	taken_employee_id = fields.Many2one('hr.employee','Арга хэмжээ авсан ажилтан', readonly=True)
	taken_date = fields.Date('Арга хэмжээ авсан огноо', readonly=True)
	
	
class HseInjuryAuditLine(models.Model):
	_name ='hse.injury.audit.line'
	_description = 'Injury audit line'
   
	injury_id = fields.Many2one('hse.injury.entry','Accident ID', required=True, ondelete='cascade')
	employee_id = fields.Many2one('hr.employee','Нэр', required=True, domain=[('employee_type', 'in', ['employee','student'])])
	job_id = fields.Many2one('hr.job', related='employee_id.job_id', store=True, readonly=True)

class HseInjuryPersonLine(models.Model):
	_name = 'hse.injury.person.line'
	_description = 'Injury person line'

	injury_id = fields.Many2one('hse.injury.entry','Accident ID', required=True, ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', 'Овог нэр', required=True, domain=[('employee_type', 'in', ['employee','student'])])
	company_id = fields.Many2one('res.company', related='employee_id.company_id', string="Компани")
	job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Албан тушаал', readonly=True)
	affected_condition = fields.Selection([('connect','Холбогдсон'),('witness','Гэрч')], string='Өртсөн байдал')
	age = fields.Integer('Нас', default=0)
	working_years = fields.Integer('Ажилласан жил', default=0)
	is_taken = fields.Boolean('Авагдсан эсэх', readonly=True)
	taken_employee_id = fields.Many2one('hr.employee', string='Арга хэмжээ авсан ажилтан', readonly=True)
	taken_date = fields.Date('Арга хэмжээ авсан огноо', readonly=True)
	state = fields.Selection(related="injury_id.state", string='Төлөв', store=True)
	corrective_action = fields.Char('Авсан арга хэмжээ', readonly=True, states={'draft':[('readonly',False)]})


class HseInjuryResearchTeamLine(models.Model):
	_name = 'hse.injury.research.team.line'
	_description = 'Injury research team line'

	injury_id = fields.Many2one('hse.injury.entry','Ijnjury research ID', required=True, ondelete='cascade')
	employee_id = fields.Many2one('hr.employee', 'Овог нэр', required=True, )
	job_id = fields.Many2one('hr.job', related='employee_id.job_id', string='Албан тушаал', readonly=True)
	team = fields.Selection([('leader','Багын ахлагч'),('member','Багын гишүүд')], string='Баг бүрэлдэхүүн')
	company_id = fields.Many2one('res.company', related='employee_id.company_id', string='Компани')

class HseInjuryAuditConclusionLine(models.Model):
	_name ='hse.injury.audit.conclusion.line'
	_description = 'Injury audit conclusion line'
   
	injury_id = fields.Many2one('hse.injury.entry','Accident ID', required=True, ondelete='cascade')
	state = fields.Selection(related='injury_id.state', readonly=True, store=True)
	employee_id = fields.Many2one('hr.employee','Нэр', required=True, readonly=True, states={'draft':[('readonly',False)]})
	job_id = fields.Many2one(related='employee_id.job_id', store=True, readonly=True)
	conclusion = fields.Text('Дүгнэлт', readonly=True, states={'sent_mail':[('readonly',False)]})
	date = fields.Date('Огноо', readonly=True, states={'sent_mail':[('readonly',False)]})


class InjuryReportLine(models.Model):
	_name ='hse.injury.report.line'
	_description = 'Injury report line'
   
	injury_id = fields.Many2one('hse.injury.entry','Accident ID', required=True, ondelete='cascade')
	influencing_factor_id = fields.Many2one('hse.influencing.factor', string='Нөлөөлсөн хүчин зүйл',)
	problem_about = fields.Char(string='Энэ асуудлыг засахын тулд бид юу хийх вэ?',)
	who = fields.Many2one('hr.employee', string='Хэн', required=True,)
	when = fields.Date('Хэзээ', required=True, default=fields.Date.context_today)
	end_date = fields.Date('Дууссан огноо', required=True, default=fields.Date.context_today)

class HseCodeConfig(models.Model):
	_name ='hse.code.config'
	_description = 'Code config'
	_inherit = ["mail.thread", "mail.activity.mixin"]
   
	# model_id = fields.Many2one('ir.model', 'Загвар', required=True, domain=[('model','like','hse.%')])
	branch_id = fields.Many2one('res.branch', string='Салбар', required=True)
	name = fields.Char('Нэр', required=True)

class HseAccidentCause(models.Model):
	_name ='hse.accident.cause'
	_description = 'Causes of accidents'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'sequence asc'

	sequence = fields.Integer('Дараалал')
	name = fields.Char('Шалтгаан', required=True)
	factor_id = fields.Many2one('hse.accident.factor','Нөлөө', required=True)

class HseAccidentFactor(models.Model):
	_name ='hse.accident.factor'
	_description = 'Factors in accidents'
	_inherit = ["mail.thread", "mail.activity.mixin"]
	_order = 'name asc'
   
	name = fields.Char(string='Нэр', required=True)
	type = fields.Selection([
		('immediate_cause','Immediate cause'),
		('base_cause','Base cause')], string='Type', required=True)