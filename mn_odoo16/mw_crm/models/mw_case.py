# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class crm_case_mw(models.Model):
    _name = 'crm.case'
    _inherit = 'mail.thread'
    _description = 'crm case'

    name = fields.Char('Шалтгаан', tracking=True)
    partner_id = fields.Many2one('res.partner', 'Харилцагч', tracking=True)
    type = fields.Selection([('')], 'Шалтгаан', tracking=True)
    