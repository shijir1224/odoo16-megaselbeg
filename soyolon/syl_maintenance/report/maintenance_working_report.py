from odoo import fields, models
import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
import base64

fmt = '%Y-%m-%d'


class MaintenanceWorkingReport(models.TransientModel):
	_name = "maintenance.working.report"
	_description = "Maintenance Working Report"
	branch_ids = fields.Many2many('res.branch', 'maintenance_working_report_reports_branch_rel', 'branch_id', string='Төсөл')
	date_start = fields.Date(string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'), required=True)
	date_end = fields.Date(string=u'Дуусах огноо', required=True)

	def export_report(self):
		if self.date_start and self.date_end:
			leads = self.env['maintenance.workorder'].search([('date','>=',self.date_start),('date','<=',self.date_end)])
			print('aaaaaaaaaaaaa',leads)
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Тоног төхөөрөмжийн зогсолтын тайлан'+str(self.date_start)+'-'+str(self.date_end)+'.xlsx'
			team_ids = leads.mapped('equipment_id')
			print('bbbbbbbbbbbbbbbbbbbb', team_ids, )
			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_text_wrap()
			header.set_font_size(9)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#5fa1a5')

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
			contest_center.set_font_size(12)
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
			row=0
			worksheet = workbook.add_worksheet(u'Тоног төхөөрөмжийн зогсолтын тайлан')
			worksheet.set_zoom(100)
			row = 0
			worksheet.merge_range(row,0,row+2,7, u'Тоног төхөөрөмжийн зогсолтын тайлан', contest_center)
			# TABLE HEADER
			
			row = 3
			worksheet.merge_range( row, 0, row, +1, u'Д/д', header)
			worksheet.write(row, +2, u'Хэсэг', header)
			worksheet.write(row, 3, u'Засвар хийгдэх тоног төхөөрөмж', header)
			worksheet.write(row, 4, u'Хийгдсэн ажил  ', header)
			worksheet.write(row, 5, u'Гүйцэтгэлийн  хувь', header)
			worksheet.write(row, 6, u'Зураг ', header)
			worksheet.write(row, 7, u'Нэмэлт тайлбар', header)
			
			

			# row = 2
			row = 4
			number = 1
			worksheet.set_column('A:A', 5)
			worksheet.set_column('B:B', 5)
			worksheet.set_column('C:C', 30)
			worksheet.set_column('D:D', 30)
			worksheet.set_column('E:E', 30)
			worksheet.set_column('F:F', 30)
			worksheet.set_column('G:G', 30)
			worksheet.set_column('H:H', 30)
			worksheet.set_column('I:I', 30)
			worksheet.set_column('J:J', 30)
			worksheet.set_column('K:K', 30)
			worksheet.set_column('L:L', 30)
			worksheet.set_column('M:M', 30)
			worksheet.set_column('N:N', 30)
			worksheet.set_column('O:O', 30)
			worksheet.set_column('P:P', 30)
			worksheet.set_column('Q:Q', 30)
			for eqp in team_ids:
				eqps = leads.filtered(lambda r: r.equipment_id.id == eqp.id)
				first_row = row
				for item in eqps:
					rate = ''
					if item.workorder_rate == '5':
						rate = '100%'
					elif item.workorder_rate == '4':
						rate = '80%'
					elif item.workorder_rate == '3':
						rate = '60%'
					elif item.workorder_rate == '2':
						rate = '40%'
					elif item.workorder_rate == '1':
						rate = '20%'
					elif item.workorder_rate == '0':
						rate = '0%'
					worksheet.write(row, 0, number, contest_center)
					# worksheet.write(row, 1, item..strftime(fmt), contest_center)
					worksheet.write(row, 3, item.equipment_id.name if item.equipment_id else ' ', contest_center)
					worksheet.write(row, 4, item.performance_description, contest_center)
					worksheet.write(row, 5, rate, contest_center)
					for itemz in item.attachment_ids.filtered(lambda r: 'image' in r.mimetype ):
						base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
						image_url = base_url+'/web/content/'+str(itemz.id)+"?download=true"
						_logger.info("%s %s %s" % (itemz.name, itemz.mimetype, image_url) )
						image_data = BytesIO(urllib2.urlopen(image_url).read())
						worksheet.insert_image(row, col, image_url, {'image_data': image_data, 'x_scale': 0.5, 'y_scale': 0.5})
						worksheet.set_column(row, col, 40)
						col += 1
					# worksheet.merge_range(1, 3, 1, col, u'Зураг', header_wrap)
					worksheet.write(row, 7, ' ', contest_center)
					row += 1
					number += 1
				end_row = row
				worksheet.merge_range(first_row, 3, end_row-1, 3, eqp.name if eqp else '', contest_center)
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			# row = 8
			# worksheet.merge_range( row, 0, row, 7, u'Төлөвлөгөө боловсруулах:', header)
			# worksheet.merge_range(row+2, 0, row+2, 2, u' Технологи инженер:', header)
			# worksheet.write(row+2, 3, u' ', header)
			# worksheet.write(row+2, 4, u' Механик инженер:', header)
			# worksheet.write(row+2, 6, u' ', header)
			# worksheet.merge_range(row+4, 0, row+4, 2, u'Төслийн нэгжийн  ерөнхий менежер:', header)
			# worksheet.write(row+4, 4, u'Технологич инженер:', header)
			# worksheet.merge_range(row+6, 0, row+6, 2, u'Цахилгааны инженер:', header)
			# worksheet.write(row+6, 3, u' ', header)
			# worksheet.merge_range(row+8, 0, row+8, 2, u'Төлөвлөлтийн инженер:', header)
			# worksheet.write(row+8, 3, u' ', header)
			# worksheet.write(row+8, 4, u' Ашиглалтын геологи:', header)
			# worksheet.write(row+8, 3, u' ', header)
			# worksheet.merge_range( row+10, 0, row, 7, u'Төлөвлөгөө хянасан:', header)
			# worksheet.merge_range(row+12, 0, row+2, 2, u'Төслийн нэгжийн  ерөнхий менежер:', header)
			# worksheet.write(row+12, 3, u' ', header)


			return {
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				'target': 'new',
			}
		else:
			raise UserError('Бичлэг олдсонгүй!')