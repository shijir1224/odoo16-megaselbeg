# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from odoo.exceptions import UserError, RedirectWarning, ValidationError

import time
from io import BytesIO
import xlsxwriter
from odoo.addons.account_financial_report.report.report_excel_cell_styles import ReportExcelCellStyles
import base64
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)

class AccountBudgetChange(models.Model):
    _name = "mw.account.budget.change"
    _description = "Budget period change"
#     _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char("Төсөв шилжүүлэх шалтгаан")
    note = fields.Char("Тэмдэглэл")


    budget_total = fields.Float(string='Нийт төсөв', store=True, 
        compute='_compute_amount_total')

    real_total = fields.Float(string='Нийт гүйцэтгэл', store=True, 
        compute='_compute_amount_total')
    
    @api.depends(
                'line_ids',
                'line_ids.budget_id',
                'line_ids.budget_id.budget_total',
                'line_ids.budget_id.real_total',
                    )
    def _compute_amount_total(self):
        for item in self:
            total_budget=0
            real_total=0
            for line in item.line_ids:
                if line.budget_id:
                    total_budget+=line.budget_id.budget_total
                    real_total += line.budget_id.real_total
            item.budget_total = total_budget
            item.real_total = real_total
#             item.balance=total_budget-real_total
            
#     def budget_domain(self):
#         search_domain=[]
#         budget_ids=[]
#         for rec in self:
#             if rec.to_dep_budget_id:
#                 for line in rec.to_dep_budget_id.line_ids:
#                     for p in line.period_line_ids:  
#                         budget_ids.append(p.id)
#         search_domain = [('id', 'in', budget_ids)]
# #         search_domain = ['|',('department_ids', 'in', dapartments),('department_ids', '=', False)]
# #         search_domain.append(('model_id.model','=','payment.request'))
#         _logger.info(u'search_domain budget=====: %s '%(search_domain))
#  
#         return search_domain    
 
#     @api.onchange('to_dep_budget_id')
#     def onchange_to_dep_budget_id(self):
#         search_domain=self.budget_domain()
#         domain = {'to_budget_id': search_domain}
#         return {'domain': domain}
 
#     @api.onchange('budget_year')
#     def onchange_date(self):
#         search_domain=self.budget_domain()
#         domain = {'to_budget_id': search_domain}
#         return {'domain': domain}
    
    line_ids = fields.One2many("mw.account.budget.change.line","parent_id", string="Lines",copy=True)

    selection_years = [('2020','2020'),
                    ('2021','2021'),
                    ('2022','2022'),
                    ('2023','2023'),
                    ('2024','2024'),
                    ('2025','2025'),
                    ('2026','2026'),
                    ('2027','2027'),
                    ('2028','2028'),
                    ('2029','2029'),
                    ('2030','2030'),
                    ('2031','2031'),
                    ('2032','2032'),
                    ('2033','2033'),
                    ('2034','2034'),
                    ('2035','2035'),
                    ('2036','2036'),
                    ('2037','2037'),
                    ('2038','2038'),
                    ('2039','2039'),
                    ('2040','2040')]

    budget_year = fields.Selection(selection_years, string=u'Төсвийн огноо', default=str(datetime.today().year))

    selection_months = [('01','01'),
                    ('02','02'),
                    ('03','03'),
                    ('04','04'),
                    ('05','05'),
                    ('06','06'),
                    ('07','07'),
                    ('08','08'),
                    ('09','09'),
                    ('10','10'),
                    ('11','11'),
                    ('12','12'),]
    
    selection_month = fields.Selection(selection_months, string=u'Сар', default=format(datetime.today().month,'02d'))
    
    
    def _default_department(self):
        return self.env['hr.department'].search([('id', '=', self.env.user.department_id.id)], limit=1)
    
    department_id = fields.Many2one('hr.department', 'Хэлтэс', default=_default_department, )
    
#     to_budget_id = fields.Many2one('mw.account.budget.period.line', 'Очих төсөв',)
#     to_dep_budget_id = fields.Many2one('mw.account.budget', 'Очих хэлтэсийн төсөв', )
    
#     department_id = fields.Many2one('mw.account.budget.period.line', 'Хэлтэс', default=_default_department, )

    state = fields.Selection(
        [("send", "Төсөв шилжүүлж өгөх"), ("receive", "Төсөв шилжүүлж авах"), ("done", "Гүйцэтгэсэн"), ("cancelled", "Цуцалсан")],
        required=True,
        default="send",
#         tracking=True,
    )

    def action_draft(self):
        for rec in self:
            rec.state = "receive"


    def action_confirm(self):
        period_line_line_obj = self.env['mw.account.budget.period.line.line']
        for rec in self:
            month=rec.selection_month
            print ('month ',month)
                
            budget_month='budget_{0}'.format(month)
            print ('budget_month ',budget_month)
            for line in rec.line_ids:
                if line.budget_id and line.to_budget_id:
                    if month=='01':
                        mval={'budget_01':line.amount}
                        if line.budget_id.budget_01>=line.amount:
                            line.budget_id.write({'budget_01':line.budget_id.budget_01 - line.amount})
                            line.to_budget_id.write({'budget_01':line.to_budget_id.budget_01 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_01,line.amount))
                    if month=='02':
                        mval={'budget_02':line.amount}
                        if line.budget_id.budget_02>=line.amount:
                            line.budget_id.write({'budget_02':line.budget_id.budget_02 - line.amount})
                            line.to_budget_id.write({'budget_02':line.to_budget_id.budget_02 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_02,line.amount))
                    if month=='03':
                        mval={'budget_03':line.amount}
                        if line.budget_id.budget_03>=line.amount:
                            line.budget_id.write({'budget_03':line.budget_id.budget_03 - line.amount})
                            line.to_budget_id.write({'budget_03':line.to_budget_id.budget_03 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_03,line.amount))
                    if month=='04':
                        mval={'budget_04':line.amount}
                        if line.budget_id.budget_04>=line.amount:
                            line.budget_id.write({'budget_04':line.budget_id.budget_04 - line.amount})
                            line.to_budget_id.write({'budget_04':line.to_budget_id.budget_04 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_04,line.amount))
                    if month=='05':
                        mval={'budget_05':line.amount}
                        if line.budget_id.budget_05>=line.amount:
                            line.budget_id.write({'budget_05':line.budget_id.budget_05 - line.amount})
                            line.to_budget_id.write({'budget_05':line.to_budget_id.budget_05 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_05,line.amount))
                    if month=='06':
                        mval={'budget_06':line.amount}
                        if line.budget_id.budget_06>=line.amount:
                            line.budget_id.write({'budget_06':line.budget_id.budget_06 - line.amount})
                            line.to_budget_id.write({'budget_06':line.to_budget_id.budget_06 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_06,line.amount))
                    if month=='07':
                        mval={'budget_07':line.amount}
                        if line.budget_id.budget_07>=line.amount:
                            line.budget_id.write({'budget_07':line.budget_id.budget_07 - line.amount})
                            line.to_budget_id.write({'budget_07':line.to_budget_id.budget_07 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_07,line.amount))
                    if month=='08':
                        mval={'budget_08':line.amount}
                        if line.budget_id.budget_08>=line.amount:
                            line.budget_id.write({'budget_08':line.budget_id.budget_08 - line.amount})
                            line.to_budget_id.write({'budget_08':line.to_budget_id.budget_08 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_08,line.amount))
                    if month=='09':
                        mval={'budget_09':line.amount}
                        if line.budget_id.budget_09>=line.amount:
                            line.budget_id.write({'budget_09':line.budget_id.budget_09 - line.amount})
                            line.to_budget_id.write({'budget_09':line.to_budget_id.budget_09 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_09,line.amount))
                    if month=='10':
                        mval={'budget_10':line.amount}
                        if line.budget_id.budget_10>=line.amount:
                            line.budget_id.write({'budget_10':line.budget_id.budget_10 - line.amount})
                            line.to_budget_id.write({'budget_10':line.to_budget_id.budget_10 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_10,line.amount))
                    if month=='11':
                        mval={'budget_11':line.amount}
                        if line.budget_id.budget_11>=line.amount:
                            line.budget_id.write({'budget_11':line.budget_id.budget_11 - line.amount})
                            line.to_budget_id.write({'budget_11':line.to_budget_id.budget_11 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_11,line.amount))
                    if month=='12':
                        mval={'budget_12':line.amount}
                        if line.budget_id.budget_12>=line.amount:
                            line.budget_id.write({'budget_12':line.budget_id.budget_12 - line.amount})
                            line.to_budget_id.write({'budget_12':line.to_budget_id.budget_12 + line.amount})
                        else:
                            raise UserError(u'Үлдэгдэл хүрэхгүй байна!!!\n Төсөв {0} үлдэгдэл {1} шилжүүлэх дүн {2}'.format(line.budget_id.name,line.budget_id.budget_12,line.amount))

#                     vals={
#                         'name': line.budget_id.name,
#                         'code': line.budget_id.code,
#                         'period_line_id': line.to_budget_id.id,
#                     }
                    
                    
#                     vals.update(mval)
#                     print ('mval ',mval)
#                     period_line_line_obj.create(vals)                          
            rec.state = "done"


    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

class AccountBudgetChangeLine(models.Model):
    _name = "mw.account.budget.change.line"
    _description = "Budget period change line"
#     _inherit = ["mail.thread", "mail.activity.mixin"]


            
    def budget_domain(self):
        search_domain=[]
        dapartments=[]
        for rec in self:
            if rec.parent_id.department_id:
                dapartments=[rec.parent_id.department_id.id]+rec.parent_id.department_id.child_ids.ids
#             elif rec.user_id and rec.user_id.department_id:
#                 dapartments=[rec.user_id.department_id.id]+rec.user_id.department_id.child_ids.ids
#                 search_domain =  ['|',('department_id', '=', rec.user_id.department_id.id),('department_id', '=', False)]
        deps=[]
        for de in dapartments:
            d=self.env['hr.department'].browse(de)
            deps.append(d.id)
            parent=d.parent_id
            while parent:
                deps.append(parent.id)
                parent=parent.parent_id
        if self.parent_id:
            print ('self.budget_year ',self.parent_id.budget_year)
            search_domain = [('period_line_id.parent_line_id.parent_id.department_id', 'in', deps),
                             ('period_line_id.parent_line_id.parent_id.budget_id.flow_line_id.state_type', '=', 'done'),
                             ('period_line_id.parent_line_id.parent_id.close_state', '=', 'open'),
                             ('period_line_id.parent_line_id.parent_id.budget_id.date_from','<=',(datetime.strptime('%s-01-01'%(self.parent_id.budget_year),'%Y-%m-%d')).date()),
                             ('period_line_id.parent_line_id.parent_id.budget_id.date_to','>=',(datetime.strptime('%s-01-01'%(self.parent_id.budget_year),'%Y-%m-%d')).date()),]
#         search_domain = ['|',('department_ids', 'in', dapartments),('department_ids', '=', False)]
#         search_domain.append(('model_id.model','=','payment.request'))
        _logger.info(u'search_domain budget=====: %s '%(search_domain))

        return search_domain    

    @api.onchange('department_id')
    def onchange_department_id(self):
        search_domain=self.budget_domain()
        domain = {'budget_id': search_domain}
        return {'domain': domain}

    @api.onchange('budget_year')
    def onchange_date(self):
        search_domain=self.budget_domain()
        domain = {'budget_id': search_domain}
        return {'domain': domain}
#     period_line_line_ids = fields.Many2many("mw.account.budget.period.line.line", 'budget_change_rel','budget_id','change_id')

    name = fields.Char("Төсөв шилжүүлэх шалтгаан")
    budget_id = fields.Many2one('mw.account.budget.period.line.line', 'Гарах төсөв',
                                domain="[('id', 'in', budget_ids)]",)

    budget_ids = fields.Many2many('mw.account.budget.period.line.line', 'mw_account_budget_change_rel','change_id','budeget_id',
                                  string='Зөвшөөрөгдсэн төсөвүүд', compute='_compute_budget_ids', store=True,)
    

    @api.depends('department_id','budget_year')
    def _compute_budget_ids(self):
        for item in self:
            search_domain=self.budget_domain()
#             print ('search_domain ',search_domain)
            budgets=self.env['mw.account.budget.period.line.line'].search(search_domain)
#             print ('budgets ',budgets)
            temp_budgets=[]
            if item.department_id:
                temp_budgets=budgets.ids
            item.budget_ids = temp_budgets
        
    selection_years = [('2020','2020'),
                    ('2021','2021'),
                    ('2022','2022'),
                    ('2023','2023'),
                    ('2024','2024'),
                    ('2025','2025'),
                    ('2026','2026'),
                    ('2027','2027'),
                    ('2028','2028'),
                    ('2029','2029'),
                    ('2030','2030'),
                    ('2031','2031'),
                    ('2032','2032'),
                    ('2033','2033'),
                    ('2034','2034'),
                    ('2035','2035'),
                    ('2036','2036'),
                    ('2037','2037'),
                    ('2038','2038'),
                    ('2039','2039'),
                    ('2040','2040')]

    budget_year = fields.Selection(selection_years, string=u'Төсвийн огноо', related='parent_id.budget_year',store=True)

    def _default_department(self):
        return self.env['hr.department'].search([('id', '=', self.env.user.department_id.id)], limit=1)
    
    department_id = fields.Many2one('hr.department', 'Хэлтэс',related='parent_id.department_id',store=True )
    parent_id = fields.Many2one('mw.account.budget.change', 'Parent', )
    
    amount = fields.Float('Дүн', )
    to_dep_budget_id = fields.Many2one('mw.account.budget', 'Очих хэлтэсийн төсөв', )    
#     to_budget_id = fields.Many2one('mw.account.budget.period.line', 'Очих төсөв',)
    to_budget_id = fields.Many2one('mw.account.budget.period.line.line', 'Очих төсөв',)

    def budget_domain_line(self):
        search_domain=[]
        budget_ids=[]
        for rec in self:
            if rec.to_dep_budget_id:
                for line in rec.to_dep_budget_id.line_ids:
                    for p in line.period_line_ids:  
                        for i in p.period_line_line_ids:
                            budget_ids.append(i.id)
        search_domain = [('id', 'in', budget_ids)]
#         search_domain = ['|',('department_ids', 'in', dapartments),('department_ids', '=', False)]
#         search_domain.append(('model_id.model','=','payment.request'))
        _logger.info(u'search_domain budget line=====: %s '%(search_domain))
 
        return search_domain    
 
    @api.onchange('to_dep_budget_id')
    def onchange_to_dep_budget_id(self):
        search_domain=self.budget_domain_line()
        domain = {'to_budget_id': search_domain}
        return {'domain': domain}
    