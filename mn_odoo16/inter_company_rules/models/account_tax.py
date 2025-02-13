# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountTax(models.Model):
    _inherit = 'account.tax'

    @api.model
    def _fix_tax_included_price_company(self, price, prod_taxes, line_taxes, company_id):
        # change company to active company
        company = company_id
        if self.env.context.get('is_create_auto_purchase'):
            company = self.env.company
        else:
            # check multi company selected
            tax_company = False
            for tax in prod_taxes:
                if tax_company and tax_company != tax.company_id:
                    raise UserError('Олон компани сонгогдсон үед борлуулалт хийж болохгүй!\nЗөвхөн дотоод борлуулалт дээр олон компани сонгоно уу.')
                tax_company = tax.company_id

        return super(AccountTax, self)._fix_tax_included_price_company(price, prod_taxes, line_taxes, company)
