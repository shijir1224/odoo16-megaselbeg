# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp
from datetime import datetime
from odoo.exceptions import UserError
from ast import literal_eval
from odoo.tools.float_utils import float_is_zero, float_round

class StockMove(models.Model):
    _inherit = 'stock.move'

    niit_urtug = fields.Float('Нийт өртөг', compute='com_niit_urtug', readonly=True, groups="mw_stock_account.group_stock_view_cost", store=True)
    round_sub_total_sale =fields.Float(string=u'Нийт дүн', related='niit_urtug', store=True, digits=(12, 2))
    @api.depends('price_unit','quantity_done')
    def com_niit_urtug(self):
        for item in self:
            conqueror = 0 if item.state == 'cancel' else 1
            item.niit_urtug = item.price_unit*item.quantity_done*conqueror


    def _is_internal(self):
        self.ensure_one()
        return self.location_id.company_id.id == self.location_dest_id.company_id.id and self.location_id.usage == 'internal' and self.location_dest_id.usage == 'internal' 

    def _create_in_svl(self, forced_quantity=None):
        res = super(StockMove, self)._create_in_svl(forced_quantity)
        for item in res:
            if not item.stock_move_id.price_unit:
                item.stock_move_id.price_unit = item.unit_cost
        return res
    
    def _create_out_svl(self, forced_quantity=None):
        res = super(StockMove, self)._create_out_svl(forced_quantity)
        for item in res:
            if not item.stock_move_id.price_unit:
                item.stock_move_id.price_unit = abs(item.unit_cost)
        return res

    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        for move in self.filtered(lambda move: move._is_internal()):
            if move.product_id.cost_method in ['average','standard']:
                move.price_unit = abs(move.product_id.standard_price)
            if move.product_id.cost_method =='fifo':
                quantity = move.product_id.quantity_svl
                if float_is_zero(quantity, precision_rounding=move.product_id.uom_id.rounding):
                    continue
                average_cost = move.product_id.value_svl / quantity
                move.price_unit = abs(average_cost)
        return res

    def action_view_stock_valuation_layers(self):
        self.ensure_one()
        domain = [('id', 'in', self.stock_valuation_layer_ids.ids)]
        action = self.env.ref('stock_account.stock_valuation_layer_action').read()[0]
        context = literal_eval(action['context'])
        context.update(self.env.context)
        context['no_at_date'] = True
        return dict(action, domain=domain, context=context)
    
    # def _account_entry_move(self, qty, description, svl_id, cost):
    #     """ Accounting Valuation Entries """
    #     self.ensure_one()
    #     am_vals = []
    #     if self.product_id.type != 'product':
    #         # no stock valuation for consumable products
    #         return am_vals
    #     # if self.restrict_partner_id and self.restrict_partner_id != self.company_id.partner_id:
    #     #     # if the move isn't owned by the company, we don't make any valuation
    #     #     return am_vals
    #
    #     company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
    #     company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False
    #
    #     journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
    #     # Create Journal Entry for products arriving in the company; in case of routes making the link between several
    #     # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
    #     if self._is_in():
    #         if self._is_returned(valued_type='in'):
    #             am_vals.append(self.with_company(company_to)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
    #         else:
    #             am_vals.append(self.with_company(company_to)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))
    #
    #     # Create Journal Entry for products leaving the company
    #     if self._is_out():
    #         cost = -1 * cost
    #         if self._is_returned(valued_type='out'):
    #             am_vals.append(self.with_company(company_from)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
    #         else:
    #             am_vals.append(self.with_company(company_from)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))
    #
    #     if self.company_id.anglo_saxon_accounting:
    #         # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
    #         if self._is_dropshipped():
    #             if cost > 0:
    #                 am_vals.append(self.with_company(self.company_id)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))
    #             else:
    #                 cost = -1 * cost
    #                 am_vals.append(self.with_company(self.company_id)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))
    #         elif self._is_dropshipped_returned():
    #             if cost > 0:
    #                 am_vals.append(self.with_company(self.company_id)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
    #             else:
    #                 cost = -1 * cost
    #                 am_vals.append(self.with_company(self.company_id)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
    #
    #     return am_vals


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _compute_account_moves(self):
        acc_move_obj = self.env['account.move']
        for item in self:
            item.acc_move_count = len(acc_move_obj.sudo().search([('stock_move_id','in',item.move_ids.ids)]))
            
    acc_move_count = fields.Integer(string="Account Moves Count", compute='_compute_account_moves')
    sum_price = fields.Float(string="Нийт үнэ", compute="_compute_sum_price")

    def _compute_sum_price(self):
        for item in self:
            if item.move_ids:
                item.sum_price = round(sum([line.niit_urtug for line in item.move_ids]), 2)
            else:
                item.sum_price = 0
    def action_view_account_moves(self):
        
        return {
                'name': 'Account moves',
                'type': 'ir.actions.act_window',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                # 'view_id':self.env.ref("account.view_move_tree", False).id,
                'domain': [('stock_move_id', 'in', self.move_ids.ids)],
            }

class StockValuationLayer(models.Model):
    """Stock Valuation Layer"""
    _inherit = 'stock.valuation.layer'

    company_id = fields.Many2one('res.company', 'Company', readonly=True, required=True, index=True)
    product_id = fields.Many2one('product.product', 'Product', readonly=True, required=True, check_company=True, index=True)
    account_move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True, check_company=True, index=True)

class account_move(models.Model):
    _inherit = 'account.move'

    stock_picking_id = fields.Many2one('stock.picking', string='Агуулахын баримт', related='stock_move_id.picking_id')
    product_haih_id = fields.Many2one('product.product', related='line_ids.product_id', string='Бараанд хайх')

class product_product(models.Model):
    _inherit = 'product.product'

    def action_view_aml(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_moves_all_tree').read()[0]
        domain_quant = [('product_id', '=', self.id)]
        action['domain'] = domain_quant
        action['context'] = {}
        return action


    def _change_standard_price(self, new_price):
        """Helper to create the stock valuation layers and the account moves
        after an update of standard price.

        :param new_price: new standard price
        """
        # Handle stock valuation layers.
        if self.filtered(lambda p: p.valuation == 'real_time') and not self.env['stock.valuation.layer'].check_access_rights('read', raise_exception=False):
            raise UserError(_("You cannot update the cost of a product in automated valuation as it leads to the creation of a journal entry, for which you don't have the access rights."))

        svl_vals_list = []
        company_id = self.env.company
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        rounded_new_price = float_round(new_price, precision_digits=price_unit_prec)
        for product in self:
            # if product.cost_method not in ('standard', 'average'):
            continue

    def _run_fifo_vacuum(self, company=None):
        """Compensate layer valued at an estimated price with the price of future receipts
        if any. If the estimated price is equals to the real price, no layer is created but
        the original layer is marked as compensated.

        :param company: recordset of `res.company` to limit the execution of the vacuum
        """
        self.ensure_one()
        if company is None:
            company = self.env.company
        svls_to_vacuum = self.env['stock.valuation.layer'].sudo().search([
            ('product_id', '=', self.id),
            ('remaining_qty', '<', 0),
            ('stock_move_id', '!=', False),
            ('company_id', '=', company.id),
        ], order='create_date, id')
        if not svls_to_vacuum:
            return

        as_svls = []

        domain = [
            ('company_id', '=', company.id),
            ('product_id', '=', self.id),
            ('remaining_qty', '>', 0),
            ('create_date', '>=', svls_to_vacuum[0].create_date),
        ]
        all_candidates = self.env['stock.valuation.layer'].sudo().search(domain)

        for svl_to_vacuum in svls_to_vacuum:
            # We don't use search to avoid executing _flush_search and to decrease interaction with DB
            candidates = all_candidates.filtered(
                lambda r: r.create_date > svl_to_vacuum.create_date
                or r.create_date == svl_to_vacuum.create_date
                and r.id > svl_to_vacuum.id
            )
            if not candidates:
                break
            qty_to_take_on_candidates = abs(svl_to_vacuum.remaining_qty)
            qty_taken_on_candidates = 0
            tmp_value = 0
            for candidate in candidates:
                qty_taken_on_candidate = min(candidate.remaining_qty, qty_to_take_on_candidates)
                qty_taken_on_candidates += qty_taken_on_candidate

                candidate_unit_cost = candidate.remaining_value / candidate.remaining_qty
                value_taken_on_candidate = qty_taken_on_candidate * candidate_unit_cost
                value_taken_on_candidate = candidate.currency_id.round(value_taken_on_candidate)
                new_remaining_value = candidate.remaining_value - value_taken_on_candidate

                candidate_vals = {
                    'remaining_qty': candidate.remaining_qty - qty_taken_on_candidate,
                    'remaining_value': new_remaining_value
                }
                candidate.write(candidate_vals)
                if not (candidate.remaining_qty > 0):
                    all_candidates -= candidate

                qty_to_take_on_candidates -= qty_taken_on_candidate
                tmp_value += value_taken_on_candidate
                if float_is_zero(qty_to_take_on_candidates, precision_rounding=self.uom_id.rounding):
                    break

            # Get the estimated value we will correct.
            remaining_value_before_vacuum = svl_to_vacuum.unit_cost * qty_taken_on_candidates
            new_remaining_qty = svl_to_vacuum.remaining_qty + qty_taken_on_candidates
            corrected_value = remaining_value_before_vacuum - tmp_value
            svl_to_vacuum.write({
                'remaining_qty': new_remaining_qty,
            })

            # Don't create a layer or an accounting entry if the corrected value is zero.
            if svl_to_vacuum.currency_id.is_zero(corrected_value):
                continue

            # corrected_value = svl_to_vacuum.currency_id.round(corrected_value)
            # move = svl_to_vacuum.stock_move_id
            # vals = {
            #     'product_id': self.id,
            #     'value': corrected_value,
            #     'unit_cost': 0,
            #     'quantity': 0,
            #     'remaining_qty': 0,
            #     'stock_move_id': move.id,
            #     'company_id': move.company_id.id,
            #     'description': 'Revaluation of %s (negative inventory)' % (move.picking_id.name or move.name),
            #     'stock_valuation_layer_id': svl_to_vacuum.id,
            # }
            # vacuum_svl = self.env['stock.valuation.layer'].sudo().create(vals)

            # if self.valuation != 'real_time':
            #     continue
            # as_svls.append((vacuum_svl, svl_to_vacuum))

        # If some negative stock were fixed, we need to recompute the standard price.
        product = self.with_company(company.id)
        if product.product_tmpl_id.cost_method == 'average' and not float_is_zero(product.quantity_svl, precision_rounding=self.uom_id.rounding):
            product.sudo().with_context(disable_auto_svl=True).write({'standard_price': product.value_svl / product.quantity_svl})

        self.env['stock.valuation.layer'].browse(x[0].id for x in as_svls)._validate_accounting_entries()

        for vacuum_svl, svl_to_vacuum in as_svls:
            self._create_fifo_vacuum_anglo_saxon_expense_entry(vacuum_svl, svl_to_vacuum)

class product_template(models.Model):
    _inherit = 'product.template'

    def action_view_aml(self):
        self.ensure_one()
        action = self.env.ref('account.action_account_moves_all_tree').read()[0]
        domain_quant= [('product_id.product_tmpl_id', 'in', self.ids)]
        action['domain'] = domain_quant
        action['context'] = {}
        return action