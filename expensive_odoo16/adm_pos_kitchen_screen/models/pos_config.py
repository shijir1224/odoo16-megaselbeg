# -*- coding: utf-8 -*-

from odoo import models, fields

class PosConfig(models.Model):
    _inherit = 'pos.config'

    iface_allow_to_create_draft_order = fields.Boolean(default=True)
