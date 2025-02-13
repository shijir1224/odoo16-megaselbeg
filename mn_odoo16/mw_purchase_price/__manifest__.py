# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Pirce',
	'version': '1.0',
	'license': 'LGPL-3',
	'sequence': 31,
	'category': 'Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Purchase Order price hide""",
	'depends': ['purchase','mw_purchase','mw_purchase_expense'],
	'summary': '',
	'data': [
		"security/security.xml",
		"views/purchase_order_inherit.xml",
	],
	'installable': True,
	'application': False,
}
