# -*- coding: utf-8 -*-
from . import models
from . import wizard

from odoo import api, registry, SUPERUSER_ID, _

def _post_init_odoo_chatgpt(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    return {
            'type': 'ir.actions.act_window',
            'name': _('Pedir Acessos Jumotech'),
            'res_model': 'ask.email.jumotech',
            'view_mode': 'form',
            'usage': 'menu',
            'context': {},
            'domain': [],
            'target': 'new',
        }