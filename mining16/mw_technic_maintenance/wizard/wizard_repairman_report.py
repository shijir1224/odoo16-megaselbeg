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

class WizardRepairmanReport(models.TransientModel):
	_name = "wizard.repairman.report"
	_description = "wizard.repairman.report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	employee_id = fields.Many2one('hr.employee', string=u'Ажилтан',)
	partner_id = fields.Many2one('res.partner', string=u'Ажилтан',)
	date_type = fields.Selection([('1','WO огноо'), ('2','Цагийн хуудсын огноо')], string=u'Огнооны төрөл',	required=True, default='1')

	def see_report(self):
		if self.date_start <= self.date_end:
			context = dict(self._context)
			# GET views ID
			# mod_obj = self.env['ir.model.data']
			# search_res = mod_obj._xmlid_lookup('mw_technic_maintenance', 'repaiman_pivot_report_search')
			# search_id = search_res and search_res[1] or False
			# pivot_res = mod_obj._xmlid_lookup('mw_technic_maintenance', 'repaiman_pivot_report_pivot')
			# pivot_id = pivot_res and pivot_res[1] or False
			
			if self.date_type=='1':
				domain = [('date','>=',self.date_start.strftime("%Y-%m-%d")),
					  ('date','<=',self.date_end.strftime("%Y-%m-%d"))]
			else:
				domain = [('date_start','>=',self.date_start.strftime("%Y-%m-%d")),
						('date_end','<=',self.date_end.strftime("%Y-%m-%d"))]

			if self.partner_id:
				domain.append(('emp_partner_id','=',self.partner_id.id))

			# return {
			# 	'name': ('Report'),
			# 	'view_type': 'form',
			# 	'view_mode': 'pivot',
			# 	'res_model': 'repaiman.pivot.report',
			# 	'view_id': False,
			# 	'views': [(pivot_id, 'pivot')],
			# 	'search_view_id': search_id,
			# 	'domain': domain,
			# 	'type': 'ir.actions.act_window',
			# 	'target': 'current',
			# 	'context': context
			# }
			action = self.env.ref('mw_technic_maintenance.action_repaiman_pivot_report_view')
			vals = action.read()[0]
			vals['domain'] = domain
			vals['context'] = {}
			return vals


	def export_report(self):
		woss = ''
		wos = ''
		if not self.partner_id:
			# raise UserError(_(u'Засварчныг сонгоно уу!'))
			woss = self.env['maintenance.workorder'].sudo().search(
				[('date_required','>=',self.date_start),
				('date_required','<=',self.date_end),
				('state','in',['done','closed'])
				], order='date_required')
			print('\n\nwOS-----------',len(woss))
		else:
			wos = self.env['maintenance.workorder'].sudo().search(
				[('date_required','>=',self.date_start),
				('date_required','<=',self.date_end),
				('state','in',['done','closed']),
				('employee_timesheet_lines.emp_partner_id','=',self.partner_id.id)
				], order='date_required')
			print('\n\nwOS-----------',len(wos))
		if woss:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)

			file_name = 'Repairman report.xlsx'

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
			worksheet.write(1,3, u"Засварчны ажлын тайлан", h1)
			worksheet.write(2,0, u"Тайлант хугацаа: " + datetime.strftime(self.date_start,'%Y-%m-%d') +" ~ "+  datetime.strftime(self.date_end,'%Y-%m-%d'), contest_left0)

			# TABLE HEADER
			row = 6
			worksheet.set_row(row, 26)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column('A:A', 5)
			worksheet.write(row, 1, u"Огноо", header_wrap)
			worksheet.set_column('B:B', 12)
			worksheet.write(row, 2, u"WorkOrder", header_wrap)
			worksheet.set_column('C:C', 18)
			worksheet.write(row, 3, u"Эвдрэлийн тухай", header_wrap)
			worksheet.set_column('D:D', 20)
			worksheet.write(row, 4, u"Засварчид", header_wrap)
			worksheet.set_column('E:E', 20)
			worksheet.write(row, 5, u"Үнэлгээ", header_wrap)
			worksheet.set_column('F:F', 10)
			worksheet.write(row, 6, u"Зарцуулсан цаг", header_wrap)
			worksheet.set_column('G:G', 10)
			worksheet.write(row, 7, u"Засварын төрөл", header_wrap)
			worksheet.set_column('H:H', 20)
			worksheet.write(row, 8, u"Эвдрэлийн шалтгаан", header_wrap)
			worksheet.set_column('I:I', 20)
			worksheet.write(row, 9, u"Эвдрэлийн төрөл", header_wrap)
			worksheet.set_column('J:J', 20)
			worksheet.write(row, 10, u"Гүйцэтгэлийн тайлбар", header_wrap)
			worksheet.set_column('K:K', 22)
			worksheet.freeze_panes(7, 0)
			row += 1

			# Data
			number = 1
			total_time = 0
			for line in woss:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required.strftime("%Y-%m-%d"), contest_center)
				worksheet.write(row, 2, line.name or '-', contest_left)
				worksheet.write(row, 3, line.description, contest_left)

				spend_time = sum(line.employee_timesheet_lines.mapped('spend_time'))
				other_repairman =','.join(line.employee_timesheet_lines.filtered(lambda l: l.emp_partner_id.id != self.partner_id.id).mapped('emp_partner_id.name'))

				worksheet.write(row, 4, other_repairman or '', contest_left)
				worksheet.write(row, 5, line.workorder_rate, contest_center)
				worksheet.write(row, 6, round(spend_time,2), number_right)
				worksheet.write(row, 7, dict(line._fields['maintenance_type'].selection).get(line.maintenance_type), number_right)
				worksheet.write(row, 8, line.damaged_reason_id.name, contest_left)
				worksheet.write(row, 9, line.damaged_type_id.name, contest_left)
				worksheet.write(row, 10, line.performance_description, contest_left)
				row += 1
				number += 1
				total_time += spend_time

			# Fooder
			worksheet.write(row+1,1, u"Нийт зарцуулсан цаг: " + str(round(total_time,2)), contest_left0)
			worksheet.write(row+3,1, u"Танилцсан ажилтан: . . . . . . . . . . . . . . . .", contest_left0)
			worksheet.write(row+4,1, u"Тайлан гаргасан: . . . . . . . . . . . . . . . . .", contest_left0)
			workbook.close()

			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})


			return {
				'type' : 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				'target': 'new',
			}
		elif wos:
			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)

			file_name = 'Repairman report.xlsx'

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
			worksheet.write(1,3, u"Засварчны ажлын тайлан", h1)
			worksheet.write(2,0, u"Засварчны нэр: " + self.partner_id.name, contest_left0)
			print('=========================================', self.partner_id.job_id.name)
			worksheet.write(3,0, u"Албан тушаал: " + self.partner_id.job_id.name, contest_left0)
			worksheet.write(4,0, u"Тайлант хугацаа: " + datetime.strftime(self.date_start,'%Y-%m-%d') +" ~ "+  datetime.strftime(self.date_end,'%Y-%m-%d'), contest_left0)

			# TABLE HEADER
			row = 6
			worksheet.set_row(row, 26)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column('A:A', 5)
			worksheet.write(row, 1, u"Огноо", header_wrap)
			worksheet.set_column('B:B', 12)
			worksheet.write(row, 2, u"WorkOrder", header_wrap)
			worksheet.set_column('C:C', 18)
			worksheet.write(row, 3, u"Эвдрэлийн тухай", header_wrap)
			worksheet.set_column('D:D', 20)
			worksheet.write(row, 4, u"Хамтарсан засварчин", header_wrap)
			worksheet.set_column('E:E', 20)
			worksheet.write(row, 5, u"Үнэлгээ", header_wrap)
			worksheet.set_column('F:F', 10)
			worksheet.write(row, 6, u"Зарцуулсан цаг", header_wrap)
			worksheet.set_column('G:G', 10)
			worksheet.write(row, 7, u"Эвдрэлийн шалтгаан", header_wrap)
			worksheet.set_column('H:H', 20)
			worksheet.write(row, 8, u"Эвдрэлийн төрөл", header_wrap)
			worksheet.set_column('I:I', 20)
			worksheet.write(row, 9, u"Гүйцэтгэлийн тайлбар", header_wrap)
			worksheet.set_column('J:J', 22)
			worksheet.freeze_panes(7, 0)
			row += 1

			# Data
			number = 1
			total_time = 0
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name or '-', contest_left)
				worksheet.write(row, 3, line.description, contest_left)

				spend_time = sum(line.employee_timesheet_lines.filtered(lambda l: l.emp_partner_id.id == self.partner_id.id).mapped('spend_time'))
				other_repairman =','.join(line.employee_timesheet_lines.filtered(lambda l: l.emp_partner_id.id != self.partner_id.id).mapped('emp_partner_id.name'))

				worksheet.write(row, 4, other_repairman or '', contest_left)
				worksheet.write(row, 5, line.workorder_rate, contest_center)
				worksheet.write(row, 6, round(spend_time,2), number_right)
				worksheet.write(row, 7, line.damaged_reason_id.name, contest_left)
				worksheet.write(row, 8, line.damaged_type_id.name, contest_left)
				worksheet.write(row, 9, line.performance_description, contest_left)
				row += 1
				number += 1
				total_time += spend_time

			# Fooder
			worksheet.write(row+1,1, u"Нийт зарцуулсан цаг: " + str(round(total_time,2)), contest_left0)
			worksheet.write(row+3,1, u"Танилцсан ажилтан: . . . . . . . . . . . . . . . .", contest_left0)
			worksheet.write(row+4,1, u"Тайлан гаргасан: . . . . . . . . . . . . . . . . .", contest_left0)
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



