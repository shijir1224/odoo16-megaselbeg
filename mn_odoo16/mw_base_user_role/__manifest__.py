# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'MW User roles',
    'version': '11.0.1.0.1',
    'category': 'Tools',
    'author': 'Managewall Bayasaa (OCA)',
    'license': 'OPL-1',
    'maintainer': 'ABF OSIELL',
    'website': 'http://www.osiell.com',
    'depends': [
        'base_user_role','branch'
    ],
    'data': [
        'security/security.xml',
        'views/role.xml',
    ],
    'installable': True,
    'auto_install': False,
}
