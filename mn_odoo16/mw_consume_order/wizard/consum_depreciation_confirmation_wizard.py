# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class consumDepreciationConfirmationWizard(models.TransientModel):
    _name = "consum.depreciation.confirmation.wizard"
    _description = "consum.depreciation.confirmation.wizard"

    date = fields.Date('Account Date', required=True, default=fields.Date.context_today)
    consum_ids = fields.Many2many('consumable.material.in.use', relation='table_consum_depr_consum_ids')

    def consum_compute(self):
        self.ensure_one()
        context = self._context
        created_move_ids=[]
        if self.consum_ids:
            for asset in self.consum_ids:
                lines=asset.depreciation_line_ids.filtered(lambda x: x.depreciation_date<=self.date)
                # print ('lines+++++ ',lines)
                try: 
                    lines.action_post()
                except Exception:
                    continue


    def consum_compute_create(self):
        self.ensure_one()
        context = self._context
        created_move_ids=[]
        if self.consum_ids:
            for asset in self.consum_ids:
                asset.compute_depreciation_board()
