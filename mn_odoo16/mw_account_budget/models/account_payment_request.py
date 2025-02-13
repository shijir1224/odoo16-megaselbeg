# -*- coding: utf-8 -*-
##############################################################################
#
#    ManageWall, Enterprise Management Solution
#    Copyright (C) 2013-2018 ManageWall Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#
#    Email : daramaa26@gmail.com
#    Phone : 976 + 99081691
#
##############################################################################

from datetime import datetime, date
from odoo import fields, models, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError
from dateutil.relativedelta import relativedelta
from odoo import tools
import time
from odoo.addons.mw_base.report_helper import verbose_numeric, comma_me, convert_curr
from odoo.addons.mw_base.verbose_format import verbose_format
import logging
_logger = logging.getLogger(__name__)


class payment_request(models.Model):
    ''' Мөнгө хүссэн өргөдөл
    '''

    _inherit = 'payment.request'

    def budget_domain(self):
        domain = {'flow_id': False}
        search_domain=[]
        dapartments=[]
        for rec in self:
            if rec.department_id:
                dapartments=[rec.department_id.id]+rec.department_id.child_ids.ids
            elif rec.user_id and rec.user_id.department_id:
                dapartments=[rec.user_id.department_id.id]+rec.user_id.department_id.child_ids.ids
#                 search_domain =  ['|',('department_id', '=', rec.user_id.department_id.id),('department_id', '=', False)]
        deps=[]
        for de in dapartments:
            d=self.env['hr.department'].browse(de)
            deps.append(d.id)
            parent=d.parent_id
            while parent:
                deps.append(parent.id)
                parent=parent.parent_id
        search_domain = [('period_line_id.parent_line_id.parent_id.department_id', 'in', deps),
                         ('period_line_id.parent_line_id.parent_id.budget_id.flow_line_id.state_type', '=', 'done'),
                         ('period_line_id.parent_line_id.parent_id.close_state', '=', 'open'),
                         ('period_line_id.parent_line_id.parent_id.budget_id.date_from','<=',(datetime.strptime('%s-01-01'%(self.budget_year),'%Y-%m-%d')).date()),
                         ('period_line_id.parent_line_id.parent_id.budget_id.date_to','>=',(datetime.strptime('%s-01-01'%(self.budget_year),'%Y-%m-%d')).date()),]
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


    def _get_is_budget(self):
        if self.budget_id:
            return True
        else:
            return False

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

    budget_date = fields.Date("Төсвийн огноо",)
    budget_year = fields.Selection(selection_years, string=u'Төсвийн огноо', default=str(datetime.today().year))

    budget_id = fields.Many2one('mw.account.budget.period.line.line', 'Төсөв',readonly=True,
                                domain="[('id', 'in', budget_ids)]",states={'draft':[('readonly',False)]})
    is_budget=fields.Boolean('Төсөвтэй эсэх', default=_get_is_budget)

    budget_ids = fields.Many2many('mw.account.budget.period.line.line', 'mw_account_budget_payment_request_rel','request_id','budeget_id',
                                  string='Зөвшөөрөгдсэн төсөвүүд', compute='_compute_budget_ids', store=True, readonly=True)

    @api.depends('department_id','budget_year')
    def _compute_budget_ids(self):
        for item in self:
            if item.department_id or item.budget_year:
                search_domain = item.budget_domain()
                budgets=item.env['mw.account.budget.period.line.line'].search(search_domain)
                temp_budgets = []
                if item.department_id:
                    temp_budgets = budgets.ids
                item.budget_ids = temp_budgets

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
