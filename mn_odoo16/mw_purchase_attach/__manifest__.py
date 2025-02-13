# -*- coding: utf-8 -*-

{
	'name': 'MW Purchase attach',
	'version': '1.0',
	'license': 'LGPL-3',
	'sequence': 31,
	'category': 'Purchase & Attach Management',
	'author': 'Managewall',
	'description': """
		MW Purchase attach """,
	'depends': ['mw_purchase'],
	'data': [ 
		'security/purchase_security.xml',
		'security/ir.model.access.csv',
		'views/attach_view.xml',
	],
}
