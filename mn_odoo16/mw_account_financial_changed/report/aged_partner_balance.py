# © 2016 Julien Coux (Camptocamp)
# Copyright 2020 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import operator
from datetime import date, datetime, timedelta

from odoo import api, models
from odoo.tools import float_is_zero


class AgedPartnerBalanceReport(models.AbstractModel):
    _inherit = "report.account_financial_report.aged_partner_balance"
    _description = "Aged Partner Balance Report"

    @api.model
    def _calculate_amounts(
        self, ag_pb_data, acc_id, prt_id, residual, due_date, date_at_object
    ):
        ag_pb_data[acc_id]["residual"] += residual
        ag_pb_data[acc_id][prt_id]["residual"] += residual
        today = date_at_object
        if due_date and acc_id:
            account=self.env['account.account'].browse(acc_id)
            print ('account2 ',account.code)
            if account.aged_number:
                aged_number=account.aged_number-30
                print ('aged_number1 ',aged_number)
                # if aged_number>0:
                due_date = due_date + timedelta(days=aged_number)
        if not due_date or today <= due_date:
            ag_pb_data[acc_id]["current"] += residual
            ag_pb_data[acc_id][prt_id]["current"] += residual
        elif today <= due_date + timedelta(days=30):
            ag_pb_data[acc_id]["30_days"] += residual
            ag_pb_data[acc_id][prt_id]["30_days"] += residual
        elif today <= due_date + timedelta(days=60):
            ag_pb_data[acc_id]["60_days"] += residual
            ag_pb_data[acc_id][prt_id]["60_days"] += residual
        elif today <= due_date + timedelta(days=90):
            ag_pb_data[acc_id]["90_days"] += residual
            ag_pb_data[acc_id][prt_id]["90_days"] += residual
        elif today <= due_date + timedelta(days=120):
            ag_pb_data[acc_id]["120_days"] += residual
            ag_pb_data[acc_id][prt_id]["120_days"] += residual
        else:
            ag_pb_data[acc_id]["older"] += residual
            ag_pb_data[acc_id][prt_id]["older"] += residual
        return ag_pb_data

    @api.model
    def _compute_maturity_date(self, ml, date_at_object):
        ml.update(
            {
                "current": 0.0,
                "30_days": 0.0,
                "60_days": 0.0,
                "90_days": 0.0,
                "120_days": 0.0,
                "older": 0.0,
            }
        )
        due_date = ml["due_date"]
        if ml.get('line_rec',False):
            account=ml['line_rec'].account_id
            if account.aged_number:
                aged_number=account.aged_number-30
                due_date = due_date + timedelta(days=aged_number)

        amount = ml["residual"]
        today = date_at_object
        if not due_date or today <= due_date:
            ml["current"] += amount
        elif today <= due_date + timedelta(days=30):
            ml["30_days"] += amount
        elif today <= due_date + timedelta(days=60):
            ml["60_days"] += amount
        elif today <= due_date + timedelta(days=90):
            ml["90_days"] += amount
        elif today <= due_date + timedelta(days=120):
            ml["120_days"] += amount
        else:
            ml["older"] += amount

