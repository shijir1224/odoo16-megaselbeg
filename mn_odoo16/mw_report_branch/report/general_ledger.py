# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class GeneralLedgerReportCompute(models.AbstractModel):

    _inherit = 'report.account_financial_report.general_ledger'

    branch_id = fields.Many2one(comodel_name='res.branch')

    @api.model
    def _get_period_domain(
        self,
        account_ids,
        partner_ids,
        company_id,
        only_posted_moves,
        date_to,
        date_from,
        cost_center_ids,
        branch_id
    ):
        domain = [
            ("display_type", "not in", ["line_note", "line_section"]),
            ("date", ">=", date_from),
            ("date", "<=", date_to),
        ]
        if account_ids:
            domain += [("account_id", "in", account_ids)]
        if company_id:
            domain += [("company_id", "=", company_id)]
        if partner_ids:
            domain += [("partner_id", "in", partner_ids)]
        if only_posted_moves:
            domain += [("move_id.state", "=", "posted")]
        else:
            domain += [("move_id.state", "in", ["posted", "draft"])]

        if cost_center_ids:
            domain += [("analytic_account_ids", "in", cost_center_ids)]
        if branch_id:
            domain += [("branch_id", "=", branch_id)]
                        
        return domain
    
    def _get_period_ml_data(
        self,
        account_ids,
        partner_ids,
        company_id,
        foreign_currency,
        only_posted_moves,
        date_from,
        date_to,
        gen_ld_data,
        cost_center_ids,
        branch_id,
        extra_domain,
        grouped_by,
    ):
        domain = self._get_period_domain(
            account_ids,
            partner_ids,
            company_id,
            only_posted_moves,
            date_to,
            date_from,
            cost_center_ids,
            branch_id
        )
        if extra_domain:
            domain += extra_domain
        ml_fields = self._get_ml_fields()
        move_lines = self.env["account.move.line"].search_read(
            domain=domain, fields=ml_fields, order="date,move_name"
        )
        journal_ids = set()
        full_reconcile_ids = set()
        taxes_ids = set()
        analytic_ids = set()
        branch_ids = set()
        full_reconcile_data = {}
        acc_prt_account_ids = self._get_acc_prt_accounts_ids(company_id, grouped_by)
        for move_line in move_lines:
            journal_ids.add(move_line["journal_id"][0])
            for tax_id in move_line["tax_ids"]:
                taxes_ids.add(tax_id)
            for analytic_account in move_line["analytic_distribution"] or {}:
                analytic_ids.add(int(analytic_account))
            if move_line.get('branch_id',False):
                branch_ids.add(move_line["branch_id"][0])
                
            if move_line["full_reconcile_id"]:
                rec_id = move_line["full_reconcile_id"][0]
                if rec_id not in full_reconcile_ids:
                    full_reconcile_data.update(
                        {
                            rec_id: {
                                "id": rec_id,
                                "name": move_line["full_reconcile_id"][1],
                            }
                        }
                    )
                    full_reconcile_ids.add(rec_id)
            acc_id = move_line["account_id"][0]
            ml_id = move_line["id"]
            if acc_id not in gen_ld_data.keys():
                gen_ld_data[acc_id] = self._initialize_data(foreign_currency)
                gen_ld_data[acc_id]["id"] = acc_id
                gen_ld_data[acc_id]["mame"] = move_line["account_id"][1]
                if grouped_by:
                    gen_ld_data[acc_id][grouped_by] = False
            if acc_id in acc_prt_account_ids:
                item_ids = self._prepare_ml_items(move_line, grouped_by)
                for item in item_ids:
                    item_id = item["id"]
                    if item_id not in gen_ld_data[acc_id]:
                        if grouped_by:
                            gen_ld_data[acc_id][grouped_by] = True
                        gen_ld_data[acc_id][item_id] = self._initialize_data(
                            foreign_currency
                        )
                        gen_ld_data[acc_id][item_id]["id"] = item_id
                        gen_ld_data[acc_id][item_id]["name"] = item["name"]
                    gen_ld_data[acc_id][item_id][ml_id] = self._get_move_line_data(
                        move_line
                    )
                    gen_ld_data[acc_id][item_id]["fin_bal"]["credit"] += move_line[
                        "credit"
                    ]
                    gen_ld_data[acc_id][item_id]["fin_bal"]["debit"] += move_line[
                        "debit"
                    ]
                    gen_ld_data[acc_id][item_id]["fin_bal"]["balance"] += move_line[
                        "balance"
                    ]
                    if foreign_currency:
                        gen_ld_data[acc_id][item_id]["fin_bal"][
                            "bal_curr"
                        ] += move_line["amount_currency"]
            else:
                gen_ld_data[acc_id][ml_id] = self._get_move_line_data(move_line)
            gen_ld_data[acc_id]["fin_bal"]["credit"] += move_line["credit"]
            gen_ld_data[acc_id]["fin_bal"]["debit"] += move_line["debit"]
            gen_ld_data[acc_id]["fin_bal"]["balance"] += move_line["balance"]
            if foreign_currency:
                gen_ld_data[acc_id]["fin_bal"]["bal_curr"] += move_line[
                    "amount_currency"
                ]
        journals_data = self._get_journals_data(list(journal_ids))
        accounts_data = self._get_accounts_data(gen_ld_data.keys())
        taxes_data = self._get_taxes_data(list(taxes_ids))
        analytic_data = self._get_analytic_data(list(analytic_ids))
        rec_after_date_to_ids = self._get_reconciled_after_date_to_ids(
            full_reconcile_data.keys(), date_to
        )
        branch_data = self._get_branch_data(branch_ids)
        return (
            gen_ld_data,
            accounts_data,
            journals_data,
            full_reconcile_data,
            taxes_data,
            analytic_data,
            branch_data,
            rec_after_date_to_ids,
        )    
        
    def _get_report_values(self, docids, data):
        wizard_id = data["wizard_id"]
        company = self.env["res.company"].browse(data["company_id"])
        company_id = data["company_id"]
        date_to = data["date_to"]
        date_from = data["date_from"]
        partner_ids = data["partner_ids"]
        account_ids = data["account_ids"]
        cost_center_ids = data["cost_center_ids"]
        grouped_by = data["grouped_by"]
        hide_account_at_0 = data["hide_account_at_0"]
        foreign_currency = data["foreign_currency"]
        only_posted_moves = data["only_posted_moves"]
        unaffected_earnings_account = data["unaffected_earnings_account"]
        fy_start_date = data["fy_start_date"]
        extra_domain = data["domain"]
        branch_id = data["branch_id"]
        
        gen_ld_data = self._get_initial_balance_data(
            account_ids,
            partner_ids,
            company_id,
            date_from,
            foreign_currency,
            only_posted_moves,
            unaffected_earnings_account,
            fy_start_date,
            cost_center_ids,
            # branch_id,
            extra_domain,
            grouped_by,
        )
        centralize = data["centralize"]
        (
            gen_ld_data,
            accounts_data,
            journals_data,
            full_reconcile_data,
            taxes_data,
            analytic_data,
            branch_data,
            rec_after_date_to_ids,
        ) = self._get_period_ml_data(
            account_ids,
            partner_ids,
            company_id,
            foreign_currency,
            only_posted_moves,
            date_from,
            date_to,
            gen_ld_data,
            cost_center_ids,
            branch_id,
            extra_domain,
            grouped_by,
        )
        general_ledger = self._create_general_ledger(
            gen_ld_data,
            accounts_data,
            grouped_by,
            rec_after_date_to_ids,
            hide_account_at_0,
        )
        if centralize:
            for account in general_ledger:
                if account["centralized"]:
                    centralized_ml = self._get_centralized_ml(
                        account, date_to, grouped_by
                    )
                    account["move_lines"] = centralized_ml
                    account["move_lines"] = self._recalculate_cumul_balance(
                        account["move_lines"],
                        gen_ld_data[account["id"]]["init_bal"]["balance"],
                        rec_after_date_to_ids,
                    )
                    if grouped_by and account[grouped_by]:
                        account[grouped_by] = False
                        del account["list_grouped"]
        general_ledger = sorted(general_ledger, key=lambda k: k["code"])
        total_amount_data={'debit':0,
                           'credit':0,
                           'balance':0,
                           }
        for gd in general_ledger:
            if gd['fin_bal'].get('debit',0):
                if total_amount_data.get('debit',0):
                    total_amount_data['debit']+=gd['fin_bal']['debit']
                    total_amount_data['credit']+=gd['fin_bal']['credit']
                    total_amount_data['balance']+=gd['fin_bal']['balance']
                else:
                    total_amount_data={'debit':gd['fin_bal']['debit'],
                                       'credit':gd['fin_bal']['credit'],
                                       'balance':gd['fin_bal']['balance'],
                                       }
        return {
            "doc_ids": [wizard_id],
            "doc_model": "general.ledger.report.wizard",
            "docs": self.env["general.ledger.report.wizard"].browse(wizard_id),
            "foreign_currency": data["foreign_currency"],
            "company_name": company.display_name,
            "company_currency": company.currency_id,
            "currency_name": company.currency_id.name,
            "date_from": data["date_from"],
            "date_to": data["date_to"],
            "only_posted_moves": data["only_posted_moves"],
            "hide_account_at_0": data["hide_account_at_0"],
            "show_cost_center": data["show_cost_center"],
            "general_ledger": general_ledger,
            "accounts_data": accounts_data,
            "journals_data": journals_data,
            "full_reconcile_data": full_reconcile_data,
            "taxes_data": taxes_data,
            "centralize": centralize,
            "analytic_data": analytic_data,
            "branch_data": branch_data,
            "total_amount_data":total_amount_data,
            "filter_partner_ids": True if partner_ids else False,
            "currency_model": self.env["res.currency"],
        }
        
    # @api.model
    # def _get_period_domain(
    #     self,
    #     account_ids,
    #     partner_ids,
    #     company_id,
    #     only_posted_moves,
    #     date_to,
    #     date_from,
    #     analytic_tag_ids,
    #     cost_center_ids,
    #     branch_id
    # ):
    #     domain = [
    #         ("display_type", "=", False),
    #         ("date", ">=", date_from),
    #         ("date", "<=", date_to),
    #     ]
    #     if account_ids:
    #         domain += [("account_id", "in", account_ids)]
    #     if company_id:
    #         domain += [("company_id", "=", company_id)]
    #     if partner_ids:
    #         domain += [("partner_id", "in", partner_ids)]
    #     if only_posted_moves:
    #         domain += [("move_id.state", "=", "posted")]
    #     if analytic_tag_ids:
    #         domain += [("analytic_tag_ids", "in", analytic_tag_ids)]
    #     if cost_center_ids:
    #         domain += [("analytic_account_id", "in", cost_center_ids)]
    #     if branch_id:
    #         domain += [("branch_id", "=", branch_id)]
    #
    #     return domain
    #
    #
    #
    # @api.model
    # def _get_move_line_data(self, move_line):
    #     result = super(GeneralLedgerReportCompute, self)._get_move_line_data(move_line)
    #     if move_line.get('branch_id',False):
    #         result.update({'branch_id':move_line['branch_id'][0]})
    #     if move_line.get('analytic_account_id',False):
    #         result.update({'analytic_account_id':move_line['analytic_account_id'][0]})
    #     #Гүйлгээний утга нь line дээрх утгаас авах
    #     if move_line.get('name',False):
    #         result.update({'ref':move_line['name']})
    #     return result
    #
    def _get_branch_data(self, branch_ids):
        branchs = self.env["res.branch"].browse(branch_ids)
        branchs_data = {}
        for branch in branchs:
            branchs_data.update({branch.id: {"id": branch.id, "name": branch.name}})
        return branchs_data
    #
    #
    # def _get_analytic_account(self, analytic_account_ids):
    #     analytic_accounts = self.env["account.analytic.account"].browse(analytic_account_ids)
    #     analytic_account_data = {}
    #     for analytic_account in analytic_accounts:
    #         analytic_account_data.update({analytic_account.id: {"id": analytic_account.id, "name": analytic_account.name}})
    #     return analytic_account_data
    #
    #
    # def _get_period_ml_data(
    #     self,
    #     account_ids,
    #     partner_ids,
    #     company_id,
    #     foreign_currency,
    #     only_posted_moves,
    #     date_from,
    #     date_to,
    #     partners_data,
    #     gen_ld_data,
    #     partners_ids,
    #     analytic_tag_ids,
    #     cost_center_ids,
    #     branch_id,
    #     extra_domain,
    # ):
    #     domain = self._get_period_domain(
    #         account_ids,
    #         partner_ids,
    #         company_id,
    #         only_posted_moves,
    #         date_to,
    #         date_from,
    #         analytic_tag_ids,
    #         cost_center_ids,
    #         branch_id
    #     )
    #     if extra_domain:
    #         domain += extra_domain
    #     ml_fields = [
    #         "id",
    #         "name",
    #         "date",
    #         "move_id",
    #         "journal_id",
    #         "account_id",
    #         "partner_id",
    #         "debit",
    #         "credit",
    #         "balance",
    #         "currency_id",
    #         "full_reconcile_id",
    #         "tax_ids",
    #         "analytic_tag_ids",
    #         "amount_currency",
    #         "ref",
    #         "name",
    #         "branch_id",
    #         "analytic_account_id",
    #     ]
    #     move_lines = self.env["account.move.line"].search_read(
    #         domain=domain, fields=ml_fields
    #     )
    #     journal_ids = set()
    #     full_reconcile_ids = set()
    #     taxes_ids = set()
    #     tags_ids = set()
    #     branch_ids = set()
    #     full_reconcile_data = {}
    #     acc_prt_account_ids = self._get_acc_prt_accounts_ids(company_id)
    #     for move_line in move_lines:
    #         journal_ids.add(move_line["journal_id"][0])
    #         for tax_id in move_line["tax_ids"]:
    #             taxes_ids.add(tax_id)
    #         if move_line.get('branch_id',False):
    #             branch_ids.add(move_line["branch_id"][0])
    #         for analytic_tag_id in move_line["analytic_tag_ids"]:
    #             tags_ids.add(analytic_tag_id)
    #
    #         if move_line["full_reconcile_id"]:
    #             rec_id = move_line["full_reconcile_id"][0]
    #             if rec_id not in full_reconcile_ids:
    #                 full_reconcile_data.update(
    #                     {
    #                         rec_id: {
    #                             "id": rec_id,
    #                             "name": move_line["full_reconcile_id"][1],
    #                         }
    #                     }
    #                 )
    #                 full_reconcile_ids.add(rec_id)
    #         acc_id = move_line["account_id"][0]
    #         ml_id = move_line["id"]
    #         if move_line["partner_id"]:
    #             prt_id = move_line["partner_id"][0]
    #             partner_name = move_line["partner_id"][1]
    #         if acc_id not in gen_ld_data.keys():
    #             gen_ld_data = self._initialize_account(
    #                 gen_ld_data, acc_id, foreign_currency
    #             )
    #         if acc_id in acc_prt_account_ids:
    #             if not move_line["partner_id"]:
    #                 prt_id = 0
    #                 partner_name = "Missing Partner"
    #             partners_ids.append(prt_id)
    #             partners_data.update({prt_id: {"id": prt_id, "name": partner_name}})
    #             if prt_id not in gen_ld_data[acc_id]:
    #                 gen_ld_data = self._initialize_partner(
    #                     gen_ld_data, acc_id, prt_id, foreign_currency
    #                 )
    #             gen_ld_data[acc_id][prt_id][ml_id] = self._get_move_line_data(move_line)
    #             gen_ld_data[acc_id][prt_id]["fin_bal"]["credit"] += move_line["credit"]
    #             gen_ld_data[acc_id][prt_id]["fin_bal"]["debit"] += move_line["debit"]
    #             gen_ld_data[acc_id][prt_id]["fin_bal"]["balance"] += move_line[
    #                 "balance"
    #             ]
    #             if foreign_currency:
    #                 gen_ld_data[acc_id][prt_id]["fin_bal"]["bal_curr"] += move_line[
    #                     "amount_currency"
    #                 ]
    #         else:
    #             gen_ld_data[acc_id][ml_id] = self._get_move_line_data(move_line)
    #         gen_ld_data[acc_id]["fin_bal"]["credit"] += move_line["credit"]
    #         gen_ld_data[acc_id]["fin_bal"]["debit"] += move_line["debit"]
    #         gen_ld_data[acc_id]["fin_bal"]["balance"] += move_line["balance"]
    #         if foreign_currency:
    #             gen_ld_data[acc_id]["fin_bal"]["bal_curr"] += move_line[
    #                 "amount_currency"
    #             ]
    #     journals_data = self._get_journals_data(list(journal_ids))
    #     accounts_data = self._get_accounts_data(gen_ld_data.keys())
    #     taxes_data = self._get_taxes_data(list(taxes_ids))
    #     tags_data = self._get_tags_data(list(tags_ids))
    #     branch_data = self._get_branch_data(branch_ids)
    #     rec_after_date_to_ids = self._get_reconciled_after_date_to_ids(
    #         full_reconcile_data.keys(), date_to
    #     )
    #     return (
    #         gen_ld_data,
    #         accounts_data,
    #         partners_data,
    #         journals_data,
    #         full_reconcile_data,
    #         taxes_data,
    #         tags_data,
    #         branch_data,
    #         rec_after_date_to_ids,
    #     )
    #


    
    # def _get_report_values(self, docids, data):
    #     wizard_id = data["wizard_id"]
    #     company = self.env["res.company"].browse(data["company_id"])
    #     company_id = data["company_id"]
    #     date_to = data["date_to"]
    #     date_from = data["date_from"]
    #     partner_ids = data["partner_ids"]
    #     if not partner_ids:
    #         filter_partner_ids = False
    #     else:
    #         filter_partner_ids = True
    #     account_ids = data["account_ids"]
    #     analytic_tag_ids = data["analytic_tag_ids"]
    #     cost_center_ids = data["cost_center_ids"]
    #     show_partner_details = data["show_partner_details"]
    #     hide_account_at_0 = data["hide_account_at_0"]
    #     foreign_currency = data["foreign_currency"]
    #     only_posted_moves = data["only_posted_moves"]
    #     unaffected_earnings_account = data["unaffected_earnings_account"]
    #     fy_start_date = data["fy_start_date"]
    #     extra_domain = data["domain"]
    #
    #     branch_id = data["branch_id"]
    #
    #     gen_ld_data, partners_data, partners_ids = self._get_initial_balance_data(
    #         account_ids,
    #         partner_ids,
    #         company_id,
    #         date_from,
    #         foreign_currency,
    #         only_posted_moves,
    #         unaffected_earnings_account,
    #         fy_start_date,
    #         analytic_tag_ids,
    #         cost_center_ids,
    #         extra_domain,
    #     )
    #     centralize = data["centralize"]
    #     (
    #         gen_ld_data,
    #         accounts_data,
    #         partners_data,
    #         journals_data,
    #         full_reconcile_data,
    #         taxes_data,
    #         tags_data,
    #         branch_data,
    #         rec_after_date_to_ids,
    #     ) = self._get_period_ml_data(
    #         account_ids,
    #         partner_ids,
    #         company_id,
    #         foreign_currency,
    #         only_posted_moves,
    #         date_from,
    #         date_to,
    #         partners_data,
    #         gen_ld_data,
    #         partners_ids,
    #         analytic_tag_ids,
    #         cost_center_ids,
    #         branch_id,
    #         extra_domain,
    #     )
    #     general_ledger = self._create_general_ledger(
    #         gen_ld_data,
    #         accounts_data,
    #         show_partner_details,
    #         rec_after_date_to_ids,
    #         hide_account_at_0,
    #     )
    #     if centralize:
    #         for account in general_ledger:
    #             if account["centralized"]:
    #                 centralized_ml = self._get_centralized_ml(account, date_to)
    #                 account["move_lines"] = centralized_ml
    #                 account["move_lines"] = self._recalculate_cumul_balance(
    #                     account["move_lines"],
    #                     gen_ld_data[account["id"]]["init_bal"]["balance"],
    #                     rec_after_date_to_ids,
    #                 )
    #                 if account["partners"]:
    #                     account["partners"] = False
    #                     del account["list_partner"]
    #     general_ledger = sorted(general_ledger, key=lambda k: k["code"])
    #     return {
    #         "doc_ids": [wizard_id],
    #         "doc_model": "general.ledger.report.wizard",
    #         "docs": self.env["general.ledger.report.wizard"].browse(wizard_id),
    #         "foreign_currency": data["foreign_currency"],
    #         "company_name": company.display_name,
    #         "company_currency": company.currency_id,
    #         "currency_name": company.currency_id.name,
    #         "date_from": data["date_from"],
    #         "date_to": data["date_to"],
    #         "only_posted_moves": data["only_posted_moves"],
    #         "hide_account_at_0": data["hide_account_at_0"],
    #         "show_analytic_tags": data["show_analytic_tags"],
    #         "show_cost_center": data["show_cost_center"],
    #         "general_ledger": general_ledger,
    #         "accounts_data": accounts_data,
    #         "partners_data": partners_data,
    #         "journals_data": journals_data,
    #         "full_reconcile_data": full_reconcile_data,
    #         "taxes_data": taxes_data,
    #         "centralize": centralize,
    #         "tags_data": tags_data,
    #         "branch_data": branch_data,
    #         "filter_partner_ids": filter_partner_ids,
    #     }                        