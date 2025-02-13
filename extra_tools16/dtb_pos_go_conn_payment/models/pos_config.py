# coding: utf-8
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PosOrderInherit(models.Model):
    _inherit = "pos.order"

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        fields = super(PosOrderInherit, self)._payment_fields(order, ui_paymentline)

        fields.update({
            'is_go_conn': ui_paymentline.get('is_go_conn'),
            'go_conn_amount': ui_paymentline.get('go_conn_amount'),
            'go_conn_db_ref_no': ui_paymentline.get('go_conn_db_ref_no'),
            'go_conn_textresponse': ui_paymentline.get('go_conn_textresponse'),
            'go_conn_resp_code': ui_paymentline.get('go_conn_resp_code'),
            'go_conn_rrn': ui_paymentline.get('go_conn_rrn'),
            'go_conn_aid': ui_paymentline.get('go_conn_aid'),
            'go_conn_pan': ui_paymentline.get('go_conn_pan'),
            'go_conn_model': ui_paymentline.get('go_conn_model'),
            'go_conn_trace_no': ui_paymentline.get('go_conn_trace_no'),
            'go_conn_terminal_id': ui_paymentline.get('go_conn_terminal_id'),
        })

        return fields


class PosPaymentInherit(models.Model):
    _inherit = 'pos.payment'

    is_go_conn = fields.Boolean('Is Go conn', default=False)
    go_conn_amount = fields.Char('Amount')
    go_conn_db_ref_no = fields.Char('db ref no')
    go_conn_resp_code = fields.Char('Resp code')
    go_conn_rrn = fields.Char('RRN')
    go_conn_textresponse = fields.Char('resp text')
    go_conn_aid = fields.Char('AID')
    go_conn_pan = fields.Char('PAN')
    go_conn_model = fields.Char('Model')
    go_conn_trace_no = fields.Char('trace_no')
    go_conn_terminal_id = fields.Char('terminal_id')