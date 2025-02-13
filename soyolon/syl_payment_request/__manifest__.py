# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'SYL Payment request',
    'version': '1.0.1',
    'license': 'LGPL-3',
    'category': 'Payment',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Payment request',
    'description': "",
    'depends': ['mw_account_payment_request','fixed_tree_width_one2many'],
    'data': [
        'views/syl_payment_request_view.xml',
    ],
    'qweb': [],
    'website': 'http://managewall.mn',
    'installable': True,
    'auto_install': False,
    'icon': '/mw_base/static/src/img/managewall.png',
}
