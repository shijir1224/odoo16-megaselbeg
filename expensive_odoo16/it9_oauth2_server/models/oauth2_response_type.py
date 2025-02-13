from odoo import models, fields


class OAuth2ResponseType(models.Model):
    _name = 'oauth2.response_type'
    _description = 'OAuth 2.0 Response Type'

    name = fields.Char()
