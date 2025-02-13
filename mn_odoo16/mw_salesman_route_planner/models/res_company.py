from odoo.models import Model


class ResCompany(Model):
    _inherit = 'res.company'

    def get_location_data(self, company_id=False):
        if not self and company_id:
            self = self.browse(company_id)
        return {
            'lat': self.partner_id.partner_latitude,
            'lng': self.partner_id.partner_longitude,
            'name': self.name,
        }
