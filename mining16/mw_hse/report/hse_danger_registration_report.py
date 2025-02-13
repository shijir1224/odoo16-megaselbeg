# -*- coding: utf-8 -*-
from odoo import models, fields
import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
import base64
from datetime import date

class HseDangerRegistrationReport(models.TransientModel):
	_name = "hse.danger.registration.report"
	_description = "Danger registration report"

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
			file_name ='Химийн бодисын тайлан.xlsx'

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
			normal_wrap.set_bg_color('FFFFFF')

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

			worksheet = workbook.add_worksheet(u'Хиймийн бодсын тайлан')
			row = +0
			worksheet.merge_range(row, 0, row, 16, u'Хиймийн бодсын төвлөрсөн агуулхын орлого бүртгэл', header)
			worksheet.merge_range( 1, 0, 2,0, u'№', header)
			worksheet.merge_range(1, 1, 2, 1, u'Хиймийн бодисын нэр', header)
			worksheet.merge_range(1, 2, 2, 2, u'Хиймийн бодисын томьёо', header)
			worksheet.merge_range(1, 3, 2, 3, u'CAS код', header)
			worksheet.merge_range(1, 4, 2, 4,u'Тусгай зөвшөөрлийн дугаар', header)
			worksheet.merge_range(1, 5,  2, 5,u'Эхний үлдэгдэл,тн', header)
			worksheet.merge_range(1, 6, 1, 8, u'Агуулхад хүлээн авсан байдал', header)
			worksheet.merge_range(1, 9, 1, 11, u'Агуулхаас зарлагдсан байдал', header)
			worksheet.merge_range(1, 12, 2, 12, u'Нийт үлдэгдэл,тн', header)
			worksheet.merge_range(1, 13, 1, 16, u'Ашиглагдсан химийн бодисын сав, баглаа боодол', header)
			worksheet.write(2, 6, u'Оггоо', header)
			worksheet.write(2, 7, u'Хэмжээ,тн', header)
			worksheet.write(2, 8, u'Хянагдсан ажилтаны нэр', header)
			worksheet.write(2, 9, u'Хэмжээ,тн', header)
			worksheet.write(2, 10, u'Ашиглах хэсэгийн нэр', header)
			worksheet.write(2, 11, u'Хянасан ажилтаны нэр', header)
			worksheet.write(2, 13, u'Уут/Шуудай/,ш', header)
			worksheet.write(2, 14, u'Төмөр торх /боошиг/,ш', header)
			worksheet.write(2, 15, u'Хуванцар торх /боошиг/,ш', header)
			worksheet.write(2, 16, u'Хуванцар сав/,ш', header)
			worksheet.set_row(row + 1, 30)
			worksheet.set_row(row + 2, 45)
			worksheet.set_column('A:A', 5)
			worksheet.set_column('B:B', 23)
			worksheet.set_column('C:C', 20)
			worksheet.set_column('D:D', 15)
			worksheet.set_column('E:E', 20)
			worksheet.set_column('F:F', 20)
			worksheet.set_column('J:J', 25)
			worksheet.set_column('H:H', 15)
			worksheet.set_column('I:I', 20)
			worksheet.set_column('G:G', 15)
			worksheet.set_column('K:K', 20)
			worksheet.set_column('L:L', 20)
			worksheet.set_column('M:M', 15)
			worksheet.set_column('N:N', 15)
			worksheet.set_column('M:M', 15)
			worksheet.set_column('O:O', 20)
			worksheet.set_column('P:P', 20)
			worksheet.set_column('Q:Q', 20)
			worksheet.set_column('R:R', 15)
			worksheet.write(3, 0, u'', normal_wrap)
			worksheet.write(3, 1, u'', normal_wrap)
			worksheet.write(3, 2, u'', normal_wrap)
			worksheet.write(3, 3, u'', normal_wrap)
			worksheet.write(3, 4, u'', normal_wrap)
			worksheet.write(3, 5, u'', normal_wrap)
			worksheet.write(3, 6, u'', normal_wrap)
			worksheet.write(3, 7, u'', normal_wrap)
			worksheet.write(3, 8, u'', normal_wrap)
			worksheet.write(3, 9, u'', normal_wrap)
			worksheet.write(3, 10, u'', normal_wrap)
			worksheet.write(3, 11, u'', normal_wrap)
			worksheet.write(3, 12, u'', normal_wrap)
			worksheet.write(3, 13, u'', normal_wrap)
			worksheet.write(3, 14, u'', normal_wrap)
			worksheet.write(3, 15, u'', normal_wrap)
			worksheet.write(3, 16, u'', normal_wrap)
			row = 3
			n=1
			domains=[
				('date', '>=', self.date_start),
				('date', '<=', self.date_end)
			]
			if self.branch_id:
				domains.append(('parent_id.branch_id','=',self.branch_id.id))

			dangers = self.env['hse.danger.registration.line'].search(domains)
			for danger in dangers:
				worksheet.write(row, 0, n, contest_center)
				worksheet.write(row, 1, danger.chemicals_name if danger.chemicals_name else '', normal_wrap)
				worksheet.write(row, 2, danger.chemical_formula if danger.chemical_formula else ' ', normal_wrap)
				worksheet.write(row, 3, danger.cas_code if danger.cas_code else ' ', normal_wrap)
				worksheet.write(row, 4, danger.license_number if danger.license_number else ' ', normal_wrap)
				worksheet.write(row, 5, danger.first_balance if danger.first_balance else ' ', normal_wrap)
				worksheet.write(row, 6, danger.date.strftime('%Y-%m-%d') if danger.date else ' ', normal_wrap)
				worksheet.write(row, 7, danger.rec_amount if danger.rec_amount else ' ', normal_wrap)
				worksheet.write(row, 8, danger.rec_employee_id.name if danger.rec_employee_id.name else '', normal_wrap)
				worksheet.write(row, 9, danger.wit_amount if danger.wit_amount else ' ', normal_wrap)
				worksheet.write(row, 10, danger.use_section if danger.use_section else ' ', normal_wrap)
				worksheet.write(row, 11, danger.wit_employee_id.name if danger.wit_employee_id.name else ' ', normal_wrap)
				worksheet.write(row, 12, danger.total_balance if danger.total_balance else ' ', normal_wrap)
				worksheet.write(row, 13, danger.bag if danger.bag else ' ', normal_wrap)
				worksheet.write(row, 14, danger.iron if danger.iron else ' ', normal_wrap)
				worksheet.write(row, 15, danger.plastic_bag if danger.plastic_bag else ' ', normal_wrap)
				worksheet.write(row, 16, danger.plastic_bottle if danger.plastic_bottle else ' ', normal_wrap)
				row += 1
				n += 1
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