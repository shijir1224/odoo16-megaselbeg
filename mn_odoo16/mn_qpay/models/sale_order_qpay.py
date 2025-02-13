import json
import logging

import requests
from odoo import fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


QPAY_TOKEN = 'https://merchant.qpay.mn/v2/auth/token'
QPAY_BILL_CREATE = 'https://merchant.qpay.mn/v2/invoice'
QPAY_CHECK = 'https://merchant.qpay.mn/v2/payment/check'
QPAY_TOKEN_REFRESH = "https://merchant.qpay.mn/v2/auth/refresh"

class SaleOrder(models.Model):
	_inherit = 'sale.order'

	qpay_line_ids = fields.One2many('qpay.sale.order.line', 'order_id', string='QPay payments')

class QpaySaleOrderLine(models.Model):
	_name = 'qpay.sale.order.line'
	_description = "Qpay line Entry"

	name = fields.Char('Name')
	qpay_amount = fields.Float('Дүн')
	qpay_invoice_id = fields.Char('Qpay invoice id')
	qpay_qr_text = fields.Char('Qpay QR text')
	qpay_qr_image = fields.Image('Qpay QR image')
	qpay_short_url = fields.Char('Qpay short url')
	qpay_data = fields.Text('Qpay data')
	qpay_check_data = fields.Char('Qpay check data')
	qpay_payment_status = fields.Char('Payment status')
	order_id = fields.Many2one(comodel_name='sale.order',string='SO',copy=False,)


	def generate_qpay(self):
		if self.qpay_invoice_id:
			raise UserError('Qpay үүссэн байна.')

		order_id = self.order_id
		company_id = order_id.company_id
		url = company_id.qpay_url + ('/' if company_id.qpay_url[-1] != '/' else '')
		invoice_code = company_id.qpay_invoice_code

		invoice_number = self.order_id.name
		invoice_receiver_code = order_id.partner_id.vat
		if not invoice_receiver_code:
			invoice_receiver_code='83'
		payload = json.dumps({
			'invoice_code': invoice_code,
			'sender_invoice_no': invoice_number,
			'invoice_receiver_code': invoice_receiver_code,
			'invoice_description': invoice_number,
			'amount': self.qpay_amount,
		})
		token = company_id.qpay_get_token()
		headers = {
			'Authorization': 'Bearer ' + token,
			'Content-Type': 'application/json',
		}
		response = requests.post(url + 'invoice', headers=headers, data=payload)
		if response.status_code == 401:
			token = company_id.qpay_get_token(basic_auth=True)
			headers = {
				'Authorization': 'Bearer ' + token,
				'Content-Type': 'application/json',
			}
			response = requests.post(url + 'invoice', headers=headers, data=payload)
		if not response.status_code == 200:
			raise UserError('Qpay нэхэмжлэх үүсгэх явцад алдаа гарлаа. {}.'.format(response.status_code))
		json_response = response.json()
		self.qpay_invoice_id = json_response['invoice_id']
		self.qpay_qr_text = json_response['qr_text']
		self.qpay_qr_image = json_response['qr_image']
		self.qpay_short_url = json_response['qPay_shortUrl']
		self.qpay_data = str(json_response)
		return True


	def qpay_check(self):
		order_id = self.order_id
		company_id = order_id.company_id
		url = company_id.qpay_url + ('/' if company_id.qpay_url[-1] != '/' else '')
		invoice_code = company_id.qpay_invoice_code

		invoice_number = self.name
		invoice_receiver_code = order_id.partner_id.vat
		payload = json.dumps({
			'invoice_code': invoice_code,
			'sender_invoice_no': invoice_number,
			'invoice_receiver_code': invoice_receiver_code,
			'invoice_description': invoice_number,
			'amount': self.qpay_amount,
		})
		token = company_id.qpay_get_token()
		headers = {
			'Authorization': 'Bearer ' + token,
			'Content-Type': 'application/json',
		}
		
		payload = json.dumps({
		"object_type": "INVOICE",
		"object_id": self.qpay_invoice_id,
		"offset": {
			"page_number": 1,
			"page_limit": 100
		}
		})
		headers = {
				'Content-Type': 'application/json',
				'Authorization': 'Bearer '+token
		}
		response = requests.request("POST", QPAY_CHECK, headers=headers, data=payload)
		self.qpay_check_data = str(response.text)
		if 'error' in response.text:
			ss = response.text
		else:
			ss = json.loads(response.text)
			for rowsdata in ss['rows']:
	   			self.qpay_payment_status = rowsdata['payment_status']