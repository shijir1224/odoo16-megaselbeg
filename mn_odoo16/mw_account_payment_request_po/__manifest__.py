# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'MN Account Payment Request PO',
	'version': '1.0.1',
	'category': 'Accounting',
	'sequence': 20,
	'author': 'Managewall LLC',
	'summary': 'Changed by Mongolian Accounting',
	'description': "",
	'depends': ['mw_account_payment_request','mw_purchase'],
	'data': [
		'views/apr_po.xml',
		],
	'website': 'http://managewall.mn',
	'installable': True,
	'qweb': [],
	'license': 'LGPL-3',
    'icon': '/mw_base/static/src/img/managewall.png',
}
