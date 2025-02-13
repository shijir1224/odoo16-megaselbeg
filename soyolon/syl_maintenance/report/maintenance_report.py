from odoo import fields, models
import time
import xlsxwriter
from odoo.exceptions import UserError
from io import BytesIO
import base64

fmt = '%Y-%m-%d'


class MaintenanceReport(models.TransientModel):
	_name = "maintenance.report"
	_description = "Maintenance Report"
	branch_ids = fields.Many2many('res.branch', 'maintenance_report_reports_branch_rel', 'branch_id', string='Төсөл')
	date_start = fields.Date(string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'), required=True)
	date_end = fields.Date(string=u'Дуусах огноо', required=True)

	def export_report(self):
		if self.date_start and self.date_end:
			leads = self.env['maintenance.workorder'].search([('date','>=',self.date_start),('date','<=',self.date_end)])
			print('aaaaaaaaaaaaa',leads)
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Тоног төхөөрөмжийн зогсолтын тайлан'+str(self.date_start)+'-'+str(self.date_end)+'.xlsx'
			team_ids = leads.mapped('equipment_id')
			print('bbbbbbbbbbbbbbbbbbbb', team_ids, )
			h1 = workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header = workbook.add_format({'bold': 1})
			header.set_text_wrap()
			header.set_font_size(9)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#5fa1a5')

			header_wrap = workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#99ccff')

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

			contest_right = workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)

			contest_center = workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(12)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sub_total_90 = workbook.add_format({'bold': 1})
			sub_total_90.set_text_wrap()
			sub_total_90.set_font_size(9)
			sub_total_90.set_align('center')
			sub_total_90.set_align('vcenter')
			sub_total_90.set_border(style=1)
			sub_total_90.set_bg_color('#F7EE5E')
			sub_total_90.set_rotation(90)
