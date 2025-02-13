# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

ACCOUNT_DOMAIN = "['&', '&', '&', ('deprecated', '=', False), ('account_type', 'not in', ('asset_receivable','liability_payable','asset_cash','liability_credit_card')), ('company_id', '=', current_company_id), ('is_off_balance', '=', False)]"

class ProductCategory(models.Model):
	_name = "product.category"
	_inherit = ['product.category','mail.thread']
	
	company_id = fields.Many2one('res.company', 'Company')
	code = fields.Char('Код')
	possible_to_choose = fields.Boolean(string='Бараан дээр сонгох боломжтой эсэх', default=True)

	property_stock_account_input_categ_id = fields.Many2one(
		'account.account', 'Stock Input Account', company_dependent=True, tracking=True,
		domain="[('company_id', '=', allowed_company_ids[0]), ('deprecated', '=', False)]", check_company=True,
		help="""Counterpart journal items for all incoming stock moves will be posted in this account, unless there is a specific valuation account
				set on the source location. This is the default value for all products in this category. It can also directly be set on each product.""")
	property_stock_account_output_categ_id = fields.Many2one(
		'account.account', 'Stock Output Account', company_dependent=True, tracking=True,
		domain="[('company_id', '=', allowed_company_ids[0]), ('deprecated', '=', False)]", check_company=True,
		help="""When doing automated inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account,
				unless there is a specific valuation account set on the destination location. This is the default value for all products in this category.
				It can also directly be set on each product.""")
	property_stock_valuation_account_id = fields.Many2one(
		'account.account', 'Stock Valuation Account', company_dependent=True, tracking=True,
		domain="[('company_id', '=', allowed_company_ids[0]), ('deprecated', '=', False)]", check_company=True,
		help="""When automated inventory valuation is enabled on a product, this account will hold the current value of the products.""",)
	property_account_income_categ_id = fields.Many2one('account.account', company_dependent=True, tracking=True, string="Income Account",
		domain=ACCOUNT_DOMAIN, help="This account will be used when validating a customer invoice.")
	property_account_expense_categ_id = fields.Many2one('account.account', company_dependent=True, tracking=True, string="Expense Account",
		domain=ACCOUNT_DOMAIN, help="The expense is accounted for when a vendor bill is validated, except in anglo-saxon accounting with perpetual inventory valuation in which case the expense (Cost of Goods Sold account) is recognized at the customer invoice validation.")
