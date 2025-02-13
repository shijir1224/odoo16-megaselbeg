from odoo import models, fields


class SaleOrder(models.Model):
    _inherit = "sale.order"

    priority = fields.Selection([("0", "Normal"), ("1", "Urgent")], "Priority", default="0", index=True)
