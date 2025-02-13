# -*- coding: utf-8 -*-
from odoo import fields, models, _
from io import BytesIO
import base64
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.exceptions import UserError

class PurchaseOrderLineImport(models.Model):
	_inherit = 'purchase.order'

	import_data = fields.Binary('Import excel', copy=False)

	def action_export(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(u'Гүйцэтгэл')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#9ad808')
		header.set_text_wrap()
		header.set_font_name('Arial')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(11)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_font_name('Arial')

		cell_format2 = workbook.add_format({
			'border': 1,
			'align': 'right',
			'font_size':9,
			'font_name': 'Arial',
		})

		worksheet.merge_range(0, 0, 0, 2, u'"'+self.name+'"'+u' Худалдан авалт', header_wrap)
		worksheet.merge_range(1, 0, 1, 2, u'Худалдан авалт импортлох загвар', contest_center)

		row = 2

		worksheet.write(row, 0, u"Бараа", header)
		worksheet.write(row, 1, u"Тоо хэмжээ", header)
		worksheet.write(row, 2, u"Үнэ", header)
		worksheet.set_column('A:A', 20)
		worksheet.set_column('B:C', 10)

		for item in self.order_line:
			row += 1
			worksheet.write(row, 0, item.product_id.default_code, cell_format2)
			worksheet.write(row, 1, item.product_qty, cell_format2)
			worksheet.write(row, 2, item.price_unit, cell_format2)

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

		line_obj = self.env['purchase.order.line']
		for item in range(3, nrows):
			row = sheet.row(item)
			try:
				default_code = str(row[0].value)
			except ValueError:
				default_code = str(int(row[0].value))
			product_qty = row[1].value
			price_unit = row[2].value
			product_id = self.env['product.product'].search([('default_code','=',default_code)], limit=1)
			if product_id:
				order_obj = self.order_line.filtered(lambda r: r.product_id == product_id)
				if order_obj:
					order_obj.write({
						'price_unit': price_unit,
						'price_unit_without_discount': price_unit, 
						'product_qty': product_qty
					})
				else:
					line_obj.create({
						'order_id': self.id,
						'name': product_id.name_get()[0][1],
						'product_id': product_id.id,
						'product_uom': product_id.uom_po_id.id,
						'product_qty': product_qty,
						'price_unit_without_discount': price_unit,
						'price_unit': price_unit,
						'date_planned': self.date_order
					})
			else:
				raise UserError(default_code+' кодтой бараа олдсонгүй!!!')