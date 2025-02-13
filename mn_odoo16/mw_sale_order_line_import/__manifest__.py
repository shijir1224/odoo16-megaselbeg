# -*- coding: utf-8 -*-
{
    'name': 'MW Sale Order Line Import',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Sale order',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian Sale order',
    'description': "",
    'depends': [
        'sale','mw_sale',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/so_line_import_view.xml'
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
}
