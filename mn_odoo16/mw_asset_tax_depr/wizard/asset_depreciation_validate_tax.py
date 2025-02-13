# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AssetDepreciationConfirmationTax(models.TransientModel):
    _name = "asset.depreciation.confirmation.tax"
    _description = "asset.depreciation.confirmation.tax"

    date = fields.Date('Account Date', required=True,
                       help="Choose the period for which you want to automatically post the depreciation "
                            "lines of running assets", default=fields.Date.context_today)


    def asset_compute(self):
        self.ensure_one()
        context = self._context
        created_move_ids = self.env['account.asset'].compute_generated_entries_tax(self.date)


