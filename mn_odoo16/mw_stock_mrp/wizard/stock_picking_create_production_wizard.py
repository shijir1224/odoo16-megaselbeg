# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class StockPickingCreateProductionWizard(models.TransientModel):
    _name = 'stock.picking.create.production.wizard'
    _description = 'Stock picking create production Wizard'

    production_type = fields.Selection(string="Үйлдвэрлэх төрөл", required=True,
                                       help="Үйлдвэрлэх шаардлагатай: Дотоод шилжүүлгийн нийт тоо хэмжээнээс уг шилжүүлгийн эх байрлалд байгаа тоо хэмжээг хасч үйлдвэрлэл үүсгэнэ.\n"
                                       "Шилжүүлгийн нийт дүнгээр: Дотоод шилжүүлгийн нийт тоо хэмжээгээр үйлдвэрлэл үүсгэнэ",
                                       selection=[
                                           ('need_produce', 'Үйлдвэрлэх шаардлагатай'),
                                           ('all', 'Шилжүүлгийн нийт дүнгээр'),
                                       ],
                                       default="need_produce")

    def create_production(self):
        pickings = self.env['stock.picking'].browse(self.env.context.get('active_ids'))
        pickings = pickings.filtered(lambda r: not r.created_production_id)
        pickings = pickings.filtered(lambda r: r.location_id.usage == 'internal' and r.location_dest_id.usage == 'internal')
        pickings = pickings.filtered(lambda r: r.state == 'confirmed')
        # print('\nmamamamammama', pickings.mapped('location_id'))
        for src_loc in pickings.mapped('location_id'):
            products_qty = {}
            this_pickings = pickings.filtered(lambda r: r.location_id == src_loc)
            for picking in this_pickings:
                for move in picking.move_ids:
                    if move.product_id.id in products_qty.keys():
                        products_qty[move.product_id.id] += move.product_qty
                    else:
                        products_qty[move.product_id.id] = move.product_qty

            # check quantity on src location
            if self.production_type == 'need_produce':
                exist_stock = self.env['stock.quant'].search([
                    ('location_id', '=', src_loc.id),
                    ('product_id', 'in', list(products_qty.keys())),
                ])

                to_delete_ids = []
                for product_id in products_qty:
                    exist_qty = sum(exist_stock.filtered(lambda r: r.product_id.id == product_id).mapped('quantity'))
                    if exist_qty >= products_qty[product_id]:
                        to_delete_ids.append(product_id)
                    elif exist_qty > 0:
                        products_qty[product_id] = products_qty[product_id] - exist_qty

                for del_id in to_delete_ids:
                    del products_qty[del_id]
            # create production
            product_boms = {}
            for product_id in products_qty:
                product = self.env['product.product'].browse([product_id])
                product_boms.update(self.env['mrp.bom']._bom_find(products=product,
                company_id=self.env.company.id))
                prod_src_loc_id = self.env['mrp.production']._get_default_location_src_id()
                if product_boms[product].picking_type_id:
                    prod_src_loc_id = self.env['mrp.production'].with_context(default_picking_type_id=bom.picking_type_id.id)._get_default_location_src_id()
                picking_type = self.env['stock.picking.type'].search([
                    ('company_id', '=', self.env.company.id),
                    ('code', '=', 'mrp_operation'),
                    ('warehouse_id', '=', self.env['stock.warehouse'].search([('active', '=', True), '|', ('lot_stock_id', '=', src_loc.id), ('view_location_id', '=', src_loc.id)]).id)
                ], limit=1)
                production = self.env['mrp.production'].create({
                    'company_id': self.env.company.id,
                    'date_planned_start': fields.Datetime.now(),
                    'location_dest_id': src_loc.id,
                    'location_src_id': prod_src_loc_id,
                    'picking_type_id': picking_type.id,
                    'product_id': product_id,
                    'product_qty': products_qty[product_id],
                    'product_uom_id': product.uom_id.id,
                    'bom_id': product_boms[product] and product_boms[product].id or False,
                    'origin': ', '.join(this_pickings.mapped('name'))
                })

                production._onchange_move_raw()

                this_pickings.write({'created_production_id': production.id})
