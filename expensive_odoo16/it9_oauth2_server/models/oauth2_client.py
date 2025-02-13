import random
import string
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.it9_oauth2_server.exceptions import AuthenticateException


class OAuth2Client(models.Model):
    _name = 'oauth2.client'
    _description = 'Application'
    _rec_name = 'client_name'

    client_id = fields.Char(string='Client ID', required=True, default=lambda self: self.generate_client_id(), readonly=True, groups='base.group_system')
    client_secret = fields.Char(required=True, default=lambda self: self.generate_client_secret(), readonly=True, groups='base.group_system')
    client_secret_expires_at = fields.Datetime(string='Expired at', default=lambda *a: fields.datetime.now() + relativedelta(years=1), required=True)

    client_name = fields.Char(required=True)
    logo_url = fields.Char(string='Logo')
    logo_url_image = fields.Char(related='logo_url')
    client_uri = fields.Char(string='Client Website')
    grant_types = fields.Many2many('oauth2.grant_type', 'oauth2_client_grant_type_rel')
    redirect_uris = fields.Many2many('oauth2.uri', 'oauth2_client_uri_rel')
    response_types = fields.Many2many('oauth2.response_type', 'oauth2_client_response_type_rel')
    scope = fields.Many2many('oauth2.scope', 'oauth2_client_scope_rel', string='Scopes')
    token_endpoint_auth_method = 'client_secret_basic'
    default_token_expires_in = fields.Integer(string='Token Expires In (s)', default=3600)

    state = fields.Selection([
        ('valid', 'Valid'),
        ('expire', 'Expired')
    ], string='Status', compute='_compute_state')

    code_ids = fields.One2many('oauth2.code', 'client_id', 'Authorization Codes')
    token_ids = fields.One2many('oauth2.token', 'client_id', 'Access Tokens')

    def generate_client_id(self):
        return self._generate_string(24)

    def generate_client_secret(self):
        return self._generate_string(48)

    def _generate_string(self, length):
        return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(length)])

    @api.depends('client_secret_expires_at')
    def _compute_state(self):
        for one in self:
            one.state = 'valid' if one.client_secret_expires_at and fields.Datetime.now() < one.client_secret_expires_at else 'expire'

    def action_regenerate_client_secret(self):
        self.ensure_one()
        new_client_secret = self.generate_client_secret()
        # self.client_secret = new_client_secret
        self.write({'client_secret': new_client_secret})
        self.env.cr.commit()
        return {
            'name': _('Reset Secret'),
            'target': 'new',
            'view_mode': 'form',
            'res_model': 'oauth2.dialog',
            'view_id': self.env.ref("it9_oauth2_server.oauth2_dialog_form", False).id,
            'type': 'ir.actions.act_window',
            'context': {'default_message': 'Please keep this secret independently.\n\n' + new_client_secret}
        }

    def action_new_token(self, scopes: list = []):
        invalid_scope = [x for x in scopes if x not in [y.code for y in self.scope]]
        if invalid_scope:
            raise AuthenticateException('invalid_scope', ','.join(invalid_scope), 400)
        return self.token_ids.create({
            'client_id': self.id,
            'scope': [(6, 0, [x.id for x in self.scope if x.code in scopes])],
            'expires_in': self.default_token_expires_in,
        })
