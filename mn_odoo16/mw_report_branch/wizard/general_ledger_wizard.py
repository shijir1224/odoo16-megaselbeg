# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.tools import pycompat


class GeneralLedgerReportWizard(models.TransientModel):
    """General ledger report wizard."""

    _inherit = "general.ledger.report.wizard"
    _description = "General Ledger Report Wizard"

    branch_id = fields.Many2one(
        comodel_name='res.branch',
        string='Branch'
    )
    

    show_warehouse = fields.Boolean(
        string='Агуулах харуулах?', default=False
    )    

    def _prepare_report_general_ledger(self):
        result = super(GeneralLedgerReportWizard, self)._prepare_report_general_ledger()
        result.update({'branch_id':self.branch_id and self.branch_id.id or False})
        result.update({'show_warehouse':self.show_warehouse})
        return result

#     @api.onchange('company_id')
#     def onchange_company_id(self):
#         """Handle company change."""
#         # account_type = self.env.ref('account.data_unaffected_earnings')
#         earning_accounts=self.search([('account_type','=','equity_unaffected'),('company_id','=',company_id)])
#         count = self.env['account.account'].search_count(
#             [
#                 ('user_type_id', '=', account_type.id),
#                 ('company_id', '=', self.company_id.id)
#             ])
#         self.not_only_one_unaffected_earnings_account = count != 1
#         if self.company_id and self.date_range_id.company_id and \
#                 self.date_range_id.company_id != self.company_id:
#             self.date_range_id = False
#         if self.company_id and self.account_journal_ids:
#             self.account_journal_ids = self.account_journal_ids.filtered(
#                 lambda p: p.company_id == self.company_id or
#                 not p.company_id)
#         if self.company_id and self.partner_ids:
#             self.partner_ids = self.partner_ids.filtered(
#                 lambda p: p.company_id == self.company_id or
#                 not p.company_id)
#         if self.company_id and self.account_ids:
#             if self.receivable_accounts_only or self.payable_accounts_only:
#                 self.onchange_type_accounts_only()
#             else:
#                 self.account_ids = self.account_ids.filtered(
#                     lambda a: a.company_id == self.company_id)
#         if self.company_id and self.cost_center_ids:
#             self.cost_center_ids = self.cost_center_ids.filtered(
#                 lambda c: c.company_id == self.company_id)
#         res = {'domain': {'account_ids': [],
#                           'partner_ids': [],
#                           'account_journal_ids': [],
#                           'cost_center_ids': [],
#                           'date_range_id': []
#                           }
#                }
#
# #         action = self.env.ref(
# #             'mw_report_branch.action_general_ledger_sale_wizard')
# #         action_data = action.read()[0]
# #         context1 = action_data.get('context', {})
# #         context1 = safe_eval(context1)
#         context1=self._context
#         print ('context1 ',context1)
#         if context1.get('from_sale',False):
#             res['domain']['account_ids'] += [
#                 ('user_type_id.type', 'in', ('receivable', 'payable'))]
#             return res
#         if not self.company_id:
#             return res
#         else:
#             res['domain']['account_ids'] += [
#                 ('company_id', '=', self.company_id.id)]
#             res['domain']['account_journal_ids'] += [
#                 ('company_id', '=', self.company_id.id)]
#             res['domain']['partner_ids'] += self._get_partner_ids_domain()
#             res['domain']['cost_center_ids'] += [
#                 ('company_id', '=', self.company_id.id)]
#             res['domain']['date_range_id'] += [
#                 '|', ('company_id', '=', self.company_id.id),
#                 ('company_id', '=', False)]
#
#         return res