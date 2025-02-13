# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
from lxml import etree
import logging
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Account Entry"
    _order = 'date desc, id desc'



    def _post(self, soft=True):
    # def action_post(self):
        #inherit 
        for move in self:
            for line in move.line_ids:
                if line.account_id.check_balance:
                    this_amount=0
                    if line.account_id.account_type in ('asset_receivable','asset_cash','asset_current',\
                                                        'asset_non_current','asset_prepayments','asset_fixed',
                                                        'expense','expense_depreciation','expense_direct_cost'):
                        this_amount=line.credit
                        if line.partner_id and line.account_id.account_type in ('asset_receivable','liability_payable'):
                            self._cr.execute('select sum(debit-credit) as balance from account_move_line l \
                                                    left join account_move m on l.move_id=m.id \
                                                 where m.state=\'posted\' and l.partner_id={0} and account_id={1} '.format(line.partner_id.id,line.account_id.id))
                        else: 
                            self._cr.execute('select sum(debit-credit) as balance from account_move_line  l \
                                                    left join account_move m on l.move_id=m.id \
                                                 where m.state=\'posted\' and account_id={0} '.format(line.account_id.id))
                    else:
                        this_amount=line.debit
                        if line.partner_id and line.account_id.account_type in ('asset_receivable','liability_payable'):
                            self._cr.execute('select sum(credit-debit) as balance from account_move_line l \
                                                    left join account_move m on l.move_id=m.id \
                                                 where m.state=\'posted\' and l.partner_id={0} and account_id={1} '.format(line.partner_id.id,line.account_id.id))
                        else:
                            self._cr.execute('select sum(credit-debit) as balance from account_move_line l \
                                                    left join account_move m on l.move_id=m.id \
                                                 where m.state=\'posted\' and account_id={0} '.format(line.account_id.id))
                        
                    all_result = self._cr.fetchall()
                    # print ('allal_result ',all_result)
#                     print ('this_amount ',this_amount)

                    if all_result[0][0]:
                        if all_result[0][0]-float(this_amount)<0:
                            message = _(u"Үлдэгдэл шалгах данс дээр хасах үлдэгдэлтэй болох гээд байна {0} дүн {1}".format(line.account_id.code,str(all_result[0][0]-float(this_amount))))
                            raise UserError(message)
                if line.statement_line_id and line.statement_line_id.analytic_distribution and not line.analytic_distribution:
                    line.analytic_distribution= line.statement_line_id.analytic_distribution
                _logger.info('line.analytic_distribution %s'%(line.analytic_distribution))
                # print ('line.account_id.internal_type ',line.account_id.check_analytic)
                if line.account_id.check_analytic and not line.analytic_distribution:
#                    print (a)
                    message = _(u"Зардлын гүйлгээн шинжилгээний данс заавал сонгоно!!! %s") % (line.account_id.code)
                    raise UserError(message)
                if not line.account_id.check_analytic and line.analytic_distribution:
                    line.analytic_distribution=False
        res = super(AccountMove, self)._post(soft=soft)
        # res = super(AccountMove, self).action_post()
        return res
    

class AccountMoveLine(models.Model):
    _inherit  = 'account.move.line'

    def _prepare_analytic_distribution_line(self, distribution, account_id, distribution_on_each_plan):
        """ Prepare the values used to create() an account.analytic.line upon validation of an account.move.line having
            analytic tags with analytic distribution.
        """
        if self.account_id.create_analytic:
            res = super(AccountMoveLine, self)._prepare_analytic_distribution_line(distribution=distribution, account_id=account_id, distribution_on_each_plan=distribution_on_each_plan)
            return res
        else:
            return {'amount':0}
        

    def _create_analytic_lines(self):
        """ Create analytic items upon validation of an account.move.line having an analytic distribution.
        id буцаах
        """
        self._validate_analytic_distribution()
        analytic_line_vals = []
        for line in self:
            aa=line._prepare_analytic_lines()
            # print ('aa1231321 ',aa)
            analytic_line_vals.extend(aa)

        id=self.env['account.analytic.line'].create(analytic_line_vals)
        return id        
#     @api.model
#     def _get_aml_default_analytic_account(self):
#         user_pool = self.env['res.users']
#         user = user_pool.browse(self.env.uid)
# #         print ('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa')
#         _logger.info('user %s'%(user))
#         try:
#             analytic_account_id = (user.analytic_account_id and user.analytic_account_id.company_id.id == self.env.user.company_id.id and user.analytic_account_id.id)  or False
# #             analytic_account_id = user.analytic_account_id.id  or False
#         except Exception:
#             analytic_account_id=False

#         _logger.info('analytic_account_id %s'%(analytic_account_id))
        
#         return analytic_account_id

    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic account',default=_get_aml_default_analytic_account)
    
    # @api.depends('account_id', 'partner_id', 'product_id','branch_id','move_id.branch_id')
    # def _compute_analytic_distribution(self):
    #     for line in self:
    #         if line.display_type == 'product' or not line.move_id.is_invoice(include_receipts=True):
    #             distribution = self.env['account.analytic.distribution.model']._get_distribution({
    #                 "product_id": line.product_id.id,
    #                 "product_categ_id": line.product_id.categ_id.id,
    #                 "partner_id": line.partner_id.id,
    #                 "partner_category_id": line.partner_id.category_id.ids,
    #                 "account_prefix": line.account_id.code,
    #                 "company_id": line.company_id.id,
    #                 "branch_id":line.move_id.branch_id and line.move_id.branch_id.id or line.branch_id.id
    #             })
    #             line.analytic_distribution = distribution or line.analytic_distribution
    

class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    brand_id = fields.Many2one(related='move_line_id.brand_id', string='Brand', store=True)