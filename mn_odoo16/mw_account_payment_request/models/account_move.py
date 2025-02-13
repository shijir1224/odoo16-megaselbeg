from odoo.exceptions import UserError
from odoo.models import Model
from odoo import fields, _, api


class AccountMove(Model):
    _inherit = 'account.move'

    payment_request_id = fields.Many2one('payment.request', string='Request', ondelete='set null')
    payment_request_line_ids = fields.One2many('payment.request.desc.line', 'move_id', string='Төлбөрийн хүсэлтийн мөр')
    payment_request_ids = fields.Many2many('payment.request', string='Төлбөрийн хүсэлтийн мөрүүд',
                                           compute='compute_request_ids')
    entry_count = fields.Integer(compute='_entry_count', string='Payment Request')
    
    def get_payment_line(self):
        vals = []
        for item in self.invoice_line_ids:
            vals.append((0, 0, item.get_payment_request_line_data()))
        return vals

    def compute_request_ids(self):
        for obj in self:
            obj.payment_request_ids = obj.payment_request_id | obj.payment_request_line_ids.mapped('payment_request_id')

    def create_payment_request(self):
        if self:
            invoices = self
        else:
            active_ids = self._context.get('active_ids') or self._context.get('active_id')
            invoices = self.env['account.move'].browse(active_ids)
        wizard = self.env['create.payment.request'].create({'line_ids': invoices._get_payment_request_line_vals()})
        wizard.check_invoices(invoices)
        action = self.env.ref('mw_account_payment_request.action_create_payment_request_mw').read()[0]
        action['context'] = dict(self._context)
        action['context'].update({'active_ids': self.ids, 'active_model': self._name})
        action['res_id'] = wizard.id
        return action

    @api.depends('payment_request_id')
    def _entry_count(self):
        for move in self:
            move_ids = []
            for move in self:
                for requist_id in move.payment_request_id:
                    if requist_id:
                        move_ids.append(requist_id.id)
                for requist_ids in move.payment_request_ids:
                    if requist_ids:
                        move_ids.append(requist_ids.id)
            res = self.env['payment.request'].search_count([('id', '=', (move_ids))])
            move.entry_count = res or 0

    def _get_payment_request_line_vals(self):
        reconciled_vals = []
        for bsl in self:
            if bsl.payment_reference:
                val = (0, 0, {
                    'ref_name': bsl.payment_reference,
                    'date': bsl.date,
                    'invoice_id': bsl.id,
                    'partner_id': bsl.partner_id.id,
                })
            else:
                val = (0, 0, {
                    'ref_name': bsl.name,
                    'date': bsl.date,
                    'invoice_id': bsl.id,
                    'partner_id': bsl.partner_id.id,
                })
            reconciled_vals.append(val)
        return reconciled_vals

    def action_register_payment(self):
        for obj in self:
            if obj.payment_request_id:
                raise UserError(_('Payment request has been created so payment cannot be directly made from invoice'))
        return super(AccountMove, self).action_register_payment()

    def open_payment_request(self):
        action = self.env.ref('mw_account_payment_request.action_view_payment_request_my_batlah').read()[0]
        action['domain'] = [('id', 'in', self.payment_request_ids.ids)]
        action['context'] = {}
        return action


class AccountMoveLine(Model):
    _inherit = 'account.move.line'

    def get_payment_request_line_data(self):
        self.ensure_one()
        return {
                'qty': self.quantity,
                'name': self.name,
                'move_line_id': self.id,
                'price_unit': self.price_unit,
                'taxes_id': [(6, 0, self.tax_ids.ids)],
            }
