# -*- coding: utf-8 -*-

from odoo import models, fields
import ctypes
import json
from datetime import date, datetime
from odoo.exceptions import UserError
from odoo.tools.translate import _
import requests
import logging

_logger = logging.getLogger(__name__)

class ebarimt_send(models.Model):
    _name = "ebarimt.send"
    _description = 'Mongolian VAT information exchange'

    def put(self, put_data):
        _logger.info("--- Ebarimt put request: %s", put_data)
        if not self.env.company.vat:
            raise UserError(_('VAT number is False!'))

        url = "%sput?%s" % (self.env.company.ebarimt_endpoint_url, self.env.company.vat)
        _logger.info("--- Ebarimt put URL: %s", url)

        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers, data=put_data, verify=True)
            data = {}
            _logger.info("--- Ebarimt put response status code: %s", response.status_code)
            if response.status_code == 200:
                data = response.json()
                _logger.info("Ebarimt put response json --- : %s", data)
                # p1 = ctypes.c_char_p(put_data.encode('utf-8'))
            else:
                raise UserError(_('Ebarimt connection error! status code: %s' % (response.status_code)))

            if not data.get('success'):
                # if data not in 'success':
                raise UserError(_('Error occurred when putting VAT data. Error code: %s Message: %s') % (
                    data['errorCode'], data['message']))

            if 'lotteryWarningMsg' in data:
                if data['lotteryWarningMsg']:
                    raise UserError(_('Error occurred when putting VAT data: %s') % data['lotteryWarningMsg'])
            return data
        except requests.ConnectionError:
            raise UserError(_('Ebarimt connection error!'))

    def returnBill(self, return_data):
        _logger.info("--- Ebarimt returnBill request: %s", return_data)
        if not self.env.company.vat:
            raise UserError(_('Company VAT number is False!'))

        url = "%sreturnBill?lib=%s" % (self.env.company.ebarimt_endpoint_url, self.env.company.vat)
        _logger.info("--- Ebarimt returnBill URL: %s", url)

        headers = {
            'Content-Type': 'application/json'
        }
        try:
            response = requests.post(url, headers=headers, data=return_data, verify=True)
            data = {}
            _logger.info("--- Ebarimt returnBill response status code: %s", response.status_code)
            if response.status_code == 200:
                data = response.json()
                _logger.info("Ebarimt returnBill response json --- : %s", data)
                # p1 = ctypes.c_char_p(put_data.encode('utf-8'))
            else:
                raise UserError(_('Ebarimt connection error! status code: %s' % (response.status_code)))

            if not data.get('success'):
                # if data not in 'success':
                raise UserError(_('Error occurred when putting VAT data. Error code: %s Message: %s') % (
                    data['errorCode'], data['message']))

            if 'lotteryWarningMsg' in data:
                if data['lotteryWarningMsg']:
                    raise UserError(_('Error occurred when putting VAT data: %s') % data['lotteryWarningMsg'])
            return data
        except requests.ConnectionError:
            raise UserError(_('Ebarimt connection error!'))

