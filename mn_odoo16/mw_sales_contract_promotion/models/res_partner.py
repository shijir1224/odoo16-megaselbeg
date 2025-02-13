from odoo import fields
from odoo.models import Model


class ResPartner(Model):
    _inherit = 'res.partner'

    sale_contract_ids = fields.One2many('mw.sales.contract', 'partner_id', string='Sale contracts')
    sale_contract_count = fields.Integer(string='Sale contract count', compute='compute_sale_contract_count')

    def compute_sale_contract_count(self):
        for obj in self:
            obj.sale_contract_count = len(obj.sale_contract_ids)

    def action_view_sale_contract(self):
        self.ensure_one()
        action = self.sudo().env.ref('mw_sales_contract_promotion.action_sales_contract').read()[0]
        action['domain'] = [
            ('id', 'in', self.sale_contract_ids.ids),
        ]
        action['context'] = {'create': False}
        return action
