	# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
import base64
from datetime import date, datetime, timedelta
from odoo import fields, models, _



class WizardSaleReport(models.TransientModel):
	_name = "wizard.sale.report"
	_description = "wizard.sale.report"

	date_start = fields.Date(string='Эхлэх огноо', required=True)
	date_end = fields.Date(string='Дуусах огноо', required=True)


	def excel_report(self):
		if self.date_start < self.date_end:
			output=BytesIO()
			workbook=xlsxwriter.Workbook(output)
			file_name='Sale Report.xlsx'

			header = workbook.add_format({'bold':1})
			header.set_text_wrap()
			header.set_font_size(14)
			header.set_font('Times new roman')
			header.set_align('center')
			header.set_align('vcenter')

			sub_header = workbook.add_format()
			sub_header.set_text_wrap()
			sub_header.set_font_size(10)
			sub_header.set_font('Times new roman')
			sub_header.set_align('center')
			sub_header.set_align('vcenter')

			title = workbook.add_format({'bold':1})
			title.set_text_wrap()
			title.set_font_size(10)
			title.set_font('Times new roman')
			title.set_align('center')
			title.set_align('vcenter')
			title.set_border(style=1)

			tnumber = workbook.add_format()
			tnumber.set_font_size(9)
			tnumber.set_font('Times new roman')
			tnumber.set_align('center')
			tnumber.set_align('vcenter')
			tnumber.set_border(style=1)

			contest_center = workbook.add_format({'num_format': '#,##0.0'})
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sheet = workbook.add_worksheet('Борлуулалтын тайлан')
			sheet.merge_range(0, 0, 0, 6, u'Борлуулалтын дансны дэлгэрэнгүй тайлан', header)
			sheet.merge_range(0, 7, 0, 10, u'Санхүү, эдийн засгийн сайдын  2002 оны 191 тоот тушаалаар батлав.', sub_header)
			sheet.merge_range(1, 7, 1, 10, u'Тайлант үе %s - %s' %(self.date_start, self.date_end), sub_header)
			row = 4
			number = 1
			sheet.merge_range(3, 0, 4, 0, u'№', title)
			sheet.merge_range(3, 1, 4, 1, u'Огноо', title)
			sheet.merge_range(3, 2, 4, 2, u'Бэлтгэн нийлүүлэгч байгууллагын нэр', title)
			sheet.merge_range(3, 3, 4, 3, u'Захиалгын дугаар', title)
			sheet.merge_range(3, 4, 3, 6, u'Батлагдсан захиалга', title)
			sheet.merge_range(3, 7, 3, 10, u'Хүргэгдсэн захиалга', title)
			sheet.write(row, 4, u'Нийт дүн', title)
			sheet.write(row, 5, u'НӨАТ-гүй дүн', title)
			sheet.write(row, 6, u'НӨАТ', title)
			sheet.write(row, 7, u'Нийт дүн', title)
			sheet.write(row, 8, u'НӨАТ-гүй дүн', title)
			sheet.write(row, 9, u'НӨАТ', title)
			sheet.write(row, 10, u'ББӨ', title)
			sheet.merge_range(3, 11, 4, 11, u'Нийт ашиг', title)
			sheet.merge_range(3, 12, 4, 12, u'Нийт ашиг %', title)
			
			sheet.write(row, 12, u'Нийт ашиг', title)

			sheet.set_column('A:A', 5)
			sheet.set_column('B:D', 20)
			sheet.set_column('E:M', 15)

			domains=[
				('date_done','>=',self.date_start.strftime("%Y-%m-%d")),
				('date_done','<=',self.date_end.strftime("%Y-%m-%d")),
				('date_done','!=',False),
				('state','=','done'),
				('sale_id','!=',False)
				# ('invoice_status','in',['invoiced']),
				# ('uldegdel_tulbur','=',0),
			]

			# sales = self.env['sale.order'].search(domains)
			pickings = self.env['stock.picking'].search(domains, order='date_done ASC')
			row+=1
			for picking in pickings:
				so_amount = picking.sale_id.amount_total
				so_nuat_amount = so_amount/1.1*0.1
				so_net_amount = so_amount - so_nuat_amount

				picking_amount = sum(picking.move_ids.mapped('sub_total_sale')) + (sum(picking.move_ids.mapped('sub_total_sale'))*0.1)
				# picking_nuat_amount = picking_amount/1.1*0.1
				picking_nuat_amount = sum(picking.move_ids.mapped('sub_total_sale'))
				picking_net_amount = picking_amount - picking_nuat_amount

				niit_urtug = sum(picking.move_ids.mapped('niit_urtug'))
				profit_amount = picking_nuat_amount - niit_urtug
				profit_percent = profit_amount/picking_amount*100

				sheet.write(row, 0, number, tnumber)
				sheet.write(row, 1, picking.date_done.strftime('%Y-%m-%d') if picking else False, contest_center)
				sheet.write(row, 2, picking.partner_id.name, contest_center)
				sheet.write(row, 3, picking.sale_id.name if picking.sale_id else False, contest_center)
				sheet.write(row, 4, so_amount if picking.sale_id else 0, contest_center)
				sheet.write(row, 5, so_net_amount if picking.sale_id else 0, contest_center)
				sheet.write(row, 6, so_nuat_amount if picking.sale_id else 0, contest_center)
				sheet.write(row, 7, picking_amount if picking.sale_id else 0, contest_center)
				sheet.write(row, 8, picking_nuat_amount if picking.move_ids else 0, contest_center)
				sheet.write(row, 9, picking_net_amount if picking.move_ids else 0, contest_center)
				sheet.write(row, 10, niit_urtug if picking.move_ids else 0, contest_center)
				sheet.write(row, 11, profit_amount if picking_amount and niit_urtug else picking_amount, contest_center)
				sheet.write(row, 12, profit_percent if profit_amount and picking_amount else 0, contest_center)
				number += 1
				row += 1
			

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