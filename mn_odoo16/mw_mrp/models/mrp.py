# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from collections import defaultdict
from odoo.tools.misc import OrderedSet, format_date, groupby as tools_groupby

class StockMove(models.Model):
    _inherit = 'stock.move'

    is_mrp_sale = fields.Boolean('Зарагдахгүй?', )
    mo_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Зардлын данс',
    )    

    @api.onchange('product_id')
    def _onchange_pr_id(self):
        for sm  in self:
            mo_account_id=False
            if sm.product_id and sm.raw_material_production_id and sm.raw_material_production_id.is_account_mo:
                mo_account_id = (sm.product_id.property_account_expense_id and sm.product_id.property_account_expense_id) \
                                    or (sm.product_id.categ_id and sm.product_id.categ_id.property_stock_account_output_categ_id)
            if mo_account_id:
                sm.mo_account_id = mo_account_id.id

                
class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    _order = 'priority desc, date_planned_start desc,id'
    
    def action_view_account_move_line(self):
        """ Санхүү гүйлгээнүүд
        """
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_moves_all")
        if len(self.aml_ids) > 1:
            action['domain'] = [('id', 'in', self.aml_ids.ids)]
        action['context'] = {'search_default_group_by_account': 1,}
        return action
        
    def action_confirm(self ):
        """ Заавал стандарт өртөг авах """
        res=super(MrpProduction, self).action_confirm()
        if not self.standart_cost_id:
            raise UserError(('Стандарт өртөг сонгоогүй байна.'))
        return res
            

    def button_mark_done(self):
        """ picking date_done """
        action=super(MrpProduction, self).button_mark_done()
        for production in self:
            if production.picking_ids:
                production.picking_ids.write({'date_done': fields.Datetime.now()})
            production.button_create_st_aml()
        return action

            
    @api.model
    def _get_default_cost(self):

        cost_id = self.env['mrp.product.standart.cost'].search([('product_ids', 'in', [self.product_id.id]),
                                                                             ('state', '=', 'done')])
        if cost_id:
            return cost_id.id
        else:
            return False

    standart_cost_id = fields.Many2one('mrp.product.standart.cost', string='Стандарт өртөг', domain="[('state','=','done')]")

    st_line_ids = fields.One2many(related='standart_cost_id.line_ids')
    st_line_by_ids = fields.One2many(related='standart_cost_id.line_by_ids')
    
    is_add_cost = fields.Boolean('Нэмэлт өртөгтэй?', )
    add_standart_cost_ids = fields.Many2many('mrp.product.standart.cost',  'mrp_prod_add_cost_st_rel','mrp_id', 'cost_id', string='Нэмэлт стандарт өртөг',copy=False)
    # add_st_line_ids = fields.One2many(related='add_standart_cost_ids.line_ids')
    add_st_line_by_ids = fields.One2many(related='add_standart_cost_ids.line_by_ids')
    
    add_st_line_ids = fields.Many2many(
        comodel_name='mrp.product.standart.cost.line',
        string="Lines",
        compute='_compute_add_lines_ids', store=True, readonly=False, precompute=True,
        context={'active_test': False},
    )
    
    is_account_mo = fields.Boolean(string='MO дээрээс ТЭМ данс авах?', default=True)

    @api.onchange('move_raw_ids.product_id', 'is_account_mo')
    def _onchange_acc(self):
        for sm  in self.move_raw_ids:
            mo_account_id=False
            print ('sm.workorder_id2 ',sm.raw_material_production_id)
            if sm.product_id and sm.raw_material_production_id and sm.raw_material_production_id.is_account_mo:
                mo_account_id = (sm.product_id.property_account_expense_id and sm.product_id.property_account_expense_id) \
                                    or (sm.product_id.categ_id and sm.product_id.categ_id.property_stock_account_output_categ_id)
            print ('mo_account_id ',mo_account_id)
            if mo_account_id:
                sm.mo_account_id = mo_account_id.id

    
        
    @api.depends('add_standart_cost_ids', 'add_standart_cost_ids.line_ids')
    def _compute_add_lines_ids(self):
        for line in self:
            line_ids=self.env['mrp.product.standart.cost.line']
            for l in  line.add_standart_cost_ids:
                line_ids += l.line_ids
            line.add_st_line_ids = line_ids


    standart_aml_ids = fields.Many2many('account.move', 'mrp_prod_account_move_st_rel','mrp_id', 'move_id', string='Стандарт бичилт',copy=False)
    standart_close_aml_ids = fields.Many2many('account.move', 'mrp_prod_account_move_st_close_rel','mrp_id', 'move_id', string='Стандарт хаалт бичилт',copy=False)

    shift_select = fields.Selection([
            ('day', "Өдөр"),
            ('night', "Шөнө"),
        ],default='day',string='Ээлж',)
    branch_id = fields.Many2one('res.branch', string='Салбар',default=lambda self: self.env.user.branch_id.id)    
    aml_count = fields.Integer(string='Account moves', compute='_compute_aml_ids')
    aml_ids = fields.Many2many('account.move.line', compute='_compute_aml_ids',)
    is_internal = fields.Boolean('Дотоод хөдөлгөөн?', )
    
    @api.depends('standart_aml_ids',
                 'standart_close_aml_ids',
                 'move_raw_ids.account_move_ids',
                'move_finished_ids.account_move_ids',)
    def _compute_aml_ids(self):
        for order in self:
            amls=self.env['account.move.line']
            if order.standart_aml_ids:
                amls+=order.standart_aml_ids.line_ids
            if order.standart_close_aml_ids:
                amls+=order.standart_close_aml_ids.line_ids
            if order.move_raw_ids.account_move_ids.line_ids:
                amls+=order.move_raw_ids.account_move_ids.line_ids
            if order.move_finished_ids.account_move_ids.line_ids:
                amls+=order.move_finished_ids.account_move_ids.line_ids
            order.aml_ids = amls
            order.aml_count = len(order.aml_ids)
    
    @api.onchange('product_id', 'lot_producing_id')
    def _compute_cost_id(self):

        for mrp  in self:
            cost_id = self.env['mrp.product.standart.cost'].search([('product_id', '=', mrp.product_id.id),
                                                                                 ('state', '=', 'done')], limit=1)
            if cost_id:
                mrp.standart_cost_id = cost_id.id


    def _cal_price(self, consumed_moves):
        """Set a price unit on the finished move according to `consumed_moves`.
        """
        # super(MrpProduction, self)._cal_price(consumed_moves)
        work_center_cost = 0
        finished_move = self.move_finished_ids.filtered(
            lambda x: x.product_id == self.product_id and x.state not in ('cancel') and x.quantity_done > 0) #'done', 
        if finished_move:
            finished_move.ensure_one()
            for work_order in self.workorder_ids:
                time_lines = work_order.time_ids.filtered(lambda t: t.date_end and not t.cost_already_recorded)
                work_center_cost += work_order._cal_cost(times=time_lines)
                time_lines.write({'cost_already_recorded': True})
            qty_done = finished_move.product_uom._compute_quantity(
                finished_move.quantity_done, finished_move.product_id.uom_id)
            extra_cost = self.extra_cost * qty_done
            
            total_cost = - sum(consumed_moves.sudo().stock_valuation_layer_ids.mapped('value')) + work_center_cost + extra_cost
#            print ('total_costtotal_cost ',total_cost)
            #MW
            # if self.standart_cost_id:
            #         # total_cost += self.standart_cost_id.price_unit*self.product_qty                
            #     for  ll in self.standart_cost_id.line_ids:
            #         total_cost += ll.price_unit*self.product_qty
            raw_unit=total_cost/qty_done
            raw_total = total_cost
            bb_st=0
            if self.st_line_ids:
                for  ll in self.st_line_ids:
                    total_cost += ll.price_unit*self.product_qty 
                    bb_st  += ll.price_unit*self.product_qty
            if self.add_st_line_ids:
                for  ll2 in self.add_st_line_ids:
                    total_cost += ll2.price_unit*self.product_qty 
                    bb_st  += ll2.price_unit*self.product_qty
            # by_st=0
            # if self.st_line_by_ids:
            #     for  lll in self.st_line_by_ids:
            #         by_st += lll.price_unit*self.product_qty            
#            print ('total_cost++: ',total_cost)
#            print ('raw_total+11+: ',raw_total)
            #MW
            byproduct_moves = self.move_byproduct_ids.filtered(lambda m: m.state not in ('done', 'cancel') and m.quantity_done > 0)
            byproduct_cost_share = 0
            not_sale_amount=0
            by_product_share=0
#            print ('byproduct_moves123:================= ',byproduct_moves)
            by_st_products=[]
            by_st_products = self.st_line_by_ids.by_product_id
#            print ('by_st_products ',by_st_products)
            total_qty=0
            bb_unit_price = total_cost / qty_done
            not_st_qty = sum(self.move_byproduct_ids.filtered(lambda t: t.product_id not in by_st_products).mapped('product_uom_qty'))
            has_st_qty = sum(self.move_byproduct_ids.filtered(lambda t: t.product_id in by_st_products).mapped('product_uom_qty'))
#            print ('not_st_qty ',not_st_qty)
#            print ('has_st_qty ',has_st_qty)
            for byproduct in byproduct_moves:
                # if byproduct.cost_share == 0:
                #     continue
                byproduct_cost_share += byproduct.cost_share
                if byproduct.product_id.cost_method in ('fifo', 'average'):
                    # byproduct.price_unit = total_cost * byproduct.cost_share / 100 / byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id)
                    #20231122 zasav
                    if byproduct.is_mrp_sale: #ЗАРАХГҮЙ
                        if self.st_line_by_ids.filtered(lambda t: t.by_product_id == byproduct.product_id): #СӨ тэй
                            by_st=sum(self.st_line_by_ids.filtered(lambda t: t.by_product_id == byproduct.product_id).mapped('price_unit'))*byproduct.product_uom_qty 
                            # bb_unit_price = (total_cost + by_st)/(qty_done)
                            not_sale_amount += by_st
                            byproduct.price_unit = 0 #all_total_amount / byproduct.product_uom_qty
                        else: # СӨ гүй
                            # for  ii in self.st_line_by_ids:
                            # not_qty = sum(self.move_byproduct_ids.filtered(lambda t: t.product_id not in by_st_products).mapped('product_uom_qty'))
                            # print ('not_qty ',not_qty)
                            # total_qty=qty_done+not_qty
                            # print ('total_qty ',total_qty)
                            byproduct.price_unit = 0 #total_cost  / total_qty * qty_done
                            # print(a)
                    else: # ЗАРАХ
                        if self.st_line_by_ids.filtered(lambda t: t.by_product_id == byproduct.product_id): #СӨ тэй
                            byproduct.price_unit = ((raw_total / (has_st_qty+qty_done)) +  sum(self.st_line_by_ids.filtered(lambda t: t.by_product_id == byproduct.product_id).mapped('price_unit')))/byproduct.product_uom_qty
                            by_product_share+=(raw_total / (has_st_qty+qty_done))*byproduct.product_uom_qty
                        else: #СӨ гүй
                            byproduct.price_unit = (raw_total / (has_st_qty+qty_done))/byproduct.product_uom_qty
                            by_product_share+=(raw_total / (has_st_qty+qty_done))*byproduct.product_uom_qty
                            
                        # byproduct.price_unit = 0
                        # not_sale_amount+=sum(self.st_line_by_ids.filtered(lambda t: t.by_product_id == byproduct.product_id).mapped('price_unit'))*byproduct.product_uom_qty
#            print ('not_sale_amount ',not_sale_amount)
                    # if by_st>0:
                        # byproduct.price_unit = by_st  / qty_done#total_cost / byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id) # * byproduct.cost_share / 100                     
                    # else:
                    #     byproduct.price_unit = total_cost  / qty_done#total_cost / byproduct.product_uom._compute_quantity(byproduct.quantity_done, byproduct.product_id.uom_id) # * byproduct.cost_share / 100                     
                    #20231122 zasav
   # if finished_move.product_id.cost_method in ('fifo', 'average'):
   #     finished_move.price_unit = total_cost * float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001) / qty_done
   #Дайвар бүтээгдэхүүнтэй бол хувиар хуваахгүй
            if finished_move.product_id.cost_method in ('fifo', 'average'):
                # if total_qty>0:
                #     finished_move.price_unit = (total_cost+not_sale_amount)  / qty_done
                # else:
                finished_move.price_unit = (total_cost+not_sale_amount-by_product_share)  / qty_done # * float_round(1 - byproduct_cost_share / 100, precision_rounding=0.0001)
        return True
       

    def _post_inventory(self, cancel_backorder=False):
        '''ТЭМ ийн picking эхэлж батлаад MO батлахад ТЭМ өртөг тооцохгүй байгааг засах.
            if move.state == 'done':
                # moves_not_to_do.add(move.id)
                print ('skip done')
        '''
        moves_to_do, moves_not_to_do = set(), set()
        for move in self.move_raw_ids:
            if move.state == 'done':
                # moves_not_to_do.add(move.id)
                print ('skip done')
            elif move.state != 'cancel':
                moves_to_do.add(move.id)
                if move.product_qty == 0.0 and move.quantity_done > 0:
                    move.product_uom_qty = move.quantity_done
        self.env['stock.move'].browse(moves_to_do)._action_done(cancel_backorder=cancel_backorder)
        moves_to_do = self.move_raw_ids.filtered(lambda x: x.state == 'done') - self.env['stock.move'].browse(moves_not_to_do)
        # Create a dict to avoid calling filtered inside for loops.
        moves_to_do_by_order = defaultdict(lambda: self.env['stock.move'], [
            (key, self.env['stock.move'].concat(*values))
            for key, values in tools_groupby(moves_to_do, key=lambda m: m.raw_material_production_id.id)
        ])
        for order in self:
            finish_moves = order.move_finished_ids.filtered(lambda m: m.product_id == order.product_id and m.state not in ('done', 'cancel'))
            # the finish move can already be completed by the workorder.
            for move in finish_moves:
                if move.quantity_done:
                    continue
                move._set_quantity_done(float_round(order.qty_producing - order.qty_produced, precision_rounding=order.product_uom_id.rounding, rounding_method='HALF-UP'))
                move.move_line_ids.lot_id = order.lot_producing_id
            # workorder duration need to be set to calculate the price of the product
            for workorder in order.workorder_ids:
                if workorder.state not in ('done', 'cancel'):
                    workorder.duration_expected = workorder._get_duration_expected()
                if workorder.duration == 0.0:
                    workorder.duration = workorder.duration_expected * order.qty_produced/order.product_qty
                    workorder.duration_unit = round(workorder.duration / max(workorder.qty_produced, 1), 2)
            # print ('moves_to_do_by_order[order.id] ',moves_to_do_by_order[order.id])
            order._cal_price(moves_to_do_by_order[order.id])
        moves_to_finish = self.move_finished_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_to_finish = moves_to_finish._action_done(cancel_backorder=cancel_backorder)
        self.action_assign()
        for order in self:
            consume_move_lines = moves_to_do_by_order[order.id].mapped('move_line_ids')
            order.move_finished_ids.move_line_ids.consume_line_ids = [(6, 0, consume_move_lines.ids)]
        return True
    
    def _prepare_account_move_cost(self,line):
        self.ensure_one()
        # if not line.debit_account_id:
        #                 raise UserError((u'Дебит данс хоосон байна .{}'.format(line.name))
        # if not line.debit_account_id:
        #     raise UserError((u'Дебит данс хоосон байна .{}'.format(line.name))
                            
        vals = [
                (0, 0, {
                    'account_id': line.debit_account_id.id,
                    'debit': line.price_unit*self.product_qty  ,
                    'credit': 0.0,
                    'name':self.name+' '+self.product_id.name+' '+line.name,
                    'product_id':self.product_id.id,
                    'branch_id':self.branch_id and self.branch_id.id or self.standart_cost_id and self.standart_cost_id.branch_id and self.standart_cost_id.branch_id.id,
                    'analytic_distribution':self.standart_cost_id and self.standart_cost_id.analytic_distribution,
                }),
                (0, 0, {
                    'account_id': line.credit_account_id.id,
                    'debit': 0.0,
                    'credit': line.price_unit*self.product_qty  ,
                    'name':self.name+' '+self.product_id.name+' '+line.name,
                    'product_id':self.product_id.id,
                    'branch_id':self.branch_id and self.branch_id.id or self.standart_cost_id and self.standart_cost_id.branch_id and self.standart_cost_id.branch_id.id,
                    'analytic_distribution':self.standart_cost_id and self.standart_cost_id.analytic_distribution,
                }),
            ]
        return vals                            
        

    def _prepare_account_move_cost_bb(self):
        self.ensure_one()
        accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        journal_id = accounts_data['stock_journal'].id
        # if not line.debit_account_id:
        #                 raise UserError((u'Дебит данс хоосон байна .{}'.format(line.name))
        # if not line.debit_account_id:
        #     raise UserError((u'Дебит данс хоосон байна .{}'.format(line.name))

  # accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
        if not self.move_finished_ids:
              raise UserError(('Бэлэн бүтээгдэхүүний хөдөлгөөн хийгдээгүй байна.'))
        acc_src = self.move_finished_ids._get_src_account(accounts_data)
        vals = {
            'move_type': 'entry',
            'date': self.date_planned_start,
            'journal_id': journal_id,
            'ref': self.name,
            'line_ids': [],
            'branch_id':self.branch_id.id
        }        
        amount=0
        for  line in self.st_line_ids:        
            vals['line_ids'].append(
                    (0, 0, {
                        'account_id': line.debit_account_id.id,
                        'debit': 0.0,
                        'credit': round(line.price_unit*self.product_qty,2)  ,
                        'name':self.name+' '+self.product_id.name+' '+line.name,
                        'product_id':self.product_id.id,
                        'branch_id':self.branch_id and self.branch_id.id or self.standart_cost_id and self.standart_cost_id.branch_id and self.standart_cost_id.branch_id.id,
                        'analytic_distribution':self.standart_cost_id and self.standart_cost_id.analytic_distribution,
                    }))
            amount+=round(line.price_unit*self.product_qty,2)
        vals['line_ids'].append(
            (0, 0, {
                        'account_id': acc_src,
                        'debit': amount  ,
                        'credit': 0.0,
                        'name':self.name+' '+self.product_id.name,
                        'product_id':self.product_id.id,
                        'branch_id':self.branch_id and self.branch_id.id or self.standart_cost_id and self.standart_cost_id.branch_id and self.standart_cost_id.branch_id.id,
                        'analytic_distribution':self.standart_cost_id and self.standart_cost_id.analytic_distribution,
            }))

        return vals        
            
    def button_create_st_aml(self):
        self.ensure_one()
        if self.standart_close_aml_ids or self.standart_aml_ids:
            return True
            # raise UserError(('Санхүү бичилт үүссэн байна.'))
        
        if self.st_line_ids:
            standart_close_aml_ids=[]
            standart_aml_ids=[]
            accounts_data = self.product_id.product_tmpl_id.get_product_accounts()
            journal_id = accounts_data['stock_journal'].id
            vals = {
                'move_type': 'entry',
                'date': self.date_planned_start,
                'journal_id': journal_id,
                'ref': self.name,
                'line_ids': [],
                'branch_id':self.branch_id.id
            }                    
            for  ll in self.st_line_ids:
                #Стандарт Дт
                #ДҮ кр
                val=self._prepare_account_move_cost(ll)
                vals['line_ids']+=val
            move=self.env['account.move'].create(vals)
            standart_aml_ids.append(move.id)
            move.action_post()
    # ll.write({'move_id':move.id})

            #ББ ДҮ нэгтгэл Дт
            #Стандарт Кр
            val_st=self._prepare_account_move_cost_bb()
            move=self.env['account.move'].create(val_st)
            standart_close_aml_ids.append(move.id)
            move.action_post()
            self.write({'standart_close_aml_ids': [(6, None, standart_close_aml_ids)]})
            self.write({'standart_aml_ids': [(6, None, standart_aml_ids)]})
        
    def _get_move_raw_values(self, product_id, product_uom_qty, product_uom, operation_id=False, bom_line=False):
        """ ТЭМ татах байрлал БОМ тохиргооноос авах """
        data=super(MrpProduction, self)._get_move_raw_values(product_id=product_id, product_uom_qty=product_uom_qty, product_uom=product_uom, operation_id=operation_id, bom_line=bom_line)
        if bom_line and bom_line.bom_location_id:
            data['location_id'] = bom_line.bom_location_id.id
        return data
        
        

    def button_delete_st_aml(self):
        self.ensure_one()
        if self.standart_close_aml_ids or self.standart_aml_ids:
            for aml in self.standart_close_aml_ids:
                aml.button_draft()
                aml.unlink()
            for aml2 in self.standart_aml_ids:
                aml2.button_draft()
                aml2.unlink()
        else:
            raise UserError(('Санхүү бичилт хоосон байна.'))
                

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _should_be_assigned(self):
        '''stock move iin undsen eer darav picking uusgeh nuhtsul'''
        res = super(StockMove, self)._should_be_assigned()
        # bbb=bool(res and  (self.production_id or self.raw_material_production_id))
        rr=bool(not self.picking_id and self.picking_type_id)
        return rr
        
        