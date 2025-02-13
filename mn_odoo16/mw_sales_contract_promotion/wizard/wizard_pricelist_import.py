# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import time
from datetime import datetime, timedelta
from odoo.exceptions import UserError
from tempfile import NamedTemporaryFile
import base64
import xlrd

import logging
_logger = logging.getLogger(__name__)

class PriceListImportFromExcel(models.TransientModel):
	_name = 'pricelist.import.from.excel'
	_description = "pricelist import from excel"
	# Columns
	name = fields.Char(u'Name', required=True,)
	excel_data = fields.Binary(string='Excel file', required=True)

	def import_from_excel(self):
		_logger.info(u'-***********--import_from_excel--*************--')

		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		book = xlrd.open_workbook(fileobj.name)
		try :
			 sheet = book.sheet_by_index(0)
		except:
			 raise UserError(u'Warning', u'Wrong Sheet number.')
		# ДАТА унших
		temp_datas = {}
		nrows = sheet.nrows
		ncols = sheet.ncols
		_logger.info(u'-***********--rows, cols--************* %d %d ', nrows, ncols)
		for c in range(2, ncols):
			print('===COL repeat==')
			col = sheet.col(c)
			# Харилцагчийн дугаар авах, олох
			partner_name = col[0].value
			if isinstance(partner_name, float):
				if (partner_name - int(partner_name)) == 0:
					partner_name = int(partner_name)
			partner = self.env['res.partner'].search([('name','=',partner_name)], limit=1)
			# if not partner:
			# 	continue
			# 	# raise UserError(u'%s кодтой харилцагч олдсонгүй!' % str(partner_name))
			_logger.info(u'-***********--partner--************* %s ' % str(partner_name))
			if partner:
				temp_datas[partner.id] = {}
			else:
				temp_datas[partner_name] = {}
			# ====
			for r in range(1, nrows):
				row = sheet.row(r)
				# Тоо хэмжээг авах
				qty = row[c].value or 0
				if int(qty) > 0:
					# Тоо байвал барааг олох
					search_value = ""
					product = False
					if row[0].value:
						search_value = row[0].value
						if isinstance(search_value, float):
							if (search_value - int(search_value)) == 0:
								search_value = int(search_value)
						product = self.env['product.product'].search([('default_code','=',search_value)], limit=1)
					elif row[1].value:
						search_value = row[1].value
						if isinstance(search_value, float):
							if (search_value - int(search_value)) == 0:
								search_value = int(search_value)
						product = self.env['product.product'].search([('barcode','=',search_value)], limit=1)
					_logger.info(u'-***********--search_value %s ***  %d' % (str(search_value), qty))
					# Line үүсгэх
					if product:
						if partner:
							temp_datas[partner.id][product.id] = qty
						else:
							temp_datas[partner_name][product.id] = qty
					else:
						continue
						# raise UserError(u'%s кодтой бараа олдсонгүй!' % str(default_code))
		# print ('===================', temp_datas)
		# ДАТА үүсгэх
		for key_p in temp_datas:
			partner = False
			if isinstance(key_p, int):
				partner = self.env['res.partner'].search([('id','=',key_p)], limit=1)
				if partner:
					ppl = self.env['product.pricelist'].create({'name': partner.display_name +': '+self.name, 'company_id': self.env.user.company_id.id})
					for p_id in temp_datas[key_p]:
						vals = {
							'pricelist_id': ppl.id,
							'name': 'import pid: %d' % p_id,
							'applied_on': '0_product_variant',
							'product_id': p_id,
							'compute_price': 'fixed',
							'fixed_price': temp_datas[key_p][p_id],
							'company_id': self.env.user.company_id.id
						}
						ppli = self.env['product.pricelist.item'].create(vals)
					partner.property_product_pricelist = ppl.id
			else:
				ppl = self.env['product.pricelist'].create({'name': str(key_p) +': '+self.name, 'company_id': self.env.user.company_id.id})
				for p_id in temp_datas[key_p]:
					vals = {
						'pricelist_id': ppl.id,
						'name': 'import pid: %d' % p_id,
						'applied_on': '0_product_variant',
						'product_id': p_id,
						'compute_price': 'fixed',
						'fixed_price': temp_datas[key_p][p_id],
						'company_id': self.env.user.company_id.id
					}
					ppli = self.env['product.pricelist.item'].create(vals)
		return True
