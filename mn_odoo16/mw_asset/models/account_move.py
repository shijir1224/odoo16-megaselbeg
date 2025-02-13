# -*- coding: utf-8 -*-
from odoo import fields, models, api,_,_lt
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from odoo.tools import float_compare
from odoo.tools.misc import formatLang
from dateutil.relativedelta import relativedelta
from collections import defaultdict, namedtuple
import logging

_logger = logging.getLogger(__name__)





class AccountMove(models.Model):
    _inherit = "account.move"

    asset_remaining_value = fields.Monetary(string='Depreciable Value', compute='_compute_depreciation_cumulative_value', store=True)
    asset_depreciated_value = fields.Monetary(string='Cumulative Depreciation', compute='_compute_depreciation_cumulative_value', store=True)

    # -------------------------------------------------------------------------
    # COMPUTE METHODS INHERITED
    # -------------------------------------------------------------------------
    @api.depends('asset_id', 'depreciation_value', 'asset_id.total_depreciable_value', 'asset_id.already_depreciated_amount_import')
    def _compute_depreciation_cumulative_value(self):
        '''Дараах мөрүүд нэмсэн
                for capital in capital_ids:
                    if capital.capital_id.date<move.date and capital not in added :
                        remaining+=capital.capital_amount
                        added.append(capital)        '''
        self.asset_depreciated_value = 0
        self.asset_remaining_value = 0

        for asset in self.asset_id:
            depreciated = 0
            remaining = asset.total_depreciable_value - asset.already_depreciated_amount_import
            capital_ids=[]
            added=[]
            # .filtered(lambda m: m.state != 'posted')
            if asset.capital_value>0:
                capital_ids=self.env['account.asset.capital.line'].search([('asset_id','=',asset.id),
                                                                           ('capital_id.flow_line_id.state_type','=','done')])
                remaining+=asset.capital_value
            for move in asset.depreciation_move_ids.sorted(lambda mv: (mv.date, mv._origin.id)):
                # for capital in capital_ids:
                #     if capital.capital_id.date<move.date and capital not in added and move.state!='posted':
                #         remaining+=capital.capital_amount
                #         added.append(capital)
                remaining -= move.depreciation_value
                depreciated += move.depreciation_value
                move.asset_remaining_value = remaining
                move.asset_depreciated_value = depreciated
                
    def unlink(self):
        # Журналын бичилт нь үндсэн хөрөнгөнөөс үүссэн бол устгагдахгүй
        asset_unlink = self._context.get('asset_unlink', False)
        if not asset_unlink:
            for move in self:
                for line in move.line_ids:
                    if line.asset_id:
                        raise UserError(_('The entries created when registered asset or depreciated asset cannot delete.'))
        return super(AccountMove, self).unlink()

    
    # def action_open_asset_ids(self):
    #     return self.asset_ids.open_asset_view(['tree', 'form'])
    
    def action_delete_am_to_check(self):
        # print(S)
        delete_moves = self.env['account.move'].search([('to_check','=',True),('state','=','draft')], limit = 100)
        # print('121424214124124',delete_moves)
        if delete_moves:
            # print('121424214124124',delete_moves)
            # print(s)
            sql_query = """
            delete from account_move where id in ({0}) 
                    """.format(
                ','.join([str(i) for i in delete_moves.ids])
            )
            _logger.info("%s sql_query " % (sql_query))
            self.env.cr.execute(sql_query)



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
                    # and not (move_line.account_id.internal_group == 'asset')
                ):

                    if not move_line.name:
                        raise UserError(_('Journal Items of {account} should have a label in order to generate an asset').format(account=move_line.account_id.display_name))
                    if move_line.account_id.multiple_assets_per_line:
                        # decimal quantities are not supported, quantities are rounded to the lower int
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
    
    def _inverse_depreciation_value(self):
        context = self._context or {}
        for move in self:
            asset = move.asset_id
            amount = abs(move.depreciation_value)
            account = asset.account_depreciation_expense_id if asset.asset_type != 'sale' else asset.account_depreciation_id
            print ('account11111 ',account)
            # if not context.get("src_account_id", False):
            #     move.write({'line_ids': [
            #         Command.update(line.id, {
            #             'balance': amount if line.account_id == account else -amount,
            #         })
            #         for line in move.line_ids
            #     ]})

    @api.model
    def _prepare_move_for_asset_depreciation(self, vals):
        missing_fields = set(['asset_id', 'amount', 'depreciation_beginning_date', 'date', 'asset_number_days']) - set(vals)
        if missing_fields:
            raise UserError(_('Some fields are missing {}').format(', '.join(missing_fields)))
        asset = vals['asset_id']
        analytic_distribution = asset.analytic_distribution
        depreciation_date = vals.get('date', fields.Date.context_today(self))
        company_currency = asset.company_id.currency_id
        current_currency = asset.currency_id
        prec = company_currency.decimal_places
        amount_currency = vals['amount']
        amount = current_currency._convert(amount_currency, company_currency, asset.company_id, depreciation_date)
        # Keep the partner on the original invoice if there is only one
        partner = asset.original_move_line_ids.mapped('partner_id')
        partner = partner[:1] if len(partner) <= 1 else self.env['res.partner']
        
        move_line_1 = {
            'name': asset.name,
            'partner_id': partner.id,
            'account_id': asset.account_depreciation_id.id,
            'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_distribution': analytic_distribution,
            'currency_id': current_currency.id,
            'amount_currency': -amount_currency,
            'branch_id': vals.get('branch_id', False),
        }
        move_line_2 = {
            'name': asset.name,
            'partner_id': partner.id,
            'account_id': asset.account_depreciation_expense_id.id,
            'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
            'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
            'analytic_distribution': analytic_distribution,
            'currency_id': current_currency.id,
            'amount_currency': amount_currency,
            'branch_id': vals.get('branch_id', False),
        }
        move_vals = {
            'partner_id': partner.id,
            'date': depreciation_date,
            'journal_id': asset.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            'asset_id': asset.id,
            'ref': _("%s: Depreciation", asset.name),
            'asset_depreciation_beginning_date': vals['depreciation_beginning_date'],
            'asset_number_days': vals['asset_number_days'],
            'name': '/',
            'asset_value_change': vals.get('asset_value_change', False),
            'move_type': 'entry',
            'currency_id': current_currency.id,
            'auto_post':'no',
            'branch_id': vals.get('branch_id', False)
        }
        return move_vals
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    original_many_asset_ids = fields.Many2many('account.asset', 'account_asset_multi_aml_rel','aml_id', 'asset_id', string='Assets', copy=False)
    asset_id = fields.Many2one('account.asset', string='Asset', ondelete="restrict")
    asset_type_id = fields.Many2one('account.asset.type', string="Хөрөнгийн төрөл", store=True)
    
    
    @api.depends('move_id')
    def compute_asset_type_id_mw(self):
        for item in self:
            if item.move_id and item.move_id.asset_id and item.move_id.asset_id.asset_type_id:
                item.asset_type_id = item.move_id.asset_id.asset_type_id.id
            else:
                item.asset_type_id = False
