# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_allow_to_create_draft_order = fields.Boolean(related='pos_config_id.iface_allow_to_create_draft_order',
                                                        readonly=False)

