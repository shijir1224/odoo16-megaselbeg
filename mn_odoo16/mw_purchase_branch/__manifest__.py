# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Branch',
	'version': '1.0',
	'license': 'LGPL-3',
	'sequence': 31,
	'category': 'Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """Main managewall purchase stock branch""",
	'depends': ['branch','purchase'],
	'data': [
		"views/purchase_order_inherit.xml",
	],
	'installable': True,
	'application': False,
}
