# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.addons.mw_purchase_expense.models.purchase_order_expenses import PORTION_SELECTION
from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class amove(models.Model):
    _inherit = 'account.move'
    
    nemegdel_zardaluud = fields.One2many('purchase.order.expenses', 'invoice_id', string='Add costs')
    add_cost_id = fields.Many2one('purchase.add.cost', related='nemegdel_zardaluud.add_cost_id', readonly=True)

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def update_ireh_too(self):
        if self.purchase_id:
            if not self.add_cost_id:
                raise UserError('Нэмэгдэл зардлаа сонгоно уу!')
            for item in self.move_line_ids:
                if item.move_id.purchase_line_id.qty_received_future and item.move_id.purchase_line_id.add_cost_ids:
                    quantity_done =sum(item.move_id.purchase_line_id.move_ids.filtered(lambda r:  r.state=='done').mapped('quantity_done'))
                    item.qty_done = 0
                    if quantity_done<item.move_id.purchase_line_id.qty_received_future:
                        _logger.info(u'self.add_cost_id.po_line_ids.ids=====: %s  '%(self.add_cost_id.po_line_ids.ids))
                        if item.move_id.purchase_line_id.id in (self.add_cost_id.po_line_ids.ids):
                            item.qty_done = item.move_id.purchase_line_id.qty_received_future

    add_cost_id = fields.Many2one('purchase.add.cost')

class AMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    po_id = fields.Many2one('purchase.order', related='purchase_line_id.order_id', string='PO')
    add_cost_id = fields.Many2one('purchase.add.cost', related='move_id.add_cost_id', readonly=True)


    def _apply_price_difference(self):
        '''valuation leyr uusgehgui'''
        
        return self.env['stock.valuation.layer'], self.env['account.move.line']

class PurchaseAddCostAmView(models.TransientModel):
    _name = 'purchase.add.cost.am.view'

    def view(self):
        action = self.env.ref('mw_purchase_expense_custom.action_purchase_acc_view_add_form_am').read()[0]
        am_ids = []
        for item in self.env['purchase.add.cost'].search([]):
            am_ids += item.expenses_line.mapped('invoice_id').ids
            sm_ids = item.mapped('po_line_ids.sm_ids').ids
            am_ids += self.env['account.move.line'].search([('purchase_line_id','in',item.po_line_ids.ids)]).mapped('move_id').ids
            am_ids += self.env['account.move'].search([('stock_move_id','in',sm_ids)]).ids
        action['domain'] = [('move_id','in', am_ids),('move_id.state','=','posted')]
        return action

class PurchaseAddCost(models.Model):
    _name = 'purchase.add.cost'
    _description = 'purchase add cost'
    _inherit = ['mail.thread']
    _order = 'date desc'
    
    name = fields.Char('Name', required=True, index=True, copy=False, default='New')
    date = fields.Date('Date /Rate/', required=True, tracking=True)
    current_rate = fields.Float('Бодогдох ханш', tracking=True)
    currency_id = fields.Many2one('res.currency', 'Валют', default=lambda self: self.env.user.company_id.currency_id.id, tracking=True)
    import_po_id = fields.Many2one('purchase.order', string='Import Purchases')
    import_po_partner_id = fields.Many2one('res.partner', string='Partner')
    po_line_ids = fields.Many2many('purchase.order.line', 'purchase_add_cost_purchase_order_line_rel', 'purchase_add_cost_id', 'purchase_order_line_id', string='Purchase Lines')
    po_ids = fields.Many2many('purchase.order', string='POs', compute='_compute_po_ids')
    expenses_line = fields.One2many('purchase.order.expenses', 'add_cost_id', 'Expenses line')
    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    amount_expenses = fields.Monetary(string='Total Expenses', store=True, readonly=True, compute='_amount_expenses_all', currency_field='company_currency_id', tracking=True)
    amount_expenses_in = fields.Monetary(string='Allocation of Total Costs', readonly=True, compute='_amount_expenses_all', currency_field='company_currency_id', tracking=True)
    state = fields.Selection([('draft','Ноорог'),('sent','Хянагчид илгээсэн'),('checked','Хянасан'),('done','Дууссан')], string='State', default='draft', tracking=True)
    product_id = fields.Many2one('product.product', string='Search for product')
    po_count = fields.Integer('Po count', compute='_compute_po_count', store=True)
    pol_count = fields.Integer('Pol count', compute='_compute_po_count', store=True)
    amount_expenses_po_tot2 = fields.Monetary(string='Total Cost PO', store=True, readonly=True, compute='_compute_po_count', currency_field='company_currency_id')
    po_niit_dun = fields.Float(string='Total PO amount', store=True, readonly=True, compute='_compute_po_count', tracking=True)
    qty_received_future_ok = fields.Boolean(string='Number of arrivals is 0', default=False)

    @api.depends('po_line_ids')
    def _compute_po_ids(self):
        for item in self:
            if item.po_line_ids:
                item.po_ids = item.po_line_ids.mapped('order_id').ids
            else:
                item.po_ids = False

    @api.onchange('date', 'currency_id')
    def _onchange_current_rate(self):
        if self.currency_id and self.date:
            rr = self.env['res.currency']._get_conversion_rate(self.currency_id, self.company_id.currency_id, self.company_id, self.date)
            self.current_rate = rr
        else:
            self.current_rate = 0
            
    def unlink(self):
        for s in self:
            if s.state != 'draft':
                raise UserError('Ноорог төлөвт устгах боломжтой!')
        return super(PurchaseAddCost, self).unlink()

    @api.depends('po_line_ids','po_line_ids.total_cost_unit')
    def _compute_po_count(self):
        for item in self:
            order_line = len(item.po_line_ids.mapped('order_id')) or 1
            item.po_count = order_line
            item.pol_count = len(item.po_line_ids)
            item.amount_expenses_po_tot2 = sum(item.po_line_ids.mapped('total_cost_unit'))
            item.po_niit_dun = sum(item.po_line_ids.mapped('price_total'))

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.add.cost') or '/'
        return super(PurchaseAddCost, self).create(vals)

    @api.depends('expenses_line.amount')
    def _amount_expenses_all(self):
        for order in self:
            amount_expenses = 0.0
            amount_expenses_in = 0
            for line in order.expenses_line:
                from_currency = line.currency_id
                to_currency = order.company_currency_id
                if from_currency == to_currency:
                    current_amount = line.amount
                else:
                    current_amount = line.amount * line.current_cur
                line.sudo().current_amount = self.env['res.currency'].with_context(date=line.date_cur)._compute(from_currency, to_currency, line.amount)
                line.sudo().current_amount = line.taxes_id.compute_all(current_amount, currency=to_currency, quantity=1.0)['total_excluded']
                amount_expenses += line.current_amount
                if not line.is_without_cost:
                    amount_expenses_in += line.current_amount
                    
            order.update({
                'amount_expenses': amount_expenses,
                'amount_expenses_in': amount_expenses_in,
            })

    # def make_expenses(self):
    #     self.po_line_ids.update({'cost_unit': 0})
    #     self._amount_expenses_all()
    #     self.make_expenses_line(self.expenses_line.filtered(lambda r: not r.is_without_cost))

    def make_expenses(self):
        self.po_line_ids.update({'cost_unit': 0})
        for line in self.po_line_ids.filtered(lambda l: l.product_qty > 0):
            # Урвуу хэлбэрээр өртөг тооцоолох хэсгийг шинэчлэв
            self.expense_per_line(line)
        self._amount_expenses_all()

    def expense_per_line(self, line):
        portion_methods = list(set(self.expenses_line.mapped('portion_method')))
        sum_for_line = 0
        product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
        for method in portion_methods:
            method_lines = self.expenses_line.filtered(lambda r: not r.is_without_cost and r.portion_method == method and (not r.purchase_lines or line.id in r.purchase_lines.ids))
            for expense_line in method_lines:
                current_amount = expense_line.current_amount
                lines = expense_line.purchase_lines if expense_line.purchase_lines else self.po_line_ids
                if method == 'price':
                    sum_for_line += current_amount * line.price_unit / sum(lines.mapped('price_unit'))
                elif method == 'subtotal':
                    sum_for_line += (current_amount / self.get_total_amount_currency(lines)) * self.get_total_amount_currency(line)
                elif method == 'volume':
                    total_volume = sum([(line.product_id.volume or 1) * line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id) for line in lines])
                    line_res = ((current_amount / total_volume) * ((line.product_id.volume or 1) * product_uom_qty)) / product_uom_qty
                    sum_for_line += line_res * product_uom_qty
                elif method == 'weight':  # weight
                    tot_w = sum(lines.mapped('subtotal_weight'))
                    tot_w_amount = current_amount * line.subtotal_weight / tot_w if tot_w else 1
                    sum_for_line += tot_w_amount
                elif method == 'qty':
                    sum_for_line += expense_line.current_amount * line.product_uom_qty / sum(lines.mapped('product_uom_qty'))
        line.cost_unit = sum_for_line / product_uom_qty

    def get_total_amount_currency(self, lines):
        sum_amount = 0
        for line in lines.filtered(lambda l: l.product_qty > 0):
            price_unit = line.price_unit_product
            sum_amount += price_unit * line.product_qty
   # if line.order_id.currency_id != self.company_id.currency_id:
   #     price_unit *= self.current_rate
        return sum_amount
    
    def remove_line(self):
        self.po_line_ids = False

    def import_po(self):
        suuld_nemedgdej = self.import_po_id.order_line.filtered(lambda r: not r.add_cost_ids and r.qty_received==0)
        self.po_line_ids += suuld_nemedgdej
        if self.qty_received_future_ok:
            for pol in suuld_nemedgdej:
                pol.qty_received_future = 0
        else:
            for pol in suuld_nemedgdej:
                pol.qty_received_future = pol.product_qty

    def make_expenses_line(self, expenses_line):
        for item in expenses_line:
            amount = 0.0
            selected_lines = item.purchase_lines
            if not selected_lines:
                selected_lines = self.po_line_ids
            
            to_currency = self.company_currency_id
            for pol in selected_lines:
                from_currency = pol.order_id.currency_id
                product_uom_qty = pol.product_uom._compute_quantity(pol.product_qty, pol.product_id.uom_id)
                price_unit = pol._get_stock_move_price_unit()
                amount += product_uom_qty * price_unit

            portion_dict = self.env['purchase.order'].make_portion(item.portion_method, selected_lines, amount, item.date_cur, item)
            for line in selected_lines:
                product_uom_qty = line.product_uom._compute_quantity(line.product_qty, line.product_id.uom_id)
                if product_uom_qty !=0:
                    line.cost_unit += portion_dict[line.id] / product_uom_qty
                else:
                    line.cost_unit = 0

    # def create_expense_invoice(self):
    #     names = str(self.date)
    #     self.env['purchase.order'].create_expense_invoice_hand(self.expenses_line, self.company_id, 'Many exp %s'%(str(names)))

    def create_expense_invoice(self):
        inv_expenses_line = self.expenses_line.filtered(lambda r: not r.invoice_id)
        ref = ', '.join(inv_expenses_line.filtered(lambda r: r.invoice_ref).mapped('invoice_ref')) or ''
        names = (self.name or '')+ref+' '+str(self.date)
        self.env['purchase.order'].create_expense_invoice_hand(inv_expenses_line, self.company_id, 'Many exp %s'%(str(names)))

    def action_sent(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env.ref('mw_purchase_expense_custom.action_purchase_expense_line_product_tree').id
        html = u'<b>Нэмэгдэл зардал батлана уу</b><br/>'
        html += u"""<b><a target="_blank" href=%s/web#id=%s&model=purchase.add.cost&action=%s>%s</a></b>, дугаартай Нэмэгдэл батлана уу"""% (base_url, self.id,action_id, self.display_name)
        res_model = self.env['ir.model.data'].search([
            ('module','=','mw_purchase_expense_custom'),
            ('name','in',['group_add_custom_checker'])])
        group = self.env['res.groups'].search([('id','in',res_model.mapped('res_id'))], limit=1)
        partner_ids = group.mapped('users.partner_id')
        self.send_chat(html, partner_ids)
        self.state = 'sent'

    def action_check(self):
        self.state = 'checked'

    def action_done(self):
        self.make_expenses()
        self.state = 'done'

    def action_draft(self):
        pol = self.po_line_ids.filtered(lambda r: r.qty_received>0)
        if pol:
            raise UserError(u'Орлого авсан байна %s'%(', '.join(pol.mapped('display_name'))))
        self.state = 'draft'

    def view_po(self):
        action = self.env.ref('purchase.purchase_form_action')
        vals = action.read()[0]
        order_ids = self.po_line_ids.mapped('order_id').ids
        domain = [('id','in',order_ids)]
        vals['domain'] = domain
        return vals
    
    def view_invoice(self):
        action = self.env.ref('account.action_move_out_invoice_type')
        vals = action.read()[0]
        order_ids = self.expenses_line.mapped('invoice_id').ids
        domain = [('id','in',order_ids)]
        vals['domain'] = domain
        return vals

    def view_po_am(self):
        action = self.env.ref('account.action_account_moves_all_tree')
        vals = action.read()[0]
        aml_ids = self.env['account.move.line'].search([('move_id','in',self.mapped('expenses_line.invoice_id').ids)]).ids
        aml_ids += self.env['account.move.line'].search([('purchase_line_id','in',self.po_line_ids.ids)]).ids
        aml_ids += self.env['account.move.line'].search([('move_id.stock_move_id.purchase_line_id','in',self.po_line_ids.ids)]).ids
        domain = [('id','in',aml_ids),('move_id.state','=','posted')]
        vals['domain'] = domain
        vals['context'] = {'search_default_group_by_account':1}
        return vals

    def send_chat(self, html, partner_ids):
        if not partner_ids:
            raise UserError(u'Мэдэгдэл хүргэх харилцагч байхгүй байна')
        
        channel_obj = self.env['mail.channel']
        for item in partner_ids:
            if self.env.user.partner_id.id!=item.id:
                channel_ids = channel_obj.search([
                    ('channel_partner_ids', 'in', [item.id])
                    ,('channel_partner_ids', 'in', [self.env.user.partner_id.id])
                    ]).filtered(lambda r: len(r.channel_partner_ids) == 2).ids
                if not channel_ids:
                    vals = {
                        'channel_type': 'chat', 
                        'name': u''+item.name+u', '+self.env.user.name, 
                        # 'public': 'private', 
                        'channel_partner_ids': [(4, item.id), (4, self.env.user.partner_id.id)], 
                        #'email_send': False
                    }
                    new_channel = channel_obj.create(vals)
                    notification = _('<div class="o_mail_notification">created <a href="#" class="o_channel_redirect" data-oe-id="%s">#%s</a></div>') % (new_channel.id, new_channel.name,)
                    new_channel.message_post(body=notification, message_type="notification", subtype_xmlid='mail.mt_note')
                    channel_info = new_channel.channel_info()[0]
                    self.env['bus.bus']._sendone((self._cr.dbname, 'res.partner', self.env.user.partner_id.id), channel_info, {
                                'id': self.id, 
                                'model':'purchase.add.cost'})

                    channel_ids = [new_channel.id]
                if channel_ids:
                    mail_channel = channel_obj.browse(channel_ids[0])
                    message = mail_channel.with_context(mail_create_nosubscribe=True).message_post(
                                                                                       body=html,
                                                                                       message_type='comment',
                                                                                       subtype_xmlid='mail.mt_comment')

class PurchaseOrderExpenses(models.Model):
    _inherit = 'purchase.order.expenses'

    add_cost_id = fields.Many2one('purchase.add.cost', 'Order id', ondelete='cascade')

    def get_po_id(self):
        res = super(PurchaseOrderExpenses, self).get_po_id()
        if self.add_cost_id.po_line_ids and self.add_cost_id.po_line_ids[0].order_id:
            res = self.add_cost_id.po_line_ids[0].order_id
        return res

    @api.onchange('product_id')
    def onch_product(self):
        for obj in self:
            obj.is_without_cost = obj.product_id.is_without_cost
            obj.portion_method = obj.product_id.portion_method

class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_po_ids = fields.One2many('purchase.order', 'partner_id', 'Expenses line')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    is_add_cost_custom = fields.Boolean('Optional Additional Costs', compute='_compute_is_add_cost_custom', store=True)
    amount_expenses_po_tot2 = fields.Float(string='Total Cost PO')
    
    def make_expenses(self):
        for item in self:
            if item.is_add_cost_custom and item.expenses_line:
                raise UserError('Сонголттой Олон Нэмэгдэл Зардлаар Хуваарилагдах PO дээр %s дангаар зардал хуваарилахгүй!!!'%(item.name))
            if item.is_add_cost_custom:
                return False
        return super(PurchaseOrder,self).make_expenses()

    @api.depends('order_line.add_cost_ids')
    def _compute_is_add_cost_custom(self):
        for item in self:
            if item.order_line.add_cost_ids:
                item.is_add_cost_custom = True
            else:
                item.is_add_cost_custom = False
    
    def view_custom_add_cost(self):
        action = self.env.ref('mw_purchase_expense_custom.action_purchase_expense_line_product_tree')
        vals = action.read()[0]
        order_ids = self.order_line.mapped('add_cost_ids').ids
        domain = [('id','in',order_ids)]
        vals['domain'] = domain
        return vals

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sm_ids = fields.One2many('stock.move', 'purchase_line_id', string='SM ids')
    add_cost_ids = fields.Many2many('purchase.add.cost', 'purchase_add_cost_purchase_order_line_rel',  'purchase_order_line_id', 'purchase_add_cost_id', string='Additional Costs', copy=False)
    is_qty_received = fields.Boolean('Re-Income', compute='_compute_is_qty_received')
    qty_received_future = fields.Float('Arrival number', compute='_compute_qty_received_future', store=True)
    add_cost_id_one = fields.Many2one('purchase.add.cost', string='One Additional Cost', store=True, compute='_compute_add_cost_id_one')

    # @api.depends('price_unit', 'product_id', 'taxes_id', 'order_id.date_currency', 'order_id.currency_id', 'cost_unit',
    #              'order_id.current_rate')
    # @api.onchange('price_unit', 'product_id', 'taxes_id', 'order_id.date_currency', 'order_id.currency_id', 'cost_unit',
    #               'order_id.current_rate')
    # def compute_price_unit_stock_move(self):
    #     for line in self:
    #         print('---------', self.add_cost_id_one, self.add_cost_ids)
    #         line.price_unit_stock_move = line._get_stock_move_price_unit(self.add_cost_id_one.current_rate)
    #         line.price_unit_product = line.price_unit_stock_move - line.cost_unit

    @api.depends('add_cost_ids')
    def _compute_add_cost_id_one(self):
        for item in self:
            if item.add_cost_ids:
                item.add_cost_id_one = item.add_cost_ids[0].id
            else:
                item.add_cost_id_one = False

    @api.depends('product_qty')
    def _compute_qty_received_future(self):
        for item in self:
            item.qty_received_future = item.product_qty

    @api.depends('qty_received_future','product_qty')
    def _compute_is_qty_received(self):
        for item in self:
            if item.qty_received_future!=item.product_qty:
                item.is_qty_received = True
            else:
                item.is_qty_received = False

    # Хүлээж авсан тоогоор задлах
    def extra_po_line(self):
        old_po_line = self
        old_rec = old_po_line.qty_received_future
        new_qty = old_po_line.product_qty - old_po_line.qty_received_future
        if new_qty>0:
            old_po_line.product_qty = old_rec
            new_po_line = self.copy()
            new_po_line.add_cost_ids = False
            new_po_line.product_qty = new_qty
        else:
            raise UserError('Ирэх тоо үндсэн тооноос их байна')
        
    def get_date_currency(self):
        res = super(PurchaseOrderLine,self).get_date_currency()
        if self.add_cost_ids:
            return self.add_cost_ids[0].current_rate
        return res

    def more_view_po_line(self):
        view_id = self.env.ref('mw_purchase_expense_custom.purchase_order_line_form2_add_custom')
        return {
                'name': u'Дэлгэрэнгүй Засах Худалдан авалтын мөр',
                'type': 'ir.actions.act_window',
                'res_model': 'purchase.order.line',
                'res_id': self.id,
                'view_mode': 'form',
                'views': [(view_id.id, 'form')],
                'view_id': view_id.id,
                'target':'new',
            }

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    portion_method = fields.Selection(PORTION_SELECTION, 'Хуваарилах Арга')
    is_without_cost = fields.Boolean('Not included in the cost /VAT../', default=False)

class PurchaseAccView(models.Model):
    _inherit = "purchase.acc.view"
    
    # add_cost_id = fields.Many2one('purchase.add.cost', 'Нэмэгдэл Зардалын баримт')
    # is_add_cost_custom = fields.Boolean('Сонголтой Нэмэгдэл Зардалтай', readonly=True)

    # def union_all(self):
    #     return """ union all """
    # def _select(self):
    #     res = super(purchase_acc_view, self)._select()
    #     res += """
    #         ,max(add_cost_rel.purchase_add_cost_id) as add_cost_id
    #         ,po.is_add_cost_custom
    #     """
    #     return res

    def _where(self):
        res = super(PurchaseAccView, self)._where()
        res += """
            and pol.id not in (select purchase_order_line_id from purchase_add_cost_purchase_order_line_rel)
        """
        return res

    # def _from(self):
    #     res = super(purchase_acc_view, self)._from()
    #     res += """
    #         left join purchase_add_cost_purchase_order_line_rel add_cost_rel on (pol.id=add_cost_rel.purchase_order_line_id)
    #     """
    #     return res

    # def _select2(self):
    #     res = super(purchase_acc_view,self)._select2()
    #     res +="""
    #         SELECT
    #             aml.id*po.id as id,
    #             aml.id as account_move_line_id,
    #             aml.account_id,
    #             aml.debit/pac.po_count,
    #             aml.credit/pac.po_count,
    #             po.id as purchase_id,
    #             am.partner_id,
    #             am.company_id,
    #             po.state as po_state,
    #             po.date_order as po_date,
    #             am.state as acc_state,
    #             aml.date as acc_date,
    #             poe.add_cost_id,
    #             po.is_add_cost_custom
    #     """
    #     return res

    # def _from2(self):
    #     return """
    #         FROM account_move_line AS aml
    #         left join account_move am on (am.id=aml.move_id)
    #         left join purchase_order_expenses poe on (poe.invoice_id=am.id)
    #         left join purchase_add_cost pac on (poe.add_cost_id=pac.id)
    #         left join purchase_order_line pol on (pol.add_cost_id_one=pac.id)
    #         left join purchase_order po on (po.id=pol.order_id)
    #     """

    # def _group_by2(self):
    #     return """
    #     group by 1,2,3,4,5,6,7,8,9,10,11,12,13,po.is_add_cost_custom,pac.po_count
    #     """
    # def _group_by(self):
    #     res = super(purchase_acc_view,self)._group_by()
    #     res +="""
    #         ,po.is_add_cost_custom
    #     """
    #     return res
    # def _having2(self):
    #     return """
           
    #     """

    # def _where2(self):
    #     return """
    #     where poe.add_cost_id is not null and am.state='posted'
    #     """

class PurchaseAccViewAdd(models.Model):
    _name = "purchase.acc.view.add"
    _description = "purchase acc view add"
    _auto = False

    partner_id = fields.Many2one('res.partner', string='PO Partner', readonly=True)
    company_id = fields.Many2one('res.company', string='PO Company', readonly=True)
    account_move_line_id = fields.Many2one('account.move.line', string='Financial Records', readonly=True)
    account_id = fields.Many2one('account.account', string='Account', readonly=True)
    acc_state = fields.Char(string='Financial Statements', readonly=True)
    acc_date = fields.Date('Financial Record Date', readonly=True)
    debit = fields.Float('Debit', readonly=True)
    credit = fields.Float('Credit', readonly=True)
    
    def _select(self):
        return """
            SELECT
                aml.id,
                aml.id as account_move_line_id,
                aml.account_id,
                aml.debit,
                aml.credit,
                am.partner_id,
                am.company_id,
                am.state as acc_state,
                aml.date as acc_date
                
        """

    def _from(self):
        return """
            FROM account_move_line AS aml
            left join account_move am on (am.id=aml.move_id)
        """

    def _group_by(self):
        return """
        """

    def _having(self):
        return """
           
        """

    def _where(self):
        return """
        where am.id in (
            select invoice_id from purchase_order_expenses poe where poe.add_cost_id is not null and invoice_id is not null
            )
            or 
            am.stock_move_id in (
                select sm.id from stock_move sm
                where sm.purchase_line_id in (
                    select purchase_order_line_id from purchase_add_cost_purchase_order_line_rel
                ) and sm.purchase_line_id is not null
            )
        """

    def union_all(self):
        return """
        
        """
        
    def _select2(self):
        return """
            
        """

    def _from2(self):
        return """
           
        """

    def _group_by2(self):
        return """
            
        """

    def _having2(self):
        return """
           
        """

    def _where2(self):
        return """
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                %s
            %s
                %s
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(), self._where(), self._group_by(),self._having(), self.union_all(), self._select2(), self._from2(), self._where2(), self._group_by2(),self._having2())
        )
