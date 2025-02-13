from odoo import models, fields


class OAuth2Scope(models.Model):
    _name = 'oauth2.scope'
    _description = 'OAuth 2.0 Scope'
    _sql_constraints = [
        ('unique', 'UNIQUE(code)', 'Record has already existed.'),
    ]

    name = fields.Char()
    code = fields.Char()
