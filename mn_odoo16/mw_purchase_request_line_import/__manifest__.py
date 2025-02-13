# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'MW Purchase Request Line Import',
	'version': '1.0.1',
	'license': 'LGPL-3',
	'category': 'Purchase request',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Changed by Mongolian Purchase order',
	'description': "",
	'depends': ['mw_purchase_request'],
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'views/pr_line_import_view.xml'
	],
	'qweb': [],
	'website': 'http://managewall.mn',
	'installable': True,
	'auto_install': False,
}
