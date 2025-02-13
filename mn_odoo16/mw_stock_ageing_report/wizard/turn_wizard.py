# -*- coding: utf-8 -*-

import time
from odoo import api, fields, models, _, tools
from datetime import datetime, timedelta
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64

import logging
_logger = logging.getLogger(__name__)

class stock_ageing_wizard(models.TransientModel):
    _inherit = "stock.ageing.wizard"

    def open_stock_turn_view(self):
        action = self.env.ref('mw_stock_ageing_report.action_stock_turn_report')
        vals = action.read()[0]
        domain = []
        product_dom = ''
        product_tmpl_dom = ''
        categ_dom = ''
        warehouse_dom = ''
        if self.product_ids:
            product_dom = ' and ll.product_id in %s '% (self.get_tuple(self.product_ids.ids))
        if self.product_tmpl_ids:
            product_tmpl_dom = ' and ll.product_tmpl_id in %s '% (self.get_tuple(self.product_tmpl_ids.ids))
        if self.categ_ids:
            categ_dom = ' and ll.categ_id in %s '% (self.get_tuple(self.categ_ids.ids))
        if self.warehouse_ids:
            warehouse_dom = ' and ll.warehouse_id in %s '% (self.get_tuple(self.warehouse_ids.ids))
            
        query = """
            insert into stock_turn_report (report_date, report_id, warehouse_id, categ_id, 
            product_id, product_tmpl_id, qty, price_unit, total_price, date, in_date_count, in_date_count_mid,date_range)
            SELECT '{0}',{1},*,
            in_date_count as in_date_count_mid,
            CASE WHEN in_date_count <= 30 THEN '1_0_30'
                WHEN 31 <= in_date_count and in_date_count <= 180 THEN '2_31_180'
                WHEN 181 <= in_date_count and in_date_count <= 365 THEN '3_181_365'
                WHEN 366 <= in_date_count and in_date_count <= 730 THEN '4_366_730' ELSE '5_731_up' END as date_range
            from (
            SELECT 
                ll.warehouse_id,
                ll.categ_id,
                ll.product_id,
                ll.product_tmpl_id,
                sum(ll.used_qty) as qty,
                max(ll.used_price_unit) as price_unit,
                sum(ll.used_total_price) as total_price,
                st_l.max_date as max_date,
                DATE_PART('day', '{0}'::timestamp - st_l.max_date::timestamp)+1  as in_date_count
            FROM stock_turn_report_balance as ll
            left join (SELECT 
                ll2.product_id as product_left_id,
                coalesce(max(pp.date_ageing_first),max(ll2.date)) as max_date
              FROM stock_turn_report_balance as ll2
              left join product_product pp on (pp.id=ll2.product_id)
              where ll2.transfer_type='incoming'
              and ll2.date <= '{0}'
              group by product_id) as st_l on (st_l.product_left_id=ll.product_id)
            where ll.date <= '{0}' {2} {3} {4} {5}
            group by 1,2,3,4,8
            ) as tttt
        """ .format(self.date, self.id, product_dom, product_tmpl_dom, categ_dom, warehouse_dom)
        # print query
        self.env.cr.execute(query)
        domain.append(('report_id','=',self.id))
        vals['domain'] = domain
        return vals
    
    def get_tuple(self, obj):
        if len(obj) > 1:
            return str(tuple(obj))
        else:
            return "("+str(obj[0])+") "
            
    def open_stock_turn_download(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        file_name = 'Нөөцийн эргэц'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#bfbfbf')


        #fce4d6
        #d6dce4

        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(9)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        header_wrap.set_bg_color('#fce4d6')

        footer = workbook.add_format({'bold': 1})
        footer.set_text_wrap()
        footer.set_font_size(9)
        footer.set_align('center')
        footer.set_align('vcenter')
        footer.set_border(style=1)
        footer.set_bg_color('#d6dce4')
        footer.set_num_format('#,##0.00')

        footer2 = workbook.add_format()
        footer2.set_text_wrap()
        footer2.set_font_size(9)
        footer2.set_align('right')
        footer2.set_align('vcenter')
        footer2.set_border(style=1)
        footer2.set_bg_color('#d6dce4')
        footer2.set_num_format('#,##0.00')

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_num_format('#,##0.00')

        contest_right2 = workbook.add_format({'bold': 1})
        contest_right2.set_text_wrap()
        contest_right2.set_font_size(9)
        contest_right2.set_align('right')
        contest_right2.set_align('vcenter')
        contest_right2.set_border(style=1)
        contest_right2.set_num_format('#,##0.00')
        contest_right2.set_bg_color('#bfbfbf')

        contest_right_green = workbook.add_format()
        contest_right_green.set_text_wrap()
        contest_right_green.set_font_size(9)
        contest_right_green.set_align('right')
        contest_right_green.set_align('vcenter')
        contest_right_green.set_font_color('green')
        contest_right_green.set_num_format('#,##0.00')

        contest_left = workbook.add_format()
        # contest_left.set_text_wrap()
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

        

        row = 1
        worksheet = workbook.add_worksheet(file_name)
        worksheet.merge_range(row, 0, row+1, 0, 'Барааны нийлүүлэгч', header)
        worksheet.merge_range(row, 1, row+1, 1, 'Барааны код', header)
        worksheet.merge_range(row, 2, row+1, 2, 'Барааны нэр', header)
        worksheet.merge_range(row, 3, row+1, 3, 'Барааны ангилал', header)
        worksheet.merge_range(row, 4, row, 6, 'Нөөцөнд байгаа барааны өртөг', header)
        worksheet.merge_range(row, 7, row, 9, 'Хэргэлсэн барааны өртөг (12 сар)', header)
        worksheet.merge_range(row, 10, row+1, 10, 'Нөөцийн эргэц', footer)
        worksheet.merge_range(row, 11, row+1, 11, 'Categories', contest_center)
        worksheet.write(row+1, 4, u"Тоо", header)
        worksheet.write(row+1, 5, u"Өртөг", header)
        worksheet.write(row+1, 6, u"Нийт", header_wrap)
        worksheet.write(row+1, 7, u"Тоо", header)
        worksheet.write(row+1, 8, u"Өртөг", header)
        worksheet.write(row+1, 9, u"Нийт", header_wrap)
        row += 2

        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 18)
        worksheet.set_column('D:D', 21)
        worksheet.set_column('F:F', 18)
        worksheet.set_column('G:G', 21)
        worksheet.freeze_panes(3, 0)

        query_where = []
        query_where2 = []
        if self.product_ids:
            query_where.append(' product_id in %s '%(self.get_tuple(self.product_ids.ids)))
            query_where2.append(' product_id in %s '%(self.get_tuple(self.product_ids.ids)))
        if self.product_tmpl_ids:
            query_where.append(' product_tmpl_id in %s '%(self.get_tuple(self.product_tmpl_ids.ids)))
            query_where2.append(' product_tmpl_id in %s '%(self.get_tuple(self.product_tmpl_ids.ids)))
        if self.categ_ids:
            query_where.append(' categ_id in %s '%(self.get_tuple(self.categ_ids.ids)))
            query_where2.append(' categ_id in %s '%(self.get_tuple(self.categ_ids.ids)))
        query_where.append(" state = 'done' ")
        query_where2.append(" state = 'done' ")
        if self.location_ids:
            query_where.append(' location_id in %s '%(self.get_tuple(self.location_ids.ids)))
            query_where2.append(' location_id in %s '%(self.get_tuple(self.location_ids.ids)))
        elif self.warehouse_ids:
            query_where.append(' warehouse_id in %s '%(self.get_tuple(self.warehouse_ids.ids)))
            query_where2.append(' warehouse_id in %s '%(self.get_tuple(self.warehouse_ids.ids)))

        query_where2.append(" date_expected >= '%s' and date_expected <= '%s'"%(self.date, self.date_end))
        query_where2.append(" transfer_type = 'outgoing' ")


        query_where.append(" date_expected <= '%s'"%(self.date_end))
        # Dotood hud oruuldag bolgov
        # query_where.append(" transfer_type != 'internal'")
        
        query_real = ' and '.join(query_where)
        query_real2 = ' and '.join(query_where2)
        
        query = """
        select 
        product_id,
        coalesce(sum(qty), 0) as qty,
        coalesce(sum(standart_amount),0 ) as standart_amount,
        abs(coalesce(sum(qty2), 0)) as qty2,
        abs(coalesce(sum(standart_amount2), 0)) as standart_amount2
        FROM
        (
            SELECT 
                product_id,
                coalesce(sum(qty), 0) as qty,
                coalesce(sum(standart_amount),0 ) as standart_amount,
                0 as qty2,
                0 as standart_amount2
            FROM product_balance_pivot_report ll
            where {0}
             group by product_id
             having coalesce(sum(qty), 0)!=0
        UNION ALL
            SELECT 
                product_id,
                0 as qty,
                0 as standart_amount,
                coalesce(sum(qty), 0) as qty2,
                coalesce(sum(standart_amount),0 ) as standart_amount2
            FROM product_balance_pivot_report ll
            where {1}
             group by product_id
        ) as temp_ttt
        group by product_id
        
        """ .format(query_real, query_real2)
        # print (query)
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        save_row = row
        for item in records:
            # print (item)
            p_id = self.env['product.product'].browse(item['product_id'])
            code = p_id.default_code or ''
            qty = float(item['qty'] or 0)
            price_unit = float(item['standart_amount'])/qty if qty!=0 else 0
            total_price_unit = float(item['standart_amount'])

            qty2 = float(item['qty2'] or 0)
            price_unit2 = float(item['standart_amount2'])/qty2 if qty2!=0 else 0
            total_price_unit2 = float(item['standart_amount2'])
            supplier_partner_id = p_id.supplier_partner_id.name or ''
            product_name = p_id.name 
            product_category = p_id.categ_id.name or '' 

            worksheet.write(row, 0, supplier_partner_id, contest_center)
            worksheet.write(row, 1, code, contest_center)
            worksheet.write(row, 2, product_name, contest_center)
            worksheet.write(row, 3 , product_category, contest_center)
            worksheet.write(row, 4, qty, contest_center)
            worksheet.write(row, 5, price_unit, contest_right)
            worksheet.write(row, 6, total_price_unit, contest_right)
            worksheet.write(row, 7, qty2, contest_center)
            worksheet.write(row, 8, price_unit2, contest_right)
            worksheet.write(row, 9, total_price_unit2, contest_right)

            worksheet.write_formula(row, 10,'{=IFERROR('+xl_rowcol_to_cell(row, 9)+'/'+xl_rowcol_to_cell(row, 6)+',0)}', footer2)
            h8 = xl_rowcol_to_cell(row, 10)
            worksheet.write_formula(row, 11,'=IF('+h8+'=0,"Non Moving",IF('+h8+'<1,"Slow Moving",IF('+h8+'<3,"Sales Moving","Fast Moving")))', contest_right)
            row +=1
        
        worksheet.write(row, 0, 'TOTAL IN COST VALUE', contest_right2)
        worksheet.merge_range(row, 1, row, 6, '', contest_right2)
        worksheet.write_formula(row, 1,'{=SUM('+xl_rowcol_to_cell(save_row, 6)+':'+xl_rowcol_to_cell(row-1, 6)+')}', contest_right2)

        worksheet.merge_range(row, 7, row, 9, '', contest_right2)
        worksheet.write_formula(row, 7,'{=SUM('+xl_rowcol_to_cell(save_row, 9)+':'+xl_rowcol_to_cell(row-1, 9)+')}', contest_right2)

        worksheet.write_formula(row, 10,'{=IFERROR('+xl_rowcol_to_cell(row, 7)+'/'+xl_rowcol_to_cell(row, 1)+',0)}', footer2)
        h8 = xl_rowcol_to_cell(row, 9)
        worksheet.write_formula(row, 11,'=IF('+h8+'=0,"Non Moving",IF('+h8+'<1,"Slow Moving",IF('+h8+'<3,"Sales Moving","Fast Moving")))', contest_right2)

        worksheet.merge_range(row+1, 0,row+1,9, 'INVENTORY ACCURACY', contest_right2)
        worksheet.write(row+1, 10, '{=IFERROR(('+xl_rowcol_to_cell(row, 1)+'-'+xl_rowcol_to_cell(row, 7)+')/'+xl_rowcol_to_cell(row, 1)+',0)}', footer2)
        row += 2
        
        # worksheet.write(row, 6, '=SUM('+xl_rowcol_to_cell(save_row, 6)+':'+xl_rowcol_to_cell(row-1, 6)+')'+ '+' + '=SUM('+xl_rowcol_to_cell(save_row, 9)+':'+xl_rowcol_to_cell(row-1, 9)+')' + '/' + '=SUM('+xl_rowcol_to_cell(save_row, 6)+':'+xl_rowcol_to_cell(row-1, 6)+')', contest_right2)

        # worksheet.write(row, 0, u'Stock Turn', footer)
        # worksheet.write(row+1, 0, u'0', footer)
        # worksheet.write(row+2, 0, u'>0 ; <1', footer)
        # worksheet.write(row+3, 0, u'=>1 ; =<3', footer)
        # worksheet.write(row+4, 0, u'>3', footer)

        # worksheet.write(row, 1, u'Categories', contest_center)
        # worksheet.write(row+1, 1, u'Non Moving', contest_center)
        # worksheet.write(row+2, 1, u'Slow Moving', contest_center)
        # worksheet.write(row+3, 1, u'Sales Moving', contest_center)
        # worksheet.write(row+4, 1, u'Fast Moving', contest_center)

        # worksheet.write(row+6, 0, u'Assumption:', contest_center)
        # worksheet.write(row+7, 0, u'Generally stock turn is in a Good shape because it is in Sales Moving category (1,71):', contest_left)
        # worksheet.write(row+8, 0, u'But if items are taken in consideration separately, there is a problem because item 1 is not moving, item 2 is fast moving and item3/4 are slow moving:', contest_left)

        workbook.close()

        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
