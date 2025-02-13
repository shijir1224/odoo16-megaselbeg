from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CreatePaymenRequest(models.TransientModel):
    _name = 'create.payment.request'
    _description = 'Create payment request'

    def check_invoices(self, invoices):
        if len(list(dict.fromkeys(invoices.mapped('move_type')))) != 1 and invoices[0].move_type != 'in_invoice':
            raise UserError('Ижил харилцагчтай нэхэмжлэх байх шаардлагатай ')
        if len(list(dict.fromkeys(invoices.mapped('partner_id')))) != 1:
            raise UserError('Ижил харилцагчтай нэхэмжлэх байх шаардлагатай ')
        if len(list(dict.fromkeys(invoices.mapped('journal_id')))) != 1:
            raise UserError('Ижил журналтай нэхэмжлэх байх шаардлагатай ')
        if len(list(dict.fromkeys(invoices.mapped('currency_id')))) != 1:
            raise UserError('Ижил валюттай нэхэмжлэх байх шаардлагатай ')
        for state in invoices.mapped('payment_state'):
            if state not in ['not_paid', 'partial']:
                raise UserError('Төлөгдөөгүй нэхэмжлэх байх шаардлагатай')
        for state in invoices.mapped('state'):
            if state != 'posted':
                raise UserError('Нэхэмжлэх батлагдсан байх шаардлагатай')

    amount = fields.Float(u'Дүн', compute='compute_amount')
    line_ids = fields.One2many('create.payment.request.line', 'parent_id', string='Lines', readonly=False)

    @api.depends('line_ids.invoice_id')
    def compute_amount(self):
        for obj in self:
            mmamount = sum(obj.line_ids.invoice_id.mapped('amount_residual'))
            obj.amount=abs(mmamount)

    def get_payment_line(self):
        vals = []
        for line in self.line_ids:
            vals.append((0, 0, line.get_payment_request_line_data()))
        return vals

    def full_payment_process(self):
        self.ensure_one()
        if self.line_ids.filtered(lambda line: line.invoice_id.payment_request_id):
            raise UserError(_('Payment request has already been created'))
        partner_id = False
        account_move_ids = []
        name = 'New'
        amount = 0
        partner_check = False
        for l in self.line_ids:
            partner_id = l.invoice_id.partner_id
            if partner_check and partner_check != partner_id.id:
                raise UserError(_('Ижил харилцагчтай гүйлгээ байх ёстой'))
            partner_check = partner_id.id
            account_move_ids.append(l.invoice_id.id)
            # name += self.name
            amount=l.amount
        obj_id = self.env['payment.request'].create({
            'flow_id': self.env['dynamic.flow'].search([('model_id.model', '=', 'payment.request')], order='sequence',
                                                       limit=1).id,
            'amount': amount,
            'name': name,
            'currency_id': self.line_ids[0].currency_id.id,
            'partner_id': partner_id.id,
            'desc_line_ids': self.get_payment_line(),
            'ex_account_id': partner_id.property_account_payable_id.id,
        })
        return obj_id


class CreatePaymenRequestLine(models.TransientModel):
    _name = 'create.payment.request.line'
    _description = 'create payment request line'

    name = fields.Char(u'Нэр')
    ref_name = fields.Char(u'Утга')
    amount = fields.Float(u'Дүн')
    date = fields.Date(u'Огноо', )
    parent_id = fields.Many2one('create.payment.request', string='parent')
    invoice_id = fields.Many2one('account.move', string='Нэхэмжлэх')
    invoice_amount_residual = fields.Monetary(string='Нэхэмжлэхийн боломжит дүн', compute='_compute_amount')
    currency_id = fields.Many2one(related='invoice_id.currency_id')
    partner_id = fields.Many2one('res.partner', string='Харилцагч')

    def check_amount(self):
        for obj in self:
            if obj.invoice_amount_residual < obj.amount:
                raise UserError('Төлбөрийн хүсэлт үүсгэх дүн нэхэмжлэхийн боломжит дүнгээс их байж болохгүй.')

                    
    def _compute_amount(self):
        for move in self.invoice_id:
            if move.payment_request_id:
                self.invoice_amount_residual = self.parent_id.amount
                # self.amount=self.invoice_amount_residual if self.amount == 0 else self.amount
            # elif move.payment_request_ids:
            #     mm_amount=0
            #     pr_id = self.env['payment.request'].search([('id', '=', move.payment_request_ids.ids)])
            #     for pr_ids in pr_id:
            #         # print('==============',pr_ids.amount)
            #         mm_amount += pr_ids.amount
            #         self.invoice_amount_residual = self.parent_id.amount - mm_amount
            #         # self.amount=self.invoice_amount_residual if self.amount == 0 else self.amount
            else:
                self.invoice_amount_residual = self.parent_id.amount
   

    def get_payment_request_line_data(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError('Төлбөр хүсэх дүнгээ оруулна уу.')
        elif self.amount > self.invoice_amount_residual:
            raise UserError('Төлбөр хүсэх дүн их байх боломжгүй.')
        else:
            return {
                'qty': 1,
                'name': self.ref_name,
                'move_id': self.invoice_id.id,
                'price_unit': self.amount,
            }
