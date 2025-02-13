    # -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Mongolian Account Currency Equalization",
    'version': '1.0',
    'license': 'LGPL-3',
    'depends': ['mw_account', 'account'],
    'author': "Managewall LLC",
    'category': 'Mongolian Account Modules',
    'description': """ Тайлант хугацааны ханшийн тэгшитгэл
                    - Санхүү -- Санхүү -- Валютын ханшийн тэгшитгэл
                    - Санхүү -- Тохиргоо -- Тохиргоо
   """,
    'website' : 'http://managewall.mn',
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'views/res_config_settings_view.xml',
        'views/account_currency_equalization_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'icon': '/mw_base/static/src/img/managewall.png',
}
