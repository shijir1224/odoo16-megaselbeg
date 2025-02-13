# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class AssetDepreciationConfirmationWizard(models.TransientModel):
    _name = "asset.depreciation.confirmation.wizard"
    _description = "asset.depreciation.confirmation.wizard"

    date = fields.Date('Account Date', required=True,
                       help="Choose the period for which you want to automatically post the depreciation "
                            "lines of running assets", default=fields.Date.context_today)
    asset_types = fields.Many2many('account.asset.type', string="Хөрөнгийн төрөл")

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)

    is_all_types = fields.Boolean(string='Бүх төрөл сонгох')
    @api.onchange('is_all_types')
    def onchange_is_all_types(self):
        if self.is_all_types:
            self.asset_types = self.env['account.asset.type'].search([('company_id','=',self.company_id.id)])
        else:
            self.asset_types = False

    def asset_compute(self):
        self.ensure_one()
        context = self._context
        created_move_ids = self.env['account.asset'].compute_generated_entries(self.date, self.asset_types, self.company_id)

