# -*- coding: utf-8 -*-

{
	'name': 'Technic on Other expense',
	'version': '1.1',
	'sequence': 34,
	'category': 'Repair',
	'license': 'LGPL-3',
	'website': 'http://manangewall.mn',
	'author': 'Managewall LLC amaraa',
	'description': """
		БМ-ын шаардах дээр техник сонгодог болгох """,
	'depends': ['mw_stock_moves','mw_technic_maintenance'],
	'summary': '',
	'data': [
		'views/stock_product_expense_inherit_view.xml',
	],
	'installable': True,
	'application': False,
}
