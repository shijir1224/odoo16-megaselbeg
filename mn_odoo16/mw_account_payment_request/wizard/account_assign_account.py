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

from odoo import fields, models, api, _  # @UnresolvedImport
from odoo.exceptions import UserError, ValidationError  # @UnresolvedImport

class account_assign_account(models.TransientModel):
    """
        Төлбөрийн хүсэлт дээр үндэслэн харилцахын зарлага үүсгэнэ.
    """
    _name = "account.assign.account"
    _description = "Payment Request Make Expense"
    
    TYPE_Selection = [
                      ('cash',u'Бэлнээр'),
                      ('bank',u'Банкны шилжүүлгээр'),
                      ('pretty',u'Жижиг мөнгөн сангаас'),
                      ('credit_card',u'Кредит картаар'),
                      ('transfer',u'Хоорондын тооцоо'),
    ]
        
    def _default_partner(self):
        context = context = self.env.context
        payment_obj = self.env['payment.request']
        if context and context.get('active_id',False):
            payment=payment_obj.browse(context['active_id'])
            if payment and payment.partner_id:
                return payment.partner_id.id
            else:
                False
        else:
            return False
                
    user_id= fields.Many2one('res.users', 'Accountant')
    type = fields.Selection(TYPE_Selection, 'Request Type', required=True, default='cash')
    
#     partner_id= fields.Many2one('res.partner', 'Partner',default=_default_partner)

    
    def action_create(self):
        context = context = self.env.context
        print ('context----: ',context)
        form = self
        self.env['payment.request'].browse(context['active_ids']).accountant_set(form)
        
        return {'type': 'ir.actions.act_window_close'}

account_assign_account()


class account_assign_account_line(models.TransientModel):
    """
        Төлбөрийн хүсэлт дээр үндэслэн харилцахын зарлага үүсгэнэ.
    """
    _name = "account.assign.account.line"
    _description = "Payment Request line"
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
