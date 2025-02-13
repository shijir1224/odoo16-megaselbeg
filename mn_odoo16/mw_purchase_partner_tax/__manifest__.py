# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase Partner Tax',
	'version': '1.0',
	'license': 'LGPL-3',
	'sequence': 31,
	'category': 'Purchase',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC',
	'description': """
		Main managewall purchase stock""",
	'depends': [
		'mw_purchase',
	],
	'summary': '',
	'data': [
		"views/res_partner_views.xml",
	],
	'installable': True,
	'application': False,
}
