# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardPartWaitingMove(models.TransientModel):
	_name = "wizard.part.waiting.move"  
	_description = "wizard.part.waiting.move"  

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)

	technic_id = fields.Many2one('technic.equipment', string='Техник',)

	def waiting_export_report(self):
		domains = [('state','=','confirmed'),
				 ('date_end','>=',self.date_start),
				 ('date_end','<=',self.date_end)]
		if self.technic_id:
			domains.append(('technic_id','=',self.technic_id.id))
		lines = self.env['maintenance.parts.waiting'].sudo().search(domains, order='date_start')
		if lines:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)

			file_name = 'Part waiting report.xlsx'

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

			header_date = workbook.add_format({'bold': 1})
			header_date.set_text_wrap()
			header_date.set_font_size(8)
			header_date.set_align('center')
			header_date.set_align('vcenter')
			header_date.set_border(style=1)
			header_date.set_bg_color('#6495ED')

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

			contest_left0 = workbook.add_format()
			contest_left0.set_font_size(9)
			contest_left0.set_align('left')
			contest_left0.set_align('vcenter')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			# Colors
			cell_stopped = workbook.add_format()
			cell_stopped.set_bg_color('#F7574D')

			cell_working = workbook.add_format()
			cell_working.set_bg_color('#65B9FA')

			# Борлуулагчаар харуулах sheet
			worksheet = workbook.add_worksheet(u'Тайлан')
			worksheet.write(0,3, u"Part waiting report", h1)
			worksheet.write(1,0, u"Тайлант хугацаа: " + datetime.strftime(self.date_start, '%Y-%m-%d') +" ~ "+ datetime.strftime(self.date_end, '%Y-%m-%d'), contest_left0)

			# TABLE HEADER
			row = 2
			worksheet.set_row(row, 26)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column('A:A', 5)
			worksheet.write(row, 1, u"TYPE", header_wrap)
			worksheet.set_column('B:B', 12)
			worksheet.write(row, 2, u"Парк №", header_wrap)
			worksheet.set_column('C:C', 18)
			worksheet.write(row, 3, u"Техникийн нэр", header_wrap)
			worksheet.set_column('D:D', 20)
			# Сарын өдрүүд зурах
			col = 4
			col_dict = {}
			# GET dates
			query_dates = """
				SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
			""" % (self.date_start, self.date_end)
			self.env.cr.execute(query_dates)
			dates_result = self.env.cr.dictfetchall()
			for ll in dates_result:
				worksheet.write(row, col, ll['dddd'].strftime("%Y-%m-%d"), header_date)
				col_dict[ll['dddd']] = col
				col += 1
			worksheet.set_column(4, col-1, 6)
			worksheet.freeze_panes(3, 4)
			worksheet.set_zoom(80)
			row += 1

			# Data
			number = 1
			for line in lines:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.technic_id.technic_type, contest_center)
				worksheet.write(row, 2, line.technic_id.program_code or '-', contest_left)
				worksheet.write(row, 3, line.technic_id.park_number, contest_left)
				# ================
				query_dates = """
					SELECT generate_series('%s', '%s', '1 day'::interval)::date as dddd
				""" % (line.date_start, line.date_end)
				self.env.cr.execute(query_dates)
				dates_result = self.env.cr.dictfetchall()
				for ll in dates_result:
					if ll['dddd'] in col_dict:
						cc = col_dict[ ll['dddd'] ]
						tmp_style = cell_working
						if line.technic_status == 'stopped':
							tmp_style = cell_stopped
						worksheet.write_comment(row, cc, line.name)
						worksheet.write(row, cc, '', tmp_style)
				# =================
				row += 1
				number += 1

			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!')) 

	def move_export_report(self):
		domains = [('parent_id.state','=','confirmed'),
				 ('parent_id.date_required','>=',self.date_start),
				 ('parent_id.date_required','<=',self.date_end)]
		if self.technic_id:
			domains.append(('parent_id.from_technic_id','=',self.technic_id.id))
		lines = self.env['maintenance.parts.move.line'].sudo().search(domains)
		if lines:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)

			file_name = 'Part moving report.xlsx'

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

			header_date = workbook.add_format({'bold': 1})
			header_date.set_text_wrap()
			header_date.set_font_size(8)
			header_date.set_align('center')
			header_date.set_align('vcenter')
			header_date.set_border(style=1)
			header_date.set_bg_color('#6495ED')

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

			contest_left0 = workbook.add_format()
			contest_left0.set_font_size(9)
			contest_left0.set_align('left')
			contest_left0.set_align('vcenter')

			contest_right = workbook.add_format()
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


			# харуулах sheet
			worksheet = workbook.add_worksheet(u'Тайлан')
			worksheet.write(0,3, u"Part moving report", h1)
			worksheet.write(1,0, u"Тайлант хугацаа: " + datetime.strftime(self.date_start, '%Y-%m-%d') +" ~ "+ datetime.strftime(self.date_end, '%Y-%m-%d'), contest_left0)

			# TABLE HEADER
			row = 2
			worksheet.set_row(row, 26)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column('A:A', 5)
			worksheet.write(row, 1, u"Сэлбэгийн нэр", header_wrap)
			worksheet.set_column('B:B', 30)
			worksheet.write(row, 2, u"Сэлбэгийн сериал", header_wrap)
			worksheet.set_column('C:C', 15)
			worksheet.write(row, 3, u"Тоо ширхэг", header_wrap)
			worksheet.set_column('D:D', 9)
			worksheet.write(row, 4, u"Хэмжих нэгж", header_wrap)
			worksheet.set_column('E:E', 8)
			worksheet.write(row, 5, u"Шилжүүлсэн огноо", header_wrap)
			worksheet.set_column('F:F', 15)
			worksheet.write(row, 6, u"Шилжүүлэн авах техник", header_wrap)
			worksheet.set_column('G:G', 28)
			worksheet.write(row, 7, u"Шилжүүлэн тавих техник", header_wrap)
			worksheet.set_column('H:H', 28)
			worksheet.write(row, 8, u"Албан тушаал", header_wrap)
			worksheet.set_column('I:I', 15)
			worksheet.write(row, 9, u"Овог нэр", header_wrap)
			worksheet.set_column('J:J', 20)
			worksheet.write(row, 10, u"Тайлбар", header_wrap)
			worksheet.set_column('K:K', 50)

			worksheet.freeze_panes(3, 4)
			worksheet.set_zoom(80)
			row += 1

			# Data
			number = 1
			for line in lines:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.product_id.name, contest_left)
				worksheet.write(row, 2, line.product_id.default_code, contest_left)
				worksheet.write(row, 3, line.qty, contest_right)
				worksheet.write(row, 4, line.uom_id.name or '', contest_center)
				worksheet.write(row, 5, line.parent_id.date_required.strftime('%Y-%m-%d'), contest_center)
				worksheet.write(row, 6, line.parent_id.from_technic_id.display_name or '-', contest_left)
				worksheet.write(row, 7, line.parent_id.to_technic_id.display_name or '-', contest_left)
				worksheet.write(row, 8, line.parent_id.repairman_id.job_id.display_name or '-', contest_left)
				worksheet.write(row, 9, line.parent_id.repairman_id.display_name or '-', contest_left)
				worksheet.write(row, 10, line.parent_id.description, contest_left)
				# ================
				row += 1
				number += 1

			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!')) 
	
	# UB явуулсан сэлбэгийн тайлан
	def move_ub_export_report(self):
		lines = self.env['spare.parts.travel'].sudo().search(
			[('state','!=','draft'),
				 ('date_required','>=', datetime.strftime(self.date_start, '%Y-%m-%d')),
				 ('date_required','<=', datetime.strftime(self.date_end, '%Y-%m-%d')),
			], order='date_required')
		if lines:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)

			file_name = 'UB Part report.xlsx'

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

			contest_right = workbook.add_format()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)

			header_date = workbook.add_format({'bold': 1})
			header_date.set_text_wrap()
			header_date.set_font_size(8)
			header_date.set_align('center')
			header_date.set_align('vcenter')
			header_date.set_border(style=1)
			header_date.set_bg_color('#6495ED')

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

			contest_left0 = workbook.add_format()
			contest_left0.set_font_size(9)
			contest_left0.set_align('left')
			contest_left0.set_align('vcenter')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			# Colors
			cell_stopped = workbook.add_format()
			cell_stopped.set_bg_color('#F7574D')

			cell_working = workbook.add_format()
			cell_working.set_bg_color('#65B9FA')

			worksheet = workbook.add_worksheet(u'Тайлан')
			worksheet.write(0,3, u"UB part report", h1)
			worksheet.write(1,0, u"Тайлант хугацаа: " + datetime.strftime(self.date_start, '') +" ~ "+ datetime.strftime(self.date_end, '%Y-%m-%d'), contest_left0)

			# TABLE HEADER
			row = 2
			worksheet.set_row(row, 26)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column('A:A', 5)
			worksheet.write(row, 1, u"Нэр", header_wrap)
			worksheet.set_column('B:B', 28)
			worksheet.write(row, 2, u"Парк дугаар", header_wrap)
			worksheet.set_column('C:C', 14)
			worksheet.write(row, 3, u"Код", header_wrap)
			worksheet.set_column('D:D', 12)
			worksheet.write(row, 4, u"Тоо ширхэг", header_wrap)
			worksheet.set_column('E:E', 10)
			worksheet.write(row, 5, u"Бүрэн бүтэн байдал", header_wrap)
			worksheet.set_column('F:F', 20)
			worksheet.write(row, 6, u"Буцаах болсон шалтгаан", header_wrap)
			worksheet.set_column('G:G', 50)
			worksheet.write(row, 7, u"Хүлээлгэн өгсөн ажилтан", header_wrap)
			worksheet.set_column('H:H', 25)
			worksheet.write(row, 8, u"Албан тушаал", header_wrap)
			worksheet.set_column('I:I', 20)
			worksheet.write(row, 9, u"Явуулсан он сар", header_wrap)
			worksheet.set_column('J:J', 12)
			worksheet.write(row, 10, u"Тайлбар", header_wrap)
			worksheet.set_column('K:K', 50)
			worksheet.write(row, 11, u"Ирсэн огноо", header_wrap)
			worksheet.set_column('L:L', 16)
			worksheet.write(row, 12, u"Төлөв", header_wrap)
			worksheet.set_column('M:M', 12)

			worksheet.freeze_panes(3, 4)
			worksheet.set_zoom(80)
			row += 1

			# Data
			number = 1
			for line in lines:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.name, contest_left)
				worksheet.write(row, 2, line.technic_id.park_number or '-', contest_center)
				worksheet.write(row, 3, line.code, contest_center)
				worksheet.write(row, 4, line.qty, contest_right)
				worksheet.write(row, 5, line.spare_type, contest_center)
				worksheet.write(row, 6, line.back_description, contest_left)
				worksheet.write(row, 7, line.ref_user_id.display_name, contest_left)
				worksheet.write(row, 8, "", contest_left)
				worksheet.write(row, 9, line.date_required, contest_center)
				worksheet.write(row, 10, line.description or '', contest_left)
				worksheet.write(row, 11, line.date_required, contest_center)
				worksheet.write(row, 12, line.state, contest_center)
				row += 1
				number += 1

			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))	
