# -*- coding: utf-8 -*-
from odoo import models, fields

import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
import base64
from datetime import date

class WizardHseDailyReport(models.TransientModel):
	_name = "wizard.hse.daily.report"
	_description = "wizard.hse.daily.report"

	date_start = fields.Date(string='Эхлэх огноо', required=True,  default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(string='Дуусах огноо', required=True)
	branch_id = fields.Many2one('res.branch', string='Төсөл', required=True)

	def _set_capitalize(self, txt):
		if txt:
			return txt.capitalize()
		else:
			return txt

	def excel_report(self):
		if self.date_start <= self.date_end:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name ='Өдөр тутмын ХАБЭАБО-ны мэдээ тайлан.xlsx'

			header = workbook.add_format({'bold': 1})
			header.set_font_size(10)
			header.set_font('Times new roman')
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#FBE5D6')

			normal_wrap = workbook.add_format()
			normal_wrap.set_text_wrap()
			normal_wrap.set_font_size(9)
			normal_wrap.set_font('Times new roman')
			normal_wrap.set_align('center')
			normal_wrap.set_align('vcenter')
			normal_wrap.set_border(style=1)
			normal_wrap.set_bg_color('#FBE5D6')

			normal_left = workbook.add_format()
			normal_left.set_text_wrap()
			normal_left.set_font_size(9)
			normal_left.set_font('Times new roman')
			normal_left.set_align('center')
			normal_left.set_align('vcenter')
			normal_left.set_border(style=1)
			normal_left.set_bg_color('#FBE5D6')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_font('Times new roman')
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)
			contest_center.set_bg_color('#DEEBF7')

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_font('Times new roman')
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)
			contest_left.set_bg_color('#DEEBF7')

			number_format = workbook.add_format()
			number_format.set_text_wrap()
			number_format.set_font_size(9)
			number_format.set_font('Times new roman')
			number_format.set_align('center')
			number_format.set_align('vcenter')
			number_format.set_border(style=1)

			worksheet = workbook.add_worksheet(u'Өдөр тутмын мэдээ')
			row = 0
			worksheet.merge_range(row, 0, row, 5, u'ӨДӨР ТУТМЫН ХАБЭАБО-НЫ МЭДЭЭ', header)
			worksheet.merge_range(1, 0, 1, 1, u'Төслийн нэр', normal_wrap)
			worksheet.merge_range(2, 0, 2, 1, u'Үйлдвэрлэлийн осолгүй  ажилласан', contest_left)
			worksheet.write(2, 2, u'Хоног', number_format)
			worksheet.write(2, 4, u'Хүн/цаг', number_format)
			worksheet.merge_range(3, 0, 5, 0, u' Ажиллах хүчний мэдээлэл', contest_left)
			worksheet.merge_range(3, 1, 3, 2, u'Үндсэн', normal_wrap)
			worksheet.write(4, 1, u'ИТА', contest_center)
			worksheet.write(4, 2, u' Ажилчид', contest_center)
			worksheet.merge_range(3, 3, 4, 3, u'Гэрээт', normal_wrap)
			worksheet.merge_range(3, 4, 4, 4, u'Зочин /төв оффис/',normal_wrap)
			worksheet.merge_range(3, 5, 4, 5, u'Нийт', normal_wrap)
			worksheet.merge_range(6, 0, 6, 5, u'Осол, осол дөхсөн тохиолдлын мэдээ', normal_wrap)
			worksheet.merge_range(7, 0, 7, 2, u'Үйлдвэрлэлийн осол', contest_left)
			worksheet.merge_range(8, 0, 8, 2, u'Осол дөхсөн тохиолдол', contest_left)
			worksheet.merge_range(9, 0, 9, 2, u'Анхны тусламж авсан', contest_left)
			worksheet.merge_range(10, 0, 10, 2, u'Эмнэлэгийн тусламж авсан', contest_left)
			worksheet.merge_range(11, 0, 11, 2, u'Хугацаа алдсан гэмтэл', contest_left)
			worksheet.merge_range(12, 0, 12, 2, u'Өмчийн эвдрэл гэмтэл', contest_left)
			worksheet.merge_range(13, 0, 13, 2, u'Асгаралт', contest_left)
			worksheet.merge_range(14, 0, 14, 2, u'Гал түймрийн тохиолдол', contest_left)
			worksheet.merge_range(15, 0, 15, 3, u'ХАБЭА-н ажлын мэдээ', normal_left)
			worksheet.write(15, 4, u'Сургалт орсон тоо', contest_left)
			worksheet.write(15, 5, u'Сургалтанд хамрагдсан ажилтны тоо', contest_left)
			worksheet.merge_range(16, 0, 20, 0, u'Сургалт', contest_left)
			worksheet.merge_range(16, 1, 16, 3, u'Урьдчилсан зааварчилгаа', contest_left)
			worksheet.merge_range(17, 1, 17, 3, u'Анхан шатны зааварчилгаа', contest_left)
			worksheet.merge_range(18, 1, 18, 3, u'Зочны зааварчилгаа', contest_left)
			worksheet.merge_range(19, 1, 19, 3, u'Ээлжит зааварчилгаа', contest_left)
			worksheet.merge_range(20, 1, 20, 3, u'Ээлжит бус зааварчилгаа', contest_left)
			worksheet.merge_range(21, 0, 24, 0, u'Эрсдэлийн хяналт', contest_left)
			worksheet.merge_range(21, 1, 21, 4, u'Өндөр эрсдэлтэй ажлын зөвшөөрөл', contest_left)
			worksheet.merge_range(22, 1, 22, 4, u'Болзошгүй эрсдлийн үнэлгээ', contest_left)
			worksheet.merge_range(23, 1, 23, 4, u'Ажлын байрны үзлэг', contest_left)
			worksheet.merge_range(24, 1, 24, 4, u'Тээврийн хэрэгслийн хяналт', contest_left)
			worksheet.merge_range(25, 0, 28, 0, u'Арга хэмжээ', contest_left)
			worksheet.merge_range(25, 1, 25, 4, u'Талбайн зааварчилгаа', contest_left)
			worksheet.merge_range(26, 1, 26, 4, u'ХАБЭА-н уулзалт', contest_left)
			worksheet.merge_range(27, 1, 27, 4, u'Мэдэгдэл өгсөн', contest_left)
			worksheet.merge_range(28, 1, 28, 4, u'Ажил зогсоосон', contest_left)
			worksheet.merge_range(29, 0, 29, 1, u'Бусад', normal_wrap)
			
			domains=[
				('date', '>=', self.date_start),
				('date', '<=', self.date_end)
			]
			if self.branch_id:
				domains.append(('branch_id','=',self.branch_id.id))
			daily = self.env['hse.daily.report.line'].search(domains)
			worksheet.merge_range(1, 2, 1, 5, daily.branch_id.name if daily else '', normal_wrap)
			worksheet.write(2, 3, u' ', number_format)
			worksheet.write(2, 5, u' ', number_format)
			worksheet.write(5, 1, sum(daily.mapped('ita_count')) if daily else 0, number_format)
			worksheet.write(5, 2, sum(daily.mapped('employee_count')) if daily else 0, number_format)
			worksheet.write(5, 3, sum(daily.mapped('gereet_employee_count')) if daily else 0, number_format)
			worksheet.write(5, 4, sum(daily.mapped('guest_count')) if daily else 0, number_format)
			worksheet.write(5, 5, sum(daily.mapped('total_employee')) if daily else 0, number_format)
			worksheet.merge_range(7, 3, 7, 5, sum(daily.mapped('uildver_osol')) if daily else 0, number_format)
			worksheet.merge_range(8, 3, 8, 5,  sum(daily.mapped('osol_duhsun')) if daily else 0, number_format)
			worksheet.merge_range(9, 3, 9, 5, sum(daily.mapped('first_help')) if daily else 0, number_format)
			worksheet.merge_range(10, 3, 10, 5, sum(daily.mapped('hosp_help')) if daily else 0, number_format)
			worksheet.merge_range(11, 3, 11, 5, sum(daily.mapped('timed_damage')) if daily else 0, number_format)
			worksheet.merge_range(12, 3, 12, 5, sum(daily.mapped('property_damage')) if daily else 0, number_format)
			worksheet.merge_range(13, 3, 13, 5, sum(daily.mapped('leakage')) if daily else 0, number_format)
			worksheet.merge_range(14, 3, 14, 5, sum(daily.mapped('fire_incident')) if daily else 0, number_format)
			worksheet.write(16, 4, sum(daily.mapped('urid_zaavar')) if daily else 0, number_format)
			worksheet.write(17, 4, sum(daily.mapped('first_zaavar')) if daily else 0, number_format)
			worksheet.write(18, 4, sum(daily.mapped('guest_zaavar')) if daily else 0, number_format)
			worksheet.write(19, 4, sum(daily.mapped('regularly_zaavar')) if daily else 0, number_format)
			worksheet.write(20, 4, sum(daily.mapped('not_regularly_zaavar')) if daily else 0, number_format)
			worksheet.write(16, 5, sum(daily.mapped('urid_zaavar_sum')) if daily else 0, number_format)
			worksheet.write(17, 5, sum(daily.mapped('first_zaavar_sum')) if daily else 0, number_format)
			worksheet.write(18, 5, sum(daily.mapped('guest_zaavar_sum')) if daily else 0, number_format)
			worksheet.write(19, 5, sum(daily.mapped('regularly_zaavar_sum')) if daily else 0, number_format)
			worksheet.write(20, 5, sum(daily.mapped('not_regularly_zaavar_sum')) if daily else 0, number_format)
			worksheet.write(21, 5, sum(daily.mapped('high_risk')) if daily else 0, number_format)
			worksheet.write(22, 5, sum(daily.mapped('risk_assessment')) if daily else 0, number_format)
			worksheet.write(23, 5, sum(daily.mapped('workplace_inspection')) if daily else 0, number_format)
			worksheet.write(24, 5, sum(daily.mapped('vehicle_check')) if daily else 0, number_format)
			worksheet.write(25, 5, sum(daily.mapped('field_instruction')) if daily else 0, number_format)
			worksheet.write(26, 5, sum(daily.mapped('hse_conf')) if daily else 0, number_format)
			worksheet.write(27, 5, sum(daily.mapped('noticed')) if daily else 0, number_format)
			worksheet.write(28, 5, sum(daily.mapped('work_stopped')) if daily else 0, number_format)
			names = []
			others = daily.filtered(lambda r: r.other != False)
			names += others.mapped('other')
			worksheet.merge_range(29, 2, 29, 5, ', '.join([(n) for n in names]) if daily else ' ', normal_wrap)
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
			raise UserError((u'Бичлэг олдсонгүй!'))