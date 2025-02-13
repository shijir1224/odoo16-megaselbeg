from odoo import api, fields, models, _


class StockReturnPickingLine(models.TransientModel):
    _inherit = 'stock.return.picking.line'
    price_unit = fields.Float('Нэгж үнэ', required=True, digits='Product Price', compute='compute_price_unit')

    @api.onchange('wizard_id.cost_method')
    def compute_price_unit(self):
        for obj in self:
            if obj.wizard_id.cost_method == 'main':
                obj.price_unit = obj.product_id.standard_price
            else:
                obj.price_unit = obj.move_id.price_unit


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    return_desc = fields.Char('Буцаалтын тайлбар')
    cost_method = fields.Selection([('picking', 'Агуулахын баримтын үнээр'),
                                    ('main', 'Одоо байгаа өртөгөөр')], required=True, default='picking', string='Өртөг')

    @api.onchange('cost_method')
    def onchange_cost_method(self):
        for obj in self:
            obj.product_return_moves.compute_price_unit()

    def _create_returns(self):
        new_picking_id, pick_type_id = super(StockReturnPicking, self)._create_returns()
        if new_picking_id and self.return_desc:
            pick_id = self.env['stock.picking'].browse(new_picking_id)
            pick_id.origin = str(pick_id.origin) + u' ' + self.return_desc
        for item in self.picking_id.move_ids:
            if item.product_id.tracking != 'none':
                for new_move in self.env['stock.picking'].browse(new_picking_id).move_ids:
                    new_move_line_id = new_move.move_line_ids.filtered(lambda r: not r.lot_id and r.product_id.id==item.product_id.id)
                    if new_move_line_id:
                        new_move_line_id = new_move_line_id[0]
                        lot_ids = new_move.move_line_ids.mapped('lot_id').ids
                        old_move_line_id = item.move_line_ids.filtered(lambda r: r.lot_id not in lot_ids and r.product_id.id==item.product_id.id)
                        if old_move_line_id:
                            old_move_line_id = old_move_line_id[0]
                        new_move_line_id.lot_id = old_move_line_id.lot_id.id
                        break
                    # qty_save = 
        return new_picking_id, pick_type_id 

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = super(StockReturnPicking, self)._prepare_move_default_values(return_line, new_picking)
        vals['price_unit'] = return_line.price_unit
        return vals

    def _prepare_picking_default_values(self):
        res = super(StockReturnPicking, self)._prepare_picking_default_values()
        res['return_cost_method'] = self.cost_method
        return res
