# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError

class stock_picking_many_done(models.TransientModel):
    _name = 'stock.picking.many.done'
    _description = 'stock.picking.many.done'

    def _default_picking(self):
        objs = self.env['stock.picking'].browse(self._context['active_ids']).filtered(lambda r: r.state not in ['done','cancel'])
        if objs:
            return objs.ids
        return False

    picking_ids = fields.Many2many('stock.picking',string='Olon picking', default=_default_picking)
    is_copy_done = fields.Boolean(string='Захиалсан Тоог Дууссанруу хуулж батлах', default=False)

    def copy_uom_qty_to_done(self, pick):
        self.ensure_one()
        if pick.state not in ['done','cancel']:
            for line in pick.move_ids:
                if not line.quantity_done:
                    line._set_quantity_done(line.product_uom_qty)

    def action_picking_done(self, pick):
        if pick.state in ['done','cancel']:
            return False
        if pick.state=='draft':
            pick.action_confirm()
        if self.is_copy_done:
            self.copy_uom_qty_to_done(pick)

        pick.action_assign()
        pick.action_confirm()
        pick.with_context(skip_immediate=True,skip_backorder=True,skip_expired=True,skip_sms=True).button_validate()
        return True

    def supply(self):
        for item in self.picking_ids:
            self.action_picking_done(item)
            # if item.state!='done':
            #     raise UserError('%s hudulguun duussangui'%item.display_name)
            