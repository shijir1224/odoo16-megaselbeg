# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
import collections

import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO

class TechnicTireSetting(models.Model):
	_name = 'technic.tire.setting'
	_description = 'Setting of the technic tire'
	_order = 'name'

	@api.depends('model_id')
	def _set_name(self):
		for obj in self:
			if obj.model_id:
				obj.name = obj.model_id.name+' ('+obj.norm_tire_size+')'

	name = fields.Char(compute='_set_name',string=u'Нэр', readonly=True, store=True)
	model_id = fields.Many2one('technic.model.model', string=u'Загвар', required=True,)

	norm_tire_size = fields.Char(string='Дугуйн хэмжээ', size=32, required=True)
	norm_tread_deep = fields.Integer(string='Хээний гүний норм', required=True,help='mm unit')
	norm_pressure = fields.Float(string='Дугуйн даралтын норм', required=True,help='psi unit')
	norm_moto_hour = fields.Float(string='Мото/ц норм', help='Required on mining vehicles')
	norm_km = fields.Float(string='Километрын норм', help='Required on service cars')
	purchase_value = fields.Float(string='Худалдаж авсан үнэ', required=True, digits = (16,1),)
	warning_percent = fields.Float(string='Ашиглалтын анхааруулах %', required=True, digits = (16,1), default=90,
		help="Дугуйн элэгдлийн хувь нь аюултай хэмжээнд хүрсэн үед анхааруулна")
	warning_2_percent = fields.Float(string='Шилжүүлэх үеийн анхааруулах %', required=True, digits = (16,1), default=30,
		help="Дугуйг хойд тэнхлэг рүү шилжүүлэх үеийн анхааруулах хувь")

	monthly_odometer_norm = fields.Integer(string='Сарын норм', required=True, help=u'Сард ажиллах мото цаг норм')

	odometer_unit = fields.Selection([
		('km','Km'),
		('motoh','Moto/h')], string='Гүйлтийн нэгж',
		required=True, help='Km on service cars, Moto/h on mining vehicles')

	depreciation_method = fields.Selection([
		('tread_deep','Хээний гүнээр'),
		('norm_odometer','Гүйлтийн нормоор')], string='Элэгдэл бодох арга', default='tread_deep',
		required=True, help=u'Хээний элэгдлийн хувийг бодох аргачлал. Хээний гүнээс эсвэл Норм мото/цаг, Км')
	# Сүүлд нэмсэн
	width = fields.Float(string='Өргөн(mm)', digits = (16,1), default=0,)
	height = fields.Float(string='Өндөр(mm)', digits = (16,1), default=0,)
	weight = fields.Float(string='Жин(kg)', digits = (16,1), default=0,)

	tkph = fields.Char(string='TKPH', )
	tra_code = fields.Char(string='TRA code', )
	tread_type = fields.Char(string='Хээний төрөл', )

	product_id = fields.Many2one('product.product', string=u'Холбоотой бараа', )
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', )

class TechnicTire(models.Model):
	_name = 'technic.tire'
	_description = 'Technic tire'
	_inherit = 'mail.thread'
	_order = 'name'

	@api.depends('model_id','serial_number')
	def _set_name(self):
		for obj in self:
			if obj.serial_number:
				obj.name = '['+obj.serial_number+'] '+(obj.brand_id.name or '')
			else:
				obj.name = "New"
	@api.model
	def _get_user(self):
		return self.env.user.id

	# Auto field compute
	@api.depends('tire_depreciation_lines','total_moto_hour','total_km')
	def _set_auto_fields(self):
		for obj in self:
			obj.residual_value = obj.purchase_value - sum(obj.tire_depreciation_lines.mapped('depreciation_amount'))
			obj.total_moto_hour = sum(obj.tire_depreciation_lines.mapped('increasing_odometer'))
			obj.total_km = sum(obj.tire_depreciation_lines.mapped('increasing_km'))
	branch_id = fields.Many2one('res.branch', string=u'Салбар', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})

	date_of_record = fields.Date(string=u'Эхлэх огноо', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	date_of_manufactured = fields.Date(string=u'Үйлдвэрлэсэн огноо', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	date_of_retired = fields.Date(string=u'Актласан огноо', readonly=True, )

	name = fields.Char(compute='_set_name',string=u'Нэр', readonly=True, store=True)
	serial_number = fields.Char(string='Сериал дугаар', required=True,
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	tire_setting_id = fields.Many2one('technic.tire.setting', string=u'Тохиргоо',
		help='Tire norn and setting',
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	# RELATED fields
	model_id = fields.Many2one(related='tire_setting_id.model_id', string='Загвар', readonly=True, store=True)
	brand_id = fields.Many2one(related='model_id.brand_id', string='Үйлдвэрлэгч', readonly=True, store=True)

	tkph = fields.Char(related='tire_setting_id.tkph', string='TKPH', store=True, readonly=True, )
	tra_code = fields.Char(related='tire_setting_id.tra_code', string='TRA code', store=True, readonly=True, )
	tread_type = fields.Char(related='tire_setting_id.tread_type', string='Хээний төрөл', store=True, readonly=True, )

	norm_tire_size = fields.Char(related='tire_setting_id.norm_tire_size', string='Дугуйн хэмжээ',
		store=True, readonly=True, )
	norm_tread_deep = fields.Integer(related='tire_setting_id.norm_tread_deep', string='Хээний гүний норм',
		help='mm Unit', store=True, readonly=True, )
	odometer_unit = fields.Selection(related='tire_setting_id.odometer_unit', string='Гүйлтийн нэгж',
		readonly=True, store=True)
	depreciation_method = fields.Selection(related='tire_setting_id.depreciation_method', string='Элэгдэл бодох арга',
		readonly=True, store=True)

	purchase_value = fields.Float(string='Худалдаж авсан үнэ', required=True, digits = (16,1),
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	residual_value = fields.Float(string='Үлдэгдэл өртөг', digits = (16,1), readonly=True,
		compute=_set_auto_fields, store=True, default=0)

	total_moto_hour = fields.Float(string='Нийт мото/ц', help='Required on mining vehicles',
		compute=_set_auto_fields, store=True, default=0)
	total_km = fields.Float(string='Нийт КМ',help='Required on service cars',
		compute=_set_auto_fields, store=True, default=0)

	tread_current_deep = fields.Float(string='Одоогийн хээний гүн', digits = (16,1),
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	tread_depreciation_percent = fields.Float(string='Хээний элэгдлийн %',
		digits = (16,1), )
	warning_deep = fields.Selection([
			('normal','Хэвийн'),
			('warning_check','Анхаарах, аюултай'),
			('warning','Хээний гүн аюултай'),], default='normal',
		string=u'Анхааруулах статус', readonly=True)

	# Шинэ дугуй тавьсан эсвэл Шилжүүлсэн эсэх
	new_or_old = fields.Selection([
			('new_tire_set','Шинэ дугуй суурьлуулсан'),
			('old_tire_set','Хуучин дугуй суурьлуулсан'),],
		string=u'Дугуйны шилжилт', readonly=True)

	current_technic_id = fields.Many2one('technic.equipment', string=u'Одоогийн техник')
	current_position = fields.Integer(string=u'Одоогийн байрлал')
	technic_odometer = fields.Integer(string=u'Техникийн мото цаг', readonly=True,
		help="Дугуйг техникт суурьлуулах үеийн мото цаг")

	state = fields.Selection([
		('draft','Draft'),
		('new','New'),
		('using','Using'),
		('inactive','Inactive'),
		('repairing','Repairing'),
		('retired','Retired')], string='Төлөв',
		readonly=True, default='draft', tracking=True)

	working_type = fields.Selection([
		('normal',u'Хэвийн'),
		('use_again',u'Дахин ашиглах'),
		('available_repair',u'Засагдах боломжтой'),
		('rear_used','Арын тэнхлэгт шилжүүлсэн'),
		('burny','Халсан'),
		('exploded','Буудсан'),
		('shapeless','Хэлбэр алдсан'),
		('dont_use',u'Ашиглах боломжгүй')], string=u'Ажиллагаа',
		tracking=True, default='normal',
		states={'new':[('readonly',True)],'using':[('readonly', True)],'inactive':[('readonly', True)],
				'repairing':[('readonly',True)],'retired':[('readonly', True)]})
	with_coolant = fields.Boolean('Coolant-тай эсэх?', default=False)

	tire_depreciation_lines = fields.One2many('tire.depreciation.line', 'tire_id',
		string='Элэгдлийн түүх', )
	tire_inspection_lines = fields.One2many('tire.inspection.line', 'tire_id',
		string='Үзлэгийн түүх',
		# readonly=True,
	)
	tire_used_history = fields.One2many('tire.used.history', 'tire_id',
		string='Хэрэглэсэн түүх', )

	user_id = fields.Many2one('res.users', string=u'Бүртгэсэн', readonly=True,
		default=_get_user)

	retired_description = fields.Text(string=u'Актласан тайлбар', readonly=True,)
	retire_type = fields.Selection([
		('after_deadline',u'Хугацаандаа'),
		('before_dealine',u'Хугацаанаас өмнө')], string=u'Актлах төрөл', readonly=True,)
	retire_attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', readonly=True,)

	retire_tire_type = fields.Selection([
		('shapeless','Дугуйн хэлбэр алдалт'),
		('burny','Халалт'),
		('odometer_overload','Мото цацгийн хэтрэлт'),
		('depend_roads','Зам талбайгаас хамаарсан'),
		('depend_pressure','Хийн даралтаас хамаарсан'),
		('cut','Дугуйн зүсэлт'),
		('exploded','Буудсан'),
		('tread_warning','Элэгдэл ихтэй'),
		('depend_operator',u'Операторын үйл ажиллагаанаас хамаарсан'),
		('tread_damage',u'Хээ хөндийрсөн')], string=u'Ашиглалтаас гарсан үзүүлэлт', readonly=True, )

	excel_data = fields.Binary('Excel file')
	file_name = fields.Char('File name')

	# Constraints
	_sql_constraints = [
		('tire_uniq', 'unique(serial_number)', "Сериал дугаар давхардсан байна!"),
	]

	@api.constrains('tread_current_deep')
	def _check_validation(self):
		for obj in self:
			if obj.tread_current_deep < 0:
				raise ValidationError(_('Хээний гүн хасах утгатай байж болохгүй!'))
			if obj.tire_setting_id.norm_tread_deep < obj.tread_current_deep:
				raise ValidationError(_('Дугуйны одоогийн хээний гүн нормоос их байна!'))

	# =================== Overrided methods ================
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_('Ноороглох ёстой!'))
		return super(TechnicTire, self).unlink()

	# =================== CUSTOM METHODs ===========
	@api.onchange('tire_setting_id')
	def onchange_tire_setting_id(self):
		self.purchase_value = self.tire_setting_id.purchase_value
		self.tread_current_deep = self.tire_setting_id.norm_tread_deep

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_use(self):
		self.user_id = self.env.user.id
		self.state = 'new'

	def action_to_inactive(self):
		self.state = 'inactive'

	# Дугуй актлах
	def action_to_retire(self):
		context = dict(self._context)
		context.update({'tire_id': self.id})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'tire.retirement',
			'view_mode': 'form',
			'context': context,
			'target': 'new',
		}

	# Гараар нэмэгдүүлэх
	def manual_increase_odometer(self):
		context = dict(self._context)
		context.update({'tire_id': self.id})
		return {
			'type': 'ir.actions.act_window',
			'res_model': 'tire.odometer.increase',
			'view_mode': 'form',
			'context': context,
			'target': 'new',
		}

	# Дугуйн МЦ, КМ нэмэгдүүлэх func
	def _increase_odometer(self, i_date, motoh, km, shift):
		if motoh > 0 or km > 0:
			if self.state not in ['retired','draft']:
				current_odometer = self.total_moto_hour if self.odometer_unit == 'motoh' else self.total_km
				norm_odometer = self.tire_setting_id.norm_moto_hour if self.odometer_unit == 'motoh' else self.tire_setting_id.norm_km
				odometer_value = motoh if self.odometer_unit == 'motoh' else km
				dep_percent = 0
				dep_amount = 0
				if norm_odometer > 0:
					dep_percent = (odometer_value * 100.0)/norm_odometer
					dep_amount = (dep_percent * self.purchase_value)/100
				else:
					raise UserError(_('Гүйлтийн норм тохиргоо олдсонгүй!\n%s'%self.tire_setting_id.name))

				line_ids = self.env['tire.depreciation.line'].search([('tire_id','=',self.id),('date','=',i_date),('shift','=',shift)])
				if line_ids:
					for line in line_ids:
						line.write( {'increasing_odometer': motoh,
									 'increasing_km': km,
									 'depreciation_percent': dep_percent,
									 'depreciation_amount': dep_amount })
				else:
					vals = {
						'date': i_date,
						'technic_id': self.current_technic_id.id,
						'tire_id': self.id,
						'tire_odometer': current_odometer,
						'increasing_odometer': motoh,
						'increasing_km': km,
						'depreciation_percent': dep_percent,
						'depreciation_amount': dep_amount,
						'user_id': self.env.user.id,
						'shift': shift,
					}
					self.env['tire.depreciation.line'].create(vals)

	# Элэгдлийн дата авах
	def get_inspection_datas(self, tire_id, context=None):
		series = []
		obj = self.env['technic.tire'].browse(tire_id)
		# Хээний элэгдэл. Үзлэгээс
		datas = []
		for line in obj.tire_inspection_lines:
			if line.state == 'done' or not line.state:
				temp = [ self._unix_time_millis(line.date), line.depreciation ]
				datas.append(temp)
		series.append({
				'type': 'area',
				'name': 'Хээ',
				'data': datas,
			})
		# Мото/ц, КМ ээс элэгдэл
		datas = []
		for line in obj.tire_depreciation_lines:
			temp = [ self._unix_time_millis(line.date), line.depreciation_percent ]
			datas.append(temp)
		series.append({
				'type': 'spline',
				'yAxis': 1,
				'name': 'Км, мото/ц',
				'data': datas,
				'color': '#F781F3',
			})
		return series

	# Хөрвүүлэх
	def _unix_time_millis(self, dt):
		epoch = datetime.utcfromtimestamp(0).date()
		date_start = dt
		date_start += timedelta(hours=8)
		return (date_start - epoch).total_seconds() * 1000.0

	# Түүх нөхөж импорт хийх
	def import_history(self):
		if not self.excel_data:
			raise UserError(_(u'Choose import excel file!'))

		# File нээх
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			 raise osv.except_osv(u'Error',u'Importing error.\nCheck excel file!')

		book = xlrd.open_workbook(fileobj.name)
		# Sheet1 ийг унших - Гүйлтийн түүх
		try :
			 sheet1 = book.sheet_by_index(0)
		except:
			 raise osv.except_osv(u'Warning', u'Wrong Sheet number.')
		# Унших
		nrows = sheet1.nrows
		for r in range(1,nrows):
			row = sheet1.row(r)
			i_date = row[0].value
			motoh = row[1].value
			km = row[2].value
			dep_percent = row[3].value
			dep_amount = row[4].value
			# Insert
			vals = {
				'date': i_date,
				'tire_id': self.id,
				'increasing_odometer': motoh,
				'increasing_km': km,
				'depreciation_percent': dep_percent,
				'depreciation_amount': dep_amount,
				'user_id': self.env.user.id,
			}
			self.env['tire.depreciation.line'].create(vals)

		# Sheet2 ийг унших - Хээний түүх
		try :
			 sheet2 = book.sheet_by_index(1)
		except:
			 raise osv.except_osv(u'Warning', u'Wrong Sheet number.')
		# Унших
		nrows = sheet2.nrows
		for r in range(1,nrows):
			row = sheet2.row(r)
			i_date = row[0].value
			tread_deep1 = row[1].value
			tread_deep2 = row[2].value
			deep_average = row[3].value
			depreciation = row[4].value
			# Insert
			vals = {
				'date': i_date,
				'tire_id': self.id,
				'position': 0,
				'tread_deep1': tread_deep1,
				'tread_deep2': tread_deep2,
				'deep_average': deep_average,
				'depreciation': depreciation,
			}
			self.env['tire.inspection.line'].create(vals)
		return True

	# Зарлага хийх үед шинэ дугуйн бүртгэл үүсгэх
	def _create_tire_from_stock(self, product, serial):
		setting = self.env['technic.tire.setting'].sudo().search(
			[('product_id','=',product.id)], limit=1)
		if setting:
			vals = {
				'branch_id': self.env.user.branch_id.id,
				'date_of_record': datetime.now(),
				'date_of_manufactured': datetime.now(),
				'serial_number': serial,
				'tire_setting_id': setting.id,
				'state': 'new',
			}
			tire = self.env['technic.tire'].sudo().create(vals)
			tire.onchange_tire_setting_id()
		else:
			raise UserError(_('%s бараатай дугуйн тохиргоо олдсонгүй!' % product.display_name))

	# Failure report татах
	def get_failure_report(self):
		# Generate EXCEL
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'failure_report.xlsx'

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_text_wrap()
		header.set_bg_color('#C2CACA')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_left2 = workbook.add_format()
		contest_left2.set_text_wrap()
		contest_left2.set_font_size(9)
		contest_left2.set_align('left')
		contest_left2.set_align('vcenter')
		contest_left2.set_border(style=1)
		contest_left2.set_bg_color('#C2CACA')

		contest_right = workbook.add_format()
		contest_right.set_text_wrap()
		contest_right.set_font_size(9)
		contest_right.set_align('right')
		contest_right.set_align('vcenter')
		contest_right.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		contest_center2 = workbook.add_format()
		contest_center2.set_font_size(9)
		contest_center2.set_align('center')
		contest_center2.set_align('vcenter')

		worksheet = workbook.add_worksheet(u'Failure report')
		worksheet.write(0,2, u"FAILURE REPORT", h1)
		txt = ("%s %d position tire" % (self.current_technic_id.park_number, self.current_position)) if self.current_technic_id else ''
		worksheet.merge_range(1,1,1,4, "COMPONENT INVOLVED: %s" % txt, contest_center2)
		# TABLE HEADER
		worksheet.set_column("A:G", 10)
		worksheet.set_row(1, 25)
		worksheet.merge_range(2,0,2,1, "Prepared By", contest_left2)
		worksheet.merge_range(2,2,2,7, self.env.user.display_name, contest_left)
		worksheet.merge_range(3,0,3,1, "Date", contest_left2)
		worksheet.merge_range(3,2,3,7, datetime.now().strftime("%Y-%m-%d"), contest_left)
		worksheet.merge_range(4,0,4,1, "Distribution List", contest_left2)
		worksheet.merge_range(4,2,4,7, "", contest_left)
		
		worksheet.merge_range(5,0,5,1, "Customer", contest_left2)
		worksheet.merge_range(5,2,5,7, "MME", contest_left)
		worksheet.merge_range(6,0,6,1, "Location (country)", contest_left2)
		worksheet.merge_range(6,2,6,7, self.branch_id.name, contest_left)
		worksheet.merge_range(7,0,7,1, "Mine", contest_left2)
		worksheet.merge_range(7,2,7,7, self.branch_id.name, contest_left)
		worksheet.merge_range(8,0,8,1, "Contact", contest_left2)
		worksheet.merge_range(8,2,8,7, "", contest_left)
		worksheet.merge_range(9,0,9,1, "Job / work order №", contest_left2)
		worksheet.merge_range(9,2,9,3, "", contest_left)
		worksheet.write(9,4, "Failure date", contest_left2)
		worksheet.merge_range(9,5,9,7, "", contest_left)

		worksheet.set_row(10, 25)
		worksheet.merge_range(10,1,10,4, "HISTORY OF USE", contest_center2)
		worksheet.set_row(11, 25)
		worksheet.write(11, 0, "Machine Model", header)
		worksheet.write(11, 1, "Date of assembly", header)
		worksheet.write(11, 2, "Machine Hours", header)
		worksheet.write(11, 3, "Wheel position", header)
		worksheet.write(11, 4, "Description", header)
		worksheet.write(11, 5, "Техникт ашигласан м/ц", header)
		# worksheet.write(11, 6, "WO-н түүх", header)
		# DATA зурах
		row = 12
		for line in self.tire_used_history:
			worksheet.write(row, 0, line.technic_id.park_number, contest_left)
			worksheet.write(row, 1, line.date.strftime("%Y-%m-%d"), contest_center)
			worksheet.write(row, 2, line.technic_odometer, contest_right)
			worksheet.write(row, 3, line.position, contest_center)
			worksheet.write(row, 4, line.description, contest_left)
			worksheet.write(row, 5, "", contest_center)
			row += 1

		worksheet.set_row(row, 25)
		worksheet.merge_range(row,1,row,4, "DAMAGED OF INFORMATION", contest_center2)
		row += 1
		worksheet.set_row(row, 25)
		worksheet.write(row, 0, "Component name", header)
		worksheet.write(row, 1, "Serial number", header)
		worksheet.write(row, 2, "Size", header)
		worksheet.write(row, 3, "Tire hours", header)
		worksheet.write(row, 4, "Хадгалагдсан цаг", header)
		worksheet.write(row, 5, "Ашиглалтын хувь", header)
		worksheet.write(row, 6, "Дугуйн TKPH", header)
		row += 1
		worksheet.write(row, 0, self.brand_id.name, contest_center)
		worksheet.write(row, 1, self.serial_number, contest_center)
		worksheet.write(row, 2, self.norm_tire_size, contest_center)
		worksheet.write(row, 3, self.total_moto_hour, contest_center)
		worksheet.write(row, 4, self.stored_time, contest_center)
		worksheet.write(row, 5, self.usage_percent, contest_center)
		worksheet.write(row, 6, self.tkph, contest_center)
		row += 2

		worksheet.set_row(row, 25)
		worksheet.merge_range(row,0,row,7, "Service life / ашиглалтын хугацааны төлөв", header)
		row += 1
		worksheet.merge_range(row, 0, row, 1, u'Үзлэгийн мэдээлэл', contest_left2)
		worksheet.merge_range(row+1, 0, row+1, 1, u'Хийн даралт', contest_left2)
		worksheet.merge_range(row+2, 0, row+2, 1, u'Температур', contest_left2)
		worksheet.merge_range(row+3, 0, row+3, 1, u'Гэмтэлийн мэдээлэл', contest_left2)
		col = 2
		for item in self.env['tire.inspection.line'].search([('serial_number','=', self.serial_number)], limit = 5):
			worksheet.write(row, col, item.parent_id.date_inspection.strftime('%Y-%m-%d'), contest_center)
			worksheet.write(row+1, col, item.pressure, contest_center)
			worksheet.write(row+2, col, item.temperature, contest_center)
			worksheet.write(row+3, col, dict(item._fields['tire_status'].selection).get(item.tire_status), contest_center)
			col += 1

		inspection = self.env['tire.inspection.line'].search([
			('parent_id.state','=','done'),
			('parent_id.inspection_type','=','operation_inspection'),
			('tire_id','=',self.id)
			], order='date desc', limit=1)
		txt = ""
		if inspection:
			txt = "Темпартур: %d, Даралт: %d, Статус: %s, Тайлбар: %s" % (inspection.temperature, inspection.pressure,inspection.description, (inspection.tire_status or ''))
		row += 1
		worksheet.merge_range(row+4,0,row+4,7, "Damage caused / Үүссэн гэмтэл", header)
		worksheet.merge_range(row+5,0,row+6,7, "", contest_left)
		row += 2
		worksheet.merge_range(row+6,0,row+6,7, "Analysis / Дүгнэлт", header)
		worksheet.merge_range(row+7,0,row+8,7, "", contest_left)

		# =============================
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
			 'target': 'new',
		}

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol

class TireDepreciationLine(models.Model):
	_name = 'tire.depreciation.line'
	_description = 'Tire depreciation history'
	_order = 'date desc'

	date = fields.Date(string='Огноо', required=True)
	technic_id = fields.Many2one('technic.equipment', string='Техник')

	tire_id = fields.Many2one('technic.tire', string='Дугуй', ondelete='cascade')
	tire_odometer =  fields.Float(string='Гүйлт',digits = (16,1))
	increasing_odometer =  fields.Float(string=u'Нэмэгдүүлсэн мото/ц',digits = (16,1))
	increasing_km =  fields.Float(string=u'Нэмэгдүүлсэн КМ',digits = (16,1))
	depreciation_percent =  fields.Float(string='Элэгдлийн хувь',digits = (16,2), required=True)
	depreciation_amount =  fields.Float(string='Элэгдлийн дүн',digits = (16,1), required=True)
	user_id = fields.Many2one('res.users', string='Бүртгэсэн',)
	shift = fields.Selection([
			('day', u'Өдөр'),
			('night', u'Шөнө'),],
			string=u'Ээлж',)

class TireUsedHistory(models.Model):
	_name = 'tire.used.history'
	_description = 'Tire used history'
	_order = 'date desc, id desc'

	date = fields.Date(string='Огноо', required=True,)
	technic_id = fields.Many2one('technic.equipment', string='Техник')
	technic_odometer =  fields.Float(string='Technic odometer',digits = (16,1))

	tire_id = fields.Many2one('technic.tire', string='Дугуй', ondelete='cascade')
	tire_odometer =  fields.Float(string='Дугуйн мото/ц',digits = (16,1))
	tire_km =  fields.Float(string=u'Дугуйн КМ',digits = (16,1))
	tread_percent =  fields.Float(string=u'Хээний элэгдлийн %',digits = (16,1))
	position =  fields.Integer(string=u'Байрлал',)
	description = fields.Char(string='Тайлбар',)
	other_notes = fields.Char(string='Бусад',)

class TireOdometerIncrease(models.TransientModel):
	_name = 'tire.odometer.increase'
	_description = 'Tire odometer increase'

	# Columns
	date = fields.Date('Огноо', required=True)
	tire_odometer =  fields.Float(string='Дугуйн мото/ц',digits = (16,1))
	tire_km =  fields.Float(string=u'Дугуйн КМ',digits = (16,1))

	def save_and_increase(self):
		if self._context.get('tire_id'):
			tire = self.env['technic.tire'].browse(self._context.get('tire_id'))
			tire._increase_odometer(self.date, self.tire_odometer, self.tire_km, 'day')
		return True

class TireRetirement(models.TransientModel):
	_name = 'tire.retirement'
	_description = 'Tire retirement'

	# Columns
	date = fields.Date(string='Огноо', required=True, default=datetime.now())
	description =  fields.Text(string='Актласан тайлбар', required=True,)
	retire_type = fields.Selection([
		('after_deadline',u'Хугацаандаа'),
		('before_dealine',u'Хугацаанаас өмнө')], string=u'Актлах төрөл', required=True,)
	attachment_ids = fields.Many2many('ir.attachment', string=u'Хавсралтууд', required=True, )
	is_required_attach = fields.Boolean(string=u'Файл хавсаргах шаардлагатай эсэх', default=True)

	retire_tire_type = fields.Selection([
		('shapeless','Дугуйн хэлбэр алдалт'),
		('burny','Халалт'),
		('odometer_overload','Мото цацгийн хэтрэлт'),
		('depend_roads','Зам талбайгаас хамаарсан'),
		('depend_pressure','Хийн даралтаас хамаарсан'),
		('cut','Дугуйн зүсэлт'),
		('exploded','Буудсан'),
		('tread_warning','Элэгдэл ихтэй'),
		('depend_operator',u'Операторын үйл ажиллагаанаас хамаарсан'),
		('tread_damage',u'Хээ хөндийрсөн')], string=u'Ашиглалтаас гарсан үзүүлэлт', required=True,)

	def save_and_retire(self):
		if self._context.get('tire_id'):
			if not self.attachment_ids and self.is_required_attach == True:
				raise UserError(_('Актлахтай холбоотой баримтыг хавсаргана уу!'))

			tire = self.env['technic.tire'].browse(self._context.get('tire_id'))
			tire.retire_type = self.retire_type
			tire.retired_description = self.description
			body = "Дугуй актлав.\nМото/ц:<b>%d</b>, Kм:<b>%d</b>" % (tire.total_moto_hour, tire.total_km)
			tire.message_post(body=body)
			tire.date_of_retired = self.date
			tire.state = 'retired'
			tire.retire_attachment_ids = self.attachment_ids
			tire.retire_tire_type = self.retire_tire_type

			# Түүх бичих
			vals = {
				'date': self.date,
				'technic_id': False,
				'tire_id': tire.id,
				'tire_odometer': tire.total_moto_hour,
				'tire_km': tire.total_km,
				'tread_percent': tire.tread_depreciation_percent,
				'position': 0,
				'description': u'Дугуйг актлав'
			}
			self.env['tire.used.history'].create(vals)
		return True


