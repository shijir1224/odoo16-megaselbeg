# -*- coding: utf-8 -*-
##############################################################################
#
#    ManageWall, Enterprise Management Solution    
#    Copyright (C) 2007-2014 ManageWall Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#
#    Email : daramaa26@gmail.com
#    Phone : 976 + 99081691
#
##############################################################################

import time
import odoo.pooler as pooler
import locale
from odoo.report import report_sxw

class print_payment_request(report_sxw.rml_parse):
# class print_payment_request(report_sxw.rml_parse, common_report_header):
    _name = 'report.account.payment.request'

    def __init__(self, cr, uid, name, context):
        super(print_payment_request, self).__init__(cr, uid, name, context=context)
        self.localcontext.update( {
            'time': time,
            'format': self._format,
            'notes': self._notes,
            'note': self._note,
#             'company': self._company
        })
        # print "AAAAAAA"
        self.context= context
        self.cr = cr
        self.uid = uid
        self.pool = pooler.get_pool(cr.dbname)
        self.income_total = {}
        self.expense_total = {}
    
#     def _company(self, obj):
#         print "CCCCCCCCCc"
#         if obj.user_id.company_id :
#             return obj.user_id.company_id.name
#         if obj.department_id.company_id :
#             return obj.department_id.company_id.name
#         company_ids = self.pool.get('res.company').search(self.cr, self.uid, [])
#         if len(company_ids) > 0 :
#             return self.pool.get('res.company').read(self.cr, self.uid, company_ids[0],['name'])['name']
#         return u'Тодорхойгүй'
#         return obj
#     
    def _format(self, value):
        # print "value ",value
        return locale.format("%.2f", value, grouping=True)

    def _notes(self,obj):
        # print "obj ",obj
        name=''
        for i in obj.wkf_note_ids:
#             print i
            if i.name=='Department chiep Verification':
                name+=i.notes  
        # print "name ",name      
        return name

    def _note(self,obj):
        # print "obj ",obj
        name=[]
        for i in obj.wkf_note_ids:
#             print i
            if i.name!='Department chiep Verification':
                name.append(i)  
#         print "name ",name      
        return name

report_sxw.report_sxw(
            'report.account.payment.request',
            'payment.request',
            'addons/l10n_mn_account_payment/report/print_payment_request.rml',
            parser=print_payment_request,
            header=False,
            store=False
)
# report_sxw.report_sxw(
#             'report.bank.statement',
#             'account.bank.statement',
#             'addons/l10n_mn_account/report/bank_statement.rml',
#             parser=cash_and_bank_statement, header="internal"
# )

# report_sxw.report_sxw('report.account.account.balance', 'account.account', 'addons/account/report/account_balance.rml', parser=account_balance, header="internal")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
