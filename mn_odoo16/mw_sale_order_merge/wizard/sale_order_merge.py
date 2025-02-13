# -*- coding: utf-8 -*-
from odoo import fields, models, api
from odoo.exceptions import UserError


class SaleOrderMerge(models.TransientModel):
    _name = 'sale.order.merge'
    _description = 'Sale order merge'

    sale_order_ids = fields.Many2many('sale.order', string='Бусад')
    sale_order_id = fields.Many2one('sale.order', string='Нэгтгэх санал')
    update_pricelist = fields.Boolean(string='Үнийн хүснэгт харилцагчаар солих', default=False)

    @api.constrains("sale_order_ids")
    def check_sale_share_ids(self):
        if self.sale_order_ids.filtered(lambda l: l.state != 'draft'):
            raise UserError('Заавал ноорог төлөвтэй захиалгыг сонгоно уу')
        if len(self.sale_order_ids.mapped('partner_id')) != 1:
            raise UserError('Ижилхэн харилцагч байх ёстой')

    def action_merge(self):
        self.check_sale_share_ids()
        query = "UPDATE sale_order_line set order_id = {0} where order_id in {1}".format(self.sale_order_id.id,
                                                                                         str(self.sale_order_ids.ids).replace('[', '(').replace(']', ')'))
        self.env.cr.execute(query)
        rem_ids = self.sale_order_ids.ids
        rem_ids.remove(self.sale_order_id.id)
        # Зүгээр надаа хэрэгтэй байсымо
        if self.update_pricelist:
            self.sale_order_id.change_product_pricelist()
        self.env.cr.execute("DELETE FROM sale_order where id in {0}".format(str(rem_ids).replace('[', '(').replace(']', ')')))
