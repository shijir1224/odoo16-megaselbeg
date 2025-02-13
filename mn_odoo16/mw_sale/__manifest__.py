# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW Sale',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Sales',
    'sequence': 21,
    'summary': 'Changed by Mongolian Sale Stock',
    'author': 'Managewall LLC',
    'website': 'http://managewall.mn',
    'description': """Боруулалтын модуль
                - Борлуулалтын захиалга
                    - Нэхэмжлэх харах хуудас
                    - Нэхэмжлэх үлдэгдэл төлбөр болон үүсгэсэн огноо харах
                    - Хайлт хэсгээс нэхэмжлэхийн төлөв болон үлдэгдэл шууд хайх
                    """,
    'depends': [
        'sale', 'sale_management'
    ],
    'data': [
        'security/security.xml',
        'views/sale_order_views.xml',
    ],
    'qweb': [],
    'installable': True,
    'auto_install': False,
}
