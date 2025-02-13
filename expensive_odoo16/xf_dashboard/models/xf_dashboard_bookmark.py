# -*- coding: utf-8 -*-
from odoo import models, fields, api


class XFDashboardBookmark(models.Model):
    _name = 'xf.dashboard.bookmark'
    _description = 'Dashboard Bookmark'
    _order = 'name asc'

    def _get_default_icon(self):
        return self.env.ref('xf_dashboard.link_icon', False)

    menu_id = fields.Many2one('ir.ui.menu', string='Menu', ondelete='cascade')
    name = fields.Char('Name', required=True)
    external_url = fields.Char('External URL')
    url = fields.Char('URL', compute='_compute_url')
    target = fields.Selection(
        selection=[('_blank', 'New Window'), ('_self', 'This Window')],
        string='Target', default='_self', required=True)
    type = fields.Selection(
        selection=[('link', 'Link'), ('tile', 'Tile')],
        string='Type', default='link', required=True, index=True,
        help='Links and Tiles will be displayed as separate widgets')

    icon_image = fields.Binary(string='Icon Preview', related='icon_id.icon', readonly=True)
    icon_id = fields.Many2one('xf.dashboard.icon', string='Icon', required=True, default=_get_default_icon)

    visibility = fields.Selection(
        selection=[
            ('public', 'Public'),
            ('group', 'Based on User Groups'),
            ('private', 'Private'),
        ], string='Visibility', default='private', required=True)
    groups = fields.Many2many('res.groups', 'xf_dashboard_quick_link_groups', 'link_id', 'group_id', string='Groups')
    private_bookmarks_ids = fields.One2many(
        comodel_name='xf.dashboard.bookmark.private', inverse_name='parent_id', string='User Settings',
        readonly=True,
    )

    @api.onchange('menu_id')
    def _onchange_menu(self):
        self.name = self.menu_id.name

    @api.depends('menu_id', 'external_url')
    def _compute_url(self):
        for link in self:
            if link.external_url:
                link.url = link.external_url
            elif link.menu_id:
                link.url = '/web#menu_id={}'.format(link.menu_id.id)
            else:
                link.url = ''


class XFDashboardBookmarkPrivate(models.Model):
    _name = 'xf.dashboard.bookmark.private'
    _description = "User Bookmark"
    _inherits = {'xf.dashboard.bookmark': 'parent_id'}
    _order = 'pinned desc, sequence asc, name asc'

    parent_id = fields.Many2one(
        comodel_name='xf.dashboard.bookmark', string='Link',
        required=True, ondelete='cascade', index=True)

    active = fields.Boolean('Active', default=True)
    visible = fields.Boolean('Visible', default=True, index=True)
    sequence = fields.Integer('Sequence', default=10)
    pinned = fields.Boolean('Pinned', default=False)
    icon_image = fields.Binary(string='Icon Preview', related='icon_id.icon', readonly=True)

    _sql_constraints = [
        ('user_link_uniq', 'unique (create_uid, parent_id)', 'The link must be unique per user!'),
    ]

    @api.model
    def get_bookmarks(self, limit=10):
        self.generate_user_links()
        domain = [('visible', '=', True), ('type', '=', 'link'), ('create_uid', '=', self.env.user.id)]
        return self.search_read(domain, ['name', 'url', 'target'], limit=limit)

    def get_tiles(self, limit=10):
        self.generate_user_links()
        domain = [('visible', '=', True), ('type', '=', 'tile'), ('create_uid', '=', self.env.user.id)]
        return self.search_read(domain, ['name', 'url', 'target'], limit=limit)

    def generate_user_links(self):
        bookmarks = self.env['xf.dashboard.bookmark'].search([('visibility', '!=', 'private')])
        bookmarks_ids = set(bookmarks.ids)
        private_bookmarks = self.search([('create_uid', '=', self.env.user.id)])
        private_bookmarks_ids = set(private_bookmarks.mapped('parent_id').ids)
        diff_ids = bookmarks_ids - private_bookmarks_ids
        if diff_ids:
            diff_bookmarks = self.env['xf.dashboard.bookmark'].browse(diff_ids)
            for bookmark in diff_bookmarks:
                self.create({'parent_id': bookmark.id})

    def action_open_link(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'name': 'Open Link',
            'target': 'self' if self.target == '_self' else 'new',
            'url': self.url,
        }

    def unlink(self):
        for private_bookmark in self:
            if private_bookmark.visibility == 'private':
                private_bookmark.parent_id.unlink()
        return super(XFDashboardBookmarkPrivate, self).unlink()

    def action_toggle_visibility(self):
        for record in self:
            record.visible = not record.visible
        return True
