# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

class TechnicComponentPart(models.Model):
	_name = 'technic.component.part'
	_description = 'Technic component part'
	_order = 'report_order, program_code, current_technic_id, sequence, name'
	_inherit = ['mail.thread']

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Auto field compute
	@api.depends('component_depreciation_lines','component_depreciation_lines.increasing_odometer')
	def _set_auto_fields(self):
		for obj in self:
			ll = obj.component_depreciation_lines.filtered(lambda l: l.is_repaired == False).mapped('increasing_odometer')
			obj.total_odometer = sum(ll)

	@api.depends('product_id','serial_number')
	def _set_name(self):
		for obj in self:
			if obj.product_id and obj.serial_number:
				obj.name = '['+obj.serial_number+'] '+obj.product_id.name
			else:
				obj.name = ""
		return True

	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})

	date_of_record = fields.Date(u'Эхлэх огноо', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	date_of_manufactured = fields.Date(u'Үйлдвэрлэсэн огноо',
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	date_of_retired = fields.Date(u'Актласан огноо', readonly=True, )
	date_of_set = fields.Date(u'Суурьлуулсан огноо', tracking=True)

	name = fields.Char(compute='_set_name',string=u'Нэр', readonly=True, store=True)
	sequence = fields.Integer(string=u'Дугаар', required=True,)
	component_config_id = fields.Many2one('technic.component.config',
		string=u'Тохиргооны мөр', readonly=True, )

	component_type = fields.Selection([
		('engine','Engine'),
		('transmission','Transmission'),
		('generator_alternator','Generator & Alternator'),
		('wheel_motor_r','Wheel motor R'),
		('wheel_motor_l','Wheel motor L')], string='Компонентийн төрөл', )

	serial_number = fields.Char(string='Сериал дугаар',
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})

	account_id = fields.Many2one('account.account', string=u'Санхүүгийн данс', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})

	product_id = fields.Many2one('product.product', string=u'Компонентийн бараа', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	real_part_number = fields.Char(string='Эд ангийн дугаар', states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})

	norm_odometer = fields.Integer(string='Exchange гүйлт', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	norm_overhaul_odometer = fields.Integer(string=u'Overhaul норм', required=True, default=0,
		# states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
		# 		'repairing':[('readonly',True)],'retired':[('readonly', True)]}
		)
	norm_reseal_odometer = fields.Integer(string=u'Reseal норм', required=True, default=0,
		# states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
		# 		'repairing':[('readonly',True)],'retired':[('readonly', True)]}
		)
	norm_rebuild_odometer = fields.Integer(string=u'Rebuild норм', required=True, default=0,
		# states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
		# 		'repairing':[('readonly',True)],'retired':[('readonly', True)]}
		)
	norm_dcheck_odometer = fields.Integer(string=u'D-Check норм', required=True, default=0)

	total_odometer = fields.Float('Нийт гүйлт', compute=_set_auto_fields, store=True, readonly=True, )
	set_odometer = fields.Float('Суурьлуулсан гүйлт', )

	last_date = fields.Date(u'Last огноо', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	last_odometer = fields.Float(u'Last засварын гүйлт', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	last_maintenance = fields.Selection([
		('exchange','Exchange'),
		('overhaul','Overhaul'),
		('reseal','Reseal')], string='Last maintenance',
		default='exchange')

	component_depreciation_lines = fields.One2many('component.depreciation.line', 'parent_id', string='Элэгдлийн түүх',
		# states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
		# 		'repairing':[('readonly',True)],'retired':[('readonly', True)]}
		)
	component_used_lines = fields.One2many('component.used.history', 'parent_id', string='Хэрэглэсэн түүх',
		# states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
		# 		'repairing':[('readonly',True)],'retired':[('readonly', True)]}
		)

	origin = fields.Char(string="Эх баримт",
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})

	current_technic_id = fields.Many2one('technic.equipment', string=u'Одоогийн техник', tracking=True)
	report_order = fields.Char(related='current_technic_id.report_order', string=u'Sort',
		store=True, readonly=True, )
	program_code = fields.Char(related='current_technic_id.program_code', string=u'Sort 2', readonly=True, store=True)

	state = fields.Selection([
		('draft','Draft'),
		('new','New'),
		('using','Using'),
		('inactive','Inactive'),
		('repairing','Repairing'),
		('retired','Retired')], string='Төлөв',
		readonly=True, default='draft', tracking=True)

	user_id = fields.Many2one('res.users', string=u'User', readonly=True,
		default=_get_user)

	retired_description = fields.Text(string=u'Актласан тайлбар', readonly=True,)
	retire_type = fields.Selection([
		('after_deadline',u'Хугацаандаа'),
		('before_dealine',u'Хугацаанаас өмнө')], string=u'Актлах төрөл', readonly=True,)
	retire_attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', readonly=True,)

	is_lv_component = fields.Boolean(string='LV component', default=False,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})

	# Баталгаат хугацаа, гүйлт
	rebuild_info = fields.Boolean(u'Rebuild info', default=False,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	overhaul_info = fields.Boolean(u'Overhaul info', default=False,
	states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
			'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	reseal_info = fields.Boolean(u'Reseal info', default=False,
	states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
			'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	d_check_info = fields.Boolean(u'D-check info', default=False,
	states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
			'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	with_warrenty = fields.Boolean(u'Warranty info', default=False,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	warranty_period = fields.Integer(string=u'Баталгааны хугацаа', help=u'Баталгаат хугацааг сараар тооцно',
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]} )
	warranty_odometer = fields.Integer(string=u'Баталгааны гүйлт', help=u'Баталгаа өгсөн гүйлт',
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]} )
	company_id = fields.Many2one('res.company', string="Компани", compute='com_company_id', store=True, tracking=True)

	@api.depends('product_id')
	def com_company_id(self):
		for item in self:
			item.company_id = item.product_id.company_id.id or False
	
	@api.depends('warranty_period','warranty_odometer','date_of_record')
	def _get_warranty_info(self):
		for obj in self:
			if obj.with_warrenty:
				txt = ""
				if obj.date_of_record and obj.warranty_period > 0:
					a = obj.date_of_record
					b = datetime.now().date()
					delta = b - a
					days = obj.warranty_period * 30
					if days > delta.days:
						date1 = obj.date_of_record
						date2 = date1 + timedelta(days=days)
						txt = u"<b style='color:green;'>Дуусах өдөр: %s, Үлдсэн: %d өдөр</b>" % (date2.strftime('%Y-%m-%d'), days-delta.days)
					else:
						txt = u"<b style='color:red;'>Баталгаа дууссан! Хэтэрсэн өдөр: %d</b>" % (delta.days-days)
				if obj.warranty_odometer > 0:
					delta = obj.warranty_odometer - obj.total_odometer
					if delta > 0:
						txt += u"<br/><b style='color:green;'>Үлдсэн: %d гүйлт</b>" % (delta)
					else:
						txt += u"<br/><b style='color:red;'>Баталгаа дууссан! Хэтэрсэн гүйлт: %d</b>" % (delta)
				obj.warranty_info = txt
			else:
				obj.warranty_info = ""
	warranty_info = fields.Html(string='Баталгааны мэдээлэл',
		readonly=True, compute="_get_warranty_info", )

	# Сүүлд нэмсэн 1.25 нд
	norm_odometer_percent = fields.Float(string='Норм гүйлт %', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))
	norm_overhaul_percent = fields.Float(string='Overhaul гүйлт %', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))
	norm_reseal_percent = fields.Float(string='Reseal гүйлт %', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))
	norm_rebuild_percent = fields.Float(string='Rebuild гүйлт %', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))
	norm_dcheck_percent = fields.Float(string='D-Check гүйлт %', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))

	diff_odometer = fields.Float(string='Зөрүү Норм гүйлт', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))
	diff_overhaul = fields.Float(string='Зөрүү Overhaul гүйлт', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))
	diff_reseal = fields.Float(string='Зөрүү Reseal гүйлт', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))
	diff_rebuild = fields.Float(string='Зөрүү Rebuild гүйлт', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))
	diff_dcheck = fields.Float(string='Зөрүү D-Check гүйлт', store=True,
		readonly=True, compute="_set_odometer_info", digits=(16,2))

	@api.depends('norm_odometer','norm_overhaul_odometer','norm_reseal_odometer','norm_rebuild_odometer','total_odometer','norm_dcheck_odometer')
	def _set_odometer_info(self):
		for obj in self:
			obj.norm_odometer_percent = (obj.total_odometer*100)/obj.norm_odometer if obj.norm_odometer != 0 else 0
			obj.diff_odometer = obj.norm_odometer - obj.total_odometer if obj.norm_odometer != 0 else 0

			obj.norm_overhaul_percent = (obj.total_odometer*100)/obj.norm_overhaul_odometer if obj.norm_overhaul_odometer != 0 else 0
			obj.diff_overhaul = obj.norm_overhaul_odometer - obj.total_odometer if obj.norm_overhaul_odometer != 0 else 0

			obj.norm_reseal_percent = (obj.total_odometer*100)/obj.norm_reseal_odometer if obj.norm_reseal_odometer != 0 else 0
			obj.diff_reseal = obj.norm_reseal_odometer - obj.total_odometer if obj.norm_reseal_odometer != 0 else 0

			obj.norm_rebuild_percent = (obj.total_odometer*100)/obj.norm_rebuild_odometer if obj.norm_rebuild_odometer != 0 else 0
			obj.diff_rebuild = obj.norm_rebuild_odometer - obj.total_odometer if obj.norm_rebuild_odometer != 0 else 0

			obj.norm_dcheck_percent = (obj.total_odometer*100)/obj.norm_dcheck_odometer if obj.norm_dcheck_odometer != 0 else 0
			obj.diff_dcheck = obj.norm_dcheck_odometer - obj.total_odometer if obj.norm_dcheck_odometer != 0 else 0

	@api.depends('norm_odometer_percent','norm_overhaul_percent','norm_reseal_percent','norm_rebuild_percent','diff_odometer','diff_overhaul','diff_reseal', 'diff_rebuild')
	def _get_odometer_info(self):
		for obj in self:
			txt = ""
			if obj.diff_odometer > 0:
				txt = u"<b style='color:green;'>Orignal хувь: %d, Мото/цаг: %d</b>" % (obj.norm_odometer_percent, obj.diff_odometer)
			else:
				txt = u"<b style='color:red;'> Orignal хувь: %d, Хэтэрсэн Мото/цаг: %d</b>" % (obj.norm_odometer_percent, obj.diff_odometer)
			if obj.diff_overhaul > 0:
				txt += u"<br/><b style='color:green;'>Overehaul хувь: %d, Мото/цаг: %d</b>" % (obj.norm_overhaul_percent, obj.diff_overhaul)
			else:
				txt += u"<br/><b style='color:red;'> Overehaul хувь: %d, Хэтэрсэн Мото/цаг: %d</b>" % (obj.norm_overhaul_percent, obj.diff_overhaul)
			if obj.diff_overhaul > 0:
				txt += u"<br/><b style='color:green;'>Reseal хувь: %d, Мото/цаг: %d</b>" % (obj.norm_overhaul_percent, obj.diff_reseal)
			else:
				txt += u"<br/><b style='color:red;'> Reseal хувь: %d, Хэтэрсэн Мото/цаг: %d</b>" % (obj.norm_overhaul_percent, obj.diff_reseal)
			obj.odometer_info = txt
			if obj.diff_overhaul > 0:
				txt += u"<br/><b style='color:green;'>Reseal хувь: %d, Мото/цаг: %d</b>" % (obj.norm_overhaul_percent, obj.diff_rebuild)
			else:
				txt += u"<br/><b style='color:red;'> Reseal хувь: %d, Хэтэрсэн Мото/цаг: %d</b>" % (obj.norm_overhaul_percent, obj.diff_rebuild)
			obj.odometer_info = txt
	odometer_info = fields.Html(string='Элэгдэл, нормын мэдээлэл',
		readonly=True, compute="_get_odometer_info", )

	# Field TEST =====================================================
	is_field_test = fields.Boolean(string='Field Test', default=False, copy=False,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	ft_inspection_method = fields.Selection([
			('every_day','1 visual inspection every day'),
			('every_week','2 visual inspection every week'),
			('every_2_week','3 visual inspection every two week'),
			('every_month','4 visual inspection every month'),
			('every_pm','5 visual inspection every PM service'),
			('every_1000hrs','6 Visual inspection every 1000hrs')],
		string='Inspection method', copy=False,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	ft_physical_inspection = fields.Selection([
			('every_day','1 visual inspection every day'),
			('every_week','2 visual inspection every week'),
			('every_2_week','3 visual inspection every two week'),
			('every_month','4 visual inspection every month'),
			('every_pm','5 visual inspection every PM service'),
			('every_1000hrs','6 Visual inspection every 1000hrs')],
		string='Physical inspection', copy=False,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	ft_frequency_hrs = fields.Integer(string='Шалгах давтамж /hrs', default=0, copy=False,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	ft_until_hrs = fields.Integer(string='Хүртэл шалгах /hrs', default=0, copy=False,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	ft_last_checked_odometer = fields.Float(string='Сүүлд шалгасан hrs', default=0, readonly=True, )
	ft_before_odometer = fields.Float(string='Анхааруулах hrs', default=50,
		help="Хэдэн мото цагийн өмнө нь анхааруулахыг зааж өгнө үү")

	field_test_line = fields.One2many('component.field.test.line', 'parent_id',
		string='Field test line', copy=False,)
	ft_next_check_odometer = fields.Integer(string='Дараагийн шалгах hrs', default=0,
		compute='_check_field_test_inspection', store=True, readonly=True, )
	ft_last_checked_date = fields.Date(string='Сүүлд шалгасан өдөр', default=False,
		compute='_check_field_test_inspection', store=True, readonly=True, )

	@api.depends('total_odometer','ft_frequency_hrs')
	def _check_field_test_inspection(self):
		for obj in self:
			if obj.is_field_test and obj.current_technic_id and isinstance(obj.id, int):
				if obj.total_odometer < obj.ft_until_hrs:
					# Мото цагын хуваарь шалгах - Хүртэл шалгах мото цаг болоогүй бол
					# Дараагийн шалгах мото цагийг олох
					if obj.ft_next_check_odometer == 0:
						obj.ft_next_check_odometer = obj.ft_frequency_hrs
					# Өмнө нь анхааруулах
					if obj.ft_next_check_odometer < obj.total_odometer+obj.ft_before_odometer:
						# Мэдэгдэл илгээх
						base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
						action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_equipment.action_technic_component_part')[2]
						html = u"""<b>%s - <a target="_blank" href=%s/web#id=%s&view_type=form&model=technic.component.part&action=%s>%s</a></b> FIELD TEST - үзлэг хийх дөхөж байна анхаарна уу!""" % (obj.current_technic_id.display_name, base_url, obj.id,action_id, obj.display_name)
						group = obj._get_send_group()
						obj._send_chat(html, group.users)
					# Хэрэв дараагийн шалгах мото цаг болсон бол
					if obj.ft_next_check_odometer < obj.total_odometer:
						# Шалгасан тэмдэглэл хөтлөх мөр нэмэх
						today = datetime.now().date()
						temp = [(0,0,{
							'date': today,
							'check_type': 'FIELD TEST - Мото цагаар',
							'technic_id': obj.current_technic_id.id,
							'technic_odometer': obj.current_technic_id.total_odometer,
							'component_odometer': obj.total_odometer,
						})]
						obj.field_test_line = temp
						obj.ft_last_checked_date = today
						obj.ft_next_check_odometer += obj.ft_frequency_hrs
						# Мэдэгдэл илгээх
						base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
						action_id = self.env['ir.model.data']._xmlid_lookup('mw_technic_equipment.action_technic_component_part')[2]
						html = u"""<b>%s - <a target="_blank" href=%s/web#id=%s&view_type=form&model=technic.component.part&action=%s>%s</a></b> FIELD TEST үзлэг хийнэ үү!""" % (obj.current_technic_id.display_name, base_url, obj.id,action_id, obj.display_name)
						group = obj._get_send_group()
						obj._send_chat(html, group.users)
			else:
				obj.ft_next_check_odometer = 0
				obj.ft_last_checked_date = False

	# Чат илгээх груп авах
	def _get_send_group(self):
		return self.env.ref('mw_technic_equipment.group_technic_module_employee')
	# Үзлэг хийх төрлөөс хэдэн мото цаг ажиллахыг олж авах
	def _get_day_interval(self):
		work_per_day = 21
		day_interval = ""
		interval_name = ""
		if self.ft_inspection_method:
			day_interval = self.ft_inspection_method
			interval_name = "Inspection method"
		if self.ft_physical_inspection:
			day_interval = self.ft_physical_inspection
			interval_name = "Physical inspection"

		if day_interval == 'every_day':
			return interval_name, 1*work_per_day
		elif day_interval == 'every_week':
			return interval_name, 7*work_per_day
		elif day_interval == 'every_2_week':
			return interval_name, 14*work_per_day
		elif day_interval == 'every_month':
			return interval_name, 30*work_per_day

	@api.onchange('ft_inspection_method')
	def onchange_ft_inspection_method(self):
		if self.ft_inspection_method:
			self.ft_physical_inspection = False
	@api.onchange('ft_physical_inspection')
	def onchange_ft_physical_inspection(self):
		if self.ft_physical_inspection:
			self.ft_inspection_method = False

	# Constraints
	_sql_constraints = [
		('component_uniq', 'unique(serial_number)', "Сериал дугаар давхардсан байна!"),
	]
	def _check_validation(self):
		for obj in self:
			if obj.norm_odometer < 0:
				return False
		return True
	@api.constrains('norm_odometer')
	def _check_current_odometer(self):
		for obj in self:
			if obj.norm_odometer < 0:
				raise ValidationError(_('Норм гүйлт 0-с бага байж болохгүй!'))

	# =================== OVERRIDED ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Ноороглох ёстой!'))
		return super(TechnicComponentPart, self).unlink()

	# =================== CUSTOM methods ===========
	# Нөхөж ашигласан түүх оруулах - Эхний үлдэгдэл
	def create_used_history(self):
		for comp in self.env['technic.component.part'].search([('component_used_lines','=',False)]):
			temp = [(0,0,{
						'date': comp.date_of_record,
						'technic_id': comp.current_technic_id.id,
						'description': "Installed"
				})]
			comp.component_used_lines = temp
		#
		for comp in self.env['technic.component.part'].search([('is_lv_component','=',True)]):
			for ll in comp.component_depreciation_lines:
				if not ll.technic_id:
					ll.technic_id = comp.current_technic_id.id or False
					break

	def write(self, vals):
		if vals.get('current_technic_id'):
			vals['state'] = 'using'
		return super(TechnicComponentPart, self).write(vals)

	# =================== CUSTOM METHODs ===========
	# Техникийн Баталгаат хугацаа шалгах - Крон метод - CRON
	def _get_warrenty_period(self):
		if self.with_warrenty:
			if self.date_of_record and self.warranty_period > 0:
				a = self.date_of_record
				b = datetime.now()
				delta = b - a
				days = self.warranty_period * 30
				return days - delta.days
			else:
				return 0
		else:
			return -1

	def _get_warrenty_odometer(self):
		if self.with_warrenty:
			if self.warranty_odometer > 0:
				delta = self.warranty_odometer - self.total_odometer
				return delta
			else:
				return 0
		return -1

	def _get_used_technics(self):
		lines = self.env['component.depreciation.line'].search([
			('parent_id','=',self.id),
			'|',('technic_id','!=',False),('is_wo_line','=',True)
			], order='date desc')
		before_datas = []
		technic_odometer = []
		park_number = []
		temp_name = ''
		for line in lines:
			if line.technic_id.program_code != temp_name or line.is_wo_line:
				if line.technic_id:
					before_datas.append(line.technic_id.program_code)
					technic_odometer.append(line.increasing_odometer)
					park_number.append(line.technic_id.park_number)
			else:
				technic_odometer[len(technic_odometer)-1] += line.increasing_odometer
			temp_name = line.technic_id.program_code

		datas = {'names': before_datas, 'datas': technic_odometer, 'park_num': park_number}
		return datas

	# Заасан техник дээр хэдэн мото цаг ажилласанг олох
	def _get_worked_odometer(self, technic_id):
		odometer = sum(self.component_depreciation_lines.filtered(lambda l: l.technic_id.id == technic_id).mapped('increasing_odometer')) or 0
		return odometer

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_repairing(self):
		self.state = 'repairing'

	def action_to_new(self):
		temp = [(0,0,{
				'date': self.date_of_record,
				'technic_id': self.current_technic_id.id,
				'technic_odometer': self.current_technic_id.total_odometer or 0,
				'component_odometer': self.total_odometer,
				'description': "Шинэ компонент бүртгэсэн"
		})]
		self.component_used_lines = temp
		self.state = 'new'

	def action_to_use(self):
		self.user_id = self.env.user.id
		# if self.sequence <= 0:
		# 	raise UserError(_(u'Sequence-ийг оруулна уу!'))
		if not self.component_config_id:
			self.set_component_config_id()
		self.state = 'using'

	def set_component_config_id(self):
		comps = self.env['technic.component.part'].search([('state','!=','draft')])
		for comp in comps:
			if comp.sequence > 0 and comp.current_technic_id:
				config_id = comp.current_technic_id.technic_setting_id.component_config_line.filtered(lambda l: l.sequence == comp.sequence)
				if len(config_id) > 1:
					warning_msj = '%d дугаартай %s-компонентын тохиргоо давхардсан(олон) байна!\n%s техникийн дээр гарлаа.' % (comp.sequence, comp.name, comp.current_technic_id.name)
					raise UserError(_(warning_msj))
				comp.component_config_id = config_id

	def action_to_inactive(self):
		# if self.sequence <= 0:
		# 	raise UserError(_(u'Sequence-ийг оруулна уу!'))
		if not self.component_config_id:
			self.set_component_config_id()
		self.state = 'inactive'

	def action_to_retire(self):
		context = dict(self._context)
		context.update({'component_id': self.id})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'technic.retire.history.wizard',
			'view_mode': 'form',
			'context': context,
			'target': 'new',
		}
	# Хөрвүүлэх
	def _unix_time_millis(self, dt):
		epoch = datetime.utcfromtimestamp(0)
		date_start = datetime.strptime(dt, "%Y-%m-%d")
		date_start += timedelta(hours=8)
		return (date_start - epoch).total_seconds() * 1000.0

	# Компонентийн МЦ, КМ нэмэгдүүлэх func
	def _increase_odometer(self, i_date, motoh, shift):
		if motoh != 0:
			current_odometer = self.total_odometer
			norm_odometer = self.norm_odometer
			odometer_value = motoh
			dep_percent = 0
			if norm_odometer > 0:
				dep_percent = (odometer_value * 100.0)/norm_odometer
			else:
				raise UserError(_('Норм гүйлтийн тохиргоо олдсонгүй!\n%s' % self.name))

			line_ids = self.env['component.depreciation.line'].search([('parent_id','=',self.id),('date','=',i_date),('shift','=',shift)])
			if line_ids:
				for line in line_ids:
					line.write( {'increasing_odometer': motoh,
								 'depreciation_percent': dep_percent,
								 'technic_odometer': self.current_technic_id.total_odometer })
			else:
				vals = {
					'parent_id': self.id,
					'date': i_date,
					'technic_id': self.current_technic_id.id,
					'technic_odometer': self.current_technic_id.total_odometer,
					'increasing_odometer': motoh,
					'depreciation_percent': dep_percent,
					'user_id': self.env.user.id,
					'shift': shift,
				}
				self.env['component.depreciation.line'].create(vals)

	# Мото цагийн түүхийг тэглэх буюу
	# Засагдсан бол нийт мото цагийг 0 болгох ёстой
	def _new_start_odometer(self, component_id):
		lines = self.env['component.depreciation.line'].search([
			('is_repaired','=',False),
			('parent_id','=',component_id)])
		for ll in lines:
			ll.is_repaired = True

	# Chat илгээх
	def _send_chat(self, txt, users):
		partners = []
		for receiver in users:
			if receiver.partner_id:
				if self.env.user.partner_id.id != receiver.partner_id.id:
					partners.append(receiver.partner_id)
		# self.env.user.send_chat(txt, partners)
		self.env.user.send_emails(partners=partners, body=txt, attachment_ids=False)

class ComponentFieldTestLine(models.Model):
	_name = 'component.field.test.line'
	_description = 'component field test line'
	_order = 'date, component_odometer'
	@api.model
	def _get_user(self):
		return self.env.user.id

	parent_id = fields.Many2one('technic.component.part', 'Parent', ondelete='cascade')

	date = fields.Date(string='Шалгах өдөр', readonly=True, )
	check_type = fields.Char(string='Төрөл', readonly=True, )
	technic_id = fields.Many2one('technic.equipment', string='Техник', readonly=True, )
	technic_odometer =  fields.Float(string='Техникийн гүйлт', digits = (16,1), readonly=True, )
	component_odometer =  fields.Float(string=u'Компонент гүйлт', digits = (16,1), )
	description =  fields.Char(string='Тайлбар', )
	is_checked =  fields.Boolean(string='Шалгасан', default=False, )
	is_success =  fields.Boolean(string='Амжилттай?', default=False, )
	user_id = fields.Many2one('res.users', string='Бичсэн хэрэглэгч', default=_get_user, required=True,)

	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', )

	@api.onchange('is_checked')
	def onchange_is_checked(self):
		if self.is_checked and not self.description:
			raise UserError(_('Тайлбарыг оруулна уу!'))
		self.user_id = self.env.user.id

class ComponentDepreciationLine(models.Model):
	_name = 'component.depreciation.line'
	_description = 'component depreciation history'
	_order = 'date desc, create_date desc'

	parent_id = fields.Many2one('technic.component.part', 'Parent', ondelete='cascade')

	date = fields.Date(string='Огноо', required=True)
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	technic_odometer =  fields.Float(string='Техникийн гүйлт',digits = (16,1))
	increasing_odometer =  fields.Float(string=u'Нэмэгдүүлсэн гүйлт',digits = (16,1))
	depreciation_percent =  fields.Float(string='Элэгдлийн хувь', digits = (16,2), required=True)
	user_id = fields.Many2one('res.users', string='Бүртгэсэн',)
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
			string=u'Ээлж',)
	is_repaired =  fields.Boolean('Old history', default=False, readonly=True, )
	is_wo_line =  fields.Boolean('WO line', default=False, )

class ComponentUsedHistory(models.Model):
	_name = 'component.used.history'
	_description = 'Component used history'
	_order = 'date desc, create_date desc'

	parent_id = fields.Many2one('technic.component.part', 'Parent', ondelete='cascade')

	date = fields.Date(string='Огноо', required=True,)
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	technic_odometer =  fields.Float(string='Техникийн гүйлт',digits = (16,1))
	component_odometer =  fields.Float(string='Компонентийн гүйлт',digits = (16,1))
	description = fields.Char(string='Тайлбар',)

class TechnicComponentConfig(models.Model):
	_name = 'technic.component.config'
	_description = 'Technic Component Config'
	_order = 'sequence, component_id'
	_rec_name = 'component_id'
	_inherit = ['mail.thread']

	parent_id = fields.Many2one('technic.equipment.setting', string=u'Модел тохиргоо', ondelete='cascade', tracking=True)
	component_id = fields.Many2one('product.product', string=u'Компонентийн нэр', required=True, tracking=True)

	norm_odometer = fields.Integer(string='Exchange норм', required=True, default=0, tracking=True)
	norm_overhaul_odometer = fields.Integer(string=u'Overhaul норм', required=True, default=0, tracking=True)
	norm_reseal_odometer = fields.Integer(string=u'Reseal норм', required=True, default=0, tracking=True)
	norm_rebuild_odometer = fields.Integer(string=u'Rebuild норм', required=True, default=0, tracking=True)
	norm_dcheck_odometer = fields.Integer(string=u'D-Check норм', required=True, default=0, tracking=True)

	work_time = fields.Float(string=u'Засварын цаг(Ex)', required=True, default=0, tracking=True)
	work_time_overhaul = fields.Float(string=u'Засварын цаг(OH)', required=True, default=1, tracking=True)
	work_time_reseal = fields.Float(string=u'Засварын цаг(Rs)', required=True, default=1, tracking=True)
	work_time_dcheck = fields.Float(string=u'Засварын цаг(D-check)', required=True, default=1, tracking=True)

	amount_exchange = fields.Float(string=u'Мөнгөн дүн(EX)', required=True, default=1, tracking=True)
	amount_overhaul = fields.Float(string=u'Мөнгөн дүн(OH)', required=True, default=1, tracking=True)
	amount_reseal = fields.Float(string=u'Мөнгөн дүн(Rs)', required=True, default=1, tracking=True)
	amount_d_check = fields.Float(string=u'Мөнгөн дүн(D-check)', required=True, default=1, tracking=True)

	qty = fields.Float(string=u'Тоо хэмжээ', required=True, default=1, tracking=True)

	sequence = fields.Integer(string='Дугаар', required=True, tracking=True)
	# Position
	position_x = fields.Float(string=u'Байрлал X', copy=False, required=False, tracking=True)
	position_y = fields.Float(string=u'Байрлал Y', copy=False, required=False, tracking=True)
	company_id = fields.Many2one('res.company', string="Компани", compute='com_company_id', store=True, tracking=True)

	@api.depends('component_id')
	def com_company_id(self):
		for item in self:
			item.company_id = item.component_id.company_id.id or False
