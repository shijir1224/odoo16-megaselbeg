# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'MW Applicant',
    'version': '16.0.1',
    'license': 'LGPL-3',
    'category': 'HMW Human resourse',
    'sequence': 20,
    'author': 'Managewall LLC',
    'summary': 'Changed by Mongolian hr',
    'description': "",
    'depends': ['hr_recruitment','mw_hr_additional','mw_hr'],
    'data': [
        # 'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/applicant_view.xml',
        ],
        
    'website': 'http://managewall.mn',
    'installable': True,
    # 'auto_install': False,
}
