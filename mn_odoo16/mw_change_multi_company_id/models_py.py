# -*- coding: utf-8 -*-
from odoo import api, fields, models

class res_users(models.Model):
    _inherit = "res.users"

    def write_company(self, vals):
        if not self.env.user.has_group("mw_change_multi_company_id.group_change_not_company"):
            self.write(vals)
