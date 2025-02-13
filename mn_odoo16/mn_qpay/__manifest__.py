# -*- coding: utf-8 -*-

{
    'name': 'Sale Qpay',
    'version': '1.0',
    'license': 'LGPL-3',
    'sequence': 30,
    'category': 'Sale',
    'website': 'http://managewall.mn',
    'author': 'Managewall LLC by Odka',
    'description': """
        Sale""",
    'depends': ['base','sale','branch'],
    'summary': 'Борлуулалтын Qpay төлөлт',
    'data': [
        "security/qpay_security.xml",
        "security/ir.model.access.csv",
        'views/sale_order_view.xml',
        'views/res_company_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'qweb': [],
}

