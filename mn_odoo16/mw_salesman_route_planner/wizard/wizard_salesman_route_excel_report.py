# -*- coding: utf-8 -*-

from odoo import _, tools
from odoo import api, fields, models
import time
from odoo.exceptions import UserError, ValidationError

import xlsxwriter
from io import BytesIO
import base64

class WizardSalesmanRouteExcelReport(models.TransientModel):
	_name = "wizard.salesman.route.excel.report"
	_description = "wizard salesman route excel report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	user_id = fields.Many2one('res.users', string=u'Salesman', required=True)
	
	def export_excel(self):
		if self.date_start <= self.date_end:
			context = dict(self._context)
			
			route_plan = self.env['salesman.route.planner'].search([
				('state','=','confirmed'),
				('salesman_id','=',self.user_id.id)], limit=1)
			if not route_plan:
				raise UserError(_('Not found Route Plan!'))

			# Excel дата бэлдэх
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)

			worksheet = workbook.add_worksheet(u'Salesman route report')
			file_name = 'Salesman route report.xlsx'

			h1 = workbook.add_format({'bold':1,'italic':1})
			h1.set_font_size(12)
			h1_1 = workbook.add_format({'bold': 1})
			h1_1.set_align('right')
			h1_1.set_font_size(12)

			header_wrap = workbook.add_format({'bold':1,'italic':1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#83a5e2')

			contest_right_ttl = workbook.add_format()
			contest_right_ttl.set_text_wrap()
			contest_right_ttl.set_font_size(9)
			contest_right_ttl.set_align('right')
			contest_right_ttl.set_align('vcenter')
			contest_right_ttl.set_num_format('#,##0.00')
			contest_right_ttl.set_bg_color('#83a5e2')

			contest_right = workbook.add_format({'italic':1})
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_number = workbook.add_format()
			contest_number.set_text_wrap()
			contest_number.set_font_size(9)
			contest_number.set_align('right')
			contest_number.set_align('vcenter')
			contest_number.set_border(style=1)

			contest_left = workbook.add_format({'italic':1})
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_right_per = workbook.add_format()
			contest_right_per.set_text_wrap()
			contest_right_per.set_font_size(9)
			contest_right_per.set_align('right')
			contest_right_per.set_align('vcenter')
			contest_right_per.set_num_format('#,##0.0')
			contest_right_per.set_bg_color('#cfdbf0')

			contest_center = workbook.add_format({'italic':1})
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			contest_fc = workbook.add_format({'bold':1})
			contest_fc.set_text_wrap()
			contest_fc.set_font_size(9)
			contest_fc.set_align('center')
			contest_fc.set_align('vcenter')
			contest_fc.set_border(style=1)

			contest_left0 = workbook.add_format({'italic':1})
			contest_left0.set_font_size(9)
			contest_left0.set_align('left')
			contest_left0.set_align('vcenter')

			# Draw headers
			worksheet.write(0,2, u"Борлуулагчийн маршруын тайлан", h1)
			worksheet.write(1,0, u"Борлуулагч: " + self.user_id.display_name, contest_left0)
			worksheet.write(1,4, u"DATE: " + self.date_start.strftime("%Y-%m-%d") +" - "+ self.date_end.strftime("%Y-%m-%d"), contest_left0)

			row = 2
			worksheet.set_row(row, 26)
			worksheet.write(row, 0, u"№", header_wrap)
			worksheet.set_column('A:A', 4)
			worksheet.write(row, 1, "Өдөр", header_wrap)
			worksheet.set_column('B:B', 18)
			worksheet.write(row, 2, "Чиглэл", header_wrap)
			worksheet.set_column('C:C', 30)
			worksheet.write(row, 3, "Нийт орох ёстой", header_wrap)
			worksheet.set_column('D:D', 10)
			worksheet.write(row, 4, "Чиглэлийн дагуу явсан", header_wrap)
			worksheet.set_column('E:E', 40)
			worksheet.write(row, 5, "Тоо", header_wrap)
			worksheet.set_column('F:F', 9)
			worksheet.write(row, 6, "Чиглэлийн дагуу явсан", header_wrap)
			worksheet.set_column('G:G', 40)
			worksheet.write(row, 7, "Тоо", header_wrap)
			worksheet.set_column('H:H', 9)
			worksheet.write(row, 8, "%", header_wrap)
			worksheet.set_column('I:I', 9)
			worksheet.freeze_panes(3, 4)

			number = 1
			row = 3
			route = self.env['salesman.route.planner.line']
			for line in route_plan.line_ids:
				name_str = line.week_day if line.day_type == 'weekly' else line.month_days
				worksheet.write(row, 0, number, contest_number)
				worksheet.write(row, 1, name_str, contest_left)
				ok_names = []
				no_names = []
				ok_qty = 0
				no_qty = 0
				for partner in line.partner_ids:
					sos = self.env['sale.order'].search([
						('state','in',['sale','done']),
						('validity_date','>=',self.date_start),
						('validity_date','<=',self.date_end),
						('user_id','=',self.user_id.id),
						('partner_id','=',partner.id)])
					for so in sos:
						check = route._check_partner_route(so.user_id.id, so.partner_id.id, so.validity_date.strftime("%Y-%m-%d"))
						if check:
							ok_names.append(so.partner_id.name)
							ok_qty += 1
						else:
							no_names.append(so.partner_id.name)
							no_qty += 1
					if len(sos) == 0:
						no_names.append(partner.name)
						no_qty += 1

				worksheet.write(row, 2, ','.join(line.route_ids.mapped('name')), contest_left)
				worksheet.write(row, 3, len(line.partner_ids.ids), contest_right)
				worksheet.write(row, 4, ','.join(ok_names), contest_left)
				worksheet.write(row, 5, ok_qty, contest_right)
				worksheet.write(row, 6, ','.join(no_names), contest_left)
				worksheet.write(row, 7, no_qty, contest_right)
				worksheet.write_formula(row, 8, 
						'{=IFERROR(('+self._symbol(row, 5) +'*100)/'+ self._symbol(row, 3)+',0)}', contest_right)
				number += 1
				row += 1

			# =================================================================================
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
				 'target': 'new',
			}

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol



