import json
from odoo import http
from odoo.http import request, Response


class UserProfile(http.Controller):

    @http.route('/oauth/profile', type='http', auth='it9_oauth2_server', csrf=False, methods=['GET'], scope=['profile'])
    def profile(self):
        res_user_id = request.env['res.users'].sudo().search([('id', '=', request.uid)])
        if res_user_id:
            headers = {
                'Cache-Control': 'no-store',
                'Content-Type': 'application/json'
            }
            return Response(json.dumps({
                'display_name': res_user_id.name,
                'email': res_user_id.email,
                'language': res_user_id.lang,
                'timezone': res_user_id.tz
            }), headers=headers, status=200)
        else:
            return Response(status=404)
