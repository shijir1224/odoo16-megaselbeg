# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date, datetime
from io import BytesIO
import base64
import xlsxwriter
import time


class WorkplaceInspectionReport(models.TransientModel):
	_name ='workplace.inspection.report'
	_description = 'ХАБ Ажлын байрны үзлэг тайлан'


	branch_ids = fields.Many2many('res.branch', 'workplace_inspection_report_wizard_branch_rel', 'report_id', 'branch_id', string='Төсөл')
	date_start = fields.Date('Эхлэх огноо', required=True,  default=time.strftime('%Y-%m-01'))
	date_end = fields.Date('Дуусах огноо', default=fields.Date.context_today, required=True)

	def download_report(self):
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Ажлын байрны үзлэг.xlsx'

		header = workbook.add_format({'bold': 1})
		header.set_font_size(14)
		header.set_font('Times new roman')
		header.set_align('center')
		header.set_align('vcenter')
		header.set_border(style=1)

		contest_center = workbook.add_format()
		contest_center.set_text_wrap()
		contest_center.set_font_size(9)
		contest_center.set_font('Times new roman')
		contest_center.set_align('center')
		contest_center.set_align('vcenter')
		contest_center.set_border(style=1)

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_font('Times new roman')
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)
		
		contest_left_bold = workbook.add_format({'bold': 1})
		contest_left_bold.set_text_wrap()
		contest_left_bold.set_font_size(9)
		contest_left_bold.set_font('Times new roman')
		contest_left_bold.set_align('left')
		contest_left_bold.set_align('vcenter')
		contest_left_bold.set_border(style=1)

		contest_center_bold = workbook.add_format({'bold': 1})
		contest_center_bold.set_text_wrap()
		contest_center_bold.set_font_size(9)
		contest_center_bold.set_font('Times new roman')
		contest_center_bold.set_align('center')
		contest_center_bold.set_align('vcenter')
		contest_center_bold.set_border(style=1)
		contest_center_bold.set_bg_color('#d3ebe7')

		contest_sub_center_bold = workbook.add_format({'bold': 1})
		contest_sub_center_bold.set_text_wrap()
		contest_sub_center_bold.set_font_size(9)
		contest_sub_center_bold.set_font('Times new roman')
		contest_sub_center_bold.set_align('center')
		contest_sub_center_bold.set_align('vcenter')
		contest_sub_center_bold.set_border(style=1)
		contest_sub_center_bold.set_bg_color('#f5bf6e')

		sum_contest_center_bold = workbook.add_format({'bold': 1})
		sum_contest_center_bold.set_text_wrap()
		sum_contest_center_bold.set_font_size(9)
		sum_contest_center_bold.set_font('Times new roman')
		sum_contest_center_bold.set_align('center')
		sum_contest_center_bold.set_align('vcenter')

		sheet = workbook.add_worksheet(u'Үзлэгийн мэдээ')
		row = 0
		sheet.merge_range(row, 0, row, 12, u'АЖЛЫН БАЙРНЫ ҮЗЛЭГ ШАЛГАЛТ', header)
		sheet.freeze_panes(2, 0)

		# HEADER
		row += 1
		sheet.merge_range(row, 0, row, 6, u'Аюул, зөрчлийн илрүүлэлт', contest_sub_center_bold)
		sheet.write(row+1, 0, u'№', contest_center_bold)
		sheet.write(row+1, 1, u'Үзлэгийн дугаар', contest_center_bold)
		sheet.write(row+1, 2, u'Салбар', contest_center_bold)
		sheet.write(row+1, 3, u'Үүсгэсэн огноо', contest_center_bold)
		sheet.write(row+1, 4, u'Шалгалт хийсэн байршил', contest_center_bold)
		sheet.write(row+1, 5, u'Аюул', contest_center_bold)
		sheet.write(row+1, 6, u'Зөрчил', contest_center_bold)
		sheet.merge_range(row, 7, row, 10, u'Арилгах арга хэмжээний төлөвлөгөө, даалгавар', contest_sub_center_bold)
		sheet.write(row+1, 7, u'Авах арга хэмжээ', contest_center_bold)
		sheet.write(row+1, 8, u'Дуусах хугацаа', contest_center_bold)
		sheet.write(row+1, 9, u'Хариуцагч овог нэр', contest_center_bold)
		sheet.write(row+1, 10, u'Хариуцагч албан тушаал', contest_center_bold)
		sheet.merge_range(row, 11, row, 13, u'Биелэлт', contest_sub_center_bold)
		sheet.write(row+1, 11, u'Авагдсан арга хэмжээ', contest_center_bold)
		sheet.write(row+1, 12, u'Засагдсан огноо', contest_center_bold)
		sheet.write(row+1, 13, u'Зассан ажилтан', contest_center_bold)
		sheet.merge_range(row, 14, row, 16, u'Үзлэгийн багийн гишүүд', contest_sub_center_bold)
		sheet.write(row+1, 14, u'Багийн ахлагч', contest_center_bold)
		sheet.write(row+1, 15, u'Багийн гишүүд', contest_center_bold)
		sheet.write(row+1, 16, u'Гадны гишүүд', contest_center_bold)
		row += 1

		domains=[
			('workplace_is_id.date','>=',self.date_start),
			('workplace_is_id.date','<=',self.date_end),
		]
		if self.branch_ids:
			domains.append(('workplace_is_id.branch_id', 'in', self.branch_ids.ids))
		inspections = self.env['hse.workplace.inspection.line'].sudo().search(domains)
		for inspection in inspections:
			sheet.write(row+1, 0, row, contest_center)
			sheet.write(row+1, 1, inspection.workplace_is_id.name if inspection.workplace_is_id.name else '', contest_center)
			sheet.write(row+1, 2, inspection.workplace_is_id.branch_id.name if inspection.workplace_is_id.branch_id else '', contest_center)
			sheet.write(row+1, 3, inspection.workplace_is_id.date.strftime('%Y-%m-%d') if inspection.location_id else '', contest_center)
			sheet.write(row+1, 4, inspection.location_id.name if inspection.location_id else '', contest_center)
			sheet.write(row+1, 5, inspection.hazard_zorchil if inspection.hazard_zorchil else '', contest_center)
			sheet.write(row+1, 6, dict(inspection._fields['hazard_rating'].selection).get(inspection.hazard_rating), contest_center)
			sheet.write(row+1, 7, inspection.corrective_action_instructions if inspection.corrective_action_instructions else '', contest_center)
			sheet.write(row+1, 8, inspection.when_start.strftime('%Y-%m-%d') if inspection.when_start else '', contest_center)
			sheet.write(row+1, 9, inspection.taken_employee_id.name if inspection.taken_employee_id else '', contest_center)
			sheet.write(row+1, 10, inspection.job_id.name if inspection.job_id else '', contest_center)
			sheet.write(row+1, 11, inspection.corrective_action_taken if inspection.corrective_action_taken else '', contest_center)
			sheet.write(row+1, 12, inspection.repair_date.strftime('%Y-%m-%d') if inspection.repair_date else '', contest_center)
			sheet.write(row+1, 13, inspection.repair_user_id.name if inspection.repair_user_id else '', contest_center)
			sheet.write(row+1, 14, inspection.workplace_is_id.captian_id.name if inspection.workplace_is_id.captian_id else '', contest_center)
			sheet.write(row+1, 15, ','.join(inspection.workplace_is_id.employee_ids.mapped('name')), contest_center)
			sheet.write(row+1, 16, ','.join(inspection.workplace_is_id.partner_ids.mapped('name')), contest_center)
			row += 1
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

		return {
			'type': 'ir.actions.act_url',
			'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s" % (excel_id.id, excel_id.name),
			'target': 'new',
		}




