# -*- coding: utf-8 -*-

{
	'name': 'Актны хүсэлт модуль',
	'version': '1.0',
	'sequence': 31,
	'category': 'Technic',
	'license': 'LGPL-3',
	'website': 'http://manangewall.mn',
	'author': 'Managewall LLC Badaam',
	'description': """
		Актны менежмент модуль """,
	'depends': ['mw_technic_equipment','mw_factory_equipment','mw_dynamic_flow'],
	'summary': '',
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		# 'data/retire_request.xml',
		'views/retire_request_view.xml',
		'views/menu_view.xml',
	],
	'installable': True,
	'application': True,
	'assets': {
		'web.assets_frontend': [
		],
		'web.assets_backend': [
		],
		'web.assets_qweb': [
		]
	}
}
