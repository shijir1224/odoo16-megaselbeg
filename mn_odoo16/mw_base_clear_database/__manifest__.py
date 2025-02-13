# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'MW Base clear database cron',
    'version': '11.0.1.0.1',
    'category': 'Tools',
    'author': 'Managewall Bayasaa (OCA)',
    'license': 'OPL-1',
    'maintainer': 'ABF OSIELL',
    'website': 'http://www.osiell.com',
    'depends': [
        'base'
    ],
    'data': [
        'views/base_clear_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
