import datetime
import logging

import requests
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from requests.auth import HTTPBasicAuth

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    qpay_url = fields.Char('Url')
    qpay_username = fields.Char('Username')
    qpay_password = fields.Char('Password')
    qpay_token_type = fields.Char('Token type')
    qpay_refresh_expires_in = fields.Integer('Refresh token expires in')
    qpay_refresh_token = fields.Char('Refresh token')
    qpay_access_token = fields.Char('Access token')
    qpay_expires_in = fields.Integer('Expires in')
    qpay_invoice_code = fields.Char('Invoice code')
    

    def qpay_get_token(self, basic_auth=False):
        self.ensure_one()
        url = self.qpay_url
        if not url:
            raise UserError('Qpay url тохируулагдаагүй байна.')

        token = ''
        now = int(datetime.datetime.now().timestamp())
        if basic_auth:
            headers = {
                'Authorization': 'Basic QUdVTEFfREFBVEdBTDowWEVPVE1RaQ==',
            }
            if not self.qpay_username or not self.qpay_password:
                return {
                    'status': 'error',
                    'message': 'Qpay username, password not set!'
                }
            response = requests.post(
                url + 'auth/token', auth=HTTPBasicAuth(self.qpay_username, self.qpay_password))
            json_response = response.json()
            self.qpay_token_type = json_response['token_type']
            self.qpay_refresh_expires_in = json_response['refresh_expires_in']
            self.qpay_refresh_token = json_response['refresh_token']
            self.qpay_access_token = json_response['access_token']
            token = json_response['access_token']
            self.qpay_expires_in = json_response['expires_in']
            _logger.info('==================================== qpay token avav')
        else:
            if self.qpay_access_token and self.qpay_expires_in > now:
                _logger.info('==================================== qpay token baigaag ashiglav')
                token = self.qpay_access_token
            elif self.qpay_refresh_token and self.qpay_refresh_expires_in > now:
                headers = {
                    'Authorization': 'Bearer ' + self.qpay_refresh_token
                }
                response = requests.post(url + 'auth/refresh', headers=headers)
                json_response = response.json()
                self.qpay_token_type = json_response['token_type']
                self.qpay_refresh_expires_in = json_response['refresh_expires_in']
                self.qpay_refresh_token = json_response['refresh_token']
                self.qpay_access_token = json_response['access_token']
                token = json_response['access_token']
                self.qpay_expires_in = json_response['expires_in']
                _logger.info('==================================== qpay token refresh hiiv')
            else:
                headers = {
                    'Authorization': 'Basic QUdVTEFfREFBVEdBTDowWEVPVE1RaQ==',
                }
                if not self.qpay_username or not self.qpay_password:
                    return {
                        'status': 'error',
                        'message': 'Qpay username, password not set!'
                    }
                response = requests.post(
                    url + 'auth/token', auth=HTTPBasicAuth(self.qpay_username, self.qpay_password))
                json_response = response.json()
                self.qpay_token_type = json_response['token_type']
                self.qpay_refresh_expires_in = json_response['refresh_expires_in']
                self.qpay_refresh_token = json_response['refresh_token']
                self.qpay_access_token = json_response['access_token']
                token = json_response['access_token']
                self.qpay_expires_in = json_response['expires_in']
                _logger.info('==================================== qpay token avav')
        return token
