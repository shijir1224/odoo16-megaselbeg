from odoo import models, fields


class OAuth2GrantType(models.Model):
    _name = 'oauth2.grant_type'
    _description = 'OAuth 2.0 Grant Type'
    _sql_constraints = [
        ('unique', 'unique (code)', 'Record has already existed.'),
    ]

    name = fields.Char()
    code = fields.Char()
    model_id = fields.Many2one('ir.model')
