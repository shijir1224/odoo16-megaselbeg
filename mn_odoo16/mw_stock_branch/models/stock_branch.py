# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules
from odoo.osv import expression
import operator as py_operator

OPERATORS = {
    '<': py_operator.lt,
    '>': py_operator.gt,
    '<=': py_operator.le,
    '>=': py_operator.ge,
    '=': py_operator.eq,
    '!=': py_operator.ne
}

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    set_warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', related='location_id.set_warehouse_id', readonly=True)

    @api.model
    def action_view_quants(self):
        res = super(StockQuant, self).action_view_quants()
        if self.user_has_groups('mw_stock_branch.group_stock_by_branch'):
            domain_quant = res['domain']
            warehouse_ids = [self.env.user.warehouse_id.id]+self.env.user.warehouse_ids.ids
            domain_quant.append(('location_id.set_warehouse_id', 'in', warehouse_ids))
            res['domain'] = domain_quant
        return res

class ProductDetailedIncomeExpenseReport(models.TransientModel):
    _inherit = "product.detailed.income.expense"  

    @api.onchange('import_wh')
    def onchange_all_wh_import(self):
        # res = super(ProductDetailedIncomeExpenseReport, self).onchange_all_wh_import()
        if self.import_wh and self.user_has_groups('mw_stock_branch.group_stock_by_branch'):
            warehouse_ids = [self.env.user.warehouse_id.id]+self.env.user.warehouse_ids.ids
            self.warehouse_id = self.env['stock.warehouse'].search([('id','in',warehouse_ids)])
        else:
            return super(ProductDetailedIncomeExpenseReport, self).onchange_all_wh_import()
        # return res

class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_available_branch = fields.Float(
        'Үлдэгдэл Өөрийн', compute='_compute_quantities_branch', search='_search_qty_available_branch',
        digits='Product Unit of Measure', compute_sudo=False,
        help="Өөрийн үлдэгдэл харуулна")

    def _search_qty_available_branch(self, operator, value):
        # In the very specific case we want to retrieve products with stock available, we only need
        # to use the quants, not the stock moves. Therefore, we bypass the usual
        # '_search_product_quantity' method and call '_search_qty_available_new' instead. This
        # allows better performances.
        if value == 0.0 and operator == '>' and not ({'from_date', 'to_date'} & set(self.env.context.keys())):
            product_ids = self._search_qty_available_new_branch(
                operator, value, self.env.context.get('lot_id'), self.env.context.get('owner_id'),
                self.env.context.get('package_id')
            )
            return [('id', 'in', product_ids)]
        return self._search_product_quantity_branch(operator, value, 'qty_available_branch')
    
    def _search_product_quantity_branch(self, operator, value, field):
        # TDE FIXME: should probably clean the search methods
        # to prevent sql injections
        if field not in ('qty_available_branch'):
            raise UserError(_('Invalid domain left operand %s') % field)
        if operator not in ('<', '>', '=', '!=', '<=', '>='):
            raise UserError(_('Invalid domain operator %s') % operator)
        if not isinstance(value, (float, int)):
            raise UserError(_('Invalid domain right operand %s') % value)

        # TODO: Still optimization possible when searching virtual quantities
        ids = []
        # Order the search on `id` to prevent the default order on the product name which slows
        # down the search because of the join on the translation table to get the translated names.
        for product in self.with_context(prefetch_fields=False).search([], order='id'):
            if OPERATORS[operator](product[field], value):
                ids.append(product.id)
        return [('id', 'in', ids)]
    
    def _search_qty_available_new_branch(self, operator, value, lot_id=False, owner_id=False, package_id=False):
        ''' Optimized method which doesn't search on stock.moves, only on stock.quants. '''
        product_ids = set()
        domain_quant = self._get_domain_locations_branch()[0]
        if lot_id:
            domain_quant.append(('lot_id', '=', lot_id))
        if owner_id:
            domain_quant.append(('owner_id', '=', owner_id))
        if package_id:
            domain_quant.append(('package_id', '=', package_id))
        quants_groupby = self.env['stock.quant'].read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id')
        for quant in quants_groupby:
            if OPERATORS[operator](quant['quantity'], value):
                product_ids.add(quant['product_id'][0])
        return list(product_ids)

    def _compute_quantities_branch(self):
        products = self.filtered(lambda p: p.type != 'service')
        domain_quant_loc = self._get_domain_locations_branch()[0]
        Quant = self.env['stock.quant']
        for product in products:
            domain_quant = [('product_id', '=', product.id)] + domain_quant_loc
            quants_res = dict((item['product_id'][0], (item['quantity'], item['reserved_quantity'])) for item in Quant.read_group(domain_quant, ['product_id', 'quantity', 'reserved_quantity'], ['product_id'], orderby='id'))
            product.qty_available_branch =  quants_res.get(product.id, [0.0])[0]

        # Services need to be set with 0.0 for all quantities
        services = self - products
        services.qty_available_branch = 0.0
    
    def _get_domain_locations_branch(self):
        company_id = self.env.company.id
        warehouse_ids = [self.env.user.warehouse_id.id]+self.env.user.warehouse_ids.ids
        return (
            [('location_id.set_warehouse_id', 'in', warehouse_ids), ('location_id.company_id', '=', company_id), ('location_id.usage', 'in', ['internal', 'transit'])],
        )
    
    def action_open_quants_branch(self):
        location_domain = self._get_domain_locations_branch()[0]
        print ('location_domain',location_domain)
        domain = expression.AND([[('product_id', 'in', self.ids)], location_domain])
        hide_location = not self.user_has_groups('stock.group_stock_multi_locations')
        hide_lot = all([product.tracking == 'none' for product in self])
        self = self.with_context(hide_location=hide_location, hide_lot=hide_lot)

        # If user have rights to write on quant, we define the view as editable.
        if self.user_has_groups('stock.group_stock_manager'):
            self = self.with_context(inventory_mode=True)
            # Set default location id if multilocations is inactive
            if not self.user_has_groups('stock.group_stock_multi_locations'):
                user_company = self.env.company
                warehouse = self.env['stock.warehouse'].search(
                    [('company_id', '=', user_company.id)], limit=1
                )
                if warehouse:
                    self = self.with_context(default_location_id=warehouse.lot_stock_id.id)
        # Set default product id if quants concern only one product
        if len(self) == 1:
            self = self.with_context(
                default_product_id=self.id,
                single_product=True
            )
        else:
            self = self.with_context(product_tmpl_id=self.product_tmpl_id.id)
        ctx = dict(self.env.context)
        ctx.update({'no_at_date': True})
        
        return self.env['stock.quant'].with_context(ctx)._get_quants_action(domain)

    def action_view_stock_move_lines(self):
        res = super(ProductProduct, self).action_view_stock_move_lines()
        if self.user_has_groups('mw_stock_branch.group_stock_by_branch'):
            domain_quant = res['domain']
            warehouse_ids = [self.env.user.warehouse_id.id]+self.env.user.warehouse_ids.ids
            domain_quant.append(('|'))
            domain_quant.append(('location_id.set_warehouse_id', 'in', warehouse_ids))
            domain_quant.append(('location_dest_id.set_warehouse_id', 'in', warehouse_ids))
            res['domain'] = domain_quant
        return res

    def action_view_stock_move_lines_mw(self):
        res = super(ProductProduct, self).action_view_stock_move_lines_mw()
        if self.user_has_groups('mw_stock_branch.group_stock_by_branch'):
            domain_quant = res['domain']
            warehouse_ids = [self.env.user.warehouse_id.id]+self.env.user.warehouse_ids.ids
            domain_quant.append(('|'))
            domain_quant.append(('location_id.set_warehouse_id', 'in', warehouse_ids))
            domain_quant.append(('location_dest_id.set_warehouse_id', 'in', warehouse_ids))
            res['domain'] = domain_quant
        return res

class ProductTemplace(models.Model):
    _inherit = 'product.template'

    qty_available_branch = fields.Float(
        'Үлдэгдэл Салбараар', compute='_compute_quantities_branch', search='_search_qty_available_branch',
        compute_sudo=False, digits='Product Unit of Measure')
    
    @api.depends_context('company_owned', 'force_company')
    def _compute_quantities_branch(self):
        for template in self:
            qty_available_branch = 0
            for p in template.product_variant_ids:
                qty_available_branch += p.qty_available_branch
                
            template.qty_available_branch = qty_available_branch
        
    def action_open_quants_branch(self):
        return self.product_variant_ids.action_open_quants_branch()

    def _search_qty_available_branch(self, operator, value):
        domain = [('qty_available_branch', operator, value)]
        product_variant_ids = self.env['product.product'].search(domain)
        return [('product_variant_ids', 'in', product_variant_ids.ids)]

    def action_view_stock_move_lines(self):
        res = super(ProductTemplace, self).action_view_stock_move_lines()
        if self.user_has_groups('mw_stock_branch.group_stock_by_branch'):
            domain_quant = res['domain']
            warehouse_ids = [self.env.user.warehouse_id.id]+self.env.user.warehouse_ids.ids
            domain_quant.append(('|'))
            domain_quant.append(('location_id.set_warehouse_id', 'in', warehouse_ids))
            domain_quant.append(('location_dest_id.set_warehouse_id', 'in', warehouse_ids))
            res['domain'] = domain_quant
        return res

    def action_view_stock_move_lines_mw(self):
        res = super(ProductTemplace, self).action_view_stock_move_lines_mw()
        if self.user_has_groups('mw_stock_branch.group_stock_by_branch'):
            domain_quant = res['domain']
            warehouse_ids = [self.env.user.warehouse_id.id]+self.env.user.warehouse_ids.ids
            domain_quant.append(('|'))
            domain_quant.append(('location_id.set_warehouse_id', 'in', warehouse_ids))
            domain_quant.append(('location_dest_id.set_warehouse_id', 'in', warehouse_ids))
            res['domain'] = domain_quant
        return res

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    branch_id  = fields.Many2one('res.branch', store=True, readonly=False, compute='_compute_res_branch')

    @api.depends('warehouse_id')
    def _compute_res_branch(self):
        for item in self:
            item.branch_id = item.warehouse_id.branch_id.id
            
class res_branch(models.Model):
    _inherit = "res.branch"

    diff_partner_id  = fields.Many2one('res.partner', string='Тооллогийн Зөрүүгийн Харилцагч')


# class stock_inventory(models.Model):
#     _inherit = "stock.inventory"
#
#     @api.model
#     def _default_branch_id_main(self):
#         return self.env.user.branch_id.id
#
#     @api.model
#     def _default_diff_partner_id_inherit(self):
#         branch_id = self.branch_id or self.env.user.branch_id
#         return branch_id.diff_partner_id.id
#
#     diff_partner_id = fields.Many2one('res.partner', string=u'Зөрүүгийн Харилцагч', default=_default_diff_partner_id_inherit)
#     branch_id  = fields.Many2one('res.branch', string='Салбар', store=True, compute='_compute_res_branch', default=_default_branch_id_main)
#
#     @api.depends('line_ids')
#     def _compute_res_branch(self):
#         for item in self:
#             if not item.branch_id and item.line_ids:
#                 item.branch_id = item.line_ids[0].location_id.set_warehouse_id.branch_id.id
#
#     def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
#         res = super(stock_inventory, self)._generate_valuation_lines_data(partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
#         res['credit_line_vals']['branch_id'] = self.branch_id.id
#         res['debit_line_vals']['branch_id'] = self.branch_id.id
#         return res