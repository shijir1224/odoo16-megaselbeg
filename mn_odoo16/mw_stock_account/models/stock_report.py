# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class StockQuantReport(models.Model):
    _inherit = "stock.quant.report"
    
    value_old = fields.Monetary(related='qaunt_id.value', string='Хуучин Өртөг', groups='mw_stock_account.group_stock_view_cost')
    currency_id = fields.Many2one(related='product_id.currency_id', groups='stock.group_stock_manager')
    value = fields.Float(string='Нэгж Өртөг', groups='mw_stock_account.group_stock_view_cost', group_operator='avg')
    value_sum = fields.Float(string='Нийт Өртөг', groups='mw_stock_account.group_stock_view_cost')

    zarah_negj_price = fields.Float(string=u'Зарах нэгж үнэ', groups='mw_stock_account.group_stock_view_cost')
    zarah_niit_price = fields.Float(string=u'Зарах нийт үнэ', groups='mw_stock_account.group_stock_view_cost')
    bohir_ashig = fields.Float(string=u'Бохир ашиг', groups='mw_stock_account.group_stock_view_cost')

    def _select(self):
        select_str = super(StockQuantReport, self)._select()
        select_str += """
            ,ip.value_float as value
            ,sq.quantity*ip.value_float as value_sum
            ,pt.list_price as zarah_negj_price
            ,sq.quantity*pt.list_price as zarah_niit_price
            ,(sq.quantity*pt.list_price)-(sq.quantity*ip.value_float) as bohir_ashig
        """
        return select_str

    def _from(self):
        select_str = super(StockQuantReport, self)._from()
        select_str += """
            LEFT JOIN ir_property as ip on (ip.res_id = 'product.product,'||sq.product_id and ip.name = 'standard_price')
        """
        return select_str