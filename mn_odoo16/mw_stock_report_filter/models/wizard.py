# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ProductDetailedIncomeExpenseReport(models.TransientModel):
    _inherit = "product.detailed.income.expense"  

    def open_analyze_view_full(self):
        domain = []
        if self.move_type=='income_expense':
            action = self.env.ref('mw_stock_report_filter.action_stock_report_detail_full')
        vals = action.read()[0]
        vals['domain'] = self.get_domain(domain)
        return vals
