from odoo import models, fields
from odoo.addons.it9_oauth2_server.exceptions import AuthenticateException


class OAuth2GrantTypeMixin(models.TransientModel):
    _name = 'oauth2.grant_type.mixin'
    _auto = False
    _log_access = True

    def token(self, grant_type, client, kwargs):
        raise NotImplementedError()

    def new_token(self, client_id, scope_ids):
        return client_id.token_ids.create({
            'client_id': client_id.id,
            'scope': [(6, 0, [client_id.scope.filtered_domain([('code', '=', x)]).id for x in scopes])],
            'expires_in': client_id.default_token_expires_in,
        })

    def compare_scopes(self, allowed_scope_ids, requested_scopes_code):
        extra = [x for x in requested_scopes_code if x not in [y.code for y in allowed_scope_ids]]
        if extra:
            raise AuthenticateException('invalid_scope', ','.join(extra), 400)

        return [x for x in allowed_scope_ids if x.code in requested_scopes_code]
