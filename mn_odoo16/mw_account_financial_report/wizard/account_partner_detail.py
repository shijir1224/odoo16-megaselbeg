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
        Өглөгийн дансны товчоо
    """
    
    _name = "account.partner.detail_mw"
    _description = "Payable Account Detail"
    _inherit="account.report.mw"
    
    def _get_report_columns(self,):
        res = [
            {"header": _("№"), "field": "number", "width": 9, "type": "char",},
            {"header": _("Огноо"), "field": "date", "width": 15, "type": "date",},
            {"header": _("Баримтын дугаар"), "field": "entry", "width": 15},
            {"header": _("Данс"), "field": "code", "width": 18},
            {"header": _("Харилцагч"), "field": "partner_name", "width": 25},
            {"header": _("Регистер"), "field": "vat", "width": 14},
            {"header": _("Холбогдол"), "field": "ref", "width": 14},
            {"header": _("Ангилал"), "field": "partner_categ", "width": 18},
            {"header": _("Гүйлгээний утга"), "field": "ref_label", "width": 40},
        ]
        res += [{"header": _("Дебит"), "field": "debit","field_initial": "initial_debit","field_final": "final_debit","type": "amount","width": 14,},
                {"header": _("Кредит"),"field": "credit","field_initial": "initial_credit","field_final": "final_credit","type": "amount","width": 14,},
                {"header": _("Үлдэгдэл"),"field": "balance_calc","field_initial": "initial_balance","field_final": "final_balance", "type": "amount","width": 14,},
        ]
        if self.foreign_currency:
            res += [{"header": _("Валютын дүн"),"field": "amount_curr","field_initial": "initial_bal_curr","field_final": "final_bal_curr","type": "amount","width": 14,},
                    {"header": _("Валютаар үлдэгдэл"),"field": "total_bal_curr","field_initial": "initial_bal_curr","field_final": "final_bal_curr","type": "amount","width": 20,},
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


    def write_init(self, report_data,partner_id,account_where):
        # account_where=""
        partner_where=""
        company_where=" "
        filters=""
        if partner_id:
            partner_where+=''' AND partner_id ={0}
            '''.format(partner_id)
        # if account_id:
        #     partner_where+=''' AND account_id = {0}
            # '''.format(account_id)
        query='''SELECT sum(debit-credit) as balance_calc,
                'Эхний үлдэгдэл'  as ref_label,
                '' as partner_categ,
                sum(amount_currency) as amount_curr,
                partner_name
            FROM mw_account_report 
            WHERE  state='posted' AND date  <'{0}' '''.format(self.date_from, self.date_to) +" \
             " + account_where + " "+ partner_where +" "+ company_where+" " + filters + " group by partner_name "
        print ('query2222 ',query)
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        for line in res:
            for col_pos, column in report_data["columns"].items():
                format=report_data["formats"]["format_amount_bold"]
                if line.get(column["field"],False):
                    report_data["sheet"].write(report_data["row_pos"],col_pos,line[column["field"]],format,)
                else:
                    report_data["sheet"].write(report_data["row_pos"],col_pos,'',format,)
                    
            report_data["row_pos"] += 1
            

    def write_final(self, report_data,partner_id,account_where): #account_id):
        # account_where=""
        partner_where=""
        company_where=" "
        filters=""
        if partner_id:
            partner_where+=''' AND partner_id ={0}
            '''.format(partner_id)
        # if account_id:
        #     partner_where+=''' AND account_id = {0}
        #     '''.format(account_id)
        query='''SELECT sum(debit-credit) as balance_cal,sum(debit) as debit,sum(credit) as credit,
                'ДЭД ДҮН'  as ref_label,
                '' as partner_categ
            FROM mw_account_report 
            WHERE  state='posted' AND date  <='{1}' '''.format(self.date_from, self.date_to) +" \
             " + account_where + " "+ partner_where +" "+ company_where+" " + filters + " "
        print ('query333 ',query)
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        for line in res:
            for col_pos, column in report_data["columns"].items():
                format=report_data["formats"]["format_amount_bold"]
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
            partner_where+=''' AND partner_id in ({0}) 
            '''.format(','.join(map(str, self.partner_ids.ids)))
        # else:
        #     raise UserError((u'Харилцагч сонгоно уу.'))            
        if self.account_ids:
            account_where+=''' AND account_id in ({0}) 
            '''.format(','.join(map(str, self.account_ids.ids)))
        else:
            account_ids=self.env['account.account'].search([("account_type", "in", ("asset_receivable", "liability_payable"))])
            account_where+=''' AND account_id in ({0}) 
            '''.format(','.join(map(str, account_ids.ids)))
        if self.show_reconciled:
            reconciled_where+=''' AND reconciled = False'''
            
        query='''SELECT * ,1 as number, (select unnest(ARRAY_AGG(c.name  -> 'en_US')) from res_partner_res_partner_category_rel r left join res_partner_category c on r.category_id=c.id where r.partner_id=ma.partner_id group by r.partner_id) as partner_categ
            FROM mw_account_report ma
            WHERE state='posted' AND date between '{0}' and '{1}' '''.format(self.date_from, self.date_to) +" \
             " + account_where + " "+ partner_where +" "+ company_where +" " + reconciled_where +" " + filters + "  order by date, id "
        print ('query ',query)
        self._cr.execute(query)
        res = self._cr.dictfetchall()
        parter_check=[]
        account_check=[]

        index=1
        check=0
        
        # print ('res ',res)
        cpartners=[]
        count=self._count_grouped(res)
        if self.with_balance:
            for cl in res:
                cpartners.append(cl['partner_id'])
            for part in self.partner_ids.ids:
                if part not in cpartners:
                    self.write_init(report_data,part,account_where)
                    self.write_final(report_data,part,account_where)
                
        for line in res:
            umnuh=False
            if line['partner_id'] not in parter_check:
                index=1
                parter_check.append(line['partner_id'])
                # self.write_init(report_data,line['partner_id'],line['account_id'],)
                self.write_init(report_data,line['partner_id'],account_where,)
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
                                                           + self._symbol(report_data["row_pos"],col_pos-2) +'-'\
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
            if count.get(line['partner_id'],False) and count[line['partner_id']]==check  :  
                parter_check.append(line['partner_id'])
                # self.write_final(report_data,line['partner_id'],line['account_id'],)
                self.write_final(report_data,line['partner_id'],account_where)                
                # report_data["row_pos"] += 1        

            