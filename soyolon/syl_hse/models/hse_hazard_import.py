# -*- coding: utf-8 -*-
from odoo import  api, fields, models, _
from datetime import datetime, timedelta
from io import BytesIO
from tempfile import NamedTemporaryFile
import base64
import xlsxwriter
import os,xlrd
from odoo.exceptions import UserError

class HseHazardReport(models.Model):
	_name = "hse.hazard.import"
	_description = 'Hazard import'

	excel_data = fields.Binary(string='Импорт файл')

	def date_value(self,dd):
		if dd:
			try:
				if type(dd)==float:
					serial = dd
					seconds = (serial - 25569) * 86400.0
					date=datetime.utcfromtimestamp(seconds)
					print ('date ',date)
				else:
					date = datetime.strptime(dd, '%Y-%m-%d')
			except ValueError:
				raise UserError(_('Date error %s row! \n \
				format must \'YYYY-mm-dd\'' % dd))
		else:
			date=''
		return date
	
	def get_field_value(self, f_id, f_value):
		if f_id.ttype=='date':
			if type(f_value) in [float, int]:
				f_value = (f_value - 25569) * 86400.0
				date_time = datetime.utcfromtimestamp(f_value)
				return str(date_time)
			else:
				return f_value
		elif f_id.ttype=='many2one':
			obj = self.env[f_id.relation]
			if type(f_value) in [float, int]:
				f_value = str(int(f_value))
			value_ids = obj.sudo()._name_search(f_value, operator='=',limit=100)
			if len(value_ids)>1:
				raise UserError('%s Талбарын утга %s 1-ээс олон ирээд байна'%(f_id.display_name, f_value))
			if value_ids:
				if not type(value_ids) == list:
					query = value_ids
					query_str, params = query.select("*")
					self._cr.execute(query_str, params)
					res = self._cr.fetchone()
					if res:
						value_ids = res
				return value_ids[0]
				# return value_ids[0][0]
			elif f_id.relation == 'res.partner':
				value_ids = obj.sudo().search([('vat','=',f_value)], limit=1)
				if not value_ids:
					raise UserError('%s талбарын %s регистр-тэй Харицлагч олдсонгүй'%(f_value,f_id.display_name))
				return value_ids.id
			else:
				return False
		elif f_id.ttype in ['char','text'] and type(f_value) in [float, int]:
			f_value = str(int(f_value))
			return f_value
		elif f_id.ttype == 'selection':
			if not f_id.selection_ids:
				raise UserError('%s Selection утга оруулаагүй байна',f_id.display_name)
			found_it = False
			if type(f_value) in [float, int]:
				f_value = str(int(f_value))
			for sel in f_id.selection_ids:
				if sel.value==f_value or sel.name==f_value:
					found_it = sel.value
					break
			if not found_it and f_value:
				raise UserError('%s ТАЛБАРЫН %s Selection field-ийн утга буруу байна олдсонгүй %s'%(f_id.display_name, f_value,', '.join(f_id.selection_ids.mapped('name'))))
			return found_it
		else:
			return f_value
		

	def hazard_from_import(self):
		line_pool =  self.env['hse.hazard.report']

		fileobj = NamedTemporaryFile('w+b')
		fileobj.write(base64.decodebytes(self.excel_data))
		fileobj.seek(0)
		if not os.path.isfile(fileobj.name):
			raise UserError(u'Aldaa')
		book = xlrd.open_workbook(fileobj.name)

		try :
			sheet = book.sheet_by_index(0)
		except:
			raise UserError(u'Aldaa')
		nrows = sheet.nrows

		for item in range(2,nrows):
			row = sheet.row(item)
			datetime= self.date_value(row[0].value)
			branch_id= self.env['res.branch'].search([('name','=',row[1].value)])
			hazard_type = row[2].value
			employee_id= self.env['hr.employee'].sudo().search([('name','ilike',row[3].value)])
			location_id= self.env['hse.location'].sudo().search([('name','ilike',row[4].value)])
			hazard_category_id= self.env['hse.hazard.category'].sudo().search([('name','=', row[5].value)])
			notify_emp_id= self.env['hr.employee'].sudo().search([('name','ilike', row[6].value)])
			hazard_identification = row[7].value	
			corrective_action_to_be_taken= row[8].value

			print('boldoo', hazard_category_id)

			line_id = line_pool.create({
				'datetime':datetime,
				'branch_id':branch_id.id,
				'hazard_type': hazard_type,
				'employee_id':employee_id.id,
				'location_id':location_id.id,
				'hazard_category_id':hazard_category_id.id,
				'notify_emp_id': notify_emp_id.id,
				'hazard_identification': hazard_identification,
				'corrective_action_to_be_taken':corrective_action_to_be_taken,
				# 'hazard_identification': 'aa',
				# 'corrective_action_to_be_taken':'bo',
			})
			if not line_id:
				raise UserError('Амжилтгүй')

	def hazart_export_template(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Аюулыг мэдээллэх.xlsx'
		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(12)
		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#6495ED')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(9)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)
		header_wrap.set_bg_color('#6495ED')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		# Борлуулагчаар харуулах sheet
		worksheet = workbook.add_worksheet(u'Темплати')
		worksheet.write(0,1, u"Темплати", h1)
		# TABLE HEADER
		row = 1
		worksheet.write(row, 0, u"Бүртгэсэн огноо", header_wrap)
		worksheet.write(row, 1, u"Салбар", header_wrap)
		worksheet.write(row, 2, u"Аюулын түвшин", header_wrap)
		worksheet.write(row, 3, u"Хариуцагч ", header_wrap)
		worksheet.write(row, 4, u"Байрлал", header_wrap)
		worksheet.write(row, 5, u"Аюулын ангилал", header_wrap)
		worksheet.write(row, 6, u"Үүсгэсэн ажилтан", header_wrap)
		worksheet.write(row, 7, u"АЮУЛЫН АГУУЛГА", header_wrap)
		worksheet.write(row, 8, u"АВСАН ШУУРХАЙ АРГА ХЭМЖЭЭ", header_wrap)
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
				'type' : 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				'target': 'new',
		}