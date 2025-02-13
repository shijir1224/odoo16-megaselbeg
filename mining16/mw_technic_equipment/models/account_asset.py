from odoo import api, models, fields

class AccountAsset(models.Model):
    _inherit = 'account.asset'

    technic_id = fields.Many2one('technic.equipment', string='Техник', store=True)