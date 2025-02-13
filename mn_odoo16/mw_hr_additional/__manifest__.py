# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW HR Additional',
    'version': '16.0.1.0',
    'license': 'LGPL-3',
    'category': 'MW Human resourse',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Хүний нөөцийн модульд нэмэлт
                - Хувийн хуудас
                    - Хувийн хуудас -- Миний мэдээлэл
                - Хүний нөөц
                    - Хүний нөөц  -- Хүний нөөц-- Хүний нөөц
                    """,
    'depends': ['hr', 'mw_hr',],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_additional_view.xml',
    ],
    'website': 'http://managewall.mn',
    'installable': True,
}
