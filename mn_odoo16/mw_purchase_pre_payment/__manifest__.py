# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Payment',
	'version': '1.0',
	'license': 'LGPL-3',
	'sequence': 31,
	'category': 'Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Uridchilgaa tuldug module""",
	'depends': [
		'mw_account_payment_request_po', 'mw_purchase_expense', 'account', 'mw_purchase_dynamic_flow'
	],
	'summary': '',
	'data': [
		'security/ir.model.access.csv',
		"views/purchase_views.xml",
		'views/res_config_settings_views.xml',
        'views/account_move.xml',
	],
	'installable': True,
	'application': False,
}
