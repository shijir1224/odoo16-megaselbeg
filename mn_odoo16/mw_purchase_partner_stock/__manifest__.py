# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Partner Stock',
	'version': '1.0',
	'license': 'LGPL-3',
	'sequence': 32,
	'category': 'Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Main managewall purchase partner""",
	'depends': [
		'purchase',
		'purchase_stock',
	],
	'summary': '',
	'data': [
		"views/purchase_order_views.xml",
	],
	'installable': True,
	'application': False,
}
