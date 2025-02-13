# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class sale_plan_pr_report(models.Model):
    _name = "sale.plan.pr.report"
    _description = "Sale plan pr report"
    _auto = False
    _order = 'product_id'

    plan_pr_id = fields.Many2one('sale.plan.pr', string='Баримт', readonly=True)
    product_id = fields.Many2one('product.product', string='Бараа', readonly=True)
    categ_id = fields.Many2one('product.category', string='Ангилал', readonly=True)
    uom_id = fields.Many2one('uom.uom', string='Хэмжих Нэгж', readonly=True)
    bom_id = fields.Many2one('mrp.bom', string='Орц', readonly=True)
    product_qty = fields.Float(string='Тоо хэмжээ')
    product_qty_actual = fields.Float(string='Гүйцэтгэл')
    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('done', 'PR Үүссэн')
    ], readonly=True)
    year = fields.Char(string=u'Жил', readonly=True)
    month = fields.Selection([
        ('1', u'January'),
        ('2', u'February'),
        ('3', u'March'),
        ('4', u'April'),
        ('5', u'May'),
        ('6', u'June'),
        ('7', u'July'),
        ('8', u'August'),
        ('9', u'September'),
        ('10', u'October'),
        ('11', u'November'),
        ('12', u'December'),
    ], string=u'Сар', readonly=True)
    user_id = fields.Many2one('res.users', string='User', readonly=True)
    pr_warehouse_id = fields.Many2one('stock.warehouse', string='PR Агуулах', readonly=True)
    pr_flow_id = fields.Many2one('dynamic.flow', string='PR Урсгал Тохиргоо', readonly=True)
    pr_line_id = fields.Many2one('purchase.request.line', string='PR Мөр', readonly=True)

    def _select(self):
        return """
            SELECT  
                sppl.id as id,
                spp.id as plan_pr_id,
                spp.user_id,
                spp.year::text as year,
                spp.pr_warehouse_id,
                spp.pr_flow_id,
                sppl.pr_line_id,
                spp.state,
                sppl.bom_id,
                sppl.product_id,
                pt.categ_id,
                pt.uom_po_id as uom_id,
                sppl.product_qty,
                0 as product_qty_actual
            FROM sale_plan_pr_line as sppl
            LEFT JOIN sale_plan_pr as spp on (spp.id = sppl.parent2_id)
            LEFT JOIN product_product as pp on (pp.id = sppl.product_id)
            LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
            WHERE spp.state in ('done') and sppl.parent2_id is not null
            union all
             SELECT  
                sml.id as id,
                null as plan_pr_id,
                null as user_id,
                date_part('year', sml.date)::text as year,
                null as pr_warehouse_id,
                null as pr_flow_id,
                null as pr_line_id,
                null as state,
                null as bom_id,
                sml.product_id,
                pt.categ_id,
                pt.uom_po_id as uom_id,
                0 as product_qty,
                (sml.qty_done / uu.factor)*to_unit.factor as product_qty_actual
            FROM stock_move_line as sml
            LEFT JOIN stock_move as sm on (sm.id=sml.move_id)
            LEFT JOIN product_product as pp on (pp.id = sml.product_id)
            LEFT JOIN product_template as pt on (pt.id = pp.product_tmpl_id)
            left join uom_uom uu on (sml.product_uom_id=uu.id)
            left join uom_uom to_unit on (pt.uom_po_id=to_unit.id)
            WHERE sml.state in ('done') and sm.raw_material_production_id is not null
            
        """

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s 
            )""" % (self._table, self._select())
        )
