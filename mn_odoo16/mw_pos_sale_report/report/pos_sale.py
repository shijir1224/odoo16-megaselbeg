# -*- coding: utf-8 -*-
from odoo import fields, models, tools, api
from odoo.exceptions import UserError, ValidationError
import datetime

class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    report_journal_id = fields.Many2one('account.journal',
        string='Journal in Report',
        help='POS Sale payment')

class pos_sale_report(models.Model):
    _name = 'pos.sale.report'
    _description = 'pos.sale.report'
    _auto = False
    _order = 'id'

    sale_order_id = fields.Many2one('sale.order', string='S0 дугаар', readonly=True)
    sale_state = fields.Selection([
        ('draft', 'Draft Quotation'),
        ('sent', 'Quotation Sent'),
        ('sale', 'Sales Order'),
        ('done', 'Sales Done'),
        ('cancel', 'Cancelled'),
        ], string='Status SO', readonly=True)
    sale_order_line_id = fields.Many2one('sale.order.line', string='S0 мөр', readonly=True)
    pos_order_id = fields.Many2one('pos.order', string='POS дугаар', readonly=True)
    pos_reference = fields.Char(string='ПОС баримт дугаар', readonly=True)
    pos_state = fields.Selection(
        [('draft', 'New'), ('paid', 'Paid'), ('done', 'Posted'),
         ('invoiced', 'Invoiced'), ('cancel', 'Cancelled')],
        string='Status POS')
    pos_order_line_id = fields.Many2one('pos.order.line', string='POS мөр', readonly=True)

    company_id = fields.Many2one('res.company', string='Company', readonly=True)
    product_id = fields.Many2one('product.product', string=u'Бараа', readonly=True)
    partner_id = fields.Many2one('res.partner', string=u'Харилцагч', readonly=True)
    categ_id = fields.Many2one('product.category', string=u'Ангилал', readonly=True)
    default_code = fields.Char(string=u'Барааны код', readonly=True)
    pos_sale_date = fields.Datetime(string='Борлуулалтын огноо', readonly=True)
    qty = fields.Float(string='Тоо хэмжээ', readonly=True)
    price_unit = fields.Float('Нэгж үнэ', readonly=True, group_operator="avg")
    sub_total = fields.Float('Нийт дүн', readonly=True)
    sub_untaxed_total = fields.Float('Нийт татваргүй', readonly=True)
    sub_total_pay = fields.Float('Нийт үнэ төлбөр ноогдох', readonly=True)
    partner_vat = fields.Char('Регистр', compute='_vat_compute')
    stock_date = fields.Datetime(string='БМ зарлагын огноо', readonly=True)
    picking_id = fields.Many2one('stock.picking', string='БМ зарлагын дугаар', readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='БМ зарлагадсан агуулах', readonly=True)

    qty_stock = fields.Float(string='Тоо хэмжээ Агуулах', readonly=True)
    price_unit_stock = fields.Float('Нэгж өртөг Агуулах', readonly=True, group_operator="avg")
    sub_total_stock = fields.Float('Нийт өртөг Агуулах', readonly=True)
    total_ashig = fields.Float('Нийт ашиг', readonly=True)
    sale_type = fields.Selection([('pos','ПОС-ын борлуулалт'), ('sale','Борлуулалтын захиалга')], string='Борлуулалтын төрөл', readonly=True)

    payment_total = fields.Float('Төлбөрийн дүн', readonly=True)
    payment_mehtod_id = fields.Many2one('account.journal', 'Төлбөрийн арга', readonly=True)
    payment_date = fields.Datetime('Төлбөрийн огноо', readonly=True)
    product_type = fields.Selection([
        ('consu', 'Хангамжийн'),
        ('service', 'Үйлчилгээ'),
        ('product', 'Stockable Product')
        ], string='Барааны төрөл', readonly=True)
    user_id = fields.Many2one('res.users', 'Борлуулагч', readonly=True)
    branch_id = fields.Many2one('res.branch', 'Салбар', readonly=True)
    sanhuu_avlaga = fields.Float('Санхүү авлагын бичилт', readonly=True)
    move_id = fields.Many2one('account.move', 'Ажил гүйлгээ', readonly=True)
    aml_id = fields.Many2one('account.move.line', 'Журнал бичилт', readonly=True)
    move_date = fields.Date('Санхүү бичилтийн огноо', readonly=True)
    session_id = fields.Many2one('pos.session', string=u'Сешн', readonly=True)
    move_state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
        ], string='Санхүү төлөв', readonly=True)
    sale_discount = fields.Float(string="ХӨН%")
    discount_amount = fields.Float(string="ХӨН Дүн")
    price_list_amount = fields.Float(string="ХӨН ҮНЭ")
    sale_order_origin_id = fields.Many2one('sale.order', string="POS Шууд борлуулалт" , index=True)


    @api.depends('partner_id')
    def _vat_compute(self):
        for i in self:
            if i.partner_id.company_type == 'company':
                i.partner_vat = i.partner_id.vat
            else:
                i.partner_vat = ' '

    def _select0(self):
        return """
            SELECT
                id as id,
                company_id,
                branch_id,
                sale_order_id,
                sale_order_line_id,
                pos_order_id,
                pos_reference,
                pos_order_line_id,
                sale_state,
                pos_state,
                partner_id,
                product_id,
                sale_discount,
                discount_amount,
                price_list_amount,
                categ_id,
                default_code,
                product_type,
                user_id,
                pos_sale_date,
                qty,
                price_unit,
                sub_total,
                sub_untaxed_total,
                stock_date,
                picking_id,
                warehouse_id,
                qty_stock,
                price_unit_stock,
                sub_total_stock,
                total_ashig,
                sale_type,
                payment_mehtod_id,
                payment_total,
                payment_date,
                sub_total_pay,
                sanhuu_avlaga,
                move_id,
                aml_id,
                move_date,
                move_state,
                session_id,
                sale_order_origin_id
        """
    
    def _select(self):
        return """
            SELECT
                10000000000000000+sm.id as id,
                so.company_id,
                so.branch_id,
                so.id as sale_order_id,
                sol.id as sale_order_line_id,
                null::int as pos_order_id,
                null::text as pos_reference,
                null::int as pos_order_line_id,
                so.state as sale_state,
                null::text as pos_state,
                so.partner_id,
                sol.product_id,
                null::int as sale_discount,
                null::int as discount_amount,
                null::int as price_list_amount,
                pt.categ_id,
                pp.default_code,
                pt.type as product_type,
                so.user_id as user_id,
                so.date_order as pos_sale_date,
                
                CASE WHEN sl.usage='customer' then -1*abs(sm.product_uom_qty) else sm.product_uom_qty END as qty,
                CASE WHEN sl.usage='customer' then -1*abs(sol.price_unit) else sol.price_unit END as price_unit,
                CASE WHEN sl.usage='customer' then -1*abs(sol.price_total*sm.product_uom_qty/(case when sol.product_uom_qty!=0 then sol.product_uom_qty else sm.product_uom_qty end)) else sol.price_total*sm.product_uom_qty/(case when sol.product_uom_qty!=0 then sol.product_uom_qty else sm.product_uom_qty end) END as sub_total,
                CASE WHEN sl.usage='customer' then -1*abs(sol.price_subtotal*sm.product_uom_qty/(case when sol.product_uom_qty!=0 then sol.product_uom_qty else sm.product_uom_qty end)) else sol.price_subtotal*sm.product_uom_qty/(case when sol.product_uom_qty!=0 then sol.product_uom_qty else sm.product_uom_qty end) END as sub_untaxed_total,

                sm.date as stock_date,
                sm.picking_id,
                so.warehouse_id,
                
                CASE WHEN sl.usage='customer' then -1*abs(sm.product_uom_qty) else sm.product_uom_qty END as qty_stock,
                CASE WHEN sl.usage='customer' then -1*abs(sm.price_unit) else sm.price_unit END as price_unit_stock,
                CASE WHEN sl.usage='customer' then -1*abs(sm.price_unit*sm.product_uom_qty) else sm.price_unit*sm.product_uom_qty END as sub_total_stock,
                CASE WHEN sl.usage='customer' then -1*abs(abs(sol.price_total) - abs(sm.price_unit*sm.product_uom_qty)) else abs(sol.price_total) - abs(sm.price_unit*sm.product_uom_qty) END as total_ashig,

                'sale' as sale_type,
                null::int as payment_mehtod_id,
                null::int as payment_total,
                null::date as payment_date,
                null::int as sub_total_pay,
                null::int as sanhuu_avlaga,
                null::int as move_id,
                null::int as aml_id,
                null::date as move_date,
                null::text as move_state,
                null::int as session_id,
                null::int as sale_order_origin_id
        """

    def _from(self):
        return """
            FROM sale_order_line sol 
                LEFT JOIN sale_order so on (sol.order_id=so.id)
                LEFT JOIN stock_move sm on (sm.sale_line_id=sol.id)
                LEFT JOIN product_product pp on (pp.id=sol.product_id)
                LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)
                LEFT JOIN stock_location sl on (sl.id=sm.location_id)
        """

    def _group_by(self):
        return """ """

    def _where(self):
        return """
            where ((sm.state='done' and sm.sale_line_id is not null) or pt.type ='service') and so.state in ('sale','done')
        """

    def _select2(self):
        return """
            SELECT
                20000000000000000+pol.id as id,
                pos.company_id,
                pos.branch_id,
                null::int as sale_order_id,
                null::int as sale_order_line_id,
                pos.id as pos_order_id,
                pos.pos_reference as pos_reference,
                pol.id as pos_order_line_id,
                null::text as sale_state,
                pos.state as pos_state,
                pos.partner_id,
                pol.product_id,
                pol.discount as sale_discount,
                pol.price_subtotal_incl as discount_amount,
                pol.discount as price_list_amount,
                pt.categ_id,
                pp.default_code,
                pt.type as product_type,
                pos.user_id as user_id,
                pos.date_order as pos_sale_date,

                CASE WHEN sl.usage='customer' then -1*abs(pol.qty) else pol.qty END as qty,
                CASE WHEN sl.usage='customer' then -1*abs(pol.price_unit) else pol.price_unit END as price_unit,
                CASE WHEN sl.usage='customer' then -1*abs(pol.price_subtotal_incl) else pol.price_subtotal_incl END as sub_total,
                null::int as sub_untaxed_total,
                sm.date as stock_date,
                sm.picking_id,
                stp.warehouse_id as warehouse_id,

                CASE WHEN sl.usage='customer' then -1*abs(pol.qty) else pol.qty END as qty_stock,
                CASE WHEN sl.usage='customer' then -1*abs(sm.price_unit) else sm.price_unit END as price_unit_stock,
                CASE WHEN sl.usage='customer' then -1*abs(sm.price_unit*pol.qty) else sm.price_unit*pol.qty END as sub_total_stock,
                CASE WHEN sl.usage='customer' then -1*abs(abs(pol.price_subtotal) - abs(sm.price_unit*sm.product_uom_qty)) else abs(pol.price_subtotal) - abs(sm.price_unit*sm.product_uom_qty) END as total_ashig,
                
                'pos' as sale_type,
                null::int as payment_mehtod_id,
                null::int as payment_total,
                null::date as payment_date,
                null::int as sub_total_pay,
                null::int as sanhuu_avlaga,
                null::int as move_id,
                null::int as aml_id,
                null::date as move_date,
                null::text as move_state,
                pos.session_id as session_id,
                pol.sale_order_origin_id as sale_order_origin_id
        """


    def _from2(self):
        return """
            FROM pos_order_line pol 
                LEFT JOIN pos_order pos on (pos.id=pol.order_id)
                LEFT JOIN stock_picking sp on (pos.id=sp.pos_order_id)
                LEFT JOIN stock_move sm on (sm.picking_id=sp.id and sm.product_id=pol.product_id)
                LEFT JOIN product_product pp on (pp.id=pol.product_id)
                LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)
                LEFT JOIN stock_location sl on (sl.id=sm.location_id)
                LEFT JOIN stock_picking_type stp on (sm.picking_type_id=stp.id)
        """

    def _group_by2(self):
        return """ """

    def _where2(self):
        return """
        """
            #where (sm.state='done' and sp.pos_order_id is not null) or pt.type ='service'

    def _select3(self):
        return """
            SELECT
                30000000000000000+pap.id as id,
                pos.company_id,
                pos.branch_id,
                null::int as sale_order_id,
                null::int as sale_order_line_id,
                pos.id as pos_order_id,
                pos.pos_reference as pos_reference,
                null::int as pos_order_line_id,
                null::text as sale_state,
                pos.state as pos_state,
                pos.partner_id,
                null::int as product_id,
                null::int as sale_discount,
                null::int as discount_amount,
                null::int as price_list_amount,
                null::int as categ_id,
                null::text as default_code,
                null::text as product_type,
                pos.user_id as user_id,
                pos.date_order as pos_sale_date,

                null::int as qty,
                null::int as price_unit,
                null::int as sub_total,
                null::int as sub_untaxed_total,
                null::date as stock_date,
                sp.id as picking_id,
                stp.warehouse_id as warehouse_id,

                null::int as qty_stock,
                null::int as price_unit_stock,
                null::int as sub_total_stock,
                null::int as total_ashig,
                'pos' as sale_type,
                ppm.report_journal_id as payment_mehtod_id,
                pap.amount as payment_total,
                pap.payment_date as payment_date,
                CASE WHEN sl.usage='customer' then -1*abs(pos.amount_total) else pos.amount_total END as sub_total_pay,
                null::int as sanhuu_avlaga,
                null::int as move_id,
                null::int as aml_id,
                null::date as move_date,
                null::text as move_state,
                pos.session_id as session_id,
                null::int as sale_order_origin_id
        """

    def _from3(self):
        return """
            FROM pos_payment pap
                LEFT JOIN pos_order pos on (pos.id=pap.pos_order_id)
                LEFT JOIN pos_payment_method ppm on (ppm.id=pap.payment_method_id)
                LEFT JOIN stock_picking sp on (pos.id=sp.pos_order_id)
                LEFT JOIN stock_picking_type stp on (sp.picking_type_id=stp.id)
                LEFT JOIN stock_location sl on (sl.id=sp.location_id)
        """

    def _group_by3(self):
        return """ """

    def _where3(self):
        return """ """

    def _select4(self):
        return """
            SELECT
                40000000000000000+apa.id as id,
                so.company_id,
                so.branch_id,
                so.id as sale_order_id,
                null::int as sale_order_line_id,
                null::int as pos_order_id,
                null::text as pos_reference,
                null::int as pos_order_line_id,
                so.state as sale_state,
                null::text as pos_state,
                so.partner_id,
                null::int as product_id,
                null::int as sale_discount,
                null::int as discount_amount,
                null::int as price_list_amount,
                null::int as categ_id,
                null::text as default_code,
                null::text as product_type,
                so.user_id as user_id,
                so.date_order as pos_sale_date,

                null::int as qty,
                null::int as price_unit,
                null::int as sub_total,
                null::int as sub_untaxed_total,
                null::date as stock_date,
                null::int as picking_id,
                so.warehouse_id as warehouse_id,

                null::int as qty_stock,
                null::int as price_unit_stock,
                null::int as sub_total_stock,
                null::int as total_ashig,
                'sale' as sale_type,
                move.journal_id as payment_mehtod_id,
                apa.amount as payment_total,
                move.date as payment_date,
                CASE WHEN apa.amount>0 then so.amount_total else -1*abs(so.amount_total) END as sub_total_pay,
                null::int as sanhuu_avlaga,
                null::int as move_id,
                null::int as aml_id,
                null::date as move_date,
                null::text as move_state,
                null::int as session_id,
                null::int as sale_order_origin_id
        """

    def _from4(self):
        return """
            FROM account_payment apa 
                JOIN account_move move ON move.id = apa.move_id
                JOIN account_move_line line ON line.move_id = move.id
                JOIN account_partial_reconcile part ON
                    part.debit_move_id = line.id
                    OR
                    part.credit_move_id = line.id
                JOIN account_move_line counterpart_line ON
                    part.debit_move_id = counterpart_line.id
                    OR
                    part.credit_move_id = counterpart_line.id
                JOIN account_move invoice ON invoice.id = counterpart_line.move_id
                JOIN account_account account ON account.id = line.account_id
                join sale_order_line_invoice_rel rrr on rrr.invoice_line_id in (select move_id from account_move_line lll where lll.move_id=invoice.id )
                LEFT JOIN sale_order so on (so.id in (select id from sale_order_line where id=rrr.order_line_id))
                
        """

    def _group_by4(self):
        return """ where so.id is not null  """

    def _where4(self):
        return """                                                AND account.account_type IN ('receivable')
                    AND line.id != counterpart_line.id
                    AND invoice.move_type in ('out_invoice', 'out_refund', 'in_invoice', 'in_refund', 'out_receipt', 'in_receipt')            
 """
    

    def _select5(self):
        return """
            SELECT
                50000000000000000+aml.id as id,
                so.company_id,
                so.branch_id,
                so.id as sale_order_id,
                sol.id as sale_order_line_id,
                null::int as pos_order_id,
                null::text as pos_reference,
                null::int as pos_order_line_id,
                so.state as sale_state,
                null::text as pos_state,
                so.partner_id,
                aml.product_id as product_id,
                sol.discount as sale_discount,
                null::int as discount_amount,
                null::int as price_list_amount,
                pt.categ_id as categ_id,
                pp.default_code as default_code,
                pt.type as product_type,
                so.user_id as user_id,
                so.date_order as pos_sale_date,

                null::int as qty,
                null::int as price_unit,
                null::int as sub_total,
                null::int as sub_untaxed_total,
                null::date as stock_date,
                null::int as picking_id,
                so.warehouse_id as warehouse_id,

                null::int as qty_stock,
                null::int as price_unit_stock,
                null::int as sub_total_stock,
                null::int as total_ashig,
                'sale' as sale_type,
                null::int as payment_mehtod_id,
                null::int as payment_total,
                null::date as payment_date,
                null::int as sub_total_pay,
                case when aml.debit>0 then -aml.debit else aml.credit end as sanhuu_avlaga,
                aml.move_id as move_id,
                aml.id as aml_id,
                aml.date as move_date,
                am.state as move_state,
                null::int as session_id,
                null::int as sale_order_origin_id
        """

    def _from5(self):
        return """
            FROM account_move_line aml
                LEFT JOIN sale_order_line_invoice_rel rel on (rel.invoice_line_id=aml.id)
                LEFT JOIN sale_order_line sol on (sol.id=rel.order_line_id)
                LEFT JOIN sale_order so on (so.id=sol.order_id)
                LEFT JOIN account_move am on (am.id=aml.move_id)
                LEFT JOIN product_product pp on (pp.id=sol.product_id)
                LEFT JOIN product_template pt on (pt.id=pp.product_tmpl_id)
        """

    def _group_by5(self):
        return """ where rel.order_line_id is not null and ((am.move_type='out_refund' and aml.debit>0 and am.state='posted') or (am.move_type='out_invoice' and aml.credit>0 and am.state='posted'))"""

    def _where5(self):
        return """ """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                from (
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
                UNION ALL
                %s
                %s
                %s
                %s
        ) as temp_pos_sale_report
            )

        """ % (self._table, self._select0(), self._select(), self._from(), self._group_by(),self._where(), self._select2(), self._from2(), self._group_by2(),self._where2(), self._select3(), self._from3(), self._group_by3(),self._where3(), self._select4(), self._from4(), self._group_by4(),self._where4(), self._select5(), self._from5(), self._group_by5(),self._where5())
        )
