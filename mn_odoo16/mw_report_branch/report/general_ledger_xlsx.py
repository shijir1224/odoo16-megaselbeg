
from odoo import _, models


class GeneralLedgerXslx(models.AbstractModel):
    _inherit = "report.a_f_r.report_general_ledger_xlsx"
    _description = "General Ledger XLSL Report"


    def _get_report_columns(self, report):
        res = [
            {"header": _("Date"), "field": "date", "width": 11},
            {"header": _("Entry"), "field": "entry", "width": 18},
            {"header": _("Journal"), "field": "journal", "width": 8},
            {"header": _("Account"), "field": "account", "width": 9},
        ]
        
        if report.show_few_fields:
            res += [
                {"header": _("Taxes"), "field": "taxes_description", "width": 15},
            ]
        res += [
                {"header": _("Partner"), "field": "partner_name", "width": 25},
                {"header": _("Ref - Label"), "field": "ref_label", "width": 40},
            ]
        
        if report.show_cost_center:
            res += [
                {
                    "header": _("Analytic Distribution"),
                    "field": "analytic_distribution",
                    "width": 20,
                },
            ]
        if report.show_few_fields:
            res += [
            {"header": _("Rec."), "field": "rec_name", "width": 15},
            ]
        res += [
            {
                "header": _("Debit"),
                "field": "debit",
                "field_initial_balance": "initial_debit",
                "field_final_balance": "final_debit",
                "type": "amount",
                "width": 14,
            },
            {
                "header": _("Credit"),
                "field": "credit",
                "field_initial_balance": "initial_credit",
                "field_final_balance": "final_credit",
                "type": "amount",
                "width": 14,
            },
            {
                "header": _("Cumul. Bal."),
                "field": "balance",
                "field_initial_balance": "initial_balance",
                "field_final_balance": "final_balance",
                "type": "amount",
                "width": 14,
            },
        ]
        if report.foreign_currency:
            res += [
                {
                    "header": _("Amount cur."),
                    "field": "bal_curr",
                    "field_initial_balance": "initial_bal_curr",
                    "field_final_balance": "final_bal_curr",
                    "type": "amount_currency",
                    "width": 10,
                },
                {
                    "header": _("Cumul cur."),
                    "field": "total_bal_curr",
                    "field_initial_balance": "initial_bal_curr",
                    "field_final_balance": "final_bal_curr",
                    "type": "amount_currency",
                    "width": 10,
                },
            ]
        res += [
                {
                    "header": _("Харьцсан данс"),
                    "field": "counterpart_account",
                    "width": 20,
                },{
                    "header": _("Сүүлд зассан ажилтан"),
                    "field": "create_uid",
                    "width": 20,
                },{
                    "header": _("Үүсгэсэн огноо"),
                    "field": "write_uid",
                    "width": 20,
                },{
                    "header": _("Салбар"),
                    "field": "branch_name",
                    "width": 20,
                },
                
            ]           
        if report.show_warehouse:
            res += [
               {
                    "header": _("Агуулах"),
                    "field": "warehouse",
                    "width": 20,
                },
            ]                         
        res_as_dict = {}
        for i, column in enumerate(res):
            res_as_dict[i] = column
        return res_as_dict

    # flake8: noqa: C901
    # flake8: noqa: C901
    def _generate_report_content(self, workbook, report, data, report_data):
        res_data = self.env[
            "report.account_financial_report.general_ledger"
        ]._get_report_values(report, data)
        # print ('res_datares_data ',res_data)
        general_ledger = res_data["general_ledger"]
        accounts_data = res_data["accounts_data"]
        journals_data = res_data["journals_data"]
        taxes_data = res_data["taxes_data"]
        analytic_data = res_data["analytic_data"]
        filter_partner_ids = res_data["filter_partner_ids"]
        foreign_currency = res_data["foreign_currency"]
        branch_data = res_data["branch_data"]
        show_wh=data['show_warehouse']
        total_amount_data = res_data['total_amount_data']
        # For each account
        for account in general_ledger:
            # Write account title
            total_bal_curr = account["init_bal"].get("bal_curr", 0)
            self.write_array_title(
                account["code"] + " - " + accounts_data[account["id"]]["name"],
                report_data,
            )

            if "list_grouped" not in account:
                # Display array header for move lines
                self.write_array_header(report_data)

                # Display initial balance line for account
                account.update(
                    {
                        "initial_debit": account["init_bal"]["debit"],
                        "initial_credit": account["init_bal"]["credit"],
                        "initial_balance": account["init_bal"]["balance"],
                    }
                )
                if foreign_currency:
                    account.update(
                        {"initial_bal_curr": account["init_bal"]["bal_curr"]}
                    )
                self.write_initial_balance_from_dict(account, report_data)

                # Display account move lines
                for line in account["move_lines"]:
                    #=====
                    if line.get('branch_id',False):
                        line.update(
                            {
                                "branch": branch_data[line["branch_id"]]["name"],
                            }
                        )
                    if line.get('account_id',False):
                        #Харьцсан данс
                        a=''
                        uid=''
                        if show_wh:
                                # select a.code,rp.name as create_name,l.create_date,wh.name from 
                                #     account_move_line l 
                                #     left join account_account a on l.account_id=a.id
                                #     left join account_move m on l.move_id=m.id 
                                #     left join stock_move sm on m.stock_move_id=sm.id
                                #     left join stock_picking_type pt on pt.id=sm.picking_type_id
                                #     left join stock_warehouse wh on wh.id=pt.warehouse_id
                                #     left join res_users u on u.id=l.write_uid
                                #     left join res_partner rp on u.partner_id = rp.id
                                # where
                                #  l.move_id=(select move_id from account_move_line where id=1422471) 
                                #  and a.id<>50742                            
                            sql = u"""select a.code,rp.name as create_name,l.create_date,wh.name as warehouse,rb.name as branch from 
                                            account_move_line l 
                                            left join account_account a on l.account_id=a.id
                                            left join account_move m on l.move_id=m.id 
                                            left join stock_move sm on m.stock_move_id=sm.id
                                            left join stock_picking_type pt on pt.id=sm.picking_type_id
                                            left join stock_warehouse wh on wh.id=pt.warehouse_id
                                            left join res_users u on u.id=l.write_uid
                                            left join res_branch rb on rb.id = l.branch_id
                                            left join res_partner rp on u.partner_id = rp.id
                                    where
                                     l.move_id=(select move_id from account_move_line where id={0}) 
                                     and a.id<>{1}""".format(line['id'],line['account_id'])                            
                        else:
                            sql = u"""select a.code,rp.name as create_name,l.create_date, rb.name as branch from 
                                        account_move_line l left join 
                                        account_account a on l.account_id=a.id left join 
                                        res_users u on u.id=l.write_uid left join
                                        res_partner rp on u.partner_id = rp.id
                                        left join res_branch rb on rb.id = l.branch_id
                                    where
                                     l.move_id=(select move_id from account_move_line where id={0}) 
                                     and a.id<>{1}""".format(line['id'],line['account_id'])
                        # print ('sqlsql ',sql)
                                                         
                        self._cr.execute(sql)
                        counterpart_res = self._cr.dictfetchall()
#                         print ('counterpart_res ',counterpart_res)
                        if len(counterpart_res)>1:
                            ch=1
                            for i in counterpart_res:
                                if ch<=3:
                                    a+=i['code']+','  
                                else:
                                    a+=' ...'
                                    break
                                ch+=1
                        elif len(counterpart_res)==1:
                            a=counterpart_res[0]['code']
                        uid=counterpart_res and len(counterpart_res)>0 and counterpart_res[0].get('create_name','')
                        wirte_date = counterpart_res and len(counterpart_res)>0 and counterpart_res[0].get('create_date','')
                        branch_name = counterpart_res and len(counterpart_res)>0 and counterpart_res[0].get('branch','')
                        line.update(
                            {
                                "counterpart_account": a,
                            }
                        )    
                        line.update(
                            {
                            "create_uid": uid,
                            "write_uid": wirte_date,
                            "branch_name": branch_name


                            } 
                        )        
                        if show_wh:
                            warehouse = counterpart_res and len(counterpart_res)>0 and counterpart_res[0].get('warehouse','')
                            line.update(
                            {
                            "warehouse": warehouse,
                            } 
                        )
               
#                         self.write_line_from_dict(line)
                        #======                        
                    line.update(
                        {
                            "account": account["code"],
                            "journal": journals_data[line["journal_id"]]["code"],
                        }
                    )
                    if line["currency_id"]:
                        line.update(
                            {
                                "currency_name": line["currency_id"][1],
                                "currency_id": line["currency_id"][0],
                            }
                        )
                    if line["ref_label"] != "Centralized entries":
                        taxes_description = ""
                        analytic_distribution = ""
                        for tax_id in line["tax_ids"]:
                            taxes_description += taxes_data[tax_id]["tax_name"] + " "
                        if line["tax_line_id"]:
                            taxes_description += line["tax_line_id"][1]
                        for account_id, value in line["analytic_distribution"].items():
                            if value < 100:
                                analytic_distribution += "%s %d%% " % (
                                    analytic_data[int(account_id)]["name"],
                                    value,
                                )
                            else:
                                analytic_distribution += (
                                    "%s " % analytic_data[int(account_id)]["name"]
                                )
                        line.update(
                            {
                                "taxes_description": taxes_description,
                                "analytic_distribution": analytic_distribution,
                            }
                        )
                    if foreign_currency:
                        total_bal_curr += line["bal_curr"]
                        line.update({"total_bal_curr": total_bal_curr})
                    self.write_line_from_dict(line, report_data)
                # Display ending balance line for account
                account.update(
                    {
                        "final_debit": account["fin_bal"]["debit"],
                        "final_credit": account["fin_bal"]["credit"],
                        "final_balance": account["fin_bal"]["balance"],
                    }
                )
                if foreign_currency:
                    account.update(
                        {
                            "final_bal_curr": account["fin_bal"]["bal_curr"],
                        }
                    )
                self.write_ending_balance_from_dict(account, report_data)

            else:
                # For each partner
                # total_bal_curr = 0  comment darmaa Тухайн харилгцачийн Валют үлдэгдэл гаргах
                for group_item in account["list_grouped"]:
                    total_bal_curr = group_item["init_bal"].get("bal_curr", 0) # add darmaa Тухайн харилгцачийн Валют үлдэгдэл гаргах
                    # Write partner title
                    self.write_array_title(group_item["name"], report_data)

                    # Display array header for move lines
                    self.write_array_header(report_data)

                    account.update(
                        {
                            "currency_id": accounts_data[account["id"]]["currency_id"],
                            "currency_name": accounts_data[account["id"]][
                                "currency_name"
                            ],
                        }
                    )

                    # Display initial balance line for partner
                    group_item.update(
                        {
                            "initial_debit": group_item["init_bal"]["debit"],
                            "initial_credit": group_item["init_bal"]["credit"],
                            "initial_balance": group_item["init_bal"]["balance"],
                            "type": "partner",
                            "grouped_by": account["grouped_by"]
                            if "grouped_by" in account
                            else "",
                            "currency_id": accounts_data[account["id"]]["currency_id"],
                            "currency_name": accounts_data[account["id"]][
                                "currency_name"
                            ],
                        }
                    )
                    if foreign_currency:
                        group_item.update(
                            {
                                "initial_bal_curr": group_item["init_bal"]["bal_curr"],
                            }
                        )
                    self.write_initial_balance_from_dict(group_item, report_data)

                    # Display account move lines
                    for line in group_item["move_lines"]:
                        line.update(
                            {
                                "account": account["code"],
                                "journal": journals_data[line["journal_id"]]["code"],
                            }
                        )
                        #=====
                        if line.get('branch_id',False):
                            line.update(
                                {
                                    "branch": branch_data[line["branch_id"]]["name"],
                                }
                            )
                        if line.get('account_id',False):
                            #Харьцсан данс
                            a=''
                            uid=''
                            if show_wh:
                                sql = u"""select a.code,rp.name as create_name,l.create_date,wh.name as warehouse,rb.name as branch from 
                                                account_move_line l 
                                                left join account_account a on l.account_id=a.id
                                                left join account_move m on l.move_id=m.id 
                                                left join stock_move sm on m.stock_move_id=sm.id
                                                left join stock_picking_type pt on pt.id=sm.picking_type_id
                                                left join stock_warehouse wh on wh.id=pt.warehouse_id
                                                left join res_users u on u.id=l.write_uid
                                                left join res_branch rb on rb.id = l.branch_id
                                                left join res_partner rp on u.partner_id = rp.id
                                        where
                                         l.move_id=(select move_id from account_move_line where id={0}) 
                                         and a.id<>{1}""".format(line['id'],line['account_id'])
                            else:        
                                sql = u"""select a.code,rp.name as create_name,l.create_date, rb.name as branch from 
                                        account_move_line l left join 
                                        account_account a on l.account_id=a.id left join 
                                        res_users u on u.id=l.write_uid left join
                                        res_partner rp on u.partner_id = rp.id
                                        left join res_branch rb on rb.id = l.branch_id

                                    where
                                     l.move_id=(select move_id from account_move_line where id={0}) 
                                     and a.id<>{1}""".format(line['id'],line['account_id'])
                            self._cr.execute(sql)
                            counterpart_res = self._cr.dictfetchall()
    #                         print ('counterpart_res ',counterpart_res)
                            if len(counterpart_res)>1:
                                ch=1
                                for i in counterpart_res:
                                    if ch<=3:
                                        a+=i['code']+','  
                                    else:
                                        a+=' ...'
                                        break
                                    ch+=1
                            elif len(counterpart_res)==1:
                                a=counterpart_res[0]['code']      
                            uid=counterpart_res and len(counterpart_res)>0 and counterpart_res[0].get('create_name','')
                            wirte_date = counterpart_res and len(counterpart_res)>0 and counterpart_res[0].get('create_date','')
                            branch_name = counterpart_res and len(counterpart_res)>0 and counterpart_res[0].get('branch','')
                            line.update(
                                {
                                    "counterpart_account": a,
                                }
                            )    
                            line.update(
                                {
                                "create_uid": uid,
                                "write_uid": wirte_date,
                                "branch_name": branch_name
                                } 
                            )     
                            if show_wh:
                                warehouse = counterpart_res and len(counterpart_res)>0 and counterpart_res[0].get('warehouse','')
                                line.update(
                                {
                                "warehouse": warehouse,
                                } 
                            )
                                                   
    #                         self.write_line_from_dict(line)
                            #======                                      
                        if line["currency_id"]:
                            line.update(
                                {
                                    "currency_name": line["currency_id"][1],
                                    "currency_id": line["currency_id"][0],
                                }
                            )
                        if line["ref_label"] != "Centralized entries":
                            taxes_description = ""
                            analytic_distribution = ""
                            for tax_id in line["tax_ids"]:
                                taxes_description += (
                                    taxes_data[tax_id]["tax_name"] + " "
                                )
                            for account_id, value in line[
                                "analytic_distribution"
                            ].items():
                                if value < 100:
                                    analytic_distribution += "%s %d%% " % (
                                        analytic_data[int(account_id)]["name"],
                                        value,
                                    )
                                else:
                                    analytic_distribution += (
                                        "%s " % analytic_data[int(account_id)]["name"]
                                    )
                            line.update(
                                {
                                    "taxes_description": taxes_description,
                                    "analytic_distribution": analytic_distribution,
                                }
                            )
                        if foreign_currency:
                            total_bal_curr += line["bal_curr"]
                            line.update({"total_bal_curr": total_bal_curr})
                        self.write_line_from_dict(line, report_data)

                    # Display ending balance line for partner
                    group_item.update(
                        {
                            "final_debit": group_item["fin_bal"]["debit"],
                            "final_credit": group_item["fin_bal"]["credit"],
                            "final_balance": group_item["fin_bal"]["balance"],
                        }
                    )
                    if foreign_currency and group_item["currency_id"]:
                        group_item.update(
                            {
                                "final_bal_curr": group_item["fin_bal"]["bal_curr"],
                            }
                        )
                    self.write_ending_balance_from_dict(group_item, report_data)

                    # Line break
                    report_data["row_pos"] += 1

                if not filter_partner_ids:
                    account.update(
                        {
                            "final_debit": account["fin_bal"]["debit"],
                            "final_credit": account["fin_bal"]["credit"],
                            "final_balance": account["fin_bal"]["balance"],
                        }
                    )
                    if foreign_currency and account["currency_id"]:
                        account.update(
                            {
                                "final_bal_curr": account["fin_bal"]["bal_curr"],
                            }
                        )
                    self.write_ending_balance_from_dict(account, report_data)
        report_data["row_pos"] += 1         
        report_data["sheet"].merge_range(
            report_data["row_pos"],
            0,
            report_data["row_pos"],
            3,
            'НИЙТ ДҮН',
            report_data["formats"]["format_header_left"],
        )
        for col_pos, column in report_data["columns"].items():
        #         value = my_object.get(column["field_final_balance"], False)
                cell_type = column.get("type", "string")
                if column["field"]in ("debit","credit","balance"):
                    report_data["sheet"].write_number(
                        report_data["row_pos"],
                        col_pos,
                        float(total_amount_data[column["field"]]),
                        report_data["formats"]["format_header_amount"],
                    )                    
                elif cell_type == "string":
                    report_data["sheet"].write_string(
                        report_data["row_pos"],
                        col_pos,
                        "",
                        report_data["formats"]["format_header_right"],
                    )
        #         elif cell_type == "amount":
        #             report_data["sheet"].write_number(
        #                 report_data["row_pos"],
        #                 col_pos,
        #                 float(value),
        #                 report_data["formats"]["format_header_amount"],
        #             )
        #         elif cell_type == "amount_currency":
        #             if my_object["currency_id"] and value:
        #                 format_amt = self._get_currency_amt_format_dict(
        #                     my_object, report_data
        #                 )
        #                 report_data["sheet"].write_number(
        #                     report_data["row_pos"], col_pos, float(value), format_amt
        #                 )
        
        
            # elif column.get("field_currency_balance"):
            #     value = my_object.get(column["field_currency_balance"], False)
            #     cell_type = column.get("type", "string")
            #     if cell_type == "many2one":
            #         if my_object["currency_id"]:
            #             report_data["sheet"].write_string(
            #                 report_data["row_pos"],
            #                 col_pos,
            #                 value or "",
            #                 report_data["formats"]["format_header_right"],
            #             )
            #     elif cell_type == "currency_name":
            #         report_data["sheet"].write_string(
            #             report_data["row_pos"],
            #             col_pos,
            #             value or "",
            #             report_data["formats"]["format_header_right"],
            #         )            
            #

