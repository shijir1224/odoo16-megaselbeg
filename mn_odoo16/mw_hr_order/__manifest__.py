# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW HR Order',
    'version': '16.0.1.0',
    'license': 'LGPL-3',
    'category': 'MW Human order',
    'sequence': 20,
    'author': 'Solongo Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Хүний нөөцийн модуль
                - Тушаал
                    - Хүний нөөц -- Хөдөлмөрийн харилцаа --Тушаал
                - Тушаалын төрөл
                    - Хүний нөөц -- Хөдөлмөрийн харилцаа --Тушаалын төрөл
                    """,
    'depends': ['hr','mw_hr','base'],
    'data': [
        'security/hr_security.xml',   
        'security/ir.model.access.csv', 
        'views/hr_order_view.xml',
        'views/order_print_view.xml',
        'reports/order_report.xml',
    ],

    'website': 'http://managewall.mn',
    'installable': True,
}
