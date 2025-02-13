# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
import datetime
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from xlsxwriter.utility import xl_rowcol_to_cell
from odoo import fields, models, _

class WizardSaleTeamReport(models.TransientModel):
	_name = "wizard.sale.team.report"
	_description = "wizard.sale.team.report"

	date_start = fields.Date(string='Эхлэх огноо', required=True)
	date_end = fields.Date(string='Дуусах огноо', required=True)

	def excel_report(self):
		if self.date_start < self.date_end:
			output=BytesIO()
			workbook=xlsxwriter.Workbook(output)
			file_name='Sale Team Report.xlsx'

			contest_center=workbook.add_format({'num_format': '###,###,###.##'})
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sheet=workbook.add_worksheet('Sale Team Report')
			sheet.set_column(0, 0, 25)
			sheet.write(2,0, '30 сая хүртэл', contest_center)
			sheet.write(3,0, '30-100 сая', contest_center)
			sheet.write(4,0, '100-200 сая', contest_center)
			sheet.write(5,0, '200-300 сая', contest_center)
			sheet.write(6,0, '300-400 сая', contest_center)
			sheet.write(7,0, '400-500 сая', contest_center)
			sheet.write(8,0, '500-600 сая', contest_center)
			sheet.write(9,0, '600-700 сая', contest_center)
			sheet.write(10,0, '700-800 сая', contest_center)
			sheet.write(11,0, '800-900 сая', contest_center)
			sheet.write(12,0, '900 сая-1 тэрбум', contest_center)
			sheet.write(13,0, '1 тэрбум-с дээш', contest_center)

			domains=[
				('date_order','>=',self.date_start.strftime("%Y-%m-%d")),
				('date_order','<=',self.date_end.strftime("%Y-%m-%d")),
				('invoice_status','in',['invoiced']),
				('uldegdel_tulbur','=',0),
			]

			sales = self.env['sale.order'].search(domains)
			sheet.merge_range(0, 0, 0, len(sales.sale_team_members_ids), 'Sales Team member', contest_center)
			col=1
			for user in sales.sale_team_members_ids:
				sheet.write(1, col, user.name, contest_center)
				domains.append(('sale_team_members_ids','in',user.ids))
				domains.append(('amount_total','>',0))
				domains.append(('amount_total','<=',30000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(2, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',30000000))
				domains.append(('amount_total','<=',100000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(3, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',100000000))
				domains.append(('amount_total','<=',200000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(4, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',200000000))
				domains.append(('amount_total','<=',300000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(5, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',300000000))
				domains.append(('amount_total','<=',400000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(6, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',400000000))
				domains.append(('amount_total','<=',500000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(7, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',500000000))
				domains.append(('amount_total','<=',600000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(8, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',600000000))
				domains.append(('amount_total','<=',700000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(9, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',700000000))
				domains.append(('amount_total','<=',800000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(10, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',800000000))
				domains.append(('amount_total','<=',900000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(11, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',900000000))
				domains.append(('amount_total','<=',1000000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(12, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				domains.append(('amount_total','>',1000000000))
				so = self.env['sale.order'].search(domains)
				sheet.write(13, col, len(so), contest_center)
				del domains[-1]
				del domains[-1]
				col += 1
			# =============================
			workbook.close()
			out=base64.encodebytes(output.getvalue())
			excel_id=self.env['report.excel.output'].create(
				{'data': out, 'name': file_name})

			return {
				 'type': 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				 'target': 'new',
			}
		else:
			raise UserError(('Бичлэг олдсонгүй!'))

	def _symbol(self, row, col):
			return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol