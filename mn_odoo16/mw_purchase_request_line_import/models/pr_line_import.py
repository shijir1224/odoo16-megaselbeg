# -*- coding: utf-8 -*-
from odoo import fields, models, _
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.exceptions import UserError

class PurchaseReuqestLineImport(models.Model):
	_inherit = 'purchase.request'

	import_data = fields.Binary('Import excel', copy=False)

	def action_export(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(u'Гүйцэтгэл')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_bg_color('#EE9A4D')
		header.set_font_name('Arial')
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_font_size(9)
		contest_center.set_font_name('Arial')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		contest_left = workbook.add_format()
		contest_left.set_font_size(9)
		contest_left.set_font_name('Arial')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		row = 0

		worksheet.write(row, 0, u"Бараа", header)
		worksheet.write(row, 1, u"Тайлбар зориулалт", header)
		worksheet.write(row, 2, u"Тоо хэмжээ", header)
		worksheet.set_column('A:A', 20)
		worksheet.set_column('B:B', 30)
		worksheet.set_column('C:C', 10)

		for line in self.line_ids:
			row += 1
			worksheet.write(row, 0, line.product_id.default_code, contest_center)
			worksheet.write(row, 1, line.desc, contest_left)
			worksheet.write(row, 2, line.qty, contest_center)

		workbook.close()

		out = base64.encodebytes(output.getvalue())
		file_name = self.name+'.xlsx'
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			 'type' : 'ir.actions.act_url',
			 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			 'target': 'new',
		}

	def action_import_line(self):
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.import_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(u'Алдаа',u'Мэдээллийн файлыг уншихад алдаа гарлаа.\nЗөв файл эсэхийг шалгаад дахин оролдоно уу!')
		book = xlrd.open_workbook(fileobj.name)
		
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(u'Алдаа', u'Sheet -ны дугаар буруу байна.')
		nrows = sheet.nrows

		line_obj = self.env['purchase.request.line']
		for item in range(1, nrows):
			row = sheet.row(item)
			try:
				default_code = str(row[0].value)
			except ValueError:
				default_code = str(int(row[0].value))
			desc = row[1].value
			qty = row[2].value
			product_id = self.env['product.product'].search([('default_code','=',default_code)], limit=1)
			if product_id:
				line_obj.create({
					'request_id': self.id,
					'product_id': product_id.id,
					'desc': desc,
					'qty': qty
				})
			else:
				raise UserError(default_code+' кодтой бараа олдсонгүй!!!')