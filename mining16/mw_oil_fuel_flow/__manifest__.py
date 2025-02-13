# -*- coding: utf-8 -*-

{
	'name': 'mw oil fuel with dynamic flow',
	'version': '1.0',
	'sequence': 31,
	'category': 'Mining',
	'license': 'LGPL-3',
	'website': 'http://manangewall.mn',
	'author': 'Managewall LLC Bayasa',
	'description': """
		Түлшний зарцуулалтын модуль урсгал тохиргоо нэмэгдсэн""",
	'depends': ['mw_oil_fuel','mw_dynamic_flow'],
	'summary': '',
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/oil_fuel_view.xml',
	],
	'installable': True,
	'application': True,
	'qweb': ['static/xml/*.xml'],
}
