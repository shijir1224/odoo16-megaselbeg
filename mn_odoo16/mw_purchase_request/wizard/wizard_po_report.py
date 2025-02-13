# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo import _
from odoo.exceptions import UserError
from io import BytesIO
import time
import xlsxwriter
import base64

class WizardPOReport(models.TransientModel):
	_name = 'wizard.po.report.mw'
	_description = "Wizard PO report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01 00:00:00'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо', default=fields.Date.context_today)
	partner_ids = fields.Many2many('res.partner', string='Нийлүүлэгч')
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id)

	def view_po_report(self):
		context = dict(self._context)
		# GET views ID
		mod_obj = self.env['ir.model.data']
		tree_res = mod_obj.get_object_reference('mw_purchase_request', 'po_report_mw_view_tree')
		tree_id = tree_res and tree_res[1] or False
		result = {
			'name': _('Report'),
			'view_type': 'list',
			'view_mode': 'tree',
			'res_model': 'po.report.mw',
			'view_id': False,
			'views': [(tree_id, 'tree')],
			'domain': [('partner_id', 'in', self.partner_ids.ids),
					   ('po_date', '>=', self.date_start),
					   ('po_date', '<=', self.date_end)],
			'type': 'ir.actions.act_window',
			'target': 'current',
			'context': context,
		}
		return result

	def excel_po_report(self):
		if self.date_start <= self.date_end:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Худалдан_авалтын_нийлүүлэгчийн_тайлан_' + str(self.date_start) + '__' + str(
				self.date_end) + '.xlsx'

			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

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

			contest_left = workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sub_total = workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(9)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			worksheet = workbook.add_worksheet(u'Нийлүүлэгчийн тайлан')
			worksheet.set_zoom(100)

			# TABLE HEADER
			row = 0
			worksheet.set_row(0, 30)
			worksheet.write(row, 0, u'Д/д', header_wrap)
			worksheet.set_column(0, 0, 10)
			worksheet.write(row, 1, u'Supplier', header_wrap)
			worksheet.set_column(1, 1, 30)
			worksheet.write(row, 2, u'PO number', header_wrap)
			worksheet.set_column(2, 2, 10)
			worksheet.write(row, 3, u'Product Code', header_wrap)
			worksheet.set_column(3, 3, 10)
			worksheet.write(row, 4, u'Supplier Part Number', header_wrap)
			worksheet.set_column(4, 4, 15)
			worksheet.write(row, 5, u'Item name', header_wrap)
			worksheet.set_column(5, 5, 20)
			worksheet.write(row, 6, u'Ordered Quantity', header_wrap)
			worksheet.set_column(6, 6, 15)
			worksheet.write(row, 7, u'Delivered', header_wrap)
			worksheet.set_column(7, 7, 10)
			worksheet.write(row, 8, u'Back Ordered', header_wrap)
			worksheet.set_column(8, 8, 10)
			worksheet.write(row, 9, u'Amount', header_wrap)
			worksheet.set_column(9, 9, 10)
			worksheet.write(row, 10, u'Total amount', header_wrap)
			worksheet.set_column(10, 10, 10)

			domains = [
				('po_date', '>=', self.date_start),
				('po_date', '<=', self.date_end),
				('company_id', '=', self.company_id.id),
			]
			if self.partner_ids:
				domains.append(('partner_id', 'in', self.partner_ids.ids))
			pos = self.env['po.report.mw'].search(domains, order='po_id, product_id')
			row = 1
			number = 1
			for po in pos:
				if not po.product_id:
					continue
				worksheet.write(row, 0, number, contest_center)
				worksheet.write(row, 1, po.partner_id.name, contest_center)
				worksheet.write(row, 2, po.po_id.name, contest_center)
				worksheet.write(row, 3, po.product_code, contest_center)
				worksheet.write(row, 4, po.default_code, contest_center)
				worksheet.write(row, 5, po.product_id.name, contest_center)
				worksheet.write(row, 6, po.qty_po, contest_center)
				worksheet.write(row, 7, po.qty_received, contest_center)
				worksheet.write(row, 8, po.qty_po_rec, contest_center)
				worksheet.write(row, 9, "{0:,.2f}".format(po.price_average), contest_center)
				worksheet.write(row, 10, "{0:,.2f}".format(po.price_average * po.qty_po_rec), contest_center)
				row += 1
				number += 1
			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create(
				{'data': out, 'name': file_name})

			return {'type': 'ir.actions.act_url',
					'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (
						excel_id.id, excel_id.name),
					'target': 'new'}
		else:
			raise UserError(_(u'Бичлэг олдсонгүй!'))
