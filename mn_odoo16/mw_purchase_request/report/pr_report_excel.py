# -*- coding: utf-8 -*-

import xlsxwriter
from io import BytesIO
import base64
from odoo import api, fields, models
from xlsxwriter.utility import xl_rowcol_to_cell
import pytz

class PrReportExcel(models.TransientModel):
	_name = 'pr.report.excel'
	_description = 'Pr report Excel'

	date_start = fields.Date(required=True, string=u'Эхлэх огноо')
	date_end = fields.Date(required=True, string=u'Дуусах огноо')
	date_range_id = fields.Many2one('date.range',string='Огнооны хязгаар')
	date_type = fields.Selection([('pr','Хүсэлтийн огноо'),('po','Худалдан авалтын огноо'),('stock','Агуулахын огноо')], string='Огнооны төрөл', default='pr')
	company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id)

	@api.onchange('date_range_id')
	def onchange_date_range_id(self):
		self.date_start = self.date_range_id.date_start
		self.date_end = self.date_range_id.date_end

	# Excel ээр харах
	def action_export(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		worksheet = workbook.add_worksheet(u'delivery report')

		h1 = workbook.add_format({'bold': 1})
		h1.set_font_size(9)
		h1.set_align('center')
		h1.set_font_name('Arial')

		header = workbook.add_format({'bold': 1})
		header.set_font_size(9)
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)
		header.set_bg_color('#9ad808')
		header.set_text_wrap()
		header.set_font_name('Arial')

		header_wrap = workbook.add_format({'bold': 1})
		header_wrap.set_text_wrap()
		header_wrap.set_font_size(11)
		header_wrap.set_align('center')
		header_wrap.set_align('vcenter')
		header_wrap.set_border(style=1)

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
		contest_right.set_num_format('#,##0.00')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)
		contest_center.set_font_name('Arial')

		header_center = workbook.add_format()
		header_center.set_text_wrap()
		header_center.set_font_size(9)
		header_center.set_align('center')
		header_center.set_align('vcenter')
		header_center.set_border(style=1)
		header_center.set_font_name('Arial')
		header_center.set_bg_color('yellow')

		cell_format2 = workbook.add_format({
			'border': 1,
			'align': 'right',
			'font_size':9,
			'font_name': 'Arial',
			'num_format':'#,####0'
		})

		row = 0
		worksheet.merge_range(row, 0, row, 23, u'Delivery reports', header_wrap)
		worksheet.set_row(row, 20)

		row += 1

		worksheet.write(row, 0, u"PR number", header_center)
		worksheet.write(row, 1, u"PR date", header_center)
		worksheet.write(row, 2, u"Item description", header_center)
		worksheet.write(row, 3, u"Source document", header_center)
		worksheet.write(row, 4, u"PO number", header_center)
		worksheet.write(row, 5, u"PO date", header_center)
		worksheet.write(row, 6, u"Deliver to [warehouse]", header_center)
		worksheet.write(row, 7, u"PR part number", header_center)
		worksheet.write(row, 8, u"PR item description", header_center)
		worksheet.write(row, 9, u"UOM", header_center)
		worksheet.write(row, 10, u"PR quantity", header_center)
		worksheet.write(row, 11, u"PO quantity", header_center)
		worksheet.write(row, 12, u"Received quantity", header_center)
		worksheet.write(row, 13, u"Outstanding delivery", header_center)
		worksheet.write(row, 14, u"PO status", header_center)
		worksheet.write(row, 15, u"PO approved date", header_center)
		worksheet.write(row, 16, u"Received date", header_center)
		worksheet.write(row, 17, u"Currency", header_center)
		worksheet.write(row, 18, u"Unit price", header_center)
		worksheet.write(row, 19, u"Vat", header_center)
		worksheet.write(row, 20, u"PO amount", header_center)
		worksheet.write(row, 21, u"Received amount", header_center)
		worksheet.write(row, 22, u"Outstanding amount", header_center)
		worksheet.write(row, 23, u"Vendor", header_center)

		pr_report = self.env['pr.report']
		where = ''
		order_by = ''

		if self.date_type == 'pr':
			where = "pr.date >= '%s' and pr.date <= '%s' and pur.company_id = %s"%(self.date_start, self.date_end, self.company_id.id)
			order_by = " order by 4, 3"
		elif self.date_type == 'po':
			where = "pr.po_date >= '%s' and pr.po_date <= '%s' and pur.company_id = %s"%(self.date_start, self.date_end, self.company_id.id)
			order_by = " order by 6"
		elif self.date_type == 'stock':
			where = "pr.stock_date >= '%s' and pr.stock_date <= '%s' and pur.company_id = %s"%(self.date_start, self.date_end, self.company_id.id)
			order_by = " order by 5"

		query = """
			SELECT
				pr.pr_line_id,
				pr.request_id,
				pr.po_id,
				max(pr.date) as date,
				max(pr.stock_date) as stock_date,
				max(pr.po_date) as po_date,
				max(pr.product_id) as product_id,
				max(pr.picking_id) as picking_id,
				sum(pr.qty) as qty,
				sum(pr.qty_po) as qty_po,
				sum(pr.qty_received) as qty_received,
				sum(pr.qty_invoiced) as qty_invoiced
			FROM pr_report pr LEFT JOIN purchase_request pur on pur.id=pr.request_id
			WHERE {0}
			GROUP BY 1,2,3
			{1}
			""".format(where, order_by)
		self.env.cr.execute(query)
		query_result = self.env.cr.dictfetchall()

		worksheet.freeze_panes(row+1, 7)
		# Open order
		for item in query_result:

			row+=1
			pr_line_id = False
			if item['pr_line_id']:
				pr_line_id = self.env['purchase.request.line'].browse(item['pr_line_id'])
				pr_date = fields.Datetime.from_string(pr_line_id.request_id.date)
				timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
				if pr_date:
					pr_date = str(pr_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19]
			po_id = False
			po_line_id = False
			if item['po_id']:
				po_id = self.env['purchase.order'].browse(item['po_id'])
				domain = [('order_id', '=', po_id.id), ('product_id', '=', item['product_id'])]
				if pr_line_id:
					domain += [('pr_line_many_ids','in',[pr_line_id.id])]
				po_line_id = self.env['purchase.order.line'].search(domain, limit=1)
				po_date_order = fields.Datetime.from_string(po_id.date_order)
				timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
				if po_date_order:
					po_date_order = str(po_date_order.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19]

				po_date_approve = fields.Datetime.from_string(po_id.date_approve)
				timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
				if po_date_approve:
					po_date_approve = str(po_date_approve.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19]

			picking_id = False
			picking_id_date_done = False
			if item['picking_id']:
				picking_id = self.env['stock.picking'].browse(item['picking_id'])
				picking_id_date_done = fields.Datetime.from_string(picking_id.date_done)
				timezone = pytz.timezone(self.env.user.tz or self._context.get('tz') or 'UTC')
				picking_id_date_done = str(picking_id_date_done.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[:19] if picking_id_date_done else False

			product_id = self.env['product.product'].browse(item['product_id'])
			qty = item['qty']
			qty_po = item['qty_po']
			qty_received = item['qty_received']

			product_id_pr = self.env['product.product'].browse(item['product_id']) if item['product_id'] else False

			worksheet.write(row, 0, pr_line_id.request_id.name if pr_line_id else '', contest_center)
			worksheet.write(row, 1, pr_date if pr_line_id else '', contest_center)
			worksheet.write(row, 2, po_line_id.name if po_line_id else '', contest_center)
			worksheet.write(row, 3, po_id.origin if po_id else '', contest_center)
			worksheet.write(row, 4, po_id.name if po_id else '', contest_left)
			worksheet.write(row, 5, po_date_order if po_id else '', contest_left)
			worksheet.write(row, 6, po_id.picking_type_id.warehouse_id.name if po_id else '', contest_center)
			worksheet.write(row, 7, product_id_pr.default_code if product_id_pr else '', contest_center)
			worksheet.write(row, 8, product_id_pr.name if product_id_pr else '', contest_center)
			worksheet.write(row, 9, product_id.uom_id.name if product_id else '', contest_center)
			worksheet.write(row, 10, qty, contest_center)
			worksheet.write(row, 11, qty_po, contest_center)
			worksheet.write(row, 12, qty_received, contest_center)
			worksheet.write_formula(row, 13,'{=('+xl_rowcol_to_cell(row, 12)+'-'+xl_rowcol_to_cell(row, 10)+')}', contest_center)
			worksheet.write(row, 14, po_id.flow_line_id.name if po_id else '', contest_center)
			worksheet.write(row, 15, po_date_approve if po_id and po_date_approve else '', contest_center)
			worksheet.write(row, 16, picking_id_date_done if picking_id_date_done else '', contest_center)
			worksheet.write(row, 17, po_id.currency_id.name if po_id else '', cell_format2)
			worksheet.write(row, 18, po_line_id.price_unit if po_line_id else '', cell_format2)
			worksheet.write(row, 19, po_line_id.price_tax if po_line_id else '', cell_format2)
			worksheet.write_formula(row, 20,'{=('+xl_rowcol_to_cell(row, 11)+'*'+xl_rowcol_to_cell(row, 18)+')}', cell_format2)
			worksheet.write_formula(row, 21,'{=('+xl_rowcol_to_cell(row, 12)+'*'+xl_rowcol_to_cell(row, 18)+')}', cell_format2)
			worksheet.write_formula(row, 22,'{=('+xl_rowcol_to_cell(row, 13)+'*'+xl_rowcol_to_cell(row, 18)+')}', cell_format2)
			worksheet.write(row, 23, po_id.partner_id.name if po_id else '', contest_center)

		file_name = u'Delivery reports.xlsx'
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
			'target': 'new',
		}