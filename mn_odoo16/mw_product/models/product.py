# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import re
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.addons import decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools import format_amount


class PricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    product_tmpl_id = fields.Many2one(
        'product.template', 'Product', ondelete='cascade', check_company=False,
        help="Specify a template if this rule only applies to one product template. Keep empty otherwise.")
    product_id = fields.Many2one(
        'product.product', 'Product Variant', ondelete='cascade', check_company=False,
        help="Specify a product if this rule only applies to one product. Keep empty otherwise.")


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_default_category_id(self):
        return super(ProductTemplate, self)._get_default_category_id()

    def _get_default_uom_id(self):
        return self.env["uom.uom"].search([], limit=1, order='id').id

    name = fields.Char('Name', index=True, required=True, translate=True, tracking=True)
    type = fields.Selection([
        ('consu', _('Consumable')),
        ('service', _('Service')),
        ('product', 'Stockable Product')
    ], string='Product Type', tracking=True, default='product')
    categ_id = fields.Many2one(
        'product.category', 'Internal Category',
        change_default=True, default=_get_default_category_id, domain="[('possible_to_choose', '=', True)]",
        required=True, help="Select category for the current product", tracking=True)

    list_price = fields.Float(
        'Sales Price', default=1.0,
        digits=dp.get_precision('Product Price'),
        help="Base price to compute the customer price. Sometimes called the catalog price.", tracking=True)
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env['res.company']._company_default_get('product.template'), index=1, tracking=True)

    active = fields.Boolean('Active', default=True,
                            help="If unchecked, it will allow you to hide the product without removing it.",
                            tracking=True)

    product_code = fields.Char('Product code', index=True, tracking=True, copy=False)
    default_code = fields.Char(
        'Internal Reference', compute='_compute_default_code',
        inverse='_set_default_code', store=True, tracking=True)

    uom_id = fields.Many2one(
        'uom.uom', 'Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for all stock operations.", tracking=True)
    uom_po_id = fields.Many2one(
        'uom.uom', 'Purchase Unit of Measure',
        default=_get_default_uom_id, required=True,
        help="Default unit of measure used for purchase orders. It must be in the same category as the default unit of measure.",
        tracking=True)
    tracking = fields.Selection([
        ('serial', 'By Unique Serial Number'),
        ('lot', 'By Lots'),
        ('none', 'No Tracking')], string="Tracking",
        help="Ensure the traceability of a storable product in your warehouse.", default='none', required=True,
        tracking=True)

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч')
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч')
    sequence = fields.Integer('Sequence', default=1000, help='Gives the sequence order when displaying a product list')
    huvilbat_too = fields.Integer('Хувилбар тоо', compute='_compute_huvilbat_too', search='_search_huvilbat_too')

    def _construct_tax_string(self, price):
        currency = self.currency_id
        res = self.taxes_id.compute_all(price, product=self, partner=self.env['res.partner'])
        joined = []
        included = res['total_included']
        if not currency:
            currency = self.env.user.company_id.currency_id
        if currency.compare_amounts(included, price):
            joined.append(_('%s Incl. Taxes', format_amount(self.env, included, currency)))
        excluded = res['total_excluded']
        if currency.compare_amounts(excluded, price):
            joined.append(_('%s Excl. Taxes', format_amount(self.env, excluded, currency)))
        if joined:
            tax_string = f"(= {', '.join(joined)})"
        else:
            tax_string = " "
        return tax_string

    def _compute_huvilbat_too(self):
        for item in self:
            item.huvilbat_too = 0

    def _search_huvilbat_too(self, operator, value):
        query = """
        select sm.id from product_template sm
left  join product_product am on (am.product_tmpl_id=sm.id)
group by sm.id
having count(sm.id)>1
        """
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()
        ids = []
        for item in result:
            ids.append(item['id'])
        return [('id', 'in', ids)]

    _sql_constraints = [
        ('product_template_product_code_mw_uniq', 'unique (company_id,product_code)', 'Product code must unique MW')]

    def name_get(self):
        res = []
        for obj in self:
            res_name = super(ProductTemplate, obj).name_get()
            if obj.product_code:
                res_name = '[' + obj.product_code + '] ' + str(res_name[0][1])
                res.append((obj.id, res_name))
            else:
                res.append(res_name[0])
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            # if len(args)>0:
            domain = ['|', '|', ('product_code', operator, name), ('product_code', operator, name),
                      ('product_variant_ids', operator, name)]
            # else:
            #     domain = [('product_code', operator, name)]
        pos = self.search(domain, limit=limit)
        return pos.name_get()


class ProductProduct(models.Model):
    _inherit = "product.product"

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product Template', tracking=True,
        auto_join=True, index=True, ondelete="cascade", required=True)
    default_code = fields.Char('Internal Reference', index=True, tracking=True)
    active = fields.Boolean(
        'Active', default=True,
        help="If unchecked, it will allow you to hide the product without removing it.", tracking=True)
    barcode = fields.Char(
        'Barcode', copy=False,
        help="International Article Number used for product identification.", tracking=True)

    product_code = fields.Char(related='product_tmpl_id.product_code')
    company_id = fields.Many2one('res.company', related='product_tmpl_id.company_id', store=True, readonly=True)

    _sql_constraints = [
        ('product_product_default_code_mw_uniq', 'unique (company_id,default_code)', 'Default code must unique MW')]

    @api.constrains('company_id', 'default_code')
    def _check_default_code(self):
        for record in self.filtered(lambda r: r.default_code):
            # res = record._onchange_default_code()
            domain = [('default_code', '=', record.default_code),('id','!=',record.id)]
            if self.env['product.product'].search(domain, limit=1):
            # if isinstance(res, dict) and res.get('warning'):
                raise ValidationError(_("The Internal Reference '%s' already exists.", self.default_code))
        
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            positive_operators = ['=', 'ilike', '=ilike', 'like', '=like']
            product_ids = []
            if operator in positive_operators:
                product_ids = list(
                    self._search(['|', ('default_code', '=', name), ('product_tmpl_id.product_code', '=', name)] + args,
                                 limit=limit, access_rights_uid=name_get_uid))
                if not product_ids:
                    product_ids = list(
                        self._search([('barcode', '=', name)] + args, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator not in expression.NEGATIVE_TERM_OPERATORS:
                # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
                # on a database with thousands of matching products, due to the huge merge+unique needed for the
                # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
                # Performing a quick memory merge of ids in Python will give much better performance
                product_ids = list(self._search(args + [('default_code', operator, name)], limit=limit))
                if not limit or len(product_ids) < limit:
                    # we may underrun the limit because of dupes in the results, that's fine
                    limit2 = (limit - len(product_ids)) if limit else False
                    product2_ids = self._search(args + [('name', operator, name), ('id', 'not in', product_ids)],
                                                limit=limit2, access_rights_uid=name_get_uid)
                    product_ids.extend(product2_ids)
            elif not product_ids and operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = expression.OR([
                    ['&', ('default_code', operator, name), ('name', operator, name)],
                    ['&', ('default_code', '=', False), ('name', operator, name)],
                ])
                domain = expression.AND([args, domain])
                product_ids = list(self._search(domain, limit=limit, access_rights_uid=name_get_uid))
            if not product_ids and operator in positive_operators:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    product_ids = list(self._search([('default_code', '=', res.group(2))] + args, limit=limit,
                                                    access_rights_uid=name_get_uid))
            # still no results, partner in context: search on supplier info as last hope to find something
            if not product_ids and self._context.get('partner_id'):
                suppliers_ids = self.env['product.supplierinfo']._search([
                    # ('name', '=', self._context.get('partner_id')),
                    # '|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)], access_rights_uid=name_get_uid)
                if suppliers_ids:
                    product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit,
                                               access_rights_uid=name_get_uid)
        else:
            product_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return product_ids

    def name_get(self):
        res = []
        for obj in self:
            res_name = super(ProductProduct, obj).name_get()
            if obj.product_tmpl_id.product_code:
                res_name = '[' + obj.product_code + '] ' + str(res_name[0][1])
                res.append((obj.id, res_name))
            else:
                res.append(res_name[0])
        return res


class StockReportDetail(models.Model):
    _inherit = "stock.report.detail"

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч')
    product_code = fields.Char(string='Эдийн дугаар', readonly=True)

    def _select(self):
        select_str = super(StockReportDetail, self)._select()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select2(self):
        select_str = super(StockReportDetail, self)._select2()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select3(self):
        select_str = super(StockReportDetail, self)._select3()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select4(self):
        select_str = super(StockReportDetail, self)._select4()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select_main(self):
        select_str = super(StockReportDetail, self)._select_main()
        select_str += """
            ,supplier_partner_id
            ,production_partner_id
            ,product_code
        """
        return select_str


class ProductBothIncomeExpenseReport(models.Model):
    _inherit = "product.both.income.expense.report"

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    product_code = fields.Char(string='Эдийн дугаар', readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч', readonly=True)

    def _select(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select2(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select2()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select3(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select3()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select4(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select4()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select_main(self):
        select_str = super(ProductBothIncomeExpenseReport, self)._select_main()
        select_str += """
            ,supplier_partner_id
            ,production_partner_id
            ,product_code
        """
        return select_str


class ProductIncomeExpenseReport(models.Model):
    _inherit = "product.income.expense.report"

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    product_code = fields.Char(string='Эдийн дугаар', readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч', readonly=True)

    def _select(self):
        select_str = super(ProductIncomeExpenseReport, self)._select()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str


class ProductBalancePivotReport(models.Model):
    _inherit = "product.balance.pivot.report"

    supplier_partner_id = fields.Many2one('res.partner', 'Нэг нийлүүлэгч', readonly=True)
    product_code = fields.Char(string='Эдийн дугаар', readonly=True)
    production_partner_id = fields.Many2one('res.partner', 'Нэг Үйлдвэрлэгч', readonly=True)

    def _select(self):
        select_str = super(ProductBalancePivotReport, self)._select()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str

    def _select2(self):
        select_str = super(ProductBalancePivotReport, self)._select2()
        select_str += """
            ,pt.supplier_partner_id
            ,pt.production_partner_id
            ,pt.product_code
        """
        return select_str
