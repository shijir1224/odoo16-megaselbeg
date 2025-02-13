# Copyright 2015 ABF OSIELL <https://osiell.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': "MW Audit Log",
    'version': "11.0.1.0.0",
    'author': "ABF OSIELL,Odoo Community Association (OCA)",
    'license': "AGPL-3",
    'website': "https://github.com/OCA/server-tools/",
    'category': "Tools",
    'depends': [
        'auditlog',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/auditlog_view.xml',
    ],
    'application': True,
    'installable': True,
}
