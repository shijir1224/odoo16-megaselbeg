import json
from odoo import http
from odoo.http import request, Response

from ..exceptions import AuthenticateException


class RestAuth2Access(http.Controller):

    @http.route('/oauth/token', type='http', auth='public', csrf=False, methods=['POST'])
    def auth_url(self, **kw):
        headers = {
            'Cache-Control': 'no-store',
            'Content-Type': 'application/json'
        }

        try:
            # grant_type
            if 'grant_type' in kw:
                grant_type = request.env['oauth2.grant_type'].sudo().search([('code', '=', kw['grant_type'])], limit=1)
                if not grant_type:
                    raise AuthenticateException('unsupported_grant_type', kw['grant_type'], 400)
            else:
                raise AuthenticateException('invalid_request', "Request was missing the 'grant_type' parameter.", 400)

            # client_id
            # client_secret
            if request.httprequest.authorization:
                client_id = request.httprequest.authorization.username
                client_secret = request.httprequest.authorization.password
            elif 'client_id' in kw and 'client_secret' in kw:
                client_id = kw['client_id']
                client_secret = kw['client_secret']
            else:
                raise AuthenticateException('invalid_request', "Request was missing the 'client_id' or 'client_secret' parameter.", 400)

            oauth2_client = request.env['oauth2.client'].sudo().search([('client_id', '=', client_id), ('client_secret', '=', client_secret)], limit=1)
            if oauth2_client and oauth2_client.state == 'valid':
                pass
            else:
                raise AuthenticateException('invalid_client', "Invalid client ID or secret.", 401)

            # Raise exception if client does not support this grant type
            if grant_type.code not in [x.code for x in oauth2_client.grant_types]:
                raise AuthenticateException('unauthorized_client', kw['grant_type'], 400)

            token = request.env[grant_type.model_id.model].sudo().token(grant_type, oauth2_client, kw)
            return Response(str(token), headers=headers, status=200)
        except AuthenticateException as ex:
            return Response(str(ex), headers=headers, status=ex.status)
        except Exception as ex:
            return Response(json.dumps({'error_description': ex.args[0]}), headers=headers, status=500)
