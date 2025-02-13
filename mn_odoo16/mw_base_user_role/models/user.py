# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

import logging
_logger = logging.getLogger(__name__)

class ResUsers(models.Model):
    _inherit = 'res.users'


    def get_custom_val_base_role_branch_ids(self, role_lines, user, vals):
        add_ids = []
        rem_ids = []
        for role_line in role_lines:
            role = role_line.role_id
            if role.branch_ids:
                add_ids += role.branch_ids.ids
        nemeh_ids = list(set(add_ids))    # Remove duplicates IDs
        add_ids = list(set(nemeh_ids) - set(user.branch_ids.ids))
        rem_ids = list(set(user.branch_ids.ids) - set(nemeh_ids))
        to_add = [(4, gr) for gr in add_ids]
        to_remove = [(3, gr) for gr in rem_ids]
        diff = to_remove + to_add
        return diff

    def get_custom_val_base_role_branch_id(self, role_lines, user, vals):
        add_id = False
        for role_line in role_lines:
            role = role_line.role_id
            if role.branch_id:
                add_id = role.branch_id.id
        if add_id!=user.branch_id.id:
            return add_id
        return False


    def get_custom_val_base_role_warehouse_ids(self, role_lines, user, vals):
        add_ids = []
        rem_ids = []
        for role_line in role_lines:
            role = role_line.role_id
            if role.warehouse_ids:
                add_ids += role.warehouse_ids.ids
        nemeh_ids = list(set(add_ids))    # Remove duplicates IDs
        add_ids = list(set(nemeh_ids) - set(user.warehouse_ids.ids))
        rem_ids = list(set(user.warehouse_ids.ids) - set(nemeh_ids))
        to_add = [(4, gr) for gr in add_ids]
        to_remove = [(3, gr) for gr in rem_ids]
        diff = to_remove + to_add
        return diff

    def get_custom_val_base_role_warehouse_id(self, role_lines, user, vals):
        add_id = False
        for role_line in role_lines:
            role = role_line.role_id
            if role.warehouse_id:
                add_id = role.warehouse_id.id
        if add_id!=user.warehouse_id.id:
            return add_id
        return False

    def get_custom_val_base_role_done_warehouse_ids(self, role_lines, user, vals):
        add_ids = []
        rem_ids = []
        for role_line in role_lines:
            role = role_line.role_id
            if role.done_warehouse_ids:
                add_ids += role.done_warehouse_ids.ids
        nemeh_ids = list(set(add_ids))    # Remove duplicates IDs
        add_ids = list(set(nemeh_ids) - set(user.done_warehouse_ids.ids))
        rem_ids = list(set(user.done_warehouse_ids.ids) - set(nemeh_ids))
        to_add = [(4, gr) for gr in add_ids]
        to_remove = [(3, gr) for gr in rem_ids]
        diff = to_remove + to_add
        return diff

    def get_custom_val_base_role_manager_user_ids(self, role_lines, user, vals):
        add_ids = []
        rem_ids = []
        for role_line in role_lines:
            role = role_line.role_id
            if role.manager_user_ids:
                add_ids += role.manager_user_ids.ids
        nemeh_ids = list(set(add_ids))    # Remove duplicates IDs
        add_ids = list(set(nemeh_ids) - set(user.manager_user_ids.ids))
        rem_ids = list(set(user.manager_user_ids.ids) - set(nemeh_ids))
        to_add = [(4, gr) for gr in add_ids]
        to_remove = [(3, gr) for gr in rem_ids]
        diff = to_remove + to_add
        return diff

    def set_groups_from_roles(self, force=False):
        """Set (replace) the groups following the roles defined on users.
        If no role is defined on the user, its groups are let untouched unless
        the `force` parameter is `True`.
        """
        role_groups = {}
        # We obtain all the groups associated to each role first, so that
        # it is faster to compare later with each user's groups.
        for role in self.mapped('role_line_ids.role_id'):
            role_groups[role] = list(set(
                role.group_id.ids + role.implied_ids.ids +
                role.trans_implied_ids.ids))
        for user in self:
            if not user.role_line_ids and not force:
                continue
            group_ids = []
            vals = {}
            role_lines = user.role_line_ids.filtered(
                lambda rec: rec.is_enabled)
            for role_line in role_lines:
                role = role_line.role_id
                if role:
                    group_ids += role_groups[role]
            # vals = self.get_custom_val_base_role(role_lines, user, vals)
            
            branch_ids_vals = self.get_custom_val_base_role_branch_ids(role_lines, user, vals)
            branch_id_vals = self.get_custom_val_base_role_branch_id(role_lines, user, vals)

            warehouse_ids_vals = self.get_custom_val_base_role_warehouse_ids(role_lines, user, vals)
            warehouse_id_vals = self.get_custom_val_base_role_warehouse_id(role_lines, user, vals)

            done_warehouse_ids_vals = False
            try:
                done_warehouse_ids_vals = self.get_custom_val_base_role_done_warehouse_ids(role_lines, user, vals)
            except Exception as e:
                _logger.info('*******  done_warehouse_ids_vals algoooooo')


            manager_user_ids_vals = False
            try:
                manager_user_ids_vals = self.get_custom_val_base_role_manager_user_ids(role_lines, user, vals)
            except Exception as e:
                _logger.info('++++++  manager_user_ids algoooooo')


            group_ids = list(set(group_ids))    # Remove duplicates IDs
            groups_to_add = list(set(group_ids) - set(user.groups_id.ids))
            groups_to_remove = list(set(user.groups_id.ids) - set(group_ids))
            to_add = [(4, gr) for gr in groups_to_add]
            to_remove = [(3, gr) for gr in groups_to_remove]
            groups = to_remove + to_add

            if groups or branch_ids_vals or branch_id_vals or warehouse_ids_vals or warehouse_id_vals:
                if groups:
                    vals['groups_id'] = groups

                if branch_ids_vals:
                    vals['branch_ids'] = branch_ids_vals
                if branch_id_vals:
                    vals['branch_id'] = branch_id_vals
                
                if warehouse_ids_vals:
                    vals['warehouse_ids'] = warehouse_ids_vals
                if warehouse_id_vals:
                    vals['warehouse_id'] = warehouse_id_vals
                
                if done_warehouse_ids_vals:
                    vals['done_warehouse_ids'] = done_warehouse_ids_vals
                
                if manager_user_ids_vals:
                    vals['manager_user_ids'] = manager_user_ids_vals

                super(ResUsers, user).write(vals)
            elif force:
                super(ResUsers, user).write(vals)

        return True
