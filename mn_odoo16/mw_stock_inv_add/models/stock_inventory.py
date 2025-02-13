# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero

class StockInventory(models.Model):
    _inherit = "stock.inventory"

    @api.model
    def _default_is_invoice_diff(self):
        return False

    @api.model
    def _default_diff_partner_id(self):
        return False

    diff_partner_id = fields.Many2one('res.partner', string=u'Зөрүүгийн Харилцагч', default=_default_diff_partner_id)
    is_invoice_diff = fields.Boolean('Авлага үүсгэх', default=_default_is_invoice_diff)
    account_move_rec_id = fields.Many2one('account.move', string=u'Авлагын бичилт')
    account_move_pay_id = fields.Many2one('account.move', string=u'Өглөгийн бичилт')

    
    def _get_accounting_data_for_valuation(self, iluu=False):
        """ Return the accounts and journal to use to post Journal Entries for
        the real-time valuation of the quant. """
        self.ensure_one()
        self = self.with_context(force_company=self.company_id.id)
        product_id = self.line_ids[0].product_id
        accounts_data = product_id.product_tmpl_id.get_product_accounts()
        location_id = product_id.property_stock_inventory
        
        if iluu:
#             acc_src = self.diff_partner_id.property_account_payable_id.id
            if self.diff_partner_id and not self.diff_partner_id.property_account_receivable_id.id:
                raise UserError(u' Харилцагч дээр данс тохируулаагүй байна {}'.format(self.diff_partner_id.name))
            acc_src = self.diff_partner_id.property_account_receivable_id.id
            if not location_id.valuation_out_account_id.id:
                raise UserError(u' Байрлал дээр данс тохируулаагүй байна {}'.format(location_id.name))
            acc_dest = location_id.valuation_out_account_id.id
        else:
            if not location_id.valuation_out_account_id.id:
                raise UserError(u' Байрлал дээр данс тохируулаагүй байна {}'.format(location_id.name))
            acc_src = location_id.valuation_out_account_id.id
            if self.diff_partner_id and not self.diff_partner_id.property_account_receivable_id.id:
                raise UserError(u' Харилцагч дээр данс тохируулаагүй байна {}'.format(self.diff_partner_id.name))
            acc_dest = self.diff_partner_id.property_account_receivable_id.id
       
        if not accounts_data.get('stock_journal', False):
            raise UserError(_('You don\'t have any stock journal defined on your product category, check if you have installed a chart of accounts.'))
        # if not acc_src:
        #     raise UserError(_('Cannot find a stock input account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (product_id.display_name))
        # if not acc_dest:
        #     raise UserError(_('Cannot find a stock output account for the product %s. You must define one on the product category, or on the location, before processing this operation.') % (product_id.display_name))
        journal_id = accounts_data['stock_journal'].id
        return journal_id, acc_src, acc_dest

    # def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
    #     self.ensure_one()
    #     debit_value = self.company_id.currency_id.round(cost)
    #     credit_value = debit_value
    #     valuation_partner_id = self.diff_partner_id.id
    #     res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description).values()]

    #     return res

    def _create_account_move_line(self, credit_account_id, debit_account_id, journal_id, qty, description, cost):
        self.ensure_one()
        AccountMove = self.env['account.move'].with_context(default_journal_id=journal_id)

        move_lines = self._prepare_account_move_line(qty, cost, credit_account_id, debit_account_id, description)
        new_account_move = False
        if move_lines:
            date = self._context.get('force_period_date', fields.Date.context_today(self))
            new_account_move = AccountMove.sudo().create({
                'journal_id': journal_id,
                'line_ids': move_lines,
                'date': date,
                'ref': description,
                'move_type': 'entry',
            })
            new_account_move._post()
        return new_account_move

    def _prepare_account_move_line(self, qty, cost, credit_account_id, debit_account_id, description):
        self.ensure_one()
        debit_value = self.company_id.currency_id.round(cost)
        credit_value = debit_value
        valuation_partner_id = self.diff_partner_id.id
        svl_id = False
        res = [(0, 0, line_vals) for line_vals in self._generate_valuation_lines_data(valuation_partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description).values()]

        return res

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description):
        self.ensure_one()
        debit_line_vals = {
            'name': description,
            'product_id': False,
            'quantity': qty,
            'product_uom_id': False,
            'ref': description,
            'partner_id': partner_id,
            'debit': debit_value if debit_value > 0 else 0,
            'credit': -debit_value if debit_value < 0 else 0,
            'account_id': debit_account_id,
        }

        credit_line_vals = {
            'name': description,
            'product_id': False,
            'quantity': qty,
            'product_uom_id': False,
            'ref': description,
            'partner_id': partner_id,
            'credit': credit_value if credit_value > 0 else 0,
            'debit': -credit_value if credit_value < 0 else 0,
            'account_id': credit_account_id,
        }

        rslt = {'credit_line_vals': credit_line_vals, 'debit_line_vals': debit_line_vals}
        
        return rslt

    def _action_done(self):
        res = super(StockInventory, self)._action_done()
        for item in self:
            if item.is_invoice_diff:
                if item.price_diff_total>0:
                    journal_id, acc_src, acc_dest = self._get_accounting_data_for_valuation(iluu=True)
                    move_id = item._create_account_move_line(acc_src, acc_dest, journal_id, 1 , ' TOOLLOGO ILUUDEL', item.price_diff_total)
                    item.account_move_pay_id = move_id.id
                    
                elif item.price_diff_total<0:
                    journal_id, acc_src, acc_dest = self._get_accounting_data_for_valuation()
                    move_id = item._create_account_move_line(acc_src, acc_dest, journal_id, 1 , ' TOOLLOGO DUTAGDAL', abs(item.price_diff_total))
                    item.account_move_rec_id = move_id.id
                 
        return res

    def action_validate(self):
        inventory_lines = self.line_ids.filtered(lambda l: l.product_id.tracking in ['lot', 'serial'] and not l.prod_lot_id and l.theoretical_qty != l.product_qty)
        lines = self.line_ids.filtered(lambda l: float_compare(l.product_qty, 1, precision_rounding=l.product_uom_id.rounding) > 0 and l.product_id.tracking == 'serial' and l.prod_lot_id)
        if inventory_lines and not lines:
            line_names = ', '.join(inventory_lines.mapped('product_id.display_name'))
            raise UserError(u'Заавал цуврал оруулах ёстой!!! %s '%(line_names))
        return super(StockInventory, self).action_validate()
