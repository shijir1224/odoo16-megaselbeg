# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountAssetHistory(models.Model):
    _name = 'account.asset.history'
    _description = 'Asset history'
    _order = 'date desc'

    name = fields.Char('History name')
    move_id = fields.Many2one('account.move', 'Account move')
    user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.uid)
    date = fields.Date('Date')
    asset_id = fields.Many2one('account.asset.asset', 'Asset')
    action = fields.Selection([('capital', 'Capitalization'),
                               ('revaluation', 'Revaluation'),
                               ('close', 'Close'),
                               ('sale', 'Sale')], 'Action', default='capital')
    old_method_number = fields.Integer('Old Number of Depreciations')
    old_method_period = fields.Integer('Old Period Length')
    old_method_end = fields.Date('Old Ending Date')
    old_value = fields.Float('Old Value')
    method_time = fields.Selection([('number', 'Number of Depreciations'), ('number_day', 'Day of Depreciations'), ('end', 'Ending Date')], 'Time Method', required=True,
                                   help="The method to use to compute the dates and number of depreciation lines.\n"
                                   "Number of Depreciations: Fix the number of depreciation lines and the time between 2 depreciations.\n"
                                   "Ending Date: Choose the time between 2 depreciations and the date the depreciations won't go beyond.")
    method_number = fields.Integer('Number of Depreciations', help="The number of depreciations needed to depreciate your asset")
    method_period = fields.Integer('Period Length', help="Time in month between two depreciations")
    method_end = fields.Date('Ending Date')
    amount = fields.Float('Amount Increase')
    company_id = fields.Many2one(string="Company", store=True)
    partner_id = fields.Many2one('res.partner', 'Performer Partner')
    department_id = fields.Many2one('hr.department', 'Performer Department')

    def unlink(self):
        for his in self:
            asset = his.asset_id
            closed = self._context.get('closed', False)
            if not closed and his.action in ('close', 'sale'):
                raise UserError(_("Cannot delete %s history of the sale, closed." % his.name))
            elif his.action in ('capital', 'revaluation'):
                history_ids = self.env['account.asset.history'].search([('asset_id', '=', his.asset_id.id), ('id', '!=', his.id), ('date', '>=', his.date), ('create_date', '<', his.create_date)])
                if len(history_ids):
                    raise UserError(_("Cannot delete %s history, only delete the most recent history." % his.name))
                if his.move_id:
                    his.move_id.button_cancel()
                    his.move_id.with_context(asset_unlink=True, force_delete=True).unlink()
                dep_line = asset.depreciation_line_ids.filtered(lambda x: x.depreciation_date == his.date and x.split_check)
                dep_line.with_context(delete=True).cancel_move()
                value = asset.value
                asset.write({'method_number': his.old_method_number,
                             'method_period': his.old_method_period,
                             'method_end': his.old_method_end,
                             'value': value - his.amount,
                             'capital_value': (his.asset_id.capital_value - his.amount) if his.action == 'capital' else his.asset_id.capital_value,
                             })
                asset.message_post(body=_("Deleted history. Value: %s -- %s") % (value, asset.value))
                asset.compute_depreciation_board()
        return super(AccountAssetHistory, self).unlink()


class AccountAssetChangeHistory(models.Model):
    _name = 'account.asset.change.history'
    _description = 'Asset Change History'
    _order = 'date desc'

    user_id = fields.Many2one('res.users', 'User')
    date = fields.Date('Date')
    asset_id = fields.Many2one('account.asset.asset', 'Asset')
    asset_code = fields.Char('Asset Code')
    old_method_number = fields.Integer('Old Number of Depreciations')
    old_general_method_number = fields.Integer('Old General Number of Entries')
    new_method_number = fields.Integer('New Number of Depreciations')
    new_general_method_number = fields.Integer('New General Number of Entries')

    def unlink(self):
        for his in self:
            asset = his.asset_id
            asset.check_cancel(his, 'change_history')
            period_ids = self.env['account.period'].search([('date_start', '>=', his.date), ('company_id', '=', asset.company_id.id), ('state', '=', 'done')])
            if len(period_ids):
                raise UserError(_("You cannot delete change history. Open period after."))
            asset.write({'method_number': his.old_method_number,
                         'general_method_number': his.old_general_method_number
                         })
            asset.message_post(body=_("Deleted change history. Method number: %s -- %s \n General method number: %s -- %s")
                                    % (his.new_method_number, his.old_method_number, his.new_general_method_number, his.old_general_method_number))
            asset.compute_depreciation_board()
        return super(AccountAssetChangeHistory, self).unlink()