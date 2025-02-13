# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class PosOrder(models.Model):
	_inherit = "pos.order"
	
	@api.model
	def _payment_fields(self, order, ui_paymentline):
		fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)

		fields.update({
			'xac_status': ui_paymentline.get('xac_status',False),
			'xac_textresponse': ui_paymentline.get('xac_textresponse',False),
			'xac_pan': ui_paymentline.get('xac_pan',False),
			'xac_authorizationcode': ui_paymentline.get('xac_authorizationcode',False),
			'xac_terminalid': ui_paymentline.get('xac_terminalid',False),
			'xac_merchantid': ui_paymentline.get('xac_merchantid',False),
			'xac_amount': ui_paymentline.get('xac_amount',False),
			'xac_referencenumber': ui_paymentline.get('xac_referencenumber',False),
		})

		return fields

# class AccountBankStatementLine(models.Model):
# 	_inherit = 'account.bank.statement.line'

class AccountBankStatementLine(models.Model):
	_inherit = 'pos.payment'

	xac_status = fields.Char('xac_status')
	xac_textresponse = fields.Char('xac_textresponse')
	xac_pan = fields.Char('xac_pan')
	xac_authorizationcode = fields.Char('xac_authorizationcode')
	xac_terminalid = fields.Char('xac_terminalid')
	xac_merchantid = fields.Char('xac_merchantid')
	xac_amount = fields.Char('xac_amount')
	xac_referencenumber = fields.Char('xac_referencenumber')

class pos_config(models.Model):
	_inherit = 'pos.config'

	xac_ok = fields.Boolean('Хас Банк уншигч', default=False)
	xac_url = fields.Char('Хас URL', default='http://127.0.0.1:8088/ecrt1000/')
	
class pos_payment_method(models.Model):
	"""docstring for AccountJournal"""
	_inherit = 'pos.payment.method'

	xac_ok = fields.Boolean('Хас Банк уншигч', default=False)

	def _get_payment_terminal_selection(self):
		res = super()._get_payment_terminal_selection()
		res.append(("xac", _("Xac")))
		return res

class pos_session(models.Model):
	"""docstring for AccountJournal"""
	_inherit = 'pos.session'

	xac_udur_undurluh = fields.Text('Хас Өдөр өндөрлөх', default='', copy=False, tracking=True, readonly=True)
	xac_ok = fields.Boolean(related='config_id.xac_ok', readonly=True)

	def update_xac_udur_undurluh(self, u):
		self.xac_udur_undurluh +='\n'+ (str(u) or '')
