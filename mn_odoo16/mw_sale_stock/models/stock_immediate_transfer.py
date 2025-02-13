from odoo import api, fields, models, _
from odoo.exceptions import UserError


# OK хүргэлт ======================================
class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        res = super(StockImmediateTransfer, self).process()
        # Хүргэлт асуудалгүй бол нэхэмжлэх үүсгэх
        if not res:
            print ('self.pick_ids ',self.pick_ids)
            for pick_id in self.pick_ids:
                # Зөвхөн борлуулалтын хүргэлт байна уу шалгах
                if pick_id.picking_type_id.code == 'outgoing' and pick_id.sale_id and pick_id.sale_id.state in ['sale','done']:
                    # Нэхэмжлэлийн бодлого шалгах
                    res_config = self.env['res.config.settings']
                    delivery_policy = res_config.sudo().create({}).default_invoice_policy
                    if delivery_policy == 'delivery':
                        # Нэхэмжлэх байхгүй бол үүсгэх, батлах
#                         if not pick_id.sale_id.invoice_ids:20210630 хэд ч нэхэмжлэх үүсч болно
                        # too bval
                        qty_to_invoice=sum(pick_id.sale_id.order_line.mapped('qty_to_invoice')) 
                        if qty_to_invoice!=0:                           
                        # too bval
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
#                         else:
#                             # Батлагдаагүй бол батлах
#                             for inv in pick_id.sale_id.invoice_ids:
#                                 if inv.state == 'draft':
#                                     inv.action_post()

        return res
