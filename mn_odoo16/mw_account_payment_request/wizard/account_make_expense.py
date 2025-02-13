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

from lxml import etree

from odoo import fields, models, api, _
from odoo.exceptions import UserError


class AccountPaymentExpense(models.TransientModel):
    """
        Төлбөрийн хүсэлт дээр үндэслэн харилцахын зарлага үүсгэнэ.
    """
    _name = "account.payment.expense"
    _inherit = "analytic.mixin"
    _description = "Payment Request Make Expense"

    def _default_partner(self):
        context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_id', False):
            payment = payment_obj.browse(context['active_id'])
            if payment and payment.partner_id:
                return payment.partner_id.id
            else:
                return False
        else:
            return False
    def _default_currency(self):
        context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_id', False):
            payment = payment_obj.browse(context['active_id'])
            if payment and payment.currency_id:
                return payment.currency_id.id
            else:
                return False
        else:
            return False

    def _default_amount(self):
        context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_ids', False):
            payments = payment_obj.browse(context['active_ids'])
            amount=0
            for payment in payments:
             amount+= payment.confirmed_amount or payment.amount
            return amount

    def _default_journal_id(self):
        context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_id', False):
            payment = payment_obj.browse(context['active_id'])
            journal = payment.journal_id and payment.journal_id.id or False
            return journal
            
    def _default_ref_or_nurration(self):
        context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_id', False):
            payment = payment_obj.browse(context['active_id'])
            payment_ref = payment.payment_ref or ''
            return payment_ref
            

    def _default_cash_type_id(self):
        context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_id', False):
            payment = payment_obj.browse(context['active_id'])
            cash_type = payment.cash_type_id and payment.cash_type_id.id or False
            return cash_type

    def _default_ex_account_id(self):
        context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_id', False):
            payment = payment_obj.browse(context['active_id'])
            account = payment.ex_account_id and payment.ex_account_id.id or False
            return account

    def _default_invoice_id(self):
        context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_id', False):
            payment = payment_obj.browse(context['active_id'])
            invoice_id = payment.move_id and payment.move_id.id or False
            return invoice_id
        return False
    # cash_journal_id = fields.Many2one('account.journal', 'Журнал', required=True,  domain=[('type', 'in', ['bank', 'cash'])])
    company_id = fields.Many2one('res.company', 'Компани', required=True,
                                 default=lambda self: self.env.user.company_id.id, )
    account_id = fields.Many2one('account.account', 'Харьцсан данс', default=_default_ex_account_id)
    date = fields.Date('Date', default=time.strftime('%Y-%m-%d'))
    amount = fields.Float('Дүн', default=_default_amount)
    type = fields.Selection([
        ('supplier', 'Supplier'),
        ('customer', 'Customer'),
        ('general', 'General')
    ], 'Expense Type', required=True, default='general')
    partner_id = fields.Many2one('res.partner', 'Харилцагч', default=_default_partner)
    currency_id = fields.Many2one('res.currency', 'Валют',  default=_default_currency)
    cash_type_id = fields.Many2one('account.cash.move.type', 'МГТөрөл', default=_default_cash_type_id)
    invoice_id = fields.Many2one('account.move', default=_default_invoice_id)
    journal_id = fields.Many2one('account.journal', 'Журнал', default=_default_journal_id,
                                 domain=[('type', 'in', ['bank', 'cash'])])
    payment_ref = fields.Char(string="Гүйлгээний утга", default=_default_ref_or_nurration)

    
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        # TODO: Буруу шийдэл domain constrain зэргийг буруу шийдлээр хөгжүүлсэн байна.
        res = super(AccountPaymentExpense, self).fields_view_get(view_id, view_type, toolbar, submenu)
        context = self.env.context
        if view_type != 'form':
            return res

        if not (self._context.get('active_model') and self._context.get('active_id')):
            return res

        def department_check(dep):  # TODO: Ашиглаагүй функц
            ret = False
            while dep:
                if dep.id == 24:
                    ret = 'da'
                elif dep.id == 25:
                    ret = 'et'
                    break
                #                 prop = getattr(category)
                #                 if prop and prop.id :
                #                     ret = prop.id
                #                     break
                dep = dep.parent_id
            if not ret:
                return 'ub'
            return ret

        if not context:
            return res

        domain = ''
        domain2 = ''
        if context.get('active_model', 'ir.ui.menu') != 'ir.ui.menu':
            dep_pool = self.env['hr.department']
            request = self.env['payment.request'].browse(context['active_id'])
            doc = etree.XML(res['arch'])
            nodes = doc.xpath("//form")
            #             account_ids = repo.account_ids.mapped('id')
            #             domain2="[('id','in',"+account_ids.__repr__()+"),('type','=','account')]"

            for node in nodes:
                if request.type in ('cash', 'talon'):
                    node.set('string', _('Make Cash Expense'))
                else:
                    node.set('string', _('Make Bank Expense'))
            #             nodes = doc.xpath("//field[@name='statement_id']")
            #             statement_ids = []
            #             for node in nodes:
            journal_id = False
            if request.journal_id:
                journal_id = request.journal_id.id
            if request.type in ('cash', 'talon'):
                #                 node.set('string', _('Cash Statement'))

                if journal_id:
                    self.env.cr.execute("select s.id from account_bank_statement s "
                                        "join account_journal j on (s.journal_id=j.id) "
                                        "where s.state in ('draft','open') and j.type = 'cash' and j.id={}".format(journal_id))
                else:
                    self.env.cr.execute("select s.id from account_bank_statement s "
                                        "join account_journal j on (s.journal_id=j.id) "
                                        "where s.state in ('draft','open') and j.type = 'cash'")

            else:
                if journal_id:
                    self.env.cr.execute("select s.id from account_bank_statement s "
                                        "join account_journal j on (s.journal_id=j.id) "
                                        "where s.state in ('draft','open') and j.type = 'bank' and j.id={}".format(journal_id))
                else:
                    self.env.cr.execute("select s.id from account_bank_statement s "
                                        "join account_journal j on (s.journal_id=j.id) "
                                        "where s.state in ('draft','open') and j.type = 'bank'")


        view = '''<?xml version="1.0" encoding="utf-8"?>
                                    <form>
                    <group col="2" colspan="4">
                     <field name="company_id" widget="selection" string="Компани" required="1"/>
                     <field name="invoice_id" readonly="1" force_save="1" invisible="1"/>
                     <field name="date" readonly="1" string="Огноо" required="1"/>
                     <field name="amount" />
                     <field name="journal_id" required="1" options="{'no_quick_create':True,'no_create_edit':True}"/>
<!--                      <field name="analytic_id"/> -->
                    </group>
                    <separator string="" colspan="4"/>
                    <footer>
                        <button special="cancel" string="Болих" class="btn-danger"/>
                        <button string="Төлөх" name="action_create" type="object" class="btn-success"/>
                    </footer>
               </form>
                    ''' % domain

#                      <field name="account_id" string="Данс" attrs="{'required': [('invoice_id', '!=', False)]}" options="{'no_quick_create':True,'no_create_edit':True}"/>
#                      <field name="partner_id" string="Харилцагч" options="{'no_quick_create':True,'no_create_edit':True}"/>
#                      <field name="cash_type_id" string="МГ төрөл"/>

        #                     domain="%s"
        #             domain2
        # TODO: Утгагүй шийдэл харагдацыг ашиглаж домэйн-г odoo-гийн үндсэн шийдлийн дагуу хийх шаардлагатай. Харагдацыг 2 зурах нь буруу
        res.update({
            'arch': view
        })
        #         print ("domain2:",domain)
        return res

    #     @api.model
    #     def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #         res = super(BaseModuleUpgrade, self).fields_view_get(view_id, view_type, toolbar=toolbar,submenu=False)
    #         if view_type != 'form':
    #             return res
    #
    #         if not(self._context.get('active_model') and self._context.get('active_id')):
    #             return res
    #
    #         if not self.get_module_list():
    #             res['arch'] = '''<form string="Upgrade Completed">
    #                                 <separator string="Upgrade Completed" colspan="4"/>
    #                                 <footer>
    #                                     <button name="config" string="Start Configuration" type="object" class="btn-primary"/>
    #                                     <button special="cancel" string="Close" class="btn-secondary"/>
    #                                 </footer>
    #                              </form>'''
    #
    #         return res

    def action_create(self):
        """Сонгогдсон кассын баримтанд зарлага үүсгэнэ.
        """
        context = self.env.context
        #         if not context or not context.has_key('active_id') or not context['active_id']:
        #             return {'type': 'ir.actions.act_window_close'}
        
        multi=False
        if len(context['active_ids'])>1:
            multi=True
        self.env['payment.request'].browse(context['active_ids']).with_context(multi=multi).create_payment(self)

        return {'type': 'ir.actions.act_window_close'}
