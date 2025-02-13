# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import time
import xlsxwriter
from io import BytesIO
import base64

class WizardOilSampleReport(models.TransientModel):
	_name = "wizard.oil.sample.report"
	_description = "wizard.oil.sample.report"

	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	technic_id = fields.Many2one('technic.equipment', string=u'Техник')
	technic_ids = fields.Many2many('technic.equipment', string=u'Техникүүд')
	damaged_type_id = fields.Many2one('maintenance.damaged.type', u'Дээж авсан систем', domain=[('is_oil_sample','=',True)])
	damaged_type_ids = fields.Many2one('maintenance.damaged.type', u'Дээж авсан системүүд', domain=[('is_oil_sample','=',True)])
	response_type = fields.Selection([
		('no_action_required','No action required'),
		('monitor_compartment','Monitor compartment'),
		('action_required','Action required')], string=u'Хариуны төрөл')

	state = fields.Selection([
		('draft', u'Ноорог'),
		('sent_sample', u'Дээж илгээсэн'),
		('received_response', u'Хариу ирсэн'),
		('closed', u'Хаагдсан'),], string=u'Төлөв')

	def see_report(self):
		if self.date_start and self.date_end:
			# GET views ID
			mod_obj = self.env['ir.model.data']
			search_res = mod_obj._xmlid_lookup('mw_technic_maintenance.oil_sample_pivot_report_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup('mw_technic_maintenance.oil_sample_pivot_report_pivot')
			pivot_id = pivot_res and pivot_res[2] or False

			domain = [('date_sample','>=',self.date_start.strftime("%Y-%m-%d")),
					  ('date_sample','<=',self.date_end.strftime("%Y-%m-%d"))]

			if self.technic_id:
				domain.append(('technic_id','=',self.technic_id.id))

			if self.technic_ids:
				domain.append((('technic_id','in',self.technic_ids.ids)))

			if self.damaged_type_id:
				domain.append(('damaged_type_id','=',self.damaged_type_id.id))

			if self.response_type:
				domain.append(('response_type','=',self.response_type))

			if self.state:
				domain.append(('state','>=',self.state))

			return {
				'name': ('Report'),
				'view_mode': 'pivot',
				'res_model': 'oil.sample.pivot.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
			}

	# Татах
	def export_report(self):
		if self.date_start <= self.date_end:
			oils = self.env['maintenance.oil.sample'].sudo().search(
				[('date_sample','>=',self.date_start),
				 ('date_sample','<=',self.date_end),
				 ('state','!=','draft'),
				], order='name, date_sample, technic_id')
			if not oils:
				raise UserError(_(u'Бичлэг олдсонгүй!'))

			output = BytesIO()
			workbook = xlsxwriter.Workbook(output)
			file_name = 'Oil sample report.xlsx'

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
			worksheet.write(0,3, u"Тосны дээжийн тайлан", h1)
			worksheet.write(1,0, u"Тайлант хугацаа: " + datetime.strftime(self.date_start, '%Y-%m-%d') +" ~ "+ datetime.strftime(self.date_end, '%Y-%m-%d'), contest_left0)

			# TABLE HEADER
			row = 2
			worksheet.set_row(row, 26)
			worksheet.write(row, 0, u"№", header)
			worksheet.set_column('A:A', 3)
			worksheet.write(row, 1, u"Дугаар", header_wrap)
			worksheet.set_column('B:B', 12)
			worksheet.write(row, 2, u"Модель", header_wrap)
			worksheet.set_column('C:C', 30)
			worksheet.write(row, 3, u"Парк дугаар", header_wrap)
			worksheet.set_column('D:D', 10)
			worksheet.write(row, 4, u"Сериал дугаар", header_wrap)
			worksheet.set_column('E:E', 10)
			worksheet.write(row, 5, u"компонентийн төрөл", header_wrap)
			worksheet.set_column('F:F', 20)
			worksheet.write(row, 6, u"Компонент", header_wrap)
			worksheet.set_column('G:G', 20)
			worksheet.write(row, 7, u"Эд ангиийн сериал дугаар", header_wrap)
			worksheet.set_column('H:H', 20)
			worksheet.write(row, 8, u"Эд ангиийн дугаар", header_wrap)
			worksheet.set_column('I:I', 20)
			worksheet.write(row, 9, u"Дээж авсан огноо", header_wrap)
			worksheet.set_column('J:J', 10)
			worksheet.write(row, 10, u"Мото цаг", header_wrap)
			worksheet.set_column('K:K', 10)
			worksheet.write(row, 11, u"Хаанаас авсан", header_wrap)
			worksheet.set_column('L:L', 15)
			worksheet.write(row, 12, u"Тосны брэнд", header_wrap)
			worksheet.set_column('M:M', 10)
			worksheet.write(row, 13, u"Тосны төрөл", header_wrap)
			worksheet.set_column('N:N', 30)
			worksheet.write(row, 14, u"WO дугаар", header_wrap)
			worksheet.set_column('O:O', 10)
			worksheet.write(row, 15, u"Хариу ирсэн огноо", header_wrap)
			worksheet.set_column('P:P', 10)
			worksheet.write(row, 16, u"Хариу", header_wrap)
			worksheet.set_column('Q:Q', 18)
			worksheet.write(row, 17, u"Хариу тайлбар English, Монгол", header_wrap)
			worksheet.set_column('R:R', 30)
			worksheet.write(row, 18, u"Авсан арга хэмжээ", header_wrap)
			worksheet.set_column('S:S', 20)
			worksheet.write(row, 19, u"Тайлбар", header_wrap)
			worksheet.set_column('T:T', 20)
			worksheet.freeze_panes(3, 0)
			row += 1

			# Data
			number = 1
			total_time = 0
			for line in oils:
				if self.technic_id:
					if line.technic_id != self.technic_id:
						continue
				if self.technic_ids:
					if line.technic_id not in self.technic_ids:
						continue
				if self.damaged_type_id:
					if line.damaged_type_id != self.damaged_type_id:
						continue
				if self.response_type:
					if line.response_type != self.response_type:
						continue
				if self.state:
					if line.state != self.state:
						continue
				date_response = ''
				date_sample = ''
				if line.date_sample:
					date_sample = line.date_sample.strftime('%Y-%m-%d')
				if line.date_response:
					date_response = line.date_response.strftime('%Y-%m-%d %H:%M:%S')
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.name, contest_center)
				worksheet.write(row, 2, line.technic_id.model_id.name, contest_center)
				worksheet.write(row, 3, line.technic_id.park_number, contest_left)
				worksheet.write(row, 4, line.technic_id.vin_number, contest_left)
				worksheet.write(row, 5, dict(line._fields['comportment_system'].selection).get(line.comportment_system), contest_left)
				worksheet.write(row, 6, line.component_id.name or '', contest_left)
				worksheet.write(row, 7, line.component_serial or '', contest_left)
				worksheet.write(row, 8, line.component_part_number or '', contest_left)
				worksheet.write(row, 9, date_sample, contest_center)
				worksheet.write(row, 10, line.technic_odometer, contest_right)
				worksheet.write(row, 11, line.damaged_type_id.name, contest_left)
				if line.oil_type_id.brand_id:
					worksheet.write(row, 12, line.oil_type_id.brand_id.name, contest_left)
				else:
					worksheet.write(row, 12, '', contest_left)
				worksheet.write(row, 13, line.oil_type_id.name, contest_left)
				worksheet.write(row, 14, line.workorder_id.name, contest_center)
				worksheet.write(row, 15, date_response, contest_center)
				worksheet.write(row, 16, dict(line._fields['response_type'].selection).get(line.response_type), contest_center)
				worksheet.write(row, 17, line.response_description, contest_left)
				worksheet.write(row, 18, line.action_description, contest_left)
				worksheet.write(row, 19, line.description, contest_left)
				row += 1
				number += 1

			workbook.close()
			out = base64.encodebytes(output.getvalue())
			excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

			return {
				 'type' : 'ir.actions.act_url',
				 'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
				 'target': 'new',
			}







