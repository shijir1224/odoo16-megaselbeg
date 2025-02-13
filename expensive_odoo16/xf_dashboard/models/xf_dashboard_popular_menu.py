# -*- coding: utf-8 -*-

from odoo import models, fields, api


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    menu_icon_data = fields.Binary(
        string='Menu Icon Image',
        compute="_compute_menu_icon",
        store=True,
        attachment=True,
        recursive=True,
    )
    app_menu_id = fields.Many2one(
        string='App Menu',
        comodel_name='ir.ui.menu',
        compute="_compute_app_menu",
        store=True,
        readonly=True,
        recursive=True,
    )

    @api.depends('web_icon_data', 'parent_id.menu_icon_data')
    def _compute_menu_icon(self):
        for menu in self:
            if menu.web_icon_data:
                menu.menu_icon_data = menu.web_icon_data
            elif menu.parent_id and menu.parent_id.menu_icon_data:
                menu.menu_icon_data = menu.parent_id.menu_icon_data

    @api.depends('parent_id', 'parent_id.app_menu_id')
    def _compute_app_menu(self):
        for menu in self:
            if not menu.parent_id:
                menu.app_menu_id = menu
            elif menu.parent_id.app_menu_id:
                menu.app_menu_id = menu.parent_id.app_menu_id


class XFDashboardPopularMenu(models.Model):
    _name = 'xf.dashboard.popular.menu'
    _description = 'Popular Odoo Menu'

    _inherits = {'ir.ui.menu': 'menu_id'}
    _order = 'number desc'

    menu_id = fields.Many2one('ir.ui.menu', string='Menu Item', required=True, readonly=True, ondelete='cascade')
    visible = fields.Boolean('Visible', default=True)
    number = fields.Integer('Number', required=True, default=1, readonly=True)

    @api.model
    def save_menu(self, menu_id):
        home_menu = self.env.ref('xf_dashboard.xf_dashboard_menu')
        if menu_id == home_menu.id:
            # Skip Home Page and return False
            return False
        menu = self.env['ir.ui.menu'].browse(menu_id)
        if not menu:
            # If menu not found, return False
            return False
        link = self.search([('create_uid', '=', self.env.user.id), ('menu_id', '=', menu.id)], limit=1)
        if link:
            # If popular link record found, increase number of click and return True
            link.number += 1
            return True
        if self.create({'menu_id': menu.id}):
            # Create new popular link record and return True
            return True

    def action_toggle_visibility(self):
        for record in self:
            record.visible = not record.visible
        return True

    def action_open_app_menu(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': self.app_menu_id.name,
            'target': 'new',
            'url': '/web#menu_id={}'.format(self.app_menu_id.id),
        }

    def action_open_menu(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': self.name,
            'target': 'new',
            'url': '/web#menu_id={}'.format(self.menu_id.id),
        }
