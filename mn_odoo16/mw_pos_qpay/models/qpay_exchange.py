# -*- coding: utf-8 -*-
from odoo import api, models, fields
import json
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError
from odoo.tools.translate import _
import requests
import logging

_logger = logging.getLogger(__name__)
RECUSIVE_COUNT_LIMIT = 4


class QpayExchange(models.Model):
    _name = "qpay.exchange"
    _description = 'QPay exchange'

    """
    QPAY V2 дээр refresh токен ашиглах шаардлагагүй 24 цагт нэг удаа access токен авахад болно гэсэн.
    """

    def check_and_update_qpay_access_token(self):
        if not self.env.company.access_token_expire_datetime or self.env.company.access_token_expire_datetime < datetime.now():  # access token хугацаа дууссан гэсэн үг
            # try:
            #     self.check_and_update_qpay_refresh_token()
            # except UserError as e:
            #     _logger.info('Error updating qpay refresh token : {0}'.format(e))
            self.login()
        return True

    def check_and_update_qpay_refresh_token(self):
        """
        QPAY V2 дээр refresh токен ашиглах шаардлагагүй 24 цагт нэг удаа access токен авахад болно гэсэн тэгэхээр ашиглагдахгүй байгаа.
        :return:
        """
        res = self.refresh_token(self.env.company.qpay_refresh_token)
        qpay_vals = {
            'qpay_access_token': res.get('access_token'),
            'qpay_refresh_token': res.get('refresh_token'),
            'refresh_token_expire_datetime': datetime.fromtimestamp(res.get('refresh_expires_in')),
            'access_token_expire_datetime': datetime.fromtimestamp(res.get('expires_in')),
        }
        self.env.company.sudo().write(qpay_vals)

    def login(self):
        '''
        QPAY логин функц
        :return:
        '''
        _logger.info("---- QPay login service request: %s", self.env.user.login)
        try:
            login_base_url = self.env.company.qpay_login_url
            response = requests.post(login_base_url, auth=(self.env.company.qpay_username, self.env.company.qpay_password), verify=True)
            if response.status_code == 200:
                _logger.info("---- QPay login service success, status code: %s" % response.status_code)
                res = response.json()
                qpay_vals = {
                    'qpay_access_token': res.get('access_token'),
                    'qpay_refresh_token': res.get('refresh_token'),
                    'refresh_token_expire_datetime': datetime.fromtimestamp(res.get('refresh_expires_in')),
                    'access_token_expire_datetime': datetime.fromtimestamp(res.get('expires_in')),
                }
                self.env.company.sudo().write(qpay_vals)
                self._cr.commit()
            else:
                _logger.info("---- QPay login service failed, status code: %s" % response.status_code)
                raise UserError(_('An error occurred while login in to QPay!'))
        except requests.ConnectionError:
            raise UserError(_('An error occurred while login in to QPay!'))

    def refresh_token(self, refresh_token):
        '''
        QPAY token сэргээх функц
        :param refresh_token:
        :return:
        '''
        _logger.info("---- QPay refresh_token, request: %s", self.env.user.login)
        try:
            headers = {'Content-Type': 'application/json',
                       'Authorization': 'Bearer {}'.format(refresh_token)}
            refresh_base_url = self.env.company.qpay_refresh_url
            response = requests.post(refresh_base_url, headers=headers, verify=True)

            if response.status_code == 200:
                _logger.info("---- QPay refresh_token success, status code: %s" % response.status_code)
                return response.json()
            else:
                _logger.info("---- QPay refresh_token failed, status code: %s" % response.status_code)
                raise UserError(_('An error occurred while refresh_token in to QPay!'))
        except requests.ConnectionError:
            raise UserError(_('An error occurred while refresh_token in to QPay!'))

    @api.model
    def create_invoice(self, order_name, config_id, amount=0, rec_count=0, previous_response=''):
        """
        Нэхэмжлэх үүсгэх үйлдэл, recusive байдлаар Дээд талдаа RECUSIVE_COUNT_LIMIT удаа давтана.
        :param order_name: Захиалгын дугаар
        :param config_id: pos.config ID
        :param amount: Дүн
        :param rec_count: recusive үйлдлийн дугаар
        :param previous_response: Өмнөх үйлдлийн алдааны мэдээлэл
        :return:
        """
        if rec_count:
            if rec_count > RECUSIVE_COUNT_LIMIT:
                raise UserError(_('QPay invoice create error! message: %s' % previous_response))
            _logger.info("---- Trying to send qpay invoice again %s: %s %s %s" % (rec_count, order_name, config_id, amount))
        else:
            _logger.info("---- QPay create invoice, %s, %s, %s" % (order_name, config_id, amount))
        pos_config = self.env['pos.config'].browse(config_id)
        po_name = pos_config.name + "(" + order_name + ")"
        bill_num = "{}, {}/{}".format(pos_config.name, order_name, datetime.now().microsecond)

        body = {
            "invoice_code": self.env.company.qpay_invoice_code,
            "sender_invoice_no": bill_num,
            "invoice_description": po_name,
            "sender_branch_code": pos_config.branch_no,
            "invoice_receiver_code": order_name,
            "amount": amount,
            "callback_url": ""
        }
        self.check_and_update_qpay_access_token()
        headers = {'Content-Type': 'application/json',
                   'Authorization': 'Bearer {}'.format(self.env.company.qpay_access_token)}
        try:
            invoice_base_url = self.env.company.qpay_invoice_create_url
            response = requests.post(invoice_base_url, headers=headers, data=json.dumps(body, indent=2), verify=True)
            if response.status_code == 200:
                response_data = response.json()
                _logger.info("---- QPay create invoice, response success %s" % response_data)
                return {'qr_data': response_data['qr_image'], 'invoice_id': response_data['invoice_id']}
            else:
                _logger.info(_('QPay invoice create error! code: %s, message: %s' % (response.status_code, response.json()['message'])))
                self.login()
                return self.create_invoice(order_name, config_id, amount, rec_count + 1, response.json()['message'])
        except requests.ConnectionError:
            raise UserError(_('QPay Invoice create connection error!'))

    @api.model
    def check_invoice(self, invoice_id):
        _logger.info("---- QPay check_invoice, request %s" % invoice_id)
        body = {
                "object_type": "INVOICE",
                "object_id": invoice_id
        }
        self.check_and_update_qpay_access_token()
        token = self.env.company.qpay_access_token
        if token:
            headers = {'Content-Type': 'application/json',
                       'Authorization': 'Bearer {}'.format(token)}
            try:
                check_invoice_base_url = self.env.company.qpay_invoice_check_url
                response = requests.post(check_invoice_base_url, headers=headers, data=json.dumps(body, indent=2),
                                         verify=True)
                if response.status_code == 200:
                    response_data = response.json()
                    if response_data['count'] > 0:
                        _logger.info("---- QPay check_invoice, response paid %s" % response_data)
                        return {'msg': _('Invoice paid'), 'status': '2'}
                    else:
                        _logger.info("---- QPay check_invoice, response unpiad %s" % response_data)
                        return {'msg': _('Invoice unpaid'), 'status': '0'}
                else:
                    raise UserError(_('QPay check_invoice error! code: %s, message: %s' % (
                        response.status_code, response.json()['message'])))
            except requests.ConnectionError:
                raise UserError(_('QPay check_invoice connection error!'))
