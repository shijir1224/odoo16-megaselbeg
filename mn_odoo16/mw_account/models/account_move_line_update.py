# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning,UserError
from odoo.tools import float_compare, float_is_zero, float_round
from calendar import monthrange
from odoo.tools import float_compare
from math import copysign

class AccountMoveLineUpdate(models.Model):
    _name = 'account.move.line.update'
    _description = 'Account Move Line Update'
    _inherit = 'analytic.mixin' 



    move_line_ids = fields.Many2many('account.move.line', string='Мөрүүд', default=lambda self: self.env.context.get('active_ids', []))
    branch_id = fields.Many2one('res.branch', string='Салбар')

    def change_button(self):
        for i in self.move_line_ids:
            if self.branch_id:
                i.branch_id = self.branch_id.id

