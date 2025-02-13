# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MW HR Org structure',
    'version': '16.0.1.0',
    'license': 'LGPL-3',
    'category': 'MW Human order',
    'sequence': 20,
    'author': 'Puujee Managewall LLC',
    'summary': 'Changed by Mongolian HR',
    'description': """Org straucture
                    """,
    'depends': ['hr','mw_hr'],
    'data': [
        'security/security.xml',   
        'security/ir.model.access.csv', 
        'views/hr_org_structure_view.xml',
        'views/hr_department_view.xml',
        'views/hr_job_view.xml',
    ],

    'website': 'http://managewall.mn',
    'installable': True,
}
