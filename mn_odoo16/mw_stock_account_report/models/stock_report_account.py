# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class stock_report_account(models.Model):
    _name = "stock.report.account"
    _description = "Stock Report Detailt Full"
    _auto = False
    _order = 'product_id'

    picking_id = fields.Many2one('stock.picking', u'Баримт', readonly=True)
    stock_move_id = fields.Many2one('stock.move', u'Хөдөлгөөн', readonly=True)
    location_id = fields.Many2one('stock.location', u'Гарах байрлал', readonly=True)
    location_dest_id = fields.Many2one('stock.location', u'Хүрэх байрлал', readonly=True)
    account_move_id = fields.Many2one('account.move', u'Санхүү бичилт', readonly=True)
    partner_id = fields.Many2one('res.partner', u'Агуулах Харилцагч', readonly=True)
    acc_partner_id = fields.Many2one('res.partner', u'Санхүү Харилцагч', readonly=True)
    product_id = fields.Many2one('product.product', u'Бараа', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', u'Бараа/Template', readonly=True)
    categ_id = fields.Many2one('product.category', u'Ангилал', readonly=True,)
    uom_id = fields.Many2one('uom.uom', string=u'Хэмжих нэгж',readonly=True)
    default_code = fields.Char(string=u'Дотоод Код',readonly=True)
    barcode = fields.Char(string=u'Баркод',readonly=True)

    account_id_debit = fields.Many2one('account.account', u'Данс Дебит', readonly=True)
    account_id_credit = fields.Many2one('account.account', u'Данс Кредит', readonly=True)
    stock_date = fields.Date(u'Агуулахын Огноо', readonly=True)
    account_date = fields.Date(u'Санхүү Огноо', readonly=True)
    stock_move_price_out = fields.Float(u'Агуулахын Зарлага', readonly=True)
    stock_move_price_in = fields.Float(u'Агуулахын Орлого', readonly=True)
    account_out = fields.Float(u'Санхүү Зарлага', readonly=True)
    account_in = fields.Float(u'Санхүү Орлого', readonly=True)
    date_diff = fields.Boolean(u'Огноо зөрүүтэй', readonly=True)
    month_diff = fields.Boolean(u'Сар зөрүүтэй', readonly=True)
    year_diff = fields.Boolean(u'Жил зөрүүтэй', readonly=True)
    urtug_zuruu_in = fields.Float(u'Зөрүү Орлого', readonly=True)
    urtug_zuruu_out = fields.Float(u'Зөрүү Зарлаг', readonly=True)
    urtug_zuruu_company = fields.Boolean(u'Зөрүү компани', readonly=True)
    ijil_account = fields.Boolean(u'Дебит Кредит ижил', readonly=True)

    company_id = fields.Many2one('res.company', string='Компани',readonly=True)

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                select
                picking_id,
                stock_move_id,
                location_id,
                location_dest_id,
                product_id,
                product_tmpl_id,
                categ_id,
                uom_id,
                default_code,
                barcode,
                stock_date,
                max(partner_id) as partner_id,
                max(account_id_debit) as account_id_debit,
                max(account_id_credit) as account_id_credit,
                max(account_move_id) as account_move_id,
                max(account_date) as account_date,
                max(acc_partner_id) as acc_partner_id,
                max(id) as id,
                sum(stock_move_price_in) as stock_move_price_in,
                sum(stock_move_price_out) as stock_move_price_out,
                sum(account_out) as account_out,
                sum(account_in) as account_in,
                case when max(account_id_debit)=max(account_id_credit) then true else false end ijil_account,
                case when stock_date!=max(account_date) then true else false end date_diff,
                case when date_part('month', stock_date)!=date_part('month', max(account_date)) then true else false end month_diff,
                abs(sum(stock_move_price_out)-sum(account_out)) as urtug_zuruu_out,
                abs(sum(stock_move_price_in)-sum(account_in)) as urtug_zuruu_in,
                urtug_zuruu_company as urtug_zuruu_company,
                company_id,
                case when date_part('year', stock_date)!=date_part('year', max(account_date)) then true else false end year_diff
                FROM (
                select
                sm.id,
                sm.id as stock_move_id,
                sm.location_id,
                sm.location_dest_id,
                sm.product_id,
                pt.categ_id,
                pt.uom_id,
                pp.default_code,
                pp.product_tmpl_id,
                pp.barcode,
                sm.picking_id,
                sp.partner_id,
                null::int as acc_partner_id,
                (sm.date+interval '8 hour')::date as stock_date,
                null::int as account_move_id,
                null::int as account_id_debit,
                null::int as account_id_credit,
                null::date as account_date,
                case when sl.usage='internal' then abs(sm.price_unit)*sm.quantity_done else 0 end as stock_move_price_out,
                case when sl.usage='internal' then 0 else abs(sm.price_unit)*sm.quantity_done end as stock_move_price_in,
                0 as account_out,
                0 as account_in,
                True as urtug_zuruu_company,
                sm.company_id
                from stock_move as sm
                left join product_product pp on pp.id = sm.product_id
                left join product_template pt on pt.id = pp.product_tmpl_id
                left join stock_picking sp on sp.id = sm.picking_id and sm.company_id = sp.company_id
                left join stock_location sl on sl.id=sm.location_id
                left join stock_location sl2 on sl2.id=sm.location_dest_id
                where sm.state='done' and (sl.usage!='internal' or sl2.usage!='internal')
                UNION ALL

                select
                -1*aml.id,
                am.stock_move_id as stock_move_id,
                sm.location_id,
                sm.location_dest_id,
                sm.product_id,
                pt.categ_id,
                pt.uom_id,
                pp.default_code,
                pp.product_tmpl_id,
                pp.barcode,
                sm.picking_id,
                null::int as partner_id,
                aml.partner_id as acc_partner_id,
                (sm.date+interval '8 hour')::date as stock_date,
                am.id as account_move_id,
                case when aml.debit>0 then aml.account_id else null::int end account_id_debit,
                case when aml.credit>0 then aml.account_id else null::int end account_id_credit,
                aml.date as account_date,
                0 as stock_move_price_out,
                0 as stock_move_price_in,
                case when sl.usage='internal' then coalesce(aml.debit,aml.credit) else 0 end as account_out,
                case when sl.usage='internal' then 0 else coalesce(aml.debit,aml.credit) end as account_in,
                am.company_id=sm.company_id as urtug_zuruu_company,
                sm.company_id
                from account_move_line as aml
                left join account_move am on am.id = aml.move_id
                left join stock_move sm on sm.id = am.stock_move_id and sm.company_id = am.company_id
                left join stock_location sl on sl.id=sm.location_id
                left join product_product pp on pp.id = sm.product_id
                left join product_template pt on pt.id = pp.product_tmpl_id
                where am.state='posted' and am.stock_move_id is not null
                ) as temp_bayasaa
                group by 1,2,3,4,5,6,7,8,9,10,11,28,29
            )
        """ % (self._table)
        )
