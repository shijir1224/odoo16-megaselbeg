# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)


class AccountBudgetConfiguration(models.Model):
    _name = "mw.account.budget.configuration"
    _description = "Budget configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Name")
    description = fields.Text("Description")
    line_ids = fields.One2many("mw.account.budget.configuration.line", "parent_id", copy=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )


class AccountBudgetConfigurationLine(models.Model):
    _name = "mw.account.budget.configuration.line"
    _description = "Budget configuration line"

    parent_id = fields.Many2one("mw.account.budget.configuration","Budget",ondelete="cascade",)
    name = fields.Char('Name',required=True)
    account_ids = fields.Many2many('account.account', 'account_mw_budget_line_rel', 'budget_id', 'account_id', 'Accounts')

    item_ids = fields.Many2many('mw.account.budget.items', 'account_mw_budget_item_line_rel', 'budget_id', 'item_id', 'Items')



class AccountBudgetItems(models.Model):
    _name = "mw.account.budget.items"
    _description = "Budget Items"

    code = fields.Char("Code",)
    name = fields.Char('Name',required=True)
    account_ids = fields.Many2many('account.account', 'account_mw_budget_items_line_rel', 'budget_id', 'account_id', 'Accounts')

