# -*- encoding: utf-8 -*-
############################################################################################
#
#    Managewall-ERP, Enterprise Management Solution    
#    Copyright (C) 2007-2023 mw Co.,ltd (<http://www.managewall.mn>). All Rights Reserved
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
from odoo.exceptions import ValidationError
from odoo.tools import date_utils
from odoo.addons.account_financial_report.report.report_excel_cell_styles import ReportExcelCellStyles


from io import BytesIO
import xlsxwriter
import base64
try:
    from base64 import encodestring
except ImportError:
    from base64 import encodebytes as encodestring

class account_report_mw(models.TransientModel):
    """
        Санхүүгийн ерөнхий тайлан
    """
    
    _name = "account.report.mw"
    _description = "Account report mw"
    
    company_id = fields.Many2one('res.company', 'Company',default=lambda self: self.env.company)
    date_range_id = fields.Many2one(comodel_name="date.range", string="Date range")
    date_from = fields.Date(required=True, default=lambda self: self._init_date_from())
    date_to = fields.Date(required=True, default=fields.Date.context_today)
    fy_start_date = fields.Date(compute="_compute_fy_start_date")
    target_move = fields.Selection(
        [("posted", "All Posted Entries"), ("all", "All Entries")],
        string="Target Moves",
        required=True,
        default="posted",
    )
    account_ids = fields.Many2many(
        comodel_name="account.account", string="Filter accounts"
    )
    centralize = fields.Boolean(string="Activate centralization", default=True)
    hide_account_at_0 = fields.Boolean(
        string="Hide account ending balance at 0",
        help="Use this filter to hide an account or a partner "
        "with an ending balance at 0. "
        "If partners are filtered, "
        "debits and credits totals will not match the trial balance.",
    )
    receivable_accounts_only = fields.Boolean()
    payable_accounts_only = fields.Boolean()
    partner_ids = fields.Many2many(
        comodel_name="res.partner",
    )
    account_journal_ids = fields.Many2many(
        comodel_name="account.journal", string="Filter journals"
    )
    cost_center_ids = fields.Many2many(
        comodel_name="account.analytic.account", string="Filter cost centers"
    )

    not_only_one_unaffected_earnings_account = fields.Boolean(readonly=True)
    foreign_currency = fields.Boolean(
        string="Show foreign currency",
        help="Display foreign currency for move lines, unless "
        "account currency is not setup through chart of accounts "
        "will display initial and final balance in that currency.",
        default= True, #lambda self: self._default_foreign_currency(),
    )
    account_code_from = fields.Many2one(
        comodel_name="account.account",
        help="Starting account in a range",
    )
    account_code_to = fields.Many2one(
        comodel_name="account.account",
        help="Ending account in a range",
    )
    grouped_by = fields.Selection(
        selection=[("", "None"), ("partners", "Partners"), ("taxes", "Taxes")],
        default="partners",
    )
    show_cost_center = fields.Boolean(
        string="Show Analytic Account",
        default=False,
    )
    show_reconciled = fields.Boolean(
        string="Show reconciled",
        default=False,
    )
    domain = fields.Char(
        string="Journal Items Domain",
        default=[],
        help="This domain will be used to select specific domain for Journal " "Items",
    )

    partner_categ_ids = fields.Many2many(
        comodel_name="res.partner.category",
    )

    not_group = fields.Boolean(string="Харилцагчаар груплэхгүй?", default=True)
    with_balance = fields.Boolean(string="Үлдэгдэлтэй?", default=True)

    @api.onchange("partner_categ_ids")
    def on_change_categ_range(self):
        if self.partner_categ_ids:
            partners=self.env['res.partner'].search([('category_id','in',self.partner_categ_ids.ids)])
            self.partner_ids = partners
            
    def _get_account_move_lines_domain(self):
        domain = literal_eval(self.domain) if self.domain else []
        return domain

    @api.onchange("account_code_from", "account_code_to")
    def on_change_account_range(self):
        if (
            self.account_code_from
            and self.account_code_from.code.isdigit()
            and self.account_code_to
            and self.account_code_to.code.isdigit()
        ):
            start_range = int(self.account_code_from.code)
            end_range = int(self.account_code_to.code)
            self.account_ids = self.env["account.account"].search(
                [("code", ">=", start_range), ("code", "<=", end_range)]
            )
            if self.company_id:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id
                )

    def _init_date_from(self):
        """set start date to begin of current year if fiscal year running"""
        today = fields.Date.context_today(self)
        company = self.company_id or self.env.company
        last_fsc_month = company.fiscalyear_last_month
        last_fsc_day = company.fiscalyear_last_day

        if (
            today.month < int(last_fsc_month)
            or today.month == int(last_fsc_month)
            and today.day <= last_fsc_day
        ):
            return time.strftime("%Y-01-01")
        else:
            return False

    def _default_foreign_currency(self):
        return self.env.user.has_group("base.group_multi_currency")

    @api.depends("date_from")
    def _compute_fy_start_date(self):
        for wiz in self:
            if wiz.date_from:
                date_from, date_to = date_utils.get_fiscal_year(
                    wiz.date_from,
                    day=self.company_id.fiscalyear_last_day,
                    month=int(self.company_id.fiscalyear_last_month),
                )
                wiz.fy_start_date = date_from
            else:
                wiz.fy_start_date = False

    @api.onchange("company_id")
    def onchange_company_id(self):
        """Handle company change."""
        count = self.env["account.account"].search_count(
            [
                ("account_type", "=", "equity_unaffected"),
                ("company_id", "=", self.company_id.id),
            ]
        )
        self.not_only_one_unaffected_earnings_account = count != 1
        if (
            self.company_id
            and self.date_range_id.company_id
            and self.date_range_id.company_id != self.company_id
        ):
            self.date_range_id = False
        if self.company_id and self.account_journal_ids:
            self.account_journal_ids = self.account_journal_ids.filtered(
                lambda p: p.company_id == self.company_id or not p.company_id
            )
        if self.company_id and self.partner_ids:
            self.partner_ids = self.partner_ids.filtered(
                lambda p: p.company_id == self.company_id or not p.company_id
            )
        if self.company_id and self.account_ids:
            if self.receivable_accounts_only or self.payable_accounts_only:
                self.onchange_type_accounts_only()
            else:
                self.account_ids = self.account_ids.filtered(
                    lambda a: a.company_id == self.company_id
                )
        if self.company_id and self.cost_center_ids:
            self.cost_center_ids = self.cost_center_ids.filtered(
                lambda c: c.company_id == self.company_id
            )
        res = {
            "domain": {
                "account_ids": [],
                "partner_ids": [],
                "account_journal_ids": [],
                "cost_center_ids": [],
                "date_range_id": [],
            }
        }
        if not self.company_id:
            return res
        else:
            res["domain"]["account_ids"] += [("company_id", "=", self.company_id.id)]
            res["domain"]["account_journal_ids"] += [
                ("company_id", "=", self.company_id.id)
            ]
            # res["domain"]["partner_ids"] += self._get_partner_ids_domain()
            res["domain"]["cost_center_ids"] += [
                ("company_id", "=", self.company_id.id)
            ]
            res["domain"]["date_range_id"] += [
                "|",
                ("company_id", "=", self.company_id.id),
                ("company_id", "=", False),
            ]
        return res

    @api.onchange("date_range_id")
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.constrains("company_id", "date_range_id")
    def _check_company_id_date_range_id(self):
        for rec in self.sudo():
            if (
                rec.company_id
                and rec.date_range_id.company_id
                and rec.company_id != rec.date_range_id.company_id
            ):
                raise ValidationError(
                    _(
                        "The Company in the General Ledger Report Wizard and in "
                        "Date Range must be the same."
                    )
                )

    @api.onchange("receivable_accounts_only", "payable_accounts_only")
    def onchange_type_accounts_only(self):
        """Handle receivable/payable accounts only change."""
        if self.receivable_accounts_only or self.payable_accounts_only:
            domain = [("company_id", "=", self.company_id.id)]
            if self.receivable_accounts_only and self.payable_accounts_only:
                domain += [
                    ("account_type", "in", ("asset_receivable", "liability_payable"))
                ]
            elif self.receivable_accounts_only:
                domain += [("account_type", "=", "asset_receivable")]
            elif self.payable_accounts_only:
                domain += [("account_type", "=", "liability_payable")]
            self.account_ids = self.env["account.account"].search(domain)
        else:
            self.account_ids = None

    @api.onchange("partner_ids")
    def onchange_partner_ids(self):
        if self.partner_ids:
            self.receivable_accounts_only = self.payable_accounts_only = True
        else:
            self.receivable_accounts_only = self.payable_accounts_only = False

    @api.depends("company_id")
    def _compute_unaffected_earnings_account(self):
        for record in self:
            record.unaffected_earnings_account = self.env["account.account"].search(
                [
                    ("account_type", "=", "equity_unaffected"),
                    ("company_id", "=", record.company_id.id),
                ]
            )

    unaffected_earnings_account = fields.Many2one(
        comodel_name="account.account",
        compute="_compute_unaffected_earnings_account",
        store=True,
    )
    
    def _symbol(self, row, col):
        return self._symbol_col(col) + str(row+1)
    def _symbol_col(self, col):
        excelCol = str()
        div = col+1
        while div:
            (div, mod) = divmod(div-1, 26)
            excelCol = chr(mod + 65) + excelCol
        return excelCol
    

    def _count_grouped(self, lst):
        cc={}
        for i in lst:
            if cc.get(i['partner_id']):
                cc[i['partner_id']]+=1
            else:
                cc[i['partner_id']]=1        
        return cc
    

    def _get_report_columns(self,):
        res = [
            {"header": _("Огноо"), "field": "date", "width": 11, "type": "date",},
            {"header": _("Гүйлгээ"), "field": "entry", "width": 18},
            {"header": _("Журнал"), "field": "journal", "width": 8},
            {"header": _("Данс"), "field": "code", "width": 9},
            {"header": _("Харилцагч"), "field": "partner_name", "width": 25},
            {"header": _("Гүйлгээний утга"), "field": "ref_label", "width": 40},
        ]
        if self.show_cost_center:
            res += [{"header": _("Analytic Distribution"),"field": "analytic_distribution","width": 20,},]
        res += [{
                "header": _("Дебит"),
                "field": "debit",
                "field_initial_balance": "initial_debit",
                "field_final_balance": "final_debit",
                "type": "amount",
                "width": 14,
            },
            {
                "header": _("Кредит"),
                "field": "credit",
                "field_initial_balance": "initial_credit",
                "field_final_balance": "final_credit",
                "type": "amount",
                "width": 14,
            },
            {
                "header": _("Үлдэгдэл"),
                "field": "balance",
                "field_initial_balance": "initial_balance",
                "field_final_balance": "final_balance",
                "type": "amount",
                "width": 14,
            },
        ]
        if self.foreign_currency:
            res += [
                {
                    "header": _("Валютын дүн"),
                    "field": "amount_curr",
                    "field_initial_balance": "initial_bal_curr",
                    "field_final_balance": "final_bal_curr",
                    "type": "amount_currency",
                    "width": 14,
                },
                {
                    "header": _("Валютаар үлдэгдэл"),
                    "field": "total_bal_curr",
                    "field_initial_balance": "initial_bal_curr",
                    "field_final_balance": "final_bal_curr",
                    "type": "amount_currency",
                    "width": 14,
                },
            ]
        res_as_dict = {}
        for i, column in enumerate(res):
            res_as_dict[i] = column
        return res_as_dict
    

    def _define_formats(self, workbook, report_data):
        currency_id = self.env["res.company"]._default_currency_id()
        report_data["formats"] = {
            "format_bold": workbook.add_format({"bold": True}),
            "format_right": workbook.add_format({"align": "right",'text_wrap': 1,}),
            "format_left": workbook.add_format({"align": "left",'text_wrap': 1,"border": True}),
            "format_center_bold": workbook.add_format(
                {"align": "center", "bold": True, }
            ),
            "format_right_bold_italic": workbook.add_format(
                {"align": "right", "bold": True, "italic": True}
            ),
            "format_header_left": workbook.add_format(
                {"bold": True, "border": True, "bg_color": "#CFF999"}
            ),
            "format_header_center": workbook.add_format(
                {"bold": True, "align": "center", "border": True, "bg_color": "#CFF999"}
            ),
            "format_header_right": workbook.add_format(
                {"bold": True, "align": "right", "border": True, "bg_color": "#CFF999"}
            ),
            "format_header_amount": workbook.add_format(
                {"bold": True, "border": True, "bg_color": "#CFF999"}
            ),
            "format_amount": workbook.add_format({'num_format': '#,##0.00', "align": "right", "border": True,}),
            "format_amount_bold": workbook.add_format({"bold": True,'num_format': '#,##0.00', "align": "right","bg_color": "#e9fccf"}
            ),
            "format_percent_bold_italic": workbook.add_format(
                {"bold": True, "italic": True}
            ),
            "format_date": workbook.add_format(
                {
                    'align': 'center',
                    'valign': 'vcenter',
                    'num_format': 'yyyy-mm-dd',
                     "border": True,
                }
            ),
            
            
        }
        report_data["formats"]["format_amount"].set_num_format(
            "#,##0." + "0" * currency_id.decimal_places
        )
        report_data["formats"]["format_header_amount"].set_num_format(
            "#,##0." + "0" * currency_id.decimal_places
        )
        report_data["formats"]["format_percent_bold_italic"].set_num_format("#,##0.00%")

    
    def write_array_header(self, report_data):
        for col_pos, column in report_data["columns"].items():
            report_data["sheet"].write(
                report_data["row_pos"],
                col_pos,
                column["header"],
                report_data["formats"]["format_header_center"],
            )
        report_data["row_pos"] += 1
        
    def write_array_title(self, report_data,title):
        rowx = 0
        # create name
        report_data["sheet"].merge_range(0, 0, 0, 3, '%s' % (self.company_id.name),report_data["formats"]["format_right"],)
        report_data["sheet"].merge_range(1, 0, 1, 3, '%s: %s - %s' % (_('Тайлант хугацаа'), self.date_from, self.date_to), report_data["formats"]["format_right"])
        report_data["sheet"].merge_range(2, 1, 2, 9, title, report_data["formats"]["format_center_bold"],)
    
    def _set_column_width(self, report_data):
        for position, column in report_data["columns"].items():
            report_data["sheet"].set_column(position, position, column["width"])
                
    def button_mw_xlsx(self):
        from io import StringIO
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        report_data={}
        self._define_formats(workbook, report_data)
        report_data["row_pos"]=3
        report_data["columns"]=self._get_report_columns()
        file_name = "transfer_balance_%s.xlsx" % (time.strftime('%Y%m%d_%H%M'),)
        self.mw_xlsx_report(workbook, report_data, self, 'report')
        self._set_column_width(report_data)        
        workbook.close()
        out = encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
    def write_array_body(self, report_data):
        account_where=""
        partner_where=""
        company_where=" "
        filters=""
        if self.partner_ids:
            partner_where+=''' AND partner_id in ({0}) '
            '''.format(','.join(map(str, self.partner_ids.ids)))
        if self.account_ids:
            partner_where+=''' AND account_id in ({0}) '
            '''.format(','.join(map(str, self.account_ids.ids)))
        self._cr.execute(
            "SELECT * "
            "FROM mw_account_report "
            "WHERE  date between '{0}' and '{1}' ".format(self.date_from, self.date_to) +" "
            " " + account_where + " "+ partner_where +" "+ company_where+" " + filters + " ")
        res = self._cr.dictfetchall()
        print ('res ',res)
        for line in res:
            for col_pos, column in report_data["columns"].items():
                print ('column["field"] ',column["field"])
                format=report_data["formats"]["format_left"]
                if column.get("type","amount")=="date":
                    format=report_data["formats"]["format_date"]
                if line.get(column["field"],False):
                    report_data["sheet"].write(report_data["row_pos"],col_pos,line[column["field"]],format,)
                else:
                    report_data["sheet"].write(report_data["row_pos"],col_pos,'',format,)
                    
            report_data["row_pos"] += 1        
    
    def mw_xlsx_report(self, workbook, data, wizard,sheet_name):
        sheet = workbook.add_worksheet(sheet_name)
        data["sheet"]=sheet
        self.write_array_title(data,u' Санхүү тайлан')
        self.write_array_header(data)
        self.write_array_body(data)


    def write_ending_balance(self, my_object, name, label, report_data):
        for i in range(0, len(report_data["columns"])):
            report_data["sheet"].write(
                report_data["row_pos"],
                i,
                "",
                report_data["formats"]["format_header_right"],
            )
        row_count_name = self._get_col_count_final_balance_name()
        col_pos_label = self._get_col_pos_final_balance_label()
        report_data["sheet"].merge_range(
            report_data["row_pos"],
            0,
            report_data["row_pos"],
            row_count_name - 1,
            name,
            report_data["formats"]["format_header_left"],
        )
        report_data["sheet"].write(
            report_data["row_pos"],
            col_pos_label,
            label,
            report_data["formats"]["format_header_right"],
        )
        for col_pos, column in report_data["columns"].items():
            if column.get("field_final_balance"):
                value = my_object.get(column["field_final_balance"], False)
                cell_type = column.get("type", "string")
                if cell_type == "string":
                    report_data["sheet"].write_string(
                        report_data["row_pos"],
                        col_pos,
                        value or "",
                        report_data["formats"]["format_header_right"],
                    )
                elif cell_type == "amount":
                    report_data["sheet"].write_number(
                        report_data["row_pos"],
                        col_pos,
                        float(value),
                        report_data["formats"]["format_header_amount"],
                    )
                elif cell_type == "amount_currency":
                    if my_object["currency_id"] and value:
                        format_amt = self._get_currency_amt_format_dict(
                            my_object, report_data
                        )
                        report_data["sheet"].write_number(
                            report_data["row_pos"], col_pos, float(value), format_amt
                        )
            elif column.get("field_currency_balance"):
                value = my_object.get(column["field_currency_balance"], False)
                cell_type = column.get("type", "string")
                if cell_type == "many2one":
                    if my_object["currency_id"]:
                        report_data["sheet"].write_string(
                            report_data["row_pos"],
                            col_pos,
                            value or "",
                            report_data["formats"]["format_header_right"],
                        )
                elif cell_type == "currency_name":
                    report_data["sheet"].write_string(
                        report_data["row_pos"],
                        col_pos,
                        value or "",
                        report_data["formats"]["format_header_right"],
                    )
        report_data["row_pos"] += 1
        