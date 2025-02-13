# pylint: disable=missing-docstring
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
	'name': 'MW Web Notify',
	'summary': """
		Send notification messages to user""",
	'version': '13.0.1.0.1',
	'license': 'OPL-1',
	'author': 'ACSONE SA/NV,'
			  'AdaptiveCity,'
			  'Odoo Community Association (OCA)',
	'website': 'https://github.com/OCA/web',
	'depends': [
		'web_notify',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/template_view.xml',
		'views/mw_notify_view.xml',
	],
	'assets': {
		'web.assets_backend': [
			'mw_web_notify/static/src/js/notify.js',
		]
	},
	'demo': [],
	'qweb': ['static/src/xml/notify.xml'],
	'installable': True,
}
