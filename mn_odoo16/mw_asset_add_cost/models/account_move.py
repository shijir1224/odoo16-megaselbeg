# -*- coding: utf-8 -*-
from odoo import fields, models, api,_,_lt
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta
from collections import defaultdict, namedtuple

class AccountMove(models.Model):
    _inherit = "account.move"

    def _auto_create_asset(self):
        create_list = []
        invoice_list = []
        auto_validate = []
        amount=0
        for move in self:
            for move_line in move.line_ids:

                if (
                    move_line.account_id
                    and (move_line.account_id.can_create_asset)
                    and move_line.account_id.create_asset != "no"
                    # and not (move_line.currency_id or move.currency_id).is_zero(move_line.price_total)
                    and not move_line.asset_ids
                    and not move_line.tax_line_id
                    and move_line.debit > 0
                    and not move_line.move_id.purchase_order_expenses
                    # and not (move_line.account_id.internal_group == 'asset')
                ):

                    if not move_line.name:
                        raise UserError(_('Journal Items of {account} should have a label in order to generate an asset').format(account=move_line.account_id.display_name))
                    if move_line.account_id.multiple_assets_per_line:
                        # decimal quantities are not supported, quantities are rounded to the lower int
                        if move_line.purchase_line_id and move_line.purchase_line_id.price_unit_product<move_line.purchase_line_id.price_unit_stock_move:
                            amount = move_line.purchase_line_id.price_unit_stock_move
                            units_quantity = max(1, abs(int(move_line.quantity)))
                        else:
                            units_quantity = max(1, abs(int(move_line.quantity)))
                            # print('12412412414124',units_quantity)
                            amount =move_line.debit/units_quantity
                        # print('124124124141sfaasfa24',amount)
                    else:
                        units_quantity = 1
                        amount = move_line.debit
                    vals = {
                        'name': move_line.name,
                        'company_id': move_line.company_id.id,
                        'currency_id': move_line.company_currency_id.id,
                        'analytic_distribution': move_line.analytic_distribution,
                        'original_move_line_ids': [(6, False, move_line.ids)],
                        'state': 'draft',
                        'partner_id': move.partner_id.id,
                        'invoice_id':move.id,
                        'acquisition_date': move.invoice_date,
                        'initial_value' : amount,
                        'original_value' : amount,
                        'method_period':'1',
                    }
                    # print('12412412414safasfsafsa1sfaasfa24',vals)

                    model_id = move_line.account_id.asset_model
                    if model_id:
                        vals.update({
                            'model_id': model_id.id,
                            'method_number':model_id.method_number,
                        })
                    auto_validate.extend([move_line.account_id.create_asset == 'validate'] * units_quantity)
                    invoice_list.extend([move] * units_quantity)
                    for i in range(1, units_quantity + 1):
                        if units_quantity > 1:
                            vals['name'] = move_line.name + _(" (%s of %s)", i, units_quantity)
                        create_list.extend([vals.copy()])

        assets = self.env['account.asset'].create(create_list)
        for asset, vals, invoice, validate in zip(assets, create_list, invoice_list, auto_validate):
            if 'model_id' in vals:
                asset._onchange_model_id()
                if validate:
                    asset.validate()
            if invoice:
                asset_name = {
                    'purchase': _lt('Asset'),
                    'sale': _lt('Deferred revenue'),
                    'expense': _lt('Deferred expense'),
                }[asset.asset_type]
                asset.message_post(body=_('%s created from invoice: %s', asset_name, invoice._get_html_link()))
                asset._post_non_deductible_tax_value()
        return assets
    
