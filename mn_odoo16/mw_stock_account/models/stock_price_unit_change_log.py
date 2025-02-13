# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
import odoo.addons.decimal_precision as dp


class StockPriceUnitChangeLog(models.Model):
    _name = "stock.price.unit.change.log"
    _description = "stock.price.unit.change.log"

    product_id = fields.Many2one("product.product", "Бараа", ondelete="cascade")
    product_tmpl_id = fields.Many2one(
        "product.template", related="product_id.product_tmpl_id"
    )
    new_standard_price = fields.Float(
        "Cost New",
        digits=dp.get_precision("Product Price"),
        groups="base.group_user",
    )
    company_id = fields.Many2one("res.company", "Компани")

    _order = "create_date desc"


class ProductTemplate(models.Model):
    _inherit = "product.template"

    cost_change_log_ids = fields.One2many(
        "stock.price.unit.change.log", "product_tmpl_id", "Өртөгийн өөрчлөлт"
    )


class ProductProduct(models.Model):
    _inherit = "product.product"

    cost_change_log_ids = fields.One2many(
        "stock.price.unit.change.log",
        "product_id",
        "Өртөгийн өөрчлөлт",
    )

    def write(self, values):
        res = super(ProductProduct, self).write(values)
        if "standard_price" in values:
            self.create_standard_price_change_log()
        return res

    @api.depends("standard_price")
    def create_standard_price_change_log(self):
        log_obj = self.env["stock.price.unit.change.log"]
        for item in self:
            if len(item.cost_change_log_ids) > 0:
                if (
                    abs(
                        abs(item.standard_price)
                        - abs(item.cost_change_log_ids[0].new_standard_price)
                    )
                    > 0.0001
                ):
                    log_obj.create(
                        {
                            "new_standard_price": item.standard_price,
                            "product_id": item.id,
                            "company_id": self.env.user.company_id.id,
                        }
                    )
            else:
                log_obj.create(
                    {
                        "new_standard_price": item.standard_price,
                        "product_id": item.id,
                        "company_id": self.env.user.company_id.id,
                    }
                )
