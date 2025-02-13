from odoo import fields, models, tools, api
from io import BytesIO
import base64
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
import time

class SoyolonPoReport(models.TransientModel):
	_name = 'partner.po.report'
	_description = 'Нийлүүлэгчийн гүйцэтгэлийн тайлан'

	date_start = fields.Date(string=u'Эхлэх огноо', required=True, default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(string=u'Дуусах огноо', required=True, default=fields.Date.context_today)

	def action_export(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Нийлүүлэгчийн гүйцэтгэлийн тайлан.xlsx'

		header = workbook.add_format({'bold': 1})
		header.set_font_size(14)
		header.set_font('Times new roman')
		header.set_align('center')
		header.set_align('vcenter')

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		contest_left_no_border = workbook.add_format()
		contest_left_no_border.set_text_wrap()
		contest_left_no_border.set_font_size(9)
		contest_left_no_border.set_font('Times new roman')
		contest_left_no_border.set_align('left')
		contest_left_no_border.set_align('vcenter')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)

		contest_center_bold = workbook.add_format({'bold': 1})
		contest_center_bold.set_text_wrap()
		contest_center_bold.set_font_size(9)
		contest_center_bold.set_font('Times new roman')
		contest_center_bold.set_align('center')
		contest_center_bold.set_align('vcenter')
		contest_center_bold.set_border(style=1)
		contest_center_bold.set_bg_color('#D1D0CE')

		percent_format = workbook.add_format({
			'num_format': '#,##0_)',
			'font_size': 9,
			'align': 'center',
			'valign': 'vcenter',
			'border': 1,
		})

		sheet = workbook.add_worksheet(u'Sheet1')
		row = 0
		sheet.merge_range(row, 0, row, 10, u'Нийлүүлэгчийн гүйцэтгэлийн тайлан', header)
		sheet.set_row(row, 20)
		sheet.merge_range(row+1, 8, row+1, 10, u'Хамаарах огноо: %s -> %s' %(self.date_start, self.date_end), contest_left_no_border)
		sheet.freeze_panes(2, 0)

		# HEADER
		row = 2
		sheet.set_row(row, 35)
		sheet.write(row, 0, u'PO', contest_center_bold)
		sheet.set_column('A:A', 10)
		sheet.write(row, 1, u'Нийлүүлэгч', contest_center_bold)
		sheet.set_column('B:B', 25)
		sheet.write(row, 2, u'Нийлүүлэх хугацаа', contest_center_bold)
		sheet.write(row, 3, u'Нийлүүлсэн хугацаа', contest_center_bold)
		sheet.write(row, 4, u'Хоцролт /хоног/', contest_center_bold)
		sheet.write(row, 5, u'Хоцролт %', contest_center_bold)
		sheet.write(row, 6, u'Төлөв', contest_center_bold)
		sheet.write(row, 7, u'DOT %', contest_center_bold)
		sheet.write(row, 8, u'DOQ %', contest_center_bold)
		sheet.write(row, 9, u'DIF %', contest_center_bold)
		sheet.write(row, 10, u'SIFOT %', contest_center_bold)
		sheet.set_column('C:K', 15)

		pos = self.env['purchase.order'].search([('delivered_date','>=',self.date_start),('delivered_date','<=',self.date_end)])

		row = 3

		for po in pos:
			sum_ordered_qty = sum([line.product_uom_qty for line in po.order_line])
			sum_received_qty = sum([line.qty_received for line in po.order_line])
			sheet.write(row, 0, po.name, contest_center)
			sheet.write(row, 1, po.partner_id.name if po.partner_id else '', contest_left)
			sheet.write(row, 2, po.deliver_day, contest_center)
			sheet.write(row, 3, po.delivered_day, contest_center)
			sheet.write_formula(row, 4, '{='+ xl_rowcol_to_cell(row, 3) + '-' + xl_rowcol_to_cell(row, 2) +'}', contest_center)
			sheet.write_formula(row, 5, '{='+ xl_rowcol_to_cell(row, 4) + '/' + xl_rowcol_to_cell(row, 2) + '*' + '100' +'}', percent_format)
			h5 = xl_rowcol_to_cell(row, 5)
			sheet.write(row, 6, '=IF(AND(' + h5 + '<=10, ' + h5 + '>=-10), "Хэвийн", IF(' + h5 + '>10, "Хоцорсон", IF(' + h5 + '<-10, "Түрүүлсэн")))', contest_center)
			sheet.write_formula(row, 7, '{=('+ xl_rowcol_to_cell(row, 3) + '/' + xl_rowcol_to_cell(row, 2) + ')' + '*' + '100' +'}', percent_format)
			sheet.write(row, 8, ((sum_received_qty-po.quality_qty) / sum_ordered_qty) * 100, percent_format)
			sheet.write(row, 9, (sum_received_qty / sum_ordered_qty) * 100, percent_format)
			sheet.write_formula(row, 10, '{='+ xl_rowcol_to_cell(row, 7) + '*' + xl_rowcol_to_cell(row, 8) + '*' + xl_rowcol_to_cell(row, 9) +'}', percent_format)

			row += 1

		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
			'target': 'new',
		}

	def action_view(self):
		action = self.env.ref('syl_purchase.action_partner_po_report_list')
		vals = action.read()[0]
		domain = [('delivered_date','>=',self.date_start),('delivered_date','<=',self.date_end)]
		vals['domain'] = domain
		return vals

class PartnerPOReportList(models.Model):
	_name = 'partner.po.report.list'
	_auto = False
	_description = "Partner po report list"
	_order = 'po_id asc'

	po_id = fields.Many2one('purchase.order', string='PO дугаар')
	partner_id = fields.Many2one('res.partner', string='Нийлүүлэгч')
	delivered_date = fields.Date(string='Нийлүүлэгч хүлээн авсан огноо')
	deliver_day = fields.Integer(string='Нийлүүлэх хугацаа')
	delivered_day = fields.Integer(string='Нийлүүлсэн хугацаа')
	delay_day = fields.Integer(string='Хоцролт /хоног/')
	delay_percent = fields.Integer(string='Хоцролт %', compute='_compute_all_field')
	quality_qty = fields.Integer(string='Чанартай ирсэн тоо хэмжээ')
	state = fields.Char(string='Төлөв', compute='_compute_all_field', store=False)
	dot_percent = fields.Integer(string='DOT %', compute='_compute_all_field')
	doq_percent = fields.Integer(string='DOQ %', compute='_compute_all_field')
	dif_percent = fields.Integer(string='DIF %', compute='_compute_all_field')
	sifot_percent = fields.Integer(string='SIFOT %', compute='_compute_all_field')

	@api.depends('deliver_day', 'delivered_day', 'delay_day')
	def _compute_all_field(self):
		for item in self:
			sum_received_qty = sum([line.qty_received for line in item.po_id.order_line])
			sum_ordered_qty = sum([line.product_uom_qty for line in item.po_id.order_line])
			item.delay_percent = (item.delay_day / item.deliver_day) * 100
			if item.delay_percent <= 10 and item.delay_percent >=-10:
				item.state = 'Хэвийн'
			elif item.delay_percent > 10:
				item.state = 'Хоцорсон'
			else:
				item.state = 'Түрүүлсэн'
			item.dot_percent = (item.delivered_day / item.deliver_day) * 100
			item.doq_percent = ((sum_received_qty - item.quality_qty) / sum_ordered_qty) * 100
			item.dif_percent = (sum_received_qty / sum_ordered_qty) * 100
			item.sifot_percent = item.dot_percent * item.doq_percent * item.dif_percent

	def _select(self):
		return """
			SELECT
				(po.id::text||po.company_id::text)::bigint as id,
				po.id as po_id,
				po.partner_id as partner_id,
				po.delivered_date as delivered_date,
				po.deliver_day as deliver_day,
				po.delivered_day as delivered_day,
				po.delivered_day - po.deliver_day as delay_day,
				po.quality_qty as quality_qty
		"""

	def _from(self):
		return """
			FROM purchase_order AS po
		"""

	def _where(self):
		return """
			WHERE po.delivered_date is not null
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
				CREATE OR REPLACE VIEW %s AS (%s %s %s)
			""" % (self._table, self._select(), self._from(), self._where())
		)