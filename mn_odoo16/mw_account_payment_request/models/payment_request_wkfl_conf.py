from odoo import models


class PaymentRequestWkflConf(models.Model):
    _name = 'payment.request.wkfl.conf'
    _description = 'Payment Request Conf'


class PaymentRequestWkflConfLine(models.Model):
    _name = 'payment.request.wkfl.conf.line'
    _description = 'Payment Request Conf'
