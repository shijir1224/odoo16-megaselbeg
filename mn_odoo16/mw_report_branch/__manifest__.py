# Author: Damien Crier
# Author: Julien Coux
# Copyright 2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'MN Account Financial Reports',
    'version': '1.0.1',
    'category': 'Accounting',
    'sequence': 20,
    'author': 'Daramaa Managewall LLC',
    'summary': 'Changed by Mongolian Accounting',
    'description': "",
    'depends': [
        'branch',
        'account_financial_report',
        'mw_account',
        'stock_account'
    ],
    'data': [
        'wizard/general_ledger_wizard_view.xml',
        'view/branch_view.xml',
        # 'wizard/account_payable_account_detail_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'OPL-1',
}
