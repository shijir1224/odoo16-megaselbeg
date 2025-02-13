# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"


    def get_initial_balance(self, company_id, account_ids, date_start, target_move):
        ''' Тухайн дансны тайлант хугацааны эхний үлдэгдлийг олно.
        '''
        where = " "
        join = " "
        select = " "
        sub_select = " "
        group_by = " "
        if target_move == 'posted':
            where += "AND m.state = 'posted'"
        if self.env.context.get('journal_ids', False):
            journal_ids = self.env.context.get('journal_ids', False)
            sub_select += ", ml.journal_id AS journal_id "
            select += ", j.id AS jid, j.name AS jname "
            join += "LEFT JOIN account_journal j ON (j.id = mv.journal_id) "
            group_by += ", j.id, j.name "
            where += ' AND ml.journal_id in ('+','.join(map(str, journal_ids))+') '
            #where += "AND ml.journal_id in %s " %tuple(journal_ids)
        if self.env.context.get('partner_ids', False):
            partner_ids = self.env.context.get('partner_ids', False)
            sub_select += ", ml.partner_id AS partner_id "
            select += ", p.id AS pid, p.name AS pname "
            join += "LEFT JOIN res_partner p ON (p.id = mv.partner_id) "
            group_by += ", p.id, p.name "
            where += ' AND ml.partner_id in ('+','.join(map(str, partner_ids))+') '
        self.env.cr.execute("SELECT mv.account_id AS account_id, aa.code AS code, aa.name AS name, cur.id AS currency_id, cur.name AS currency, "
                                    "sum(mv.debit) AS start_debit, sum(mv.credit) AS start_credit, "
                                    "sum(mv.cur_debit) AS cur_start_debit, sum(mv.cur_credit) AS cur_start_credit, "
                                    "0 AS debit, 0 AS credit, 0 AS cur_debit, 0 AS cur_credit "
                                                        + select + ""
                             "FROM     (SELECT  ml.account_id AS account_id, ml.debit AS debit, "
                                                "ml.credit AS credit, "
                                                "CASE WHEN ml.amount_currency > 0 "
                                                "THEN ml.amount_currency ELSE 0 END AS cur_debit, "
                                                "CASE WHEN ml.amount_currency < 0 "
                                                "THEN abs(ml.amount_currency) ELSE 0 END AS cur_credit "
                                                        + sub_select + ""
                                        "FROM account_move_line ml "
                                        "LEFT JOIN account_move m ON (ml.move_id = m.id) "
                                        "WHERE m.date <= %s AND ml.account_id in %s " + where + ""
                                              "AND m.state = 'posted' AND ml.company_id = %s) AS mv "
                             "LEFT JOIN account_account aa ON (mv.account_id = aa.id) "  +
                             "LEFT JOIN res_currency cur ON cur.id = aa.currency_id " + join + ""
                             "GROUP BY mv.account_id, aa.code, aa.name, cur.id, cur.name " + group_by + ""
                             "ORDER BY aa.code, aa.name ",
                             (date_start, tuple(account_ids), company_id))
        a=self.env.cr.dictfetchall()
        print ('aa ',a)
        return a

    def get_balance(self, company_id, account_ids, date_start, date_stop, target_move, without_profit_revenue=False):
        ''' Тухайн дансны тайлант хугацааны хоорондох дүнг олно.
        '''
        where = " "
        join = " "
        select = " "
        sub_select = " "
        group_by = " "

        # check period journal
        if without_profit_revenue:
            company = self.env['res.company'].browse(company_id)
            if not company.period_journal_id:
                raise ValidationError(_('Please configure period journal on account settings.'))
            else:
                where += 'AND ml.journal_id != %s ' % company.period_journal_id.id

        if target_move == 'posted':
            where += "AND m.state = 'posted'"
        if self.env.context.get('journal_ids', False):
            journal_ids = self.env.context.get('journal_ids', False)
            sub_select += ", ml.journal_id AS journal_id "
            select += ", j.id AS jid, j.name AS jname "
            join += "LEFT JOIN account_journal j ON (j.id = mv.journal_id) "
            group_by += ", j.id, j.name "
            where += ' AND ml.journal_id in ('+','.join(map(str, journal_ids))+') '

        if self.env.context.get('partner_ids', False):
            partner_ids = self.env.context.get('partner_ids', False)
            sub_select += ", ml.partner_id AS partner_id "
            select += ", p.id AS pid, p.name AS pname "
            join += "LEFT JOIN res_partner p ON (p.id = mv.partner_id) "
            group_by += ", p.id, p.name "
            where += ' AND ml.partner_id in ('+','.join(map(str, partner_ids))+') '
        self.env.cr.execute("SELECT mv.account_id AS account_id, aa.code AS code, aa.name AS name, cur.id AS currency_id, cur.name AS currency, "
                                    "sum(mv.debit) AS debit, sum(mv.credit) AS credit, "
                                    "sum(mv.cur_debit) AS cur_debit, sum(mv.cur_credit) AS cur_credit, "
                                    "0 AS start_debit, 0 AS start_credit, 0 AS cur_start_debit, 0 AS cur_start_credit "
                                                        + select + ""
                            "FROM     (SELECT  ml.account_id AS account_id, ml.debit AS debit, "
                                                "ml.credit AS credit, "
                                                "CASE WHEN ml.amount_currency > 0 "
                                                "THEN ml.amount_currency ELSE 0 END AS cur_debit, "
                                                "CASE WHEN ml.amount_currency < 0 "
                                                "THEN abs(ml.amount_currency) ELSE 0 END AS cur_credit "
                                                        + sub_select + ""
                                        "FROM account_move_line ml "
                                        "LEFT JOIN account_move m ON (ml.move_id = m.id) "
                                        "WHERE m.date BETWEEN %s AND %s AND ml.account_id in %s " + where + ""
                                              "AND m.state = 'posted' AND ml.company_id = %s) AS mv "
                             "LEFT JOIN account_account aa ON (mv.account_id = aa.id) " +
                             "LEFT JOIN res_currency cur ON cur.id = aa.currency_id "+ join + ""
                             "GROUP BY mv.account_id, aa.code, aa.name, cur.id, cur.name " + group_by + ""
                             "ORDER BY aa.code, aa.name",
                             (date_start, date_stop, tuple(account_ids), company_id))
        return self.env.cr.dictfetchall()

    def get_all_disc_balance(self, company_id, account_ids, date_start, date_stop, target_move):
        ''' Тухайн дансны эхний үлдэгдэл болон тайлант хугацааны хоорондох дүнг олно.
        '''
        where = " "
        join = " "
        select = " "
        sub_select = " "
        sub_join = " "
        group_by = " "
        if self.env.context.get('order_by', False):
            order_by = self.env.context.get('order_by')
        if not self.env.context.get('order_by', False):
            order_by = "aa.code, aa.name "
        if target_move == 'posted':
            where += "AND m.state = 'posted'"
        if self.env.context.get('journal_ids', False):
            journal_ids = self.env.context.get('journal_ids', False)
            sub_select += ", ml.journal_id AS journal_id "
            select += ", j.id AS jid, j.name AS jname "
            join += "LEFT JOIN account_journal j ON (j.id = mv.journal_id) "
            group_by += ", j.id, j.name "
            where += ' AND ml.journal_id in ('+','.join(map(str, journal_ids))+') '

        if self.env.context.get('partner_ids', False):
            partner_ids = self.env.context.get('partner_ids', False)
            sub_select += ", ml.partner_id AS partner_id "
            select += ", p.id AS pid, p.name AS pname "
            join += "LEFT JOIN res_partner p ON (p.id = mv.partner_id) "
            group_by += ", p.id, p.name "
            where += ' AND ml.partner_id in ('+','.join(map(str, partner_ids))+') '
            if not self.env.context.get('order_by', False):
                order_by += "p.name "
        # Харилцагчын товчоо тайланг борлуулалтын ажилтнаар бүлэглэсэн утга авах
        if self.env.context.get('salesman_ids',False):
            salesman_ids = self.env.context.get('salesman_ids', False)
            sub_select += ", ml.invoice_id AS invoice, ai.user_id as salesman "
            select += ", mv.invoice as invoice, mv.salesman as salesman "
            join += " LEFT JOIN res_users ru on (ru.id = mv.salesman) "
            sub_join += " LEFT JOIN account_invoice ai on (ml.invoice_id = ai.id) "
            group_by += ", ru.id, mv.salesman, mv.invoice "
            where += ' AND ai.user_id in ('+','.join(map(str, salesman_ids))+') '

        self.env.cr.execute("SELECT mv.account_id AS account_id, COALESCE(aa.code, '') AS acode, "
                                    "COALESCE(aa.name, '') AS aname, COALESCE(rc.name, '') AS cname, "
                                    "sum(mv.start_balance) AS start_balance, sum(mv.cur_start_balance) AS cur_start_balance, "
                                    "sum(mv.debit) AS debit, sum(mv.credit) AS credit, COALESCE(aa.internal_type, '') AS atype, "
                                    "sum(mv.cur_debit) AS cur_debit, sum(mv.cur_credit) AS cur_credit "
                                                        + select + ""
                            "FROM     (SELECT  ml.account_id AS account_id, "
                                                "CASE WHEN (ml.debit > 0 OR ml.credit > 0) AND ml.date < %s "
                                                "THEN COALESCE(ml.debit - ml.credit, 0) ELSE 0 END AS start_balance, "
                                                "CASE WHEN ml.amount_currency != 0  and ml.date < %s "
                                                "THEN COALESCE(amount_currency, 0) ELSE 0 END AS cur_start_balance, "
                                                "CASE WHEN ml.debit > 0 AND m.date BETWEEN %s AND %s"
                                                "THEN COALESCE(ml.debit,0) ELSE 0 END AS debit, "
                                                "CASE WHEN ml.credit > 0 AND m.date BETWEEN %s AND %s "
                                                "THEN COALESCE(ml.credit,0) ELSE 0 END AS credit, "
                                                "CASE WHEN ml.amount_currency > 0  AND m.date BETWEEN %s AND %s "
                                                "THEN ml.amount_currency ELSE 0 END AS cur_debit, "
                                                "CASE WHEN ml.amount_currency < 0  AND m.date BETWEEN %s AND %s "
                                                "THEN abs(ml.amount_currency) ELSE 0 END AS cur_credit "
                                                        + sub_select + ""
                                        "FROM account_move_line ml "
                                        "LEFT JOIN account_move m ON (ml.move_id = m.id) " + sub_join + ""
                                        "WHERE ml.account_id in %s " + where + ""
                                              "AND m.state = 'posted' AND ml.company_id = %s) AS mv "
                            "LEFT JOIN account_account aa ON (mv.account_id = aa.id) "
                            "LEFT JOIN res_currency rc ON (aa.currency_id = rc.id) " + join + ""
                            "GROUP BY mv.account_id, aa.code, aa.name, rc.name, aa.internal_type " + group_by + ""
                            "ORDER BY " + order_by,
                             (date_start, date_start, date_start, date_stop, date_start, date_stop, date_start,
                              date_stop, date_start, date_stop, tuple(account_ids), company_id))
        return self.env.cr.dictfetchall()


    def get_partner_balance(self, company_id, account_ids, date_start, date_stop, target_move):
        ''' Тухайн дансны эхний үлдэгдэл болон тайлант хугацааны хоорондох дүнг олно.
        '''
        where = " "
        join = " "
        sub_join = " "
        select = " "
        sub_select = " "
        group_by = " "
        if self.env.context.get('order_by', False):
            order_by = self.env.context.get('order_by')
        if target_move == 'posted':
            where += "AND m.state = 'posted'"

        if self.env.context.get('partner_ids', False):
            partner_ids = self.env.context.get('partner_ids', False)
            sub_select += ", ml.partner_id AS partner_id "
            select += ", p.id AS pid, p.name AS pname "
            join += "LEFT JOIN res_partner p ON (p.id = mv.partner_id) "
            group_by += ", p.id, p.name "
            where += ' AND ml.partner_id in ('+','.join(map(str, partner_ids))+') '
            if not self.env.context.get('order_by', False):
                order_by += ", p.name "
        # Харилцагчын баланс тайланд борлуулалтын ажилтнаар бүлэглэх үед утга олгох
        if self.env.context.get('salesman_ids',False):
            salesman_ids = self.env.context.get('salesman_ids', False)
            sub_select += ", ai.user_id as salesman_id "
            select += ", mv.invoice as invoice, mv.salesman_id as salesman_id "
            join += " LEFT JOIN res_users ru on (ru.id = mv.salesman_id) "
            sub_join += " LEFT JOIN account_invoice ai on (ml.invoice_id = ai.id) "
            group_by += ", ru.id, mv.salesman_id, mv.invoice "
            where += ' AND ai.user_id in ('+','.join(map(str, salesman_ids))+') '

        self.env.cr.execute("SELECT mv.account_id AS account_id, COALESCE(aa.code, '') AS acode, "
                                    "COALESCE(aa.name, '') AS aname, COALESCE(rc.name, '') AS cname, "
                                    "mv.start_balance AS start_balance, mv.cur_start_balance AS cur_start_balance, "
                                    "mv.debit AS debit, mv.credit AS credit, COALESCE(aa.internal_type, '') AS atype, "
                                    "mv.cur_debit AS cur_debit, mv.cur_credit AS cur_credit, mv.name AS name, mv.ml_id AS ml_id, mv.ref AS ref, mv.ml_date as ml_date, mv.rec AS rec, mv.cid AS cid, mv.invoice AS invoice, "
                                    "mv.currency_rate as currency_rate"
                                                        + select + ""
                            "FROM     (SELECT  ml.account_id AS account_id, "
                                                "CASE WHEN (ml.debit > 0 OR ml.credit > 0) AND ml.date < %s "
                                                "THEN COALESCE(ml.debit - ml.credit, 0) ELSE 0 END AS start_balance, "
                                                "CASE WHEN ml.amount_currency != 0  and ml.date < %s "
                                                "THEN COALESCE(amount_currency, 0) ELSE 0 END AS cur_start_balance, "
                                                "CASE WHEN ml.debit > 0 AND m.date BETWEEN %s AND %s"
                                                "THEN COALESCE(ml.debit,0) ELSE 0 END AS debit, "
                                                "CASE WHEN ml.credit > 0 AND m.date BETWEEN %s AND %s "
                                                "THEN COALESCE(ml.credit,0) ELSE 0 END AS credit, "
                                                "CASE WHEN ml.amount_currency > 0  AND m.date BETWEEN %s AND %s "
                                                "THEN ml.amount_currency ELSE 0 END AS cur_debit, "
                                                "CASE WHEN ml.amount_currency < 0  AND m.date BETWEEN %s AND %s "
                                                "THEN abs(ml.amount_currency) ELSE 0 END AS cur_credit "
                                                ", ml.name AS name , ml.id as ml_id, ml.ref As ref, ml.date AS ml_date, ml.currency_rate AS currency_rate, ml.full_reconcile_id AS rec, ml.currency_id AS cid, ml.invoice_id AS invoice"
                                                        + sub_select + ""
                                        "FROM account_move_line ml "
                                        "LEFT JOIN account_move m ON (ml.move_id = m.id) " + sub_join + ""
                                        "WHERE ml.account_id in %s " + where + ""
                                              "AND m.state = 'posted' AND ml.company_id = %s) AS mv "
                            "LEFT JOIN account_account aa ON (mv.account_id = aa.id) "
                            "LEFT JOIN res_currency rc ON (aa.currency_id = rc.id) " + join + ""
#                             "GROUP BY mv.account_id, aa.code, aa.name, rc.name, aa.internal_type " + group_by + ""
                            "ORDER BY " + order_by,
                             (date_start, date_start, date_start, date_stop, date_start, date_stop, date_start,
                              date_stop, date_start, date_stop, tuple(account_ids), company_id))
        return self.env.cr.dictfetchall()
    
