# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MN Stock Allowed UOMs',
    'version': '1.0.1',
    'category': 'Stock',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Энэ модульд Зөвшөөрөгдсөн Хэмжих нэгжийг бараан дээр тохируулна.',
    'description': "",
    'depends': ['stock','purchase','sale'],
    'data': [
        'views/allow_uom_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'license': 'OPL-1',
}
