# -*- coding: utf-8 -*-
# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResUsersRole(models.Model):
    _inherit = 'res.users.role'
    
    branch_id = fields.Many2one('res.branch', 'Салбар')
    branch_ids = fields.Many2many('res.branch', 'res_branch_res_users_role_rel', column1='role_id', column2='branch_id',string='Салбарууд')

    warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах')
    warehouse_ids = fields.Many2many('stock.warehouse', 'stock_warehouse_res_users_role_rel', column1='role_id', column2='warehouse_id',string='Агуулахууд')
    done_warehouse_ids = fields.Many2many('stock.warehouse', 'stock_warehouse_done_res_users_role_rel', column1='role_id', column2='done_warehouse_id',string='Батлах Агуулахууд')
    manager_user_ids = fields.Many2many('res.users', 'manager_user_res_users_role_rel', column1='role_id', column2='manager_user_id',string='Батлах хэрэглэгчид')

    import_user_id = fields.Many2one('res.users', 'Импортлох хэрэглэгч')

    company_id = fields.Many2one('res.company', string='Company', required=True, index=True, default=lambda self: self.env.user.company_id)


    def action_import_user(self):
        if not self.import_user_id:
            raise UserError(u'Импортлох хэрэглэгчээ сонгох шаарлагатай')

        self.implied_ids = self.import_user_id.groups_id.ids
        self.branch_id = self.import_user_id.branch_id.id
        self.branch_ids = self.import_user_id.branch_ids.ids
        self.warehouse_id = self.import_user_id.warehouse_id.id
        self.warehouse_ids = self.import_user_id.warehouse_ids.ids
        try:
            self.done_warehouse_ids = self.import_user_id.done_warehouse_ids.ids
        except Exception as e:
            _logger.info(' user deer done_warehouse_ids alga bnaaaaaa------- ')
        
        try:
            self.manager_user_ids = self.import_user_id.manager_user_ids.ids
        except Exception as e:
            _logger.info(' user deer manager_user_ids alga bnaaaaaa------- ')
        self.import_user_id = False

    def action_update_user(self):
    	for item in self.user_ids:
    		item.set_groups_from_roles(force=True)


    def copy(self, default=None):
        # TDE FIXME: should probably be copy_data
        self.ensure_one()
        if default is None:
            default = {}
        if 'name' not in default:
            default['name'] = "%s (copy)" % self.name
        return super(ResUsersRole, self).copy(default=default)

