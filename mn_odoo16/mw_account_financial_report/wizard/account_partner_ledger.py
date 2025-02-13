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

class account_partner_ledger(models.TransientModel):
    """
        Өглөгийн дансны товчоо
    """
    
    _name = "account.partner.ledger_mw"
    _description = "Payable Account Ledger"
    _inherit="account.report.mw"
    
    def _get_report_columns(self,):
        res = [
            {"header": _("№"), "field": "number", "width": 9, "type": "char",},
            {"header": _("Код"), "field": "ref", "width": 15, "type": "date",},
            {"header": _("Нэр"), "field": "name", "width": 20},
            {"header": _("Ангилал"), "field": "category", "width": 15},
        ]
        if self.not_group:
            res += [
                {"header": _("Дансны код"), "field": "account_code", "width": 18, "type": "char"},
                {"header": _("Дансны нэр"), "field": "account_name", "width": 30, "type": "char"},
        ]
        if self.foreign_currency:  
            res += [
                {"header": _("Валют"),"field": "curr_name","type": "amount","width": 14,},
                    {"header": _("Эхний үлдэгдэл"), "field": "field_initial","field_initial": "initial_debit","field_final": "final_debit","type": "amount","width": 14,},
                    {"header": _("Эхний үлдэгдэл /Валют/"),"field": "initial_bal_curr","type": "amount","width": 14,},
                    {"header": _("Дебит"), "field": "debit","field_initial": "initial_debit","field_final": "final_debit","type": "amount","width": 14,},
                    {"header": _("Валют Дт"),"field": "amount_curr_dt","type": "amount","width": 14,},
                    {"header": _("Кредит"),"field": "credit","field_initial": "initial_credit","field_final": "final_credit","type": "amount","width": 14,},
                    {"header": _("Валют Кр"),"field": "amount_curr_cr","type": "amount","width": 14,},
                    {"header": _("Үлдэгдэл "),"field": "balance_calc","field_initial": "initial_balance","field_final": "final_balance", "type": "amount","width": 14,},
                    {"header": _("Үлдэгдэл /Валют/"),"field": "total_bal_curr","type": "amount","width": 14,},
            ]
        else:
            res += [
                {"header": _("Эхний үлдэгдэл"), "field": "field_initial","field_initial": "initial_debit","field_final": "final_debit","type": "amount","width": 14,},
                {"header": _("Дебит"), "field": "debit","field_initial": "initial_debit","field_final": "final_debit","type": "amount","width": 14,},
                {"header": _("Кредит"),"field": "credit","field_initial": "initial_credit","field_final": "final_credit","type": "amount","width": 14,},
                {"header": _("Үлдэгдэл"),"field": "balance_calc","field_initial": "initial_balance","field_final": "final_balance", "type": "amount","width": 14,},
                ]
        # if self.foreign_currency:
        #     res += [
        #         {"header": _("Валют"),"field": "curr_name","type": "amount","width": 14,},
        #             {"header": _("Валют Эхний үлдэгдэл"),"field": "initial_bal_curr","type": "amount","width": 14,},
        #             {"header": _("Валютын дүн"),"field": "amount_curr","type": "amount","width": 14,},
        #             {"header": _("Валютаар үлдэгдэл"),"field": "total_bal_curr","type": "amount","width": 14,},
        #     ]
        res_as_dict = {}
        for i, column in enumerate(res):
            res_as_dict[i] = column
        return res_as_dict

    def mw_xlsx_report(self, workbook, data, wizard,sheet_name):
        sheet = workbook.add_worksheet(sheet_name)
        
        data["sheet"]=sheet
        self.write_array_title(data, u'Харилцагчийн дэвтэр')
        self.write_array_header(data)
        self.write_array_body(data)

    def write_array_body(self, report_data):
        account_where=""
        partner_where=""
        company_where=" "
        filters=""
        partner_ids=[]
        if self.partner_ids:
            partner_ids=self.partner_ids
        else:
            partner_account_ids=self.env['account.move.line'].search([('company_id','in',self.env.user.company_ids.ids)])
            partner_ids=partner_account_ids.mapped('partner_id')
        #     raise UserError((u'Харилцагч сонгоно уу.'))   
        account_ids=[]         
        if self.account_ids:
            account_where+=''' AND account_id in ({0}) 
            '''.format(','.join(map(str, self.account_ids.ids)))
            account_ids=self.account_ids
        else:
            account_ids=self.env['account.account'].search([("account_type", "in", ("asset_receivable", "liability_payable"))])
            account_where+=''' AND account_id in ({0}) 
            '''.format(','.join(map(str, account_ids.ids)))
            
        check=0
            
        index=1
        for partner in partner_ids:
            partner_where=" AND partner_id={}".format(partner.id)
            # print ('partner_where ',partner_where)
            if self.not_group:
                query='''SELECT sum(debit) as debit, sum(credit) as credit,'' as ref, 
                            partner_name as name, code as account_code, 
                            account_name as account_name ,1 as number,
                            account_id,
                            (select sum(debit-credit) from mw_account_report r2 where state='posted' AND date < '{0}' and r2.code=r.code {2} {3} {4} {5} and r2.currency_id=r.currency_id) as field_initial,
                            case when curr_name='MNT' then 0 ELSE (select sum(amount_currency) from mw_account_report r3 where state='posted' AND date < '{0}' and r3.code=r.code {2} {3} {4} {5} and r3.currency_id=r.currency_id) end as initial_bal_curr,
                            case when curr_name='MNT' then 0 ELSE (select sum(amount_currency) from mw_account_report r4 where state='posted' AND date <= '{1}' and r4.code=r.code {2} {3} {4} {5} and r4.currency_id=r.currency_id) end as total_bal_curr,
                            {6} as partner_id , 
                            case when curr_name!='MNT' and sum(amount_curr) <0 
                                    then sum(amount_curr) 
                                    else 
                                        0 
                                end as amount_curr_cr,
                            case when curr_name!='MNT' and sum(amount_curr) >0 
                                    then sum(amount_curr) 
                                    else 
                                        0 
                                end as amount_curr_dt,
                            curr_name,
                            (select unnest(ARRAY_AGG(c.name  -> 'en_US')) from res_partner_res_partner_category_rel rr left join res_partner_category c on rr.category_id=c.id where rr.partner_id={6} group by rr.partner_id limit 1) as category 
                    FROM mw_account_report r 
                    WHERE state='posted' AND date between '{0}' and '{1}' {2} {3} {4} {5} '''.format(self.date_from, self.date_to,account_where,\
                                                                                      partner_where ,company_where, filters, str(partner.id))+ \
                    " group by code,account_name,partner_name,curr_name,currency_id,account_id  order by code,account_name "
            else:
                query='''SELECT sum(debit) as debit, sum(credit) as credit,code as ref, 
                            account_name as name ,1 as number,
                            account_id,
                            (select sum(debit-credit) from mw_account_report r2 where state='posted' AND date < '{0}' and r2.code=r.code {2} {3} {4} {5} and r2.currency_id=r.currency_id) as field_initial,
                            case when curr_name='MNT' then 0 ELSE (select sum(amount_currency) from mw_account_report r3 where state='posted' AND date < '{0}' and r3.code=r.code {2} {3} {4} {5} and r3.currency_id=r.currency_id) end as initial_bal_curr,
                            case when curr_name='MNT' then 0 ELSE (select sum(amount_currency) from mw_account_report r4 where state='posted' AND date <= '{1}' and r4.code=r.code {2} {3} {4} {5} and r4.currency_id=r.currency_id) end as total_bal_curr,
                            {6} as partner_id , 
                            --case when curr_name='MNT' then 0 ELSE sum(amount_curr) end as amount_curr,
                            case when curr_name!='MNT' and sum(amount_curr) <0 
                                    then sum(amount_curr) 
                                    else 
                                        0 
                                end as amount_curr_cr,
                            case when curr_name!='MNT' and sum(amount_curr) >0 
                                    then sum(amount_curr) 
                                    else 
                                        0 
                                end as amount_curr_dt,                            
                            curr_name,
                            (select unnest(ARRAY_AGG(c.name  -> 'en_US')) from res_partner_res_partner_category_rel rr left join res_partner_category c on rr.category_id=c.id where rr.partner_id={6} group by rr.partner_id limit 1) as category 
                    FROM mw_account_report r 
                    WHERE state='posted' AND date between '{0}' and '{1}' {2} {3} {4} {5} '''.format(self.date_from, self.date_to,account_where,\
                                                                                      partner_where ,company_where, filters, str(partner.id))+\
                     " group by code,account_name,curr_name,currency_id,account_id  order by code,account_name "                
            # if partner.id==31821:
            #     print ('query==: ',query)
            
              #   SELECT sum(debit) as debit, sum(credit) as credit,'' as ref, partner_name as name, code as account_code, account_name as account_name ,1 as number,
              #               (select sum(debit-credit) from mw_account_report r2 where state='posted' AND date < '2024-03-01' and r2.code=r.code  AND account_id in (30025) 
              # AND partner_id=32672   ) as field_initial,
              #               32672 as partner_id , sum(amount_curr) as amount_curr,
              #               (select unnest(ARRAY_AGG(c.name  -> 'en_US')) from res_partner_res_partner_category_rel rr left join res_partner_category c on rr.category_id=c.id where rr.partner_id=32672 group by rr.partner_id limit 1) as category 
              #       FROM mw_account_report r 
              #       WHERE state='posted' AND date between '2024-03-01' and '2024-03-05'  AND account_id in (30025) 
              # AND partner_id=32672     group by code,account_name,partner_name  order by code,account_name 
                          
 # SELECT sum(debit) as debit, sum(credit) as credit,'' as ref, partner_name as name, code as account_code, account_name as account_name ,1 as number,
 #                            (select sum(debit-credit) from mw_account_report r2 where state='posted' AND date < '2024-03-01' and r2.code=r.code  AND account_id in (30025) 
 #              AND partner_id=32672   ) as field_initial,
 #                            32672 as partner_id , sum(amount_curr) as amount_curr,
 #                            (select unnest(ARRAY_AGG(c.name  -> 'en_US')) from res_partner_res_partner_category_rel rr left join res_partner_category c on rr.category_id=c.id where rr.partner_id=32672 group by rr.partner_id limit 1) as category 
 #                    FROM mw_account_report r 
 #                    WHERE state='posted' AND date between '2024-02-01' and '2024-03-05'  AND account_id in (30025) 
 #              AND partner_id=32672     group by code,account_name,partner_name  order by code,account_name 
            # print ('query ',query)
            self._cr.execute(query)
            res = self._cr.dictfetchall()
            # if partner.id==31821:
            # print ('resres ',res)
            check_accounts=[]
            null_accounts=[]
            if len(res)>0:
                for i in res:
                    check_accounts.append(i['account_id'])
                for ii in account_ids.ids:
                    if ii not in check_accounts:
                        null_accounts.append(ii)
            # print ('null_accounts ',null_accounts)
            if not res or len(null_accounts)>0:
                # if partner.id==64347:
                #     print ('init_query ',init_query)
                account_where_init=''
                if null_accounts:
                    account_where_init+=''' AND account_id in ({0}) 
            '''.format(','.join(map(str, null_accounts)))
                else:
                    account_where_init=account_where
                if self.not_group:
                    init_query='''SELECT 0 as debit, 0 as credit,'' as ref, partner_name as name, code as account_code, account_name as account_name ,1 as number,
                            sum(debit-credit) as field_initial,
                            case when curr_name='MNT' then 0 ELSE sum(amount_currency) end as initial_bal_curr,
                            case when curr_name='MNT' then 0 ELSE sum(amount_currency) end as total_bal_curr,
                            {6} as partner_id , 0 as amount_curr,
                            curr_name,
                            (select unnest(ARRAY_AGG(c.name  -> 'en_US')) from res_partner_res_partner_category_rel rr left join res_partner_category c on rr.category_id=c.id where rr.partner_id={6} group by rr.partner_id limit 1) as category 
                    FROM mw_account_report r 
                    WHERE state='posted' AND date < '{0}' {2} {3} {4} {5} '''.format(self.date_from, self.date_to,account_where_init,\
                                                                                      partner_where ,company_where, filters, str(partner.id))+ " group by code,account_name,partner_name,curr_name  order by code,account_name "
                    
                else:
                    init_query='''SELECT 0 as debit, 0 as credit,code as ref, account_name as name ,1 as number,
                                sum(debit-credit) as field_initial,
                                case when curr_name='MNT' then 0 ELSE sum(amount_currency) end as initial_bal_curr,
                                case when curr_name='MNT' then 0 ELSE sum(amount_currency) end as total_bal_curr,
                                {6} as partner_id , 0 as amount_curr,
                                curr_name,
                                (select unnest(ARRAY_AGG(c.name  -> 'en_US')) from res_partner_res_partner_category_rel rr left join res_partner_category c on rr.category_id=c.id where rr.partner_id={6} group by rr.partner_id limit 1) as category 
                        FROM mw_account_report r 
                        WHERE state='posted' AND date < '{0}' {2} {3} {4} {5} '''.format(self.date_from, self.date_to,account_where_init,\
                                                                                          partner_where ,company_where, filters, str(partner.id))+ " group by code,account_name,curr_name  order by code,account_name "                 
                # if partner.id==31821:
                #     print ('init_query ',init_query)

                self._cr.execute(init_query)
                res_init = self._cr.dictfetchall()
                res+=res_init
            parter_check=[]
            account_check=[]
            # if res.get('partner_id',1)==31821:
            # print ('res=== ',res)
            # index=1
            if len(res)>0:
                for col_pos, column in report_data["columns"].items():
                    format=report_data["formats"]["format_left"]
                    if  not self.not_group:
                        if col_pos==0:
                            report_data["sheet"].write(report_data["row_pos"],col_pos,u'харилцагч:',format,)
                        elif col_pos==1:
                            report_data["sheet"].write(report_data["row_pos"],col_pos,partner.ref and partner.ref or '',format,)
                        elif col_pos==2:
                            report_data["sheet"].write(report_data["row_pos"],col_pos,partner.name,format,)
                        else:
                            report_data["sheet"].write(report_data["row_pos"],col_pos,u'',format,)
                    # else:
                    #     if col_pos==0:
                    #         report_data["sheet"].write(report_data["row_pos"],col_pos,u'харилцагч:',format,)
                    #     elif col_pos==1:
                    #         report_data["sheet"].write(report_data["row_pos"],col_pos,partner.ref and partner.ref or '',format,)
                    #     elif col_pos==2:
                    #         report_data["sheet"].write(report_data["row_pos"],col_pos,partner.name,format,)
                    #     else:
                    #         report_data["sheet"].write(report_data["row_pos"],col_pos,u'',format,)                        
                if  not self.not_group:
                    report_data["row_pos"]+=1
                    index= 1
                count=self._count_grouped(res)
                for line in res:
                    umnuh=False
                    if line['partner_id'] not in parter_check:
                    #     index=1
                        parter_check.append(line['partner_id'])
                    #     self.write_init(report_data,line['partner_id'],line['account_id'],)
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
                                if self.foreign_currency:  
                                    report_data["sheet"].write_formula(report_data["row_pos"],col_pos,'{=sum('+ self._symbol(report_data["row_pos"],col_pos-6)+'+'\
                                                                   + self._symbol(report_data["row_pos"],col_pos-4) +'-'\
                                                                   + self._symbol(report_data["row_pos"],col_pos-2) +\
                                                                   ')}', format)
                                else:
                                    report_data["sheet"].write_formula(report_data["row_pos"],col_pos,'{=sum('+ self._symbol(report_data["row_pos"],col_pos-3)+'+'\
                                                                   + self._symbol(report_data["row_pos"],col_pos-2) +'-'\
                                                                   + self._symbol(report_data["row_pos"],col_pos-1) +\
                                                                   ')}', format)
                            elif column["field"]=="number":
                                report_data["sheet"].write(report_data["row_pos"],col_pos,index,format,)
                                index+=1
                            else:
                                report_data["sheet"].write(report_data["row_pos"],col_pos,line[column["field"]],format,)
                        elif column["field"]=="ref" and self.not_group:
                            report_data["sheet"].write(report_data["row_pos"],col_pos,partner.ref,format)
                        else:
                            report_data["sheet"].write(report_data["row_pos"],col_pos,'',format,)
                            
                    report_data["row_pos"] += 1 
                    if count.get(line['partner_id'],False) and count[line['partner_id']]==check  and  not self.not_group:  
                        parter_check.append(line['partner_id'])
                        for col_pos, column in report_data["columns"].items():
                            if column["field"] in ("field_initial","debit","credit","balance_calc"):
                                report_data["sheet"].write_formula(report_data["row_pos"],col_pos,'{=sum('+ self._symbol(report_data["row_pos"]-count.get(line['partner_id'],False),col_pos)+':'\
                                                                   + self._symbol(report_data["row_pos"]-1,col_pos) +')}', format)
                            elif column["field"] in ("name"):
                                report_data["sheet"].write(report_data["row_pos"],2,u'Дүн',format,)
                            else:
                                report_data["sheet"].write(report_data["row_pos"],col_pos,'',format,)
                        report_data["row_pos"] += 1        
            