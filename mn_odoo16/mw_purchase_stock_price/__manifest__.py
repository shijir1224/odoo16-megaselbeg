# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Stock Pirce',
	'version': '1.0',
	'license': 'LGPL-3',
	'sequence': 31,
	'category': 'Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		purchase order price hide""",
	'depends': ['purchase','mw_purchase'],
	'summary': '',
	'data': [
		"security/security.xml",
		"views/purchase_order_view.xml",
	],
	'installable': True,
	'application': False,
}
