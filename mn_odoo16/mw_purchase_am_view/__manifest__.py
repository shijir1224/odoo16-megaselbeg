# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Invoice',
	'version': '1.0',
	'sequence': 31,
	'category': 'Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Main managewall purchase stock""",
	'depends': ['mw_purchase','mw_purchase_expense'],
	'summary': '',
	'data': [
		"security/security.xml",
		"security/ir.model.access.csv",
		"views/po_am_view.xml",
		"views/menu_view.xml",
	],
	'license': 'LGPL-3',
	'installable': True,
	'application': False,
}
