{
  "name": "MW Stock Additional Report",
  "version": "1.0",
  'license': 'LGPL-3',
  "author": "MW Badaam",
  "description": """MW Stock REPORT stock check & interal move""",
  "category": "mak",
  "depends": ['mw_stock','mw_stock_product_report'],
  "init": [],
  "data": [
    'security/security.xml',
    'security/ir.model.access.csv',
    'wizard/stock_internal_report_view.xml',
    'wizard/stock_check_report_view.xml',
  ],
  "active": False,
  "installable": True,
  "application": True,
}
