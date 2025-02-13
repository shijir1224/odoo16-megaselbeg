from odoo import models
from odoo.addons.it9_oauth2_server.exceptions import AuthenticateException


class RefreshTokenGrant(models.TransientModel):
    _name = 'oauth2.grant_type.refresh_token'
    _description = 'Refresh Token'
    _inherit = 'oauth2.grant_type.mixin'

    code = 'refresh_token'

    def token(self, grant_type, client, kwargs):
        if grant_type.code == 'refresh_token':
            token_id = self.env['oauth2.token'].search([
                ('refresh_token', '=', kwargs['refresh_token']),
                ('client_id', '=', client.id),
            ])

            if token_id and not token_id.revoked:
                token_id.revoked = True
                return client.with_user(token_id.create_uid).action_new_token([x.code for x in token_id.scope])
            else:
                raise AuthenticateException('invalid_token', 'The access token expired', 401)
