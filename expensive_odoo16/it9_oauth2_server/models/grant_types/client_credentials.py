from odoo import models


class ClientCredential(models.TransientModel):
    _name = 'oauth2.grant_type.client_credentials'
    _description = 'Client Credentials'
    _inherit = 'oauth2.grant_type.mixin'

    def token(self, grant_type, client, kwargs):
        if grant_type.code == 'client_credentials':
            scopes = kwargs.get('scope').split(',') if kwargs.get('scope') else []
            return client.with_user(client.create_uid).action_new_token(scopes)
