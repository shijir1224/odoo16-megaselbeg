# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class pos_session(models.Model):
    """docstring for AccountJournal"""
    _inherit = 'pos.session'

    last_ebarimt_senddata = fields.Date('Ибаримт',copy=False, readonly=True)

    def set_last_ebarimt_senddata(self, sess_id):
        obj_id = self.browse(sess_id)
        obj_id.last_ebarimt_senddata = fields.Date.context_today(self)