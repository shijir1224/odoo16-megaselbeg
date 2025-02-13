from odoo import models, fields


class OAuth2Uri(models.Model):
    _name = 'oauth2.uri'
    _description = 'OAuth 2.0 Uri'

    name = fields.Char()
