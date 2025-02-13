# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval as eval


class AccountAccount(models.Model):
    _inherit ='account.account'

    mobile_receivable = fields.Boolean('Утасны төлбөр?')
    clotes_receivable = fields.Boolean('Хувцасны төлбөр?')
    payment_receivable = fields.Boolean('Торгууль эсэх?')
    is_employee_recpay = fields.Boolean('Ажилтны авлага?')

class ir_attachment(models.Model):
	_inherit = 'ir.attachment'

	@api.model_create_multi
	def create(self, vals_list):
		# ir.attachment дээр access restriction гараад болохгүй байгаа учир public болгов.
		for vals in vals_list:
			vals.update({'public': True}) 
		return super(ir_attachment, self).create(vals_list)
	


class GeneralLedgerReportWizard(models.TransientModel):
    _inherit = "general.ledger.report.wizard"

    foreign_currency = fields.Boolean(
        string="Валют харуулах",
        default=True,
    )
