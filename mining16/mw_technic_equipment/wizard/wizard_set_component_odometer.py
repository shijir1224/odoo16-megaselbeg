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

class WizardSetComponentOdometer(models.TransientModel):
	_name = "wizard.set.component.odometer"
	_description = "wizard set component odometer"

	excel_data = fields.Binary(u'Excel file', required=True,)
	file_name = fields.Char('File name')
	
	def import_pm_data(self):
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
			_logger.info("---comp serial ==%s ",str(row[0].value))
			if row[0].value and row[1].value and row[2].value:
				serial_number = str(row[0].value).split('.')[0]
				moto_h = row[1].value
				odometer_date = row[2].value
				_logger.info("--------import ======%s %s %s ",str(serial_number),str(moto_h), str(odometer_date))
				component = self.env['technic.component.part'].search([('serial_number','=',serial_number)], limit=1)
				if not component:
					raise UserError(_(u'%s дугаартай компонент олдсонгүй!' % serial_number))
				vals = {
					'parent_id': component.id,
					'date': odometer_date,
					'increasing_odometer': moto_h,
					'depreciation_percent': 0,
				}
				self.env['component.depreciation.line'].create(vals)

				# Одоогийн техникийг SET хийх
				if row[3].value:
					program_code = row[3].value
					technic = self.env['technic.equipment'].search([('program_code','=',program_code)], limit=1)
					if technic:
						component.current_technic_id = technic.id
					else:
						raise UserError(_(u'%s program_code той техник олдсонгүй!' % program_code))
		return True