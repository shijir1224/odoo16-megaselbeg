# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models

class ComparisonReport(models.TransientModel):
    _name = "comparison.report"

    date_start = fields.Date(string='Огноо', required=True,
        default=time.strftime('%Y-%m-01'))
    date_end = fields.Date(string='Огноо', required=True,
        default=fields.Date.context_today)

    warehouse_ids = fields.Many2many('stock.warehouse',string='Агуулах')
    product_ids = fields.Many2many('product.product',string='Бараа')
    
    def export_report(self):
        # ===================================
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        file_name = 'internal_move_comparison_report.xlsx'

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

        # SHEET 2
        worksheet = workbook.add_worksheet(u'Харьцуулалтын тайлан')
        worksheet.write(0,2, u"Харьцуулалтын тайлан", h1)
        # TABLE HEADER
        row = 1
        worksheet.set_row(row, 26)
        worksheet.write(row, 0, u"№", header)
        worksheet.set_column('A:A', 5)
        worksheet.write(row, 1, u"Агуулах", header_wrap)
        worksheet.set_column('B:B', 15)
        worksheet.write(row, 2, u"Бар код", header_wrap)
        worksheet.set_column('C:C', 13)
        worksheet.write(row, 3, u"Бараа", header_wrap)
        worksheet.set_column('D:D', 35)
        worksheet.write(row, 4, u"Зарлагын тоо", header_wrap)
        worksheet.set_column('E:E', 12)
        worksheet.write(row, 5, u"Орлогын тоо", header_wrap)
        worksheet.set_column('F:F', 12)
        worksheet.write(row, 6, u"Буцаалт тоо", header_wrap)
        worksheet.set_column('G:G', 12)
        worksheet.write(row, 7, u"Зөрүү", header_wrap)
        worksheet.set_column('H:H', 8)
        worksheet.write(row, 8, u"Зарлагын баримт", header_wrap)
        worksheet.set_column('I:I', 12)
        worksheet.write(row, 9, u"Зарлагын огноо", header_wrap)
        worksheet.set_column('J:J', 12)
        worksheet.write(row, 10, u"Орлогын баримт", header_wrap)
        worksheet.set_column('K:K', 12)
        worksheet.write(row, 11, u"Хүлээн авсан", header_wrap)
        worksheet.set_column('L:L', 17)
        worksheet.freeze_panes(2, 5)

        where_warehouse = ""
        if self.warehouse_ids:
            if len(self.warehouse_ids.ids) > 1:
                where_warehouse = " and so.warehouse_id in %s " % str(tuple(self.warehouse_ids.ids))
            else:
                where_warehouse = " and so.warehouse_id in (%s) " % self.warehouse_ids.ids[0]
        where_product = ""
        if self.product_ids:
            if len(self.product_ids.ids) > 1:
                where_product = " and sol.product_id in %s " % str(tuple(self.product_ids.ids))
            else:
                where_product = " and sol.product_id in (%s) " % self.product_ids.ids[0]

        query = """
            SELECT 
                sw.name as warehouse_name,
                so.name as origin,
                so.picking_date as picking_date,
                sol.product_id as product_id,
                sum(sol.qty_delivered) as qty
            FROM sale_order_line as sol
            LEFT JOIN sale_order as so on so.id = sol.order_id
            LEFT JOIN stock_warehouse as sw on sw.id = so.warehouse_id
            WHERE so.state in ('sale','done') and 
                  so.validity_date >= '%s' and
                  so.validity_date <= '%s' and 
                  so.is_create_auto_purchase = 't'
                   %s 
                   %s 
            GROUP BY sw.name, so.name, so.picking_date, sol.product_id
            ORDER BY sw.name, so.picking_date, so.name, sol.product_id
        """ % (self.date_start, self.date_end, where_warehouse, where_product)
        print ('===', query)
        self.env.cr.execute(query)
        qty_result = self.env.cr.dictfetchall()
        row += 1
        number = 1

        for ll in qty_result:
            pp = self.env['product.product'].sudo().search([('id','=',ll['product_id'])], limit=1)
            worksheet.write(row, 0, number, contest_right)
            worksheet.write(row, 1, ll['warehouse_name'] or '', contest_left)
            worksheet.write(row, 2, pp.barcode, contest_center)
            worksheet.write(row, 3, pp.display_name, contest_left)
            worksheet.write(row, 4, ll['qty'], contest_right)
            # PO тоо олох
            po_qty = 0
            pos = self.env['purchase.order'].sudo().search([
                ('origin','=',ll['origin']),
                ('state','in',['purchase','done'])])
            aguulax_str = ""
            po0 = False
            for po in pos:
                po_qty += sum(po.order_line.filtered(lambda l: l.product_id.id == ll['product_id']).mapped('qty_received'))
                aguulax_str = po.branch_id.name
                po0 = po
            worksheet.write(row, 5, po_qty, contest_right)
            # PO буцаалтын тоог олох
            return_qty = 0
            ret_pos = self.env['purchase.return'].sudo().search([
                ('purchase_ids','in',pos.ids),
                ('state','in',['confirmed','done'])])
            for pr in ret_pos:
                return_qty += sum(pr.return_line.filtered(lambda l: l.product_id.id == ll['product_id']).mapped('qty'))
            if ret_pos:
                print ('==return=', ll['origin'], pos.ids, ret_pos, return_qty)
            worksheet.write(row, 6, return_qty, contest_right)
            zurvv = ll['qty'] - po_qty + return_qty
            worksheet.write(row, 7, zurvv, contest_right if zurvv == 0 else contest_right_red)
            worksheet.write(row, 8, ll['origin'], contest_center)
            worksheet.write(row, 9, str(ll['picking_date']), contest_center)
            worksheet.write(row, 10, po0.name if po0 else '-', contest_center)
            worksheet.write(row, 11, aguulax_str or '-', contest_left)
            row += 1
            number += 1

        # CLOSE ==========================================================================
        workbook.close()

        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
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



