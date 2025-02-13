# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta, datetime
import logging
_logger = logging.getLogger(__name__)

class SalesMasterPlanLine(models.Model):
    _inherit = 'sales.master.plan.line'
    pr_sale_id = fields.Many2one('sale.plan.pr.line', string='PR үүсгэх мөр')

class SalePlanPrMonth(models.Model):
    _name = 'sale.plan.pr.month'
    _description = 'sale plan pr month'
    name = fields.Char(required=True, string='Сар')

class SalePlanPr(models.Model):
    _name = 'sale.plan.pr'
    _description = 'sale plan pr'
    _inherit = 'mail.thread'
    state = fields.Selection([
        ('draft', 'Ноорог'),
        ('done', 'PR Үүссэн')
    ], default='draft', required=True, string='Төлөв', tracking=True)
    year = fields.Integer(string=u'Жил', copy=True, required=True,
        states={'done': [('readonly', True)]})
    # month = fields.Selection([
    #     ('1', u'January'),
    #     ('2', u'February'),
    #     ('3', u'March'),
    #     ('4', u'April'),
    #     ('5', u'May'),
    #     ('6', u'June'),
    #     ('7', u'July'),
    #     ('8', u'August'),
    #     ('9', u'September'),
    #     ('10', u'October'),
    #     ('11', u'November'),
    #     ('12', u'December'),
    # ], string=u'Сар', copy=True, required=False, readonly=True)
    months = fields.Many2many('sale.plan.pr.month', 'month_plan_sale_plan_pr_rel', 'month_id', 'pr_plan_id', string="Сарууд", copy=True, states={'done': [('readonly', True)]})
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user.id, readonly=True)
    line_plan_ids = fields.One2many('sale.plan.pr.line', 'parent_id', 'Төлөвлөгөөний Мөр', states={'done': [('readonly', True)]})
    line_pr_create_ids = fields.One2many('sale.plan.pr.line', 'parent2_id', 'PR үүсгэх мөр', states={'done': [('readonly', True)]})
    line_pr_pre_bom_ids = fields.One2many('sale.plan.pr.line', 'parent_pre_bom_id', 'Бэлдэх Мөр', states={'done': [('readonly', True)]})
    pr_warehouse_id = fields.Many2one('stock.warehouse', string='PR Агуулах', states={'done': [('readonly', True)]})
    pr_flow_id = fields.Many2one('dynamic.flow', string='PR Урсгал Тохиргоо', domain='[("model_id.model","=","purchase.request")]', states={'done': [('readonly', True)]})
    pr_line_id = fields.Many2one('purchase.request.line', related='line_pr_create_ids.pr_line_id')
    def get_tuple(self, obj):
        if len(obj) > 1:
            return str(tuple(obj))
        else:
            return " ("+str(obj[0])+") "

    def import_line(self):
        # print('')
        if self.line_plan_ids:
            raise UserError(u'Мөр хоосон Биш байна')
        plan_lines = self.env['sales.master.plan.line'].search([('parent_id.year','=',self.year),('parent_id.month','in',self.months.mapped('name')),('product_id.bom_ids','!=',False)]).ids
        if plan_lines:
            plan_lines = self.get_tuple(plan_lines)
            query1 = """
                    SELECT 
                        pl.product_id,
                        sum(pl.qty) as qty,
                        array_agg(pl.id) as update_line_ids
                    FROM sales_master_plan_line as pl
                    left join sales_master_plan as p on (p.id=pl.parent_id)
                    WHERE 
                    pl.id in {0} and pl.pr_sale_id is null
                    GROUP BY pl.product_id
                """.format(plan_lines)
            
            self.env.cr.execute(query1)
            query_result = self.env.cr.dictfetchall()
            line_obj = self.env['sale.plan.pr.line']
            for item in query_result:
                prod_id = self.env['product.product'].browse(item['product_id'])
                bom_id = self.get_bom_sale_pos(prod_id, False)
                if not bom_id:
                    raise UserError(u'Орц олдсонгүй %s'%(prod_id.display_name))
                line_id = line_obj.create({
                    'parent_id': self.id,
                    'product_id': item['product_id'],
                    'product_qty': item['qty'],
                    'bom_id': bom_id.id
                })
                self.env['sales.master.plan.line'].browse(item['update_line_ids']).sudo().write({
                        'pr_sale_id': line_id.id
                })

    def prepare_bom_line(self):
        if not self.line_plan_ids:
            raise UserError(u'Төлөвлөөгний мөр хоосон байна')
        if self.line_pr_pre_bom_ids:
            raise UserError(u'Бэлдэх мөр байна')
        line_obj = self.env['sale.plan.pr.line']
        for item in self.line_plan_ids:
            bom = item.bom_id
            bom_quantity = item.product_qty
            product = item.product_id
            bom_result = self.env['report.mrp.report_bom_structure']._get_pdf_line(bom.id, product_id=product, qty=bom_quantity, unfolded=True)
            for res in bom_result['lines']:
                if res['child_bom']==False and self.env['product.product'].browse(res['prod_id']).purchase_ok:
                    pre_uom_id = self.env['uom.uom'].search([('name','=',res['uom'])], limit=1)
                    line_id = line_obj.create({
                        'parent_pre_bom_id': self.id,
                        'product_id': res['prod_id'],
                        'product_qty': res['quantity'],
                        'plan_pr_pre_line_id': item.id,
                        'pre_uom_id': pre_uom_id.id or False,
                    })


    def create_pr_line(self):
        line_obj = self.env['sale.plan.pr.line']
        # 
        # query1 = """
        #         SELECT 
        #             mbl.product_id,
        #             sum((mbl.product_qty / uu.factor)*to_unit.factor) as qty,
        #             array_agg(sppl.id) as update_line_ids
        #         FROM sale_plan_pr_line sppl
        #         left join mrp_bom_line mbl on (mbl.bom_id=sppl.bom_id)
        #         left join product_product pp on (mbl.product_id=pp.id)
        #         left join product_template pt on (pp.product_tmpl_id=pt.id)
        #         left join uom_uom uu on (pt.uom_id=uu.id)
        #         left join uom_uom to_unit on (mbl.product_uom_id=to_unit.id)
        #         WHERE sppl.parent_id={0}
        #         and mbl.product_id is not null
        #         GROUP BY mbl.product_id
        #      """.format(self.id)
        query1 = """
                SELECT 
                    sppl.product_id,
                    sum((sppl.product_qty / uu.factor)*to_unit.factor) as qty,
                    array_agg(sppl.id) as update_line_ids
                FROM sale_plan_pr_line sppl
                left join product_product pp on (sppl.product_id=pp.id)
                left join product_template pt on (pp.product_tmpl_id=pt.id)
                left join uom_uom uu on (sppl.pre_uom_id=uu.id)
                left join uom_uom to_unit on (pt.uom_po_id=to_unit.id)
                WHERE sppl.parent_pre_bom_id={0}
                and sppl.product_id is not null
                GROUP BY sppl.product_id
             """.format(self.id)
        # print (query1)
        self.env.cr.execute(query1)
        query_result = self.env.cr.dictfetchall()
        line_obj = self.env['sale.plan.pr.line']
        for item in query_result:
            prod_id = self.env['product.product'].browse(item['product_id'])
            line_id = line_obj.create({
                'parent2_id': self.id,
                'product_id': item['product_id'],
                'product_qty': item['qty'],
            })
            line_id.plan_pr_line_ids = [(6,0, item['update_line_ids'])]
            
        # print (blbllb)
    def action_to_draft(self):
        if self.pr_line_id:
            raise UserError(u'PR үүссэн байна')

        self.state = 'draft'

    def action_to_done(self):
        if not self.line_pr_create_ids:
            raise UserError('Pr uusgeh mur alga')
        obj = self.env['purchase.request']
        line_obj = self.env['purchase.request.line']
        obj_id = obj.create({
            'warehouse_id': self.pr_warehouse_id.id,
            'flow_id': self.pr_flow_id.id,
            'employee_id': self.env.user.employee_id.id,
            'date': datetime.now().strftime(DEFAULT_SERVER_DATE_FORMAT),
            'desc': str(self.year)+' '+', '.join(self.months.mapped('name'))+' ТЭМ',
            'branch_id': self.pr_warehouse_id.branch_id.id,
        })

        for item in self.line_pr_create_ids.filtered(lambda r: not r.pr_line_id):
            line_id = line_obj.create({
                'request_id': obj_id.id,
                'product_id': item.product_id.id,
                'desc': item.product_id.display_name,
                'qty': item.product_qty,
                # 'product_qty': item.product_qty,
            })
            item.pr_line_id = line_id.id
        self.state='done'
    def delete_line(self):
        self.line_plan_ids.unlink()
        self.line_pr_create_ids.unlink()
        self.line_pr_pre_bom_ids.unlink()
    def get_bom_sale_pos(self, product_id, mrp_pick_type_id):
        try:
            boms = self.env['mrp.bom']._get_bom_mw(product_id, mrp_pick_type_id)
            if not boms:
                boms = self.env['mrp.bom']._get_bom_mw(product_id, not_picking_type_id=True)
        except Exception as e:
            boms = product_id.bom_ids
        return boms[0] if boms else False

    def view_line_plan(self):
        action = self.env.ref('mw_sales_plan_bom_create_pr.action_sale_plan_pr_daily_line_pivot')
        vals = action.read()[0]
        vals['domain'] = [('parent2_id','=',self.id)]
        return vals

    def view_line(self):
        action = self.env.ref('mw_sales_plan_bom_create_pr.action_sale_plan_pr_daily_line_pivot')
        vals = action.read()[0]
        vals['domain'] = [('parent2_id','=',self.id)]
        return vals

    def view_line_prepare(self):
        action = self.env.ref('mw_sales_plan_bom_create_pr.action_sale_plan_pr_daily_line_pivot')
        vals = action.read()[0]
        vals['domain'] = [('parent_pre_bom_id','=',self.id)]
        return vals
    
    def view_pr(self):
        action = self.env.ref('mw_purchase_request.action_purchase_request_tree_view')
        vals = action.read()[0]
        req_ids = self.line_pr_create_ids.mapped('pr_line_id.request_id')
        vals['domain'] = [('id','in',req_ids.ids)]
        return vals
        
class SalePlanPrLine(models.Model):
    _name = 'sale.plan.pr.line'
    _description = 'sale plan pr line'

    parent_id = fields.Many2one('sale.plan.pr', string='Parent', ondelete='cascade')
    parent2_id = fields.Many2one('sale.plan.pr', string='Parent2', ondelete='cascade')
    parent_pre_bom_id = fields.Many2one('sale.plan.pr', string='Орцонд тааруулж бэлдэх', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Бараа', required=True)
    uom_id = fields.Many2one('uom.uom', string='Хэмжих Нэгж', related='product_id.uom_id')
    bom_id = fields.Many2one('mrp.bom', string='Орц')
    product_qty = fields.Float(string='Тоо хэмжээ')
    pre_uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж Бэлдэх')
    plan_lines = fields.One2many('sales.master.plan.line', 'pr_sale_id', string='Төлөвлөгөөний Мөр', readonly=True)
    plan_pr_pre_line_id = fields.Many2one('sale.plan.pr.line', string='Төлөвлөгөөнд')
    prepare_lines = fields.One2many('sale.plan.pr.line',  'plan_pr_pre_line_id', string='Өөрийн Төлөвлөгөө Мөр Олон', readonly=True)

    plan_pr_line_ids = fields.Many2many('sale.plan.pr.line',  'sale_plan_pr_line_self_rel', 'self_id', 'plan_pr_line_id', string='Өөрийн Төлөвлөгөө Мөр Олон', readonly=True)

    pr_line_id = fields.Many2one('purchase.request.line', string='PR мөр')
    
    from_name = fields.Char('Ямар Бүтээгдэхүүн', compute='_compute_from_name')

    @api.depends('plan_pr_line_ids')
    def _compute_from_name(self):
        for item in self:
            item.from_name = '\n '.join(item.mapped('plan_pr_line_ids.plan_pr_pre_line_id.product_id.display_name'))