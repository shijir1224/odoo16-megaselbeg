# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from odoo import fields, models, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from dateutil.relativedelta import relativedelta


class account_account_close(models.Model):
    _name = "account.account.close"
    _description = "Account close"
    _inherit = ['mail.thread']
    _order = "date_start, id"


    description = fields.Char('Нэр', required=True)
    name = fields.Char('Fiscal Year', required=True, tracking=True)
    date_start = fields.Date('Start Date', required=True, tracking=True)
    date_stop = fields.Date('End Date', required=True, tracking=True)
    state = fields.Selection([('draft','Open'), ('done','Closed')], 'Status', readonly=True, copy=False, default='draft', tracking=True)
    account_ids = fields.Many2many('account.account', 'account_account_close_rel', 'close_id', 'account_id', 'Accounts', tracking=True)
    partner_ids = fields.Many2many('res.partner', 'account_partner_close_rel', 'close_id', 'partner_id', 'Partners', tracking=True)
    account_and_partner = fields.Boolean('Account partner both?',)
    company_id = fields.Many2one('res.company', string="Компани", default=lambda self: self.env.user.company_id, tracking=True, copy=False)


