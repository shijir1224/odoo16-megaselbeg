from odoo import api, fields, models
from datetime import datetime, timedelta

class StockWarehouse(models.Model):
	_inherit = 'stock.warehouse'

	is_view_po = fields.Boolean(string='ХА-ын агуулах')

class StockReportDetail(models.Model):
	_inherit = "stock.report.detail"

	product_specification = fields.Char(string='Барааны үзүүлэлт')
	# product_brand_id = fields.Many2one('product.brand', string='Бренд')

	def _select(self):
		select_str = super(StockReportDetail, self)._select()
		select_str += """
			,pt.product_specification as product_specification
		"""
		return select_str

	def _select2(self):
		select_str = super(StockReportDetail, self)._select2()
		select_str += """
			,pt.product_specification as product_specification
		"""
		return select_str

	def _select3(self):
		select_str = super(StockReportDetail, self)._select3()
		select_str += """
			,pt.product_specification as product_specification
		"""
		return select_str

	def _select4(self):
		select_str = super(StockReportDetail, self)._select4()
		select_str += """
			,pt.product_specification as product_specification
		"""
		return select_str

	def _select_main(self):
		select_str = super(StockReportDetail, self)._select_main()
		select_str += """
			,product_specification
		"""
		return select_str

class ProductIncomeExpenseReport(models.Model):
	_inherit = "product.income.expense.report"

	product_specification = fields.Char(string='Барааны үзүүлэлт')

	def _select(self):
		select_str = super(ProductIncomeExpenseReport, self)._select()
		select_str += """
			,pt.product_specification as product_specification
		"""
		return select_str

class ProductDetailedIncomeExpenseReport(models.TransientModel):
	_inherit = "product.detailed.income.expense"

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
		if self.move_type == 'income_expense':
			if self.with_attribute:
				left_join += """ left join product_attribute_value_product_product_rel val_rel on (val_rel.product_product_id=rep.product_id)
					left join product_attribute_value attr on (val_rel.product_attribute_value_id=attr.id) """
				select_from += """ case when NULLIF(count(distinct attr.name),0)>0  then pt.name||' ('||coalesce(STRING_AGG(distinct attr.name,','),'')||')' else pt.name end as product_name, 
						case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.qty_first)/NULLIF(count(distinct attr.name),1) else sum(rep.qty_first) end as qty_first,
						case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.total_price_first)/NULLIF(count(distinct attr.name),1)  else sum(rep.total_price_first) end as total_price_first,
						case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.qty_last)/NULLIF(count(distinct attr.name),1)  else sum(rep.qty_last) end as qty_last,
						case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.total_price_last)/NULLIF(count(distinct attr.name),1)  else sum(rep.total_price_last) end as total_price_last,
						case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.qty_income)/NULLIF(count(distinct attr.name),1)  else sum(rep.qty_income) end as qty_income,
						case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.total_price_income)/NULLIF(count(distinct attr.name),1)  else sum(rep.total_price_income) end as total_price_income,
						case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.qty_expense)/NULLIF(count(distinct attr.name),1)  else sum(rep.qty_expense) end as qty_expense,
						case when NULLIF(count(distinct attr.name),0)>0 then sum(rep.total_price_expense)/NULLIF(count(distinct attr.name),1)  else sum(rep.total_price_expense) end as total_price_expense"""
			else:
				select_from += """ pt.name as product_name,
						sum(rep.qty_first) as qty_first,
						sum(rep.total_price_first) as total_price_first,
						sum(rep.qty_last) as qty_last,
						sum(rep.total_price_last) as total_price_last,
						sum(rep.qty_income) as qty_income,
						sum(rep.total_price_income) as total_price_income,
						sum(rep.qty_expense) as qty_expense,
						sum(rep.total_price_expense) as total_price_expense """
		else:
			select_from += " 'else' as else"
		if self.move_type == 'income_expense':
			query1 = """
					SELECT 
						rep.product_id,
						rep.default_code,
						rep.product_code,
						rep.barcode,
						pu.name as uom_name,
						rep.categ_id,
						pt.product_specification,
						pb.name as product_brand,
						{4}
						
					FROM stock_report_detail as rep
					left join product_template as pt on (pt.id=rep.product_tmpl_id)
					left join uom_uom as pu on (pu.id=rep.uom_id)
					left join product_brand as pb on (pb.id=pt.product_brand_id)
					{3}
					WHERE 
						1=1 {0}
					GROUP BY 1,2,3,4,5,6,7,8,pt.name {2}
					{1}
				""".format(domain, order_by, group_by, left_join, select_from)
		elif self.move_type == 'expense':
			query1 = """
				SELECT 
					rep.stock_move_id,
					rep.product_id,
					rep.default_code,
					rep.product_code,
					rep.barcode,
					pt.product_specification,
					pb.name as product_brand,
					pu.name as uom_name,
					rep.categ_id,
					{4}
					
				FROM product_income_expense_report as rep
				left join product_template as pt on (pt.id=rep.product_tmpl_id)
				left join product_brand as pb on (pb.id=pt.product_brand_id)
				left join uom_uom as pu on (pu.id=rep.uom_id)
				{3}
				WHERE 
					1=1 {0}
				GROUP BY 1,2,3,4,5,6,7,8,9,pt.name {2}
				{1}
			 """.format(domain, order_by, group_by, left_join, select_from)
		# print('download query1: ', query1)
		self.env.cr.execute(query1)
		query_result = self.env.cr.dictfetchall()
		w_names = ', '.join(self.warehouse_id.mapped('name'))


		dt = datetime.now() + timedelta(hours=8)

		report_header_name = u'Бараа материалын дэлгэрэнгүй тайлан'
		if self.move_type == 'expense':
			report_header_name = u'Дотоод Зарлагын тайлан'

		worksheet.write(1,3, report_header_name, h1)
		worksheet.write(2,0, u"Агуулах: " + w_names, contest_left0)
		worksheet.write(3,0, u"Тайлан бэлдсэн: " + str(fields.Datetime.to_string(dt)), contest_left0)
		worksheet.write(4,0, u"Тайлант үеийн хугацаа: " + str(self.date_start) +" ~ "+ str(self.date_end), contest_left0)
		worksheet.write(5,0, u"Дотоод хөдөлгөөн: Оруулахгүй" if self.included_internal else u"Дотоод хөдөлгөөн: Орсон", contest_left0)
		
		get_cost = self.sudo().see_value
		get_list_price = self.sudo().see_list_price
		get_see_account = self.sudo().see_account
		row = 6
		col = 0
		# report income expense
		if self.move_type == 'income_expense':
			worksheet.write(row, col, u"№", header)
			worksheet.write(row, col+1, u"Код", header_wrap)
			worksheet.write(row, col+2, u"Эдийн дугаар", header_wrap)
			worksheet.write(row, col+3, u"Бараа", header_wrap)
			worksheet.write(row, col+4, u"Хэмжих нэгж", header_wrap)
			worksheet.write(row, col+5, u"Баркод", header_wrap)
			worksheet.write(row, col+6, u"Эхний үлдэгдэл", header_wrap)
			if get_cost:
				worksheet.write(row, col+7, u"Өртөг Эхний үлдэгдэл", header_wrap)
				col+=1
			worksheet.write(row, col+7, u"Орлого", header_wrap)
			if get_cost:
				worksheet.write(row, col+8, u"Өртөг Орлого", header_wrap)
				col+=1
			worksheet.write(row, col+8, u"Зарлага", header_wrap)
			if get_cost:
				worksheet.write(row, col+9, u"Өртөг Зарлага", header_wrap)
				col+=1
			worksheet.write(row, col+9, u"Эцсийн үлдэгдэл", header_wrap)
			if get_cost:
				worksheet.write(row, col+10, u"Өртөг Эцсийн үлдэгдэл", header_wrap)
				col+=1

			if get_cost:
				worksheet.write(row, col+10, u"Өртөг", header_wrap)
				col += 1
			if get_list_price:
				worksheet.write(row, col+10, u"Зарах үнэ", header_wrap)
				col += 1

			worksheet.write(row, col+10, u"Барааны ангилал", header_wrap)
			col += 1
			if get_see_account:
				worksheet.write(row, col+10, u"Данс", header_wrap)
				col += 1
			worksheet.write(row, col+10, u"Барааны үзүүлэлт", header_wrap)
			worksheet.write(row, col+11, u"Бренд", header_wrap)

			sum_col = col+12
			worksheet.freeze_panes(7, 4)
			row+=1
			categ_ids = []
			number=1
			first_categ = 0
			save_rows = []
			first_first_row = row
			first_row = row
			row_categ_index = 'P:P'
			for item in query_result:
				# print('query_result: ', row ,'==', item)
				if not self.no_category_total and first_categ!=item['categ_id']:
					categ_name_print = item['complete_name'] or ''
					worksheet.write(row, 0, categ_name_print, categ_name)
					for cc in range(1, sum_col):
						worksheet.write(row, cc, '', categ_name)
					first_categ = item['categ_id']
					last_row = row
					if len(save_rows)>0:
						last_row = save_rows[len(save_rows)-1]['current_row']
					save_rows.append({'last_row': last_row,'first_row': first_row , 'row_1': row-1, 'current_row': row})
					row += 1
					first_row = row
				product_name = item['product_name'] if item.get('product_name') else ''
				uom_name = item['uom_name'] if item.get('uom_name') else ''
				if isinstance(product_name, dict):
					product_name = product_name[self.env.user.lang] if product_name.get(self.env.user.lang) else product_name['en_US']
				if isinstance(uom_name, dict):
					uom_name = uom_name[self.env.user.lang] if uom_name.get(self.env.user.lang) else uom_name['en_US']
				# product_name = self.env['product.product'].browse(item['product_id']).display_name
				default_code = item['default_code'] or ''
				product_code = item['product_code'] or ''
				barcode = item['barcode'] or ''
				product_specification = item['product_specification'] or ''
				col = 0
				worksheet.write(row, col, number, contest_center)
				worksheet.write(row, col+1, default_code, contest_center)
				worksheet.write(row, col+2, product_code, contest_center)
				worksheet.write(row, col+3, product_name, contest_left)
				worksheet.write(row, col+4, uom_name, contest_center)
				worksheet.write(row, col+5, barcode, contest_center)
				worksheet.write(row, col+6, item['qty_first'], contest_right)
				if get_cost:
					worksheet.write(row, col+7, item['total_price_first'], contest_right)
					col+=1
				worksheet.write(row, col+7, item['qty_income'], contest_right)
				if get_cost:
					worksheet.write(row, col+8, item['total_price_income'], contest_right)
					col+=1
				worksheet.write(row, col+8, item['qty_expense'], contest_right)
				if get_cost:
					worksheet.write(row, col+9, item['total_price_expense'], contest_right)
					col+=1
				worksheet.write(row, col+9, item['qty_last'], contest_right)
				if get_cost:
					if item['qty_last'] == 0.0:
						worksheet.write(row, col + 10, 0.0, contest_right)
					else:
						worksheet.write(row, col+10, item['total_price_last'], contest_right)
					col+=1
				if get_cost:
					worksheet.write(row, col + 10, self.get_product_cost(item['product_id']), contest_right)
					col += 1
				if get_list_price:
					worksheet.write(row, col + 10, self.get_product_list_price(item['product_id']), contest_right)
					col += 1
				worksheet.write(row, col+10, item['complete_name'] or '', contest_left)
				col += 1
				if get_see_account:
					worksheet.write(row, col + 10, self.get_product_account(item['categ_id']), contest_right)
					col += 1
				worksheet.write(row, col+10, item['product_specification'] or '', contest_left)
				worksheet.write(row, col+11, item['product_brand'] or '', contest_left)

				row += 1
				number += 1
			sum_val1 = ''
			sum_val2 = ''
			sum_val3 = ''
			sum_val4 = ''
			sum_val5 = ''
			sum_val6 = ''
			sum_val7 = ''
			sum_val8 = ''
			if not self.no_category_total:
				last_row = row
				if len(save_rows)>0:
					last_row = save_rows[len(save_rows)-1]['current_row']
				save_rows.append({'last_row': last_row,'first_row': first_row , 'row_1': row-1, 'current_row': False})
				for cc in save_rows:
					last_row = cc['last_row']
					first_row = cc['first_row']
					row_1 = cc['row_1']
					current_row = cc['current_row']
					col = 0
					sum_val1 += '+'+(self._symbol(current_row, col+6) if current_row else '0')
					worksheet.write_formula(last_row, col+6,'{=sum('+ self._symbol(first_row, col+6)+':'+ self._symbol(row_1,col+6) +')}', categ_right)
					if get_cost:
						sum_val2 += '+'+(self._symbol(current_row, col+7) if current_row else '0')
						worksheet.write_formula(last_row, col+7,'{=sum('+ self._symbol(first_row, col+7)+':'+ self._symbol(row_1,col+7) +')}', categ_right)
						col+=1
					sum_val3 += '+'+(self._symbol(current_row, col+7) if current_row else '0')
					worksheet.write_formula(last_row, col+7,'{=sum('+ self._symbol(first_row, col+7)+':'+ self._symbol(row_1,col+7) +')}', categ_right)
					if get_cost:
						sum_val4 += '+'+(self._symbol(current_row, col+8) if current_row else '0')
						worksheet.write_formula(last_row, col+8,'{=sum('+ self._symbol(first_row, col+8)+':'+ self._symbol(row_1,col+8) +')}', categ_right)
						col+=1
					sum_val5 += '+'+(self._symbol(current_row, col+8) if current_row else '0')
					worksheet.write_formula(last_row, col+8,'{=sum('+ self._symbol(first_row, col+8)+':'+ self._symbol(row_1,col+7) +')}', categ_right)
					if get_cost:
						sum_val6 += '+'+(self._symbol(current_row, col+9) if current_row else '0')
						worksheet.write_formula(last_row, col+9,'{=sum('+ self._symbol(first_row, col+9)+':'+ self._symbol(row_1,col+9) +')}', categ_right)
						col+=1
					sum_val7 += '+'+(self._symbol(current_row, col+9) if current_row else '0')
					worksheet.write_formula(last_row, col+9,'{=sum('+ self._symbol(first_row, col+9)+':'+ self._symbol(row_1,col+9) +')}', categ_right)
					if get_cost:
						sum_val8 += '+'+(self._symbol(current_row, col+10) if current_row else '0')
						worksheet.write_formula(last_row, col+10,'{=sum('+ self._symbol(first_row, col+10)+':'+ self._symbol(row_1,col+10) +')}', categ_right)
						col+=1
			else:
				col = 0
				sum_val1 = self._symbol(first_first_row, col+6)+':'+ self._symbol(row-1,col+5)
				if get_cost:
					sum_val2 = self._symbol(first_first_row, col+7)+':'+ self._symbol(row-1,col+6)
					col+=1
				sum_val3 = self._symbol(first_first_row, col+7)+':'+ self._symbol(row-1,col+6)
				if get_cost:
					sum_val4 = self._symbol(first_first_row, col+8)+':'+ self._symbol(row-1,col+7)
					col+=1
				sum_val5 = self._symbol(first_first_row, col+8)+':'+ self._symbol(row-1,col+7)
				if get_cost:
					sum_val6 = self._symbol(first_first_row, col+9)+':'+ self._symbol(row-1,col+8)
					col+=1
				sum_val7 = self._symbol(first_first_row, col+9)+':'+ self._symbol(row-1,col+8)
				if get_cost:
					sum_val8 = self._symbol(first_first_row, col+10)+':'+ self._symbol(row-1,col+9)
					col+=1
			col = 0
			worksheet.write_formula(row, col+6,'{=sum('+ sum_val1 +')}', footer)
			if get_cost:
				worksheet.write_formula(row, col+7,'{=sum('+ sum_val2 +')}', footer)
				col+=1
			worksheet.write_formula(row, col+7,'{=sum('+ sum_val3 +')}', footer)
			if get_cost:
				worksheet.write_formula(row, col+8,'{=sum('+ sum_val4 +')}', footer)
				col+=1
			worksheet.write_formula(row, col+8,'{=sum('+ sum_val5 +')}', footer)
			if get_cost:
				worksheet.write_formula(row, col+9,'{=sum('+ sum_val6 +')}', footer)
				col+=1
			worksheet.write_formula(row, col+9,'{=sum('+ sum_val7 +')}', footer)
			if get_cost:
				worksheet.write_formula(row, col+10,'{=sum('+ sum_val8 +')}', footer)
				col+=1
			worksheet.set_column('A:A', 5)
			worksheet.set_column('B:B', 13)
			worksheet.set_column('C:C', 13)
			worksheet.set_column('D:D', 35)
			worksheet.set_column('J:J', 14)
			worksheet.set_column('E:O', 14)
			worksheet.set_column('K:K', 45)

			account_row_categ_index = 'Q:Q'
			if not get_cost and not get_list_price:
				row_categ_index = 'J:J'
				account_row_categ_index = 'K:K'
			if get_cost and not get_list_price:
				row_categ_index = 'O:O'
				account_row_categ_index = 'P:P'
			if not get_cost and get_list_price:
				row_categ_index = 'K:K'
				account_row_categ_index = 'L:L'
			worksheet.set_column(row_categ_index, 35)
			if get_see_account:
				worksheet.set_column(account_row_categ_index, 20)
			# print(aa)
		# report expense
		elif self.move_type == 'expense':
			worksheet.write(row, col, u"№", header)
			worksheet.write(row, col+1, u"Огноо", header_wrap)
			worksheet.write(row, col+2, u"Баримтын дугаар", header_wrap)
			worksheet.write(row, col+3, u"Код", header_wrap)
			worksheet.write(row, col+4, u"Эдийн дугаар", header_wrap)
			worksheet.write(row, col+5, u"Бараа", header_wrap)
			worksheet.write(row, col+6, u"Хөдөлгөөний дугаар", header_wrap)
			worksheet.write(row, col+7, u"Шинжилгээний данс", header_wrap)
			worksheet.write(row, col+8, u"Харилцагч", header_wrap)
			worksheet.write(row, col+9, u"Тоо хэмжээ", header_wrap)
			worksheet.write(row, col+10, u"Буцаасан тоо хэмжээ", header_wrap)
			worksheet.write(row, col+11, u"Нэгж өртөг", header_wrap)
			worksheet.write(row, col+12, u"Өртөг дүн", header_wrap)
			worksheet.write(row, col+13, u"Буцаасан өртөг дүн", header_wrap)
			worksheet.write(row, col+14, u"Цэвэр өртөг дүн", header_wrap)
			worksheet.write(row, col+15, u"Барааны үзүүлэлт", header_wrap)
			worksheet.write(row, col+16, u"Бренд", header_wrap)

			sum_col = col+10
			worksheet.freeze_panes(7, 4)
			row+=1
			categ_ids = []
			number=1
			first_categ = 0
			save_rows = []
			first_first_row = row
			first_row = row
			row_categ_index = 'P:P'
			for item in query_result:
				move_id = self.env['stock.move'].browse(int(item['stock_move_id']))
				account_move_id = self.env['account.move'].search([('stock_move_id','=',int(item['stock_move_id'])), ('state','=','posted')])
				def get_move_refund_total(move_id, date_from, date_to):
					move = self.env['stock.move'].browse(move_id)
					self._cr.execute("SELECT SUM(coalesce((m.product_qty / u.factor * u2.factor),0)) AS qty, "
									"SUM(coalesce((m.price_unit * m.product_qty / u.factor * u2.factor),0)) AS cost "
								"FROM stock_move AS m "
									"JOIN product_product AS pp ON (m.product_id = pp.id) "
									"JOIN product_template AS pt ON (pp.product_tmpl_id = pt.id) "
									"JOIN uom_uom AS u ON (m.product_uom = u.id) "
									"JOIN uom_uom AS u2 ON (pt.uom_id = u2.id) "
								"WHERE m.origin_returned_move_id = %s AND m.location_dest_id = %s "
									"AND m.state = 'done' "
									"AND m.date >= %s AND m.date <= %s ", (move_id, move.location_id.id, date_from + ' 00:00:00', date_to + ' 23:59:59'))
					result = self._cr.dictfetchall()
					qty = 0
					cost = 0
					for r in result:
						if r['qty']:
							qty += r['qty']
						if r['cost']:
							cost += r['cost']
					return qty, cost
				refund_qty, refund_total_cost = get_move_refund_total(int(item['stock_move_id']), str(self.date_start), str(self.date_end))
				worksheet.write(row, col, number, contest_center)
				worksheet.write(row, col+1, str(move_id.date.date()) if move_id.date else '', contest_center)
				worksheet.write(row, col+2, move_id.reference, contest_center)
				worksheet.write(row, col+3, move_id.product_id.default_code, contest_center)
				worksheet.write(row, col+4, move_id.product_id.product_code, contest_center)
				worksheet.write(row, col+5, move_id.product_id.name, contest_center)
				worksheet.write(row, col+6, account_move_id.name, contest_left)
				worksheet.write(row, col+7, '', contest_left)
				worksheet.write(row, col+8, account_move_id.partner_id.name, contest_center)
				worksheet.write(row, col+9, move_id.quantity_done, contest_center)
				worksheet.write(row, col+10, refund_qty, contest_right)
				worksheet.write(row, col+11, move_id.price_unit, contest_right)
				worksheet.write(row, col+12, move_id.niit_urtug, contest_right)
				worksheet.write(row, col+13, refund_total_cost, contest_right)
				worksheet.write(row, col+14, move_id.niit_urtug - refund_total_cost, contest_right)
				worksheet.write(row, col+15, move_id.product_id.product_specification, contest_center)
				worksheet.write(row, col+16, move_id.product_id.product_brand_id.name or '', contest_center)

				row += 1
				number += 1
			worksheet.set_column('A:A', 5)
			worksheet.set_column('B:B', 13)
			worksheet.set_column('C:C', 13)
			worksheet.set_column('D:D', 35)
			worksheet.set_column('J:J', 14)
			worksheet.set_column('E:O', 14)
			worksheet.set_column('K:K', 14)
		return workbook