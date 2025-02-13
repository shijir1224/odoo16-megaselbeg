from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

# Борлуулалтын хүргэлт дуусахад нэхэмжлэх үүсгэх батлах ======================

# BackOrder той


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def _process(self, cancel_backorder=False):
        res = super(StockBackorderConfirmation, self)._process(cancel_backorder)
        for confirmation in self:
                _logger.info('confirmation %s'%(confirmation))
                _logger.info('cancel_backorder %s'%(cancel_backorder))
#             if cancel_backorder:Дутагдлын захиалга үүсгэсэн ч нэхэмжлэх үүсэх
                for pick_id in confirmation.pick_ids:
                    # Зөвхөн борлуулалтын хүргэлт байна уу шалгах
                    _logger.info('pick_id %s'%(pick_id))
                    if pick_id.picking_type_id.code == 'outgoing' and pick_id.sale_id and pick_id.sale_id.state in ['sale', 'done']:
                        # Нэхэмжлэлийн бодлого шалгах
                        res_config = self.env['res.config.settings']
                        delivery_policy = res_config.sudo().create({}).default_invoice_policy
                        _logger.info('delivery_policy %s'%(delivery_policy))
                        if delivery_policy == 'delivery':
                            # Нэхэмжлэх байхгүй бол үүсгэх, батлах
                            if not pick_id.sale_id.invoice_ids:
                                context = {
                                    "active_model": 'sale.order',
                                    "active_ids": [pick_id.sale_id.id],
                                    "active_id": pick_id.sale_id.id,
                                    'open_invoices': False,
                                }
                                payment = self.env['sale.advance.payment.inv'].with_context(context).create({
                                    'advance_payment_method': 'delivered',
                                })
                                payment.with_context(context).create_invoices()
                                pick_id.sale_id.invoice_ids.action_post()
                            else:
                                # Батлагдаагүй бол батлах
                                for inv in pick_id.sale_id.invoice_ids:
                                    if inv.state == 'draft':
                                        inv.action_post()
        return res
