from odoo import api, fields, models, tools, _
from io import BytesIO
import base64
import xlsxwriter
from odoo.exceptions import UserError

class ProductQualityReport(models.Model):
	_name = 'stock.quality.report'
	_description = 'Шаардлага хангаагүй барааны тайлан'
	_auto = False

	product_id = fields.Many2one('product.product', string='Бараа', readonly=True)
	po_id = fields.Many2one('purchase.order', string='Худалдан авалт', readonly=True)
	picking_id = fields.Many2one('stock.picking', string='Дотоод хөдөлгөөний дугаар', readonly=True)
	date_done = fields.Date(string='Хүлээн авсан огноо')
	is_qualified = fields.Selection([('yes','Тийм'), ('no','Үгүй')], string='Шаардлага хангасан эсэх')
	no_quality = fields.Char(string='Тайлбар')
	in_coming_picking_id = fields.Many2one('stock.picking', string='Эх үүсвэр баримт', readonly=True)
	po_id = fields.Many2one(related='in_coming_picking_id.purchase_id', string='ХА дугаар', readonly=True)
	po_user_id = fields.Many2one(related='po_id.user_id', string='ХА ажилтан', readonly=True)
	is_sent = fields.Boolean(string='Мэдэгдэл очсон эсэх', readonly=True)

	def cron_quality_notification(self):
		stock_quality_obj = self.env['stock.quality.report'].search([('is_sent','=',False)])
		if stock_quality_obj:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Шаардлага хангаагүй барааны тайлан.xlsx'
			sheet = workbook.add_worksheet(u'sheet')

			contest_center_bg = workbook.add_format()
			contest_center_bg.set_text_wrap()
			contest_center_bg.set_font_size(10)
			contest_center_bg.set_align('center')
			contest_center_bg.set_align('vcenter')
			contest_center_bg.set_border(style=1)
			contest_center_bg.set_font_name('Times new roman')
			contest_center_bg.set_bg_color('#EE9A4D')

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_font('Times new roman')
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			row = 0
			sheet.set_row(row, 30)
			sheet.write(row, 0, u'Бараа', contest_center_bg)
			sheet.write(row, 1, u'Эх үүсвэр баримт', contest_center_bg)
			sheet.write(row, 2, u'Дотоод хөдөлгөөний дугаар', contest_center_bg)
			sheet.write(row, 3, u'Хүлээн авсан огноо', contest_center_bg)
			sheet.write(row, 4, u'ХА дугаар', contest_center_bg)
			sheet.write(row, 5, u'ХА ажилтан', contest_center_bg)
			sheet.write(row, 6, u'Шаардлага хангасан эсэх', contest_center_bg)
			sheet.write(row, 7, u'Тайлбар', contest_center_bg)
			sheet.set_column('A:H', 20)
			sheet.freeze_panes(1, 0)

			for item in stock_quality_obj:
				row += 1
				sheet.write(row, 0, u'%s' %(item.product_id.default_code or ''), contest_center)
				sheet.write(row, 1, u'%s' %(item.in_coming_picking_id.name or ''), contest_center)
				sheet.write(row, 2, u'%s' %(item.picking_id.name or ''), contest_center)
				sheet.write(row, 3, u'%s' %(item.date_done or ''), contest_center)
				sheet.write(row, 4, u'%s' %(item.po_id.name or ''), contest_center)
				sheet.write(row, 5, u'%s' %(item.po_user_id.name or ''), contest_center)
				sheet.write(row, 6, u'%s' %(dict(item._fields['is_qualified'].selection).get(item.is_qualified) or ''), contest_center)
				sheet.write(row, 7, u'%s' %(item.no_quality or ''), contest_center)

				no_sent_obj = self.env['stock.move.line'].search([('picking_id','=',item.picking_id.id),('product_id','=',item.product_id.id),('is_qualified','=','no')])

				if no_sent_obj:
					no_sent_obj.is_sent = True

			workbook.close()
			out = base64.encodebytes(output.getvalue())

			user_ids = self.env['stock.quality.notification'].search([('id','!=',False)], limit=1).mapped('user_ids')
			for user in user_ids:
				if user.partner_id:
					# Create attachment
					html = u'<b style="color:red">Шаардлага хангаагүй барааны тайлан</b><br/>'
					values = {
						'name':file_name,
						'res_model':'mail.message',
						'type':'binary',
						'datas':out,
						'public': True
					}
					base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
					attach_id = self.env['ir.attachment'].sudo().create(values)
					html += u"""<b><a target="_blank" href=%sweb/content/%s>%s</a></b>"""% (base_url,attach_id.id,file_name)
					self.env.user.send_emails(partners=[user.partner_id], subject='Шаардлага хангаагүй барааны тайлан', body=html, attachment_ids=[attach_id.id])

	def _select(self):
		return """
			SELECT
				(sml.id::text||sml.company_id::text)::bigint as id,
				sml.product_id as product_id,
				sp.id as picking_id,
				sp.date_done as date_done,
				sp.in_coming_picking_id as in_coming_picking_id,
				sml.is_qualified as is_qualified,
				sml.no_quality as no_quality,
				sml.is_sent as is_sent
		"""

	def _from(self):
		return """
			FROM stock_move_line AS sml 
				LEFT JOIN stock_picking sp ON (sp.id = sml.picking_id)
		"""
	
	def _where(self):
		return """
			WHERE
				sml.is_qualified = 'no'
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
				CREATE OR REPLACE VIEW %s AS (%s %s %s)
			""" % (self._table, self._select(), self._from(), self._where())
		)