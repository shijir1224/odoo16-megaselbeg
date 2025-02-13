# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta
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

class MaintenancePmMaterialGenerator(models.Model):
	_name = 'maintenance.pm.material.generator'
	_description = 'Maintenance pm material generator'
	_order = 'date desc, user_id'

	@api.model
	def _get_user(self):
		return self.env.user.id

	# Columns
	date = fields.Datetime(string=u'Үүсгэсэн огноо', readonly=True, default=datetime.now(), copy=False)
	name = fields.Char(string=u'Нэр', copy=False,
		states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

	user_id = fields.Many2one('res.users', string=u'Баталсан', readonly=True, default=_get_user)
	warehouse_id = fields.Many2one('stock.warehouse', string=u'Агуулах',
		states={'done': [('readonly', True)]})
	state = fields.Selection([
			('draft', 'Draft'),
			('confirmed', 'Confirmed'),
			('done', 'Done')
		], default='draft', required=True, string=u'Төлөв', tracking=True)

	pm_generated_line = fields.One2many('maintenance.pm.material.generator.line', 'parent_id', string='Lines', copy=False,
		states={'done': [('readonly', True)]})

	technic_setting_line = fields.One2many('pm.technic.setting.line', 'parent_id', string='Lines', copy=True,
		states={'confirmed': [('readonly', True)],'done': [('readonly', True)]})

	excel_data = fields.Binary('Excel file')
	file_name = fields.Char('File name')

	# ============ Override ===============
	def unlink(self):
		for s in self:
			if s.state != 'draft':
				raise UserError(_(u'Устгахын тулд эхлээд ноороглох ёстой!'))
		return super(MaintenancePmMaterialGenerator, self).unlink()

	# ============ Custom methods =========
	def action_to_draft(self):
		self.state = 'draft'

	# Одоогийн ДАТА наас импорт хийх
	def import_from_current(self):
		self.technic_setting_line.unlink()
		settings = self.env['technic.equipment.setting'].search([
			('is_tbb_report','=',True),
			('pm_material_config','!=',False)])
		_logger.info("--------import from ==%d====",len(settings))
		setting_lines = []
		for tt in settings:
			material_datas = []
			temp_pm = {}
			for m_line in tt.pm_material_config:
				if m_line.maintenance_type_id.id not in temp_pm:
					temp_pm[m_line.maintenance_type_id.id] = 1
					temp = (0,0,{
						'maintenance_type_id': m_line.maintenance_type_id.id,
						'qty': 0,
						'maintenance_pm_material_condif_id': m_line.id,
					})
					material_datas.append(temp)
			temp = (0,0,{
				'technic_setting_id': tt.id,
				'line_ids': material_datas,
			})
			setting_lines.append(temp)
		if setting_lines:
			self.technic_setting_line = setting_lines
		return True

	def action_to_confirm(self):
		self.user_id = self.env.user.id
		if not self.technic_setting_line:
			raise UserError(_(u'Техникүүдийн мэдээллийг оруулна уу!'))
		self.state = 'confirmed'

	def action_to_done(self):
		self.user_id = self.env.user.id
		if not self.pm_generated_line:
			raise UserError(_(u'Захиалгын мөр үүсээгүй байна!\n"Generate" товч дээр дарна уу!'))
		# PR үүсгэх
		# ...... .......
		self.state = 'done'
	
	def generate_lines(self):
		# Өмнөх мөрийг устгах
		# self.pm_generated_line.unlink()
		temp_datas = []
		quant_obj = self.env['stock.quant']

		self.pm_generated_line.unlink()

		for setting in self.technic_setting_line:
			for line in setting.line_ids:
				for pl in line.maintenance_pm_material_condif_id.pm_material_line:
					# Агуулахын үлдэгдэл авах
					a_qty = 0
					domain = [('product_id','=',pl.material_id.id),('location_id.usage','=','internal')]
					if self.warehouse_id:
						domain.append(('location_id.set_warehouse_id','=',self.warehouse_id.id))
					quant_ids = quant_obj.sudo().search(domain)
					a_qty = sum(quant_ids.mapped('quantity'))
					# DATA
					if pl.material_id.default_code:
						temp = (0,0,{
							'model_id': setting.technic_setting_id.model_id.id,
							'maintenance_type_id': pl.maintenance_type_id.id,
							'product_id': pl.material_id.id,
							'default_code': pl.material_id.default_code,
							'qty': line.qty * pl.qty,
							'available_qty': a_qty,
							'order_qty': 0,
						})
						temp_datas.append(temp)
		if temp_datas:
			self.pm_generated_line = temp_datas
		return True

	# Pivot оор харах
	def see_expenses_view(self):
		if self.pm_generated_line:
			context = dict(self._context)
			# GET views ID
			mod_obj = self.env['ir.model.data']
			pivot_res = mod_obj._xmlid_lookup('mw_technic_maintenance.maintenance_pm_material_generator_pivot_view')
			pivot_id = pivot_res and pivot_res[2] or False

			return {
				'name': self.name,
				'view_mode': 'pivot',
				'res_model': 'maintenance.pm.material.generator.line',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				# 'search_view_id': search_id,
				'domain': [('parent_id','=',self.id)],
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context,
			}

	def export_report(self):
		# GET datas
		query = """
			SELECT
				plan.product_id as product_id,
				sum(plan.qty) as qty
			FROM maintenance_pm_material_generator_line as plan
			LEFT JOIN product_product as pp on pp.id = plan.product_id
			WHERE
				  plan.parent_id = %d
			GROUP BY plan.product_id, pp.name_attribute
			ORDER BY pp.name_attribute
		""" % (self.id)
		self.env.cr.execute(query)
		plans = self.env.cr.dictfetchall()
		if plans:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Forecast report.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_font_size(10)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#E9A227')

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(10)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(10)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right0 = workbook.add_format({'italic':1})
			contest_right0.set_text_wrap()
			contest_right0.set_font_size(10)
			contest_right0.set_align('right')
			contest_right0.set_align('vcenter')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(10)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			# DRAW
			worksheet = workbook.add_worksheet(u'Тайлан')
			worksheet.write(0,2, self.name, h1)

			# TABLE HEADER
			row = 1
			worksheet.write(row, 0, u"№", header)
			worksheet.write(row, 1, u"Барааны нэр", header_wrap)
			worksheet.set_column(1, 1, 45)
			worksheet.set_row(1, 25)
			worksheet.write(row, 2, u"Хэрэгцээт тоо", header_wrap)
			worksheet.write(row, 3, u"Үлдэгдэл", header_wrap)
			worksheet.write(row, 4, u"Захиалах тоо", header_wrap)
			worksheet.set_column(3, 3, 10)
			worksheet.freeze_panes(2, 2)

			row = 2
			number = 1
			quant_obj = self.env['stock.quant']
			for line in plans:
				# DATA
				worksheet.write(row, 0, number, number_right)
				product = self.env['product.product'].search([('id','=',line['product_id'])], limit=1)
				worksheet.write(row, 1, product.name_get()[0][1], contest_left)
				worksheet.write(row, 2, line['qty'], contest_right0)
				a_qty = 0
				domain = [('product_id','=',line['product_id']),('location_id.usage','=','internal')]
				if self.warehouse_id:
					domain.append(('location_id.set_warehouse_id','=',self.warehouse_id.id))
				quant_ids = quant_obj.sudo().search(domain)
				a_qty = sum(quant_ids.mapped('quantity'))
				worksheet.write(row, 3, a_qty or 0, contest_right0)
				worksheet.write_formula(row, 4,
					'{=IFERROR('+self._symbol(row,2) +'-'+ self._symbol(row, 3)+',0)}', contest_right0)
				row += 1
				number += 1

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

class MaintenancePmMaterialGeneratorLine(models.Model):
	_name = 'maintenance.pm.material.generator.line'
	_description = 'maintenance.pm.material.generator line'
	_order = 'product_id, model_id'

	# Columns
	parent_id = fields.Many2one('maintenance.pm.material.generator', string=u'Parent generator', ondelete='cascade')

	model_id = fields.Many2one('technic.model.model', string=u'Модель', required=True,)
	maintenance_type_id = fields.Many2one('maintenance.type', string=u'PM нэр', required=True,)
	product_id = fields.Many2one('product.product', string=u'Материал', readonly=True, required=True,)
	categ_id = fields.Many2one(related='product_id.categ_id', string=u'Ангилал', readonly=True, )
	default_code = fields.Char(string=u'Барааны код', required=True,)

	qty = fields.Integer(string=u'Хэрэгцээт тоо', required=True,)
	available_qty = fields.Integer(string=u'Үлдэгдэл', required=True, group_operator='avg')
	order_qty = fields.Integer(string=u'Захиалах тоо', required=True,)

class PmTechinicSeetingLine(models.Model):
	_name = 'pm.technic.setting.line'
	_description = 'PM Technic setting line'
	_order = 'technic_setting_id'

	# Columns
	parent_id = fields.Many2one('maintenance.pm.material.generator', string=u'Parent generator', ondelete='cascade')
	technic_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техник тохиргоо', required=True,)
	line_ids = fields.One2many('pm.technic.setting.line.line', 'parent_id', string='Lines', copy=False, required=True)
	
	@api.depends('line_ids')
	def _methods_compute(self):
		for obj in self:
			txt = ""
			for ll in obj.line_ids:
				txt += (ll.maintenance_type_id.name or '-')+'='+str(ll.qty or 0)+', '
			obj.description = txt
	description = fields.Text(compute=_methods_compute, string=u'Тайлбар', )

class PmTechinicSeetingLineLine(models.Model):
	_name = 'pm.technic.setting.line.line'
	_description = 'PM Technic setting line line'
	_order = 'maintenance_type_id'

	# Columns
	parent_id = fields.Many2one('pm.technic.setting.line', string=u'Parent generator line', ondelete='cascade')
	maintenance_type_id = fields.Many2one('maintenance.type', string=u'PM нэр', readonly=True,)
	qty = fields.Integer(string=u'Тоо ширхэг', required=True, default=0)
	maintenance_pm_material_condif_id = fields.Many2one('maintenance.pm.material.config', string=u'Config line', readonly=True,)
