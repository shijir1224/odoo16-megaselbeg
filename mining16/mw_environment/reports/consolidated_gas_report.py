from odoo import fields, models
import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
import base64

fmt = '%Y-%m-%d'

class ConsolidatedGasReport(models.TransientModel):
	_name = "consolidated.gas.report"
	_description = "Consolidated Gas Report"

	mining_location_ids = fields.Many2many('env.mining', string='Үйлдвэр, Уурхай', domain="[('is_active','=', 'active')]")
	start_date = fields.Date(string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'), required=True)
	end_date = fields.Date(string=u'Дуусах огноо', required=True)

	def export_report(self):
		if self.start_date and self.end_date:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Хүлэмжийн хий тайлан '+str(self.start_date)+'-'+str(self.end_date)+'.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_text_wrap()
			header.set_font_size(9)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#fff2cc')
 
			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#99ccff')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

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

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sub_total_90 = workbook.add_format({'bold': 1})
			sub_total_90.set_text_wrap()
			sub_total_90.set_font_size(9)
			sub_total_90.set_align('center')
			sub_total_90.set_align('vcenter')
			sub_total_90.set_border(style=1)
			sub_total_90.set_bg_color('#F7EE5E')
			sub_total_90.set_rotation(90)
			
			worksheet = workbook.add_worksheet(u'SCOPE-1')
			worksheet.set_zoom(100)
			row = 0
			worksheet.merge_range(row,0, row,4, u'SCOPE 1', contest_center)

			scope_1 = self.env['env.technic'].search([('date','>=',self.start_date),('date','<=',self.end_date),('mining_location','in',self.mining_location_ids.ids),('state','=','done')])
			scope_2 = self.env['env.tseh'].search([('date','>=',self.start_date),('date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)])
			scope_3 = self.env['env.contract.shipping'].search([('date','>=',self.start_date),('date','<=',self.end_date),('state','=','done'),('mining_location','in',self.mining_location_ids.ids)])

			
			# TABLE HEADER
			row = 1
			worksheet.set_row(0, 28)	
			worksheet.write(row, 0, u'№', header)
			worksheet.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet.write(row, 2, u'CO2', header)
			worksheet.write(row, 3, u'CH4', header)
			worksheet.write(row, 4, u'NO2', header)

			kk = 2
			number = 1
			worksheet.set_column('A:A', 5)
			worksheet.set_column('B:B', 20)
			worksheet.set_column('C:C', 20)
			worksheet.set_column('D:D', 20)
			worksheet.set_column('E:E', 20)

			# DATA зурах
			if scope_1:
				for item in scope_1:
					worksheet.write(kk, 0, number, contest_center)
					worksheet.write(kk, 1, item.mining_location.name if item.mining_location else ' ', contest_center)
					worksheet.write(kk, 2, item.co2e_co2 if item.co2e_co2 else 0, contest_center)
					worksheet.write(kk, 3, item.co2e_ch4 if item.co2e_ch4 else 0, contest_center)
					worksheet.write(kk, 4, item.co2e_n20 if item.co2e_n20 else 0, contest_center)
				
					kk += 1
					number += 1
		
			worksheet2 = workbook.add_worksheet(u'SCOPE-2')
			worksheet2.set_zoom(100)
			row = 0
			worksheet2.merge_range(row,0, row,4, u'SCOPE 2', contest_center)
		
			# TABLE HEADER
			row = 1
			worksheet2.set_row(0, 28)	
			worksheet2.write(row, 0, u'№', header)
			worksheet2.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet2.write(row, 2, u'CO2', header)
			worksheet2.write(row, 3, u'CH4', header)
			worksheet2.write(row, 4, u'NO2', header)

			kk = 2
			number = 1
			worksheet2.set_column('A:A', 5)
			worksheet2.set_column('B:B', 20)
			worksheet2.set_column('C:C', 20)
			worksheet2.set_column('D:D', 20)
			worksheet2.set_column('E:E', 20)

			# DATA зурах
			if scope_2:
				for item in scope_2:
					worksheet2.write(kk, 0, number, contest_center)
					worksheet2.write(kk, 1, item.mining_location.name if item.mining_location else ' ', contest_center)
					worksheet2.write(kk, 2, item.co2e_co2 if item.co2e_co2 else 0, contest_center)
					worksheet2.write(kk, 3, item.co2e_ch4 if item.co2e_ch4 else 0, contest_center)
					worksheet2.write(kk, 4, item.co2e_n20 if item.co2e_n20 else 0, contest_center)
				
					kk += 1
					number += 1


			worksheet3 = workbook.add_worksheet(u'SCOPE-3')
			worksheet3.set_zoom(100)
			row = 0
			worksheet3.merge_range(row,0, row,4, u'SCOPE 3', contest_center)
		
			# TABLE HEADER
			row = 1
			worksheet3.set_row(0, 28)	
			worksheet3.write(row, 0, u'№', header)
			worksheet3.write(row, 1, u'Үйлдвэр, уурхай', header)
			worksheet3.write(row, 2, u'CO2', header)
			worksheet3.write(row, 3, u'CH4', header)
			worksheet3.write(row, 4, u'NO2', header)

			kk = 2
			number = 1
			worksheet3.set_column('A:A', 5)
			worksheet3.set_column('B:B', 20)
			worksheet3.set_column('C:C', 20)
			worksheet3.set_column('D:D', 20)
			worksheet3.set_column('E:E', 20)

			# DATA зурах
			if scope_3:
				for item in scope_3:
					worksheet3.write(kk, 0, number, contest_center)
					worksheet3.write(kk, 1, item.mining_location.name if item.mining_location else ' ', contest_center)
					worksheet3.write(kk, 2, item.co2e_co2 if item.co2e_co2 else 0, contest_center)
					worksheet3.write(kk, 3, item.co2e_ch4 if item.co2e_ch4 else 0, contest_center)
					worksheet3.write(kk, 4, item.co2e_n20 if item.co2e_n20 else 0, contest_center)
				
					kk += 1
					number += 1
			
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				'target': 'new',
			}
		else:
			raise UserError(u'Бичлэг олдсонгүй!')