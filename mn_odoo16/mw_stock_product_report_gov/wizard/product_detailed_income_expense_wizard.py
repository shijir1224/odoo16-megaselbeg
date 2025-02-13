# -*- coding: utf-8 -*-

import time
from odoo import _, tools
from datetime import datetime, timedelta
from odoo import api, fields, models
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
import logging
_logger = logging.getLogger(__name__)

class ProductDetailedIncomeExpenseReport(models.TransientModel):
    _inherit = "product.detailed.income.expense"  
    
    def export_report_delgerengui(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        worksheet = workbook.add_worksheet(u'Бараа материалын дэлгэрэнгүй бүртгэл')
        file_name = 'Бараа материалын дэлгэрэнгүй бүртгэл.xlsx'

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

        contest_left1 = workbook.add_format()
        # contest_left1.set_text_wrap()
        contest_left1.set_font_size(9)
        contest_left1.set_align('left')
        contest_left1.set_align('vcenter')
        
        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_num_format('#,##0.00')

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
        # self.date_start = self.
        if len(self.product_ids)!=1:
            raise UserError(u'Нэг бараа заавал сонгох ёстойы')
        main_product_id = self.product_ids[0]
        domain = self.get_domain([], True)
        order_by = ' ORDER BY 1 asc '
        group_by = ''
        left_join = ''
        select_from = ''
        
        select_from += """  """
        query1 = """
                SELECT 
                coalesce(rep.date_expected,'1990-10-12') as date,
                rep.stock_move_id,
                sum(rep.qty_first) as qty_first,
                sum(rep.total_price_first) as total_price_first,
                sum(rep.qty_last) as qty_last,
                sum(rep.total_price_last) as total_price_last,
                sum(rep.qty_income) as qty_income,
                sum(rep.total_price_income) as total_price_income,
                sum(rep.qty_expense) as qty_expense,
                sum(rep.total_price_expense) as total_price_expense
                FROM stock_report_detail as rep
                left join product_template as pt on (pt.id=rep.product_tmpl_id)
                left join uom_uom as pu on (pu.id=rep.uom_id)
                {3}
                WHERE 
                    1=1 {0}
                GROUP BY 1,2
                {1}
             """.format(domain, order_by, group_by, left_join, select_from)
        print (query1)

        self.env.cr.execute(query1)
        query_result = self.env.cr.dictfetchall()
        w_names = ', '.join(self.warehouse_id.mapped('name'))
        get_cost = self.sudo().see_value

        worksheet.write(0,4, u"Сангийн сайдын 2018 оны 100 дугаар тушаалын хавсралт", contest_left1)
        worksheet.write(1,3, u"Бараа материалын дэлгэрэнгүй бүртгэл", h1)
        worksheet.write(2,0, u"Материалын код", contest_left1)
        worksheet.merge_range(3, 0, 4, 0, main_product_id.default_code or '', contest_left1)
        worksheet.write(2,1, u"Материалын нэр төрөл ", contest_left1)
        worksheet.merge_range(3, 1, 4, 1, main_product_id.name, contest_left1)
        worksheet.write(2,2, u"Агуулахын Байршил", contest_left1)
        worksheet.merge_range(3, 2, 4, 2, '', contest_left1)
        worksheet.write(2,3, u"Хариуцсан нярав", contest_left1)
        worksheet.write(3,3, u"Хэмжих нэгж", contest_left1)
        worksheet.write(4,3, main_product_id.uom_id.name, contest_left1)
        worksheet.write(2,4, u"Дансны дугаар", contest_left1)
        worksheet.merge_range(3, 4, 4, 4, main_product_id.categ_id.property_stock_valuation_account_id.code or '', contest_left1)
        
        worksheet.merge_range(6, 0, 6, 2, 'Тайлант %s он %s сар'%(str(self.date_end.year),str(self.date_end.month)), contest_left1)
        worksheet.merge_range(6, 3, 6, 4, 'Бэлтгэсэн %s'%(datetime.now().strftime("%Y-%m-%d")), contest_left1)
        worksheet.merge_range(6, 11, 6, 13, 'Дэлгэрэнгүй бүртгэл БМ-1', contest_left1)
        row = 8
        col = 0
        worksheet.merge_range(row, col, row+2, col, u'Сар, өдөр', header_wrap)
        worksheet.merge_range(row, col+1, row, col+7, u'Орлого', header_wrap)
        worksheet.merge_range(row+1, col+1, row+2, col+1, u'Баримтын дугаар', header_wrap)
        worksheet.merge_range(row+1, col+2, row+1, col+4, u'Худалдан авсан', header_wrap)
        worksheet.write(row+2,col+2, u'Тоо хэмжээ', header_wrap)
        worksheet.write(row+2,col+3, u'Нэгжийн үнэ', header_wrap)
        worksheet.write(row+2,col+4, u'Дүн', header_wrap)
        worksheet.write(row+1,col+5, u'Бэлтгэх зардал', header_wrap)
        worksheet.write(row+2,col+5, u'', header_wrap)
        worksheet.merge_range(row+1, col+6, row+1, col+7, u'Өртөг', header_wrap)
        worksheet.write(row+2,col+6, u'Нэгжийн үнэ', header_wrap)
        worksheet.write(row+2,col+7, u'Бүгд', header_wrap)
        worksheet.merge_range(row, col+8, row, col+11, u'Зарлага', header_wrap)
        worksheet.write(row+1,col+8, u'Баримтын дугаар', header_wrap)
        worksheet.write(row+2,col+8, u'', header_wrap)
        worksheet.merge_range(row+1, col+9, row+2, col+9, u'Тоо хэмжээ', header_wrap)
        worksheet.merge_range(row+1, col+10, row+1, col+11, u'Өртөг', header_wrap)
        worksheet.write(row+2,col+10, u'Нэгжийн үнэ', header_wrap)
        worksheet.write(row+2,col+11, u'Бүгд', header_wrap)
        worksheet.merge_range(row, col+12, row, col+14, u'Үлдэгдэл', header_wrap)
        worksheet.write(row+1,col+12, u'Тоо хэмжээ', header_wrap)
        worksheet.write(row+2,col+12, u'', header_wrap)
        worksheet.merge_range(row+1, col+13, row+1, col+14, u'Өртөг', header_wrap)
        worksheet.write(row+2,col+13, u'Нэгжийн үнэ', header_wrap)
        worksheet.write(row+2,col+14, u'Бүгд', header_wrap)
        
        # worksheet.freeze_panes(7, 4)
        row+=3
        number=1
        first_ok = False
        first_save_row = []
        for item in query_result:
            date = item['date'] or ''
            stock_move_id = self.env['stock.move'].browse(item['stock_move_id'])
            po_ok = False
            print ('date',date," item['qty_first']", item['qty_first'])
            if str(date)=='1990-10-12' and float(item['qty_first'])!=0:
                for coo in range(col,col+12):
                    worksheet.write(row, coo, '', contest_right)
                worksheet.write(row, col+12, item['qty_first'], contest_right)
                worksheet.write(row, col+13, item['total_price_first']/item['qty_first'], contest_right)
                worksheet.write_formula(row, col+14,'{=('+ self._symbol(row, col+12)+'*'+ self._symbol(row,col+13) +')}', contest_right)
                first_save_row.append({
                    'qty': self._symbol(row, col+12),
                    'total': self._symbol(row, col+14),
                })
                first_ok = True
            else:
                worksheet.write(row, col, str(date), contest_right)
                worksheet.write(row, col+1, '', contest_right)
                po_line_id = False
                if stock_move_id.purchase_line_id and item['qty_income']>0:
                    po_ok = True
                    po_line_id = stock_move_id.purchase_line_id
                if po_ok:
                    worksheet.write(row, col+2, item['qty_income'], contest_center)
                    worksheet.write(row, col+3, po_line_id.price_unit_product, contest_right)
                    worksheet.write_formula(row, col+4,'{=('+ self._symbol(row, col+2)+'*'+ self._symbol(row,col+3) +')}', contest_right)
                    worksheet.write(row, col+5, po_line_id.total_cost_unit, contest_right)
                    worksheet.write_formula(row, col+6,'{=('+ self._symbol(row, col+7)+'/'+ self._symbol(row,col+2) +')}', contest_right)
                    worksheet.write_formula(row, col+7,'{=('+ self._symbol(row, col+4)+'+'+ self._symbol(row,col+5) +')}', contest_right)
                    for coo in range(col+8,col+15):
                        worksheet.write(row, coo, '', contest_right)
                else:
                    for coo in range(col+2,col+9):
                        worksheet.write(row, coo, '', contest_right)
                    exp = item['total_price_expense']/item['qty_expense'] if item['qty_expense']!=0 and item['total_price_expense']!=None else ''
                    worksheet.write(row, col+9, item['qty_expense'], contest_right)
                    worksheet.write(row, col+10, exp, contest_right)
                    worksheet.write_formula(row, col+11,'{=('+ self._symbol(row, col+9)+'*'+ self._symbol(row,col+10) +')}', contest_right)
                last = item['total_price_last']/item['qty_last'] if item['qty_last']!=0 and item['total_price_last']!=None else ''
                if first_ok:
                    if first_save_row:
                        sq = ''
                        st = ''
                        for ff in first_save_row:
                            sq +='+'+ff['qty']
                            st +='+'+ff['total']
                        worksheet.write_formula(row, col+12,'{=('+ sq +'+'+self._symbol(row,col+2)+'-'+self._symbol(row,col+9)+')}', contest_right)
                        worksheet.write_formula(row, col+14,'{=('+ st+'+'+self._symbol(row,col+7)+'-'+self._symbol(row,col+11)+')}', contest_right)
                        first_save_row = []
                    else:
                        worksheet.write_formula(row, col+12,'{=('+ self._symbol(row-1, col+12)+'+'+self._symbol(row,col+2)+'-'+self._symbol(row,col+9)+')}', contest_right)
                        worksheet.write_formula(row, col+14,'{=('+ self._symbol(row-1, col+14)+'+'+self._symbol(row,col+7)+'-'+self._symbol(row,col+11)+')}', contest_right)
                else:
                    first_ok = True
                    first_save_row = []
                    worksheet.write_formula(row, col+12,'{=('+self._symbol(row,col+2)+'+'+self._symbol(row,col+9)+')}', contest_right)
                    worksheet.write_formula(row, col+14,'{=('+self._symbol(row,col+7)+'-'+self._symbol(row,col+11)+')}', contest_right)
                worksheet.write_formula(row, col+13,'{=('+ self._symbol(row, col+14)+'/'+ self._symbol(row,col+12)+')}', contest_right)
            row+=1
       
        worksheet.write(row,0, u"Хөтөлсөн нягтлан бодогч ...................(                          )", contest_left1)
        worksheet.write(row+1,0, u"Хянасан ерөнхий (ахлах) нягтлан бодогч ...................(                          )", contest_left1)
        
        worksheet.set_column('H:H', 10)
        worksheet.set_column('O:O', 10)
        worksheet.set_column('E:E', 10)

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
