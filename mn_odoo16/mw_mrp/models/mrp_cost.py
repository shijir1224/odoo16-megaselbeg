# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from datetime import date, datetime

class MRPProductExpenseCostLine(models.Model):
    '''
        Шууд хөдөлмөрийн болон бусад бүтэлийн сангийн өртөг
        ҮНЗ стандарт өртөг
    '''
    _name = 'mrp.product.standart.cost.line'
    _description = 'Бүтээгдэхүүний зардал хуваарилалт тохиргоо мөр'

    name = fields.Char(required=True, tracking=True, )
    price_unit = fields.Float(string='Стандарт өртөг', )
    parent_id = fields.Many2one('mrp.product.standart.cost', string='parent', )
    credit_account_id = fields.Many2one('account.account', string='Кредит данс',)
    debit_account_id = fields.Many2one('account.account', string='Дебит данс', )
    move_id = fields.Many2one('account.move', string='Move', )

    branch_id = fields.Many2one('res.branch', string='Салбар', default=lambda self: self.env.user.branch_id.id)
    by_product_id = fields.Many2one('product.product', string='Бараа',)
    # credit_account_id = fields.Many2one('account.account', string='Кредит данс',)
    parent_by_id = fields.Many2one('mrp.product.standart.cost', string='parent by', )

    def write(self, vals):
        res = super(MRPProductExpenseCostLine, self).write(vals)
        if 'price_unit' in vals or 'credit_account_id' in vals or 'debit_account_id' in vals or 'name' in vals:
            history= self.env['mrp.product.standart.cost.history']
            history.create({'name':self.name+u' зассан',
                            'price_unit':vals.get('price_unit',False) and vals['price_unit'],
                            'old_price_unit':self.price_unit,
                            'cost_id':self.parent_id.id,
                            'cost_line_id':self.id,
                            'product_id':self.parent_id.product_id.id
                            })
        return res

    @api.model
    def create(self, vals):
        production = super(MRPProductExpenseCostLine, self).create(vals)
        if 'price_unit' in vals or 'credit_account_id' in vals or 'debit_account_id' in vals or 'name' in vals:
            history= self.env['mrp.product.standart.cost.history']
            history.create({'name':vals['name']+u' үүсгэсэн',
                            'price_unit':vals['price_unit'],
                            'old_price_unit':vals['price_unit'],
                            'cost_id':vals.get('parent_id',False) and vals['parent_id'] or vals.get('parent_by_id',False) and vals['parent_by_id'],
                            # 'cost_line_id':self.id,
                            # 'product_id':self.parent_id.product_id.id
                            })        
        return production
    
class MRPProductExpenseCost(models.Model):
    '''
        Шууд хөдөлмөрийн болон бусад бүтэлийн сангийн өртөг
        ҮНЗ стандарт өртөг
    '''
    _name = 'mrp.product.standart.cost'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'format.address.mixin', 'avatar.mixin','analytic.mixin']
    # _inherit = "analytic.mixin"
    _description = 'Бүтээгдэхүүний зардал хуваарилалт тохиргоо'

    name = fields.Char(required=True, tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    expense_type = fields.Selection([('payroll', 'Шууд хөдөлмөрийн бүтээлийн сан'),
                                  ('unz', 'ҮНЗ стандарт өртөг')], string='Зардал төрөл', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text(readonly=True, states={'draft': [('readonly', False)]})
    parameter = fields.Selection([('mining', 'Олборлох'),
                              ('crush', 'Бутлах'),
                              ('milling', 'Тээрэмдэх')], string='Параметр', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([('tn', 'төгрөг/тн'),
                              ('day', 'төгрөг/хоног')], string='Төрөл', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    price_total = fields.Float(string='Үнэлгээ', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    price_unit = fields.Float(string='Нэгж үнэ', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    account_id = fields.Many2one('account.account', string='Данс', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    credit_account_id = fields.Many2one('account.account', string='Кредит данс', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    debit_account_id = fields.Many2one('account.account', string='Дебит данс', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    product_ids = fields.Many2many('product.product', string='Бүтээгдэхүүн', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Ноорог'), ('done', 'Батлагдсан')], string='Төлөв', default='draft', tracking=True, readonly=True)

    product_id = fields.Many2one('product.product', string='Бараа', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('mrp.product.standart.cost.line', 'parent_id',readonly=True, states={'draft': [('readonly', False)]})
    line_by_ids = fields.One2many('mrp.product.standart.cost.line', 'parent_by_id',readonly=True, states={'draft': [('readonly', False)]})
    total_cost = fields.Float(compute='_compute_total')

    mrp_production_history_count = fields.Integer("Түүх", compute='_compute_mrp_history_count')
    history_ids = fields.One2many('mrp.product.standart.cost.history', 'cost_id')
    branch_id = fields.Many2one('res.branch', string='Салбар',readonly=True, states={'draft': [('readonly', False)]})

# select sum(debit) as d,sum(credit) as c from 
# account_move_line 
# where account_id in (select cl.credit_account_id from  mrp_product_standart_cost c left join mrp_product_standart_cost_line cl on c.id=cl.parent_id where product_id=38716) 
# and date between '2024-03-01' and '2024-03-31' and (
# move_id  in (select move_id from mrp_prod_account_move_st_rel) or 
# move_id  in (select move_id from mrp_prod_account_move_st_close_rel));
# #
#  select sum(l1.debit) as d,sum(l1.credit) as c,sum(l2.credit) as cc from 
#  account_move_line l1,
#  account_move_line l2
#  where 
#  l1.account_id in 
#  (select cl.credit_account_id from  mrp_product_standart_cost c 
#     left join mrp_product_standart_cost_line cl on c.id=cl.parent_id where product_id=38716) and 
# l2.account_id in 
#  (select cl.credit_account_id from  mrp_product_standart_cost c 
#     left join mrp_product_standart_cost_line cl on c.id=cl.parent_id where product_id=38716) and     
#  l1.date between '2024-03-01' and '2024-03-31' and
#   l2.date between '2024-03-01' and '2024-03-31' and 
#  l1.move_id not in (select move_id from mrp_prod_account_move_st_rel) and 
#  l1.move_id not in (select move_id from mrp_prod_account_move_st_close_rel) and
#  l2.move_id  in (select move_id from mrp_prod_account_move_st_rel) and 
#  l2.move_id  in (select move_id from mrp_prod_account_move_st_close_rel);
#
#
#  #
#  select sum(debit) as d,
#  sum(credit) FILTER (where move_id not in (select move_id from mrp_prod_account_move_st_rel) and 
# move_id not in (select move_id from mrp_prod_account_move_st_close_rel)) as c,
# sum(credit) FILTER (where move_id  in (select move_id from mrp_prod_account_move_st_rel) or 
# move_id  in (select move_id from mrp_prod_account_move_st_close_rel)) as cc,
# account_id
#   from 
# account_move_line 
# where account_id in (select cl.credit_account_id from  mrp_product_standart_cost c left join mrp_product_standart_cost_line cl on c.id=cl.parent_id where product_id=38716) 
# and date between '2024-03-01' and '2024-03-31'
# group by account_id
#
#  and 
# move_id not in (select move_id from mrp_prod_account_move_st_rel) and 
# move_id not in (select move_id from mrp_prod_account_move_st_close_rel);

     
    def _compute_mrp_history_count(self):
        for line in self:
            line.mrp_production_history_count = len(line._get_history())

    def _get_history(self):
        self.ensure_one()
        history_moves = self.history_ids
        return history_moves

    def _compute_total(self):
        for order in self:
            order.total_cost = sum(m.price_unit for m in order.line_ids)


    @api.ondelete(at_uninstall=False)
    def _unlink_except_done(self):
        if any(record.state == 'done' for record in self):
            raise UserError((u'Батлагдсан бичлэг устгах боломжгүй.'))
        st_check=[]
        for record in self:
            st_check=self.env['mrp.production'].search([('standart_cost_id','=',record.id)])
        if len(st_check)>0:
            raise UserError((u'Үйлдвэрлэлийн захиалга дээр сонгосон байна.'))
        
    @api.onchange('price_total')
    def onchange_price_total(self):
        for obj in self:
            obj.price_unit = obj.price_total
            if obj.type == 'tn':
                obj.price_unit = round(obj.price_total/1000, 2)


    def compute_all_prod_cost(self, total_qty):
        expense_costs = self.env['mrp.product.standart.cost'].search([('product_ids', 'in', [])])
        for line in expense_costs:
            qty = total_qty/1000
            qty*line.price_total

    def action_draft(self):
        for record in self:
            return record.write({'state': 'draft'})

    def action_done(self):
        for record in self:
            return record.write({'state': 'done'})
        

    def action_view_history_ids(self):
        self.ensure_one()
        history_ids = self._get_history().ids
        action = {
            'res_model': 'mrp.product.standart.cost.history',
            'type': 'ir.actions.act_window',
        }
        if len(history_ids) == 1:
            action.update({
                'view_mode': 'form',
                'res_id': history_ids[0],
            })
        else:
            action.update({
                'name': _("%s History of") % self.name,
                'domain': [('id', 'in', history_ids)],
                'view_mode': 'tree,form',
            })
        return action


class MRPCostCalculate(models.Model):
    '''
        Гүйцэтгэл тооцоолох
    '''
    _name = 'mrp.standart.cost.calc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'format.address.mixin', 'avatar.mixin','analytic.mixin']
    _description = 'Гүйцэтгэл тооцоолох'

    name = fields.Char(required=True, tracking=True, )
    config_id = fields.Many2one('mrp.product.standart.cost', string='Стандарт өртөг', )
    move_id = fields.Many2one('account.move', string='Move', )
    date_start = fields.Date('Эхлэх огноо',required=True, tracking=True, )
    date_end = fields.Date('Дуусах огноо',required=True, tracking=True, )
    line_ids = fields.One2many('mrp.standart.cost.calc.line', 'parent_id')

    state = fields.Selection([('draft', 'Ноорог'), ('done', 'Батлагдсан')], string='Төлөв', default='draft', tracking=True, readonly=True)

 # product_id = fields.Many2one('product.product', string='Бараа', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    total_debit = fields.Float(compute='_compute_total')
    total_credit = fields.Float(compute='_compute_total')
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company,index=True)
    bom_line_ids = fields.One2many('mrp.standart.cost.calc.bom.line', 'parent_id')
    qty = fields.Float('Үйлдвэрлэсэн тоо',tracking=True, )
    sum_amount = fields.Float('Нийт өртөг',compute='_compute_total')
    price_unit = fields.Float('Нэгж өртөг',compute='_compute_total')
    change_account_id = fields.Many2one('account.account', string='Солих данс',)
    config_ids = fields.Many2many('mrp.product.standart.cost', string='Стандарт өртөгүүд', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    
    def _compute_total(self):
        for order in self:
            order.total_debit = sum(m.debit for m in order.line_ids)
            order.total_credit = sum(m.credit for m in order.line_ids)
            order.sum_amount = sum(m.debit for m in order.line_ids) + sum(m.debit for m in order.bom_line_ids)
            order.price_unit = order.qty and order.sum_amount/order.qty or 0


    @api.ondelete(at_uninstall=False)
    def _unlink_except_done(self):
        if any(record.state == 'done' for record in self):
            raise UserError((u'Батлагдсан бичлэг устгах боломжгүй.'))


    def action_calculate(self):
        calc_line = self.env['mrp.standart.cost.calc.line']
        for item in self:
            # if item.config_id:
            if item.config_ids:
                data={}
                data['company_id'] = item.company_id.id
                data['date_from'] = item.date_start
                data['date_to'] = item.date_end
                data['state'] = 'posted'
                # if item.config_id.line_ids:
                if item.config_ids.line_ids:                
                    item.line_ids.unlink()
                    # for line in item.config_id.line_ids:
                    # for line in item.config_ids.line_ids:
                    check_acc=[]
                    for conf in item.config_ids:                
                      for line in conf.line_ids:
                    # for line in item.line_ids:
                        if not line.credit_account_id:
                            raise UserError((u'Тохиргоонд кр данс сонгоогүй байна {}.'.format(line.name)))
                        if not conf.product_id:                    
                            raise UserError((u'Тохиргоонд бараа сонгоогүй байна {}.'.format(line.name)))
                        if line.credit_account_id.id in check_acc:
                            continue
                        else:
                            check_acc.append(line.credit_account_id.id)
                        data['branch_id'] = (line.branch_id and line.branch_id.id) or ( conf.branch_id and conf.branch_id.id) or False
                        account=line.credit_account_id.with_context(data)
                        # debit_account=line.debit_account_id.with_context(data)
                        # select mo.id as mo_id, sm.id as sm_id,p.id as product_id,foo.acc_id,aml.account_id,aml.debit,aml.credit,sm.state from mrp_production mo left join stock_move sm on sm.raw_material_production_id=mo.id left join product_product p on sm.product_id=p.id left join (select value_reference,REPLACE(res_id,'product.template,','')::int as product_tml_id,res_id,REPLACE(value_reference,'account.account,','')::int as acc_id from ir_property where res_id like 'product.template,%' and name='property_account_expense_id') as foo on foo.product_tml_id=p.product_tmpl_id left join account_move am on am.stock_move_id=sm.id
                        # left join account_move_line aml on aml.move_id=am.id
                        # where mo.bom_id=106;
                        debit=account.debit
                        credit=account.credit    
                        # print ('debit ',debit)
                        # query ="""
                        # select 
                        #     -- mo.id as mo_id, sm.id as sm_id,p.id as product_id,aml.account_id,
                        #     -- aml.debit,
                        #     sum(aml.credit)
                        #     --,sm.state 
                        #     from mrp_production mo 
                        #     left join stock_move sm on sm.raw_material_production_id=mo.id 
                        #     left join product_product p on sm.product_id=p.id 
                        #     left join account_move am on am.stock_move_id=sm.id
                        #     left join account_move_line aml on aml.move_id=am.id
                        #     where mo.bom_id in 
                        #             (select id from mrp_bom where product_tmpl_id in (select product_tmpl_id from product_product where id={0}))
                        #             AND aml.account_id={1}
                        #     """.format(item.config_id.product_id.id,line.credit_account_id.id)
                        # self.env.cr.execute(query)
                        # records = self.env.cr.fetchall()
                        # print ('recordsrecords ',records)
                        # credit=0
                        # if records[0][0]:
                        #     for c in records:
                        #         credit+=c
                        calc_line.create({'name':line.name,
                                          'debit':debit,
                                          'credit':credit,
                                          'parent_id':item.id,
                                          'config_line_id':line.id,
                                          'product_id':conf.product_id.id,
                                          'branch_id':line.branch_id and line.branch_id.id,
                                          })    
                        
    def action_calculate_bom(self):
        calc_line = self.env['mrp.standart.cost.calc.bom.line']
        mrp_obj = self.env['mrp.production']
        for item in self:
            debit=0
            credit=0
            qty=0
            
            if item.config_ids:
                data={}
                for config_id in item.config_ids:
                    if not config_id.product_id:
                        raise UserError((u'Тохиргоонд бараа сонгоогүй байна {}.'.format(config_id.name)))
                    domain = [('state', '=', 'done'), ('product_id', '=', config_id.product_id.id)]   
                    mrp_ids = mrp_obj.search(domain)
                    # print ('mrp_ids ',mrp_ids)
                    # print ('mrp_idsmove_raw_ids ',mrp_ids.move_raw_ids)
                    move_ids=[]
                    if mrp_ids.move_raw_ids:
                        move_ids=mrp_ids.move_raw_ids.account_move_ids.filtered(lambda m: m.state == 'posted' and m.date>=item.date_start and m.date<=item.date_end)
                        debit+= sum(move_ids.line_ids.mapped('debit'))
                        
                        mrp_bb_ids = mrp_ids.filtered(lambda m: m.state == 'done' and m.date_planned_start.date()>=item.date_start and m.date_planned_start.date()<=item.date_end)
                        # print ('mrp_bb_ids ',mrp_bb_ids)
                        # print ('mrp_bb_idsproduct_ids ',mrp_bb_ids.product_id)
                        move_finished_ids = mrp_bb_ids.move_finished_ids.filtered(lambda m: m.state == 'done' and m.location_dest_id.usage=='internal' and m.product_id in mrp_bb_ids.product_id)
                        # print ('move_finished_ids ',move_finished_ids)
                        move_finished_ids2 = mrp_bb_ids.move_finished_ids.filtered(lambda m: m.state == 'done' and m.location_dest_id.usage!='internal' and m.product_id in mrp_bb_ids.product_id)
                        # print ('move_finished_ids2 butsaalt ',move_finished_ids2)
                        qty+= sum(move_finished_ids.mapped('quantity_done'))
                        qty-= sum(move_finished_ids2.mapped('quantity_done'))
                    # print ('move_ids ',move_ids)
                    # print ('debit ',debit)
                    # print ('qty ',qty)
            item.write({'qty':qty})
            if debit>0:
                calc_line.create({'name':item.name,
                              'debit':debit,
                              'credit':credit,
                              'parent_id':item.id,
                              # 'config_line_id':line.id,
                              'product_id':config_id.product_id.id,
                              
                              # 'branch_id':line.branch_id and line.branch_id.id,
                              })    
    def action_update_st_price(self):      
        for item in self:
            if not item.config_id.product_id:
                raise UserError((u'Тохиргоонд dgjgg сонгоогүй байна {}.'.format(item.config_id.name)))
            if item.price_unit>0:
                item.config_id.product_id.write({'standard_price':item.price_unit})
                
    def action_draft(self):
        for record in self:
            return record.write({'state': 'draft'})

    def action_done(self):
        for record in self:
            return record.write({'state': 'done'})
        
    def _prepare_account_move_cost(self,journal_id):
        self.ensure_one()
        vals = {
            'move_type': 'entry',
            'date': self.date_end,
            'journal_id': journal_id,
            'ref': self.name,
        }
        return vals                        
    
    def button_create_difference_aml(self):
        self.ensure_one()
        if self.line_ids:
            aml_vals=[]
            for  ll in self.line_ids:
                # ll.create_difference_aml(move)
                vv = ll.create_difference_aml()
                aml_vals+=vv[0]
            val=self._prepare_account_move_cost(vv[1])
            val.update({'line_ids':aml_vals})
            print ('val ',val)
            move=self.env['account.move'].create(val)
            for  lll in self.line_ids:
                lll.write({'move_id':move.id})
    def button_change_aml_account(self):
        self.ensure_one()
        if self.line_ids:
            acc_ids=[]
            for  ll in self.line_ids:
                if ll.credit_account_id.id:
                    acc_ids.append(ll.credit_account_id.id)
            for  ll in self.line_ids:
                if ll.move_id and self.change_account_id:
                    for aml in ll.move_id.line_ids:
                        if ll.credit_account_id and aml.account_id.id not in acc_ids:
                            print ('aml.account_id.id ',aml.account_id.id)
                            print ('ll.credit_account_id.id ',ll.credit_account_id.id)
                            aml.write({'account_id':self.change_account_id.id})
    
class MRPCostCalculateLine(models.Model):
    '''
        Гүйцэтгэл тооцоолох мөр
    '''
    _name = 'mrp.standart.cost.calc.line'
    _description = 'Гүйцэтгэл тооцоолох'

    name = fields.Char(required=True, tracking=True, )
    debit = fields.Float(string='Дебит дүн', )
    credit = fields.Float(string='Кредит дүн', )
    config_line_id = fields.Many2one('mrp.product.standart.cost.line', string='Стандарт өртөг', )
    credit_account_id = fields.Many2one(related='config_line_id.credit_account_id', string='Данс',)
 # debit_account_id = fields.Many2one(related='config_line_id.debit_account_id', string='Дебит данс', )
    move_id = fields.Many2one('account.move', string='Move', )
    parent_id = fields.Many2one('mrp.standart.cost.calc', string='parent', )
    difference = fields.Float(compute='_compute_difference')
    product_id = fields.Many2one('product.product', string='Бараа', )
    branch_id = fields.Many2one('res.branch', string='Салбар',)
    
    def _compute_difference(self):
        for line in self:
            line.difference = line.debit-line.credit
    
    def _prepare_account_move_cost_line(self):
        self.ensure_one()
        if not self.product_id:                    
            raise UserError((u'Бараагүй байна {}.'.format(self.name)))
        
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        journal_id = accounts_data['stock_journal'].id
        # if not line.debit_account_id:
        #                 raise UserError((u'Дебит данс хоосон байна .{}'.format(line.name))
        # if not line.debit_account_id:
        #     raise UserError((u'Дебит данс хоосон байна .{}'.format(line.name))
        credit=debit=abs(self.difference)
        debit_account_id=self.difference>0 and accounts_data['stock_output'].id or self.credit_account_id.id
        credit_account_id=self.difference<0 and accounts_data['stock_output'].id or self.credit_account_id.id
        branch=(self.branch_id and self.branch_id.id) or \
                    (self.config_line_id.branch_id and self.config_line_id.branch_id.id) or \
                    (self.config_line_id.parent_id and  self.config_line_id.parent_id.branch_id and self.config_line_id.parent_id.branch_id.id) or False
        
        vals = [
                (0, 0, {
                    'account_id': debit_account_id,
                    'debit': debit  ,
                    'credit': 0.0,
                    'name':self.name+' '+self.product_id.name+' '+self.name,
                    'branch_id':branch,
                    'analytic_distribution':self.parent_id.analytic_distribution,
                }), 
                    (0,0,{
                    'account_id': credit_account_id,
                    'debit': 0.0,
                    'credit': credit  ,
                    'name':self.name+' '+self.product_id.name+' '+self.name,
                    'branch_id':branch,
                    'analytic_distribution':self.parent_id.analytic_distribution,
                })
                ]  
        # vals = {
        #     'move_type': 'entry',
        #     'date': self.parent_id.date_end,
        #     'journal_id': journal_id,
        #     'ref': self.name,
        #     'line_ids': [
        #         (0, 0, {
        #             'account_id': debit_account_id,
        #             'debit': debit  ,
        #             'credit': 0.0,
        #             'name':self.name+' '+self.product_id.name+' '+self.name,
        #             'branch_id':self.branch_id and self.branch_id.id
        #         }),
        #         (0, 0, {
        #             'account_id': credit_account_id,
        #             'debit': 0.0,
        #             'credit': credit  ,
        #             'name':self.name+' '+self.product_id.name+' '+self.name,
        #             'branch_id':self.branch_id and self.branch_id.id
        #         }),
        #     ],
        # }
        return [vals,journal_id]                     
        
    def create_difference_aml(self):
        self.ensure_one()
        val=self._prepare_account_move_cost_line()
        # aml=self.env['account.move.line'].create(val)
        # self.write({'move_id':move.id})              
        return   val
    

class MRPCostCalculateBOMLine(models.Model):
    '''
        Гүйцэтгэл тооцоолох мөр
    '''
    _name = 'mrp.standart.cost.calc.bom.line'
    _description = 'Гүйцэтгэл тооцоолох bom'

    name = fields.Char(required=True, tracking=True, )
    debit = fields.Float(string='Дебит дүн', )
    credit = fields.Float(string='Кредит дүн', )
    # config_line_id = fields.Many2one('mrp.product.standart.cost.line', string='Стандарт өртөг', )
    credit_account_id = fields.Many2one('account.account',string='Данс',)
 # debit_account_id = fields.Many2one(related='config_line_id.debit_account_id', string='Дебит данс', )
    move_id = fields.Many2one('account.move', string='Move', )
    parent_id = fields.Many2one('mrp.standart.cost.calc', string='parent', )
    difference = fields.Float(compute='_compute_difference')
    product_id = fields.Many2one('product.product', string='Бараа', )
    branch_id = fields.Many2one('res.branch', string='Салбар',)
    
    def _compute_difference(self):
        for line in self:
            line.difference = line.debit-line.credit
        
class MRPProductExpenseCostHistory(models.Model):
    '''
    ҮНЗ стандарт өртөг түүх 
    '''
    _name = 'mrp.product.standart.cost.history'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'format.address.mixin', 'avatar.mixin']
    _description = 'ҮНЗ стандарт өртөг түүх '
    
    name = fields.Char(required=True, tracking=True, )
    price_unit = fields.Float(string='Стандарт өртөг', )
    old_price_unit = fields.Float(string='Хуучин Стандарт өртөг', )
    cost_id = fields.Many2one('mrp.product.standart.cost', string='Standart cost', )
    cost_line_id = fields.Many2one('mrp.product.standart.cost.line', string='Standart cost line', )
    product_id = fields.Many2one(related='cost_id.product_id', string='Бараа', store=True)
    
    