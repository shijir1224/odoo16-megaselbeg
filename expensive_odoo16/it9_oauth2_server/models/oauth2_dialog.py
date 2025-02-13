from odoo import models, fields


class OAuth2Dialog(models.TransientModel):
    _name = 'oauth2.dialog'
    _auto = False
    _log_access = True

    message = fields.Text()
