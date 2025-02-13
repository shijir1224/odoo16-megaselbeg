# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models
from odoo.tools.float_utils import float_compare
import logging

from odoo.tools.safe_eval import pytz

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_method = fields.Selection([
        ('sale', 'Захиалсан тоогоор'),
        ('receive', 'Хүргэгдсэн Тоогоор'),
    ], string="Борлуулалтын Нэхэмжлэх Үүсгэх")
    sale_receive_invoice = fields.Boolean(string="Зарлага Гарсаны Дараа Нэхэмжлэх Үүсгэх", default=False)
    post_invoice = fields.Boolean(string="Нэхэмжлэх шууд батлах", default=False)

class sale_order(models.Model):
    _inherit = 'sale.order'

    def _create_invoices(self, grouped=False, final=False):
        invoice_vals = super(sale_order, self)._create_invoices(grouped, final)
        for item in self:
            if item.partner_id.sale_method=='sale':
                item._force_lines_to_invoice_policy_order()
        return invoice_vals

    def _prepare_invoice(self):
        invoice_vals = super(sale_order, self)._prepare_invoice()
        picking_done_date = self.env.context.get('so_picking_date', False)
        if self.picking_ids and not picking_done_date:
            picks = self.picking_ids.filtered(lambda r: r.date_done)
            if len(picks) > 0:
                picking_done_date = picks[0].date_done
                for p in picks:
                    if p.date_done > picking_done_date:
                        picking_done_date = p.date_done
        _logger.info(" ========_prepare_invoice iin context==%s=====\n", self.env.context)                        
        if picking_done_date:
            user_tz = self.env.user.tz or self.env.context.get('tz')
            user_pytz = pytz.timezone(user_tz) if user_tz else pytz.utc
            picking_done_date = pytz.utc.localize(picking_done_date, is_dst=None)
            picking_done_date = picking_done_date.astimezone(user_pytz).replace(tzinfo=None)
            invoice_vals['invoice_date'] = picking_done_date
            invoice_vals['date'] = picking_done_date
        return invoice_vals

    def _get_invoiceable_lines(self, final=False):
        lines = super(sale_order, self)._get_invoiceable_lines(final)
        pre_lines=lines.filtered(lambda r: r.is_downpayment)
        if self.env.context.get('so_picking_id',False):
            pick_id = self.env['stock.picking'].browse(self.env.context.get('so_picking_id',False))
            sol_ids = pick_id.mapped('move_ids.sale_line_id')
            lines = lines.filtered(lambda r: r.id in sol_ids.ids or (r.product_id.type=='service' and r.qty_invoiced==0))
        lines+=pre_lines
        return lines

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    def get_sale_method(self, sale_method):
        res = super(stock_picking, self).get_sale_method(sale_method)
        if self.partner_id.sale_method:
            res = self.partner_id.sale_method
        return res

    def action_done(self):
        res = super(stock_picking, self).action_done()
        for picking in self:
            # Нэхэмжлэх үүсгэх
            if picking.picking_type_id.code == 'outgoing' and picking.sudo().sale_id and picking.partner_id.sale_receive_invoice:
                invoice = picking.sale_id.with_context(so_picking_date=fields.Date.context_today(self),so_picking_id=picking.id)._create_invoices(final=True)
                if picking.partner_id.post_invoice:
                    invoice.post()
                # invoice = hnpicking.sale_id.deduct_down_paymentsz(picking.partner_id.sale_method, picking=picking)
                # if invoice:
                #     invoice.action_post()
        return res
    
    def create_invoice_so(self):
        for picking in self:
            # Нэхэмжлэх үүсгэх
            if picking.picking_type_id.code == 'outgoing' and picking.sudo().sale_id:
#                 picking.sale_id.with_context(so_picking_date=fields.Date.context_today(self),so_picking_id=picking.id)._create_invoices(final=True)
 # Өнөөдрөөр биш дууссан огноо авна
                so_picking_date=picking.date_done and picking.date_done or fields.Date.context_today(self)
                picking.sale_id.with_context(so_picking_date=so_picking_date,so_picking_id=picking.id)._create_invoices(final=True)
