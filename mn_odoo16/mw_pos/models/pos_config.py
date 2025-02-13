# -*- coding: utf-8 -*-
from odoo import api, fields, models
import requests, json
import logging
_logger = logging.getLogger(__name__)

class pos_config(models.Model):
    _inherit = 'pos.config'

    aimag_district_id = fields.Many2one('ebarimt.aimag.district', string="Aimag/District", help="This Aimag/District will be assigned by default on new EBarimt put operation.")
    branch_no = fields.Char(string="Branch No", required=True, default="001")
    pos_no = fields.Char(string="POS No", required=True, default="0001")

    @api.model
    def get_partner_info(self, vat):
        resp = requests.get("http://info.ebarimt.mn/rest/merchant/info?regno=" + vat)
        resp_json = json.loads(resp.text)
        data = {}
        data['name'] = resp_json['name']
        return data
