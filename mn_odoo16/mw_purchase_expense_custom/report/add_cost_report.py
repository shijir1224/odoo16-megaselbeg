# -*- coding: utf-8 -*-
from odoo import fields, models, _
import time
from io import BytesIO
import xlsxwriter
import base64
from odoo.exceptions import UserError

class WizardAddCostExcelReport(models.TransientModel):
	_name = 'wizard.add.cost.report'
	_description = "Wizard add cost report"

	date_start = fields.Date(string=u'Эхлэх огноо', required=True, default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(string=u'Дуусах огноо', required=True, default=fields.Date.context_today)

	def action_add_cost_export(self):
		if self.date_start <= self.date_end:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Нэмэгдэл зардлын тайлан.xlsx'

			header = workbook.add_format({'bold': 1})
			header.set_font_size(14)
			header.set_font('Times new roman')
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)

			header3 = workbook.add_format({'bold': 1})
			header3.set_font_size(11)
			header3.set_font('Times new roman')
			header3.set_align('left')
			header3.set_align('vleft')
			header3.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_font('Times new roman')
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			contest_center_red = workbook.add_format()
			contest_center_red.set_text_wrap()
			contest_center_red.set_font_size(9)
			contest_center_red.set_font('Times new roman')
			contest_center_red.set_font_color('red')
			contest_center_red.set_align('center')
			contest_center_red.set_align('vcenter')
			contest_center_red.set_border(style=1)

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_font('Times new roman')
			contest_left.set_align('left')
			contest_left.set_align('vleft')
			contest_left.set_border(style=1)

			contest_center_b = workbook.add_format({'bold': 1})
			contest_center_b.set_text_wrap()
			contest_center_b.set_font_size(9)
			contest_center_b.set_font('Times new roman')
			contest_center_b.set_align('center')
			contest_center_b.set_align('vcenter')
			contest_center_b.set_border(style=1)
			contest_center_b.set_bg_color('#EE9A4D')

			sheet = workbook.add_worksheet(u'Задаргаа')
			row = 0
			sheet.merge_range(row, 0, row, 14, u'Нэмэгдэл зардлын тайлан', header)
			sheet.freeze_panes(3, 0)
			
			row += 1
			sheet.merge_range(row, 0, row, 14, u'Хамрах хугацаа: %s -----> %s'%(self.date_start, self.date_end), header3)
			
			add_costs = self.env['purchase.add.cost'].search([('date', '>=', self.date_start),('date', '<=', self.date_end)])
			
			# HEADER
			row += 1
			sheet.set_row(row, 25)
			sheet.write(row, 0, u'№', contest_center_b)
			sheet.set_column('A:A', 5)
			sheet.write(row, 1, u'Нэмэгдэл зардлын дугаар', contest_center_b)
			sheet.set_column('B:B', 15)
			sheet.write(row, 2, u'Огноо ханш', contest_center_b)
			sheet.set_column('C:C', 10)
			sheet.write(row, 3, u'Зардлын харилцагч', contest_center_b)
			sheet.set_column('D:D', 30)
			sheet.write(row, 4, u'Зардлын бараа', contest_center_b)
			sheet.set_column('E:E', 25)
			sheet.write(row, 5, u'Хуваарилах арга', contest_center_b)
			sheet.set_column('F:F', 12)
			sheet.write(row, 6, u'Зардлын дүн', contest_center_b)
			sheet.set_column('G:G', 12)
			sheet.write(row, 7, u'Зардлын нэхэмлэхийн дугаар', contest_center_b)
			sheet.set_column('H:H', 25)
			sheet.write(row, 8, u'Валют', contest_center_b)
			sheet.set_column('I:I', 10)
			sheet.write(row, 9, u'Захиалгын дугаар', contest_center_b)
			sheet.set_column('J:J', 12)
			sheet.write(row, 10, u'Бараа', contest_center_b)
			sheet.set_column('K:K', 15)
			sheet.write(row, 11, u'Нийт жин', contest_center_b)
			sheet.set_column('L:L', 10)
			sheet.write(row, 12, u'Ирэх тоо', contest_center_b)
			sheet.set_column('M:M', 10)
			sheet.write(row, 13, u'Нэгж үнэ', contest_center_b)
			sheet.set_column('N:N', 10)
			sheet.write(row, 14, u'Нийт үнэ', contest_center_b)
			sheet.set_column('O:O', 10)
			
			# DATA
			i = 1
			for add_cost in add_costs:
				# total_amount_arr = sum([item.qty_received_future * item.price_unit for item in add_cost.po_line_ids
				# 					for line in add_cost.expenses_line if item.qty_received_future and item.price_unit and line])
				# total_unit_arr = sum([item.price_unit for item in add_cost.po_line_ids
				# 					for line in add_cost.expenses_line if item.price_unit and line])
				# total_weight_arr = sum([item.subtotal_weight for item in add_cost.po_line_ids
				# 					for line in add_cost.expenses_line if item.subtotal_weight and line])
				# total_qty_arr = sum([item.qty_received_future for item in add_cost.po_line_ids
				# 					for line in add_cost.expenses_line if item.qty_received_future and line])

				for exp in add_cost.expenses_line:
					each_amount = sum([item.qty_received_future * item.price_unit for item in add_cost.po_line_ids
										for line in add_cost.expenses_line if item.qty_received_future and item.price_unit and line == exp])
					each_unit = sum([item.price_unit for item in add_cost.po_line_ids
										for line in add_cost.expenses_line if item.price_unit and line == exp])
					each_weight = sum([item.subtotal_weight for item in add_cost.po_line_ids
										for line in add_cost.expenses_line if item.subtotal_weight and line == exp])
					each_qty = sum([item.qty_received_future for item in add_cost.po_line_ids
										for line in add_cost.expenses_line if item.qty_received_future and line == exp])
				
				for po_line in add_cost.po_line_ids:
					for expenses_line in add_cost.expenses_line:
						add_cost_name = add_cost.name
						date = add_cost.date
						partner_name = expenses_line.partner_id.name
						cost_product = expenses_line.product_id.name
						portion_method = dict(expenses_line._fields['portion_method'].selection).get(expenses_line.portion_method)
						invoice_ref = expenses_line.invoice_ref
						currency_name = expenses_line.currency_id.name
						po_name = po_line.order_id.name
						if po_line.product_id.type != 'service':
							po_product = po_line.product_id.default_code
						else:
							po_product = po_line.product_id.name
						subtotal_weight = po_line.subtotal_weight
						qty_received_future = po_line.qty_received_future
						price_unit = po_line.price_unit
						price_total = po_line.qty_received_future * po_line.price_unit
						current_amount = expenses_line.current_amount

						row += 1

						sheet.write(row, 0, u'%s' %(i), contest_center)
						sheet.write(row, 1, u'%s' %(add_cost_name), contest_center)
						sheet.write(row, 1, u'%s' %(add_cost_name), contest_center)
						sheet.write(row, 2, u'%s' %(date), contest_center)
						sheet.write(row, 3, u'%s' %(partner_name), contest_left)
						sheet.write(row, 4, u'%s' %(cost_product), contest_left)
						sheet.write(row, 5, u'%s' %(portion_method), contest_center)
						sheet.write(row, 7, u'%s' %(invoice_ref or ''), contest_center)
						sheet.write(row, 8, u'%s' %(currency_name), contest_center)
						sheet.write(row, 9, u'%s' %(po_name), contest_center)
						sheet.write(row, 10, u'%s' %(po_product), contest_center)
						sheet.write(row, 11, (subtotal_weight), contest_center)
						sheet.write(row, 12, (qty_received_future), contest_center)
						sheet.write(row, 13, (price_unit), contest_center)
						sheet.write(row, 14, (price_total), contest_center)
						# sheet.write(row, 15, (current_amount), contest_center)

						if expenses_line.portion_method in ['subtotal']:
							# sheet.write(row, 16, (price_total / each_amount), contest_center)
							sheet.write(row, 6, round((current_amount * (price_total / each_amount)),3), (contest_center if expenses_line.is_without_cost==False else contest_center_red))
						elif expenses_line.portion_method in ['price']:
							# sheet.write(row, 16, (price_unit / each_unit), contest_center)
							sheet.write(row, 6, round((current_amount * (price_unit / each_unit)),3), (contest_center if expenses_line.is_without_cost==False else contest_center_red))
						elif expenses_line.portion_method in ['qty']:
							# sheet.write(row, 16, (qty_received_future / each_qty), contest_center)
							sheet.write(row, 6, round((current_amount * (qty_received_future / each_qty)),3), (contest_center if expenses_line.is_without_cost==False else contest_center_red))
						elif expenses_line.portion_method in ['weight']:
							# sheet.write(row, 16, (subtotal_weight / round(each_weight, 2)), contest_center)
							sheet.write(row, 6, round((current_amount * (subtotal_weight / round(each_weight, 2))),3), (contest_center if expenses_line.is_without_cost==False else contest_center_red))
						else:
							sheet.write(row, 6, '', contest_center)

						i += 1

					# sheet.write(row+1, 11, (total_weight_arr), contest_center)
					# sheet.write(row+1, 12, (total_qty_arr), contest_center)
					# sheet.write(row+1, 13, (total_unit_arr), contest_center)
					# sheet.write(row+1, 14, (total_amount_arr), contest_center)

			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create(
				{'data': out, 'name': file_name})

			return {
				'type': 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
				'target': 'new',
			}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))