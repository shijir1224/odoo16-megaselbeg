# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time
import collections

class technicOInspectionCategory(models.Model):
	_name = 'technic.inspection.category'
	_description = 'technic inspection category'

	name = fields.Char(string='Үзлэг хийх төрөл')

class TechnicInspectionPackage(models.Model):
	_name = 'technic.inspection.package'
	description = 'technic inspection package'

	name = fields.Char(string='Үзлэгийн багц')
	company_id = fields.Many2one('res.company', string='Компани')
	inspection_ids = fields.Many2many('technic.inspection.item', string="Үзлэгийн зүйл")
	category_id = fields.Many2one('technic.inspection.category', string='Үзлэг хийх төрөл')

class TechnicInspectItem(models.Model):
	_name = 'technic.inspection.item'
	_description = 'Technic Inspect Item'
	_order = 'category, number, name'

	name = fields.Char(string=u'Нэр', size=256, required=True,)
	number = fields.Integer(string=u'Дугаар', )
	is_important = fields.Boolean(string='Чухал эсэх', default=False, )
	image = fields.Binary(string=u'Зураг', attachment=True,
		help="This field holds the image used as logo for the brand, limited to 1024x1024px.")
	# package_id = fields.Many2one('technic.inspection.package', string='Үзлэгийн багц')

	category = fields.Selection([
		('ground','GET'),
		('engine','Engine'),
		('transmission','Transmission'),
		('cab','Cab'),
		('electric','Electric'),
		('hydraulic','Hydraulic'),
		('steering','Steering'),
		('breaking','Brake'),
		('frame_body','Frame and Body'),
		('operating','Operating'),
		('power_train','Power train'),
		('implements','Implements'),
		('lubrication','Lubrication'),
		('cooling_system','Cooling system'),
		('attachment','Attachment'),
		('travel','Travel'),
		('gas system','Gas system'),
		('tire','Tire'), 
		('safety','Safety')], string='Ангилал', required=True)

	_sql_constraints = [
		('name_uniq', 'unique(name,company_id)', 'Нэр давхардсан байна!'),
	]
	company_id = fields.Many2one('res.company', string="Компани")

class TechnicInspectSetting(models.Model):
	_name = "technic.inspection.setting"
	_description = "Technic Inspect Setting"

	name = fields.Char(string=u'Нэр', size=256, required=True,)
	item_line = fields.Many2many('technic.inspection.item', string='Үзлэгийн зүйл', required=True)
	package_ids = fields.Many2many('technic.inspection.package', string='Үзлэгийн багц')
	attachment_id = fields.Binary(string=u'Хэвлэх загвар', attachment=True,)
	reminder_note = fields.Char(string='Үзлэгийн хийх санамж')
	file_name = fields.Char('Файл')
	company_id = fields.Many2one('res.company', string="Компани")

	_sql_constraints = [
		('name_uniq', 'unique(name,company_id)', 'Нэр давхардсан байна!'),
	]

	def print_template(self, ids):
		headers = [u' № ',u'Үзлэгийн нэр',u' Хэвийн эсэх', u'Тайлбар']
		datas = []
		obj = self.env['technic.inspection.setting'].search([('id','=',ids)])
		categ_temp = ''
		for line in obj.item_line:
			categ_name = dict(line._fields['category'].selection).get(line.category)
			if categ_temp != categ_name:
				temp = ['',' - "'+categ_name+'"', '', '']
				datas.append(temp)
				categ_temp = categ_name

			desc = '__________________'
			temp = [str(line.number),(line.name), "__", desc]
			datas.append(temp)

		res = {'header': headers, 'data':datas}
		return res

	def refresh_inspection_package(self):
		self.ensure_one()
		inspections = self.package_ids.mapped('inspection_ids')
		for inspection_id in inspections:
			self.item_line = [(4, inspection_id.id)]

class TechnicInspect(models.Model):
	_name = 'technic.inspection'
	_description = 'Technic inspection'
	_order = 'date_inspection desc, date_record desc'
	_inherit = 'mail.thread'

	@api.model
	def _get_user(self):
		return self.env.user.id

	@api.model
	def _get_type(self):
		context = dict(self._context)
		if 'inspection_type' in context and context['inspection_type'] == 'daily':
			return 'daily'
		return 'pm'

	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})

	name = fields.Char(string=u'Дугаар', readonly=True,)
	date_inspection = fields.Date(u'Үзлэгийн огноо', required=True, copy=False,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})
	date_record = fields.Datetime(u'Нээсэн огноо', readonly=True,
		copy=False, default=datetime.now())

	user_id = fields.Many2one('res.users', u'Клерк', default=_get_user, readonly=True)
	operator_id = fields.Many2one('hr.employee', u'Оператор', copy=False,
		states={'done': [('readonly', True)]})
	# category_id = fields.Many2one('technic.inspection.category', string='Үзлэг хийх төрөл')
	inspection_config_id = fields.Many2one('technic.inspection.setting',
		string=u'Үзлэгийн тохиргоо', required=True,)

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})
	km_value = fields.Float(string='KM', digits = (16,1),
		states={'done': [('readonly', True)]})
	odometer_value = fields.Float(string='Гүйлт', digits = (16,1), required=True,
		states={'done': [('readonly', True)]})

	inspection_line = fields.One2many('technic.inspection.line', 'parent_id',
		string='Үзлэгийн мөр', required=True,
		states={'done': [('readonly', True)]})

	inspection_type = fields.Selection([
			('daily', u'Өдөр дутмын'),
			('pm', u'PM-ын үзлэг'),],
			string=u'Үзлэгийн төрөл', default=_get_type, readonly=True, )

	previous_operator_note = fields.Text("Операторын өмнөх тэмдэглэл", readonly=True)
	origin = fields.Text(u"Эх баримт", readonly=True)

	operator_note = fields.Text("Операторын тэмдэглэл",
		states={'done': [('readonly', True)]})
	maintenance_note = fields.Text("Засварын тэмдэглэл",
		states={'done': [('readonly', True)]})

	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
			string=u'Ээлж', required=True,
		states={'open': [('readonly', True)],'done': [('readonly', True)]})

	state = fields.Selection([
			('draft', u'Draft'),
			('open', u'open'),
			('done', u'Done'),
			('cancelled', u'Cancelled'),],
			default='draft', string=u'Төлөв', tracking=True)

	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд',
		states={'done': [('readonly', True)]})

	setting_name = fields.Char(string=u'Тохиргооны нэр', readonly=True,)
	reminder_note = fields.Char(string='Үзлэгийн хийх санамж', readonly=True)

	def _check_date_technic(self):
		for obj in self:
			check_ids = self.env['technic.inspection'].search([('date_inspection','=',obj.date_inspection),
											  ('technic_id','=',obj.technic_id.id),
											  ('shift','=',obj.shift),
											  ('inspection_type','=',obj.inspection_type)])
			if len(check_ids) > 1:
				return False
		return True

	# Overrided methods ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Must be 	!'))
		return super(TechnicInspect, self).unlink()

	# ==== CUSTOM METHODs ===============
	# ====== CUSTOM METHODs ===================
	# @api.onchange('technic_id')
	# def onchange_technic_id(self):
	# 	self.km_value = self.technic_id.total_km
	# 	self.odometer_value = self.technic_id.total_odometer

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_cancel(self):
		self.state = 'cancelled'

	def get_inspection(self):
		ctx = dict(self._context or {})
		if 'inspection_id' in ctx:
			return self.env['technic.inspection.setting'].browse(ctx['inspection_id'])
		else:
			return self.technic_id.technic_setting_id.inspection_config_id

	def action_to_open(self):
		if not self.inspection_line:
			inspection_setting = self.get_inspection()

			if inspection_setting:
				for line in inspection_setting.item_line:
					vals = {
						'parent_id': self.id,
						'item_id': line.id,
						'check_name': line.name,
						'is_check': True,
					}
					self.env['technic.inspection.line'].create(vals)
				# Өмнөх үзлэгийн тайлбар
				last_ins = self.env['technic.inspection'].search([
					('technic_id','=',self.technic_id.id),
					('state','=','done')], order="date_inspection desc", limit=5)
				notes= ''
				for ll in last_ins:
					if ll.operator_note:
						notes += ll.date_inspection.strftime("%Y-%m-%d")+' : \n('+ll.operator_note+')\n'
				self.previous_operator_note = notes
			else:
				raise UserError(_('Not found Inspection list configuration!'))

		if not self.name:
			self.name = self.env['ir.sequence'].next_by_code('technic.inspection')
		self.setting_name = self.technic_id.technic_setting_id.inspection_config_id.name or ' - '
		self.state = 'open'
		self.reminder_note = self.technic_id.technic_setting_id.inspection_config_id.reminder_note

	def action_to_done(self):
		for line in self.inspection_line:
			if not line.is_check and line.item_id.is_important and not line.description:
				raise UserError(_(u'%s - үзлэг нь чухал тул ямар нэгэн тайлбар бичнэ үү!'%line.check_name))
		self.state = 'done'
		self.user_id = self.env.user.id
		# Хэрэв ТББ тооцох биш буюу хөнгөн тэрэг бол
		# Мото цаг, Км ийг update хийнэ
		if not self.technic_id.is_tbb_report:
			if self.odometer_value <= 0 and self.km_value <= 0:
				raise UserError(_(u'Мото цаг эсвэл КМ ийн заалтыг оруулна уу!'))

			self.technic_id.sudo()._increase_odometer(self.date_inspection, self.odometer_value, self.km_value, 0, 0, self.shift)

	def get_lines(self, ids):
		headers = [u' № ',u'Үзлэгийн нэр',u' Хэвийн эсэх', u'Тайлбар']
		datas = []
		obj = self.env['technic.inspection'].search([('id','=',ids)])
		categ_temp = ''
		for line in obj.inspection_line:
			categ_name = dict(line.item_id._fields['category'].selection).get(line.category)
			if categ_temp != categ_name:
				temp = ['',' - "'+categ_name+'"', '', '']
				datas.append(temp)
				categ_temp = categ_name

			check = u'Тийм' if line.is_check else u'Үгүй'
			desc = line.description if line.description else '__________________'
			temp = [str(line.number),(line.item_id.name), check, desc]
			datas.append(temp)

		res = {'header': headers, 'data':datas}
		return res

	def print_inspection(self):
		model_id = self.env['ir.model'].sudo().search([('model','=','technic.inspection')], limit=1)
		template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id),('name','=','default')], limit=1)

		if template:
			res = template.sudo().print_template(self.id)
			_logger.info('res technic.inspection: {0}'.format(res))
			return res
		else:
			raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

class TechnicInspectLine(models.Model):
	_name = "technic.inspection.line"
	_description = "Technic Inspect Line"
	_order = 'category, number, check_name'
	_rec_name = 'check_name'

	parent_id = fields.Many2one('technic.inspection',string='Parent', ondelete='cascade')
	state = fields.Selection(related='parent_id.state', readonly=True, store=True)
	item_id = fields.Many2one('technic.inspection.item',string='Үзлэг', required=True,)
	category = fields.Selection(related='item_id.category', readonly=True, store=True)
	number = fields.Integer(related='item_id.number', readonly=True, store=True)
	check_name = fields.Char('Үзлэгийн нэр', size=256, required=True)
	is_check = fields.Boolean('Хэвийн эсэх', default=True, )
	description = fields.Char('Тайлбар', size=256)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд')

	@api.onchange('description')
	def onchange_description(self):
		if self.description:
			self.is_check = False
