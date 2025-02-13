import json
import datetime
from odoo import models, fields, api


class OAuth2Token(models.Model):
    _name = 'oauth2.token'
    _description = 'OAuth 2.0 Token'
    _order = 'create_date desc'
    _sql_constraints = [
        ("access_token_unique", "unique (access_token)", "Access token has already existed"),
        ("refresh_token_unique", "unique (refresh_token)", "Refresh token has already existed")
    ]

    client_id = fields.Many2one('oauth2.client', ondelete='cascade')
    token_type = fields.Char(default='Bearer')
    access_token = fields.Char(default=lambda self: self.generate_access_token())
    refresh_token = fields.Char(default=lambda self: self.generate_refresh_token())
    scope = fields.Many2many('oauth2.scope', 'oauth2_token_scope_rel', string='Scopes')
    revoked = fields.Boolean(default=False)
    expires_in = fields.Integer(default=3600)
    expires_at = fields.Datetime(compute='_compute_expires_at')
    # user_id

    state = fields.Selection([
        ('valid', 'Valid'),
        ('expire', 'Expired'),
    ], string='Status', compute='_compute_state')

    @api.depends('create_date', 'expires_in')
    def _compute_expires_at(self):
        for one in self:
            one.expires_at = one.create_date + datetime.timedelta(seconds=one.expires_in)

    @api.depends('create_date', 'expires_in', 'revoked', 'client_id.state')
    def _compute_state(self):
        for one in self:
            one.state = 'valid' if fields.Datetime.now() < one.expires_at and not one.revoked and one.client_id.state == 'valid' else 'expire'

    def generate_access_token(self):
        return self.client_id._generate_string(42)

    def generate_refresh_token(self):
        return self.client_id._generate_string(42)

    def action_revoke(self):
        self.revoked = True

    def __str__(self, *args, **kwargs):
        return json.dumps({
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "refresh_token": self.refresh_token,
            "scope": ' '.join([x.code for x in self.scope])
        })
