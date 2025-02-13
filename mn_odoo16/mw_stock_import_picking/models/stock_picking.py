# -*- coding: utf-8 -*-
from odoo import fields, models, _
import base64
import xlsxwriter
from io import BytesIO
from tempfile import NamedTemporaryFile
import os
import xlrd
from odoo.exceptions import UserError
from odoo.osv.osv import osv

class stock_picking(models.Model):
	_inherit = "stock.picking"

	import_data_ids = fields.Many2many('ir.attachment', 'stock_picking_product_attach_import_data_rel', 'picking_id',
									   'attachment_id', 'Бараа импортлох эксел', copy=False)
	is_barcode_reader = fields.Boolean('Offline Баркод уншигчаар', default=False, copy=False)
	is_barcode_with_loc_reader = fields.Boolean('Байрлалтай хамт', default=False, copy=False)

	def get_value_text(self, value):
		if isinstance(value, float) or isinstance(value, int):
			if value == 0:
				return False
			return str(value)
		value = value.encode("utf-8")
		value = value.decode('utf-8')
		return value

	def get_loc_name(self, loc_name):
		loc_id = self.env['stock.location'].search([('name', '=', loc_name)], limit=1)
		if not loc_id:
			loc_id = self.env['stock.location'].search([('complete_name', 'ilike', loc_name)], limit=1)
		return loc_id

	def get_pro_id(self, barcode):
		product_id = self.env['product.product'].search(
			['|', '|', ('barcode', '=', barcode), ('default_code', '=', barcode), ('name', '=', barcode)], limit=1)
		if not product_id:
			raise UserError('%s Бараа олдсонгүй' % barcode)
		return product_id

	def action_import_picking_update(self, barcode, product_qty, location_id_name, location_dest_id_name,
									 lot_name=False):
		if isinstance(barcode, float):
			barcode = int(barcode)
		else:
			barcode = barcode
		# lot_obj = self.env['stock.production.lot']
		product_id = self.get_pro_id(barcode)
		loc_id = False
		loc_dest_id = False
		lot_id = False
		if self.picking_type_code == 'internal':
			loc_id = self.get_loc_name(location_id_name)
			if not loc_id:
				raise UserError(u'%s Гарах Байрлал олдсонгүй' % location_id_name)
			loc_dest_id = self.get_loc_name(location_dest_id_name)
			if not loc_dest_id:
				raise UserError(u'%s Хүрэх Байрлал олдсонгүй' % location_dest_id_name)
		elif self.picking_type_code == 'incoming':
			loc_dest_id = self.get_loc_name(location_dest_id_name)
			if not loc_dest_id:
				raise UserError(u'%s Хүрэх Байрлал олдсонгүй' % location_dest_id_name)
		elif self.picking_type_code == 'outgoing':
			loc_id = self.get_loc_name(location_id_name)
			# loc_dest_id = self.location_dest_id
			if not loc_id:
				raise UserError(u'%s Гарах Байрлал олдсонгүй' % location_id_name)
		if self.has_tracking and self.picking_type_code in ['incoming', 'outgoing'] and product_id.tracking in ['lot',
																												'serial']:
			if not lot_name:
				raise UserError(u'%s Нэртэй бараа лот/сериалгүй байна' % product_id.display_name)
			# lot_id = lot_obj.search([('name', '=', lot_name), ('product_id', '=', product_id.id)], limit=1)
			if not lot_id and product_id:
				raise UserError(u'%s Нэртэй лот/сериал олдсонгүй %s' % (lot_name, product_id.display_name))
		is_stock_move_ok = True
		self.create_s_line(product_id, product_qty, loc_id, loc_dest_id, lot_id, is_stock_move_ok)

	def create_s_line(self, product_id, product_qty, loc_id, loc_dest_id, lot_id, is_stock_move_ok):
		if is_stock_move_ok:
			if self.picking_type_code != 'internal':
				raise UserError('%s Бараа шинээр үүсгэж болохгүй зөвхөн дотоод хөдөлгөөн дээр импорт хийнэ' % (
					product_id.display_name))
			line_obj = self.env['stock.move']
			line_obj.create({
				'name': product_id.display_name + ' import line',
				'picking_id': self.id,
				'product_id': product_id.id,
				'product_uom': product_id.uom_id.id,
				'product_uom_qty': product_qty,
				# 'product_qty': product_qty,
				'location_id': loc_id.id or self.location_id.id,
				'location_dest_id': loc_dest_id.id or self.location_dest_id.id,
				'state': self.state
			})
		else:
			if lot_id:
				line_obj = self.env['stock.move.line']
				line_obj.create({
					# 'name': product_id.display_name+' import line',
					'picking_id': self.id,
					'product_id': product_id.id,
					'product_uom_id': product_id.uom_id.id,
					'reserved_uom_qty': product_qty,
					'location_id': loc_id.id or self.location_id.id,
					'location_dest_id': loc_dest_id.id or self.location_dest_id.id,
					'lot_id': lot_id.id
				})

	def action_import_product(self):
		if not self.import_data_ids:
			raise UserError('Оруулах эксэлээ UPLOAD хийнэ үү ')

		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.import_data_ids[0].datas))
		fileobj.seek(0)
		if self.is_barcode_reader:
			myreader = fileobj.read().splitlines()
			for row in myreader:
				row_data = row.split(',')
				off_location_name = False
				from_loc_name = False
				dest_loc_name = False
				if self.is_barcode_with_loc_reader:
					off_location_name = self.get_value_text(row_data[0])
					barcode = self.get_value_text(row_data[1])
					qty = row_data[2]
				else:
					barcode = self.get_value_text(row_data[0])
					qty = self.get_value_text(row_data[1])
				if self.picking_type_code == 'internal':
					from_loc_name = self.location_id.name
					dest_loc_name = off_location_name or self.location_dest_id.name
				elif self.picking_type_code == 'incoming':
					dest_loc_name = off_location_name or self.location_dest_id.name
				elif self.picking_type_code == 'outgoing':
					from_loc_name = off_location_name or self.location_id.name
				self.action_import_picking_update(barcode, qty, from_loc_name, dest_loc_name)
		else:
			if not os.path.isfile(fileobj.name):
				raise osv.except_osv(_('Error'), _('Reading file error.\nChecking for excel file!'))
			book = xlrd.open_workbook(fileobj.name)
			try:
				sheet = book.sheet_by_index(0)
			except:
				raise osv.except_osv(_('Error'), _("Sheet's number error"))
			nrows = sheet.nrows
			rowi = 1
			for item in range(rowi, nrows):
				row = sheet.row(item)
				barcode = row[0].value
				product_qty = row[1].value
				from_loc_name = False
				dest_loc_name = False
				lot_name = False
				barcode = self.get_value_text(barcode)
				if self.picking_type_code == 'internal':
					from_loc_name = self.get_value_text(row[2].value)
					dest_loc_name = self.get_value_text(row[3].value)
				elif self.picking_type_code == 'incoming':
					dest_loc_name = self.get_value_text(row[2].value)
				elif self.picking_type_code == 'outgoing':
					from_loc_name = self.get_value_text(row[2].value)
				if self.has_tracking and self.picking_type_code in ['incoming', 'outgoing']:
					lot_name = self.get_value_text(row[3].value)
				# print(barcode, row[2].value, row[3].value,from_loc_name,dest_loc_name)
				self.action_import_picking_update(barcode, product_qty, from_loc_name, dest_loc_name, lot_name)

	def action_export_product(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(u'Импортлох темплати')

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(9)
		h1.set_align('center')
		h1.set_font_name('Arial')

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
		# header_wrap.set_fg_color('#6495ED')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_right = workbook.add_format()
		contest_right.set_text_wrap()
		contest_right.set_font_size(9)
		contest_right.set_align('right')
		contest_right.set_align('vcenter')
		contest_right.set_border(style=1)
		contest_right.set_num_format('#,##0.00')

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
			'font_size': 9,
			'font_name': 'Arial',
			# 'text_wrap':1,
			'num_format': '#,####0'
		})

		row = 0
		# last_col = 3
		# worksheet.merge_range(row, 0, row, last_col, u'"'+self.name+'"'+u' Бараа импортолох загвар', header_wrap)

		worksheet.write(row, 0, u"Барааны код", header)
		worksheet.write(row, 1, u"Тоо хэмжээ", header)
		if self.picking_type_code == 'internal':
			worksheet.write(row, 2, u"Гарах байрлал", header)
			worksheet.write(row, 3, u"Хүрэх байрлал", header)
		elif self.picking_type_code == 'incoming':
			worksheet.write(row, 2, u"Хүрэх байрлал", header)
		elif self.picking_type_code == 'outgoing':
			worksheet.write(row, 2, u"Гарах байрлал", header)
		if self.has_tracking and self.picking_type_code in ['incoming', 'outgoing']:
			worksheet.write(row, 4, u"Цуврал/Сериал", header)
		for item in self.move_line_ids:
			row += 1
			p_code = item.product_id.default_code or item.product_id.barcode or ''
			l_id = item.location_id.name or ''
			l_dest_id = item.location_dest_id.name or ''
			worksheet.write(row, 0, p_code, cell_format2)
			worksheet.write(row, 1, item.qty_done, cell_format2)
			if self.picking_type_code == 'internal':
				worksheet.write(row, 2, l_id, cell_format2)
				worksheet.write(row, 3, l_dest_id, cell_format2)
			elif self.picking_type_code == 'incoming':
				worksheet.write(row, 2, l_dest_id, cell_format2)
			elif self.picking_type_code == 'outgoing':
				worksheet.write(row, 2, l_id, cell_format2)
			if self.has_tracking and self.picking_type_code in ['incoming', 'outgoing']:
				worksheet.write(row, 2, l_id, cell_format2)

		worksheet.set_column('A:A', 25)
		worksheet.set_column('B:B', 20)
		worksheet.set_column('C:D', 30)

		workbook.close()

		out = base64.encodebytes(output.getvalue())
		file_name = self.name + '.xlsx'
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=" + str(
				excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
			'target': 'new',
		}
