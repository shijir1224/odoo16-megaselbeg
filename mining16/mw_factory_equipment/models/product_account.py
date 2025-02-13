# -*- coding: utf-8 -*-

import time
import math

import logging
_logger = logging.getLogger(__name__)

import re
from odoo import api, fields, models, _
from odoo.osv import expression
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


class AccountAnalytic(models.Model):
    _inherit = "account.analytic.create"
    
    def stock_analytic_distribution(self,stock_move):
        analytic_distribution = False
        technic_id=False
        equipment_id=False
        component_id=False
        branch_id=False
        # print ('check_account ',check_account)
        hr_company_id=False
        branch_id=stock_move.location_id.set_warehouse_id.branch_id
        if stock_move.picking_id.other_expense_id:
            account_id=False
            # if stock_move.picking_id.other_expense_id.branch_id:
            #     branch_id=stock_move.picking_id.other_expense_id.branch_id
            # if stock_move.expense_line_id and stock_move.expense_line_id.account_id:
            #     debit_account_id = stock_move.expense_line_id.account_id.id
            if stock_move.expense_line_id and stock_move.expense_line_id.analytic_distribution:
                analytic_distribution = stock_move.expense_line_id.analytic_distribution
            elif stock_move.picking_id.other_expense_id.analytic_distribution and not analytic_distribution:
                analytic_distribution = stock_move.picking_id.other_expense_id.analytic_distribution
            elif stock_move.picking_id.other_expense_id.transaction_value_id and stock_move.picking_id.other_expense_id.transaction_value_id.analytic_distribution and not analytic_distribution:
                analytic_distribution = stock_move.picking_id.other_expense_id.transaction_value_id.analytic_distribution
            elif stock_move.picking_id.other_expense_id.technic_id and not analytic_distribution:
                accounts_data = stock_move.product_id.product_tmpl_id.get_product_expense_accounts(technic=stock_move.picking_id.other_expense_id.technic_id,branch_id=branch_id, source=self)
                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
            elif not account_id and not analytic_distribution:
                accounts_data = stock_move.product_id.product_tmpl_id.get_product_expense_accounts(other_expense_id=stock_move.picking_id.other_expense_id,branch_id=branch_id, source=self)
                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']

            # elif stock_move.picking_id.other_expense_id.transaction_value_id and stock_move.picking_id.other_expense_id.transaction_value_id.account_id:
            #     account_id = stock_move.picking_id.other_expense_id.transaction_value_id.account_id.id
            # debit_account_id=account_id
        elif stock_move.picking_id.oil_fuel_id:
            print('come oon')
        elif stock_move.component_id and not analytic_distribution:#and stock_move.technic_id.account_id and stock_move.technic_id.account_analytic_id:
            component_id=stock_move.component_id.id
            if stock_move.technic_id:
                technic_id = stock_move.technic_id.id
            accounts_data = stock_move.product_id.product_tmpl_id.get_product_expense_accounts(technic=stock_move.technic_id,component_id=stock_move.component_id,branch_id=branch_id, source=self)
            debit_account_id = accounts_data['expense_account']
            analytic_account_id = accounts_data['account_analytic_id']
            analytic_distribution = accounts_data['analytic_distribution']
        elif stock_move.technic_id and not analytic_distribution:
            technic_id=stock_move.technic_id.id
            accounts_data = stock_move.product_id.product_tmpl_id.get_product_expense_accounts(technic=stock_move.technic_id,branch_id=branch_id, source=self)
            debit_account_id = accounts_data['expense_account']
            analytic_account_id = accounts_data['account_analytic_id']
            analytic_distribution = accounts_data['analytic_distribution']
        elif stock_move.equipment_id and not analytic_distribution:
            equipment_id=stock_move.equipment_id.id
            accounts_data = stock_move.product_id.product_tmpl_id.get_product_expense_accounts(equipment=stock_move.equipment_id,branch_id=branch_id, source=self)
            debit_account_id = accounts_data['expense_account']
            analytic_account_id = accounts_data['account_analytic_id']
            analytic_distribution = accounts_data['analytic_distribution']

        elif not (stock_move.picking_id and stock_move.picking_id.sale_id) and not \
                (stock_move.location_dest_id.usage in ('inventory') or stock_move.location_id.usage in ('inventory')) and not analytic_distribution:
            # (stock_move.location_dest_id.usage in ('production', 'inventory') or stock_move.location_id.usage in ('production', 'inventory'))
            accounts_data = stock_move.product_id.product_tmpl_id.get_product_expense_accounts(branch_id=branch_id, source=self)

            debit_account_id = accounts_data['expense_account']
            analytic_account_id = accounts_data['account_analytic_id']
            analytic_distribution = accounts_data['analytic_distribution']
            
        # print ('analytic_distribution123 ',analytic_distribution)
        return analytic_distribution   
                
    def _find_analytic_distribution(self,line):
        if line.move_id.stock_move_id:
            return self.stock_analytic_distribution(line.move_id.stock_move_id)
        elif line.display_type == 'product' and line.move_id.is_invoice(include_receipts=True) and line.move_id.stock_warehouse_id.analytic_distribution:
            return line.move_id.stock_warehouse_id.analytic_distribution
        
        return False
        
        
class ProductAccountConfig(models.Model):
    _inherit = "product.account.config"

    equipment_ids = fields.Many2many('factory.equipment','config_factory_equipment_rel','config_id','equipment_id','Equipment')
    depend_equipment = fields.Boolean('Depend equipment')

    department_ids = fields.Many2many('hr.department','product_conf_department_rel','config_id','def_id','Department')
    depend_department = fields.Boolean('Depend department')
    
    @api.constrains('equipment_ids','category_ids')
    def _check_equipment_lines(self):
        wh_ids = self.equipment_ids.sorted()
        for wh in wh_ids:
            query = """
                    select c.id from product_account_config c \
                        left join config_factory_equipment_rel r on c.id=r.config_id \
                        where r.equipment_id={0} and category_id in ({1})
                """.format(wh.id, ','.join(map(str, self.category_ids.ids)))
#             print 'query ',query
            self.env.cr.execute(query)
            ids = self.env.cr.dictfetchall()
            if len(ids)>1:
                raise ValidationError((u' Тухайн тоног төхөөрөмжийн тохиргоо хийгдсэн байна. {0}'.format(wh.name)))

#     @api.onchange('equipment_ids')
#     def onchange_equipment_ids(self):
#         name=''
#         if self.category_ids:
#             for category_ids in self.category_ids:
#                 name+=' ['+category_ids.name +']'
# #             name+=self.category_id.name
#         for w in self.equipment_ids:
#             name+=' ['+w.name +']'
#         self.name=name

#----------------------------------------------------------
# Products
#----------------------------------------------------------
class ProductTemplate(models.Model):

    _inherit = "product.template"

#     categ_id = fields.Many2one('product.category','Internal Category', required=True, change_default=True, domain="[('type','=','normal')]" ,help="Select category for the current product", default=False)

    def get_product_expense_accounts(self, fiscal_pos=None, technic=None, equipment=None,component_id=None,other_expense_id=None,branch_id=None,company_id=None, source=None):
        categ_id=self.categ_id
        conf_pool=self.env['product.account.config']
        account_id=False
        categ_pool=self.env['product.category']
        origin_text = '' if not source else ' {0}'.format(source)
        # print (a)
        if not company_id:
            company_id=self.env.user.company_id.id
        if technic:# and categ_id.id!=56:
            if branch_id:
                query = """
                    select c.id from product_account_config c
                        left join config_technic_equipment_rel r on c.id=r.config_id
                        left join config_category_rel cr on cr.config_id=c.id
                        left join config_product_branch_rel br on br.config_id=c.id
                        where r.technic_id={0} and cr.category_id={1}  and br.branch_id={2} and c.company_id={3}
                """.format(technic.id,categ_id.id,branch_id.id,company_id)
            else:
                query = """
                    select c.id from product_account_config c
                        left join config_technic_equipment_rel r on c.id=r.config_id
                        left join config_category_rel cr on cr.config_id=c.id
                        where r.technic_id={0} and cr.category_id={1}  and c.company_id={2}
                """.format(technic.id,categ_id.id,company_id)
            print ('query ',query)
            self.env.cr.execute(query)
            conf_ids = self.env.cr.fetchall()
            if not conf_ids:
                if branch_id:
                    print('****************************************** ',branch_id.name)
                    raise UserError((u' {0} техникийн тохиргоо {1} салбар {2} ангилал дээр дансны тохиргоо хийгдээгүй байна!!! Нягтланд хандана уу.'.format(technic.name,\
                                                                                                                     branch_id.name,categ_id.name)+origin_text))
                else:
                    raise UserError((u' {0} техникийн тохиргоо {1} ангилал дээр дансны тохиргоо хийгдээгүй байна!!! Нягтланд хандана уу.'.format(technic.name,\
                                                                                                                     categ_id.name)+origin_text))

            # elif len(conf_ids)>1:
            #     raise UserError((u' {0} техникийн тохиргоо {1} ангилал дээр олон тохиргоо хийгдсэн байна!!! Нягтланд хандана уу.'.format(technic.name,\
            #                                                                                                          categ_id.name)))

            conf=conf_pool.browse(conf_ids[0])
            # analytic_id=conf.account_analytic_id and conf.account_analytic_id.id or False
            analytic_id=False
            analytic_distribution = conf.analytic_distribution and conf.analytic_distribution or False
            accounts = {'account_analytic_id':analytic_id,
                        'analytic_distribution':analytic_distribution,
                        'expense_account':conf.account_id.id,
                       }            
            _logger.info(u'get_product_accounts with equipment accounts-------------3%s !'%(accounts))
            if not fiscal_pos:
                fiscal_pos = self.env['account.fiscal.position']
            # acc=fiscal_pos.map_accounts(accounts)
            return accounts
        elif equipment:
            if branch_id:
                query = """
                    select c.id from product_account_config c
                        left join config_factory_equipment_rel r on c.id=r.config_id
                        left join config_category_rel cr on cr.config_id=c.id
                        left join config_product_branch_rel br on br.config_id=c.id
                        where r.equipment_id={0} and cr.category_id={1}  and br.branch_id={2}   and c.company_id={3}
                """.format(equipment.id,categ_id.id,branch_id.id,company_id)
            else:
                query = """
                    select c.id from product_account_config c
                        left join config_factory_equipment_rel r on c.id=r.config_id
                        left join config_category_rel cr on cr.config_id=c.id
                        where r.equipment_id={0} and cr.category_id={1}   and c.company_id={2}
                """.format(equipment.id,categ_id.id,company_id)
            print ('query ',query)
            self.env.cr.execute(query)
            conf_ids = self.env.cr.fetchall()
            if not conf_ids:
                if branch_id:
                    print('****************************************** ',branch_id.name)
                    raise UserError((u' {0} тоног төхөөрөмжийн тохиргоо {1} салбар {2} ангилал дээр дансны тохиргоо хийгдээгүй байна!!! Нягтланд хандана уу.'.format(equipment.name,\
                                                                                                                     branch_id.name,categ_id.name)+origin_text))
                else:
                    raise UserError((u' {0} тоног төхөөрөмжийн тохиргоо {1} ангилал дээр дансны тохиргоо хийгдээгүй байна!!! Нягтланд хандана уу.'.format(equipment.name,\
                                                                                                                     categ_id.name)+origin_text))

            # elif len(conf_ids)>1:
            #     raise UserError((u' {0} тоног төхөөрөмжийн тохиргоо {1} ангилал дээр олон тохиргоо хийгдсэн байна!!! Нягтланд хандана уу.'.format(equipment.name,\
            #                                                                                                          categ_id.name)))

            conf=conf_pool.browse(conf_ids[0])
            # analytic_id=conf.account_analytic_id and conf.account_analytic_id.id or False
            analytic_id=False
            analytic_distribution = conf.analytic_distribution and conf.analytic_distribution or False
            accounts = {'account_analytic_id':analytic_id,
                        'analytic_distribution':analytic_distribution,
                        'expense_account':conf.account_id.id,
                       }            
            _logger.info(u'get_product_accounts with equipment accounts-------------3%s !'%(accounts))
            if not fiscal_pos:
                fiscal_pos = self.env['account.fiscal.position']
            # acc=fiscal_pos.map_accounts(accounts)
            return accounts
        else:
            if branch_id:
                query = """
                    select c.id from product_account_config c
                                left join config_category_rel cr on cr.config_id=c.id
                                left join config_product_branch_rel br on br.config_id=c.id
                        where  cr.category_id={0} and id not in (select config_id from config_technic_equipment_rel) and  br.branch_id={1}  and c.company_id={2}
                """.format(categ_id.id,branch_id.id,company_id)
            else:
                query = """
                    select c.id from product_account_config c
                                left join config_category_rel cr on cr.config_id=c.id
                        where  cr.category_id={0} and id not in (select config_id from config_technic_equipment_rel)  and c.company_id={1}
                """.format(categ_id.id,company_id)

            self.env.cr.execute(query)
            conf_ids = self.env.cr.fetchall()
            if not conf_ids:
                if branch_id:
                    # print (branch_id)
                    # print (a)
                    raise UserError((u' {0} ангилал дээр {1} салбар дээр дансны тохиргоо хийгдээгүй байна!!! Нягтланд хандана уу.'.format(
                                                                                                                     categ_id.name,branch_id.name)+origin_text))
                else:
                    raise UserError((u' {0} ангилал дээр дансны тохиргоо хийгдээгүй байна!!! Нягтланд хандана уу.'.format(
                                                                                                                     categ_id.name)+origin_text))
            # elif len(conf_ids)>1:
            #     raise UserError((u' {0} ангилал дээр олон тохиргоо хийгдсэн байна!!! Нягтланд хандана уу.'.format(categ_id.name)))

            conf=conf_pool.browse(conf_ids[0])
            _logger.info(u'get_product_accounts categ_id-------------{0}, qq {1} conf {2} !'.format(str(categ_id.id),query,conf))
            
            analytic_id=False
            analytic_distribution = conf.analytic_distribution and conf.analytic_distribution or False
            accounts = {'account_analytic_id':analytic_id,
                        'analytic_distribution':analytic_distribution,
                        'expense_account':conf.account_id.id,
                       }            
            _logger.info(u'get_product_accounts accounts without technic-------------3%s !'%(accounts))
            if not fiscal_pos:
                fiscal_pos = self.env['account.fiscal.position']
            # acc=fiscal_pos.map_accounts(accounts)
            return accounts

class StockMove(models.Model):
    _inherit = "stock.move"

    def _account_entry_move(self, qty, description, svl_id, cost):
        """ Accounting Valuation Entries 
          is_expense=True """
        self.ensure_one()
        am_vals = []
        if self.product_id.type != 'product':
            # no stock valuation for consumable products
            return am_vals
        # if self.restrict_partner_id and self.restrict_partner_id != self.company_id.partner_id: # bainga uuseh tailbar bolgov
        #     # if the move isn't owned by the company, we don't make any valuation
        #     return am_vals

        company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
        company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False
        print ('company_from ',company_from)
        print ('company_to ',company_to)

        journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            if self._is_returned(valued_type='in'):
                am_vals.append(self.with_company(company_to).with_context(is_returned=True)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
            else:
                am_vals.append(self.with_company(company_to)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))

        # Create Journal Entry for products leaving the company
        if self._is_out():
            cost = -1 * cost
            if self._is_returned(valued_type='out'):
                am_vals.append(self.with_company(company_from).with_context(is_returned=True)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
            else:
                am_vals.append(self.with_company(company_from).with_context(is_expense=True)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))

        if self.company_id.anglo_saxon_accounting:
            # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
            if self._is_dropshipped():
                if cost > 0:
                    am_vals.append(self.with_company(self.company_id)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))
                else:
                    cost = -1 * cost
                    am_vals.append(self.with_company(self.company_id)._prepare_account_move_vals(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost))
            elif self._is_dropshipped_returned():
                if cost > 0:
                    am_vals.append(self.with_company(self.company_id).with_context(is_returned=True)._prepare_account_move_vals(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost))
                else:
                    cost = -1 * cost
                    am_vals.append(self.with_company(self.company_id).with_context(is_returned=True)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))

        return am_vals

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description):
        """ Overridden from stock_account to support amount_currency on valuation lines generated from po
        """
        self.ensure_one()
        
        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description)  
        is_expense =False
        is_in_return=False
        is_return=False
        check_account=False
        if self._context.get('is_expense'):
            is_expense = True
        if self._context.get('is_in_return'):
            is_in_return = True
        in_ret=self._is_returned(valued_type='out')
        # print ('in_ret123 ',in_ret)
        # print ('1231231 ',self._context.get('is_returned'))
        if self._context.get('is_returned') and not in_ret:
            is_return = True
        #Борлуулалтын буцаалт бол КООР
        if self._context.get('is_returned'):
            if self._is_in():
                if self._is_returned(valued_type='in'):
                    return rslt
        check_account=True
        if self._context.get('check_account'):
            check_account = False
        if self._context.get('active_model','')=='mrp.production':
            check_account = False
        
        analytic_account_id=False
        analytic_distribution = False
        technic_id=False
        equipment_id=False
        component_id=False
        branch_id=False
        # print ('is_returnis_returnis_returnis_returnis_returnis_return12312 ',is_return)
        if is_expense and check_account:
            hr_company_id=False
            branch_id=self.location_id.set_warehouse_id.branch_id
            if hasattr(self, 'oil_line_id') and self.oil_line_id and hasattr(self.oil_line_id, 'branch_id'):  
                branch_id = (self.oil_line_id.branch_id and self.oil_line_id.branch_id) or  (self.oil_line_id.parent_id.branch_id) 
                _logger.info(u'get_product_accounts accounts- branch_id+++++--------\n\n\n s ====branch_id %s !'%(branch_id))
                if self.technic_id:
                    technic_id=self.technic_id.id
                    accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
                    debit_account_id = accounts_data['expense_account']
                    analytic_account_id = accounts_data['account_analytic_id']
                    analytic_distribution = accounts_data['analytic_distribution']
                    print('*****************************************88')
                elif self.equipment_id:
                    equipment_id=self.equipment_id.id
                    accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(equipment=self.equipment_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
                    debit_account_id = accounts_data['expense_account']
                    analytic_account_id = accounts_data['account_analytic_id']
                    analytic_distribution = accounts_data['analytic_distribution']
                    print('@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@222')

            elif self.picking_id.other_expense_id:
                account_id=False
                if self.picking_id.other_expense_id.branch_id:
                    branch_id=self.picking_id.other_expense_id.branch_id
                if self.expense_line_id and self.expense_line_id.account_id:
                    debit_account_id = self.expense_line_id.account_id.id
                elif self.picking_id.other_expense_id.technic_id:
                    accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.picking_id.other_expense_id.technic_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
                    debit_account_id = accounts_data['expense_account']
                    analytic_account_id = accounts_data['account_analytic_id']
                    analytic_distribution = accounts_data['analytic_distribution']
                    print('33333333333333##########################################')
                elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.account_id:
                    debit_account_id = self.picking_id.other_expense_id.transaction_value_id.account_id.id
                elif not account_id:
                    accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(other_expense_id=self.picking_id.other_expense_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
                    debit_account_id = accounts_data['expense_account']
                    analytic_account_id = accounts_data['account_analytic_id']
                    analytic_distribution = accounts_data['analytic_distribution']
                    # print('\n\n\nfound you!!!', accounts_data, accounts_data['analytic_distribution'])
                elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.account_id:
                    account_id = self.picking_id.other_expense_id.transaction_value_id.account_id.id
                # debit_account_id=account_id
            # elif self.picking_id.oil_fuel_id:
            #     print('come oon')
            elif self.component_id:#and self.technic_id.account_id and self.technic_id.account_analytic_id:
                component_id=self.component_id.id
                if self.technic_id:
                    technic_id = self.technic_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,component_id=self.component_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
                print('-1--2-1-2-1-2-1-112-1--2-21-1')
            elif self.technic_id:
                technic_id=self.technic_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
                print('22222222222222222222222222222222222')
            elif self.equipment_id:
                equipment_id=self.equipment_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(equipment=self.equipment_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
                print('1111111111111111111111111111111')

            elif not (self.picking_id and self.picking_id.sale_id) and not \
                    (self.picking_id and self.picking_id.picking_type_id and self.picking_id.picking_type_id.sequence_code=='POS') and not \
                    (self.location_dest_id.usage in ('inventory') or self.location_id.usage in ('inventory')):
                # print ('self.picking_id.pos_order_id123 ',self.picking_id.pos_order_id)
                # (self.location_dest_id.usage in ('production', 'inventory') or self.location_id.usage in ('production', 'inventory'))
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(branch_id=branch_id,company_id=self.company_id.id, source=self)

                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
                print('noonono no no n o no n on o n: ', accounts_data)
            if self.picking_id.sale_id and self.picking_id.sale_id.warehouse_id\
                    and self.picking_id.sale_id.warehouse_id.is_bbo and self.picking_id.sale_id.warehouse_id.bbo_account_id:
                debit_account_id=self.picking_id.sale_id.warehouse_id.bbo_account_id.id
            if self.picking_id.maintenance_workorder_id and self.picking_id.maintenance_workorder_id.branch_id:
                branch_id=self.picking_id.maintenance_workorder_id.branch_id
                
            if not technic_id and self.technic_id:
                technic_id= self.technic_id.id
            if not equipment_id and self.equipment_id:
                equipment_id= self.equipment_id.id
        if is_return:
            #Анхны дансруу буцаах, техник сонгох
            hr_company_id=False

            if self.component_id:#and self.technic_id.account_id and self.technic_id.account_analytic_id:
                component_id=self.component_id.id
                if self.technic_id:
                    technic_id = self.technic_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,component_id=self.component_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
    #             print 'accounts_data ',accounts_data
                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
                print('333333333333333333333')
            elif self.technic_id:
                technic_id=self.technic_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
    #             print 'accounts_data ',accounts_data
                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                print('4444444444444444444')
            elif self.equipment_id:
                equipment_id=self.equipment_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(equipment=self.equipment_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
    #             print 'accounts_data ',accounts_data
                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
                print('55555555555555555555555')
            elif self.picking_id.other_expense_id:
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(other_expense_id=self.picking_id.other_expense_id,branch_id=branch_id,company_id=self.company_id.id, source=self)
                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
                print('self.picking_id.other_expense_id: ', analytic_distribution)
            elif self.picking_id.sale_id and self.picking_id.sale_id.warehouse_id\
                    and self.picking_id.sale_id.warehouse_id.is_bbo and self.picking_id.sale_id.warehouse_id.bbo_account_id:
                debit_account_id=self.picking_id.sale_id.warehouse_id.bbo_account_id.id
            else:
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(branch_id=branch_id,company_id=self.company_id.id, source=self)
                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
                print('elseeeeeee: ', analytic_distribution)
        _logger.info(u'get_product_accounts accounts- technic_id OR equipment_id+++++------------%s ====debit_account_id %s !'%(technic_id or equipment_id,debit_account_id))
        # print (a)
        rslt['debit_line_vals']['account_id'] = debit_account_id
        rslt['credit_line_vals']['account_id'] = credit_account_id

        rslt['credit_line_vals']['technic_id'] = technic_id
        rslt['credit_line_vals']['component_id'] = component_id
        rslt['credit_line_vals']['equipment_id'] = equipment_id
        # if analytic_account_id:
        #     rslt['credit_line_vals']['analytic_account_id'] = analytic_account_id
        if analytic_distribution:
            rslt['debit_line_vals']['analytic_distribution'] = analytic_distribution
            print('finaaaaaal: ', analytic_distribution, rslt)
        if branch_id:
            rslt['credit_line_vals']['branch_id'] = branch_id.id
            rslt['debit_line_vals']['branch_id'] = branch_id.id

        rslt['debit_line_vals']['technic_id'] = technic_id
        rslt['debit_line_vals']['component_id'] = component_id
        rslt['debit_line_vals']['equipment_id'] = equipment_id
        print('mw_factory_equipment\n\n', rslt)
        return rslt
