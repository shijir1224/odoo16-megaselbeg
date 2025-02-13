# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

class PosPaymentMethod(models.Model):
	_inherit = 'pos.payment.method'

	sequence = fields.Integer('Sequence', default=1)

class PosPayment(models.Model):
	_inherit = 'pos.payment'

	method_sequence = fields.Integer(string='Payment Method Sequence', related="payment_method_id.sequence")
	