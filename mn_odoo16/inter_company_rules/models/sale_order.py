# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError


class sale_order(models.Model):

    _inherit = "sale.order"

    def _auto_warehouse_branch_domain(self):
        return [('id', 'in', self.env.user.branch_ids.ids)] if self.env.user.branch_ids else []

    auto_generated = fields.Boolean(string='Auto Generated Sales Order', copy=False)
    auto_purchase_order_id = fields.Many2one('purchase.order', string='Source Purchase Order', readonly=True, copy=False)
    auto_warehouse_branch_id = fields.Many2one('res.branch', string='Борлуулалт үүсгэх салбар', copy=False, domain=_auto_warehouse_branch_domain)
    is_create_auto_purchase = fields.Boolean(compute='_compute_is_create_auto_purchase', string='Автомат ХА үүсгэх эсэх', store=True)

    @api.depends('partner_id')
    def _compute_is_create_auto_purchase(self):
        for so in self:
            company = self.env['res.company']._find_company_from_partner(so.partner_id.id)
            if company and company.applicable_on in ('sale', 'sale_purchase') and (not so.auto_generated):
                so.is_create_auto_purchase = True
            else:
                so.is_create_auto_purchase = False

    # Тест PO үүсгэх
    def test_inter_company_create_purchase_order(self):
        for order in self:
            if order.state in ['sale','done']:
                company = self.env['res.company']._find_company_from_partner(order.partner_id.id)
                if not order.auto_purchase_order_id and company and company.applicable_on in ('sale', 'sale_purchase') and (not order.auto_generated):
                    order.inter_company_create_purchase_order(company)
    # Дотоод борлуулалтын PO үүсгэх
    def inter_company_create_purchase_order(self, company):
        """ Create a Purchase Order from the current SO (self)
            Note : In this method, reading the current SO is done as sudo, and the creation of the derived
            PO as intercompany_user, minimizing the access right required for the trigger user
            :param company : the company of the created PO
            :rtype company : res.company record
        """
        self = self.with_context(force_company=company.id, company_id=company.id)
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        for rec in self:
            company_partner = rec.company_id and rec.company_id.partner_id or False
            if not company or not company_partner.id:
                continue

            # find user for creating and validating SO/PO from company
            # intercompany_uid = company.intercompany_user_id and company.intercompany_user_id.id or False
            intercompany_uid = self.env.user.id
            # if not intercompany_uid:
            #     raise Warning(_('Provide one user for intercompany relation for % ') % company.name)
            # check intercompany user access rights
            if not PurchaseOrder.with_user(intercompany_uid).check_access_rights('create', raise_exception=False):
                raise Warning(_("Inter company user of company %s doesn't have enough access rights") % company.name)
            
            # create the PO and generate its lines from the SO
            # read it as sudo, because inter-compagny user can not have the access right on PO
            po_vals = rec.sudo()._prepare_purchase_order_data(company, company_partner)
            purchase_order = PurchaseOrder.with_user(intercompany_uid).create(po_vals)
            for line in rec.order_line.sudo().filtered(lambda l: l.qty_delivered > 0):
                po_line_vals = rec._prepare_purchase_order_line_data(line, rec.date_order, purchase_order.id, company)
                # TODO: create can be done in batch; this may be a performance bottleneck
                PurchaseOrderLine.with_user(intercompany_uid).create(po_line_vals)
                print('====qty_delivered', line.qty_delivered)

            # write customer reference field on SO
            rec.client_order_ref = purchase_order.name
            rec.auto_purchase_order_id = purchase_order.id

            # auto-validate the purchase order if needed
            if company.auto_validation:
                purchase_order.with_user(intercompany_uid).button_confirm()

    def _prepare_purchase_order_data(self, company, company_partner):
        """ Generate purchase order values, from the SO (self)
            :param company_partner : the partner representing the company of the SO
            :rtype company_partner : res.partner record
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        self.ensure_one()
        # find location and warehouse, pick warehouse from company object
        PurchaseOrder = self.env['purchase.order']
        # warehouse = company.warehouse_id and company.warehouse_id.company_id.id == company.id and company.warehouse_id or False
        # if not warehouse:
        #     raise Warning(_('Configure correct warehouse for company(%s) from Menu: Settings/Users/Companies' % (company.name)))
        query = """select id from stock_warehouse where company_id = %s and branch_id = %s""" % (company.id, self.auto_warehouse_branch_id.id)
        self.env.cr.execute(query)
        q_res = self.env.cr.dictfetchall()
        print(q_res)
        if not q_res:
            raise Warning('Сонгогдсон компани болон салбарт тохирох агуулах олдсонгүй. Мэдээллээ нягтална уу.')
        if len(q_res) > 1:
            query = """select id from stock_warehouse where company_id = %s and branch_id = %s and is_main_for_branch = 't' limit 1""" % (company.id, self.auto_warehouse_branch_id.id)
            self.env.cr.execute(query)
            q_res = self.env.cr.dictfetchall()
            if not q_res:
                raise Warning('Сонгогдсон салбарт олон агуулах олдлоо. Салбарын үндсэн агуулахыг тохируулна уу.')
        query = """select id from stock_picking_type where code = 'incoming' and warehouse_id = %s""" % q_res[0]['id']
        self.env.cr.execute(query)
        q_res = self.env.cr.dictfetchall()
        if not q_res:
            raise Warning('Хүлээн авах баримтын төрөл %s агуулах дээр олдсонгүй' % warehouse.name)

        # get flow
        purchase_model = self.env['ir.model'].search([('model', '=', 'purchase.order')], limit=1)
        flow = self.env['dynamic.flow'].search([
            ('model_id', '=', purchase_model.id),
            ('user_ids', 'in', [self.env.user.id]),
        ], limit=1)
        flow_line = False
        if flow:
            flow_line = self.env['dynamic.flow.line'].search([
                ('flow_id', '=', flow.id)
            ], order='sequence', limit=1)
        vals = {
            'name': self.env['ir.sequence'].sudo().next_by_code('purchase.order'),
            'origin': self.name,
            'partner_id': company_partner.id,
            'picking_type_id': q_res[0]['id'],
            'date_order': self.date_order,
            'company_id': company.id,
            'fiscal_position_id': company_partner.property_account_position_id.id,
            'payment_term_id': company_partner.property_supplier_payment_term_id.id,
            'auto_generated': True,
            'auto_sale_order_id': self.id,
            'partner_ref': self.name,
            'currency_id': self.currency_id.id,
            'user_id': self.user_id.id,
            'branch_id': self.auto_warehouse_branch_id.id,
            'notes': self.name,
        }
        if flow and flow_line:
            vals.update({
                'flow_id': flow.id,
                'flow_line_id': flow_line.id
            })
        return vals

    @api.model
    def _prepare_purchase_order_line_data(self, so_line, date_order, purchase_id, company):
        """ Generate purchase order line values, from the SO line
            :param so_line : origin SO line
            :rtype so_line : sale.order.line record
            :param date_order : the date of the orgin SO
            :param purchase_id : the id of the purchase order
            :param company : the company in which the PO line will be created
            :rtype company : res.company record
        """
        # price on PO so_line should be so_line - discount
        price = so_line.price_unit - (so_line.price_unit * (so_line.discount / 100))

        # computing Default taxes of so_line. It may not affect because of parallel company relation
        taxes = so_line.tax_id
        if so_line.product_id:
            # taxes = so_line.product_id.supplier_taxes_id
            taxes = self.env['account.tax'].search([('type_tax_use', '=', 'purchase')])

        # fetch taxes by company not by inter-company user
        company_taxes = taxes.filtered(lambda t: t.company_id == company)
        # if purchase_id:
        #     po = self.env["purchase.order"].with_user(company.intercompany_user_id).browse(purchase_id)
        #     company_taxes = po.fiscal_position_id.map_tax(company_taxes, so_line.product_id, po.partner_id)
        if so_line.tax_id:
            if len(so_line.tax_id) > 1:
                raise Warning('1-с олон татвар сонгогдсон үед өөрийн компани хооронд автоматаар ХА үүсгэж чадахгүй')
            else:
                company_taxes = company_taxes.filtered(lambda x: x.price_include == so_line.tax_id.price_include)
        if len(company_taxes) > 1:
            raise Warning('1-с олон ХА-н татвар олдсон тул өөрийн компани хооронд автоматаар ХА үүсгэж чадахгүй')

        quantity = so_line.product_id and so_line.qty_delivered
        return {
            'name': so_line.name,
            'order_id': purchase_id,
            'product_qty': quantity,
            'product_id': so_line.product_id and so_line.product_id.id or False,
            'product_uom': so_line.product_id and so_line.product_uom.id,
            'price_unit': price or 0.0,
            'price_unit_without_discount': price or 0.0,
            'company_id': company.id,
            'date_planned': so_line.order_id.expected_date or date_order,
            'taxes_id': [(6, 0, company_taxes.ids)]
        }

    def action_send(self):
        self.order_line.write({'state': 'sent'})
        return self.write({'state': 'sent'})

    # Холбоотой PO байвал цуцлах
    def action_cancel(self):
        res = super(sale_order, self).action_cancel()
        if self.auto_purchase_order_id:
            self.auto_purchase_order_id.action_cancel_stage()
            self.client_order_ref = ''
        return res

class sale_order_line(models.Model):

    _inherit = "sale.order.line"

    # @api.onchange('product_id', 'warehouse_id')
    # def product_id_change(self):
    #     return super(sale_order_line, self.with_context(is_create_auto_purchase=self.order_id.is_create_auto_purchase)).product_id_change()

    # @api.onchange('product_uom', 'product_uom_qty')
    # def product_uom_change(self):
    #     return super(sale_order_line, self.with_context(is_create_auto_purchase=self.order_id.is_create_auto_purchase)).product_uom_change()

    def _compute_tax_id(self):
        # Override
        for line in self:
            fpos = line.order_id.fiscal_position_id or line.order_id.partner_id.property_account_position_id
            if line.order_id.is_create_auto_purchase:
                taxes = line.product_id.taxes_id.filtered(lambda r: r.company_id == line.order_id.company_id)
            else:
                taxes = line.product_id.taxes_id.filtered(lambda r: not line.company_id or r.company_id == line.company_id)
            line.tax_id = fpos.map_tax(taxes, line.product_id, line.order_id.partner_shipping_id) if fpos else taxes
