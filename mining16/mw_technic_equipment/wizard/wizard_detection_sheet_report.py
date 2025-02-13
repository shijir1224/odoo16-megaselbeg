# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

import time
import xlsxwriter
from io import BytesIO
import base64

import logging
_logger = logging.getLogger(__name__)

class WizardDetectionSheetReport(models.TransientModel):
	_name = "wizard.detection.sheet.report"
	_description = "wizard detection sheet report"

	@api.model
	def _get_start_date(self):
		date1 = datetime.now()
		date2 = date1 + timedelta(days=-14)
		return date2

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=_get_start_date)
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	technic_id = fields.Many2one('technic.equipment', string=u'Техник', 
		domain=[('owner_type','=','own_asset'),('state','!=','draft')])
	
	
	def export_report(self):
		if self.date_start <= self.date_end:
			conditions = ""
			if self.technic_id:
				conditions = " and tt.id = %d " % self.technic_id.id
			query = """
				SELECT 	
					temp.technic_id as technic_id,
					temp.qty as qty,
					temp.name as name,
					temp.description as description,
					temp.operator_note as operator_note
				FROM (
					SELECT 	
						tt.id as technic_id,
						ll.check_name as name,
						count(1) as qty,
						array_agg(DISTINCT ll.description) as description,
						array_agg(DISTINCT ins.operator_note) as operator_note
					FROM technic_inspection_line as ll
					LEFT JOIN technic_inspection as ins on ins.id = ll.parent_id
					LEFT JOIN technic_equipment as tt on (tt.id = ins.technic_id)
					WHERE ins.date_inspection >= '%s' and
					      ins.date_inspection <= '%s' and
					      ins.state = 'done' and 
					      (ll.is_check != 't' or ll.is_check is null) 
					       %s 
					GROUP BY tt.report_order, tt.program_code, tt.id, ll.check_name
					ORDER BY tt.report_order, tt.program_code, tt.name, ll.check_name
				) as temp
				WHERE temp.qty >= 5
			""" % (self.date_start, self.date_end, conditions)
			self.env.cr.execute(query)
			# print '======', query
			inspections = self.env.cr.dictfetchall()

			# Generate EXCEL
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'defection_sheet_'+str(self.date_end)+'.xlsx'

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

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

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

			sub_total_90 = workbook.add_format({'bold': 1})
			sub_total_90.set_text_wrap()
			sub_total_90.set_font_size(9)
			sub_total_90.set_align('center')
			sub_total_90.set_align('vcenter')
			sub_total_90.set_border(style=1)
			sub_total_90.set_bg_color('#F7EE5E')
			sub_total_90.set_rotation(90)

			worksheet = workbook.add_worksheet('Defection Sheet')
			worksheet.set_zoom(80)
			worksheet.write(0,2, "Defection sheet report", h1)

			# TABLE HEADER
			row = 1
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column(0, 0, 4)
			worksheet.write(row, 1, u"Төрөл", header_wrap)
			worksheet.set_column(1, 1, 5)
			worksheet.write(row, 2, u"Техникийн нэр", header_wrap)
			worksheet.set_column(2, 2, 20)
			worksheet.write(row, 3, u"Парк дугаар", header_wrap)
			worksheet.set_column(3, 3, 9)
			worksheet.write(row, 4, u'Тоо', header_wrap)
			worksheet.set_column(4, 4, 4)
			worksheet.write(row, 5, u'Үзлэгийн нэр', header_wrap)
			worksheet.set_column(5, 5, 50)
			worksheet.write(row, 6, u'Тайлбар', header_wrap)
			worksheet.set_column(6, 6, 90)
			worksheet.write(row, 7, u'Операторын тэмдэглэл', header_wrap)
			worksheet.set_column(7, 7, 90)
			worksheet.freeze_panes(2, 4)
			# DATA зурах
			row_dict = {}
			row = 2
			row_start = 2
			number = 1
			first =True
			type_name = ''

			for line in inspections:
				technic = self.env['technic.equipment'].browse(line['technic_id'])
				_logger.info('---- technic --- id %s %s %s %s'%(technic.id, line['name'], line['description'], line['operator_note']))
				if not first and type_name != technic.technic_type:
					worksheet.merge_range(row_start, 1, row-1, 1, type_name, sub_total_90)
					row_start = row

				if line['technic_id'] not in row_dict:
					worksheet.write(row, 0, number, number_right)
					worksheet.write(row, 2, technic.park_number, contest_left)
					worksheet.write(row, 3, technic.program_code, contest_left)
					row_dict[line['technic_id']] = row
					number += 1

				worksheet.write(row, 4, line['qty'], contest_center)
				worksheet.write(row, 5, line['name'], contest_left)
				# Тайлбар
				txt = ''
				for ll in line['description']:
					if ll:
						txt += unicode(ll, "utf-8")+', '
				worksheet.write(row, 6, txt, contest_left)
				# Операторын тэмдэглэл
				txt = ''
				for ll in line['operator_note']:
					if ll:
						txt += unicode(ll, "utf-8")+', '
				worksheet.write(row, 7, txt, contest_left)
				
				row += 1
				first = False
				type_name = technic.technic_type
				# 

			# =============================
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
	             'type': 'ir.actions.act_url',
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


