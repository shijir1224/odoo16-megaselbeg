from odoo import models
from odoo.addons.it9_oauth2_server.exceptions import AuthenticateException


class AuthorizationCode(models.TransientModel):
    _name = 'oauth2.grant_type.authorization_code'
    _description = 'Authorization Code'
    _inherit = 'oauth2.grant_type.mixin'

    def token(self, grant_type, client, kwargs):
        if grant_type.code == 'authorization_code':
            code = self.env['oauth2.code'].search([('code', '=', kwargs['code']), ('client_id', '=', client.id), ('redirect_uri.name', '=', kwargs['redirect_uri'])])
            if code and code.active:
                token = client.with_user(code.create_uid).action_new_token([x.code for x in code.scope])
                code.active = False
                return token
            else:
                raise AuthenticateException('invalid_request', 'Invalid authorization code', 400)
