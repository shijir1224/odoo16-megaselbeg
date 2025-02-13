# -*- coding: utf-8 -*-
{
	'name': 'Soyolon Stock',
	'version': '1.0',
	'sequence': 31,
	'category': 'Stock',
	'author': 'Manlai Managewall LLC',
	'description': """
		Соёолон Агуулахын модуль
		""",
	'depends': ['stock','mw_stock_confirm','mail','mw_stock_moves','branch','hr','mw_base','mw_stock','mw_purchase_request','mw_factory_equipment', 'mw_stock_product_report'],
	'data': [
		'security/security.xml',
		'security/ir.model.access.csv',
		'reports/product_quality_report_view.xml',
    'reports/product_defective_report.xml',
    'reports/standart_cost_location_report.xml',
		'views/stock_picking.xml',
		'views/stock_warehouse.xml',
		'views/stock_orderpoint_view.xml',
		'views/product_quality_view.xml',
		'views/stock_norm.xml',
		'views/stock_scrap.xml',
		'views/settings.xml',
		'views/menu_view.xml',
	],
	'installable': True,
	'application': False,
	'qweb': [],
}