{
	'name' : 'Mw Mobile sales',
	'version' : '2.0',
	'license': 'LGPL-3',
	'summary': 'Orders, transfer from Mobile',
	'sequence': 22,
	'description': """
Mobile module
====================
	""",
	'category': 'Tools',
	'website': 'http://managewall.mn',
	'author': 'Managewall LLC by Amaraa',
	'depends' : ['product','base','account','sale','mw_sales_master_plan',
				 'mw_salesman_route_planner','mw_sales_contract_promotion',
				 'mw_sale_ebarimt'],
	'data': [
		'security/ir.model.access.csv',
		'views/mw_mobile_view.xml',
		'views/res_partner_inherit_view.xml',
		'views/res_users_inherit_view.xml',
		'views/res_user_location.xml',
		'views/sale_order_inherit_view.xml',
	],
	'installable': True,
	'application': True,
	'auto_install': False,
	'pre_init_hook': 'pre_init_check',
} 
