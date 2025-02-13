
# -*- coding: utf-8 -*-

{
    'name': 'MW HR Job conf　',
    'version': '1.0',
    'sequence': 20,
    'category': 'Ажил мэргэжлийн код тохируулах',
    'author': 'Managewall Nandinzaya',
    'description': """
        Ажил мэргэжлийн код тохируулах  """,
    'depends': ['mw_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_job_conf.xml',
    ],
    'installable': True,
    'auto_install': True,
}
