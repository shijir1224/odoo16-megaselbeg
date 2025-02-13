from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    priority = fields.Selection([("0", "Normal"), ("1", "Urgent")], "Priority", default="0", index=True)
