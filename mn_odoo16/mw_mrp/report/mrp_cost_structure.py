# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models


class MrpCostStructure(models.AbstractModel):
    _inherit = 'report.mrp_account_enterprise.mrp_cost_structure'

    def get_lines(self, productions):
        res = super().get_lines(productions)
        for vals in res:
            product = vals['product']

            vals['standard_prices'] = []
            vals['standard_prices_total_cost'] = 0.0
            vals['standard_prices_total_qty'] = 0.0

            for mos in productions.filtered(lambda m: m.product_id == product):
                st_price_lines = mos.st_line_ids #.filtered(lambda m: m.state != 'cancel' )
                if mos.add_st_line_ids:
                    st_price_lines+=mos.add_st_line_ids
                if not st_price_lines:
                    continue
                unit_cost = mos.extra_cost
                for st_price in st_price_lines:
                    unit_cost= st_price.price_unit
                    vals['standard_prices'].append({
                        'cost': unit_cost * mos.product_qty,
                        'qty': mos.product_qty,
                        'unit_cost': unit_cost,
                        'name':st_price.name
                        # 'uom': product.uom_id,
                    })
                    vals['standard_prices_total_cost'] += unit_cost * mos.product_qty
                    vals['standard_prices_total_qty'] += mos.product_qty

            vals['total_cost'] += vals['standard_prices_total_cost']

        return res
