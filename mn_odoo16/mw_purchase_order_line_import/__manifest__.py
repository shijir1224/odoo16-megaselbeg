# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'MW Purchase Order Line Import',
	'version': '1.0.1',
	'license': 'LGPL-3',
	'category': 'Purchase order',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Changed by Mongolian Purchase order',
	'description': "",
	'depends': ['purchase','mw_purchase'],
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/po_line_import_view.xml'
	],
	'qweb': [],
	'website': 'http://managewall.mn',
	'installable': True,
	'auto_install': False,
}
