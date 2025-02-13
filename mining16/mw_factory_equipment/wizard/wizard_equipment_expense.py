# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

import time
import xlsxwriter
from io import BytesIO
import base64
from odoo.addons.mw_technic_maintenance.models.maintenance_workorder import MAINTENANCE_TYPE

class WizardEquipmentExpense(models.TransientModel):
	_name = "wizard.equipment.expense"
	_description = "wizard.maintenance.expense"

	date_start = fields.Date(
		required=True, string=u'Эхлэх огноо', default=time.strftime('%Y-%m-01'))
	date_end = fields.Date(required=True, string=u'Дуусах огноо',
						   default=fields.Date.context_today)
	equipment_id = fields.Many2one('factory.equipment', string='Тоног төхөөрөмж',)
	validator_id = fields.Many2one('res.users', string=u'Хариуцагч',)
	date_type = fields.Selection([
		('wo_date', u'WO огноо'),
		('move_date', u'Зарлагын огноо'), ],
		string='Огнооны төрөл', required=True, default='move_date')

	maintenance_type = fields.Selection(MAINTENANCE_TYPE,
		string=u'Maintenance type', default='planned')

	def open_plan_materials_report(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID
			mod_obj = self.env['ir.model.data']
			search_res = mod_obj._xmlid_lookup(
				'mw_factory_equipment.equipment_expense_report_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup(
				'mw_factory_equipment.equipment_expense_report_pivot')
			pivot_id = pivot_res and pivot_res[2] or False
			tree_res = mod_obj._xmlid_lookup(
				'mw_factory_equipment.equipment_expense_report_tree_view')
			tree_id = pivot_res and tree_res[2] or False

			domain = [('date', '>=', self.date_start.strftime("%Y-%m-%d")),
					  ('date', '<=', self.date_end.strftime("%Y-%m-%d"))]
			if self.equipment_id:
				domain.append(('equipment_id', '=', self.equipment_id.id))
			return {
				'name': ('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'equipment.expense.report',
				'view_id': False,
				'views': [(tree_id, 'tree'),(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context
			}

	def open_workorder_material_report(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID
			mod_obj = self.env['ir.model.data']
			search_res = mod_obj._xmlid_lookup(
				'mw_factory_equipment.equipment_wo_expense_report_search')
			search_id = search_res and search_res[2] or False
			pivot_res = mod_obj._xmlid_lookup(
				'mw_factory_equipment.equipment_wo_expense_report_pivot')
			tree_res = mod_obj._xmlid_lookup(
				'mw_factory_equipment.equipment_wo_expense_report_tree_view')
			pivot_id = pivot_res and pivot_res[2] or False
			tree_id = tree_res and tree_res[2] or False

			domain = [('date', '>=', self.date_start.strftime("%Y-%m-%d")),
					  ('date', '<=', self.date_end.strftime("%Y-%m-%d"))]
			if self.date_type == 'wo_date':
				domain = [('wo_date', '>=', self.date_start.strftime("%Y-%m-%d")),
					  ('wo_date', '<=', self.date_end.strftime("%Y-%m-%d"))]

			if self.equipment_id:
				domain.append(('equipment_id', '=', self.equipment_id.id))
			return {
				'name': ('Report'),
				'view_type': 'form',
				'view_mode': 'tree,pivot',
				'res_model': 'equipment.wo.expense.report',
				'view_id': False,
				'views': [(tree_id, 'tree'),(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context
			}

	def open_workorder_pivot_report(self):
		if self.date_start and self.date_end:
			context = dict(self._context)
			# GET views ID
			mod_obj = self.env['ir.model.data']
			search_id = self.env.ref('mw_factory_equipment.equipment_wo_report_search').id
			pivot_id = self.env.ref('mw_factory_equipment.equipment_wo_report_tree_view').id
			tree_id = self.env.ref('mw_factory_equipment.equipment_wo_report_pivot').id

			domain = [('date', '>=', self.date_start.strftime("%Y-%m-%d")),
				('date', '<=', self.date_end.strftime("%Y-%m-%d"))]

			if self.equipment_id :
				domain.append(('equipment_id', '=', self.equipment_id.id))
			self.ensure_one()
			action = self.env["ir.actions.act_window"]._for_xml_id(
				'mw_factory_equipment.action_equipment_wo_report')
			action['domain'] = domain
			action['context'] = context
			action['res_id'] = False
			action['view_id'] = pivot_id
			return action
			# return {
			# 	'name': ('Report'),
			# 	'view_type': 'form',
			# 	'view_mode': 'pivot',
			# 	'res_model': 'equipment.wo.report',
			# 	'view_id': False,
			# 	'views': [(tree_id, 'tree'),(pivot_id, 'pivot')],
			# 	'search_view_id': search_id,
			# 	'domain': domain,
			# 	'type': 'ir.actions.act_window',
			# 	'target': 'current',
			# 	'context': context
			# }


	def open_call_pivot_report(self):
		if self.date_start and self.date_end:
			context=dict(self._context)
			# GET views ID
			mod_obj=self.env['ir.model.data']
			search_res=mod_obj._xmlid_lookup(
				'mw_technic_maintenance.maintenance_call_report_search')
			search_id=search_res and search_res[2] or False
			pivot_res=mod_obj._xmlid_lookup(
				'mw_technic_maintenance.maintenance_call_report_pivot')
			pivot_id=pivot_res and pivot_res[2] or False

			domain=[('date_required', '>=', self.date_start.strftime("%Y-%m-%d")),
					  ('date_required', '<=', self.date_end.strftime("%Y-%m-%d"))]
			if self.equipment_id:
				domain.append(('equipment_id', '=', self.equipment_id.id))
			return {
				'name': ('Report'),
				'view_type': 'form',
				'view_mode': 'pivot',
				'res_model': 'maintenance.call.report',
				'view_id': False,
				'views': [(pivot_id, 'pivot')],
				'search_view_id': search_id,
				'domain': domain,
				'type': 'ir.actions.act_window',
				'target': 'current',
				'context': context
			}

	# Засварын ажилд хэрэглэсэн сэлбэг болон Төлөвлөгөөний гүйцэтгэл

	def export_material_performance(self):
		if self.date_start <= self.date_end:
			# EXCEL datas
			output=BytesIO()
			workbook=xlsxwriter.Workbook(output)
			file_name='material_performance_'+self.date_end.strftime("%Y-%m-%d")+'.xlsx'

			h1=workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header=workbook.add_format({'bold': 1})
			header.set_font_size(9)
			header.set_align('center')
			header.set_align('vcenter')
			header.set_border(style=1)
			header.set_bg_color('#6495ED')

			header_wrap=workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#6495ED')

			footer=workbook.add_format({'bold': 1})
			footer.set_text_wrap()
			footer.set_font_size(9)
			footer.set_align('right')
			footer.set_align('vcenter')
			footer.set_border(style=1)
			footer.set_bg_color('#6495ED')
			footer.set_num_format('#,##0.00')

			contest_right=workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_right_red=workbook.add_format()
			contest_right_red.set_text_wrap()
			contest_right_red.set_font_size(9)
			contest_right_red.set_align('right')
			contest_right_red.set_align('vcenter')
			contest_right_red.set_font_color('red')
			contest_right_red.set_num_format('#,##0.00')

			contest_right_green=workbook.add_format()
			contest_right_green.set_text_wrap()
			contest_right_green.set_font_size(9)
			contest_right_green.set_align('right')
			contest_right_green.set_align('vcenter')
			contest_right_green.set_font_color('green')
			contest_right_green.set_num_format('#,##0.00')

			contest_left=workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_left0=workbook.add_format()
			contest_left0.set_font_size(9)
			contest_left0.set_align('left')
			contest_left0.set_align('vcenter')

			contest_center=workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			categ_name=workbook.add_format({'bold': 1})
			categ_name.set_font_size(9)
			categ_name.set_align('left')
			categ_name.set_align('vcenter')
			categ_name.set_border(style=1)
			categ_name.set_bg_color('#B9CFF7')

			categ_right=workbook.add_format({'bold': 1})
			categ_right.set_font_size(9)
			categ_right.set_align('right')
			categ_right.set_align('vcenter')
			categ_right.set_border(style=1)
			categ_right.set_bg_color('#B9CFF7')
			categ_right.set_num_format('#,##0.00')

			contest_right_per=workbook.add_format()
			contest_right_per.set_text_wrap()
			contest_right_per.set_font_size(9)
			contest_right_per.set_align('right')
			contest_right_per.set_align('vcenter')
			contest_right_per.set_num_format('#,##0.0')
			contest_right_per.set_bg_color('#cfdbf0')

			number_right=workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			# DRAW
			worksheet=workbook.add_worksheet(u'Засварын ажил')
			worksheet.write(0, 2, u"Засварын материалын гүйцэтгэл", h1)
			worksheet.set_zoom(100)
			worksheet.freeze_panes(2, 0)
			# TABLE HEADER
			row=1
			worksheet.set_row(1, 30)
			worksheet.write(row, 0, u'№', header_wrap)
			worksheet.set_column(0, 0, 3)
			worksheet.write(row, 1, u'Барааны нэр', header_wrap)
			worksheet.set_column(1, 1, 40)
			worksheet.write(row, 2, u'Төлөвлөгөө', header_wrap)
			worksheet.set_column(2, 4, 12)
			worksheet.write(row, 3, u'Хэрэглэсэн', header_wrap)
			worksheet.write(row, 4, u'Гүйцэтгэл %', header_wrap)
			worksheet.write(row, 5, u'Огноо', header_wrap)

			# WO, Төлөвлөгөөн дээрх материал авах
			# Нэмэлт шүүлт
			additional_condition=""
			if self.equipment_id:
				additional_condition=' and ll.equipment_id = %d ' % self.equipment_id.id

			if self.maintenance_type == 'planned':
				additional_condition += " and ll.maintenance_type in ('main_service','pm_service','planned')"
			elif self.maintenance_type:
				additional_condition += " and ll.maintenance_type = '"+self.maintenance_type+"'"
			query="""
				SELECT
					tmp.report_order as report_order,
					tmp.equipment_id as equipment_id,
					tmp.product_id as product_id,
					tmp.date as date,
					sum(tmp.plan_qty) as plan_qty,
					sum(tmp.wo_qty) as wo_qty
				FROM (
					SELECT
						t.report_order as report_order,
						ll.equipment_id as equipment_id,
						ll.product_id as product_id,
						ll.date as date,
						ll.qty as plan_qty,
						0 as wo_qty
					FROM equipment_expense_report as ll
					LEFT JOIN factory_equipment as t on (t.id = ll.equipment_id)
					WHERE
						  ll.date >= '%s' and
						  ll.date <= '%s'
						   %s
					UNION ALL
					SELECT
						t.report_order as report_order,
						ll.equipment_id as equipment_id,
						ll.product_id as product_id,
						ll.date as date,
						0 as plan_qty,
						ll.qty as wo_qty
					FROM equipment_wo_expense_report as ll
					LEFT JOIN factory_equipment as t on (t.id = ll.equipment_id)
					WHERE
						ll.date >= '%s' and
						ll.date <= '%s'
						 %s
				) as tmp
				GROUP BY tmp.report_order, tmp.equipment_id, tmp.product_id, tmp.date
				ORDER BY tmp.report_order, tmp.equipment_id, tmp.product_id, tmp.date
			""" % (self.date_start, self.date_end, additional_condition, self.date_start, self.date_end, additional_condition)
			print('===', query)
			self.env.cr.execute(query)
			query_result=self.env.cr.dictfetchall()
			print('===', query_result)

			# INIT
			row=2
			number=1
			num_categ=1
			categ_row=-1

			equipment_id=-1
			technic=False
			sub_totals_address={2: [], 3: [], 4: []}
			for line in query_result:
				if equipment_id != line['equipment_id']:
					technic=self.env['factory.equipment'].browse(line['equipment_id'])
					name=str(num_categ)+" : "+str(technic.name)
					if categ_row+1 == row:
						row -= 1
					worksheet.merge_range(row, 0, row, 1, name, categ_name)
					# Total
					if categ_row != row and categ_row != -1:
						worksheet.write_formula(categ_row, 2,
							'{=IFERROR(SUM('+self._symbol(categ_row+1, 2) + ':' + self._symbol(row-1, 2)+'),0)}', categ_right)
						worksheet.write_formula(categ_row, 3,
							'{=IFERROR(SUM('+self._symbol(categ_row+1, 3) + ':' + self._symbol(row-1, 3)+'),0)}', categ_right)
						worksheet.write_formula(categ_row, 4,
							'{=IFERROR(AVERAGE('+self._symbol(categ_row+1, 4) + ':' + self._symbol(row-1, 4)+'),0)}', categ_right)
						# SET address
						sub_totals_address[2].append(self._symbol(categ_row, 2))
						sub_totals_address[3].append(self._symbol(categ_row, 3))
						sub_totals_address[4].append(self._symbol(categ_row, 4))
					worksheet.write(row, 5, '', categ_name)

					num_categ += 1
					equipment_id=line['equipment_id']
					categ_row=row
					row += 1

				worksheet.write(row, 0, number, number_right)
				product=self.env['product.product'].browse(line['product_id'])
				worksheet.write(row, 1, product.name_get()[0][1], contest_left)
				worksheet.write(row, 2, line['plan_qty'] or '', contest_right)
				worksheet.write(row, 3, line['wo_qty'] or '', contest_right)
				worksheet.write_formula(row, 4,
					'{=IFERROR(('+self._symbol(row, 3) + '*100)/' + self._symbol(row, 2)+',0)}', contest_right_per)
				worksheet.write(row, 5, line['date'].strftime("%Y-%m-%d"), contest_right)
				row += 1
				number += 1

			# Last total
			if categ_row != row and categ_row != -1:
				worksheet.write_formula(categ_row, 2,
					'{=IFERROR(SUM('+self._symbol(categ_row+1, 2) + ':' + self._symbol(row-1, 2)+'),0)}', categ_right)
				worksheet.write_formula(categ_row, 3,
					'{=IFERROR(SUM('+self._symbol(categ_row+1, 3) + ':' + self._symbol(row-1, 3)+'),0)}', categ_right)
				worksheet.write_formula(categ_row, 4,
					'{=IFERROR(AVERAGE('+self._symbol(categ_row+1, 4) + ':' + self._symbol(row-1, 4)+'),0)}', categ_right)
				# SET address
				sub_totals_address[2].append(self._symbol(categ_row, 2))
				sub_totals_address[3].append(self._symbol(categ_row, 3))
				sub_totals_address[4].append(self._symbol(categ_row, 4))

			# Footer
			worksheet.merge_range(row, 0, row, 1, u'Нийт', header_wrap)
			worksheet.write_formula(
				row, 2, '{=IFERROR(' + '+'.join(sub_totals_address[2]) + ',0)}', footer)
			worksheet.write_formula(
				row, 3, '{=IFERROR(' + '+'.join(sub_totals_address[3]) + ',0)}', footer)
			worksheet.write_formula(row, 4, '{=IFERROR((' + '+'.join(
				sub_totals_address[3]) + ')/'+str(len(sub_totals_address[3]))+',0)}', footer)

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
			raise UserError(_(u'Бичлэг олдсонгүй!'))

	# Хаагдаагүй WO ажлууд татах

	def get_done_workorder(self):
		if self.date_start <= self.date_end:
			output=BytesIO()
			workbook=xlsxwriter.Workbook(output)
			file_name='done_workorders_'+self.date_start.strftime("%Y-%m-%d")+'.xlsx'

			h1=workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header_wrap=workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			number_right=workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right=workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_left=workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center=workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sub_total=workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(9)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			worksheet=workbook.add_worksheet(u'ХААГДААГҮЙ WORKORDER-ууд')
			worksheet.set_zoom(80)
			worksheet.write(0, 2, u"ХААГДААГҮЙ WORKORDER", h1)

			# TABLE HEADER
			row=1
			worksheet.set_row(1, 30)
			worksheet.write(row, 0, u'№', header_wrap)
			worksheet.set_column(0, 0, 3)
			worksheet.write(row, 1, u'Date', header_wrap)
			worksheet.set_column(2, 2, 10)
			worksheet.write(row, 2, u'Work Order', header_wrap)
			worksheet.set_column(2, 2, 12)
			worksheet.write(row, 3, u'Equipment', header_wrap)
			worksheet.set_column(3, 3, 28)
			worksheet.write(row, 4, u'Equipment description', header_wrap)
			worksheet.write(row, 5, u'Type', header_wrap)
			worksheet.set_column(5, 5, 10)
			worksheet.write(row, 6, u'Ээлж', header_wrap)
			worksheet.set_column(6, 6, 8)
			worksheet.write(row, 7, u'Description', header_wrap)
			worksheet.set_column(7, 7, 90)
			worksheet.write(row, 8, u'Status', header_wrap)
			worksheet.set_column(8, 8, 8)
			worksheet.write(row, 9, u'Shift Foreman', header_wrap)
			worksheet.set_column(9, 9, 15)

			domains=[
				('date_required', '>=', self.date_start.strftime("%Y-%m-%d")),
				('date_required', '<=', self.date_end.strftime("%Y-%m-%d")),
				('state', '=', 'done')]
			if self.validator_id:
				domains.append(('validator_id', '=', self.validator_id.id))
			wos=self.env['maintenance.workorder'].search(domains, order='name, origin')

			row=2
			worksheet.write(row, 0, "#", sub_total)
			worksheet.merge_range(row, 1, row, 9, u"Хаагдаагүй ажлууд", sub_total)
			row += 1
			number=1
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name, contest_center)
				worksheet.write(row, 3, line.equipment_id.name or '', contest_left)
				worksheet.write(row, 4, line.equipment_id.program_code, contest_center)
				worksheet.write(row, 5, line.maintenance_type, contest_center)
				worksheet.write(row, 6, line.shift, contest_center)
				worksheet.write(row, 7, line.description, contest_left)
				worksheet.write(row, 8, line.state, contest_center)
				worksheet.write(row, 9, line.validator_id.name or '', contest_left)
				row += 1
				number += 1

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
			raise UserError(_(u'Бичлэг олдсонгүй!'))

	# Сэлбэг хүлээсэн WO ажлууд татах

	def get_ordered_workorder(self):
		if self.date_start <= self.date_end:
			output=BytesIO()
			workbook=xlsxwriter.Workbook(output)
			file_name='waiting_part_workorders_' + \
				self.date_start.strftime("%Y-%m-%d")+'.xlsx'

			h1=workbook.add_format({'bold': 1})
			h1.set_font_size(12)

			header_wrap=workbook.add_format({'bold': 1})
			header_wrap.set_text_wrap()
			header_wrap.set_font_size(9)
			header_wrap.set_align('center')
			header_wrap.set_align('vcenter')
			header_wrap.set_border(style=1)
			header_wrap.set_bg_color('#E9A227')

			number_right=workbook.add_format()
			number_right.set_text_wrap()
			number_right.set_font_size(9)
			number_right.set_align('right')
			number_right.set_align('vcenter')
			number_right.set_border(style=1)

			contest_right=workbook.add_format()
			contest_right.set_text_wrap()
			contest_right.set_font_size(9)
			contest_right.set_align('right')
			contest_right.set_align('vcenter')
			contest_right.set_border(style=1)
			contest_right.set_num_format('#,##0.00')

			contest_left=workbook.add_format()
			contest_left.set_text_wrap()
			contest_left.set_font_size(9)
			contest_left.set_align('left')
			contest_left.set_align('vcenter')
			contest_left.set_border(style=1)

			contest_center=workbook.add_format()
			contest_center.set_text_wrap()
			contest_center.set_font_size(9)
			contest_center.set_align('center')
			contest_center.set_align('vcenter')
			contest_center.set_border(style=1)

			sub_total=workbook.add_format({'bold': 1})
			sub_total.set_text_wrap()
			sub_total.set_font_size(9)
			sub_total.set_align('center')
			sub_total.set_align('vcenter')
			sub_total.set_border(style=1)
			sub_total.set_bg_color('#F7EE5E')

			worksheet=workbook.add_worksheet(u'Сэлбэг хүлээсэн WORKORDER-ууд')
			worksheet.set_zoom(80)
			worksheet.write(0, 2, u"Сэлбэг хүлээсэн WORKORDER", h1)

			# TABLE HEADER
			row=1
			worksheet.set_row(1, 30)
			worksheet.write(row, 0, u'№', header_wrap)
			worksheet.set_column(0, 0, 3)
			worksheet.write(row, 1, u'Date', header_wrap)
			worksheet.set_column(2, 2, 10)
			worksheet.write(row, 2, u'Work Order', header_wrap)
			worksheet.set_column(2, 2, 12)
			worksheet.write(row, 3, u'Equipment', header_wrap)
			worksheet.set_column(3, 3, 28)
			worksheet.write(row, 4, u'Equipment description', header_wrap)
			worksheet.write(row, 5, u'Type', header_wrap)
			worksheet.set_column(5, 5, 10)
			worksheet.write(row, 6, u'Ээлж', header_wrap)
			worksheet.set_column(6, 6, 8)
			worksheet.write(row, 7, u'Description', header_wrap)
			worksheet.set_column(7, 7, 90)
			worksheet.write(row, 8, u'Status', header_wrap)
			worksheet.set_column(8, 8, 8)
			worksheet.write(row, 9, u'Shift Foreman', header_wrap)
			worksheet.set_column(9, 9, 15)

			domains=[
				# ('date_required','>=',self.date_start),
				# ('date_required','<=',self.date_end),
				('state', '=', 'ordered_part')]
			if self.validator_id:
				domains.append(('validator_id', '=', self.validator_id.id))
			wos=self.env['maintenance.workorder'].search(domains, order='name, origin')

			row=2
			worksheet.write(row, 0, "#", sub_total)
			worksheet.merge_range(row, 1, row, 9, u"Сэлбэг хүлээсэн ажлууд", sub_total)
			row += 1
			number=1
			for line in wos:
				worksheet.write(row, 0, number, number_right)
				worksheet.write(row, 1, line.date_required, contest_center)
				worksheet.write(row, 2, line.name, contest_center)
				worksheet.write(row, 3, line.equipment_id.name or '', contest_left)
				worksheet.write(row, 4, line.equipment_id.program_code, contest_center)
				worksheet.write(row, 5, line.maintenance_type, contest_center)
				worksheet.write(row, 6, line.shift, contest_center)
				worksheet.write(row, 7, line.description, contest_left)
				worksheet.write(row, 8, line.state, contest_center)
				worksheet.write(row, 9, line.validator_id.name or '', contest_left)
				row += 1
				number += 1

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
			raise UserError(_(u'Бичлэг олдсонгүй!'))

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol=str()
		div=col+1
		while div:
			(div, mod)=divmod(div-1, 26)
			excelCol=chr(mod + 65) + excelCol
		return excelCol
