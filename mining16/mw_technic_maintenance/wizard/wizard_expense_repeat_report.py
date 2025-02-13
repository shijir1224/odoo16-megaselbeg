# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
import collections

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardExpenseRepeatReport(models.TransientModel):
	_name = "wizard.expense.repeat.report"
	_description = "wizard.expense.repeat.report"  

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	technic_id = fields.Many2one('technic.equipment', string=u'Техник',	)

	
	def export_report(self):
		additional_condition = ""
		if self.technic_id:
			additional_condition = " and ll.technic_id = %d " % self.technic_id.id
		query = """
			SELECT 
				tt.park_number as park_number,
				pt.name as name,
				(pp.default_code) as default_code,
				array_agg(ll.qty) as qty,
				array_agg(ll.date) as move_date,
				array_agg(wo.name) as wo_name,
				array_agg(rp.name) as employee_name,
				count(*)
			FROM maintenance_wo_expense_report as ll
			LEFT JOIN technic_equipment as tt on tt.id = ll.technic_id
			LEFT JOIN product_product as pp on pp.id = ll.product_id
			LEFT JOIN product_template as pt on pt.id = pp.product_tmpl_id
			LEFT JOIN maintenance_workorder as wo on wo.id = ll.wo_id
			LEFT JOIN res_users as ru on ru.id = ll.parts_user_id
			LEFT JOIN res_partner as rp on rp.id = ru.partner_id
			WHERE 
				ll.price_unit < -5000000 and 
				ll.date >= '%s' and
				ll.date <= '%s' 
				 %s
			GROUP BY tt.park_number, pt.name, pp.default_code
			HAVING count(*) > 1
			ORDER BY tt.park_number, pt.name, pp.default_code
		""" % (self.date_start, self.date_end, additional_condition)
		# print '===', query
		self.env.cr.execute(query)
		query_result = self.env.cr.dictfetchall()
		if query_result:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)

			file_name = 'Expense repeat report.xlsx'

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

			footer = workbook.add_format({'bold': 1})
			footer.set_text_wrap()
			footer.set_font_size(9)
			footer.set_align('right')
			footer.set_align('vcenter')
			footer.set_border(style=1)
			footer.set_bg_color('#6495ED')
			footer.set_num_format('#,##0.00')

			number_right = workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right = workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_right0 = workbook.add_format()
			contest_right0.set_text_wrap()
			contest_right0.set_font_size(9)
			contest_right0.set_align('right')
			contest_right0.set_align('vcenter')
			contest_right0.set_num_format('#,##0.00')

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

			categ_name = workbook.add_format({'bold': 1})
			categ_name.set_font_size(9)
			categ_name.set_align('left')
			categ_name.set_align('vcenter')
			categ_name.set_border(style=1)
			categ_name.set_bg_color('#B9CFF7')

			categ_right = workbook.add_format({'bold': 1})
			categ_right.set_font_size(9)
			categ_right.set_align('right')
			categ_right.set_align('vcenter')
			categ_right.set_border(style=1)
			categ_right.set_bg_color('#B9CFF7')
			categ_right.set_num_format('#,##0.00')

			# Борлуулагчаар харуулах sheet
			worksheet = workbook.add_worksheet(u'Тайлан')
			worksheet.write(1,3, u"Давтан зарлагын тайлан", h1)
			if self.technic_id:
				worksheet.write(2,0, u"Техник: " + self.technic_id.name or '', contest_left0)
			worksheet.write(3,0, u"Тайлант хугацаа: " + self.date_start +" ~ "+ self.date_end, contest_left0)

			# TABLE HEADER
			row = 5
			worksheet.set_row(row, 26)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column('A:A', 5)
			worksheet.write(row, 1, u"Техник", header_wrap)
			worksheet.set_column('B:B', 22)
			worksheet.write(row, 2, u"Сэлбэгийн нэр", header_wrap)
			worksheet.set_column('C:C', 30)
			worksheet.write(row, 3, u"Сэлбэгийн дугаар", header_wrap)
			worksheet.set_column('D:D', 13)
			worksheet.write(row, 4, u"Тоо ширхэг", header_wrap)
			worksheet.set_column('E:E', 8)
			worksheet.write(row, 5, u"Огноо", header_wrap)
			worksheet.set_column('F:F', 10)
			worksheet.write(row, 6, u"Хүлээн авсан ажилтан", header_wrap)
			worksheet.set_column('G:G', 18)
			worksheet.write(row, 7, u"WO дугаар", header_wrap)
			worksheet.set_column('H:H', 13)
			worksheet.freeze_panes(6, 0)
			row += 1
			# Data
			number = 1
			t_name = ""
			for line in query_result:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line['park_number'], contest_center)
				worksheet.write(row, 2, line['name'] or '-', contest_left)
				worksheet.write(row, 3, line['default_code'], contest_center)
				r = row
				for ll in line['qty']:
					worksheet.write(r, 4, ll or 0, contest_right)
					r += 1
				r = row
				for ll in line['move_date']:
					worksheet.write(r, 5, ll.strftime('%Y-%m-%d'), contest_center)
					r += 1
				r = row
				for ll in line['employee_name']:
					worksheet.write(r, 6, ll, contest_left)
					r += 1
				r = row
				for ll in line['wo_name']:
					worksheet.write(r, 7, ll, contest_center)
					r += 1
				row += len(line['qty'])
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



