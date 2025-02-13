
# -*- coding: utf-8 -*-

{
    'name': 'Соёолон сургалт',
    'version': '1.0',
    'sequence': 20,
    'category': 'Сургалт',
    'author': 'Managewall Tumee',
    'description': """
        Soyolon training  """,
    'depends': ['mw_training', 'mw_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/training_view.xml',
        'views/dev_plan_view.xml',
        'wizard/training_report_view.xml'
    ],
    'installable': True,
    'auto_install': True,
}
