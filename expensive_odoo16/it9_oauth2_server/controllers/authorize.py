import werkzeug
import json
from odoo import http
from odoo.http import request, Response
from odoo.addons.it9_oauth2_server.exceptions import AuthenticateException


class OAuth2Authorize(http.Controller):

    @http.route('/oauth/authorize', type='http', auth='user', csrf=False, methods=['GET'])
    def oauth2_authorize(self, response_type, client_id, scope, redirect_uri, **kwargs):
        client = request.env['oauth2.client'].sudo().search([('client_id', '=', client_id)])
        if client and client.state == 'valid':
            pass
        else:
            raise AuthenticateException('invalid_client', "Invalid client ID or secret.", 401)

        uri = request.env['oauth2.uri'].sudo().search([('name', '=', redirect_uri)])
        if not uri or uri not in client.redirect_uris:
            raise AuthenticateException('invalid_request', redirect_uri, 400)

        rtype = request.env['oauth2.response_type'].sudo().search([('name', '=', response_type)])
        if not rtype or rtype not in client.response_types:
            raise AuthenticateException('invalid_request', response_type, 400)

        scopes = scope.split(',')
        invalid_scope = [x for x in scopes if x not in [y.code for y in client.scope]]
        if invalid_scope:
            raise AuthenticateException('invalid_scope', ','.join(invalid_scope), 400)

        code = request.env['oauth2.code'].create({
            'client_id': client.id,
            'redirect_uri': uri.id,
            'response_type': rtype.id,
            'scope':  [(6, 0, [x.id for x in client.scope if x.code in scopes])],
            'active': False,
            'code_challenge': kwargs.get('code_challenge'),
            'code_challenge_method': kwargs.get('code_challenge_method'),
        })
        if 'state' in kwargs:
            request.session['oauth_state'] = kwargs['state']
        return werkzeug.utils.redirect(f'/web#view_type=form&model=oauth2.code&action={request.env.ref("it9_oauth2_server.action_oauth2_code_authorize").id}&id={code.id}')
