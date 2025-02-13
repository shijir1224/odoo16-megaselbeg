# -*- coding: utf-8 -*-

{
	'name': 'Equipment on Other expense',
	'version': '1.1',
	'sequence': 34,
	'category': 'Repair',
	'license': 'LGPL-3',
	'website': 'http://manangewall.mn',
	'author': 'Managewall LLC Badaam',
	'description': """
		БМ-ын шаардах дээр тоног төхөөрөмж сонгодог болгох """,
	'depends': ['mw_stock_moves','mw_factory_equipment', 'mw_stock_moves_technic'],
	'summary': '',
	'data': [
		'views/stock_product_expense_inherit_view.xml',
	],
	'installable': True,
	'application': False,
}
