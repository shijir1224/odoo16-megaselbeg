# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from datetime import datetime, time, timedelta

blacklist_type_global = {
    'greylist': 'GREY',
    'blacklist': 'BLACK',
    'no': 'ҮГҮЙ',
}
blacklist_selection = [('greylist','GREY'), ('blacklist','BLACK'),('no','Үгүй')]
class res_partner(models.Model):
    _inherit = 'res.partner'

    blacklist_type = fields.Selection(blacklist_selection, string=u'Блаклист', compute='_compute_blacklist_type', store=True, tracking=True, readonly=False, copy=False)
    blacklist_date = fields.Datetime(string=u'Блаклист орсон огноо', compute='_compute_blacklist_type', store=True, tracking=True, readonly=False, copy=False)
    blacklist_desc = fields.Char(string=u'Блаклист тайлбар', tracking=True, copy=False)
    blacklist_history_ids = fields.One2many('res.partner.blacklist.history', 'partner_id', string='Хар Жагсаалтын түүх', readonly=True)
    
    def _compute_blacklist_type(self):
        for item in self:
            item.blacklist_type = 'no'
            item.blacklist_date = False
    
    def write(self, vals):
        if vals.get('blacklist_type', False):
            self.create_black_history(vals.get('blacklist_type', False), vals.get('blacklist_desc', False), vals.get('blacklist_date', False))
        return super(res_partner, self).write(vals)

    def create_black_history(self, b_type, desc, b_date=False):
        self.env['res.partner.blacklist.history'].create({
            'partner_id': self.id,
            'date': b_date or datetime.now(),
            'blacklist_type': b_type,
            'desc': desc,
        })

    def name_get(self):
        res = []
        for partner in self:
            res_name = super(res_partner, partner).name_get()
            res_partner_name = res_name[0][1]
            if partner.blacklist_type in ['greylist','blacklist']:
                res_partner_name = res_name[0][1]+u' ['+blacklist_type_global[partner.blacklist_type]+']'
            res.append((partner.id, res_partner_name))
        return res

class res_partner_blacklist_history(models.Model):
    _name = 'res.partner.blacklist.history'
    _description = 'Харилцагчийн хар жагсаалт дүрэм'
    _order = 'partner_id, date'

    partner_id = fields.Many2one('res.partner', string='Харилцагч')
    date = fields.Datetime(string=u'Блаклист орсон огноо')
    blacklist_type = fields.Selection(blacklist_selection, string=u'Блаклист')
    desc = fields.Char(string=u'Блаклист тайлбар')

class res_partner_blacklist(models.Model):
    _name = 'res.partner.blacklist'
    _description = 'Харилцагчийн хар жагсаалт дүрэм'
    _order = 'sequence'

    name = fields.Selection(blacklist_selection, string="Блаклист", required=True)
    sequence = fields.Integer('Дараалал', default=1)
    company_type = fields.Selection([('company','Байгууллага'),('person','Иргэн')], string='Харилцагчийн төрөл')
