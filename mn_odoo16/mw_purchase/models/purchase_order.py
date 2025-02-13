# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import timedelta, date
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang, groupby
from odoo.tools.float_utils import float_round, float_is_zero
import logging

_logger = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    taxes_id = fields.Many2many('account.tax', string='Taxes', tracking=True)
    warehouse_id = fields.Many2one('stock.warehouse', related='picking_type_id.warehouse_id', string='Warehouse')
    total_qty_count = fields.Float(string='Нийт тоо хэмжээ', compute='_compute_total_qty_count')

    @api.depends('order_line')
    def _compute_total_qty_count(self):
        for item in self:
            if item.order_line:
                item.total_qty_count = sum([line.product_qty for line in item.order_line])
            else:
                item.total_qty_count = 0

    @api.model
    def _get_picking_type(self, company_id):
        if self.env.user.warehouse_id.company_id.id == company_id:
            picking_type = self.env.user.warehouse_id.in_type_id
        else:
            picking_type = self.env.user.warehouse_ids.filtered(lambda w: w.company_id.id == company_id).mapped('in_type_id')
        return picking_type[:1]

    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.picking_type_id = self._get_picking_type(self.company_id.id)

    @api.onchange('currency_id')
    def onch_po_type(self):
        for item in self:
            if item.currency_id != item.company_id.currency_id:
                item.po_type = 'foreign'
            else:
                item.po_type = 'internal'

    @api.onchange('taxes_id')
    def onchange_taxes_id(self):
        for line in self.order_line:
            line.taxes_id = self.taxes_id

    # Хөнгөлөлтийн хувийг харилцагчаас авах
    @api.onchange('partner_id')
    def onchange_partner_discount(self):
        for line in self.order_line:
            line.discount = self.partner_id.discount_percent

    def action_update_stock_account_move_price_from_po(self):
        move_obj = self.env['stock.move']
        for po in self:
            for item in po.order_line:
                move_ids = move_obj.search([('purchase_line_id', '=', item.id)])
                for move_id in move_ids:
                    if move_id.state == 'done':
                        obj = self.env['stock.move.change.price.unit']
                        change = obj.create({
                            'stock_move_ids': move_id.id,
                            'change_price_unit': round(item.price_unit_stock_move, 2)
                        })
                        change.with_context(force_update=True).set_change_price_unit()
                    else:
                        move_id.price_unit = round(item.price_unit_stock_move, 2)

    def button_cancel(self):
        for order in self:
            received_line_order = False
            not_done_pick = False
            if order.picking_ids.filtered(lambda r: r.state not in ['done', 'cancel']):
                not_done_pick = True
            if order.order_line.filtered(lambda r: r.qty_received > 0):
                received_line_order = True
            if not_done_pick or received_line_order:
                if order.picking_ids.filtered(lambda r: r.state == 'done'):
                    raise UserError(
                        _('Unable to cancel purchase order %s as some receptions have already been done.') % order.name)
            for inv in order.invoice_ids:
                if inv and inv.state not in ('cancel', 'draft'):
                    raise UserError(
                        _("Unable to cancel this purchase order. You must first cancel related vendor bills."))

            # If the product is MTO, change the procure_method of the the closest move to purchase to MTS.
            # The purpose is to link the po that the user will manually generate to the existing moves's chain.
            if order.state in ('draft', 'sent', 'to approve'):
                for order_line in order.order_line:
                    if order_line.move_dest_ids:
                        siblings_states = (order_line.move_dest_ids.mapped('move_orig_ids')).mapped('state')
                        if all(state in ('done', 'cancel') for state in siblings_states):
                            order_line.move_dest_ids.write({'procure_method': 'make_to_stock'})
                            order_line.move_dest_ids._recompute_state()

            if not_done_pick or received_line_order:
                for pick in order.picking_ids.filtered(lambda r: r.state != 'cancel'):
                    pick.action_cancel()

        self.write({'state': 'cancel'})

    def button_approve(self, force=False):
        res = super(PurchaseOrder, self).button_approve(force=force)
        # Нэхэмжлэх үүсгэх
        for po in self:
            if po.company_id.auto_create_vendor_bill and po.order_line:
                if po.order_line[0].product_id.purchase_method == 'purchase':
                    po.create_invoice_hand()
                    if po.company_id.auto_validate_vendor_bill:
                        for obj in po.invoice_ids.filtered(lambda i: i.state == 'draft'):
                            obj.action_post()
        return res

    @api.depends('state', 'order_line.qty_to_invoice', 'order_line.qty_received')
    def _get_invoiced(self):
        for order in self:
            service_products = order.order_line.filtered(lambda r: r.product_id.purchase_method == 'purchase')
            receive_products = order.order_line.filtered(lambda r: r.product_id.purchase_method == 'receive')
            if len(order.order_line.filtered(lambda r: r.qty_received == 0)) == len(order.order_line):
                order.invoice_status = 'no'
            if ((round(sum(order.order_line.mapped('qty_received')), 2) != round(sum(order.order_line.mapped('qty_invoiced')), 2)) and round(sum(order.order_line.mapped('qty_received')), 2) != 0) or (order.order_line.filtered(lambda r: r.product_id.purchase_method == 'purchase' and r.qty_to_invoice != 0)):
                order.invoice_status = 'to invoice'
            if (round(sum(order.order_line.mapped('product_qty')), 2) == round(sum(order.order_line.mapped('qty_received')), 2) == round(sum(order.order_line.mapped('qty_invoiced')), 2)) or (len(order.order_line.filtered(lambda r: r.product_id.purchase_method == 'purchase' and r.qty_to_invoice == 0)) == len(order.order_line)) or (sum(service_products.mapped('product_qty')) == round(sum(service_products.mapped('qty_invoiced')), 2) and (round(sum(receive_products.mapped('product_qty')), 2) == round(sum(receive_products.mapped('qty_received')), 2) == round(sum(receive_products.mapped('qty_invoiced')), 2))):
                order.invoice_status = 'invoiced'

    def create_invoice_hand(self):
        self.order_line._compute_qty_invoiced()
        nemegdel_zardaltai_line = self.order_line.filtered(lambda r: r.add_cost_ids and r.qty_to_invoice > 0)
        nemegdel_zardalgui_line = self.order_line.filtered(lambda r: not r.add_cost_ids and r.qty_to_invoice > 0)
        add_cost_ids = nemegdel_zardaltai_line.mapped('add_cost_ids')
        if nemegdel_zardaltai_line and len(add_cost_ids) > 1:
            for add_cost in add_cost_ids:
                add_cost_po_line = nemegdel_zardaltai_line.filtered(lambda r: r.add_cost_ids in add_cost)
                self.with_context(default_branch_id=self.branch_id.id).action_create_invoice(add_cost_po_line)
        elif nemegdel_zardaltai_line and len(add_cost_ids) == 1:
            self.with_context(default_branch_id=self.branch_id.id).action_create_invoice(nemegdel_zardaltai_line)
        if nemegdel_zardalgui_line:
            self.with_context(default_branch_id=self.branch_id.id).action_create_invoice(nemegdel_zardalgui_line)
    
    def action_create_invoice(self, po_lines):
        """Create the invoice associated to the PO.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')

        # 1) Prepare invoice vals and clean-up the section lines
        invoice_vals_list = []
        analytic_distribution = False
        sequence = 10
        for order in self:
            if order.invoice_status != 'to invoice':
                continue

            order = order.with_company(order.company_id)
            pending_section = None
            # Invoice values.
            invoice_vals = order._prepare_invoice()
            # Invoice line values (keep only necessary sections).
            if po_lines.filtered(lambda r: r.add_cost_ids):
                for line in po_lines:
                    if line.analytic_distribution:
                        analytic_distribution = line.analytic_distribution
                    add_cost_rate = line.add_cost_ids.current_rate
                    add_cost_date = line.add_cost_ids.date
                    invoice_vals.update({'date': add_cost_date, 'invoice_date': add_cost_date})
                    if invoice_vals.get('rate_manual', False) and invoice_vals.get('rate_manual_amount', False):
                        invoice_vals.update({'rate_manual': True, 'rate_manual_amount': add_cost_rate})

                    if line.display_type == 'line_section':
                        pending_section = line
                        continue
                    if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        if pending_section:
                            line_vals = pending_section._prepare_account_move_line()
                            line_vals.update({'sequence': sequence})
                            invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                            sequence += 1
                            pending_section = None
                        line_vals = line._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                invoice_vals_list.append(invoice_vals)
            if po_lines.filtered(lambda r: not r.add_cost_ids):
                for line in po_lines:
                    if line.analytic_distribution:
                        analytic_distribution = line.analytic_distribution
                    if line.display_type == 'line_section':
                        pending_section = line
                        continue
                    # invoice_vals.update({'date': self.date_order, 'invoice_date': self.date_order}) # TODO
                    if not float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        if pending_section:
                            line_vals = pending_section._prepare_account_move_line()
                            line_vals.update({'sequence': sequence})
                            invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                            sequence += 1
                            pending_section = None
                        line_vals = line._prepare_account_move_line()
                        line_vals.update({'sequence': sequence})
                        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
                        sequence += 1
                invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise UserError(_('There is no invoiceable line. If a product has a control policy based on received quantity, please make sure that a quantity has been received.'))

        # 2) group by (company_id, partner_id, currency_id) for batch creation
        new_invoice_vals_list = []
        for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: (x.get('company_id'), x.get('partner_id'), x.get('currency_id'))):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': self.name,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

        # 3) Create invoices.
        moves = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        for vals in invoice_vals_list:
            moves |= AccountMove.with_company(vals['company_id']).create(vals)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        moves.filtered(lambda m: m.currency_id.round(m.amount_total) < 0).action_switch_invoice_into_refund_credit_note()
        moves.update({'branch_id': self.branch_id.id})
        for move in moves:
            move.invoice_line_ids.write({'analytic_distribution': analytic_distribution})
        moves.update({'branch_id': self.branch_id.id})
        return self.action_view_invoice(moves)

    def _prepare_invoice(self):
        res = super(PurchaseOrder, self)._prepare_invoice()
        res['date'] = res['invoice_date'] = date.today()
        return res

    def create_auto_invoice(self, from_purchase_method, picking=False):
        self.ensure_one()
        po_lines = self.order_line
        origin = self.name or ''
        origin_inv = self.name
        invoice_date = fields.Date.context_today(self)
        if picking:
            origin += (' /' + picking.invoice_number if picking.invoice_number else '')
            po_lines = picking.move_ids.filtered(lambda m: m.state == 'done').mapped('purchase_line_id')
            invoice_date = picking.scheduled_date + timedelta(hours=8)
        try:
            if hasattr(po_lines, 'add_cost_ids') and po_lines.add_cost_ids:
                order_ids = po_lines.mapped('add_cost_ids')
                if order_ids:
                    invoice_date = order_ids[0].date
        except Exception as e:
            _logger.info(' has no add_cost_ids ------- ', e)

        # create invoice line values
        invoice_line_ids = []
        for line in po_lines:
            qty_inv = 0
            if from_purchase_method == 'purchase' or line.product_id.type in ['service', 'consu']:
                qty_inv = line.product_qty - line.qty_invoiced if (line.product_qty - line.qty_invoiced) > 0 else 0
            elif from_purchase_method == 'receive':
                qty_inv = line.qty_received - line.qty_invoiced if (line.qty_received - line.qty_invoiced) > 0 else 0
            rnd = line.product_uom.rounding or 0.001
            if qty_inv > rnd:
                # accounts = line.product_id.product_tmpl_id.get_product_accounts(fiscal_pos=self.fiscal_position_id)
                tmp = {'product_id': line.product_id.id,
                    #    'account_id': accounts['expense'].id,
                       'quantity': qty_inv,
                       'product_uom_id': line.product_uom.id,
                       'price_unit': line.price_unit,
                       'tax_ids': [(6, 0, line.taxes_id.ids)],
                       'purchase_line_id': line.id,
                       }
                if line.product_id and line.product_id.type == 'service':
                    tmp.update({'name': line.name})
                invoice_line_ids.append(
                    (0, 0, tmp)
                )
        if invoice_line_ids:
            _logger.info(u'invoice_line_ids=====: %s invoice_line_ids' % invoice_line_ids)

            invoice = self.env['account.move'].create({
                'ref': origin,
                'move_type': 'in_invoice',
                'company_id': self.company_id.id,
                'partner_id': self.partner_id.id,
                'fiscal_position_id': self.fiscal_position_id.id,
                'invoice_payment_term_id': self.payment_term_id.id,
                'currency_id': self.currency_id.id,
                'invoice_line_ids': invoice_line_ids,
                'invoice_date': invoice_date,
                'date': invoice_date,
                'payment_reference': origin_inv
            })

            # Compute invoice_origin.
            origins = set(invoice.line_ids.mapped('purchase_line_id.order_id.name'))
            invoice.invoice_origin = ','.join(list(origins))
            invoice.partner_bank_id = invoice.bank_partner_id.bank_ids and invoice.bank_partner_id.bank_ids[0]
        else:
            invoice = False
        return invoice


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # display_name = fields.Char(string='Display Name', compute='_compute_new_name', readonly=False)
    other_qty_received = fields.Float(string='Other qty received', default=0)
    detailed_type = fields.Selection(related='product_id.detailed_type', string='Барааны төрөл')
    partner_id = fields.Many2one('res.partner', related='order_id.partner_id', string='Partner', readonly=True, store=True, index=True)
    company_id = fields.Many2one('res.company', related='order_id.company_id', string='Company', store=True, readonly=True, index=True)
    sequence = fields.Integer(string='Sequence', default=10, index=True)
    qty_received = fields.Float("Received Qty", compute='_compute_qty_received', inverse='_inverse_qty_received', compute_sudo=True, store=True, digits='Product Unit of Measure', index=True)

    # @api.depends('product_id', 'product_qty', 'product_uom', 'company_id')
    # def _compute_new_name(self):
    #     for item in self:
    #         if item.product_id and item.product_qty:
    #             item.name = ('[%s]' %(item.product_id.default_code)) if item.product_id.default_code else '' + (' [%s]' %(item.product_id.product_code)) if item.product_id.product_code else '' + ' ' + item.product_id.name + ' ' + item.product_qty
    #         else:
    #             item.name = ''

    @api.depends('move_ids.state', 'move_ids.product_uom_qty', 'move_ids.product_uom')
    def _compute_qty_received(self):
        super(PurchaseOrderLine, self)._compute_qty_received()
        for line in self:
            if line.qty_received_method == 'stock_moves':
                total = 0.0
                # In case of a BOM in kit, the products delivered do not correspond to the products in
                # the PO. Therefore, we can skip them since they will be handled later on.
                for move in line.move_ids:
                    if move.state == 'done':
                        if move.location_dest_id.usage == "supplier":
                            if move.to_refund:
                                total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        elif move.origin_returned_move_id and move.origin_returned_move_id._is_dropshipped() and not move._is_dropshipped_returned():
                            # Edge case: the dropship is returned to the stock, no to the supplier.
                            # In this case, the received quantity on the PO is set although we didn't
                            # receive the product physically in our stock. To avoid counting the
                            # quantity twice, we do nothing.
                            pass
                        elif move.location_dest_id.usage == "internal" and move.to_refund and move.location_dest_id not in self.env["stock.location"].search([("id", "child_of", move.warehouse_id.view_location_id.id)]):
                            total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        else:
                            total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                if line.other_qty_received > 0:
                    line.qty_received = line.other_qty_received
                else:
                    line.qty_received = total

    def _get_qty_procurement(self):
        self.ensure_one()
        # other_qty_received тооцоолох хамаарах
        if self.other_qty_received>0:
            return super()._get_qty_procurement()+self.other_qty_received
        return super()._get_qty_procurement()
    
                        
    # Хөнгөлөлт
    discount = fields.Float('Discount(%)')
    price_unit_without_discount = fields.Float(
        string='Price Unit (without discount)',
        required=True, default=0,
        digits='Product Price')

    tracking = fields.Selection(related='product_id.tracking', string="Tracking")
    # lot_id = fields.Many2one('stock.production.lot', 'Lot')
    # lot_expiration_date = fields.Datetime(related='lot_id.expiration_date', string="Lot end date", readonly=False)
    is_diff_receive_inv = fields.Boolean('Received and Invoiced differentiated', compute='_compute_rec_qty_inv',
                                         search='_search_rec_qty_inv')
    is_diff_qty_inv = fields.Boolean('Ordered and Invoiced differentiated', compute='_compute_rec_qty_inv',
                                     search='_search_qty_inv')

    # @api.depends(')
    def _compute_rec_qty_inv(self):
        for item in self:
            if item.qty_received != item.qty_invoiced:
                item.is_diff_receive_inv = True
            else:
                item.is_diff_receive_inv = False

            if item.product_qty != item.qty_invoiced:
                item.is_diff_qty_inv = True
            else:
                item.is_diff_qty_inv = False

    def _search_rec_qty_inv(self, operator, value):
        ids = []
        for item in self.env['purchase.order.line'].search([]):
            if item.is_diff_receive_inv:
                ids.append(item.id)
        return [('id', 'in', ids)]

    def _search_qty_inv(self, operator, value):
        ids = []
        for item in self.env['purchase.order.line'].search([]):
            if item.is_diff_qty_inv:
                ids.append(item.id)
        return [('id', 'in', ids)]

    @api.onchange('discount', 'price_unit_without_discount')
    def onchange_discount_price_unit(self):
        self.price_unit = self.price_unit_without_discount * (1 - (self.discount or 0.0) / 100.0)

    # Хөнгөлөлттэй холбоотой функц
    @api.onchange('price_unit')
    def onchange_main_price_unit(self):
        if not self.price_unit_without_discount and self.price_unit:
            self.price_unit_without_discount = self.price_unit

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        self.price_unit_without_discount = 0.0
        return res

    # @api.onchange('product_qty', 'product_uom')
    # def _onchange_quantity(self):
    #     price_unit = self.price_unit_without_discount
    #     res = super(PurchaseOrderLine, self)._onchange_quantity()
        # TODO: САЙН ШАЛГАХ: Хүсэлтээс захиалга үүсэх үед price_unit 0-лээд байсан учир price_unit_without_discount байгаа үед price_unit өөрчлөх шаардлагагүй гэж үзсэн.
        # if price_unit != self.price_unit:
            # self.price_unit_without_discount = self.price_unit
        # self.onchange_discount_price_unit()
        # return res

    def _product_id_change(self):
        super(PurchaseOrderLine, self)._product_id_change()
        # ХА-н х.н-г үндсэнээр авах
        if self.env.company.is_change_po_uom_to_uom:
            self.product_uom = self.product_id.uom_id
        # Хөнгөлөлтийн хувийг харилцагчаас авах
        self.discount = self.partner_id.discount_percent

    # Захиалга дээр татвар сонгох
    def _compute_tax_id(self):
        # Override
        for line in self:
            line.taxes_id = line.order_id.taxes_id

    # Тухайн Нийлүүлэгчээс худалдаж авж байгаагүй бол нэгж үнэ 0р авдаг болгосон
    @api.depends('product_qty', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines or not line.company_id:
                continue
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.context_today(line),
                uom_id=line.product_uom,
                params=params)

            if seller or not line.date_planned:
                line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            #TODO Нийлүүлэгчээс шууд үнэ авч байсныг болиулчлаа
            # If not seller, use the standard price. It needs a proper currency conversion.
            # if not seller:
            #     unavailable_seller = line.product_id.seller_ids.filtered(
            #         lambda s: s.partner_id == line.order_id.partner_id)
            #     if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
            #         # Avoid to modify the price unit if there is no price list for this partner and
            #         # the line has already one to avoid to override unit price set manually.
            #         continue
            #     po_line_uom = line.product_uom or line.product_id.uom_po_id
            #     price_unit = line.env['account.tax']._fix_tax_included_price_company(
            #         line.product_id.uom_id._compute_price(0, po_line_uom),
            #         line.product_id.supplier_taxes_id,
            #         line.taxes_id,
            #         line.company_id,
            #     )
            #     price_unit = line.product_id.currency_id._convert(
            #         price_unit,
            #         line.currency_id,
            #         line.company_id,
            #         line.date_order or fields.Date.context_today(line),
            #         False
            #     )
            #     line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
            #     continue

            # price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price, line.product_id.supplier_taxes_id, line.taxes_id, line.company_id) if seller else 0.0
            # price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id, line.date_order or fields.Date.context_today(line), False)
            # price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places, self.env['decimal.precision'].precision_get('Product Price')))
            # line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)

            # record product names to avoid resetting custom descriptions
            default_names = []
            vendors = line.product_id._prepare_sellers({})
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_analytic_distribution(self):
        return
        # TODO шинжилгээний данс авто авахуулахгүй
        # for line in self:
            # if not line.display_type:
            #     distribution = self.env['account.analytic.distribution.model']._get_distribution({
            #         "product_id": line.product_id.id,
            #         "product_categ_id": line.product_id.categ_id.id,
            #         "partner_id": line.order_id.partner_id.id,
            #         "partner_category_id": line.order_id.partner_id.category_id.ids,
            #         "company_id": line.company_id.id,
            #     })
            #     line.analytic_distribution = distribution or line.analytic_distribution

    def write(self, values):
        if 'product_id' in values:
            for line in self:
                if line.pr_line_many_ids:
                    product_id = self.env['product.product'].search([('id','=',values['product_id'])])
                    line.order_id.message_post_with_view('mw_purchase.track_po_line_product_template',
                                                         values={'line': line, 'product_id': product_id},
                                                         subtype_id=self.env.ref('mail.mt_note').id)
        return super(PurchaseOrderLine, self).write(values)

class ProductProduct(models.Model):
    _inherit = 'product.product'

    pol_ids = fields.One2many('purchase.order.line', 'product_id', 'Vendors', compute='com_pol_ids')

    def com_pol_ids(self):
        for item in self:
            if self.env.context.get('allowed_company_ids',False):
                item.pol_ids = self.env['purchase.order.line'].search([('product_id','=',item.id),('company_id','in',self.env.context.get('allowed_company_ids',False))])
            else:
                item.pol_ids = False

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pol_tmpl_ids = fields.One2many('purchase.order.line', related='product_variant_ids.pol_ids', readonly=True)
