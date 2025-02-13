# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Invoice',
	'version': '1.0',
	'sequence': 31,
	'category': 'Inventory/Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Invoice for purchase order""",
	'depends': [
		'mw_purchase',
	],
	'summary': '',
	'data': [
		"views/res_partner_views.xml",
	],
	'installable': True,
	'application': False,
	'license': 'LGPL-3',
}
