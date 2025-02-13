# -*- coding: utf-8 -*-

import time
from odoo import _, tools
from datetime import datetime, timedelta
from odoo import api, fields, models
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from dateutil.relativedelta import relativedelta
from io import BytesIO
import base64
import logging
from odoo.tools.safe_eval import pytz

_logger = logging.getLogger(__name__)

class StockInternalReport(models.TransientModel):
	_name = "stock.internal.report"  
	_description = "stock internal report"
	
	date_range_id = fields.Many2one('date.range',string='Огнооны хязгаар')
	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	product_tmpl_ids = fields.Many2many('product.template', string=u'Бараа/Template', help=u"Тайланд гарах бараануудыг сонгоно")
	warehouse_ids = fields.Many2many('stock.warehouse', string=u'Агуулах',required=True, )
	location_ids = fields.Many2many('stock.location', string=u'Байрлал',)
	product_ids = fields.Many2many('product.product', string=u'Бараанууд', help=u"Тайланд гарах барааг сонгоно")
	categ_ids = fields.Many2many('product.category', string=u'Барааны ангилал', help=u"Тухайн сонгосон ангилал дахь бараануудыг тайланд гаргах")
	is_scheduled_date = fields.Boolean(string="Товлогдсон огноонд хайх", default=False)
	import_wh = fields.Boolean(u'Бүх агуулах ОРУУЛАХ/АРИЛГАХ', default=False)
	
	@api.onchange('import_wh')
	def onchange_all_wh_import(self):
		if self.import_wh:
			self.warehouse_ids = self.env['stock.warehouse'].search([])
		else:
			self.warehouse_ids = False
	
	@api.onchange('date_range_id')
	def onchange_date_range_id(self):
		self.date_start = self.date_range_id.date_start
		self.date_end = self.date_range_id.date_end
	
	def get_tuple(self, obj, categ_is=False):
		if categ_is:
			obj = self.env['product.category'].search([('id','child_of',obj)]).ids
			
		if len(obj) > 1:
			return str(tuple(obj))
		else:
			return " ("+str(obj[0])+") "
		
	def get_domain(self, domain, donwload=False):
		domain_val = ''
		if donwload:
			if self.product_ids:
				domain_val +=" and rep.product_id in %s "%(self.get_tuple(self.product_ids.ids))
			if self.product_tmpl_ids:
				domain_val +=" and rep.product_tmpl_id in %s "%(self.get_tuple(self.product_tmpl_ids.ids))
			if self.categ_ids:
				domain_val +=" and rep.categ_id in %s "%(self.get_tuple(self.categ_ids.ids, True))
			# domain_val +=" and rep.state in ('done','assigned') "
			domain_val +=" and rep.state in ('done') "
			if self.location_ids:
				domain_val +=" and rep.location_dest_id in %s "%(self.get_tuple(self.location_ids.ids))
			elif self.warehouse_ids:
				domain_val +=" and rep.warehouse_dest_id in %s "%(self.get_tuple(self.warehouse_ids.ids))
			domain_val +=" and rep.transfer_type in ('incoming', 'internal') "
			if self.is_scheduled_date:
				domain_val +=" and rep.scheduled_date>='%s' and rep.scheduled_date<= '%s' "%(self.date_start, self.date_end)
			else:
				domain_val +=" and rep.date_expected>='%s' and rep.date_expected<= '%s' "%(self.date_start, self.date_end)
			return domain_val
		domain.append(('date_expected','>=',self.date_start))
		domain.append(('date_expected','<=',self.date_end))
		if self.product_ids:
			domain.append(('product_id','in',self.product_ids.ids))
		if self.product_tmpl_ids:
			domain.append(('product_tmpl_id','in',self.product_tmpl_ids.ids))
		if self.categ_ids:
			domain.append(('categ_id','child_of',self.categ_ids.ids))
		domain.append(('state','in',['done','assigned']))
		if self.location_ids:
			domain.append(('location_dest_id','in',self.location_ids.ids))
		elif self.warehouse_ids:
			domain.append(('warehouse_dest_id','in',self.warehouse_ids.ids))
		domain.append(('transfer_type', 'in', ('incoming', 'internal')))
		return domain
	
	def open_analyze_view(self):
		domain = []
		qty_char = False
		action = self.env.ref('mw_stock_product_report.action_product_income_expense_report_in')
		vals = action.read()[0]
		dom = self.get_domain(domain)
		vals['domain'] = dom
		return vals

	def get_product_cost(self, product_id):
		'''
		Барааны өртөг авах функц
		:param product_id:
		:return:
		'''
		price = 0
		prod_query = """
			select value_float from ir_property where name='standard_price' and res_id='product.product,{0}' limit 1
		""".format(product_id)
		self.env.cr.execute(prod_query)
		query_result = self.env.cr.dictfetchone()
		if query_result:
			price = query_result['value_float']

		# Өртгийн түүхтэй байвал авна
		prod_his_query = """
			select new_standard_price from stock_price_unit_change_log where product_id={0} and create_date <= '{1}' order by create_date desc limit 1
		""".format(product_id, (self.date_end + relativedelta(days=1) - relativedelta(microseconds=1)).strftime('%Y-%m-%d %H:%M:%S'))
		self.env.cr.execute(prod_his_query)
		print('history_query_result: ',prod_his_query)
		history_query_result = self.env.cr.dictfetchone()
		if history_query_result:
			price = history_query_result['new_standard_price']

		return price

	def get_product_list_price(self, product_id):
		'''
		Барааны зарах үнэ авах функц
		:param product_id:
		:return:
		'''
		price = 0
		prod_query = """
			select pt.list_price from product_product as pp
			left join product_template as pt on (pt.id=pp.product_tmpl_id)
			where pp.id={0} limit 1
		""".format(product_id)
		self.env.cr.execute(prod_query)
		query_result = self.env.cr.dictfetchone()
		if query_result:
			price = query_result['list_price']
		return price

	def get_product_account(self, categ_id):
		'''
		Барааны ангилал дээрх данс авах
		:param categ_id:
		:return:
		'''
		account = ''
		categ = 'product.category,%s'%(categ_id)
		prod_query = """
			select aa.code from account_account as aa
			LEFT JOIN ir_property as ip on (ip.value_reference = 'account.account,'||aa.id)
			where ip.name = 'property_stock_valuation_account_id' and ip.res_id='{0}' limit 1
		""".format(categ)
		self.env.cr.execute(prod_query)
		query_result = self.env.cr.dictfetchone()
		if query_result:
			account = query_result['code']
		return account

	def prepair_workbook(self, workbook):
		worksheet = workbook.add_worksheet(u'Бараа материалын тайлан')

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

		contest_right = workbook.add_format()
		contest_right.set_text_wrap()
		contest_right.set_font_size(9)
		contest_right.set_align('right')
		contest_right.set_align('vcenter')
		contest_right.set_border(style=1)
		contest_right.set_num_format('#,##0.00')

		contest_right_red = workbook.add_format()
		contest_right_red.set_text_wrap()
		contest_right_red.set_font_size(9)
		contest_right_red.set_align('right')
		contest_right_red.set_align('vcenter')
		contest_right_red.set_font_color('red')
		contest_right_red.set_num_format('#,##0.00')

		contest_right_green = workbook.add_format()
		contest_right_green.set_text_wrap()
		contest_right_green.set_font_size(9)
		contest_right_green.set_align('right')
		contest_right_green.set_align('vcenter')
		contest_right_green.set_font_color('green')
		contest_right_green.set_num_format('#,##0.00')

		contest_left = workbook.add_format()
		contest_left.set_text_wrap()
		contest_left.set_font_size(9)
		contest_left.set_align('left')
		contest_left.set_align('vcenter')
		contest_left.set_border(style=1)
		contest_left.set_num_format('#,##0.00')

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

		# ======= GET Filter, Conditions
		domain = self.get_domain([], True)
		order_by = ' ORDER BY rep.categ_id  '
		group_by = ''
		left_join = ''
		select_from = ''
		#if not self.no_category_total:
		order_by = ' ORDER BY pc.complete_name, pt.name  '
		group_by += ' ,pc.complete_name '
		left_join += 'left join product_category as pc on (pc.id=rep.categ_id)'
		select_from += ' pc.complete_name, '
		select_from += """ pt.name as product_name,
				sum(rep.qty_first) as qty_first,
				sum(rep.total_price_first) as total_price_first,
				sum(rep.qty_last) as qty_last,
				sum(rep.total_price_last) as total_price_last,
				sum(rep.qty_income) as qty_income,
				sum(rep.total_price_income) as total_price_income,
				sum(rep.qty_expense) as qty_expense,
				sum(rep.total_price_expense) as total_price_expense """
		query1 = """
			SELECT 
				rep.stock_move_id,
				rep.product_id,
				rep.default_code,
				rep.product_code,
				rep.barcode,
				pu.name as uom_name,
				rep.categ_id,
				{4}
				
			FROM stock_report_detail as rep
			left join product_template as pt on (pt.id=rep.product_tmpl_id)
			left join uom_uom as pu on (pu.id=rep.uom_id)
			{3}
			WHERE 
				1=1 and stock_move_id is not null {0}
			GROUP BY 1,2,3,4,5,6,7,pt.name {2}
			{1}
			""".format(domain, order_by, group_by, left_join, select_from)
		# print(query1)
		# print(aaa)
		self.env.cr.execute(query1)
		query_result = self.env.cr.dictfetchall()
		w_names = ', '.join(self.warehouse_ids.mapped('name'))


		dt = datetime.now() + timedelta(hours=8)

		report_header_name = u'Дотоод Шилжүүлгийн тайлан'

		worksheet.write(1,3, report_header_name, h1)
		worksheet.write(2,0, u"Агуулах: " + w_names, contest_left0)
		worksheet.write(3,0, u"Тайлан бэлдсэн: " + str(fields.Datetime.to_string(dt)), contest_left0)
		worksheet.write(4,0, u"Тайлант үеийн хугацаа: " + str(self.date_start) +" ~ "+ str(self.date_end), contest_left0)
		
		row = 6
		col = 0

		worksheet.write(row, col, u"№", header)
		worksheet.write(row, col+1, u"Баримтын дугаар", header_wrap)
		worksheet.write(row, col+2, u"Товлосон огноо", header_wrap)
		worksheet.write(row, col+3, u"Хэрэгжсэн огноо", header_wrap)
		worksheet.write(row, col+4, u"Барааны нэр", header_wrap)
		worksheet.write(row, col+5, u"Код", header_wrap)
		worksheet.write(row, col+6, u"Эдийн дугаар", header_wrap)
		worksheet.write(row, col+7, u"Тоо хэмжээ", header_wrap)
		worksheet.write(row, col+8, u"Өртөг", header_wrap)
		worksheet.write(row, col+9, u"Гарсан байрлал", header_wrap)
		worksheet.write(row, col+10, u"Хүрсэн байрлал", header_wrap)
		worksheet.write(row, col+11, u"Үүсгэсэн этгээд", header_wrap)
		worksheet.write(row, col+12, u"Хүлээн авсан этгээд", header_wrap)
		# worksheet.write(row, col+13, u"Поддоны тоо", header_wrap)
		# worksheet.write(row, col+14, u"Уутны төрөл", header_wrap)
		# worksheet.write(row, col+15, u"Асгамлын шуудайн тоо", header_wrap)
		# worksheet.write(row, col+16, u"Машины дугаар", header_wrap)
		# worksheet.write(row, col+17, u"Жолоочийн нэр", header_wrap)

		worksheet.freeze_panes(7, 4)
		row+=1
		number=1
		for item in query_result:
			move_id = self.env['stock.move'].sudo().browse(int(item['stock_move_id']))
			if move_id.company_id.id not in self.env.user.company_ids.ids:
				continue
			picking_id = move_id.picking_id
			worksheet.write(row, col, number, contest_center)
			worksheet.write(row, col+1, picking_id.name, contest_center)
			worksheet.write(row, col+2, str(picking_id.scheduled_date.date()) if picking_id.scheduled_date else '', contest_center)
			worksheet.write(row, col+3, str(picking_id.date_done.date()) if picking_id.date_done else '', contest_left)
			worksheet.write(row, col+4, move_id.product_id.name, contest_left)
			worksheet.write(row, col+5, move_id.product_id.default_code or '', contest_center)
			worksheet.write(row, col+6, move_id.product_id.product_code or '', contest_center)
			worksheet.write(row, col+7, move_id.quantity_done, contest_right)
			worksheet.write(row, col+8, move_id.price_unit, contest_right)
			worksheet.write(row, col+9, picking_id.location_id.name, contest_right)
			worksheet.write(row, col+10, picking_id.location_dest_id.name, contest_right)
			worksheet.write(row, col+11, picking_id.user_id.name, contest_right)
			worksheet.write(row, col+12, picking_id.doned_user_id.name, contest_right)
			# worksheet.write(row, col+13, picking_id.podon_sum_count, contest_right)
			# worksheet.write(row, col+14, dict(self.env['sale.order']._fields['bag_type'].selection).get(picking_id.bag_type) if picking_id.bag_type else '', contest_right)
			# worksheet.write(row, col+15, 0, contest_right)
			# worksheet.write(row, col+16, picking_id.car_number, contest_right)
			# worksheet.write(row, col+17, picking_id.delivery_person, contest_right)

			row += 1
			number += 1
		worksheet.set_column('A:A', 5)
		worksheet.set_column('B:B', 13)
		worksheet.set_column('C:C', 13)
		worksheet.set_column('D:D', 13)
		worksheet.set_column('E:O', 14)
		worksheet.set_column('I:J', 25)
		worksheet.set_column('K:L', 20)
		return workbook

	def export_report(self):
		# ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Дотоод Шилжүүлгийн тайлан.xlsx'
		workbook = self.prepair_workbook(workbook)

		# CLOSE
		workbook.close()
		out = base64.encodebytes(output.getvalue())
		excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
		return {
				'type' : 'ir.actions.act_url',
				'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
				'target': 'new',
		}

	def _symbol(self, row, col):
		return self._symbol_col(col) + str(row+1)
	def _symbol_col(self, col):
		excelCol = str()
		div = col+1
		while div:
			(div, mod) = divmod(div-1, 26)
			excelCol = chr(mod + 65) + excelCol
		return excelCol
