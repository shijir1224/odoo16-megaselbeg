# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': ' HR API',
    'version': '1.0.1',
    'category': 'Base',
    'sequence': 20,
    'author': 'Managewall LLC',
    'license': 'LGPL-3',  # Specify your license here
    'description': "",
    'depends': ['hr','mw_hr_applicant'],
    'data': [
        'security/ir.model.access.csv',     
        'views/send_job_view.xml',     
        ],
    'website': 'http://managewall.mn',
    'installable': True,
}

