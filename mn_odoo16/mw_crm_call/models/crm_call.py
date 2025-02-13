# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from functools import reduce
from odoo import _, api, fields, models
import datetime
from odoo.exceptions import UserError

class res_partner(models.Model):
	_inherit = 'res.partner'
	
	crm_call_ids = fields.One2many('crm.call', 'partner_id', string='Дуудлагууд', readonly=True, compute_sudo=True )
	crm_call_count = fields.Integer('Дуудлагын тоо', compute='com_crm_call_count', readonly=True)
	
	@api.depends('crm_call_ids')
	def com_crm_call_count(self):
		for item in self:
			item.crm_call_count = len(item.sudo().crm_call_ids)

class crm_call(models.Model):
	_name = 'crm.call'
	_description = 'crm call'
	_order = 'date desc'
	_inherit = ["mail.thread", "utm.mixin", "mail.activity.mixin"]
	
	@api.model
	def default_name(self):
		return self.env.context.get('utas',False)

	create_date = fields.Datetime(string="Үүсгэсэн огноо", readonly=True)
	user_id = fields.Many2one("res.users", string="Хариуцагч",default=lambda self:self.env.user,)
	assigned_user_id = fields.Many2one("res.users", string="Дуудлага шилжүүлэх ажилтан")
	partner_id = fields.Many2one("res.partner", string="Харилцагч", index=True)
	before_crm_call_ids = fields.Many2many('crm.call', string="Дуудлагууд",
										compute="compute_call_histories", compute_sudo=True, 
										readonly=True)
	partner_depend_deed_ids = fields.One2many('res.partner.depend.partner',  related='partner_id.partner_depend_deed_ids', string='Юу болохууд', readonly=True)
	partner_depend_real_ids = fields.One2many('res.partner.depend.partner',  related='partner_id.partner_depend_real_ids',string='Холбоо барих', readonly=True)
	vat = fields.Char(related='partner_id.vat', string='Регистр', readonly=True)
	gender = fields.Selection(related='partner_id.gender', readonly=True)
	lastname = fields.Char(related='partner_id.lastname', readonly=True)
	company_id = fields.Many2one("res.company", string="Компани", default=lambda self: self.env.user.company_id)
	description = fields.Text('Нэмэлт Тайлбар')
	state = fields.Selection([
		("draft", "Ноорог"),
		("pending", "Шилжүүлсэн"),
		("done", "Хаасан"),
	],string="Төлөв", tracking=True, default="draft")
	date_open = fields.Datetime(string="Нээсэн огноо", readonly=True, tracking=True, default=lambda self: fields.Datetime.now())
	name = fields.Char(string="Утасны дугаар", required=True, default=default_name)
	call_type_id = fields.Many2one('crm.call.conf', string="Дуудлагын төрөл", required=False)
	call_type = fields.Char(string="Дуудлагg төрөл", compute='_compute_call_type')
	active = fields.Boolean(required=False, default=True)
	duration = fields.Float(string='Үргэлжилсэн хугацаа', default=0)
	partner_phone = fields.Char(string="Утасны дугаар")
	priority = fields.Selection([
		("0", "Бага"), 
		("1", "Хэвийн"), 
		("2", "Өндөр")
	] ,string="Зэрэглэл", default="1")
	date_closed = fields.Datetime(string="Хаасан", readonly=True, tracking=True)
	date = fields.Datetime(string='Товлох Огноо', default=lambda self: fields.Datetime.now(), tracking=True)
	direction = fields.Selection([
		("in", "Ирэх"), 
   		("out", "Гарах")
	], default="out", required=True, string="Дуудлага чиглэл")
	is_user_working = fields.Boolean('Is the Current User Working', compute='compute_working_users', help="Technical field indicating whether the current user is working. ")
	number = fields.Char('Дугаарлалт', readonly=True)
	lead_id = fields.Many2one('crm.lead', string="Сэжим")
	feedback_id = fields.Many2one('mw.feedback', string="Санал гомдол")
	lead_sent = fields.Boolean(string="Боломж үүсгэх", default=False)
	complaint_sent = fields.Boolean(string="Гомдол үүсгэх", default=False)

	@api.depends('partner_id')
	@api.onchange('partner_id')
	def compute_call_histories(self):
		for item in self.sudo():
			if item.partner_id:
				before_crm_call_ids = self.env['crm.call'].sudo().search([('partner_id','=',item.partner_id.id),('id','!=', item._origin.id)])
				item.before_crm_call_ids = [(6,0, before_crm_call_ids.ids)]
			else:
				item.before_crm_call_ids = False

	def action_to_done(self):
		self.state='done'

	def action_to_next(self):
		if not self.assigned_user_id:
			raise UserError(_(u'Шилжүүлэх ажилтанаа сонгоно уу!!!'))
		self.state = 'pending'
	

	def create_lead(self):
		partner_ids = []
		if self.lead_id:
			raise UserError(_(u'Сэжим үүссэн байна!'))
		else:
			vals={
				'call_id' : self.id,
				'phone' : self.name,
				'partner_id' : self.partner_id.id,
				'user_id' : self.assigned_user_id.id,
				'hariltsagchiin_tuluv': 'new',
				'sale_type':'new1',
			}
			call_lead_id = self.env['crm.lead'].create(vals)
			self.lead_id = call_lead_id.id
			partner_ids.append(self.assigned_user_id.partner_id.id)
			base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
			action_id = self.env['ir.model.data'].get_object_reference('crm', 'crm_lead_all_leads')[1]
			html = u'<b>Дуудлагаас үүссэн сэжим.</b><br/>'
			html += u"""<b><a target="_blank" href=%s/web#id=%s&view_type=form&model=crm.lead&action=%s>%s</a></b>, сэжим үүссэн байна."""% (base_url,call_lead_id.id,action_id,self.lead_id.name)
			self._send_chat(html, self.env['res.partner'].browse(partner_ids))
			self.action_to_sent_call()

	def create_feedback(self):
		partner_ids = []
		obj = self.env['mdl.feedback.conf'].search([('feedback_type','=','general')], limit=1)
		for item in self:
			if item.feedback_id:
				raise UserError(_(u'Санал, гомдол үүссэн байна!'))
			else:
				vals={
					'partner_phone' : item.name,
					'partner_id' : item.partner_id.id,
					'user_id' : item.assigned_user_id.id,
					'date_open' : str(fields.Datetime.now()),
					'feedback_turul': 'gomdol',
					'feedback_suvag':'zaal',
					'feedback_line_ids' : [(0,0,{'feedback_type_id':obj.id,'feedback_desc':item.call_serv_line_id_2.crm_call_desc})]
				}
				call_feedback_id = item.env['mw.feedback'].create(vals)
				item.feedback_id = call_feedback_id.id
				item.feedback_id.service_call_id = item.id
				partner_ids.append(self.assigned_user_id.partner_id.id)
				base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
				action_id = self.env['ir.model.data'].get_object_reference('mandal_insur', 'mdl_feedback_inher_form')[1]
				html = u'<b>Дуудлагаас үүссэн санал гомдол.</b><br/>'
				html += u"""<b><a target="_blank" href=%s/web#id=%s&action=%s&model=mw.feedback&view_type=form&>%s</a></b>, -с санал гомдол үүссэн байна."""% (base_url,call_feedback_id.id,action_id,item.number)
				self._send_chat(html, self.env['res.partner'].browse(partner_ids))
				self.action_to_sent_call()

			


	@api.depends('date_closed','date_open','state')
	def compute_working_users(self):
		for item in self:
			if (item.date_closed and item.date_open) or item.state=='cancel':
				item.is_user_working = False
			else:
				item.is_user_working = True
		
	@api.depends('call_type_id')
	def _compute_call_type(self):
		for item in self:
			item.call_type = item.call_type_id.call_type

	@api.onchange("name")
	def on_change_number(self):
		"""Contact number details should be change based on partner."""
		# if not self.partner_id:

		self.partner_id = self.env['res.partner'].sudo().search(['|',('phone','ilike',self.name),('mobile','ilike',self.name)], limit=1).id or False
			# 

	# @api.model
	# def create(self, vals):
	# 	if vals.get("state"):
	# 		if vals.get("state") == "done":
	# 			vals["date_closed"] = fields.Datetime.now()
	# 			self.compute_duration()
	# 		elif vals.get("state") == "draft":
	# 			vals["duration"] = 0.0
	# 	if vals.get('number', 'Шинэ') == 'Шинэ':
	# 		vals['number'] = self.env['ir.sequence'].next_by_code('crm.call') or 'Шинэ'
	# 	if 'date_open' in vals:
	# 		vals["duration"] = (datetime.datetime.now() - datetime.datetime.strptime(vals['date_open'], '%Y-%m-%d %H:%M:%S')).seconds
	# 	result = super().create(vals)
	# 	return result

	
	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|',  ('name', operator, name), ('number', operator, name)]
		tv = self.search(domain + args, limit=limit)
		return tv.name_get()

	def name_get(self):
		res = []
		for item in self:
			name = item.name or ''
			if item.number:
				name = item.name+' [ ' + item.number+' ]'
			res.append((item.id, name))
		return res

	def write(self, values):
		"""Override to add case management: open/close dates."""
		if values.get("state"):
			if values.get("state") == "done":
				values["date_closed"] = datetime.datetime.now()
				# self.compute_duration()
		values["duration"] = (datetime.datetime.now() - self.date_open).seconds
		
		return super().write(values)

	def compute_duration(self):
		"""Calculate duration based on phonecall date."""
		phonecall_dates = self.filtered("date")
		phonecall_no_dates = self - phonecall_dates
		for phonecall in phonecall_dates:
			if phonecall.duration <= 0 and phonecall.date:
				duration = fields.Datetime.now() - phonecall.date
				values = {"duration": duration.seconds / 60.0}
				phonecall.write(values)
			else:
				phonecall.duration = 0.0
		phonecall_no_dates.write({"duration": 0.0})
		return True
	
	def action_view_form(self):
		action = self.env.ref('mw_crm_call.crm_call_action')
		result = action.read()[0]
		res = self.env.ref('mandal_service_call.crm_call_form_inh_view', False)
		result['views'] = [(res and res.id or False, 'form')]
		result['res_id'] = self.id
		return result

class crm_call_conf(models.Model):
	_name = 'crm.call.conf'
	_description = 'crm call conf'
	_order = 'sequence'

	sequence = fields.Integer(string="Дараалал", default=1)
	name = fields.Char(string="Нэр", required=True)
	call_type = fields.Char(string="Төрлийн статик", required=True)
	