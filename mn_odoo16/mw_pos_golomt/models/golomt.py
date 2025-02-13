# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _

class PosOrder(models.Model):
	_inherit = "pos.order"
	
	@api.model
	def _payment_fields(self, order, ui_paymentline):
		fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)

		fields.update({
			'golomt_status': ui_paymentline.get('golomt_status',False),
			'golomt_textresponse': ui_paymentline.get('golomt_textresponse',False),
			'golomt_pan': ui_paymentline.get('golomt_pan',False),
			'golomt_authorizationcode': ui_paymentline.get('golomt_authorizationcode',False),
			'golomt_terminalid': ui_paymentline.get('golomt_terminalid',False),
			'golomt_merchantid': ui_paymentline.get('golomt_merchantid',False),
			'golomt_amount': ui_paymentline.get('golomt_amount',False),
			'golomt_referencenumber': ui_paymentline.get('golomt_referencenumber',False),
		})

		return fields

# class AccountBankStatementLine(models.Model):
# 	_inherit = 'account.bank.statement.line'

class AccountBankStatementLine(models.Model):
	_inherit = 'pos.payment'

	golomt_status = fields.Char('golomt_status')
	golomt_textresponse = fields.Char('golomt_textresponse')
	golomt_pan = fields.Char('golomt_pan')
	golomt_authorizationcode = fields.Char('golomt_authorizationcode')
	golomt_terminalid = fields.Char('golomt_terminalid')
	golomt_merchantid = fields.Char('golomt_merchantid')
	golomt_amount = fields.Char('golomt_amount')
	golomt_referencenumber = fields.Char('golomt_referencenumber')

class pos_config(models.Model):
	_inherit = 'pos.config'

	golomt_ok = fields.Boolean('Голомт Банк уншигч', default=False)
	golomt_url = fields.Char('Голомт URL', default='http://127.0.0.1:8088/ecrt1000/')
	
class pos_payment_method(models.Model):
	"""docstring for AccountJournal"""
	_inherit = 'pos.payment.method'

	golomt_ok = fields.Boolean('Голомт Банк уншигч', default=False)

	def _get_payment_terminal_selection(self):
		res = super()._get_payment_terminal_selection()
		res.append(("golomt", _("golomt")))
		return res

class pos_session(models.Model):
	"""docstring for AccountJournal"""
	_inherit = 'pos.session'

	golomt_udur_undurluh = fields.Text('Голомт Өдөр өндөрлөх', default='', copy=False, tracking=True, readonly=True)
	golomt_ok = fields.Boolean(related='config_id.golomt_ok', readonly=True)

	def update_golomt_udur_undurluh(self, u):
		self.golomt_udur_undurluh +='\n'+ (str(u) or '')
