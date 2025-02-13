import requests
import random
import string
from odoo import models, fields
from odoo.http import request, Response


class OAuth2Code(models.Model):
    _name = 'oauth2.code'
    _description = 'Authorization Code'
    _rec_name = 'client_name'

    code = fields.Char(required=True, default=lambda self: self.generate_code())
    client_id = fields.Many2one('oauth2.client', ondelete='cascade')
    redirect_uri = fields.Many2one('oauth2.uri', ondelete='restrict')
    response_type = fields.Many2one('oauth2.response_type', ondelete='restrict')
    scope = fields.Many2many('oauth2.scope', 'oauth2_code_scope_rel', string='Scopes', ondelete='restrict')
    nonce = fields.Char()
    code_challenge = fields.Char()
    code_challenge_method = fields.Char()
    # res_users_id = fields.Many2one('res.users', ondelete='cascade')

    active = fields.Boolean(default=False)

    client_logo_url_image = fields.Char(related='client_id.logo_url_image')
    client_name = fields.Char(related='client_id.client_name')

    def generate_code(self):
        return ''.join([random.choice(string.ascii_letters + string.digits) for n in range(48)])

    def action_deny(self):
        redirect_uri = self.redirect_uri.name
        self.unlink()
        return {
            'type': 'ir.actions.act_url',
            'url': redirect_uri,
            'target': 'self'
        }

    def action_authorize(self):
        self.active = True
        uri = f'{self.redirect_uri.name}?code={self.code}'
        if 'oauth_state' in request.session:
            uri += f"&state={request.session['oauth_state']}"
        return {
            'type': 'ir.actions.act_url',
            'url': uri,
            'target': 'self'
        }
