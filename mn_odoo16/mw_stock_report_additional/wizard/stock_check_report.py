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

class StockCheckReport(models.TransientModel):
	_name = "stock.check.report"
	_description = "stock check report"
	
	date_range_id = fields.Many2one('date.range',string='Огнооны хязгаар')
	date_start = fields.Date(required=True, string=u'Эхлэх огноо', default=fields.Date.context_today)
	date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
	product_tmpl_ids = fields.Many2many('product.template', string=u'Бараа/Template', help=u"Тайланд гарах бараануудыг сонгоно")
	# warehouse_ids = fields.Many2many('stock.warehouse', string=u'Агуулах',required=True, )
	warehouse_ids = fields.Many2many('stock.warehouse', string='Агуулах',)
	partner_ids = fields.Many2many('res.partner', string='Харилцагч',)
	location_ids = fields.Many2many('stock.location', string='Байрлал',)
	product_ids = fields.Many2many('product.product', string='Бараанууд', help="Тайланд гарах барааг сонгоно")
	categ_ids = fields.Many2many('product.category', string=u'Барааны ангилал', help="Тухайн сонгосон ангилал дахь бараануудыг тайланд гаргах")
	see_cost = fields.Boolean(string="Өртөгтэй харах", default=False)
	import_wh = fields.Boolean(u'Бүх агуулах ОРУУЛАХ/АРИЛГАХ', default=False)
	
	# @api.onchange('import_wh')
	# def onchange_all_wh_import(self):
	# 	if self.import_wh:
	# 		self.warehouse_ids = self.env['stock.warehouse'].search([])
	# 	else:
	# 		self.warehouse_ids = False
	
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
		location_ids = []
		if self.location_ids:
			location_ids = self.location_ids
		if self.warehouse_ids:
			location_ids = self.env['stock.location'].search([('set_warehouse_id','in',self.warehouse_ids.ids),('usage','=','internal')])
		if donwload:
			if self.product_ids:
				domain_val +=" and sm.product_id in %s "%(self.get_tuple(self.product_ids.ids))
			if self.product_tmpl_ids:
				domain_val +=" and sm.product_tmpl_id in %s "%(self.get_tuple(self.product_tmpl_ids.ids))
			if self.categ_ids:
				domain_val +=" and sm.categ_id in %s "%(self.get_tuple(self.categ_ids.ids, True))
			domain_val +=" and sm.state in ('done','assigned') "
			if location_ids:
				domain_val +=" and (sm.location_dest_id in %s or sm.location_id in %s)"%(self.get_tuple(location_ids.ids), self.get_tuple(location_ids.ids))
			if self.partner_ids:
				domain_val +=" and sm.partner_id in %s "%(self.get_tuple(self.partner_ids.ids))
			# elif self.warehouse_ids:
			# 	domain_val +=" and sm.warehouse_dest_id in %s "%(self.get_tuple(self.warehouse_ids.ids))
			domain_val +=" and sm.company_id = '%s'"%(self.env.user.company_id.id)
			# domain_val +=" and sm.date>='%s' and sm.date<= '%s' "%(self.date_start, self.date_end)
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
		if location_ids:
			domain.append(('location_dest_id','in',location_ids.ids))
		if self.partner_ids:
			domain.append(('partner_id','in',self.partner_ids.ids))
		domain.append(('company_id','=',self.env.user.company_id.id))
		# elif self.warehouse_ids:
		# 	domain.append(('warehouse_dest_id','in',self.warehouse_ids.ids))
		return domain
	
	def open_analyze_view(self):
		domain = []
		qty_char = False
		action = self.env.ref('mw_stock_product_report.action_stock_report_detail')
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
		worksheet = workbook.add_worksheet(u'Агуулахын бүртгэл, хяналтын баримт')

		h1_left = workbook.add_format({'bold': 1})
		h1_left.set_align('left')
		h1_left.set_font_size(12)
  
		h1_right = workbook.add_format({'bold': 1})
		h1_right.set_align('right')
		h1_right.set_font_size(12)

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
				rep.transfer_type,
				case when rep.date_expected is not null then rep.date_expected else '{5}' end as date_expected,
				{4}

			FROM stock_report_detail as rep
			left join product_template as pt on (pt.id=rep.product_tmpl_id)
			left join uom_uom as pu on (pu.id=rep.uom_id)
			{3}
			WHERE 
				1=1 and stock_move_id is not null {0}
			GROUP BY 1,2,3,4,5,6,7,pt.name, rep.transfer_type, rep.date_expected {2}
			{1}
			""".format(domain, order_by, group_by, left_join, select_from, datetime.now().strftime("%Y-%m-%d"))
		where = " WHERE date>='%s' and date<= '%s' "%(self.date_start, self.date_end)
		query = """
			-- Add indexes if not already present:
			-- CREATE INDEX idx_stock_move_product_id_date ON stock_move(product_id, date);
			-- CREATE INDEX idx_stock_move_state ON stock_move(state);
			-- CREATE INDEX idx_stock_move_location_id_dest_id ON stock_move(location_id, location_dest_id);
			SELECT * FROM (
			WITH stock_data AS (
				SELECT
					sm.id as stock_move_id,
					sm.reference,
					sm.product_id,
					sm.date,
					sm.product_qty,
					CASE WHEN sl.usage='internal' and sld.usage='internal' THEN 'internal' 
					WHEN sl.usage!='internal' and sld.usage='internal' THEN 'incoming' 
					ELSE 'outgoing' END AS transfer_type,
					CASE 
						WHEN sl.usage = 'internal' AND sld.usage != 'internal' THEN 0  -- Outgoing, expense = 0 for first row
						WHEN sl.usage != 'internal' AND sld.usage = 'internal' THEN sm.product_qty -- Incoming, income for first row
						ELSE 0
					END as income,
					CASE 
						WHEN sl.usage = 'internal' AND sld.usage != 'internal' THEN sm.product_qty -- Outgoing, expense > 0
						WHEN sl.usage != 'internal' AND sld.usage = 'internal' THEN 0 -- Incoming, expense = 0
						ELSE 0
					END as expense
				FROM
					stock_move sm
				JOIN stock_location sl ON sm.location_id = sl.id
				JOIN stock_location sld ON sm.location_dest_id = sld.id
				WHERE
					sm.state = 'done' {0}
					-- Example: and sm.product_id = 68431 and sm.company_id = 1
					-- Add any product_id and company_id filtering early to reduce rows processed
					-- AND sm.product_id = 68431 AND sm.company_id = 1
					-- AND sm.product_id = 76858 AND sm.company_id = 1
			),
			running_balance AS (
				SELECT
					stock_move_id,
					reference,
					product_id,
					date,
					transfer_type,
					income,
					expense,
					SUM(income - expense) OVER (PARTITION BY product_id ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS last_qty
				FROM stock_data
			)
			SELECT
				stock_move_id,
				reference,
				product_id,
				date,
				transfer_type,
				COALESCE(LAG(last_qty, 1, 0) OVER (PARTITION BY product_id ORDER BY date), 0) AS first_balance,  -- Use COALESCE to avoid NULL for the first row
				income,
				expense,
				last_qty as final_qty
			FROM
				running_balance
			ORDER BY
				product_id, date) as final
			{1};
		""".format(domain, where)
		print('Stock check report: ', query)
		self.env.cr.execute(query)
		query_result = self.env.cr.dictfetchall()
		# w_names = ', '.join(self.warehouse_ids.mapped('name'))

		dt = datetime.now() + timedelta(hours=8)

		report_header_name = u'Агуулахын бүртгэл, хяналтын баримт'
		if self.see_cost:
			report_header_name += ' /Өртөгөөр/'

		worksheet.merge_range(1,1,1,13 + (0 if self.see_cost else -2), self.env.user.company_id.name, h1_right)
		worksheet.merge_range(2,1,2,7, report_header_name, h1_left)
		worksheet.write(4,1, 'Салбар, нэгжийн нэр: {0}'.format(', '.join([''])), h1_left)
		worksheet.write(5,1, 'Бараа материалын бар код: ...........', h1_left)
		worksheet.write(6,1, 'Бараа материалын нэр: {0}'.format(', '.join(self.product_ids.mapped('name')) if self.product_ids else ''), h1_left)
		worksheet.write(7,1, 'Серийн дугаар: .............', h1_left)
		worksheet.write(8,1, 'Аюулгүй нөөц: .............', h1_left)
		worksheet.write(9,1, 'Хэвлэсэн огноо: {0}'.format(datetime.now().strftime('%Y-%m-%d %H:%M')), h1_left)
		
		worksheet.write(4,6, 'Баримтын дугаар: ', h1_left)
		worksheet.write(5,6, 'Дотоод код: {0}'.format(', '.join(self.product_ids.filtered(lambda r: r.default_code).mapped('default_code')) if self.product_ids else ''), h1_left)
		worksheet.write(6,6, 'Х.Н: {0}'.format(', '.join(self.product_ids.mapped('uom_name')) if self.product_ids else ''), h1_left)
		worksheet.write(7,6, 'Дуусах хугацаа: ........', h1_left)
		worksheet.write(8,6, 'Дээд нөөц: ...........', h1_left)
		worksheet.write(9,6, 'Хяналтын хугацаа: {0}-аас {1} хүртэл'.format(str(self.date_start), str(self.date_end)), h1_left)

		row = 11
		col = 1

		worksheet.merge_range(row, col, row+1, col, u"Д/д", header)
		worksheet.merge_range(row, col+1,row, col+3, u"Баримтын", header_wrap)
		worksheet.write(row+1, col+1, u"Огноо", header_wrap)
		worksheet.write(row+1, col+2, u"Төрөл", header_wrap)
		worksheet.write(row+1, col+3, u"Дугаар", header_wrap)
		worksheet.merge_range(row, col+4,row+1, col+4, u"Харилцагч", header_wrap)
		worksheet.merge_range(row, col+5,row+1, col+5, u"Барааны нэр", header_wrap)
		worksheet.merge_range(row, col+6,row+1, col+6, u"Дотоод код", header_wrap)
		worksheet.merge_range(row, col+7, row+1, col+7, u"Тоо хэмжээ", header_wrap)
		worksheet.merge_range(row, col+8, row+1, col+8, u"Нэгж Өртөг", header_wrap)
		if not self.see_cost:
			worksheet.merge_range(row, col+9, row, col+14, u"Нийт дүн /Өртөгөөр/", header_wrap)
			worksheet.write(row+1, col+9, u"Эхний үлдэгдэл", header_wrap)
			worksheet.write(row+1, col+10, u"Орлого", header_wrap)
			worksheet.write(row+1, col+11, u"Зарлага", header_wrap)
			worksheet.write(row+1, col+12, u"Хөдөлгөөнөөр орлого", header_wrap)
			worksheet.write(row+1, col+13, u"Хөдөлгөөнөөр зарлага", header_wrap)
			worksheet.write(row+1, col+14, u"Үлдэгдэл", header_wrap)
			worksheet.merge_range(row, col+15, row+1, col+15, u"Үлдэгдэл тоо хэмжээ", header_wrap)
		else:
			worksheet.merge_range(row, col+9, row, col+20, u"Нийт дүн /Өртөгөөр/", header_wrap)
			worksheet.write(row+1, col+9, u"Эхний үлдэгдэл", header_wrap)
			worksheet.write(row+1, col+10, u"Эхний өртөг", header_wrap)
			worksheet.write(row+1, col+11, u"Орлого", header_wrap)
			worksheet.write(row+1, col+12, u"Орлого өртөг", header_wrap)
			worksheet.write(row+1, col+13, u"Зарлага", header_wrap)
			worksheet.write(row+1, col+14, u"Зарлага өртөг", header_wrap)
			worksheet.write(row+1, col+15, u"Үлдэгдэл", header_wrap)
			worksheet.write(row+1, col+16, u"Үлдэгдэл өртөг", header_wrap)
			worksheet.write(row+1, col+17, u"Хөдөлгөөнөөр орлого", header_wrap)
			worksheet.write(row+1, col+18, u"Хөдөлгөөнөөр орлого өртөг", header_wrap)
			worksheet.write(row+1, col+19, u"Хөдөлгөөнөөр зарлага", header_wrap)
			worksheet.write(row+1, col+20, u"Хөдөлгөөнөөр зарлага өртөг", header_wrap)
			worksheet.merge_range(row, col+21, row+1, col+21, u"Үлдэгдэл тоо хэмжээ", header_wrap)

		row+=2
		number=1
		first_row = row
		worksheet.write(row+len(query_result)+1,3, 'Нягтлан бодогч: ', h1_left)
		worksheet.write(row+len(query_result)+3,3, 'Огноо: ', h1_left)
		query_result.sort(key=lambda x: x.get("date_expected", False))
		# worksheet.freeze_panes(7, 4)
		for item in query_result:
			# print('query_result: ', item)
			move_id = self.env['stock.move'].sudo().browse(int(item['stock_move_id']))
			if move_id.company_id.id not in self.env.user.company_ids.ids:
				continue
			picking_id = move_id.picking_id
			worksheet.write(row, col, number, contest_center)
			worksheet.write(row, col+1, str(move_id.date), contest_center)
			worksheet.write(row, col+2, item['transfer_type'], contest_center)
			worksheet.write(row, col+3, move_id.picking_id.name, contest_center)
			worksheet.write(row, col+4, move_id.picking_id.partner_id.name, contest_left)
			worksheet.write(row, col+5, move_id.product_id.name, contest_left)
			worksheet.write(row, col+6, move_id.product_id.default_code, contest_left)
			worksheet.write(row, col+7, move_id.product_uom_qty, contest_left)
			worksheet.write(row, col+8, move_id.price_unit or '', contest_right)
			# print(item)
			# if move_id.reference == "ББ-ХБ/MRP/00256":
			# 	print(aaa)
			if not self.see_cost:
				worksheet.write(row, col+9, item['first_balance'], contest_right)
				worksheet.write(row, col+10, item['income'], contest_right)
				worksheet.write(row, col+11, item['expense'], contest_right)
				worksheet.write(row, col+12, item['final_qty'] if item['transfer_type'] == 'internal' else 0, contest_right)
				worksheet.write(row, col+13, item['final_qty'] if item['transfer_type'] == 'internal' else 0, contest_right)
				worksheet.write(row, col+14, item['final_qty'], contest_right)
				worksheet.write(row, col+15, item['final_qty'], contest_right)
			else:
				worksheet.write(row, col+9, item['first_balance'], contest_right)
				worksheet.write(row, col+10, item['first_balance']*move_id.price_unit, contest_right)
				worksheet.write(row, col+11, item['income'], contest_right)
				worksheet.write(row, col+12, item['income']*move_id.price_unit, contest_right)
				worksheet.write(row, col+13, item['expense'], contest_right)
				worksheet.write(row, col+14, item['expense']*move_id.price_unit, contest_right)
				worksheet.write(row, col+15, item['final_qty'] if item['transfer_type'] == 'internal' else 0, contest_right)
				worksheet.write(row, col+16, item['final_qty']*move_id.price_unit, contest_right)
				worksheet.write(row, col+17, item['final_qty'] if item['transfer_type'] == 'internal' else 0, contest_right)
				worksheet.write(row, col+18, item['final_qty']*move_id.price_unit if item['transfer_type'] == 'internal' else 0, contest_right)
				worksheet.write(row, col+19, item['final_qty'] if item['transfer_type'] == 'internal' else 0, contest_right)
				worksheet.write(row, col+20, item['final_qty'], contest_right)
				worksheet.write(row, col+21, item['final_qty'], contest_right)

			row += 1
			number += 1
		# SUM
		if not self.see_cost:
			worksheet.write_formula(row, col+9, '{=SUM('+self._symbol(first_row, col+9) +':'+ self._symbol(row-1, col+9)+')}', contest_right)
			worksheet.write(row, col+10, '{=SUM('+self._symbol(first_row, col+10) +':'+ self._symbol(row-1, col+10)+')}', contest_right)
			worksheet.write(row, col+11, '{=SUM('+self._symbol(first_row, col+11) +':'+ self._symbol(row-1, col+11)+')}', contest_right)
			worksheet.write(row, col+12, '{=SUM('+self._symbol(first_row, col+12) +':'+ self._symbol(row-1, col+12)+')}', contest_right)
			worksheet.write(row, col+13, '{=SUM('+self._symbol(first_row, col+13) +':'+ self._symbol(row-1, col+13)+')}', contest_right)
			worksheet.write(row, col+14, '{=SUM('+self._symbol(first_row, col+14) +':'+ self._symbol(row-1, col+14)+')}', contest_right)
			worksheet.write(row, col+15, '{=SUM('+self._symbol(first_row, col+15) +':'+ self._symbol(row-1, col+15)+')}', contest_right)
		else:
			worksheet.write(row, col+9, '{=SUM('+self._symbol(first_row, col+9) +':'+ self._symbol(row-1, col+9)+')}', contest_right)
			worksheet.write(row, col+10, '{=SUM('+self._symbol(first_row, col+10) +':'+ self._symbol(row-1, col+10)+')}', contest_right)
			worksheet.write(row, col+11, '{=SUM('+self._symbol(first_row, col+11) +':'+ self._symbol(row-1, col+11)+')}', contest_right)
			worksheet.write(row, col+12, '{=SUM('+self._symbol(first_row, col+12) +':'+ self._symbol(row-1, col+12)+')}', contest_right)
			worksheet.write(row, col+13, '{=SUM('+self._symbol(first_row, col+13) +':'+ self._symbol(row-1, col+13)+')}', contest_right)
			worksheet.write(row, col+14, '{=SUM('+self._symbol(first_row, col+14) +':'+ self._symbol(row-1, col+14)+')}', contest_right)
			worksheet.write(row, col+15, '{=SUM('+self._symbol(first_row, col+15) +':'+ self._symbol(row-1, col+15)+')}', contest_right)
			worksheet.write(row, col+16, '{=SUM('+self._symbol(first_row, col+16) +':'+ self._symbol(row-1, col+16)+')}', contest_right)
			worksheet.write(row, col+17, '{=SUM('+self._symbol(first_row, col+17) +':'+ self._symbol(row-1, col+17)+')}', contest_right)
			worksheet.write(row, col+18, '{=SUM('+self._symbol(first_row, col+18) +':'+ self._symbol(row-1, col+18)+')}', contest_right)
			worksheet.write(row, col+19, '{=SUM('+self._symbol(first_row, col+19) +':'+ self._symbol(row-1, col+19)+')}', contest_right)
			worksheet.write(row, col+20, '{=SUM('+self._symbol(first_row, col+20) +':'+ self._symbol(row-1, col+20)+')}', contest_right)
			worksheet.write(row, col+21, '{=SUM('+self._symbol(first_row, col+21) +':'+ self._symbol(row-1, col+21)+')}', contest_right)

		worksheet.set_column('A:A', 5)
		worksheet.set_column('B:B', 13)
		worksheet.set_column('C:C', 13)
		worksheet.set_column('D:D', 13)
		worksheet.set_column('E:O', 14)
		worksheet.set_column('I:J', 25)
		worksheet.set_column('K:Z', 25)
		return workbook

	def export_report(self):
		# ctx = dict(self._context)
		output = BytesIO()
		workbook = xlsxwriter.Workbook(output)
		file_name = 'Агуулахын бүртгэл, хяналтын баримт.xlsx'
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
