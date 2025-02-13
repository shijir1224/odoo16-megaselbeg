# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, models
import xlsxwriter
from io import BytesIO
import base64
import logging
_logger = logging.getLogger(__name__)
from collections import defaultdict

from itertools import groupby
from operator import itemgetter

class stock_ageing_wizard(models.TransientModel):
    _name = "stock.ageing.wizard"  
    _description  = "stock ageing wizard"
    
    date = fields.Date(required=True, string=u'Огноо',default=fields.Date.context_today)
    date_end = fields.Date(required=True, string=u'Дуусах огноо',default=fields.Date.context_today)
    product_tmpl_ids = fields.Many2many('product.template', string='Барааны хувилбар', help=u"Тайланд гарах бараануудыг сонгоно")
    warehouse_ids = fields.Many2many('stock.warehouse', string='Агуулах',required=True)
    location_ids = fields.Many2many('stock.location', string='Байрлал',)
    product_ids = fields.Many2many('product.product', string='Бараанууд', help=u"Тайланд гарах барааг сонгоно")
    categ_ids = fields.Many2many('product.category', string='Барааны ангилал', help=u"Тухайн сонгосон ангилал дахь бараануудыг тайланд гаргах")
    import_wh = fields.Boolean(string='Бүх агуулах ОРУУЛАХ/АРИЛГАХ', default=False)
    day_interval = fields.Integer(string='Хугацааны интервал (хоног)', default=30)
    
    @api.onchange('import_wh')
    def onchange_all_wh_import(self):
        if self.import_wh:
            self.warehouse_ids = self.env['stock.warehouse'].search([])
        else:
            self.warehouse_ids = []
    
    def get_tuple(self, obj):
        if len(obj) > 1:
            return str(tuple(obj))
        else:
            return "("+str(obj[0])+") "

    def open_analyze_view(self):
        action = self.env.ref('mw_stock_ageing_report.action_stock_ageing_report')
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
            insert into stock_ageing_report (report_date, report_id, warehouse_id, categ_id, 
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
                sum(ll.qty) as qty,
                max(ll.price_unit) as price_unit,
                sum(ll.total_price) as total_price,
                ll.max_date as max_date,
                DATE_PART('day', '{0}'::timestamp - ll.max_date::timestamp)+1  as  in_date_count
            FROM stock_ageing_report_balance as ll
            left join (SELECT 
                ll2.product_id as product_left_id,
                coalesce(max(pp.date_ageing_first),max(ll2.date)) as removed
              FROM stock_ageing_report_balance as ll2
              left join product_product pp on (pp.id=ll2.product_id)
              where ll2.transfer_type='incoming'
              and ll2.date <= '{0}'
              group by product_id) as st_l on (st_l.product_left_id=ll.product_id)
            where ll.date <= '{0}' {2} {3} {4} {5}
            group by 1,2,3,4,8
            having sum(ll.qty) > 0
            ) as tttt
        """ .format(self.date, self.id, product_dom, product_tmpl_dom, categ_dom, warehouse_dom)
        # print(query)
        self.env.cr.execute(query)
        domain.append(('report_id','=',self.id))
        vals['domain'] = domain
        return vals

    def get_product_balance(self, warehouse_ids, date, product_ids=[], categ_ids=[]):
        '''
        Барааны үлдэгдэл авах
        :param warehouse_ids:
        :return:
        '''
        domain_val = ''
        if product_ids:
            domain_val = " and sml.product_id in %s" % (product_ids)
        if categ_ids:
            domain_val += " and pc.id in %s" % (categ_ids)

        self.env.cr.execute("""
                        SELECT
                            sm.id,
                            sl.set_warehouse_id as warehouse_id,
                            sml.location_dest_id as location_id, 
                            pt.categ_id as categ_id,
                            pc.name as categ_name,
                            sml.product_id as product_id,
                            pt.id as product_tmpl_id,
                            pp.default_code as default_code,
                            pt.name as product_name,
                            pu.name as uom_name,
                            sml.qty_done/uu.factor as qty,
                            sm.price_unit,
                            sml.qty_done/uu.factor * sm.price_unit as total_price,
                            sm.price_unit_sale,
                            sml.qty_done/uu.factor * sm.price_unit_sale as total_price_sale,
                            sm.ageing_data_ok,
                            (sml.date + interval '8 hour')::date as date,
                            case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage='internal' 
                            and sl2.usage='supplier' then 'incoming' else 'outgoing' end as transfer_type
                        FROM stock_move_line as sml
                        LEFT JOIN product_product as pp on (pp.id = sml.product_id)
                        LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
                        LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_id)
                        LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
                        LEFT JOIN stock_move as sm on (sml.move_id = sm.id)
                        LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
                        LEFT JOIN product_category as pc on (pt.categ_id = pc.id)
                        LEFT JOIN uom_uom as pu on (pt.uom_id=pu.id)
                        WHERE sml.state = 'done' and sl.set_warehouse_id in {0} and sml.date::date <= '{1}' {2}
                        UNION ALL
                        SELECT
                            sm.id,
                            sl.set_warehouse_id as warehouse_id,
                            sml.location_id as location_id,
                            pt.categ_id as categ_id,
                            pc.name as categ_name,
                            sml.product_id as product_id,
                            pt.id as product_tmpl_id,
                            pp.default_code as default_code,
                            pt.name as product_name,
                            pu.name as uom_name,
                            -(sml.qty_done/uu.factor) as qty,
                            sm.price_unit,
                            -(sml.qty_done/uu.factor * abs(sm.price_unit)) as total_price,
                            sm.price_unit_sale,
                            -(sml.qty_done/uu.factor * abs(sm.price_unit_sale)) as total_price_sale,
                            sm.ageing_data_ok,
                            (sml.date + interval '8 hour')::date as date,
                            case when sl2.usage='internal' and sl.usage='internal' then 'internal' when sl2.usage='internal' 
                            and sl.usage='supplier' then 'incoming' else 'outgoing' end as transfer_type
                        FROM stock_move_line as sml
                        LEFT JOIN product_product as pp on (pp.id = sml.product_id)
                        LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
                        LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
                        LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
                        LEFT JOIN stock_move as sm on (sml.move_id = sm.id)
                        LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
                        LEFT JOIN product_category as pc on (pt.categ_id = pc.id)
                        LEFT JOIN uom_uom as pu on (pt.uom_id=pu.id)
                        WHERE sml.state = 'done' and sl.set_warehouse_id in {0} and sml.date::date <= '{1}' {2}
                """ .format(warehouse_ids, date, domain_val))
        query_result = self.env.cr.dictfetchall()
        return query_result

    def get_product_balance1(self, warehouse_ids, date, product_ids=[], categ_ids=[]):
        '''
        Барааны үлдэгдэл авах
        :param warehouse_ids:
        :return:
        '''
        domain_val = ''
        if product_ids:
            domain_val = " and sml.product_id in %s" % (product_ids)
        if categ_ids:
            domain_val += " and pc.id in %s" % (categ_ids)

        self.env.cr.execute("""
                SELECT categ_name, product_id, default_code, product_name, sum(qty) as qty, uom_name
                    FROM (
                        SELECT
                            sl.set_warehouse_id as warehouse_id,
                            sml.location_dest_id as location_id, 
                            pt.categ_id as categ_id,
                            pc.name as categ_name,
                            sml.product_id as product_id,
                            pt.id as product_tmpl_id,
                            pp.default_code as default_code,
                            pt.name as product_name,
                            pu.name as uom_name,
                            sml.qty_done/uu.factor as qty,
                            sm.price_unit,
                            sml.qty_done/uu.factor * sm.price_unit as total_price,
                            sm.ageing_data_ok,
                            (sml.date + interval '8 hour')::date as date,
                            case when sl.usage='internal' and sl2.usage='internal' then 'internal' when sl.usage='internal' 
                            and sl2.usage='supplier' then 'incoming' else 'outgoing' end as transfer_type
                        FROM stock_move_line as sml
                        LEFT JOIN product_product as pp on (pp.id = sml.product_id)
                        LEFT JOIN stock_location as sl on (sl.id = sml.location_dest_id)
                        LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_id)
                        LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
                        LEFT JOIN stock_move as sm on (sml.move_id = sm.id)
                        LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
                        LEFT JOIN product_category as pc on (pt.categ_id = pc.id)
                        LEFT JOIN uom_uom as pu on (pt.uom_id=pu.id)
                        WHERE sml.state = 'done' and sl.set_warehouse_id in {0} and sml.date::date <= '{1}' {2}
                        UNION ALL
                        SELECT 
                            sl.set_warehouse_id as warehouse_id,
                            sml.location_id as location_id,
                            pt.categ_id as categ_id,
                            pc.name as categ_name,
                            sml.product_id as product_id,
                            pt.id as product_tmpl_id,
                            pp.default_code as default_code,
                            pt.name as product_name,
                            pu.name as uom_name,
                            -(sml.qty_done/uu.factor) as qty,
                            sm.price_unit,
                            -(sml.qty_done/uu.factor * abs(sm.price_unit)) as total_price,
                            sm.ageing_data_ok,
                            (sml.date + interval '8 hour')::date as date,
                            case when sl2.usage='internal' and sl.usage='internal' then 'internal' when sl2.usage='internal' 
                            and sl.usage='supplier' then 'incoming' else 'outgoing' end as transfer_type
                        FROM stock_move_line as sml
                        LEFT JOIN product_product as pp on (pp.id = sml.product_id)
                        LEFT JOIN stock_location as sl on (sl.id = sml.location_id)
                        LEFT JOIN stock_location as sl2 on (sl2.id = sml.location_dest_id)
                        LEFT JOIN product_template as pt on (pp.product_tmpl_id = pt.id)
                        LEFT JOIN stock_move as sm on (sml.move_id = sm.id)
                        LEFT JOIN uom_uom as uu on (sml.product_uom_id = uu.id)
                        LEFT JOIN product_category as pc on (pt.categ_id = pc.id)
                        LEFT JOIN uom_uom as pu on (pt.uom_id=pu.id)
                        WHERE sml.state = 'done' and sl.set_warehouse_id in {0} and sml.date::date <= '{1}' {2}
                    ) as temp
                    GROUP BY temp.product_id, temp.default_code, temp.product_name, temp.categ_name, temp.uom_name
                """ .format(warehouse_ids, date, domain_val))
        query_result = self.env.cr.dictfetchall()
        return query_result

    def check_age_interval(self, day, interval):
        interval_count = interval
        while interval_count < 361:
            if interval_count >= day:
                return interval_count
            interval_count += interval
        else:
            return 361

    def get_opening_data(self, stock_move_id):
        '''
        Эхний үлдэгдэл оруулах үед барааны насжилт мэдээг авна
        :param stock_move_id:
        :return:
        '''
        self.env.cr.execute("""
                        SELECT
                            date,
                            qty
                        FROM product_ageing_opening
                        WHERE stock_move_id = {0}
                        
                        
                        
                        
                        ORDER BY date desc
                        """.format(stock_move_id))
        query_result = self.env.cr.dictfetchall()
        return query_result

    def compute_income_ageing(self, datas, qty, interval_count, date):
        res = {}
        i = interval_count
        if i > 0:
            while i < 361:
                res.update({i: 0})
                i += interval_count
            else:
                res.update({361: 0})
        for item in datas:
            date_format = "%Y-%m-%d"
            report_date = datetime.strptime(date, date_format)

            in_date = datetime.strptime(str(item['date']), date_format)
            ageing_days  = (report_date - in_date).days
            income_age_count = self.check_age_interval(ageing_days, interval_count)
            opening_data = []
            if item['ageing_data_ok']:
                opening_data = self.get_opening_data(item['id'])
            while item['qty'] < qty:
                if opening_data:
                    for od in opening_data:
                        in_date = datetime.strptime(str(od['date']), date_format)
                        ageing_days = (report_date - in_date).days
                        income_age_count = self.check_age_interval(ageing_days, interval_count)
                        done_qty = res[income_age_count] + od['qty']
                        res.update({income_age_count: done_qty})
                        qty = qty - od['qty']
                else:
                    done_qty = res[income_age_count] + item['qty']
                    res.update({income_age_count: done_qty})
                    qty = qty-item['qty']
            else:
                if opening_data:
                    for od in opening_data:
                        in_date = datetime.strptime(str(od['date']), date_format)
                        ageing_days = (report_date - in_date).days
                        income_age_count = self.check_age_interval(ageing_days, interval_count)
                        if qty > od['qty']:
                            done_qty = res[income_age_count] + od['qty']
                            res.update({income_age_count: done_qty})
                            qty = qty - od['qty']
                        else:
                            done_qty = res[income_age_count] + qty
                            res.update({income_age_count: done_qty})
                            qty = 0
                else:
                    done_qty = res[income_age_count] + qty
                    res.update({income_age_count: done_qty})
        return res


    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        worksheet = workbook.add_worksheet(u'Бараа материалын насжилт')
        file_name = 'БМ насжилт тайлан.xlsx'

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

        warehouse_ids = ()
        if len(self.warehouse_ids) > 1:
            warehouse_ids = str(tuple(self.warehouse_ids.ids))
        else:
            warehouse_ids = " (" + str(self.warehouse_ids.id) + ") "

        product_ids = ()
        if len(self.product_ids) > 1:
            product_ids = str(tuple(self.product_ids.ids))
        elif len(self.product_ids) == 1:
            product_ids = " (" + str(self.product_ids.id) + ") "

        categ_ids = ()
        if len(self.categ_ids) > 1:
            categ_ids = str(tuple(self.categ_ids.ids))
        elif len(self.categ_ids) == 1:
            categ_ids = " (" + str(self.categ_ids.id) + ") "

        report_date = str(self.date)
        query_result = self.get_product_balance(warehouse_ids, report_date, product_ids=product_ids, categ_ids=categ_ids)

        w_names = ', '.join(self.warehouse_ids.mapped('name'))

        worksheet.write(1, 3, u"Бараа материалын насжилт дэлгэрэнгүйгээр", h1)
        worksheet.write(2, 0, u"Агуулах: " + w_names, contest_left0)
        worksheet.write(3, 0, u"Тайлан бэлдсэн: " + str(datetime.now()), contest_left0)
        worksheet.write(4, 0, u"Тайлант үеийн хугацаа: " + str(self.date), contest_left0)
        row = 6
        col = 0
        worksheet.write(row, col, u"№", header)
        worksheet.write(row, col + 1, u"Барааны код", header_wrap)
        worksheet.write(row, col + 2, u"Барааны нэр", header_wrap)
        worksheet.write(row, col + 3, u"Хэмжих нэгж", header_wrap)
        worksheet.write(row, col + 4, u"Барааны бүлэг", header_wrap)
        worksheet.write(row, col + 5, u"Тоо хэмжээ", header_wrap)
        worksheet.write(row, col + 6, u"Нэгж өртөг", header_wrap)
        worksheet.write(row, col + 7, u"Нийт өртөг", header_wrap)
        worksheet.write(row, col + 8, u"Худалдах үнэ", header_wrap)
        worksheet.write(row, col + 9, u"Нийт худалдах үнэ", header_wrap)
        get_interval = self.sudo().day_interval
        if get_interval > 0:
            interval_count2 = get_interval - 1
            interval_count = get_interval
            first_interval = True
            while interval_count < 361:
                if first_interval:
                    worksheet.write(row, col + 10, u"%s хоног" % (interval_count), header_wrap)
                    col += 1
                    first_interval = False
                else:
                    worksheet.write(row, col + 10, u"%s-%s хоног" % (interval_count - interval_count2, interval_count),
                                    header_wrap)
                    col += 1
                interval_count += get_interval
            worksheet.write(row, col + 10, u"361-с дээш хоног", header_wrap)

        worksheet.freeze_panes(7, 10)
        row += 1
        number = 1
        query_result = sorted(query_result, key=itemgetter('product_id'))
        for key, value in groupby(query_result, key=itemgetter('product_id')):
            item = {}
            qty = 0
            total_price = 0
            total_price_sale = 0
            income_datas = []
            for k in value:
                qty += float(k['qty'])
                total_price += float(k['total_price'])
                total_price_sale += float(k['total_price_sale'])
                item = {'default_code': k['default_code'], 'product_name': k['product_name'], 'uom_name': k['uom_name'], 'categ_name': k['categ_name']}
                if k['qty'] > 0:
                    income_datas.append({'qty': k['qty'], 'date': str(k['date']), 'id': k['id'], 'ageing_data_ok': k['ageing_data_ok']})
            if qty > 0:
                col = 0
                product_name = item['product_name'] if item.get('product_name') else ''
                uom_name = item['uom_name'] if item.get('uom_name') else ''
                if isinstance(product_name, dict):
                    product_name = product_name[self.env.user.lang] if product_name.get(self.env.user.lang) else product_name['en_US']
                if isinstance(uom_name, dict):
                    uom_name = uom_name[self.env.user.lang] if uom_name.get(self.env.user.lang) else uom_name['en_US']
                worksheet.write(row, col, number, contest_center)
                worksheet.write(row, col + 1, item['default_code'] or '', contest_center)
                worksheet.write(row, col + 2, product_name or '', contest_left)
                worksheet.write(row, col + 3, uom_name, contest_left)
                worksheet.write(row, col + 4, item['categ_name'] or '', contest_left)
                worksheet.write(row, col + 5, qty, contest_right)
                worksheet.write(row, col + 6, total_price/qty, contest_right)
                worksheet.write(row, col + 7, total_price, contest_right)
                worksheet.write(row, col + 8, total_price_sale/qty, contest_right)
                worksheet.write(row, col + 9, total_price_sale, contest_right)

                query_result2 = self.compute_income_ageing(income_datas, qty, get_interval, report_date)
                interval_count = get_interval
                if get_interval > 0:
                    while interval_count < 361:
                        worksheet.write(row, col + 10, query_result2[interval_count], contest_right)
                        col += 1
                        interval_count += get_interval
                    else:
                        worksheet.write(row, col + 10, query_result2[361], contest_right)
                        col += 1

                number += 1
                row += 1

        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 35)
        worksheet.set_column('D:D', 10)
        worksheet.set_column('E:E', 20)
        worksheet.set_column('F:J', 15)
        #
        # if not get_cost and not get_list_price:
        #     row_categ_index = 'J:J'
        # if get_cost and not get_list_price:
        #     row_categ_index = 'O:O'
        # if not get_cost and get_list_price:
        #     row_categ_index = 'K:K'
        # worksheet.set_column(row_categ_index, 35)

        # CLOSE
        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(
                excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
        }


