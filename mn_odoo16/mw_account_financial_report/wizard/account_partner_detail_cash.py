# -*- encoding: utf-8 -*-
############################################################################################
#
#    Managewall-ERP, Enterprise Management Solution    
#    Copyright (C) 2007-2017 mw Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
#    $Id:  $
#
#    Менежволл-ЕРП, Байгууллагын цогц мэдээлэлийн систем
#    Зохиогчийн зөвшөөрөлгүйгээр хуулбарлах ашиглахыг хориглоно.
#
#
#
############################################################################################
import time
from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError
from odoo.tools import date_utils
from odoo.addons.account_financial_report.report.report_excel_cell_styles import ReportExcelCellStyles


from io import BytesIO
import xlsxwriter
import base64
try:
    from base64 import encodestring
except ImportError:
    from base64 import encodebytes as encodestring

class AccountPartnerDetail(models.TransientModel):
    """
        Дансны дэлгэрэнгүй мөнгөтэй
    """
    
    _name = "account.partner.detail.cash"
    _description = "Payable Account Detail cash"
    _inherit="account.report.mw"
    
    def _get_report_columns(self,):
        res = [
            {"header": _("№"), "field": "number", "width": 9, "type": "char",},
            {"header": _("Нэр"), "field": "partner_name", "width": 15, "type": "char",},
            {"header": _("Баримтын дугаар"), "field": "entry", "width": 15},
            {"header": _("Бараа "), "field": "product", "width": 35},
            {"header": _("Шинжилгээ"), "field": "analytic", "width": 25},
            {"header": _("Яаралтай/огноо"), "field": "date_maturity", "width": 14, "type": "date",},
            {"header": _("Нийлүүлэгчийн өглөг"), "field": "credit", "width": 14,"type": "amount",},
            {"header": _("Төлөх дүн"), "field": "amount_residual", "width": 14,"type": "amount",},
            {"header": _("Мөнгөн хөрөнгийн үлдэгдэл"), "field": "balance_calc", "type": "amount","width": 14,}
        ]
        res_as_dict = {}
        for i, column in enumerate(res):
            res_as_dict[i] = column
        return res_as_dict

    def mw_xlsx_report(self, workbook, data, wizard,sheet_name):
        sheet = workbook.add_worksheet(sheet_name)
        
        data["sheet"]=sheet
        self.write_array_title(data, u'Харилцагчийн гүйлгээний дэлгэрэнгүй тайлан')
        self.write_array_header(data)
        self.write_array_body(data)


    def write_init(self, report_data):

        search_args = [('account_type', '=', 'asset_cash'),('is_temporary', '=', False)]
        account_dict = {}
        account_ids = self.env['account.account'].search(search_args, order='code')
        start_amount=0
        end_amount=0
        context={}
        context['state'] = 'posted'
        context['date_from'] = self.date_from
        # context['date_to'] = date_end
        context['company_id'] = self.company_id.id
        context['return_initial_bal_journal'] = True        
        for account_id in account_ids:
            account_br=account_id.with_context(context) 
            start_amount += account_br.balance_start
            end_amount += account_br.balance  
        for col_pos, column in report_data["columns"].items():
            format=report_data["formats"]["format_center_bold"]
            if start_amount and col_pos==8:
                report_data["sheet"].write(report_data["row_pos"],col_pos,start_amount,format,)
            else:
                report_data["sheet"].write(report_data["row_pos"],col_pos,'',format,)
                
        report_data["row_pos"] += 1
                        

    def write_final(self, report_data,partner_id,account_id):
        account_where=""
        partner_where=""
        company_where=" "
        filters=""
        if partner_id:
            partner_where+=''' AND partner_id ={0}
            '''.format(partner_id)
        if account_id:
            partner_where+=''' AND account_id = {0}
            '''.format(account_id)
        query='''SELECT sum(debit-credit) as balance_cal,sum(debit) as debit,sum(credit) as credit,
                'ДЭД ДҮН'  as ref_label,
                '' as partner_categ
            FROM mw_account_report 
            WHERE  state='posted' AND date  <='{1}' '''.format(self.date_from, self.date_to) +" \
             " + account_where + " "+ partner_where +" "+ company_where+" " + filters + " "
        # print ('query333 ',query)
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        for line in res:
            for col_pos, column in report_data["columns"].items():
                format=report_data["formats"]["format_center_bold"]
                if line.get(column["field"],False):
                    report_data["sheet"].write(report_data["row_pos"],col_pos,line[column["field"]],format,)
                else:
                    report_data["sheet"].write(report_data["row_pos"],col_pos,'',format,)
                    
            report_data["row_pos"] += 1            

        
    def write_array_body(self, report_data):
        account_where=""
        partner_where=""
        company_where=" "
        reconciled_where=""
        filters=""
        if self.partner_ids:
            partner_where+=''' AND ma.partner_id in ({0}) 
            '''.format(','.join(map(str, self.partner_ids.ids)))
        else:
            raise UserError((u'Харилцагч сонгоно уу.'))            
        if self.account_ids:
            account_where+=''' AND ma.account_id in ({0}) 
            '''.format(','.join(map(str, self.account_ids.ids)))
        else:
            account_ids=self.evn['account.account'].search([("account_type", "in", ("asset_receivable", "liability_payable"))])
            account_where+=''' AND ma.account_id in ({0}) 
            '''.format(','.join(map(str, account_ids.ids)))
        if self.show_reconciled:
            reconciled_where+=''' AND reconciled = True'''
            
        query='''SELECT l.amount_residual,l.date_maturity,l.credit ,1 as number,
        partner_name,entry,ma.partner_id,ma.account_id,
            (select name from product_product where id in (select product_id from account_move_line where move_id=l.move_id) limit 1) as product,
            '' as analytic
            FROM mw_account_report ma left join account_move_line l on ma.id=l.id
            WHERE state='posted' AND ma.date between '{0}' and '{1}' '''.format(self.date_from, self.date_to) +" \
             " + account_where + " "+ partner_where +" "+ company_where +" " + reconciled_where +" " + filters + "  order by ma.date, ma.id "
                          
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        parter_check=[]
        account_check=[]

        index=1
        check=0
        
        # print ('res ',res)
        count=self._count_grouped(res)
        for line in res:
            umnuh=False
            if line['partner_id'] not in parter_check:
                index=1
                parter_check.append(line['partner_id'])
                self.write_init(report_data)
                check=0
            check+=1
            for col_pos, column in report_data["columns"].items():
                format=report_data["formats"]["format_left"]
                if column.get("type","char")=="date":
                    format=report_data["formats"]["format_date"]
                if column.get("type","char")=="amount":
                    format=report_data["formats"]["format_amount"]
                if line.get(column["field"],False) or column["field"]=="balance_calc":
                    if column["field"]=="balance_calc":
                        report_data["sheet"].write_formula(report_data["row_pos"],col_pos,'{=sum('+ self._symbol(report_data["row_pos"]-1,col_pos)+'+'\
                                                           + self._symbol(report_data["row_pos"],col_pos-1) +\
                                                           ')}', format)
                    elif column["field"]=="number":
                        report_data["sheet"].write(report_data["row_pos"],col_pos,index,format,)
                        index+=1
                    else:
                        report_data["sheet"].write(report_data["row_pos"],col_pos,line[column["field"]],format,)
                else:
                    report_data["sheet"].write(report_data["row_pos"],col_pos,'',format,)
                    
            report_data["row_pos"] += 1   
            # if count.get(line['partner_id'],False) and count[line['partner_id']]==check  :  
            #     parter_check.append(line['partner_id'])
            #     self.write_final(report_data,line['partner_id'],line['account_id'],)

            