# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class TireInspect(models.Model):
	_name = 'tire.inspection'
	_description = 'Tire inspection'
	_order = 'date_inspection desc, date_record desc'
	_inherit = 'mail.thread'

	@api.model
	def _get_user(self):
		return self.env.user.id

	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})

	name = fields.Char(string=u'Дугаар', readonly=True, copy=False)
	date_inspection = fields.Date(u'Үзлэгийн огноо', copy=False,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})
	date_record = fields.Datetime(u'Нээсэн огноо', readonly=True,
		copy=False, default=datetime.now())

	user_id = fields.Many2one('res.users', u'Бүртгэсэн', default=_get_user, readonly=True)
	validator_id = fields.Many2one('res.users', u'Баталсан', readonly=True, copy=False,)
	operator_id = fields.Many2one('hr.employee', u'Оператор', copy=False,
		states={'done': [('readonly', True)]})

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,
		states={'open': [('readonly', True)],'done': [('readonly', True)]},
		domain=[('rubber_tired','=',True)])
	last_km = fields.Float(string='Сүүлийн KM', digits = (16,1), required=True,
		states={'done': [('readonly', True)]})
	last_odometer = fields.Float(string='Сүүлийн мото/ц', digits = (16,1), required=True,
		states={'done': [('readonly', True)]})

	inspection_type = fields.Selection([
		('tread_inspection', 'Хээний үзлэг'),
		('operation_inspection', 'Ашиглалтын үзлэг'),
		('warn_inspection', 'Анхааруулах үзлэг'),],
		string=u'Үзлэгийн төрөл', default='tread_inspection', required=True,
		states={'done': [('readonly', True)]}, copy=False )
	inspection_line = fields.One2many('tire.inspection.line', 'parent_id',
		string='Үзлэгийн мөр', required=True,
		states={'done': [('readonly', True)]})

	maintenance_note = fields.Text("Засварын тайлбар",
		states={'done': [('readonly', True)]})

	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
			string=u'Ээлж', required=True,
			states={'done': [('readonly', True)]})

	state = fields.Selection([
			('draft', u'Draft'),
			('open', u'Open'),
			('done', u'Done'),
			('cancelled', u'Cancelled'),],
			default='draft', string=u'Төлөв', tracking=True)

	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд',
		states={'done': [('readonly', True)]})

	# description = fields.Char(string=u'Дугуйчны жагсаалт')
	employee_idsd = fields.Many2many('hr.employee', string=u'Дугуйчны жагсаалт')

	@api.constrains('date_inspection','technic_id')
	def _check_date_technic_tire(self):
		for obj in self:
			check_ids = self.env['tire.inspection'].search([('date_inspection','=',obj.date_inspection),
											  ('technic_id','=',obj.technic_id.id)])
			if len(check_ids) > 1:
				raise ValidationError(_("Нэг өдөрт уг техникийн үзлэг дахин оруулах гэж байна. Өгөгдлөө шалгана уу!"))

	# Overrided methods ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Ноорог байх ёстой!'))
		return super(TireInspect, self).unlink()

	# ====== CUSTOM METHODs ===================
	@api.onchange('technic_id')
	def onchange_technic_id(self):
		self.last_km = self.technic_id.total_km
		self.last_odometer = self.technic_id.total_odometer

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_cancel(self):
		self.state = 'cancelled'

	def action_to_open(self):
		if not self.inspection_line:
			for line in self.technic_id.tire_line:
				vals = {
					'parent_id': self.id,
					'tire_id': line.tire_id.id,
					'position': line.position,
				}
				self.env['tire.inspection.line'].create(vals)

		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('tire.inspection')
		self.state = 'open'

	def action_to_done(self):
		if self.inspection_line:
			for line in self.inspection_line:
				line.tire_id.warning_deep = 'warning_check' if line.tire_status=='warning_check' else 'normal'
				# Хээний үзлэг бол
				if self.inspection_type == 'tread_inspection':
					percent = 0
					if line.tire_id.tire_setting_id.depreciation_method == 'tread_deep':
						### Хээгээр элэгдэх
						if line.tread_deep1 <= 0 or line.tread_deep2 <= 0:
							raise UserError(_('Хээний 2 хэмжээг оруулна уу, 0-ээс их байх ёстой!'))
						# Одоогийн хээнээс их оруулах, буруу оруулахыг шалгах
						if line.tread_deep1 > line.tire_id.tread_current_deep or line.tread_deep2 > line.tire_id.tread_current_deep:
							raise UserError(_('Одоо байгаа хээний гүнээс их оруулсан байна, Шалгана уу!\n%s Одоогийнх: %d' % (line.tire_id.name, line.tire_id.tread_current_deep)))

						deep_average = (line.tread_deep1 + line.tread_deep2)/2.0
						norm = line.tire_id.tire_setting_id.norm_tread_deep
						### Хээний гүн Нормоос их байвал анхааруулна
						if deep_average > norm:
							raise UserError(_('Оруулсан дундаж хээ нь дугуйн норм хээний гүнээс их байна.\n Serial %s (%.1f mm)') % (line.tire_id.serial_number,norm))

						percent = 100-(deep_average * 100)/norm
						line.depreciation = percent
						line.date = self.date_inspection
						line.tire_id.tread_current_deep = deep_average
						line.tire_id.tread_depreciation_percent = percent
						line.deep_average = deep_average
						percent = percent
					else:
						### Норм мото/цаг, Км ээр элэгдэх
						current_odometer = line.tire_id.total_moto_hour if line.tire_id.odometer_unit == 'motoh' else line.tire_id.total_km
						norm_odometer = line.tire_id.tire_setting_id.norm_moto_hour if line.tire_id.odometer_unit == 'motoh' else line.tire_id.tire_setting_id.norm_km
						percent = (current_odometer * 100.0)/norm_odometer
						line.depreciation = percent
						norm = line.tire_id.tire_setting_id.norm_tread_deep
						line.date = self.date_inspection
						line.tire_id.tread_current_deep = norm-(norm*percent)/100
						line.tire_id.tread_depreciation_percent = percent

					# Аюултай элэгдсэн бол CHAT илгээх
					if percent > line.tire_id.tire_setting_id.warning_percent:
						line.tire_id.warning_deep = 'warning'
						txt = "Дугуйн элэгдлийн анхааруулга!\n"
						txt += 'Техник:'+' ['+self.technic_id.name+']\n'
						txt += 'Дугуй: ['+line.tire_id.name+']\n'
						txt += 'Байрлал: '+ str(line.position)+'\n'
						txt += 'Элэгдэл хувь: '+str(round(percent,2))
						self.send_chat('group_technic_module_tire_amount_user', txt)
					# Хэрэв урд байрлал дээрх байгаад хойш шилжүүлэх хувь нь
					# болсон бол CHAT илгээх
					if line.position in [1,2] and percent > line.tire_id.tire_setting_id.warning_2_percent:
						txt = "Дугуйг хойд тэнхлэгт шилжүүлэх анхааруулга!\n"
						txt += 'Техник:'+' ['+self.technic_id.name+']\n'
						txt += 'Дугуй: ['+line.tire_id.name+']\n'
						txt += 'Байрлал: '+ str(line.position)+'\n'
						txt += 'Элэгдэл хувь: '+str(round(percent,2))
						self.send_chat('group_technic_module_tire_amount_user', txt)
				# Ашиглалтын үзлэг бол
				else:
					if line.temperature == 0:
						if self.inspection_type not in ['operation_inspection','warn_inspection']:
							raise UserError(_('Дугуйн Темпартурыг оруулна уу!'))
					line.date = self.date_inspection
		else:
			raise UserError(_('Дугуйн мэдээлэл олдсонгүй!'))
		self.state = 'done'

	# Чат илгээх
	def send_chat(self, group_name, text):
		res_model = self.env['ir.model.data'].search([
				('module','=','mw_technic_equipment'),
				('name','=',group_name)])
		group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))])
		partners = []
		for receiver in group.users:
			if receiver.partner_id:
				if self.env.user.partner_id.id != receiver.partner_id.id:
					partners.append(receiver.partner_id)
		html = u"<span style='font-size:10pt; color:red;'>" + self.name +u' дугуйн үзлэгээр дараах анхааруулга илгээгдлээ!\n %s</span>' % text
		# self.env.user.send_chat(html, partners)
		self.env.user.send_emails(partners=partners, body=html, attachment_ids=False)

class TireInspectLine(models.Model):
	_name = "tire.inspection.line"
	_description = "Tire Inspect Line"
	_order = 'date desc, position'

	parent_id = fields.Many2one('tire.inspection',string='Parent', ondelete='cascade')
	date = fields.Date(string='Огноо')
	technic_id = fields.Many2one(related="parent_id.technic_id", string=u'Техник',)

	tire_id = fields.Many2one('technic.tire', string='Дугуй', ondelete='cascade')
	brand_id = fields.Many2one(related="tire_id.brand_id", string=u'Үйлдвэрлэгч',)
	serial_number = fields.Char(related="tire_id.serial_number", string=u'Сериал дугаар',)
	position = fields.Integer(string=u'Байрлал', required=True)

	tread_deep1 = fields.Float(string='Хээний гүн 1',digits=(12,1), default=0)
	tread_deep2 = fields.Float(string='Хээний гүн 2',digits=(12,1), default=0)
	deep_average = fields.Float(string='Дундаж гүн',digits=(12,1), default=0, readonly=True, )
	depreciation = fields.Float(string='Элэгдлийн %', digits=(12,1), default=0)

	temperature = fields.Float(string='Темпартур', digits=(12,1), default=0)
	pressure = fields.Integer(string='Даралт')
	description = fields.Char(string='Тайлбар')

	@api.depends('parent_id.technic_id')
	def _get_before_inspection(self):
		for item in self:
			before_id = self.env['tire.inspection.line'].search([('serial_number','=',item.serial_number),('parent_id','!=',item.parent_id.id),('create_date','<',item.create_date)], order='create_date desc', limit=1)
			print(before_id, type(before_id))
			item.before_temp = before_id.temperature
			item.before_pressure = before_id.pressure

	before_temp = fields.Float(string=u'Өмнөх температур', compute='_get_before_inspection')
	before_pressure = fields.Integer(string=u'Өмнөх даралт', compute='_get_before_inspection')

	state = fields.Selection(related='parent_id.state', store=True, readonly=True, )
	tire_status = fields.Selection([
			('warning_check', u'Анхаарах'),
			('normal', u'Хэвийн'),],
			string=u'Статус', default='normal')

	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд')

	@api.onchange('tread_deep1','tread_deep2')
	def onchange_tread_deep(self):
		if self.tread_deep1 and self.tread_deep2:
			self.deep_average = (self.tread_deep1 +self.tread_deep2)/2
