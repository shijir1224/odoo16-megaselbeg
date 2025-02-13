# -*- coding: utf-8 -*-

from xml import dom
from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, date, timedelta
import time
import xlsxwriter
from io import BytesIO
import base64
import pandas

class WizardMaintenancePrLine(models.TransientModel):
	_name = "wizard.daily.report"  
	_description = "Wizard Daily report"  

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	technic_ids = fields.Many2many('technic.equipment', string='Техникүүд')
	branch_ids = fields.Many2many('res.branch', string='Салбарууд')
	# warehouse_ids = fields.Many2many('stock.warehouse', string='Агуулахууд')

	def excel_daily_report(self):
		if self.date_start <= self.date_end:
			output=BytesIO()
			workbook=xlsxwriter.Workbook(output)
			file_name='Daily_report_'+self.date_start.strftime("%Y-%m-%d")+'__'+self.date_end.strftime("%Y-%m-%d")+'.xlsx'

			h1=workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header_wrap=workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			cause_header=workbook.add_format({'bold': 1})
			cause_header.set_font_size(9)
			cause_header.set_align('center')
			cause_header.set_align('vcenter')
			cause_header.set_border(style=1)
			cause_header.set_bg_color('#E9A227')
			cause_header.set_rotation(90)
			
			cause_header_wrap=workbook.add_format({'bold': 1})
			cause_header_wrap.set_text_wrap()
			cause_header_wrap.set_font_size(9)
			cause_header_wrap.set_align('center')
			cause_header_wrap.set_align('vcenter')
			cause_header_wrap.set_border(style=1)
			cause_header_wrap.set_bg_color('#E9A227')
			cause_header_wrap.set_rotation(90)

			number_right=workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right=workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_left=workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center=workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)
			contest_center.set_bg_color('#ffe6b3')

			mh_0=workbook.add_format()
			mh_0.set_text_wrap()
			mh_0.set_font_size(9)
			mh_0.set_align('center')
			mh_0.set_align('vcenter')
			mh_0.set_border(style=1)
			mh_0.set_bg_color('#b3b3b3')
			
			mh_720=workbook.add_format()
			mh_720.set_text_wrap()
			mh_720.set_font_size(9)
			mh_720.set_align('center')
			mh_720.set_align('vcenter')
			mh_720.set_border(style=1)
			mh_720.set_bg_color('#F7EE5E')
			
			mh_other=workbook.add_format()
			mh_other.set_text_wrap()
			mh_other.set_font_size(9)
			mh_other.set_align('center')
			mh_other.set_align('vcenter')
			mh_other.set_border(style=1)
			mh_other.set_bg_color('#ffcc66')

			other=workbook.add_format()
			other.set_text_wrap()
			other.set_font_size(9)
			other.set_align('center')
			other.set_align('vcenter')
			other.set_border(style=1)
			other.set_bg_color('#ffcc66')

			sub_total=workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(9)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			worksheet=workbook.add_worksheet(u'Daily report')
			worksheet.set_zoom(80)
			# worksheet.write(0, 2, u"Daily report", h1)
			cause_ids = self.env['mining.motohours.cause'].sudo().search([('is_repair','=',True)])

			# TABLE HEADER
			row=0
			# worksheet.set_default_row(5)
			worksheet.set_row(1, 30)
			worksheet.merge_range(row, 0,row+1, 0, u'Д/д', header_wrap)
			worksheet.merge_range(row, 1,row+1, 1, u'Төрөл', header_wrap)
			worksheet.merge_range(row, 2,row+1, 2, u'Парк дугаар', header_wrap)
			worksheet.merge_range(row, 3,row+1, 3, u'Бренд', header_wrap)
			worksheet.set_column(3, 3, 15)
			worksheet.merge_range(row, 4,row+1, 4, u'Модел', header_wrap)
			worksheet.set_column(4, 4, 15)
			worksheet.merge_range(row, 5,row+1, 5, u'Сериал дугаар', header_wrap)
			worksheet.set_column(5, 5, 20)
			worksheet.merge_range(row, 6,row, 5+len(cause_ids), u'Зогсолтын төрөл', header_wrap)
			col = 6
			for cause in cause_ids:
				worksheet.write(row+1, col, cause.cause_name, cause_header)
				worksheet.set_column(col, col, 5)
				worksheet.set_row(row+1, 150)
				col += 1
			worksheet.write(row, col, u'Уулын зогсолтын цаг', header_wrap)
			worksheet.set_column(col, col, 10)
			worksheet.set_row(row, 40)
			worksheet.write(row+1, col, u'Уулын зогсолтын цаг / Диспетчерийн НӨӨЦ гэсэн бүртгэлээс татах', cause_header_wrap)
			worksheet.set_column(col, col, 10)
			worksheet.merge_range(row, col+1,row+1, col+1, u'Нийт засварт зогссон цаг', header_wrap)
			worksheet.merge_range(row, col+2,row+1, col+2, u'Нийт нөөцөнд зоссон цаг', header_wrap)
			worksheet.merge_range(row, col+3,row+1, col+3, u'Техникийн бэлэн байдал %', header_wrap)
			worksheet.merge_range(row, col+4,row+1, col+4, u'Техник ашиглалт', header_wrap)
			worksheet.merge_range(row, col+5,row+1, col+5, u'Техникийн төрлөөр Нийт бэлэн байдал %', header_wrap)
			worksheet.merge_range(row, col+6,row+1, col+6, u'Техникийн төрлөөр Нийт ашиглалт %', header_wrap)

			if not self.branch_ids:
				domains=[
					('date', '>=', self.date_start.strftime("%Y-%m-%d")),
					('date', '<=', self.date_end.strftime("%Y-%m-%d")),
					('motohour_id.state', '=', 'approved'),
					('branch_id','in',[self.env.user.branch_id.id])]
			else:
				domains=[
					('date', '>=', self.date_start.strftime("%Y-%m-%d")),
					('date', '<=', self.date_end.strftime("%Y-%m-%d")),
					('motohour_id.state', '=', 'approved'),
					('branch_id','in',self.branch_ids.ids)]
			if self.technic_ids:
				domains.append(('technic_id','in',self.technic_ids.ids))
			print(domains)
			motos=self.env['mining.motohour.entry.line'].search(domains)
			row=2
			number=1
			technic_ids = motos.mapped('technic_id')
			technic_ids = technic_ids.sorted(key=lambda r: r.name)
			technic_ids = technic_ids.sorted(key=lambda r: r.technic_type, reverse=True)
			for tech in technic_ids:
				mot_ids = motos.filtered(lambda r: r.technic_id.id == tech.id)
				worksheet.write(row, 0, number, contest_center) # Merge
				worksheet.write(row, 1, tech.technic_type, contest_center) # Merge
				worksheet.write(row, 2, tech.park_number, contest_center) # Merge
				worksheet.write(row, 3, tech.model_id.brand_id.name, contest_center) # Merge
				worksheet.write(row, 4, tech.model_id.name, contest_center) # Merge
				worksheet.write(row, 5, tech.vin_number, contest_center)
				mot_cause_lines = mot_ids.mapped('motohour_cause_line')
				col = 6
				total_time = 0
				for cause in cause_ids:
					moto_lines = mot_cause_lines.filtered(lambda r: r.cause_id.id == cause.id)
					time = sum(moto_lines.mapped('diff_time'))
					total_time += time
					if time == 0:
						worksheet.write(row, col, time, mh_0)
					elif time%24 == 0:
						worksheet.write(row, col, time, mh_720)
					else:
						worksheet.write(row, col, time, mh_other)
					col += 1
				worksheet.write(row, col, total_time, other)
				worksheet.write(row, col+1, total_time, other)
				worksheet.write(row, col+2, total_time, other)
				worksheet.write(row, col+3, total_time, other)
				worksheet.write(row, col+4, total_time, other)
				row += 1
				number += 1
			# =============================
			workbook.close()
			out=base64.encodebytes(output.getvalue())
			excel_id=self.env['report.excel.output'].create(
				{'data': out, 'name': file_name})

			return {
				 'type': 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))