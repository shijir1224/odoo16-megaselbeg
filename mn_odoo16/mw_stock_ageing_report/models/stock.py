# -*- coding: utf-8 -*-
import base64
import os
from tempfile import NamedTemporaryFile
import xlrd
from odoo.exceptions import UserError
from pyxlsb import convert_date
from odoo import fields, models, _
import logging
_logger = logging.getLogger(__name__)

class product_product(models.Model):
	_inherit = 'product.product'

	date_ageing_first = fields.Date(u'Насжилт эхлэх огноо', copy=False)

class ProductAgeingOpeningData(models.Model):
	_name = 'product.ageing.opening'
	_description = 'Product ageing'

	stock_move_id = fields.Many2one('stock.move', string='Stock move')
	product_id = fields.Many2one('product.product', string='Product')
	date = fields.Date(string='Date', required=True)
	qty = fields.Float(string='Quantity')

class StockMove(models.Model):
	_inherit = 'stock.move'

	ageing_data_ok = fields.Boolean(default=False)
	ageing_lines = fields.One2many('product.ageing.opening', 'stock_move_id', string='Ageing lines')
	first_date = fields.Date(string='Насжилтын огноо')

class InheritStockPicking(models.Model):
	_inherit = 'stock.picking'

	def _action_done(self):
		"""Call `_action_done` on the `stock.move` of the `stock.picking` in `self`.
		This method makes sure every `stock.move.line` is linked to a `stock.move` by either
		linking them to an existing one or a newly created one.
		If the context key `cancel_backorder` is present, backorders won't be created.
		:return: True
		:rtype: bool
		"""
		self._check_company()
		todo_moves = self.move_ids.filtered(lambda self: self.state in ['draft', 'waiting', 'partially_available', 'assigned', 'confirmed'])
		for picking in self:
			if picking.owner_id:
				picking.move_ids.write({'restrict_partner_id': picking.owner_id.id})
				picking.move_line_ids.write({'owner_id': picking.owner_id.id})
			todo_moves._action_done(cancel_backorder=self.env.context.get('cancel_backorder'))
			self.write({'date_done': fields.Datetime.now(), 'priority': '0'})
			for line in self.move_ids_without_package:
				line.first_date = fields.Date.today()
			# if incoming/internal moves make other confirmed/partially_available moves available, assign them
			done_incoming_moves = self.filtered(lambda p: p.picking_type_id.code in ('incoming', 'internal')).move_ids.filtered(lambda m: m.state == 'done')
			done_incoming_moves._trigger_assign()

class ProductAgeingOpeningDataWizard(models.TransientModel):
	_name = 'product.ageing.opening.wizard'
	_description = 'Product ageing data wizard'

	import_data = fields.Binary(string='Файл', required=True)
	desc = fields.Text(default='#1. Агуулах байрлал нэр \n#2. Барааны код \n#3.  Тоо хэмжээ \n#4. Огноо', readonly=True)
	first_balance_date = fields.Date(string='Эхний үлдэгдэл оруулсан огноо', required=True)

	def import_data_file(self):
		"""
		Эксэл файлаас импортлох функц
		"""
		self.ensure_one()
		if not self.import_data:
			raise UserError(_('Please insert import data file'))
		fileobj = NamedTemporaryFile()
		fileobj.write(base64.decodebytes(self.import_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(_('Reading file error. Checking for excel file!'))
		book = xlrd.open_workbook(fileobj.name)
		try:
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(_("Sheet's number error"))
		not_created_codes = []
		not_created_location = []
		not_create_move = []
		message = ''
		success_data = []
		nrows = sheet.nrows
		rowi = 1
		while rowi < nrows:
		# for item in range(1, sheet.nrows):
			_logger.info('--- Product ageing rowi: %s' % (rowi))
			row = sheet.row(rowi)
			location_name = str(row[0].value)
			product_code = str(row[1].value)
			date_str = format(convert_date(row[3].value),'%Y-%m-%d')
			qty = float(row[2].value)
			product_id = self.env['product.product'].search(['|', ('default_code', '=', product_code), ('name', '=', product_code)], limit=1)
			if not product_id:
				raise UserError((u'%s бараа олдсонгүй.' % (product_code)))
				not_created_codes.append(product_code)
				# continue

			location = self.env['stock.location'].search([('name', '=', location_name)], limit=1)
			if not location:
				raise UserError((u'%s байрлал олдсонгүй.'%(location_name)))
				not_created_location.append(location)
				# break

			# split_date = str(self.first_balance_date).split("/")
			# print (split_date)
			# str_split_date = "%s-%s-%s"%(split_date[0],split_date[1],split_date[omni 2])
			# print ("str_split_date --", str_split_date)
			str_first_balance_date = str(self.first_balance_date)+ " 00:00:00"
			str_first_balance_date2 = str(self.first_balance_date) + " 23:59:59"
			first_move = self.env['stock.move'].search([('date', '>=', str_first_balance_date), ('date', '<=', str_first_balance_date2), ('product_id', '=', product_id.id), ('location_dest_id', '=', location.id)], limit=1)
			if first_move:
				# Бараан дээрх насжилтын огноог өөрчилөх
				first_move.first_date = date_str
				# 
				success_data.append([product_id.id, date_str, qty, first_move.id])
			else:
				raise UserError((u'%s - %s эхний үлдэгдэл хөдөлгөөн олдсонгүй.' % (product_code, location_name)))
				# aa = '%s - %s'%(product_code, location_name)
				not_create_move.append(aa)
				# break

			rowi += 1
		# print (not_create_move)
		# print (not_created_location)
		if not_create_move:
			message = 'Дараах байрлал, бараа нь дээр эхний үлдэгдэл хөдөлгөөн олдсонгүй: {0}'.format(str(not_create_move))

		if not_created_location:
			message = 'Дараах байрлал олдсонгүй: {0}'.format(str(not_created_location))

		if not_created_codes:
			message = 'Дараах кодуудын бараа олдсонгүй: {0}'.format(str(not_created_codes))
		else:
			message = 'Ямар ч асуудал гарсангүй. Та цонхыг гаргаж болно.'

		for c1 in success_data:
			_logger.info('--- Product ageing data: %s' % (c1))
			self.env['product.ageing.opening'].create({'product_id': c1[0],
													   'date': c1[1],
													   'qty': c1[2],
													   'stock_move_id': c1[3]})

		return {
			'type': 'ir.actions.client',
			'tag': 'display_notification',
			'params': {
				'title': _('Амжилттай!'),
				'message': message,
				'sticky': True,
			}
		}
