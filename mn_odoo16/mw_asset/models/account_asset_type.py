from odoo import api, fields, models, _

class AccountAssetType(models.Model):
    _name = 'account.asset.type'
    _description = 'Account asset type'

    name = fields.Char(string="Төрлийн нэр")
    model_id = fields.Many2one('account.asset', string="Хөрөнгийн загвар", domain=[('state','=','model')])
    company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.user.company_id)
