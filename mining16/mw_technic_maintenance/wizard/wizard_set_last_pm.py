# -*- coding: utf-8 -*-

from odoo import api, models, fields
import xlrd, os
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
from io import BytesIO
from odoo.exceptions import UserError, ValidationError

import logging
_logger = logging.getLogger(__name__)

class WizardSetLastPM(models.TransientModel):
	_name = "wizard.set.last.pm"  
	_description = "wizard.set.last.pm"  

	excel_data = fields.Binary(u'Excel file', required=True,)
	file_name = fields.Char('File name')
	
	def import_pm_data(self):
		# File нээх
		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			 raise UserError(u'Importing error.\nCheck excel file!')
		
		book = xlrd.open_workbook(fileobj.name)
		try :
			 sheet = book.sheet_by_index(0)
		except:
			 raise UserError(u'Wrong Sheet number.')
		
		# Унших
		nrows = sheet.nrows
		setting_lines = []
		for r in range(1,nrows):
			row = sheet.row(r)
			_logger.info("---serial number ==%s %s",str(row[0].value),str(row[1].value))
			if (row[0].value or row[1].value) and row[2].value and (row[3].value or row[4].value):
				print(row[2].value)
				park_number = str(row[0].value)
				serial_number = str(row[1].value)
				pm_date = row[2].value
				moto_h = row[3].value
				km = row[4].value
				priority = row[5].value
				_logger.info("--------import ====== %s %s %s %s %s ",str(park_number), str(serial_number),str(pm_date), str(moto_h), str(priority))
				technic = False
				if park_number:
					technic = self.env['technic.equipment'].search([('park_number','=',park_number.strip())])
				elif serial_number:
					technic = self.env['technic.equipment'].search([('vin_number','=',serial_number.strip())])
				if technic:
					technic.last_pm_date = xlrd.xldate.xldate_as_datetime(row[2].value, book.datemode)
					technic.last_pm_odometer = moto_h if moto_h else km
					technic.last_pm_priority = priority
		return True