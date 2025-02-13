# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta, date
import collections
import time

import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO

from calendar import monthrange

import logging
_logger = logging.getLogger(__name__)

class TirePlanGenerator(models.Model):
	_name = 'tire.plan.generator'
	_description = 'Tire Plan Generator'
	_inherit = ["analytic.mixin","mail.thread", "mail.activity.mixin"]
	_order = 'date_start desc, name'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	date = fields.Datetime(u'Үүсгэсэн огноо', readonly=True, default=datetime.now(), copy=False)
	name = fields.Char(u'Нэр', copy=False, 
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
	date_start = fields.Date(u'Эхлэх огноо', copy=True, required=True,
		states={'done': [('readonly', True)]})
	date_end = fields.Date(u'Дуусах огноо', copy=True, required=True,
		states={'done': [('readonly', True)]})

	planner_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, default=_get_user)
	state = fields.Selection([
			('draft', 'Draft'), 
			('confirmed', 'Confirmed'),
			('done', 'Done')
		], default='draft', required=True, string=u'Төлөв', tracking=True)

	qty_type = fields.Selection([
			('odometer', u'Гүйлт'), 
			('purchase', u'Худалдан авах дүн'),
			('depreciation', u'Үлдэгдэл дүн')
		], default='odometer', required=True, string=u'Төрөл')

	long_term_line = fields.One2many('tire.plan.generator.line', 'parent_id', 'Lines', copy=False,
		states={'done': [('readonly', True)]})

	technic_setting_line = fields.One2many('technic.tire.setting.line', 'parent_id', 'Lines', copy=True,
		states={'done': [('readonly', True)]})
	only_technic_tires = fields.Boolean(u'Зөвхөн техник дээрх дугуйг татах', default=True,
		states={'done': [('readonly', True)]})

	# Экселээс forecast import хийх
	tire_forecast_line = fields.One2many('tire.forecast.line', 'parent_id', 'Lines', copy=False,
		states={'done': [('readonly', True)]})
	# 1 Дугуйн ажилд зарцуулах цаг
	tire_worktime_per = fields.Float(u'1 дугуйн ажилд зарцуулах цаг', default=3, required=True,
		states={'done': [('readonly', True)]})

	@api.depends('long_term_line')
	def _methods_totals(self):
		for obj in self:
			obj.total_amount = sum(obj.mapped('long_term_line.amount'))
	total_amount = fields.Float(compute=_methods_totals, store=True, string=u'Нийт дүн', default=0)

	excel_data = fields.Binary('Excel file')
	file_name = fields.Char('File name')

	# ============ Override ===============
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Устгахын тулд эхлээд ноороглох ёстой!'))
		return super(TirePlanGenerator, self).unlink()

	# ============ Custom methods =========
	# Одоогийн ДАТА наас импорт хийх
	def import_from_current(self):
		self.technic_setting_line.unlink()
		technics = self.env['technic.equipment'].search([
			('owner_type','=','own_asset'),
			('technic_setting_id.rubber_tired','=',True),])
		_logger.info("--------import from ==%d====",len(technics))
		setting_lines = []
		for tt in technics:
			tire_counts = tt.technic_setting_id.tire_counts
			t_lines = []
			# Байгаа дугуйн мэдээлэл бэлдэх
			if tt.tire_line:
				for line in tt.tire_line:
					temp = (0,0,{
						'tire_setting_id': line.tire_id.tire_setting_id.id,
						'tire_id': line.tire_id.id,
						'position': line.position,
						'set_date': line.date,
						'set_odometer': line.odometer_value,
					})
					t_lines.append(temp)

			# Бүх дугуйт техникийн дугуйг хоосон байсан ч татах
			if not self.only_technic_tires:
				# Дутуу дугуйг бэлдэх
				if len(t_lines) < tire_counts:
					for i in range(0,tire_counts-len(t_lines)):
						temp = (0,0,{
							'tire_setting_id': False,
							'tire_id': False,
							'position': 0,
						})
						t_lines.append(temp)
			if t_lines:
				temp2 = (0,0,{
					'technic_id': tt.id,
					'start_odometer': tt.total_odometer,
					'line_ids': t_lines,
				})
				setting_lines.append(temp2)

		if setting_lines:
			self.technic_setting_line = setting_lines
		return True

	# Excel-ээс forecast import хийх
	def import_tire_excel(self):
		# Өмнөх дата г цэвэрлэх
		self.tire_forecast_line.unlink()
		if not self.excel_data:
			raise UserError(_(u'Excel файлыг сонгоно уу!'))

		# File нээх
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			 raise osv.except_osv(u'Error',u'Importing error.\nCheck excel file!')
		
		book = xlrd.open_workbook(fileobj.name)
		try :
			 sheet = book.sheet_by_index(0)
		except:
			 raise osv.except_osv(u'Warning', u'Wrong Sheet number.')
		
		# Унших
		nrows = sheet.nrows
		ncols = sheet.ncols
		setting_lines = []
		# Month range
		row_dates = sheet.row(3)
		book_datemode = book.datemode
		for r in range(4,nrows):
			row = sheet.row(r)
			_logger.info("--------import ======%s %s ", row[0].value, row[2].value)
			if row[0].value and row[2].value:
				program_code = row[0].value
				product_code = row[2].value
				if row[2].ctype in [2, 3]:
					product_code = str(int(row[2].value))
				technic = self.env['technic.equipment'].search([('program_code','=',program_code)], limit=1)
				product = self.env['product.product'].search([('default_code','=',product_code)], limit=1)
				if technic and product:
					for c in range(3, ncols):
						if row[c].value:
							dddd = row_dates[c].value
							qty = row[c].value
							worktime = qty * self.tire_worktime_per
							temp = (0,0,{
								'date_plan': dddd, 
								'date_str': dddd[:7],
								'technic_id': technic.id,
								'product_id': product.id,
								'work_time': worktime,
								'qty': qty,
								'amount': product.standard_price * qty,
							})
							setting_lines.append(temp)
				else:
					_logger.info("--------import NOT found ======%s %s ", row[0].value, row[2].value)
		if setting_lines:
			self.tire_forecast_line = setting_lines
		return True

	def action_to_draft(self):
		self.state = 'draft'

	def action_to_confirm(self):
		self.planner_id = self.env.user.id
		if not self.technic_setting_line:
			raise UserError(_(u'Техникүүдийн мэдээллийг оруулна уу!'))
		for line in self.technic_setting_line:
			ll = line.line_ids.filtered(lambda l: l.tire_setting_id == False or l.position <= 0)
			if ll:
				raise UserError(_(u'%s техникийн дугуйн тохиргоог бүрэн оруулна уу!' % line.technic_id.name))
		self.state = 'confirmed'
	
	def action_to_done(self):
		self.planner_id = self.env.user.id
		if not self.long_term_line:
			raise UserError(_(u'LONG TERM төлөвлөгөө үүсээгүй байна!\n"Generate" товч дээр дарна уу!'))
		# for line in self.long_term_line:
		# 	line.create_plan()
		self.state = 'done'
	
	def generate_lines(self):
		# Өмнөх мөрийг устгах
		self.long_term_line.unlink()

		group_by = 1
		for setting_line in self.technic_setting_line:
			technic = setting_line.technic_id
			technic_odometer = setting_line.start_odometer
			for line in setting_line.line_ids:
				norm_moto_hour = line.tire_setting_id.norm_moto_hour
				tire_odometer = line.tire_id.total_moto_hour or 0
				set_odometer = line.set_odometer or 0
				set_date = line.set_date or False

				temp_date = self.date_start
				if set_date:
					temp_date = set_date

				# Дуусах огноо хүртэл давтана
				while temp_date <= self.date_end:
					vals = {}
					if tire_odometer >= norm_moto_hour:
						vals['is_change'] = True
						vals['amount'] = line.tire_setting_id.purchase_value
						tire_odometer = 0

					# Forecast үүсгэх
					vals['parent_id'] = self.id
					vals['technic_id'] = technic.id
					vals['technic_odometer'] = technic_odometer
					
					vals['tire_setting_id'] = line.tire_setting_id.id
					vals['position'] = line.position
					vals['tire_odometer'] = tire_odometer
					
					vals['monthly_odometer_norm'] = line.tire_setting_id.monthly_odometer_norm
					vals['norm_moto_hour'] = norm_moto_hour

					vals['set_odometer'] = set_odometer
					vals['set_date'] = temp_date
					vals['date_str'] = temp_date.strftime("%Y-%m-%d")[:7]
					
					vals['group_by'] = group_by
					# Хувь бодох
					percent = (100*tire_odometer)/norm_moto_hour
					vals['percent'] = percent
					# Үлдэгдэл дүн бодох
					dep_amount = (line.tire_setting_id.purchase_value*(100-percent)) / 100
					vals['depreciation_amount'] = dep_amount

					# Create
					ll = self.env['tire.plan.generator.line'].create(vals)

					# ------------
					temp_date = self._date_increase(temp_date, 30)
					tire_odometer += line.tire_setting_id.monthly_odometer_norm
					technic_odometer += line.tire_setting_id.monthly_odometer_norm

				group_by += 1

	# Огноог заасан өдрөөр нэмэгдүүлэх
	def _date_increase(self, temp_date, add):
		return temp_date + timedelta(days=add)

	# Pivot оор харах
	def see_expenses_view(self):
		if self.long_term_line:
			context = dict(self._context)
			# GET views ID		
			mod_obj = self.env['ir.model.data']		
			search_res = mod_obj._xmlid_lookup('mw_technic_equipment.tire_plan_generator_line_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup('mw_technic_equipment.tire_plan_generator_line_pivot')
			pivot_id = pivot_res and pivot_res[2] or False

			return {
				'name': self.name,
				'view_mode': 'pivot',
				'res_model': 'tire.plan.generator.line',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': [('parent_id','=',self.id)],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}
	
	def export_report(self):
		if self.long_term_line:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Forecast report.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_font_size(9)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#E9A227')

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			contest_right = workbook.add_format({'italic':1})
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)

			contest_right_do = workbook.add_format({'italic':1})
			contest_right_do.set_text_wrap()
			contest_right_do.set_font_size(9)
			contest_right_do.set_align('right')
			contest_right_do.set_align('vcenter')
			contest_right_do.set_border(style=1)
			contest_right_do.set_bg_color('#FF9F9B')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			worksheet = workbook.add_worksheet(u'Tire - Moto hours')
			worksheet.set_zoom(80)
			worksheet.write(0,2, u"TIRE - Forecast", h1)

			row = 2
			worksheet.merge_range(row, 1, row, 3, u"Техникийн мэдээлэл", header_wrap)
			worksheet.merge_range(row, 4, row, 7, u"Дугуйн ерөнхий мэдээлэл", header_wrap)
			worksheet.merge_range(row, 8, row, 11, u"Дугуйн төлөв", header_wrap)
			# TABLE HEADER
			row = 3
			worksheet.merge_range(row, 0, row+1, 0, u"№", header_wrap)
			worksheet.set_column(0, 0, 5)
			worksheet.merge_range(row, 1, row+1, 1,u"Модель", header_wrap)
			worksheet.set_column(1, 1, 25)
			worksheet.merge_range(row, 2, row+1, 2,u"Парк №", header_wrap)
			worksheet.merge_range(row, 3, row+1, 3,u"Байрлал", header_wrap)
			worksheet.merge_range(row, 4, row+1, 4,u"Дугуйн брэнд", header_wrap)
			worksheet.set_column(4, 4, 25)
			worksheet.merge_range(row, 5, row+1, 5,u"Дугуйн сериал", header_wrap)
			worksheet.set_column(5, 5, 15)
			worksheet.merge_range(row, 6, row+1, 6,u"Дугуйн хэмжээ", header_wrap)
			worksheet.merge_range(row, 7, row+1, 7,u"TKPH", header_wrap)
			# worksheet.merge_range(row, 8, row+1, 8,u"Дугуйн шилжүүлж ашиглах мото цагийн норм", header_wrap)
			# worksheet.merge_range(row, 9, row+1, 9,u"Дугуйн шилжүүлж ашиглах км норм", header_wrap)
			# worksheet.merge_range(row, 10,row+1, 10, u"Дугуйн ашиглалтын мото цагийн норм", header_wrap)
			# worksheet.merge_range(row, 11,row+1, 11, u"Дугуйн ашиглалтын гүйлтийн км норм", header_wrap)
			worksheet.merge_range(row, 8,row+1, 8, u"Хадгалагдсан цаг", header_wrap)
			worksheet.merge_range(row, 9,row+1, 9, u"Ашиглалтын хувь", header_wrap)
			worksheet.merge_range(row, 10,row+1, 10, u"Одоогийн мото цаг", header_wrap)
			worksheet.merge_range(row, 11,row+1, 11, u"Одоогийн км гүйлт", header_wrap)
			# worksheet.merge_range(row, 16,row+1, 16, u"Шилжүүлж угсарсан үеийн мото цаг", header_wrap)
			# worksheet.merge_range(row, 17,row+1, 17, u"Шилжүүлж угсарсан үеийн км гүйлт", header_wrap)
			# worksheet.merge_range(row, 18,row+1, 18, u"Шилжүүлэн ашигласан техник", header_wrap)
			# --------------
			lines = self.env['tire.plan.generator.line'].search([('parent_id','=',self.id)], order='date_str, set_date, technic_id, position, tire_odometer')
			row_dict = {}
			col_dict = {}
			total_dict = {}
			row = 5
			col = 12
			number = 1
			for line in lines:
				aa = self.env['technic.tire.line'].search([('technic_id.id','=',line.technic_id.id), ('position', '=', line.position)])
				if line.group_by not in row_dict:
					for item in aa:
						worksheet.write(row, 0, number, contest_right)
						worksheet.write(row, 1, line.technic_id.model_id.name, contest_left)
						worksheet.write(row, 2, line.technic_id.park_number, contest_left)
						worksheet.write(row, 3, line.position, contest_right)
						worksheet.write(row, 4, line.tire_setting_id.model_id.name, contest_center)
						worksheet.write(row, 5, item.tire_id.serial_number, contest_center)
						worksheet.write(row, 6, item.tire_id.norm_tire_size, contest_right)
						worksheet.write(row, 7, item.tire_id.tkph, contest_center)
						# worksheet.write(row, 8, item.tire_id.stored_time, contest_center)
						worksheet.write(row, 8, 0, contest_center)
						# worksheet.write(row, 9, item.tire_id.usage_percent, contest_center)
						worksheet.write(row, 9, 0, contest_center)
						worksheet.write(row, 10, item.tire_id.total_moto_hour, contest_center)
						worksheet.write(row, 11, item.tire_id.total_km, contest_center)
					row_dict[line.group_by] = row
					row += 1
					number += 1
				if line.date_str not in col_dict:
					col_dict[line.date_str] = col
					worksheet.merge_range(3, col, 4, col, line.date_str, header_wrap)
					col += 1
				rr = row_dict[line.group_by]
				cc = col_dict[line.date_str]
				temp_style = contest_right
				if line.is_change:
					temp_style = contest_right_do
					if line.group_by in total_dict:
						total_dict[line.group_by] += 1
					else:
						total_dict[line.group_by] = 1
				qty = 0
				if self.qty_type == 'odometer':
					qty = line.tire_odometer
				elif self.qty_type == 'purchase':
					qty = line.amount
				else:
					qty = line.depreciation_amount
				worksheet.write(rr, cc, qty, temp_style)

			# Total draw
			row = 2
			worksheet.merge_range(row, 12, row, col-1, u"Дугуй ашиглалтын мэдээ", header_wrap)
			# worksheet.merge_range(row, col, row, col+5, u"Статус мэдээ", header_wrap)
			# row = 3
			# # worksheet.merge_range(row, col, row, col+3, u"Шилжүүлж угсрах шаардлагатай дугуйн тоо", header_wrap)
			# # worksheet.merge_range(row, col+4, row+1, col+4, u"Захиалах шаардлагатай дугуйн тоо", header_wrap)
			# # worksheet.merge_range(row, col+5, row+1, col+5, u"Дутуу дугуйн тоо", header_wrap)
			# row = 4
			# worksheet.write(row, col, u"2600 м/ц", header_wrap)
			# worksheet.write(row, col+1, u"50000 км", header_wrap)
			# worksheet.write(row, col+2, u"6000 м/ц", header_wrap)
			# worksheet.write(row, col+3, u"110000 км", header_wrap)
			worksheet.merge_range(row, col, row+2, col, u"Нийт шинэ", header_wrap)
			for key in total_dict:
				rr = row_dict[key]
				worksheet.write(rr, col, total_dict[key], header_wrap)

			# =============================
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!')) 

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol

class TirePlanGeneratorLine(models.Model):
	_name = 'tire.plan.generator.line'
	_description = 'Maintenance Long Term Line'
	_order = 'date_str, set_date, technic_id, position, tire_setting_id'

	# Columns
	parent_id = fields.Many2one('tire.plan.generator', string=u'Parent long term', ondelete='cascade')

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', readonly=True, required=True,)
	technic_odometer = fields.Float(string=u'SMU', required=True,)

	tire_setting_id = fields.Many2one('technic.tire.setting', string=u'Дугуйн төрөл', required=True,)
	norm_tire_size = fields.Char(related='tire_setting_id.norm_tire_size', string=u'Size', readonly=True, store=True)
	position = fields.Char(string=u'Position', required=True,)
	
	tire_odometer = fields.Float(string=u'Дугуйн гүйлт', required=True,)

	monthly_odometer_norm = fields.Integer(string=u'Сард ажиллах норм', required=True,)
	norm_moto_hour = fields.Float('Давтамж, норм', required=True,)

	set_odometer = fields.Float(string=u'Set odometer', required=True,)
	set_date = fields.Date(u'Огноо', copy=False, required=True,)
	date_str = fields.Char(u'Сар', copy=False, required=True,)

	is_change = fields.Boolean(string=u'Солих эсэх', default=False)

	description = fields.Char('Тайлбар', )
	group_by = fields.Char('Sort', )

	amount = fields.Float(string=u'Худалдах авах дүн', default=0)
	depreciation_amount = fields.Float(string=u'Үлдэгдэл дүн', default=0)
	percent = fields.Float(string=u'Элэгдлийн %', default=0, group_operator="avg", digits=(16,1))

class TechinicTireSettingLine(models.Model):
	_name = 'technic.tire.setting.line'
	_description = 'Forecast tire setting line'
	_order = 'technic_id'

	# Columns
	parent_id = fields.Many2one('tire.plan.generator', string=u'Parent generator', ondelete='cascade')

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,)
	start_odometer = fields.Float(string=u'Эхлэх гүйлт', required=True,)
	line_ids = fields.One2many('technic.tire.setting.line.info', 'parent_id', 
		string='Lines', copy=False,)

class TechinicTireSettingLineInfo(models.Model):
	_name = 'technic.tire.setting.line.info'
	_description = 'Forecast tire setting line info'
	_order = 'position, tire_id'

	# Columns
	parent_id = fields.Many2one('technic.tire.setting.line', string=u'Parent info generator', ondelete='cascade')
	tire_id = fields.Many2one('technic.tire', string=u'Дугуй', readonly=True, )
	tire_setting_id = fields.Many2one('technic.tire.setting', string=u'Дугуйн төрөл', )
	position = fields.Integer(string=u'Байрлал', )
	set_odometer = fields.Float(string=u'Set odometer', )
	set_date = fields.Date(u'Огноо', copy=False, readonly=True,)

# Tire Forecast #2 ===========
class TireForecastLine(models.Model):
	_name = 'tire.forecast.line'
	_description = 'Tire forecast Line'
	_order = 'date_str, date_plan, technic_id, product_id'

	# Columns
	parent_id = fields.Many2one('tire.plan.generator', string=u'Parent long term', ondelete='cascade')

	technic_id = fields.Many2one('technic.equipment', string=u'Техник', required=True,)
	product_id = fields.Many2one('product.product', string=u'Дугуй /бараа/', required=True,)
	date_plan = fields.Date(u'Огноо', copy=False, required=True,)
	date_str = fields.Char(u'Сар', copy=False, required=True, readonly=True)

	qty = fields.Float(string=u'Тоо хэмжээ', default=0)
	amount = fields.Float(string=u'Дүн', default=0)
	work_time = fields.Float(string=u'Зарцуулар цаг', default=0)

	# ============ Custom =================
	@api.onchange('date_plan')
	def _onchange_date_plan(self):
		if self.date_plan:
			self.date_str = self.date_plan.month