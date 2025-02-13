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


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_bbo = fields.Boolean(u'Агуулахаас ББӨ данс авах',default=False)
    bo_account_id = fields.Many2one('account.account', u'БО данс')
    bbo_account_id = fields.Many2one('account.account', u'ББӨ данс')


class ProductAccountConfig(models.Model):
    _name = "product.account.config"
    _inherit = 'analytic.mixin'    
    
    name = fields.Char(required=True)

#     product_account_id = fields.Many2one('account.account', 'Product account', ondelete='cascade', domain=[('type','!=','view')])
#     expense_account_id = fields.Many2one('account.account', 'Expense account', ondelete='cascade')
#     income_account_id = fields.Many2one('account.account', 'Income account', ondelete='cascade', domain=[('type','!=','view')])
#     journal_id = fields.Many2one('account.journal', 'Journal', ondelete='cascade')

    account_id = fields.Many2one('account.account', 'Expense Account', copy=False,)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic account', copy=False,)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic account', copy=False,)
    technic_ids = fields.Many2many('technic.equipment','config_technic_equipment_rel','config_id','technic_id','Technic')
    category_id = fields.Many2one('product.category', 'Category', ondelete='cascade')#, domain=[('is_account','=',True)]
    category_ids = fields.Many2many('product.category','config_category_rel','config_id','category_id','Category')
#     company_ids = fields.Many2many('hr.company','config_company_equipment_rel','config_id','company_id','Company')

    depend_technic = fields.Boolean('Depend technic')
    depend_company = fields.Boolean('Depend company')

    is_branch = fields.Boolean('Branch?')
    branch_ids = fields.Many2many('res.branch','config_product_branch_rel','config_id','branch_id','Branch')

    company_id = fields.Many2one('res.company', string='Company', 
        default=lambda self: self.env.company)


    @api.constrains('technic_ids','category_ids')
    def _check_lines(self):
        wh_ids = self.technic_ids.sorted()
        for wh in wh_ids:
            query = """
                    select c.id from product_account_config c \
                        left join config_technic_equipment_rel r on c.id=r.config_id \
                        where r.technic_id={0} and category_id in ({1})
                """.format(wh.id, ','.join(map(str, self.category_ids.ids)))
#             print 'query ',query
            self.env.cr.execute(query)
            ids = self.env.cr.dictfetchall()
            if len(ids)>1:
                raise ValidationError((u' Тухайн техникийн тохиргоо хийгдсэн байна. {0}'.format(wh.name)))

#     @api.onchange('category_ids')
#     def onchange_category_id(self):
#         name=''
#         if self.category_ids:
#             for category_ids in self.category_ids:
#                 name+=' ['+category_ids.name +']'
# #             name+=self.category_id.name
#         for w in self.technic_ids:
# #             if self.name:
#             name+=' ['+w.name +']'
#         self.name=name
	# Устгахгүй
    def unlink(self):
        for move in self:
            if not self.env.user.has_group('mw_product_warehouse_account.group_remove_product_account'):
                raise UserError(u'({0}) Данс устгах эрхгүй байна. Эрх бүхий нягтланд хандана уу'.format( move.name))
        return super().unlink()
#     @api.onchange('technic_ids')
#     def onchange_technic_ids(self):
#         name=''
#         if self.category_ids:
#             for category_ids in self.category_ids:
#                 name+=' ['+category_ids.name +']'
# #             name+=self.category_id.name
#         for w in self.technic_ids:
#             name+=' ['+w.name +']'
#         self.name=name

# class ProductCategory(models.Model):
#     _inherit = 'product.category'
#
#     is_account = fields.Boolean('Is account',)

#----------------------------------------------------------
# Products
#----------------------------------------------------------
class ProductTemplate(models.Model):

    _inherit = "product.template"

#     categ_id = fields.Many2one('product.category','Internal Category', required=True, change_default=True, domain="[('type','=','normal')]" ,help="Select category for the current product", default=False)

    def get_product_expense_accounts(self, fiscal_pos=None, technic=None,component_id=None,other_expense_id=None,branch_id=None, source=None):
        categ_id=self.categ_id
        conf_pool=self.env['product.account.config']
        account_id=False
        categ_pool=self.env['product.category']
        origin_text = '' if not source else ' {0}'.format(source)
#         if not categ_id:
#             raise UserError((u' {0} нэртэй {1} кодтой бараа {2} гэсэн буруу ангилалд байна!!!.'.format(self.name,self.default_code,self.categ_id.name)))
        print ('branch_id ',branch_id)
#         if component_id:
#             analytic_id=False
#             if technic:
#                 technic=technic
#             elif component_id.current_technic_id:
#                 technic=component_id.current_technic_id
#             if technic :
#                 if technic.department_id:
#                     if technic.department_id.analytic_account_id:
#                         analytic_id = technic.department_id.analytic_account_id.id
#                     else:
#                         raise UserError((u' {0} Хэлтэс дээр шинжилгээний данс сонгоогүй байна!!! Нягтланд хандана уу.'.format(technic.department_id.name)))
#                 else:
#                     raise UserError((u' {0} Техник дээр хэлтэс сонгоогүй байна!!! Нягтланд хандана уу.'.format(technic.name)))
#     #         accounts.update({'stock_journal': self.categ_id.property_stock_journal or False})
#             if not component_id.account_id:
#                 raise UserError((u' {0} Компонэнт дээр зардлын данс сонгоогүй!!! Нягтланд хандана уу.'.format(component_id.name)))
#             accounts = {'account_analytic_id':analytic_id,
# #                         'expense_account':conf.account_id.id,
#                         'expense_account':component_id.account_id.id,
#                        }
#             _logger.info(u'get_product_accounts accounts-------------3%s !'%(accounts))
#             if not fiscal_pos:
#                 fiscal_pos = self.env['account.fiscal.position']
#             acc=fiscal_pos.map_accounts(accounts)
#             return acc
        if technic:# and categ_id.id!=56:
            if branch_id:
                query = """
                    select c.id from product_account_config c
                        left join config_technic_equipment_rel r on c.id=r.config_id
                        left join config_category_rel cr on cr.config_id=c.id
                        left join config_product_branch_rel br on br.config_id=c.id
                        where r.technic_id={0} and cr.category_id={1}  and br.branch_id={2}
                """.format(technic.id,categ_id.id,branch_id.id)
            else:
                query = """
                    select c.id from product_account_config c
                        left join config_technic_equipment_rel r on c.id=r.config_id
                        left join config_category_rel cr on cr.config_id=c.id
                        where r.technic_id={0} and cr.category_id={1}
                """.format(technic.id,categ_id.id)
            print ('query ',query)
            self.env.cr.execute(query)
            conf_ids = self.env.cr.fetchall()
#             print 'conf_ids ',conf_ids
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
            # if technic.department_id:
            #     if technic.department_id.analytic_account_id:
            #         analytic_id = technic.department_id.analytic_account_id.id
            #     else:
            #         raise UserError((u' {0} Хэлтэс дээр шинжилгээний данс сонгоогүй байна!!! Нягтланд хандана уу.'.format(technic.department_id.name)))
            # else:
            #     raise UserError((u' {0} Техник дээр хэлтэс сонгоогүй байна!!! Нягтланд хандана уу.'.format(technic.name)))
    #         accounts.update({'stock_journal': self.categ_id.property_stock_journal or False})
            accounts = {'account_analytic_id':analytic_id,
                        'analytic_distribution':analytic_distribution,
                        'expense_account':conf.account_id.id,
#                         'income_account':conf.income_account_id,
#                         'journal':conf.journal_id,
                       }
            _logger.info(u'get_product_accounts with technic accounts-------------3%s !'%(accounts))
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
                        where  cr.category_id={0} and id not in (select config_id from config_technic_equipment_rel) and  br.branch_id={1}
                """.format(categ_id.id,branch_id.id)
            else:
                query = """
                    select c.id from product_account_config c
                                left join config_category_rel cr on cr.config_id=c.id
                        where  cr.category_id={0} and id not in (select config_id from config_technic_equipment_rel)
                """.format(categ_id.id)

#             print 'query ',query
            self.env.cr.execute(query)
            conf_ids = self.env.cr.fetchall()
#             print 'conf_ids ',conf_ids
            if not conf_ids:
                if branch_id:
                    raise UserError((u' {0} ангилал дээр {1} салбар дээр дансны тохиргоо хийгдээгүй байна!!! Нягтланд хандана уу.'.format(
                                                                                                                     categ_id.name,branch_id.name)+origin_text))
                else:
                    raise UserError((u' {0} ангилал дээр дансны тохиргоо хийгдээгүй байна!!! Нягтланд хандана уу.'.format(
                                                                                                                     categ_id.name)+origin_text))
            # elif len(conf_ids)>1:
            #     raise UserError((u' {0} ангилал дээр олон тохиргоо хийгдсэн байна!!! Нягтланд хандана уу.'.format(categ_id.name)))

            conf=conf_pool.browse(conf_ids[0])
            _logger.info(u'get_product_accounts categ_id-------------{0}, qq {1} conf {2} !'.format(str(categ_id.id),query,conf))
            
#             conf.account_analytic_id and conf.account_analytic_id.id or False
            analytic_id=False
            # analytic_id=conf.account_analytic_id and conf.account_analytic_id.id or False
            analytic_distribution = conf.analytic_distribution and conf.analytic_distribution or False
            
            # if other_expense_id:
            #     expense_line = self.env['stock.product.other.expense.line'].search([('parent_id', '=', other_expense_id.id)])
            #     if expense_line:
            #         for line in expense_line:
            #             product_all = line.filtered(lambda r: r.product_id.product_tmpl_id.id == self.id)
            #             account_id=line.account_id.id
            #     elif other_expense_id.account_id:
            #         account_id=other_expense_id.account_id.id
            #     elif other_expense_id.transaction_value_id and other_expense_id.transaction_value_id.account_id:
            #         account_id = other_expense_id.transaction_value_id.account_id.id

            #Техниктэй шаардахгүй АА бараа WO s үүссэн бол
            # if technic and technic.department_id and not analytic_id:
            #     if technic.department_id.analytic_account_id:
            #         analytic_id = technic.department_id.analytic_account_id.id
            #     else:
            #         raise UserError((u' {0} Хэлтэс дээр шинжилгээний данс сонгоогүй байна!!! Нягтланд хандана уу.'.format(technic.department_id.name)))

    #         accounts.update({'stock_journal': self.categ_id.property_stock_journal or False})
#             if not  analytic_id:
#                 if power_product_id and power_product_id.department_id:
#                     analytic_id=power_product_id.department_id.analytic_account_id and power_product_id.department_id.analytic_account_id.id or False
#                 elif conf:
#                     analytic_id=conf.account_analytic_id and conf.account_analytic_id.id or False
#             if power_product_id:
#                 conf=conf_pool.search([('is_power','=',True)],limit=1)
            print ('account_id ',account_id)
            accounts = {'account_analytic_id':analytic_id,
                        'analytic_distribution':analytic_distribution,
                        'expense_account': account_id and account_id or conf.account_id.id,
#                         'income_account':conf.income_account_id,
#                         'journal':conf.journal_id,
                       }
            
            _logger.info(u'get_product_accounts accounts without technic-------------3%s !'%(accounts))
            if not fiscal_pos:
                fiscal_pos = self.env['account.fiscal.position']
            # acc=fiscal_pos.map_accounts(accounts)
            return accounts

#             return {}



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

        journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
        # Create Journal Entry for products arriving in the company; in case of routes making the link between several
        # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
        if self._is_in():
            print ('111111111111111111 ret check')
            if self._is_returned(valued_type='in'):
                am_vals.append(self.with_company(company_to).with_context(is_returned=True)._prepare_account_move_vals(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost))
            else:
                am_vals.append(self.with_company(company_to)._prepare_account_move_vals(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost))

        # Create Journal Entry for products leaving the company
        if self._is_out():
            print ('1111111111111111112 ret check')
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
#     def _account_entry_move(self, qty, description, svl_id, cost):
#         """ Accounting Valuation Entries
#         is_expense=True """
#         self.ensure_one()
#         if self.product_id.type != 'product':#202208 uusehgui bolgov
# #         if self.product_id.type not in  ('product','consu'):
#
#             # no stock valuation for consumable products
#             return False
#         # sanhuu bichilt uusdeggui haav bayasaa
#         # if self.restrict_partner_id:
#         #     # if the move isn't owned by the company, we don't make any valuation
#         #     return False
#
#         location_from = self.location_id
#         location_to = self.location_dest_id
#         company_from = self._is_out() and self.mapped('move_line_ids.location_id.company_id') or False
#         company_to = self._is_in() and self.mapped('move_line_ids.location_dest_id.company_id') or False
#
#         # Create Journal Entry for products arriving in the company; in case of routes making the link between several
#         # warehouse of the same company, the transit location belongs to this company, so we don't need to create accounting entries
#         if self._is_in():
#             journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
#             if location_from and location_from.usage == 'customer':  # goods returned from customer
#                 self.with_context(force_company=company_to.id,is_in_return=True)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost)
#             else:
#                 self.with_context(force_company=company_to.id)._create_account_move_line(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost)
#
#         # Create Journal Entry for products leaving the company
#         if self._is_out():
#             cost = -1 * cost
#             journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
#             if location_to and location_to.usage == 'supplier':  # goods returned to supplier
#                 self.with_context(force_company=company_from.id)._create_account_move_line(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost)
#             else:
#                 self.with_context(force_company=company_from.id,is_expense=True)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost)
#
#         if self.company_id.anglo_saxon_accounting:
#             # Creates an account entry from stock_input to stock_output on a dropship move. https://github.com/odoo/odoo/issues/12687
#             journal_id, acc_src, acc_dest, acc_valuation = self._get_accounting_data_for_valuation()
#             if self._is_dropshipped():
#                 if cost > 0:
#                     self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_src, acc_valuation, journal_id, qty, description, svl_id, cost)
#                 else:
#                     cost = -1 * cost
#                     self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation, acc_dest, journal_id, qty, description, svl_id, cost)
#             elif self._is_dropshipped_returned():
#                 if cost > 0:
#                     self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_valuation, acc_src, journal_id, qty, description, svl_id, cost)
#                 else:
#                     cost = -1 * cost
#                     self.with_context(force_company=self.company_id.id)._create_account_move_line(acc_dest, acc_valuation, journal_id, qty, description, svl_id, cost)
#
#         if self.company_id.anglo_saxon_accounting:
#             #eventually reconcile together the invoice and valuation accounting entries on the stock interim accounts
#             self._get_related_invoices()._stock_account_anglo_saxon_reconcile_valuation(product=self.product_id)

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description):
        """ Overridden from stock_account to support amount_currency on valuation lines generated from po
        """
        self.ensure_one()

        rslt = super(StockMove, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, svl_id, description)  
        installed_factory = self.env['ir.module.module'].sudo().search([('state', '=', 'installed'),
                                                                        ('name', '=', 'mw_factory_equipment')])
        
        if len(installed_factory)>0:
            return rslt
        check_account=True
        if self._context.get('check_account'):
            check_account = False
        if self._context.get('active_model','')=='mrp.production':
            check_account = False
        is_expense =False
        is_in_return=False
        if self._context.get('is_expense'):
            is_expense = True
        if self._context.get('is_in_return'):
            is_in_return = True

        analytic_account_id=False
        analytic_distribution = False
        technic_id=False
        component_id=False
        branch_id=False
        print ('check_account ',check_account)
        print ('is_in_returnis_in_returnis_in_returnis_in_return`1`2`2`2 ',is_in_return)
        if is_expense and check_account:
            hr_company_id=False
            branch_id=self.location_id.set_warehouse_id.branch_id
            # if self.picking_id.other_expense_id and self.picking_id.other_expense_id.partner_id:
            #     hr_company_check = self.env['hr.company'].search([('partner_id','=',self.picking_id.other_expense_id.partner_id.id)], limit=1)
            #     if hr_company_check:
            #         hr_company_id=hr_company_check
            if self.picking_id.other_expense_id:
                account_id=False
                if self.picking_id.other_expense_id.branch_id:
                    branch_id=self.picking_id.other_expense_id.branch_id
                if self.expense_line_id and self.expense_line_id.account_id:
                    debit_account_id = self.expense_line_id.account_id.id
                # elif self.picking_id.other_expense_id.account_id:
                #     debit_account_id = self.picking_id.other_expense_id.account_id.id
                # if self.expense_line_id and self.expense_line_id.analytic_distribution:
                #     analytic_distribution = self.expense_line_id.analytic_distribution
                # elif self.picking_id.other_expense_id.analytic_distribution:
                #     analytic_distribution = self.picking_id.other_expense_id.analytic_distribution
                # elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.analytic_distribution:
                #     analytic_distribution = self.picking_id.other_expense_id.transaction_value_id.analytic_distribution.id
                elif self.picking_id.other_expense_id.technic_id:
                    accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.picking_id.other_expense_id.technic_id,branch_id=branch_id, source=self)
                    debit_account_id = accounts_data['expense_account']
                    analytic_account_id = accounts_data['account_analytic_id']
                    analytic_distribution = accounts_data['analytic_distribution']
                elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.account_id:
                    debit_account_id = self.picking_id.other_expense_id.transaction_value_id.account_id.id
                elif not account_id:
                    accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(other_expense_id=self.picking_id.other_expense_id,branch_id=branch_id, source=self)
                    debit_account_id = accounts_data['expense_account']
                    analytic_account_id = accounts_data['account_analytic_id']
                    analytic_distribution = accounts_data['analytic_distribution']


                elif self.picking_id.other_expense_id.transaction_value_id and self.picking_id.other_expense_id.transaction_value_id.account_id:
                    account_id = self.picking_id.other_expense_id.transaction_value_id.account_id.id
                # debit_account_id=account_id
            elif self.component_id:#and self.technic_id.account_id and self.technic_id.account_analytic_id:
                component_id=self.component_id.id
                if self.technic_id:
                    technic_id = self.technic_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,component_id=self.component_id,branch_id=branch_id, source=self)
                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']

            elif self.technic_id:
                technic_id=self.technic_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,branch_id=branch_id, source=self)
                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']

            elif not (self.picking_id and self.picking_id.sale_id) and not \
                    (self.location_dest_id.usage in ('inventory') or self.location_id.usage in ('inventory')):
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(branch_id=branch_id, source=self)

                debit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
            if not technic_id and self.technic_id:
                technic_id= self.technic_id.id
            if self.picking_id.sale_id and self.picking_id.sale_id.warehouse_id\
                    and self.picking_id.sale_id.warehouse_id.is_bbo and self.picking_id.sale_id.warehouse_id.bbo_account_id:
                debit_account_id=self.picking_id.sale_id.warehouse_id.bbo_account_id.id

            if self.sale_line_id:
                for items in self.sale_line_id:
                    if items.order_id and items.order_id.warehouse_id and items.order_id.warehouse_id.analytic_distribution:
                        rslt['debit_line_vals']['analytic_distribution'] =items.order_id.warehouse_id.analytic_distribution
                        rslt['credit_line_vals']['analytic_distribution'] =items.order_id.warehouse_id.analytic_distribution

#         if not dest_branch and self.technic_id.branch_id:
#             dest_branch  = self.technic_id.branch_id.id
#         analytic_account_id=5
        if is_in_return:
            #Анхны дансруу буцаах, техник сонгох
            hr_company_id=False
            # if self.picking_id.other_expense_id and self.picking_id.other_expense_id.partner_id:
            #     hr_company_check = self.env['hr.company'].search([('partner_id','=',self.picking_id.other_expense_id.partner_id.id)], limit=1)
            #     if hr_company_check:
            #         hr_company_id=hr_company_check

            if self.component_id:#and self.technic_id.account_id and self.technic_id.account_analytic_id:
                component_id=self.component_id.id
                if self.technic_id:
                    technic_id = self.technic_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,component_id=self.component_id,branch_id=branch_id, source=self)
    #             print 'accounts_data ',accounts_data
                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
            elif self.technic_id:
                technic_id=self.technic_id.id
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(technic=self.technic_id,branch_id=branch_id, source=self)
    #             print 'accounts_data ',accounts_data
                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']
    #             accounts = {'account_analytic_id':conf.account_analytic_id,
    #                         'expense_account':conf.account_id,

    #             analytic_account_id = self.technic_id.account_analytic_id.id
    #             debit_account_id = self.technic_id.account_id.id
            elif self.picking_id.other_expense_id:
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(other_expense_id=self.picking_id.other_expense_id,branch_id=branch_id, source=self)
                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']

#                 if self.picking_id.other_expense_id.account_id:
#                     debit_account_id=self.picking_id.other_expense_id.account_id.id
#                 if self.picking_id.other_expense_id.account_analytic_id:
#                     analytic_account_id = self.picking_id.other_expense_id.account_analytic_id.id
#                 if self.picking_id.other_expense_id.branch_id:
#                     dest_branch = self.picking_id.other_expense_id.branch_id.id
            else:
                accounts_data = self.product_id.product_tmpl_id.get_product_expense_accounts(branch_id=branch_id, source=self)

                credit_account_id = accounts_data['expense_account']
                analytic_account_id = accounts_data['account_analytic_id']
                analytic_distribution = accounts_data['analytic_distribution']

        _logger.info(u'get_product_accounts accounts- technic_idtechnic_id+++++------------%s ====debit_account_id %s !'%(technic_id,debit_account_id))
        rslt['debit_line_vals']['account_id'] = debit_account_id
        rslt['credit_line_vals']['account_id'] = credit_account_id

        rslt['credit_line_vals']['technic_id'] = technic_id
        rslt['credit_line_vals']['component_id'] = component_id
        # if analytic_account_id:
        #     rslt['credit_line_vals']['analytic_account_id'] = analytic_account_id
        if analytic_distribution:
            rslt['debit_line_vals']['analytic_distribution'] = analytic_distribution
        if branch_id:
            rslt['credit_line_vals']['branch_id'] = branch_id.id
            rslt['debit_line_vals']['branch_id'] = branch_id.id
        rslt['debit_line_vals']['technic_id'] = technic_id
        rslt['debit_line_vals']['component_id'] = component_id
        
        
        return rslt
