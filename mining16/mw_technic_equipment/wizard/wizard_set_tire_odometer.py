# -*- coding: utf-8 -*-

from odoo import api, models, fields
import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class WizardSetTireOdometer(models.TransientModel):
	_name = "wizard.set.tire.odometer"
	_description = "wizard set tire odometer"

	excel_data = fields.Binary(u'Excel file', required=True,)
	file_name = fields.Char('File name')
	
	def import_data(self):
		# File нээх
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(_(u'Importing error.\nCheck excel file!'))
		
		book = xlrd.open_workbook(fileobj.name)
		try :
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(_(u'Wrong Sheet number!'))
		
		# Унших
		nrows = sheet.nrows
		setting_lines = []
		for r in range(0,nrows):
			row = sheet.row(r)
			_logger.info("--tire serial ==%s ",str(row[0].value))
			if row[0].value and row[1].value and row[2].value:
				serial_number = str(row[0].value).split('.')[0]
				moto_h = row[1].value
				odometer_date = row[2].value
				_logger.info("--------tire data import ======%s %s %s %s %s",str(serial_number),str(moto_h), str(odometer_date), str(row[3].value), str(row[4].value))
				tire = self.env['technic.tire'].search([('serial_number','=',serial_number)], limit=1)
				if not tire:
					raise UserError(_(u'%s дугаартай Дугуй олдсонгүй!' % serial_number))
				vals = {
					'tire_id': tire.id,
					'date': odometer_date,
					'increasing_odometer': moto_h,
					'depreciation_percent': 0,
					'depreciation_amount': 0,
				}
				self.env['tire.depreciation.line'].create(vals)
				# Одоогийн хээний гүн SET хийх
				if row[3].value:
					tire.tread_current_deep = row[3].value
				if row[4].value:
					tire.tread_depreciation_percent = row[4].value
		return True