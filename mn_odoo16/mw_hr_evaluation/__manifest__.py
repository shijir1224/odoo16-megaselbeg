# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'MW HR Evaluation',
    'version': '1.0.1',
    'category': 'MW Human evaluation',
    'sequence': 20,
    'author': 'Nandinzaya Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Үнэлгээ модуль
                - Үнэлгээний үзүүлэлтүүд
                    - Үнэлгээ -- Тохиргоо -- Үзүүлэлтүүд
                - Үнэлгээ тохируулах
                    - Үнэлгээ -- Тохиргоо -- Албан тушаал
                - Үнэлгээ татах
                    - Үнэлгээ -- Үнэлгээ татах
                - Үнэлгээ өгөх
                    - Үнэлгээ -- Үнэлгээ өгөх
                    """,
    'depends': ['hr','mw_hr'],
    'data': [
        'security/hr_evaluation_security.xml',   
        'security/ir.model.access.csv', 
        'views/hr_evaluation_view.xml',
        'wizard/evaluation_report_view.xml',
    ],
    'license': 'OPL-1',
    'website': 'http://managewall.mn',
    'installable': True,
}
