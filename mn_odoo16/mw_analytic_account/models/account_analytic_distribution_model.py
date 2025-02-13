# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class NonMatchingDistribution(Exception):
    pass


class AccountAnalyticDistributionModel(models.Model):
    _inherit = 'account.analytic.distribution.model'

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        ondelete='cascade',
    )

    branch_id = fields.Many2one(
        'res.branch',
        string='Branch',
        ondelete='cascade',
    )


    # @api.model
    # def _get_distribution(self, vals):
    #     """ Returns the distribution model that has the most fields that corresponds to the vals given
    #         This method should be called to prefill analytic distribution field on several models """
    #     domain = []
    #     if vals.get('department_id',False):
    #         dep_dist=self.search([('department_id','=',vals['department_id'])],limit=1).analytic_distribution
    #         return dep_dist
    #     elif vals.get('branch_id',False):
    #         dep_dist=self.search([('branch_id','=',vals['branch_id'])],limit=1).analytic_distribution
    #         return dep_dist
    #     elif self.env.user.department_id:
    #         dep_dist=self.search([('department_id','=',self.env.user.department_id.id)],limit=1).analytic_distribution
    #         return dep_dist
    #     elif self.env.user.employee_id and self.env.user.employee_id.department_id:
    #         dep_dist=self.search([('department_id','=',self.env.user.employee_id.department_id.id)],limit=1).analytic_distribution
    #         return dep_dist
    #     elif self.env.user.branch_id:
    #         dep_dist=self.search([('branch_id','=',self.env.user.branch_id.id)],limit=1).analytic_distribution
    #         return dep_dist
    #
    #     for fname, value in vals.items():
    #         domain += self._create_domain(fname, value) or []
    #     best_score = 0
    #     res = {}
    #     fnames = set(self._get_fields_to_check())
    #     for rec in self.search(domain):
    #         try:
    #             score = sum(rec._check_score(key, vals.get(key)) for key in fnames)
    #             if score > best_score:
    #                 res = rec.analytic_distribution
    #                 best_score = score
    #         except NonMatchingDistribution:
    #             continue
    #     return res
    #
    # def _get_fields_to_check(self):
    #
    #     return (
    #             set(self.env['account.analytic.distribution.model']._fields)
    #             - set(self.env['analytic.mixin']._fields)
    #             - set({'department_id'})
    #             - set({'branch_id'})
    #             - set(models.MAGIC_COLUMNS) - {'display_name', '__last_update'}
    #     )
