# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)


class SaleReturn(models.Model):
    _name = 'sale.return'
    _description = 'Бор-н буцаалт'
    _order = 'date DESC'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Дугаар', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default=lambda self: 'Шинэ')
    date = fields.Date(required=True, copy=False, default=fields.Date.context_today, string="Огноо")
    partner_id = fields.Many2one('res.partner', 'Захиалагч', required=True)
    warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', required=True)
    company_id = fields.Many2one('res.company', string='Компани', required=True,
                                 default=lambda self: self.env.company.id)
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Үнийн хүснэгт', check_company=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Нэгж үнийг тооцоолоход ашиглана")
    currency_id = fields.Many2one('res.currency', related='pricelist_id.currency_id', string='Currency', required=True,
                                  readonly=True)
    amount_untaxed = fields.Monetary(string='Татваргүй дүн', store=True, readonly=True, compute='_amount_all',
                                     tracking=True)
    amount_tax = fields.Monetary(string='Татвар', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Нийт', store=True, readonly=True, compute='_amount_all')
    taxes_id = fields.Many2many('account.tax', string='Татвар',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('calculated', 'Шалгасан'),
        ('cancelled', 'Цуцалсан'),
        ('confirmed', 'Баталсан'),
        ('done', 'Дууссан'),
    ], 'Төлөв', default='draft', copy=False, tracking=True)
    return_line = fields.One2many('sale.return.line', 'return_id', string='Мөрүүд', copy=True)
    sale_line_ids = fields.Many2many('sale.order.line', 'sale_return_so_line_rel', 'return_id', 'sale_line_id',
                                     string='Буцаах борлуулалтууд', copy=False)
    show_import_button = fields.Boolean('Импортлохыг харуулах', default=False, copy=False, store=True)
    picking_count = fields.Integer(compute='_picking_count', string='Шилжүүлгийн тоо')
    picking_ids = fields.One2many('stock.picking', 'sale_return_id', string='Шилжүүлгүүд')
    invoice_count = fields.Integer(compute='_invoice_count', string='Нэхэмжлэлийн тоо')
    invoice_ids = fields.One2many('account.move', 'sale_return_id', string='Нэхэмжлэлүүд')
    need_create_invoice = fields.Boolean(compute='_compute_need_create_invoice')
    salesman_id = fields.Many2one('res.users', 'Борлуулагч', )

    def _compute_need_create_invoice(self):
        for rec in self:
            if not rec.invoice_count and rec.state in ['confirmed', 'done']:
                rec.need_create_invoice = True
            else:
                rec.need_create_invoice = False

    def create_invoice(self):
        for order in self:
            addr = order.partner_id.address_get(['invoice'])
            move_line_vals = []
            # Нэхэмжлэл буцаах
            for line in order.return_line:
                price_unit = line.price_unit
                if line.taxes_id:
                    price_unit = line.taxes_id.with_context(round=False).compute_all(
                        price_unit,
                        currency=line.return_id.currency_id,
                        quantity=1.0,
                    )['total_included']
                move_line_vals.append((0, 0, {'name': order.name,
                                              'date_maturity': order.date or fields.Date.today(),
                                              'price_unit': price_unit,
                                              'quantity': line.qty,
                                              'partner_id': order.partner_id.id,
                                              'company_id': order.company_id.id,
                                              'tax_ids': [(6, 0, line.taxes_id.ids)]}))
            refund_invoice = self.env['account.move'].with_context({'default_move_type': 'out_refund'}).create({
                'currency_id': order.currency_id.id,
                'move_type': 'out_refund',
                'partner_id': addr['invoice'] if addr['invoice'] else order.partner_id.id,
                'ref': order.name,
                'branch_id': self.env.user.branch_id.id or False,
                'date': order.date,
                'invoice_line_ids': move_line_vals
            })
            refund_invoice.sale_return_id = order
            # butsaaltiin nehemjleh buruu bodood
            # refund_invoice.action_post()
            refund_invoice.message_post_with_view(
                'mail.message_origin_link',
                values={'self': refund_invoice, 'origin': order},
                subtype_id=self.env.ref('mail.mt_note').id
            )

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if len(self.return_line) > 0:
            raise UserError('Сонгогдсон бараануудын үнэ харилцагчаас хамааран өөрчлөгдөх магадлалтай тул бараануудаа хасаад шинээр нэмээрэй')

        if self.partner_id:
            self.pricelist_id = self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False
        else:
            self.pricelist_id = False

        self.sale_line_ids = False

    @api.onchange('pricelist_id')
    def onchange_pricelist_id(self):
        if len(self.return_line) > 0:
            raise UserError(
                'Сонгогдсон бараануудын үнэ үнийн хүснэгтээс хамааран өөрчлөгдөх магадлалтай тул бараануудаа хасаад шинээр нэмээрэй')

    @api.onchange('taxes_id')
    def onchange_taxes_id(self):
        for line in self.return_line:
            line.taxes_id = self.taxes_id

    @api.onchange('sale_line_ids')
    def onchange_sale_line_ids(self):
        if self.sale_line_ids:
            self.show_import_button = True
        else:
            self.show_import_button = False

    @api.model
    def create(self, vals):
        if vals.get('name', 'Шинэ') == 'Шинэ':
            seq_date = None
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].with_company(vals['company_id']).next_by_code(
                    'sale.return') or 'Шинэ'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.return') or 'Шинэ'

        if 'pricelist_id' not in vals:
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            vals['pricelist_id'] = vals.setdefault('pricelist_id',
                                                   partner.property_product_pricelist and partner.property_product_pricelist.id)

        result = super(SaleReturn, self).create(vals)
        return result

    # Үнэ дахин бодох ================================
    def button_dummy(self):
        for line in self.return_line:
            line._compute_price_unit()
        _logger.info('-------- RS Button dummy -----')

    def import_lines(self):
        self.return_line.unlink()
        for line in self.sale_line_ids:
            move_lines = self.env['stock.move.line']
            moves = self.env['stock.move'].search([
                ('sale_line_id', '=', line.id),
                ('picking_type_id', '=', self.warehouse_id.out_type_id.id),
                ('state', '=', 'done')
            ])
            move_lines |= moves.move_line_ids
            for move_line in move_lines:
                qty = move_line.qty_done
                if line.product_uom != move_line.product_uom_id:
                    qty = move_line.product_uom_id._compute_quantity(qty, line.product_uom, round=False)
                self.env['sale.return.line'].create({
                    'return_id': self.id,
                    'product_id': line.product_id.id,
                    'qty': qty,
                    'product_uom': line.product_uom.id,
                    'lot_id': move_line.lot_id.id,
                    'taxes_id': [(6, 0, self.taxes_id.ids)],
                    'sale_line_id': line.id
                })
        self.return_line._compute_price_unit()

    @api.depends('return_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.return_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id and order.currency_id.round(amount_untaxed) or amount_untaxed,
                'amount_tax': order.currency_id and order.currency_id.round(amount_tax) or amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })

    def _picking_count(self):
        for rec in self:
            rec.picking_count = len(rec.picking_ids)

    def _invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids.filtered(lambda x: x.move_type == 'out_refund'))

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError('Зөвхөн ноорог буцаалтыг устгах боломжтой')
        return super(SaleReturn, self).unlink()

    def action_to_cancel(self):
        self.picking_ids.filtered(lambda r: r.state != 'cancel').action_cancel()
        self.state = 'cancelled'

    def action_view_pickings(self):
        self.ensure_one()
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        pickings = self.mapped('picking_ids')
        action['domain'] = [('sale_return_id', '=', self.id)]
        action['context'] = dict(self._context, default_sale_return_id=self.id, create=False)
        return action

    def action_view_invoices(self):
        self.ensure_one()
        action = self.env.ref('account.action_move_out_refund_type').read()[0]
        invoices = self.mapped('invoice_ids')
        action['domain'] = [('sale_return_id', '=', self.id), ('move_type', '=', 'out_refund')]
        action['context'] = dict(self._context, default_sale_return_id=self.id, create=False)
        return action

    def calculate(self):
        self.ensure_one()
        order = self
        if not order.return_line:
            raise UserError('Буцаах бараануудаа сонгоно уу')
        check_line_qty = False
        for line in order.return_line:
            if line.qty > 0:
                check_line_qty = True
                break
        if not check_line_qty:
            raise UserError('Буцаах барааны тоог оруулна уу')
        order.state = 'calculated'

    def get_move_line(self, line, order, location_src_id, location_dest_id, new_picking, line_qty, picking_type_id):
        name = line.product_id.name_get()[0][1]
        res = {
            'product_id': line.product_id.id,
            'name': name,
            'product_uom_qty': line_qty,
            'product_uom': line.product_id.uom_id.id,
            'picking_id': new_picking.id,
            'location_id': location_src_id,
            'location_dest_id': location_dest_id,
            'picking_type_id': picking_type_id,
            'warehouse_id': order.warehouse_id.id,
            'procure_method': 'make_to_stock',
            'state': 'draft',
            'origin': order.name,
            'sale_return_line_id': line.id,
            # 'move_line_ids': [(0, 0, {
            #     'product_id': line.product_id.id,
            #     'product_uom_qty': 0,  # bypass reservation here
            #     'product_uom_id': line.product_id.uom_id.id,
            #     'qty_done': line_qty,
            #     'location_id': location_src_id,
            #     'location_dest_id': location_dest_id,
            #     'lot_id': line.lot_id.id if line.lot_id else False,
            #     'picking_id': new_picking.id,
            # })]
        }
        return res

    def confirm(self):
        order = self
        location_dest_id = order.warehouse_id.out_type_id.return_picking_type_id.default_location_dest_id.id
        location_src = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1)
        if not location_src:
            raise UserError('Захиалагчийн байрлал олдсонгүй')
        location_src_id = location_src.id
        picking_type_id = order.warehouse_id.in_type_id.id
        addr = order.partner_id.address_get(['delivery', 'invoice'])

        new_picking = self.env['stock.picking'].create({
            'location_id': location_src_id,
            'location_dest_id': location_dest_id,
            'picking_type_id': picking_type_id,
            'partner_id': addr['delivery'],
            'origin': order.name,
            'sale_return_id': order.id
        })

        for line in order.return_line:
            line_qty = line.qty
            if line.product_uom != line.product_id.uom_id:
                line_qty = line.product_uom._compute_quantity(line_qty, line.product_id.uom_id, round=False)
            if line_qty > 0:
                # price_unit = line.price_unit_cost
                # if line.product_uom != line.product_id.uom_id:
                #     price_unit *= line.product_uom.factor / line.product_id.uom_id.factor
                new_move = self.env['stock.move'].create(
                    self.get_move_line(line, order, location_src_id, location_dest_id, new_picking, line_qty,
                                       picking_type_id))

        # Хийхээр тэмдэглэх
        new_picking.action_confirm()
        # Нөөц шалгах
        new_picking.action_assign()

        # Зурвас үүсгэх
        new_picking.message_post_with_view(
            'mail.message_origin_link',
            values={'self': new_picking, 'origin': order},
            subtype_id=self.env.ref('mail.mt_note').id
        )

        # Нэхэмжлэл буцаах
        refund_invoice = self.env['account.move'].with_context({'default_move_type': 'out_refund'}).create({
            'currency_id': order.currency_id.id,
            'move_type': 'out_refund',
            'partner_id': addr['invoice'],
            'ref': order.name
        })
        # for line in order.return_line:
        #     fiscal_position = refund_invoice.fiscal_position_id
        #     accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
        #     price_unit = line.price_unit
        #     if line.taxes_id:
        #         price_unit = line.taxes_id.with_context(round=False).compute_all(
        #             price_unit,
        #             currency=line.return_id.currency_id,
        #             quantity=1.0,
        #         )['total_included']
        #     refund_invoice.write({
        #         'invoice_line_ids': [(0, 0, {
        #             'move_id': refund_invoice.id,
        #             'product_id': line.product_id.id,
        #             'account_id': accounts['income'].id,
        #             'quantity': line.qty,
        #             'product_uom_id': line.product_uom.id,
        #             'price_unit': price_unit,
        #             'tax_ids': [(6, 0, line.taxes_id.ids)]
        #         })]
        #     })
        # refund_invoice.sale_return_id = order
        # # butsaaltiin nehemjleh buruu bodood
        # refund_invoice.action_post()
        # refund_invoice.message_post_with_view(
        #     'mail.message_origin_link',
        #     values={'self': refund_invoice, 'origin': order},
        #     subtype_id=self.env.ref('mail.mt_note').id
        # )
        order.state = 'confirmed'

    def to_draft(self):
        self.write({'state': 'draft'})


class SaleReturnLine(models.Model):
    _name = 'sale.return.line'
    _description = 'Sale Batch Return Line'

    return_id = fields.Many2one('sale.return', 'Бор-н буцаалт', ondelete='cascade')
    product_id = fields.Many2one('product.product', 'Бараа', ondelete='restrict', required=True)
    qty = fields.Float('Тоо хэмжээ', digits='Product Unit of Measure', default=1.0)
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure',
                                  domain="[('category_id', '=', product_uom_category_id)]", required=True)
    price_unit = fields.Float(default=0.0, string='Нэгж үнэ', required=True, digits='Product Price', copy=False)
    price_unit_cost = fields.Float(compute='_compute_price_unit_cost', default=0.0, string='Өртөг үнэ', required=True,
                                   digits='Product Price', store=True, copy=False)
    price_subtotal = fields.Float(compute='_compute_amount', string='Үнийн дүн', store=True)
    price_total = fields.Float(compute='_compute_amount', string='Дэд дүн', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Татвар', store=True)
    taxes_id = fields.Many2many('account.tax', string='Татвар',
                                domain=['|', ('active', '=', False), ('active', '=', True)])
    lot_id = fields.Many2one('stock.production.lot', 'Цуврал')
    sale_line_id = fields.Many2one('sale.order.line', 'Бор-н мөр', copy=False)
    stock_moves = fields.One2many('stock.move', 'sale_return_line_id', 'Буцаасан барааны хөдөлгөөнүүд')
    cost_method = fields.Selection(related='product_id.cost_method', readonly=True)

    @api.onchange('product_id', 'taxes_id', 'sale_line_id', 'product_uom')
    def _compute_price_unit(self):
        # TODO: tax price_include calculation missing for all price
        for line in self:
            product = line.product_id.with_context(
                lang=line.return_id.partner_id.lang,
                partner=line.return_id.partner_id,
                quantity=line.qty,
                pricelist=line.return_id.pricelist_id.id,
                uom=line.product_uom.id
            )
            price_unit = 0.0
            if line.sale_line_id:
                price_unit = line.sale_line_id.price_unit
                if line.sale_line_id.tax_id:
                    price_unit = line.sale_line_id.tax_id.with_context(round=False).compute_all(
                        price_unit,
                        currency=line.sale_line_id.order_id.currency_id,
                        quantity=1.0
                    )['total_included']
            else:
                if self.return_id.pricelist_id and self.return_id.partner_id:
                    price_unit = self.env['account.tax'].with_context(
                        is_create_auto_purchase=True)._fix_tax_included_price_company(line._get_display_price(product),
                                                                                      product.taxes_id, line.taxes_id,
                                                                                      line.return_id.company_id)

            # update list price according uom
            if line.sale_line_id:
                if line.product_uom and line.product_uom != line.sale_line_id.product_uom:
                    price_unit *= line.sale_line_id.product_uom.factor / line.product_uom.factor
            else:
                if line.product_uom and line.product_uom != line.product_id.uom_id:
                    price_unit *= line.product_id.uom_id.factor / line.product_uom.factor

            # calculate tax
            if line.taxes_id:
                price_unit = \
                    line.taxes_id.with_context(round=False).compute_all(price_unit, currency=line.return_id.currency_id,
                                                                        quantity=1.0)['total_included']

            line.price_unit = price_unit

    @api.depends('product_id', 'taxes_id', 'sale_line_id', 'product_uom', 'return_id.pricelist_id',
                 'return_id.partner_id')
    def _compute_price_unit_cost(self):
        # TODO: tax price_include calculation missing for all price
        for line in self:
            if line.sale_line_id:
                stock_move = self.env['stock.move'].search([
                    ('sale_line_id', '=', line.sale_line_id.id),
                    ('state', '=', 'done'),
                    ('picking_type_id', '=', line.return_id.warehouse_id.out_type_id.id)], limit=1)
                price_unit_cost = stock_move.price_unit
            else:
                price_unit_cost = line.get_current_cost()

            # update cost price according uom
            if line.product_uom and line.product_uom != line.product_id.uom_id:
                price_unit_cost *= line.product_id.uom_id.factor / line.product_uom.factor

            line.price_unit_cost = price_unit_cost

    def _get_display_price(self, product):
        self.ensure_one()
        if self.return_id.pricelist_id.discount_policy == 'with_discount':
            return product.with_context(pricelist=self.return_id.pricelist_id.id).price
        product_context = dict(self.env.context, partner_id=self.return_id.partner_id.id, uom=self.product_uom.id)
        final_price, rule_id = self.return_id.pricelist_id.with_context(product_context).get_product_price_rule(
            self.product_id, self.qty or 1.0, self.return_id.partner_id)
        return final_price

    def get_current_cost(self):
        self.ensure_one()
        cost = self.product_id.standard_price
        if self.product_id.cost_method == 'fifo':
            svl = self.env['stock.valuation.layer'].search([
                ('product_id', '=', self.product_id.id),
                ('company_id', '=', self.return_id.company_id.id),
                ('remaining_qty', '>', 0)
            ], limit=1, order='create_date, id')
            if svl:
                cost = svl.unit_cost
        return cost

    @api.depends('qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                currency=vals['currency_id'],
                quantity=vals['qty'],
                product=vals['product'],
                partner=vals['partner'],
            )
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency_id': self.return_id.currency_id,
            'qty': self.qty,
            'product': self.product_id,
            'partner': self.return_id.partner_id,
        }

    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            line._product_id_change()
            line.taxes_id = line.return_id.taxes_id

    def _product_id_change(self):
        if not self.product_id:
            return
        self.product_uom = self.product_id.uom_id
