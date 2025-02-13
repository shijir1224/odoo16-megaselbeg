# -*- coding: utf-8 -*-
# Part of Softhealer Technologies.

from odoo import models, fields, api


class LablePrint(models.TransientModel):
    _name = 'sh.dynamic.lable.print'
    _description = 'Dynamic Lable Print'

    sh_lable_template_id = fields.Many2one(
        'sh.dynamic.template', string="Label Print Template", required=True)
    sh_lable_print_line_ids = fields.One2many(
        'sh.dynamic.lable.print.line', 'lable_id', string='Dynamic Lable Line')
    sh_company_logo = fields.Boolean('Company Logo ?')
    sh_company_logo_height = fields.Char('Logo Height(px)')
    sh_company_logo_width = fields.Char('Logo Width(px)')
    sh_company_logo_align = fields.Selection([('left','Left'),('center','Center'),('right','Right')],string='Logo Align')
    sh_display_strike_price = fields.Boolean('Display Strike Price ?')

    @api.model
    def default_get(self, fields_list):
        """Set Default Product and it's quantity to label template popup while click on dynamic label action"""
        res = super(LablePrint, self).default_get(fields_list)
        context = self.env.context
        line_ids = []

        if context.get('active_model') == 'product.template' and context.get('active_ids'):
            for template in self.env[context.get('active_model')].sudo().browse(context.get('active_ids')):
                line_vals = {
                    'product_id': template.product_variant_id.id,
                    'quantity': 1,
                    'sh_lot_number':False,
                    'sh_lot_related_fields_visible':False
                }
                if template.product_variant_id.tracking in ['lot','serial']:
                    line_vals.update({
                        'sh_lot_tracking':True
                    })
                line_ids.append((0, 0, line_vals))
        elif context.get('active_model') == 'product.product' and context.get('active_ids'):
            for product in self.env[context.get('active_model')].sudo().browse(context.get('active_ids')):
                line_vals = {
                    'product_id': product.id,
                    'quantity': 1,
                    'sh_lot_number':False,
                    'sh_lot_related_fields_visible':False
                }
                if product.tracking in ['lot','serial']:
                    line_vals.update({
                        'sh_lot_tracking':True
                    })
                line_ids.append((0, 0, line_vals))
        elif context.get('active_model') == 'sale.order' and context.get('active_ids'):
            for order in self.env[context.get('active_model')].sudo().browse(context.get('active_ids')):
                for line in order.order_line:
                    line_vals = {
                        'partner_id':order.partner_id.id,
                        'product_id': line.product_id.id,
                        'sh_lot_number':False,
                        'sh_lot_related_fields_visible':False
                    }
                    if line.product_id.tracking in ['lot','serial']:
                        line_vals.update({
                            'sh_lot_tracking':True
                        })
                    quantity = int(line.product_uom_qty)
                    if self.env.user.company_id.sh_sale_quantity_configuration and self.env.user.company_id.sh_sale_quantity_configuration == 'delivered':
                        quantity = int(line.qty_delivered)
                    elif self.env.user.company_id.sh_sale_quantity_configuration and self.env.user.company_id.sh_sale_quantity_configuration == 'invoiced':
                        quantity = int(line.qty_invoiced)
                    line_vals.update({
                        'quantity': quantity,
                    })
                    line_ids.append((0, 0, line_vals))
        elif context.get('active_model') == 'account.move' and context.get('active_ids'):
            for move in self.env[context.get('active_model')].sudo().browse(context.get('active_ids')):
                for line in move.invoice_line_ids:
                    line_vals = {
                        'partner_id':move.partner_id.id,
                        'product_id': line.product_id.id,
                        'quantity': int(line.quantity),
                        'sh_lot_number':False,
                        'sh_lot_related_fields_visible':False
                    }
                    if line.product_id.tracking in ['lot','serial']:
                        line_vals.update({
                            'sh_lot_tracking':True
                        })
                    line_ids.append((0, 0, line_vals))
        elif context.get('active_model') == 'purchase.order' and context.get('active_ids'):
            for order in self.env[context.get('active_model')].sudo().browse(context.get('active_ids')):
                for line in order.order_line:
                    line_vals = {
                        'partner_id':order.partner_id.id,
                        'product_id': line.product_id.id,
                        'sh_lot_number':False,
                        'sh_lot_related_fields_visible':False
                    }
                    if line.product_id.tracking in ['lot','serial']:
                        line_vals.update({
                            'sh_lot_tracking':True
                        })
                    quantity = int(line.product_qty)
                    if self.env.user.company_id.sh_purchase_quantity_configuration and self.env.user.company_id.sh_purchase_quantity_configuration == 'received':
                        quantity = int(line.qty_received)
                    elif self.env.user.company_id.sh_purchase_quantity_configuration and self.env.user.company_id.sh_purchase_quantity_configuration == 'billed':
                        quantity = int(line.qty_invoiced)
                    line_vals.update({
                        'quantity':quantity
                    })
                    line_ids.append((0, 0, line_vals))
        elif context.get('active_model') == 'stock.picking' and context.get('active_ids'):
            for order in self.env[context.get('active_model')].sudo().browse(context.get('active_ids')):
                without_lot_moves = self.env['stock.move'].sudo().search([('picking_id','=',order.id),('product_id.tracking','in',['none'])])
                if without_lot_moves:
                    for move in without_lot_moves:
                        line_vals = {
                            'partner_id':order.partner_id.id or False,
                            'product_id': move.product_id.id,
                            'sh_lot_number':False,
                            'sh_lot_related_fields_visible':True
                        }
                        if move.product_id.tracking in ['lot','serial']:
                            line_vals.update({
                                'sh_lot_tracking':True
                            })
                        quantity = int(move.product_uom_qty)
                        if self.env.user.company_id.sh_stock_quantity_configuration and self.env.user.company_id.sh_stock_quantity_configuration == 'done':
                            quantity = int(move.quantity_done)
                        line_vals.update({
                            'quantity': quantity,
                        })
                        line_ids.append((0, 0, line_vals))
                with_lot_move_moves = self.env['stock.move'].sudo().search([('picking_id','=',order.id),('product_id.tracking','in',['lot','serial'])])
                if with_lot_move_moves:
                    move_lines = self.env['stock.move.line'].sudo().search([('move_id','in',with_lot_move_moves.ids)])
                    if move_lines:
                        for move_line in move_lines:
                            line_vals = {
                                'partner_id':order.partner_id.id or False,
                                'product_id': move_line.product_id.id,
                                'quantity': int(move_line.qty_done),
                                'sh_lot_related_fields_visible':True
                            }
                            if move_line.product_id.tracking in ['lot','serial']:
                                line_vals.update({
                                    'sh_lot_tracking':True
                                })
                            if move_line.lot_name:
                                line_vals.update({
                                    'sh_lot_number':move_line.lot_name
                                })
                            if move_line.lot_id:
                                line_vals.update({
                                    'sh_lot_number':move_line.lot_id.name
                                })
                            quantity = int(move_line.move_id.product_uom_qty)
                            if self.env.user.company_id.sh_stock_quantity_configuration and self.env.user.company_id.sh_stock_quantity_configuration == 'done':
                                quantity = int(move_line.qty_done)
                            line_vals.update({
                                'quantity': quantity,
                            })
                            line_ids.append((0, 0, line_vals))
                
        res.update({
            'sh_lable_print_line_ids': line_ids
        })
        return res

    def print_dynamic_label(self):
        """Button For print label"""
        datas = self.read()[0]
        products = []
        if self.sh_lable_print_line_ids:
            for line in self.sh_lable_print_line_ids:
                product_vals = {
                    'partner_id':line.partner_id.id,
                    'product_id': line.product_id.id,
                    'qty': line.quantity,
                    'sh_lot_print':line.sh_lot_print,
                    'sh_lot_tracking':line.sh_lot_tracking,
                    'sh_lot_number':line.sh_lot_number
                }
                products.append(product_vals)
        datas.update({
            'product_dic': products
        })
        datas.update({
            'sh_lable_template_id': self.sh_lable_template_id.id,
        })
        report_id = self.env.ref(
            'sh_all_in_one_barcode_label.sh_barcode_report_action')
        report_id.sudo().paperformat_id = False
        report_id.sudo().paperformat_id = self.sh_lable_template_id.paperformat_id.id
        report_id.sudo().paperformat_id.report_ids = [(4,report_id.id)]
        return self.env.ref('sh_all_in_one_barcode_label.sh_barcode_report_action').report_action([], data=datas)


class LablePrintLine(models.TransientModel):
    _name = 'sh.dynamic.lable.print.line'
    _description = 'Dynamic Lable Print Line'

    lable_id = fields.Many2one(
        'sh.dynamic.lable.print', string='Dynamic Label')
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Partner')
    quantity = fields.Integer('Barcode Quantity', default=1)
    sh_lot_number = fields.Char('Lot Number',readonly=True)
    sh_lot_print = fields.Boolean('Print Lot Number as barcode label ?')
    sh_lot_tracking = fields.Boolean('Lot Tracking')
    sh_lot_related_fields_visible = fields.Boolean('Lot Related Fields Visible')

