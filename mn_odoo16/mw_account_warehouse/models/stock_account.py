# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp
from datetime import datetime
from odoo.exceptions import UserError
from ast import literal_eval
from odoo.tools.float_utils import float_is_zero


class account_move(models.Model):
    _inherit = 'account.move'

    stock_warehouse_id = fields.Many2one('stock.warehouse', string='Агуулах')
    
    # stock_warehouse_id = fields.Many2one(comodel_name='stock.warehouse',string='Warehouse',compute='_compute_stock_warehouse_id', store=True, readonly=False,
    #     precompute=True,index=True,auto_join=True,ondelete="cascade",)
    #
    # @api.depends('product_haih_id', 'stock_picking_id','line_ids.sale_line_ids')
    # def _compute_stock_warehouse_id(self):
    #     for move in self:
    #         if not move.stock_picking_id:
    #             move.stock_warehouse_id = move.stock_picking_id.picking_type_id.warehouse_id.id
    #         elif move.line_ids.sale_line_ids:
    #             move.stock_warehouse_id = move.line_ids.sale_line_ids.warehouse_id.id
    #         else:
    #             move.stock_warehouse_id = move.line_ids.sale_line_ids.warehouse_id.id

class StockWarehouse(models.Model):
    _name = 'stock.warehouse'
    _inherit = ["stock.warehouse", "analytic.mixin"]

    rec_account_id = fields.Many2one('account.account', 'Авлагын данс', domain="[('account_type', '=', 'asset_receivable')]",)
    pay_account_id = fields.Many2one('account.account', 'Өглөгийн данс', domain="[('account_type', '=', 'liability_payable')]",)

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.depends('display_type', 'company_id','move_id.stock_warehouse_id')
    def _compute_account_id(self):
        super()._compute_account_id()
        for move in self.move_id:
            if move.stock_warehouse_id and move.stock_warehouse_id.rec_account_id:
                rec_lines = self.filtered(lambda line: (
                    line.move_id.is_sale_document(include_receipts=True)
                    and line.display_type=='payment_term'
                ))

                print ('rec_lines1',rec_lines)
                for line in rec_lines:
                    line.account_id = move.stock_warehouse_id.rec_account_id.id
            if move.stock_warehouse_id and move.stock_warehouse_id.branch_id:
                move.branch_id=move.stock_warehouse_id.branch_id.id
            for line in move.line_ids:
                if line.display_type == 'product' and line.move_id.is_invoice(include_receipts=True) and line.move_id.stock_warehouse_id.analytic_distribution:
                    line.analytic_distribution = line.move_id.stock_warehouse_id.analytic_distribution
                if line.display_type == 'product' or not line.move_id.is_invoice(include_receipts=True) and line.move_id.stock_warehouse_id.branch_id:
                    line.branch_id = line.move_id.stock_warehouse_id.branch_id.id
            if move.stock_warehouse_id and move.stock_warehouse_id.pay_account_id:
                rec_lines = self.filtered(lambda line: (
                    line.move_id.is_purchase_document(include_receipts=True)
                    and line.display_type=='payment_term'
                ))
                print ('rec_lines2',rec_lines)
                for line in rec_lines:
                    line.account_id = move.stock_warehouse_id.pay_account_id.id
    # @api.depends('account_id', 'partner_id', 'product_id','move_id.stock_warehouse_id')
    # def _compute_analytic_distribution(self):
    #     for line in self:
    #         print('line2142512',line.display_type)
    #         if line.display_type == 'product' or not line.move_id.is_invoice(include_receipts=True):
    #             line.analytic_distribution = line.move_id.stock_warehouse_id.analytic_distribution

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals=super(PurchaseOrder, self)._prepare_invoice()
        invoice_vals.update({
            'stock_warehouse_id': self.picking_type_id.warehouse_id and self.picking_type_id.warehouse_id.id or False,
        })
        return invoice_vals
    

class sale_order(models.Model):
    _inherit = 'sale.order'

    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(sale_order, self)._prepare_invoice()
        invoice_vals.update({
            'stock_warehouse_id': self.warehouse_id and self.warehouse_id.id or False,
        })
        return invoice_vals
    
        