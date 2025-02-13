# -*- coding: utf-8 -*-
from datetime import datetime
# from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import time
from odoo import api, models, fields, _

import xlwt
from xlwt import *
import base64
# from report_excel_cell_styles import ReportExcelCellStyles
from odoo.addons.account_financial_report.report.report_excel_cell_styles import ReportExcelCellStyles

class ConsumableStandardReportData(models.TransientModel):

	_name = 'consumable.standard.data'
	_description = "consumable standard data"
	_rec_name = 'asset_id'

	wizard_id = fields.Many2one(
		comodel_name='consumable.report.standard.ledger',
		ondelete='cascade',
		index=True
	)

	report_id = fields.Many2one(
		comodel_name='consumable.report.standard.ledger.report',
		ondelete='cascade',
		index=True
	)

	report_obj_id = fields.Many2one(
		comodel_name='consumable.report.standard.object',
		ondelete='cascade',
		index=True
	)

	asset_id = fields.Many2one(
		'product.product',
		index=True
	)

	qty = fields.Float(digits=(16, 2))
	date = fields.Date(digits=(16, 2))
	initial_value = fields.Float(digits=(16, 2))
	income_value = fields.Float(digits=(16, 2))
	capital_value = fields.Float(digits=(16, 2))
	expense_value = fields.Float(digits=(16, 2))
	final_value = fields.Float(digits=(16, 2))

	initial_depr = fields.Float(digits=(16, 2))
	income_depr = fields.Float(digits=(16, 2))
	capital_depr = fields.Float(digits=(16, 2))
	expense_depr = fields.Float(digits=(16, 2))
	final_depr = fields.Float(digits=(16, 2))

	owner = fields.Char('owner')
	branch = fields.Char('branch')
	serial = fields.Char('Serial')
	number = fields.Char('Number')

	department = fields.Char('department')
	job = fields.Char('job')
	internal_code = fields.Char('internal_code')
	doc_number = fields.Char('doc_number')

	type = fields.Char('type')
	category = fields.Char('category')
	state = fields.Char('state')

class ConsumableStandardExcel(models.AbstractModel):
#     _name = 'report.consumable_standard_report.standard_excel'
	_name='report.mw_consume_order.standard_excel'
	_description = "report mw consume order standard excel"
	_inherit = 'report.report_xlsx.abstract'

	def generate_xlsx_report(self, workbook, data, wizard):

		num_format = '# ##0,00_);(# ##0,00)'
		bold = workbook.add_format({'bold': True})
		middle = workbook.add_format({'bold': True, 'top': 1})
		left = workbook.add_format({'left': 1, 'top': 1, 'bold': True})
		right = workbook.add_format({'right': 1, 'top': 1})
		top = workbook.add_format({'top': 1})
		currency_format = workbook.add_format({'num_format': num_format})
		c_middle = workbook.add_format({'bold': True, 'top': 1, 'num_format': num_format})
		report_format = workbook.add_format({'font_size': 24})
		rounding = self.env.user.company_id.currency_id.decimal_places or 2
		# lang_code = self.env.user.lang or 'en_US'
		# lang_id = self.env['res.lang']._lang_get(lang_code)
		date_format = '%Y-%m-%d'

		report = wizard
		print('wizard zaaawal olno', wizard)
		def _get_data_float(data):
			if data == None or data == False:
				return 0.0
			else:
				return round(data,2) + 0.0

		def get_date_format(date):
			if date:
				# date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
				date = date.strftime(date_format)
				
			return date

		def _header_sheet(sheet):
			sheet.write(0, 4, u'АБХМ дэлгэрэнгүй тайлан', report_format)
			sheet.write(2, 0, _(u'Компани:'), bold)
			sheet.write(3, 0, wizard.company_id.name,)
			sheet.write(4, 0, _('Print on %s') % time.strftime('%Y-%m-%d'))

			sheet.write(2, 2, _(u'Эхлэх огноо : %s ') % wizard.date_from if wizard.date_from else '')
			sheet.write(3, 2, _(u'Дуусах огноо : %s ') % wizard.date_to if wizard.date_to else '')

		if True:
			if report.old_temp:
				format_name = {
					'font_name': 'Times New Roman',
					'font_size': 14,
					'bold': True,
					'align': 'center',
					'valign': 'vcenter'
				}
				# create formats
				format_content_text_footer = {
				'font_name': 'Times New Roman',
				'font_size': 10,
				'align': 'vcenter',
				'valign': 'vcenter',
				}
				format_content_right = {
				'font_name': 'Times New Roman',
				'font_size': 9,
				'align': 'right',
				'valign': 'vcenter',
				'border': 1,
				'num_format': '#,##0.00'
				}
				format_group_center = {
				'font_name': 'Times New Roman',
				'font_size': 10,
				'align': 'center',
				'valign': 'vcenter',
				'border': 1,
				}
				format_group = {
				'font_name': 'Times New Roman',
				'font_size': 10,
				'bold': True,
				'align': 'center',
				'valign': 'vcenter',
				'border': 1,
				'bg_color': '#CFE7F5',
				'num_format': '#,##0.00'
				}
				format_group_center = workbook.add_format(format_group_center)
				format_name = workbook.add_format(format_name)
				format_content_text_footer = workbook.add_format(format_content_text_footer)
				format_filter = workbook.add_format(ReportExcelCellStyles.format_filter)
				format_title = workbook.add_format(ReportExcelCellStyles.format_title)
				format_group_right = workbook.add_format(ReportExcelCellStyles.format_group_right)
				format_group_float = workbook.add_format(ReportExcelCellStyles.format_group_float)
				format_group_left = workbook.add_format(ReportExcelCellStyles.format_group_left)
				format_content_text = workbook.add_format(ReportExcelCellStyles.format_content_text)
				format_content_number = workbook.add_format(ReportExcelCellStyles.format_content_number)
				format_content_float = workbook.add_format(ReportExcelCellStyles.format_content_float)
				format_content_center = workbook.add_format(ReportExcelCellStyles.format_content_center)
				format_group = workbook.add_format(format_group)
		
				format_content_right = workbook.add_format(format_content_right)

				sheet = workbook.add_worksheet('Assets')
				sheet.set_column('A:A', 5)
				sheet.set_column('B:B', 15)
				sheet.set_column('C:C', 20)
				sheet.set_column('D:D', 15)
				sheet.set_column('E:E', 14)
				sheet.set_column('F:F', 14)
				sheet.set_column('G:G', 14)
				sheet.set_column('H:H', 14)
				sheet.set_column('I:I', 14)
				sheet.set_column('J:J', 24)
				sheet.set_column('K:K', 14)
				sheet.set_column('L:L', 14)
				sheet.set_column('M:M', 14)
				sheet.set_column('N:N', 14)
				sheet.set_column('O:O', 14)
				sheet.set_column('P:P', 14)
				sheet.set_column('Q:Q', 14)
				sheet.set_column('R:R', 14)
				sheet.set_column('S:S', 14)
				sheet.set_column('T:T', 14)
				sheet.set_column('U:U', 15)
				sheet.set_column('V:V', 14)
				sheet.set_column('W:W', 16)
				sheet.set_column('Y:Y', 15)
				sheet.set_column('Z:Z', 15)
				sheet.set_column('X:X', 15)            
				rowx = 0
				# create name
				sheet.write(rowx, 0, '%s' % (wizard.company_id.name), format_filter)
				rowx += 1
				sheet.merge_range(rowx, 1, rowx, 12, report.name.upper(), format_name)
				# report duration
				sheet.write(rowx + 1, 0, '%s: %s - %s' % (_('Duration'), wizard.date_from, wizard.date_to), format_filter)
				# create date
				sheet.write(rowx + 2, 0, '%s: %s' % (_('Created On'), time.strftime('%Y-%m-%d')), format_filter)
				rowx += 3
		
				sheet.merge_range(rowx, 0, rowx + 2, 0, _(u'№'), format_title)  # seq
				sheet.merge_range(rowx, 1, rowx + 2, 1, _(u'Хөрөнгийн нэр'), format_title)  # Үндсэн хөрөнгийн нэр
				sheet.merge_range(rowx, 2, rowx + 2, 2, _(u'Дотоод код'), format_title)  # Элэгдэх тоо
				sheet.merge_range(rowx, 3, rowx + 2, 3, _(u'Худалдан авсан огноо'), format_title)  # Худалдан авсан огноо
				sheet.merge_range(rowx, 4, rowx, 7, _(u'Өртөг'), format_title)  # Өртөг
				sheet.merge_range(rowx + 1, 4, rowx + 2, 4, _(u'Эхний'), format_title)  # Эхний
				sheet.merge_range(rowx + 1, 5, rowx + 2, 5, _(u'Орлого'), format_title)  # Орлого
				sheet.merge_range(rowx + 1, 6, rowx + 2, 6, _(u'Зарлага'), format_title)  #
				sheet.merge_range(rowx + 1, 7, rowx + 2, 7, _(u'Эцсийн'), format_title)  # Эцсийн
				sheet.merge_range(rowx, 8, rowx + 2, 8, _(u'Тоо'), format_title)  # Эцсийн
				sheet.merge_range(rowx, 9, rowx + 2, 9, _(u'Эд хариуцагч'), format_title)  # Эд хариуцагч
				sheet.merge_range(rowx, 10, rowx + 2, 10, _(u'Төрөл'), format_title)  # Эд хариуцагч
				sheet.merge_range(rowx, 11, rowx + 2, 11, _(u'Салбар'), format_title)  # Эд хариуцагч
				sheet.merge_range(rowx, 12, rowx + 2, 12, _(u'Ангилал'), format_title)  # Эд хариуцагч
				sheet.merge_range(rowx, 13, rowx + 2, 13, _(u'Төлөв'), format_title)  # Эд хариуцагч

				rowx += 3

				def _set_line(line):
					product_code = ''
					if line.get('asset_id',False):
						product_obj = self.env['product.product'].browse(line['asset_id'])
						product_code=product_obj.product_code or product_obj.default_code
					sheet.write(i, 0, n ,format_content_text)
					sheet.write(i, 1, line.get('doc_number', ''),format_content_text)
					if line.get('name') and isinstance(line.get('name'), dict):
						print(line['name'],type(line['name']))
						line['name'] = line['name'][self.env.user.lang] if line['name'].get(self.env.user.lang) else list(line['name'].values())[0]
					sheet.write(i, 1, line.get('name', ''),format_content_text)
					sheet.write(i, 2, product_code,format_content_text)
					sheet.write(i, 3, get_date_format(line.get('date', '')),format_content_text)
					sheet.write(i, 4, _get_data_float(line.get('initial_value', '')), format_content_right)
					sheet.write(i, 5, _get_data_float(line.get('income_value', '')), format_content_right)
					sheet.write(i, 6, _get_data_float(line.get('expense_value', '')), format_content_right)
					sheet.write(i, 7, _get_data_float(line.get('final_value', '')), format_content_right)
					sheet.write(i, 8, line.get('qty', ''),format_content_text)
					sheet.write(i, 9, line.get('owner', ''),format_content_text)
					sheet.write(i, 10, line.get('type', ''),format_content_text)
					sheet.write(i, 11, line.get('branch', ''),format_content_text)
					sheet.write(i, 12, line.get('category', ''),format_content_text)
					sheet.write(i, 13, line.get('state', ''),format_content_text)
				row = 7
				report = wizard.report_id
				all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
				totals = wizard._sql_get_total_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))

				i=row
				n=''
				if totals[0]['income_value'] and totals[0]['final_value']:
					_set_line(totals[0])
				for obj in report.report_object_ids:
					lines_obj = []
					obj_id = obj.id
					for line in all_lines:
						if line.get('report_obj_id') == obj_id:
							lines_obj.append(line)
					if lines_obj:
						row += 1
						name_view = ''
						name_view = obj.sudo().category_id.name
						sheet.write(row, 0, name_view, left)
						sheet.write(row, 1, '', top)
						sheet.write(row, 2, '', top)
						sheet.write(row, 3, '', top)
						sheet.write(row, 4, '', top)
						sheet.write(row, 5, '', top)
						sheet.write(row, 6, '', top)
						sheet.write(row, 7, '', top)
						sheet.write(row, 8, '', top)
						sheet.write(row, 9, '', top)

						row += 1
						start_row = row
						n=1
						for i, line in enumerate(lines_obj):
							i += row
							_set_line(line)
							n+=1
						row = i

			else:  # not summary

				head = [
					{'name': _(u'Дд'),
					 'larg': 8,
					 'col': {}},
					{'name': _(u'Хөрөнгийн код'),
					 'larg': 18,
					 'col': {}},
					{'name': _(u'Хөрөнгийн нэр'),
					 'larg': 40,
					 'col': {}},
					{'name': _(u'Тоо'),
					 'larg': 10,
					 'col': {}},
					{'name': _(u'Худалдан авсан огноо'),
					 'larg': 12,
					 'col': {}},
					{'name': _(u'Худалдан авсан үнэ'),
					 'larg': 15,
					 'col': {}},
					{'name': _( u'Эхний үлдэгдэл'),
					 'larg': 15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
					{'name': _(u'Орлого'),
					 'larg': 15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
					{'name': _(u'Капиталжуулалт'),
					 'larg': 15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
					{'name': _(u'Зарлага'),
					 'larg': 15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
					{'name': _(u'Эцсийн үлдэгдэл'),
					 'larg': 15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
					{'name': _( u'ХЭ/Эхний үлдэгдэл'),
					 'larg': 15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
					{'name': _(u'ХЭ/Орлого'),
					 'larg': 15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
					{'name': _(u'ХЭ/Зарлага'),
					 'larg':15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
					{'name': _(u'ХЭ/Эцсийн үлдэгдэл'),
					 'larg': 15,
					 'col': {'total_function': 'sum', 'format': currency_format}},
				]
				table = []
				for h in head:
					col = {'header': h['name']}
					col.update(h['col'])
					table.append(col)

				def _set_line(line):
					# print('is else')
					sheet.write(i, 0, n )
					sheet.write(i, 1, line.get('internal_code', ''))
					sheet.write(i, 2, line.get('name', ''))
					sheet.write(i, 3, '')
					sheet.write(i, 4, get_date_format(line.get('date', '')))
					sheet.write(i, 5, '')
					sheet.write(i, 6, _get_data_float(line.get('initial_value', '')), currency_format)
					sheet.write(i, 7, _get_data_float(line.get('income_value', '')), currency_format)
					sheet.write(i, 8, _get_data_float(line.get('capital_value', '')), currency_format)
					sheet.write(i, 9, _get_data_float(line.get('expense_value', '')), currency_format)
					sheet.write(i, 10, _get_data_float(line.get('final_value', '')), currency_format)
					sheet.write(i, 11, _get_data_float(line.get('initial_depr', '')), currency_format)
					sheet.write(i, 12, _get_data_float(line.get('income_depr', '')), currency_format)
					sheet.write(i, 13, _get_data_float(line.get('expense_depr', '')), currency_format)
					sheet.write(i, 14, _get_data_float(line.get('final_depr', '')), currency_format)
					
					if line.get('amount_currency', ''):
						sheet.write(i, 12, _get_data_float(line.get('amount_currency', '')), workbook.add_format({'num_format': line.get('currency')}))
					sheet.write(i, 13, line.get('matching_number', ''))

				def _set_table(start_row, row):
					sheet.add_table(start_row - 1, 0, row + 1, len(head) - 1,
									{'total_row': 1,
									 'columns': table,
									 'style': 'Table Style Light 9',
									 })

				# With total workbook
				sheet = workbook.add_worksheet('asset_detail' + _(' Totals'))
				_header_sheet(sheet)

				row = 6
				report = wizard.report_id
				all_lines = wizard._sql_get_line_for_report(type_l=('0_init', '1_init_line', '2_line', '3_compact'))
				for obj in report.report_object_ids:
					lines_obj = []
					obj_id = obj.id
					for line in all_lines:
						if line.get('report_obj_id') == obj_id:
							lines_obj.append(line)
					if lines_obj:
						row += 1
						name_view = ''
						name_view = obj.category_id.name#+' - '+ obj.branch_id.name
						sheet.write(row, 0, name_view, left)
						sheet.write(row, 1, '', top)
						sheet.write(row, 2, '', top)
						sheet.write(row, 3, '', top)
						sheet.write(row, 4, '', top)
						sheet.write(row, 5, '', top)
						sheet.write(row, 6, '', top)
						sheet.write(row, 7, '', top)
						sheet.write(row, 8, '', top)
						sheet.write(row, 9, '', top)
						sheet.write(row, 10, '', top)
						sheet.write(row, 11, '', top)
						sheet.write(row, 12, '', top)
						sheet.write(row, 13, '', right)
						sheet.write(row, 14, '', right)

						row += 2
						start_row = row
						n=1
						for i, line in enumerate(lines_obj):
							i += row
							_set_line(line)
							n+=1
						row = i

						for j, h in enumerate(head):
							sheet.set_column(j, j, h['larg'])

						_set_table(start_row, row)
						row += 2
