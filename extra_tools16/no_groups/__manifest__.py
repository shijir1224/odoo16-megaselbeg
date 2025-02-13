# -*- encoding: utf-8 -*-

{
	'name': 'No groups, Read only groups',
	'version': '11',
	'license': 'LGPL-3',
	'category': 'Base',
	'description': """
	Slnne Utils

Features
========

1- Add attribute 'no_groups' the same way with 'groups': the field will be invisible for the members of selected groups
2- Add attribute 'readonly-groups' the same way with 'groups': the field will be readonly for the members of selected groups
* This attribute is not working in menuitem tag

*   ...
	<field name="name" no_groups="base.group_hr_user"/>
	<field name="name" readonly-groups="base.group_hr_user"/>
	...

""",
	'author': 'Helmi Dhaoui',
	'price': 0, 
	'currency': 'EUR',
	'licence':'OPL-1',
	'depends': ['base'],
	'images': [
		'static/description/logo.jpg',
	],
	'data': [ 
		'views/menu.xml',
	],
	'auto_install': True,
}
#TODO: must be review
