# -*- coding: utf-8 -*-
import calendar
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from calendar import monthrange
from odoo import fields, models, api, _
from odoo.tools import float_compare, float_is_zero, formatLang, end_of
from odoo.exceptions import ValidationError, UserError
from math import copysign
from odoo.osv import expression
# from odoo.exceptions import UserError
DAYS_PER_MONTH = 30
DAYS_PER_YEAR = DAYS_PER_MONTH * 12





class AccountAsset(models.Model):
    _inherit = "account.asset"


    is_project = fields.Boolean(string='Төслийн харилцагч', tracking=True)

    # @api.onchange('is_project')
    def onchange_is_project(self):
        for lines in self.depreciation_move_ids.line_ids:
            # print(lines)
            print('ssss',lines.parent_state)
            print('mmmm',self.is_project)
            if lines.parent_state == 'draft' and self.is_project ==True:
                print('sss',self.branch_id.partner_id.id)
                # lines.partner_id = self.branch_id.partner_id.id if self.branch_id.partner_id else self.owner_id.id
                lines.write({'partner_id': self.branch_id.partner_id.id if self.branch_id.partner_id else self.owner_id.id})
                print('sssmm',lines.partner_id)
            elif lines.parent_state == 'draft' and self.is_project ==False: 
                lines.write({'partner_id': self.owner_id.id})
            # print(s)
