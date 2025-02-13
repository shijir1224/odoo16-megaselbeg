from odoo import api, http, models, SUPERUSER_ID
from odoo.http import request
import inspect


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _auth_method_it9_oauth2_server(cls):
        key = request.httprequest.headers.get("Authorization")
        if key:
            env = api.Environment(request.cr, SUPERUSER_ID, request.context)
            token_type, access_token = key.split(" ")
            token = env['oauth2.token'].search([('token_type', '=', token_type), ('access_token', '=', access_token)], limit=1)
            if token.state == 'valid':
                scope = [x for x in inspect.stack() if 'cls' in x.frame.f_locals and 'rule' in x.frame.f_locals][-1].frame.f_locals['func'].routing.get('scope') or []
                scope = scope if isinstance(scope, list) else [scope]
                if not [x for x in scope if x not in [y.code for y in token.scope]]:
                    request.uid = token.create_uid.id
                    return

        raise http.AuthenticationError('Access denied')
