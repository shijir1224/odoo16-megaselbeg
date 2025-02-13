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

from odoo import api, fields, models, _

class account_budget_change(models.TransientModel):
    _name = "account.budget.change"
    _description = "Line change"
 
    name= fields.Char('Name',required=True, )
    request_id = fields.Many2one('payment.request', string='Хүсэлт',)
    budget_id = fields.Many2one('mw.account.budget.period.line.line', 'Төсөв')
    
    @api.model
    def default_get(self, fields):
        rec = super(account_budget_change, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
#         department_id=False
        if context.get('active_model',False) and context['active_model']=='payment.request':
            statement_line=self.env['payment.request']
            line=statement_line.browse(active_ids)[0]
            name=line.name
            rec['name'] = name
            if line.budget_id:
                budget_id=line.budget_id.id
                rec['budget_id'] = budget_id
            rec['request_id']=line.id
        return rec

    def account_budget_change(self):
        result_context=dict(self._context or {})
        vals={}
        if self.budget_id:
            vals.update({'budget_id':self.budget_id.id,'is_budget':True})
#         if self.name:
#             vals.update({'narration_text':self.name})
            
        self.request_id.write(vals)
        return True
    
