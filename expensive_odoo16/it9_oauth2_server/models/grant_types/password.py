from odoo import models


class Password(models.TransientModel):
    _name = 'oauth2.grant_type.password'
    _description = 'Client Credentials'
    _inherit = 'oauth2.grant_type.mixin'

    def token(self, grant_type, client, kwargs):
        if grant_type.code == 'password':
            res_user_id = self.env['res.users']._login(self.env.cr.dbname, kwargs['username'], kwargs['password'], self.env)
            if client and client.state == 'valid' and [x for x in client.grant_types if x.code == 'password'] and res_user_id:
                res_user = self.env['res.users'].browse(res_user_id)
                return client.with_user(res_user).action_new_token([x.code for x in client.scope])
            else:
                raise Exception('invalid_request')
