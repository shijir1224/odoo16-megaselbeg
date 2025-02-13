# -*- coding: utf-8 -*-

from odoo import api, fields, models
import json
from odoo.exceptions import UserError
from odoo.tools.translate import _
from .constants import *
import requests
import logging
from datetime import timedelta
import pytz
from odoo.osv.expression import AND

_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    discount_info = fields.Float(string='Pricelist Discount')

    @api.model
    def create(self, values):
        #         print ('values mw ',values)
        if values.get('order_id') and values.get('product_id'):
            # set name based on the sequence specified on the config
            order_id = self.env['pos.order'].browse(values['order_id'])
            pricelist_id = order_id.pricelist_id
            if pricelist_id and pricelist_id.id != 1:
                product = self.env['product.product'].browse(values.get('product_id'))
                lst_price = product.list_price
                price = pricelist_id.get_product_price(
                    product, values.get('qty') or 1.0, order_id.partner_id)
                values.update({'discount_info': lst_price - price})
        return super(PosOrderLine, self).create(values)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.order_id.pricelist_id:
                raise UserError(
                    _('You have to select a pricelist in the sale form !\n'
                      'Please set one before choosing a product.'))
            price = self.order_id.pricelist_id.get_product_price(
                self.product_id, self.qty or 1.0, self.order_id.partner_id)
            self.tax_ids = self.product_id.taxes_id.filtered(
                lambda r: not self.company_id or r.company_id == self.company_id)
            tax_ids_after_fiscal_position = self.order_id.fiscal_position_id.map_tax(self.tax_ids)
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(price, self.tax_ids,
                                                                                      tax_ids_after_fiscal_position,
                                                                                      self.company_id)
            self._onchange_qty()


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _apply_invoice_payments(self):
        '''Төлбөр үүсгэж төлөхгүй
        '''
        return True

    bill_id = fields.Char(string='Bill ID', help="EBarimt Bill Id.")
    bill_printed_date = fields.Datetime(string='Bill Printed Date')
    bill_type = fields.Selection([(BILL_TYPE_NOTAX, 'No Tax'),
                                  (BILL_TYPE_INDIVIDUAL, 'Individual'),
                                  (BILL_TYPE_COMPANY, 'Company'),
                                  (BILL_TYPE_INVOICE, 'Invoice')], default=BILL_TYPE_INDIVIDUAL)
    bill_mac_address = fields.Char(string='Bill MAC Address')
    tax_type = fields.Char(string='Bill Tax Type', compute='_tax_type')
    amount_tax_vat = fields.Float(compute='_compute_taxes', string='Taxes VAT', digits=0)
    amount_tax_city = fields.Float(compute='_compute_taxes', string='Taxes City', digits=0)
    customer_register = fields.Char('Customer Register')
    customer_name = fields.Char('Customer Name')
    discount_move_id = fields.Many2one('account.move', string='Discount move',)

    def _amount_tax(self, line, fiscal_position_id, ebarimt_tax_type_code):
        taxes = line.tax_ids.filtered(lambda
                                          t: t.company_id.id == line.order_id.company_id.id and t.ebarimt_tax_type_id.code == ebarimt_tax_type_code)

        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes)

        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        cur = line.order_id.pricelist_id.currency_id
        taxes = \
            taxes.compute_all(price, cur, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)[
                'taxes']
        val = 0.0
        for c in taxes:
            val += c.get('amount', 0.0)
        return val

    @api.depends('lines.price_subtotal_incl', 'lines.discount')
    def _compute_taxes(self):
        for order in self:
            currency = order.pricelist_id.currency_id
            order.amount_tax_vat = currency.round(
                sum(self._amount_tax(line, order.fiscal_position_id, TAX_TYPE_VAT) for line in order.lines))
            order.amount_tax_city = currency.round(
                sum(self._amount_tax(line, order.fiscal_position_id, TAX_TYPE_CITY) for line in order.lines))

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['customer_register'] = ui_order.get('customerReg', False)
        order_fields['customer_name'] = ui_order.get('customerName', False)
        order_fields['bill_type'] = ui_order['bill_type']
        if order_fields.get('partner_id', False):
            if self.env['res.partner'].browse(order_fields['partner_id']).nuat_no:
                lines = order_fields['lines']
                for item in lines:
                    del item[2]['tax_ids']
        return order_fields

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        order_fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)

        if ui_paymentline.get('utga', False):
            order_fields.update({'name': ui_paymentline.get('utga', '')})
        return order_fields

    #     @api.model
    #     def _order_fields(self, ui_order):
    #         result = super(PosOrder, self)._order_fields(ui_order)
    #         if result.get('partner_id', False):
    #             if self.env['res.partner'].browse(result['partner_id']).nuat_no:
    #                 lines = result['lines']
    #                 for item in lines:
    #                     del item[2]['tax_ids']
    #         return result

    def _tax_type(self):
        self.tax_type = None
        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code in [TAX_TYPE_VAT, TAX_TYPE_CITY] for t
               in self.lines.tax_ids):
            self.tax_type = TAX_TYPE_VAT
        if all(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == TAX_TYPE_VAT_FREE for t in
               self.lines.tax_ids):
            self.tax_type = TAX_TYPE_VAT_FREE
        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == TAX_TYPE_VAT_ZERO for t in
               self.lines.tax_ids):
            self.tax_type = TAX_TYPE_VAT_ZERO
        if self.partner_id and self.partner_id.nuat_no:
            self.tax_type = TAX_TYPE_VAT_FREE

    @api.model
    def get_ebarimt(self, server_ids):
        ebarimt_data = []

        for s in server_ids:
            order = self.env['pos.order'].browse(s['id'])

            if order.bill_type == BILL_TYPE_NOTAX:
                return ebarimt_data

            # if order.to_invoice:
            #     return ebarimt_data

            result = order.send_ebarimt()
            print ("result -- ", result)
            if result:
                ebarimt_data.append(
                    {'bill_id': result['billId'], 'lottery': result['lottery'], 'qr_data': result['qrData']})

        return ebarimt_data

    def generate_order_json(self):
        data = {}
        data['reportMonth'] = ""
        data['districtCode'] = self.session_id.config_id.aimag_district_id.code or self.env[
            'ebarimt.aimag.district'].search([('name', 'ilike', self.env.user.company_id.state_id.name)], limit=1).code
        data['branchNo'] = (self.session_id.config_id.branch_no or str(1)).zfill(3)
        data['posNo'] = (self.session_id.config_id.pos_no or str(1)).zfill(4)
        # data['billIdSuffix'] = self.env['ir.sequence'].next_by_code('ebarimt.billid.suffix')
        data['billIdSuffix'] = ""
        data['billType'] = self.bill_type
        data['taxType'] = self.tax_type

        data['customerNo'] = ""
        if self.bill_type == BILL_TYPE_COMPANY:
            if not self.customer_register:
                raise UserError(_('You need to set customer''s VAT number before you can proceed company pos order.'))
            data['customerNo'] = self.customer_register
        if self.bill_type == BILL_TYPE_INVOICE:
            if not self.partner_id or not self.partner_id.vat:
                raise UserError(_('You need to set customer''s VAT number before you can proceed company pos order.'))
            data['customerNo'] = self.partner_id.vat

        if self.partner_id.nuat_no:
            data['taxType'] = self.tax_type
        data['amount'] = "%.2f" % self.amount_total
        data['vat'] = "%.2f" % self.amount_tax_vat
        data['cityTax'] = "%.2f" % self.amount_tax_city

        cashAmount = sum(p.amount for p in self.payment_ids if p.payment_method_id.is_cash_count)
        data['cashAmount'] = "%.2f" % (0 if cashAmount < 0 else cashAmount)
        nonCashAmount = sum(p.amount for p in self.payment_ids if not p.payment_method_id.is_cash_count)
        data['nonCashAmount'] = "%.2f" % (self.amount_total if nonCashAmount > self.amount_total else nonCashAmount)

        data['returnBillId'] = self.bill_id or ""
        data['invoiceId'] = ""
        return data

    def generate_order_line_json(self, order_line):
        data = {}
        data['code'] = order_line.product_id.code
        data['barcode'] = order_line.product_id.barcode
        data['name'] = order_line.product_id.name
        data['measureUnit'] = order_line.product_id.uom_id.name
        data['qty'] = "%.2f" % order_line.qty
        data['unitPrice'] = "%.2f" % order_line.price_unit
        data['totalAmount'] = "%.2f" % order_line.price_subtotal

        data['vat'] = "%.2f" % order_line.amount_tax_vat
        data['cityTax'] = "%.2f" % order_line.amount_tax_city

        return data

    # def refund(self):
    #     for order in self:
    #         if order.bill_id:
    #             return_bill_json = {"data": self.generate_return_bill_json()}
    #             self.env['ebarimt.send'].returnBill(json.dumps(return_bill_json, indent=2))
    #     return super(PosOrder, self).refund()

    def generate_return_bill_json(self):
        data = {}
        data['returnBillId'] = self.bill_id
        data['date'] = self.bill_printed_date.strftime('%Y-%m-%d %H:%M:%S')
        # data['amount'] = '%s'%(self.amount_paid)
        return data

    def send_ebarimt(self):
        order_json = self.generate_order_json()
        order_lines = []
        for line in self.lines:
            if line.product_id.code:
                order_lines.append(self.generate_order_line_json(line))

        order_json['stocks'] = order_lines
        ebarimt_send = self.env['ebarimt.send']
        order_json = {"data": order_json}
        result = {}
        if float(order_json["data"]["cashAmount"]) != 0.0 or float(order_json["data"]["nonCashAmount"]) != 0.0:
            result = ebarimt_send.put(json.dumps(order_json, indent=2))

            # result = self.env['ebarimt.send'].put(data=json.dumps(order_json,indent=2), library_filename=self.session_id.config_id.library_filename)
            self.bill_id = result['billId']
            self.bill_printed_date = fields.Datetime.from_string(result['date'])
            self.bill_mac_address = result['macAddress']
        return result

    def print_ebarimt(self):
        self.ensure_one()
        # result = self.send_ebarimt()
        data = {'model': 'pos.order',
                # #'lottery_no': result['lottery'],
                # 'qr_data': result['qrData'],
                }

        return self.env.ref('mw_pos.action_report_ebarimt_pos_receipt').report_action(self, data=data)

    @api.model
    def get_merchant_info(self, urlInput):
        """ Get metchant info from ebarimt REST api """
        resp = requests.get(url=(self.env.company.ebarimt_customer_check_url + urlInput))
        try:
            data = json.loads(resp.text)
        except Exception as e:
            raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e.message)
        return data


    def _generate_pos_order_invoice(self):
        moves = self.env['account.move']
        print ('pos invoice ============================123 ')
        journal = self.session_id.config_id.journal_id
        
        for order in self:
            has_disc=False
            for line in order.lines:
                if line.discount or  line.discount_info:
                    has_disc=True
            if has_disc:
                account_move = self.env['account.move'].with_context(default_journal_id=journal.id).create({
                    'journal_id': journal.id,
                    'date': fields.Date.context_today(self),
                    'ref': self.name+u' хөнгөлөлт',
                })     
                order.write({'discount_move_id':account_move.id})       
                order._create_discount_lines()
                
                # Force company for all SUPERUSER_ID action
            if order.account_move:
                moves += order.account_move
                continue

            if not order.partner_id:
                raise UserError(_('Please provide a partner for the sale.'))

            move_vals = order._prepare_invoice_vals()
            new_move = order._create_invoice(move_vals)

            order.write({'account_move': new_move.id, 'state': 'invoiced'})
            if new_move and new_move.line_ids:
                new_move.sudo().with_company(order.company_id)._post()
            moves += new_move
            order._apply_invoice_payments()

        if not moves:
            return {}

        return {
            'name': _('Customer Invoice'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': moves and moves.ids[0] or False,
        }

    def _create_discount_lines(self):
        def get_income_disc_account(order_line):
            product = order_line.product_id
            income_account = product.with_company(order_line.company_id)._get_product_accounts()['income_discount']
            if not income_account:
                raise UserError(_('Please define income discount account for this product: "%s" (id:%d).')
                                % (product.name, product.id))
            return order_line.order_id.fiscal_position_id.map_account(income_account)
        def get_income_account(order_line):
            product = order_line.product_id
            income_account = product.with_company(order_line.company_id)._get_product_accounts()['income']
            print ('income_account ',income_account)
            if not income_account:
                raise UserError(_('Please define income discount account for this product: "%s" (id:%d).')
                                % (product.name, product.id))
            return order_line.order_id.fiscal_position_id.map_account(income_account)
                                
        MoveLine = self.env['account.move.line'].with_context(check_move_validity=False)

#         orders_data = self.env['pos.order'].search([('session_id', 'in', self.ids)])

        total_disc={}
        for line in self.lines:
            if line.discount:
                discount_account=get_income_disc_account(line).id,
                income_account=get_income_account(line).id,
                if discount_account and total_disc.get(discount_account,False):
                    total_disc[discount_account]['amount']+=line.qty*line.price_unit-line.price_subtotal_incl
                else:
                    total_disc[discount_account]={'name':'Хөнгөлөлт',
                                                    'amount':line.qty*line.price_unit-line.price_subtotal_incl,
                                                  'income_account':income_account,
                                                'product_id':line.product_id
                                                    }
            elif  line.discount_info:
                discount_account=get_income_disc_account(line).id,
                income_account=get_income_account(line).id,
                if discount_account and total_disc.get(discount_account,False):
                    total_disc[discount_account]['amount']+=line.qty*line.discount_info
                else:
                    total_disc[discount_account]={'name':'Хөнгөлөлт',
                                                    'amount':line.qty*line.discount_info,
                                                  'income_account':income_account,
                                                  'product_id':line.product_id
                                                  }
#         print ('total_disc ',total_disc)

        aml_vals=[]
        for d in total_disc:
            if total_disc[d]['product_id']:
                analytic_account_id = total_disc[d]['product_id'].product_brand_id.analytic_account_id.id
            else:
                analytic_account_id = False
            source_vals = self._debit_amounts({'account_id': d,
                                                'analytic_account_id':analytic_account_id,
                                               'name':total_disc[d]['name'],
                                               'move_id':self.discount_move_id.id}, 0, total_disc[d]['amount']/1.1)
            dest_vals = self._credit_amounts({'account_id': total_disc[d]['income_account'],
                                                'analytic_account_id':analytic_account_id,
                                              'name':total_disc[d]['name'],
                                              'move_id':self.discount_move_id.id}, 0, total_disc[d]['amount']/1.1)
            aml_vals.append(source_vals)
            aml_vals.append(dest_vals)
            _logger.info('---------------aml_vals {0}'.format(aml_vals))
            
#         source_vals = self._debit_amounts({'account_id': 2908,'move_id':self.move_id.id}, 0, total_disc)
#         dest_vals = self._credit_amounts({'account_id': 2813,'move_id':self.move_id.id}, 0, total_disc)
        MoveLine.create(
            aml_vals
#             [source_vals,dest_vals]
        )
        return True
    

    def _credit_amounts(self, partial_move_line_vals, amount, amount_converted, force_company_currency=False):
        additional_field = {}
        return {
            'debit': -amount_converted if amount_converted < 0.0 else 0.0,
            'credit': amount_converted if amount_converted > 0.0 else 0.0,
            **partial_move_line_vals,
            **additional_field,
        }

    def _debit_amounts(self, partial_move_line_vals, amount, amount_converted, force_company_currency=False):
        additional_field = {
            }
        return {
            'debit': amount_converted if amount_converted > 0.0 else 0.0,
            'credit': -amount_converted if amount_converted < 0.0 else 0.0,
            **partial_move_line_vals,
            **additional_field,
        }
    
class ReportSaleDetails(models.AbstractModel):
    _inherit = 'report.point_of_sale.report_saledetails'

    @api.model
    def get_sale_details(self, date_start=False, date_stop=False, config_ids=False, session_ids=False):
        """ Serialise the orders of the requested time period, configs and sessions.

        :param date_start: The dateTime to start, default today 00:00:00.
        :type date_start: str.
        :param date_stop: The dateTime to stop, default date_start + 23:59:59.
        :type date_stop: str.
        :param config_ids: Pos Config id's to include.
        :type config_ids: list of numbers.
        :param session_ids: Pos Config id's to include.
        :type session_ids: list of numbers.

        :returns: dict -- Serialised sales.
        """
        domain = [('state', 'in', ['paid', 'invoiced', 'done'])]

        if (session_ids):
            domain = AND([domain, [('session_id', 'in', session_ids)]])
        else:
            if date_start:
                date_start = fields.Datetime.from_string(date_start)
            else:
                # start by default today 00:00:00
                user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
                today = user_tz.localize(fields.Datetime.from_string(fields.Date.context_today(self)))
                date_start = today.astimezone(pytz.timezone('UTC'))

            if date_stop:
                date_stop = fields.Datetime.from_string(date_stop)
                # avoid a date_stop smaller than date_start
                if (date_stop < date_start):
                    date_stop = date_start + timedelta(days=1, seconds=-1)
            else:
                # stop by default today 23:59:59
                date_stop = date_start + timedelta(days=1, seconds=-1)

            domain = AND([domain,
                          [('date_order', '>=', fields.Datetime.to_string(date_start)),
                           ('date_order', '<=', fields.Datetime.to_string(date_stop))]
                          ])

            if config_ids:
                domain = AND([domain, [('config_id', 'in', config_ids)]])

        orders = self.env['pos.order'].search(domain)

        user_currency = self.env.company.currency_id

        total = 0.0
        products_sold = {}
        taxes = {}
        total_subtotal = 0.0
        for order in orders:
            if user_currency != order.pricelist_id.currency_id:
                total += order.pricelist_id.currency_id._convert(
                    order.amount_total, user_currency, order.company_id, order.date_order or fields.Date.today())
            else:
                total += order.amount_total
            currency = order.session_id.currency_id

            for line in order.lines:
                key = (line.product_id, line.price_unit, line.discount, line.price_subtotal_incl)
                products_sold.setdefault(key, 0.0)
                products_sold[key] += line.qty
                total_subtotal += line.price_subtotal_incl

                if line.tax_ids_after_fiscal_position:
                    line_taxes = line.tax_ids_after_fiscal_position.sudo().compute_all(
                        line.price_unit * (1 - (line.discount or 0.0) / 100.0), currency, line.qty,
                        product=line.product_id, partner=line.order_id.partner_id or False)
                    for tax in line_taxes['taxes']:
                        taxes.setdefault(tax['id'], {'name': tax['name'], 'tax_amount': 0.0, 'base_amount': 0.0})
                        taxes[tax['id']]['tax_amount'] += tax['amount']
                        taxes[tax['id']]['base_amount'] += tax['base']
                else:
                    taxes.setdefault(0, {'name': _('No Taxes'), 'tax_amount': 0.0, 'base_amount': 0.0})
                    taxes[0]['base_amount'] += line.price_subtotal_incl

        payment_ids = self.env["pos.payment"].search([('pos_order_id', 'in', orders.ids)]).ids
        if payment_ids:
            self.env.cr.execute("""
                SELECT method.name, sum(amount) total
                FROM pos_payment AS payment,
                     pos_payment_method AS method
                WHERE payment.payment_method_id = method.id
                    AND payment.id IN %s
                GROUP BY method.name
            """, (tuple(payment_ids),))
            payments = self.env.cr.dictfetchall()
        else:
            payments = []

        return {
            'currency_precision': user_currency.decimal_places,
            'total_paid': user_currency.round(total),
            'total_subtotal': total_subtotal,
            'payments': payments,
            'company_name': self.env.company.name,
            'taxes': list(taxes.values()),
            'products': sorted([{
                'product_id': product.id,
                'product_name': product.name,
                'code': product.default_code,
                'quantity': qty,
                'price_unit': price_unit,
                'discount': discount,
                'price_subtotal_incl': price_subtotal_incl,
                'uom': product.uom_id.name
            } for (product, price_unit, discount, price_subtotal_incl), qty in products_sold.items()],
                key=lambda l: l['product_name'])
        }