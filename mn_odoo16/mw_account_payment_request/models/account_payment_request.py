# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError,ValidationError
import time
from odoo.addons.mw_base.verbose_format import verbose_format
from odoo.addons.mw_base.verbose_format import verbose_format_china
from odoo.addons.mw_base.verbose_format import num2cn2
import logging
from odoo.addons.mw_base.verbose_format import verbose_format
from datetime import timedelta, date

_logger = logging.getLogger(__name__)


class PaymentRequest(models.Model):
    """ Мөнгө хүссэн өргөдөл
    """

    _name = 'payment.request'
    _description = 'Payment Request'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin','analytic.mixin']


    def _get_mail_thread_data_attachments(self):
        self.ensure_one()
        res = super()._get_mail_thread_data_attachments()
        # thread.check_items
        item_ids = self.check_items
        item_ids = self.env['ir.attachment'].search([('res_id', 'in', item_ids.ids), ('res_model', '=', 'payment.request.item')], order='id desc')
        return res | item_ids



    def get_user_signature_table(self, ids):
        report_id = self.browse(ids)
        print_flow_line_ids = report_id.history_flow_ids.filtered(lambda r: r.flow_line_id.is_print)
        datas = []
        flow_str = ''
        user_str = ''
        image_str = ''
        for item in print_flow_line_ids:
            image_str = '________________________'
            if item.user_id.digital_signature:
                image_buf = item.user_id.digital_signature.decode('utf-8')
                image_str = '<img alt="Embedded Image" width="150" src="data:image/png;base64,%s" />' % image_buf
            user_str = '________________________'
            if item.user_id:
                user_str = item.user_id.name
            flow_str = '________________________'
            if item.flow_line_id:
                flow_str = item.flow_line_id.name
        temp = [u'<p style="text-align: center">' + str(flow_str) + u'</p>',
                u'<p style="text-align: center">' + str(user_str) + u'</p>',
                u'<p style="text-align: center">' + str(image_str) + u'</p>']
        headers = [u'', u'', u'']
        datas.append(temp)
        res = {'header': headers, 'data': datas}

        return res

    def get_user_id_signature(self, ids):
        report_id = self.browse(ids)
        html = '<table>'
        print_flow_line_ids = report_id
        for item in print_flow_line_ids:
            image_str = '________________________'
            if item.user_id.digital_signature:
                image_buf = item.user_id.digital_signature.decode('utf-8')
                image_str = '<img alt="Embedded Image" width="150" src="data:image/png;base64,%s" />' % image_buf
            user_str = '________________________'
            if item.user_id:
                user_str = item.user_id.name
            # flow_str = '________________________'

            html += u'<tr><td><p style="text-align: left; padding-bottom: 20px">Хүсэлт гаргасан:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</p></td><td><p style="text-align: left; padding-bottom: 20px">%s&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</p></td><td><p style="text-align: left; padding-bottom: 20px">%s</p></td></tr>' % (
                user_str, image_str)
        html += '</table>'
        return html

    def get_user_signature_custom(self, ids):
        report_id = self.browse(ids)
        html = '<table>'
        print_flow_line_ids = report_id.history_flow_ids.filtered(lambda r: r.flow_line_id.is_print)
        for item in print_flow_line_ids:
            image_str = '________________________'
            if item.user_id.digital_signature:
                image_buf = item.user_id.digital_signature.decode('utf-8')
                image_str = '<img alt="Embedded Image" width="150" src="data:image/png;base64,%s" />' % image_buf
            user_str = '________________________'
            if item.user_id:
                user_str = item.user_id.name
            flow_str = '________________________'
            if item.flow_line_id:
                flow_str = item.flow_line_id.name

            html += u'<tr><td><p style="text-align: left; padding-bottom: 20px">%s&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</p></td><td><p style="text-align: left; padding-bottom: 20px">%s</p></td><td><p style="text-align: left; padding-bottom: 20px">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;%s</p></td></tr>' % (
                flow_str, user_str, image_str)
        html += '</table>'
        return html

    def get_user_signature(self, ids):
        report_id = self.browse(ids)
        html = '<table>'
        print_flow_line_ids = report_id.history_flow_ids.filtered(lambda r: r.flow_line_id.is_print)
        for item in print_flow_line_ids:
            image_str = '________________________'
            if item.user_id.digital_signature:
                image_buf = item.user_id.digital_signature.decode('utf-8')
                image_str = '<img alt="Embedded Image" width="150" src="data:image/png;base64,%s" />' % image_buf
            user_str = '________________________'
            if item.user_id:
                user_str = item.user_id.name
            html += u'<tr><td><p>%s&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</p></td><td>%s</td></tr>' % (
                user_str, image_str)
        html += '</table>'
        return html

    def _get_total_amount(self, ids):
        # Нийт тоог олох
        obj = self.env['payment.request'].browse(ids)
        tot = 0
        for line in obj.check_items:
            tot += line.subtotal
        return str(tot)

    def _get_department_manager(self):
        """ Хүсэлтэндээрх хэлтэсийн менежер user_id -г тодорхойлно.
        """
        ret = {}
        for req in self:  #
            department_id = req.department_id
            if not department_id:
                continue
            man = department_id.manager_id
            if not man:
                continue
            user = man.user_id
            if not user:
                continue
            ret[req.id] = user.id
        # for id in ids: # TODO: ids гэх хувьсагч алга байна.
        #     ret.setdefault(id, False)
        return ret

    STATE_Selection = [
        ('draft', 'Draft'),
        #                     ('ga_verify','General accountant Verify'),
        ('chief_verify', 'Director Verify'),
        ('ca_verify', 'Cash accountant verify'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ]

    TYPE_Selection = [
        ('cash', u'Бэлнээр'),
        ('bank', u'Банкны шилжүүлгээр'),
        ('pretty', u'Жижиг мөнгөн сангаас'),
        ('credit_card', u'Кредит картаар'),
        ('transfer', u'Хоорондын тооцоо'),
        ('talon', u'Бензин талон'),
    ]

    PRIORITY_Selection = [
        ('0', 'Low'),
        ('3', 'Normal'),
        ('5', 'High'),
    ]

    def _default_currency(self):
        """ Компаний үндсэн валютыг сонгох
        """
        user = self.env.user
        if user.company_id:
            return user.company_id.currency_id.id
        return False

    # def _default_department(self):
    #     return self.env['hr.department'].search([('id', '=', self.env.user.department_id.id)], limit=1)

    # @api.depends('user_id')
    # def _compute_dep_branch(self):
    #     for item in self:
    #         item.branch_id = item.user_id.branch_id.id
    #         item.department_id = item.user_id.department_id.id

    @api.model
    def _get_item_lines(self):
        res = []
        items = ['Гэрээ', 'Гэрээний гүйцэтгэлийн акт', 'Төсөв', 'Нэхэмжлэх', 'И-Баримт', 'Бусад баримт', 'ХА-ын хавсралт']
        for rs in items:
            dct = {
                'name': rs,
                'checked': False,
                'data_ids': False,
            }
            res.append(dct)
        return res

    def _invoice_count(self):
        for act in self:
            act.invoice_count = len(act.desc_line_ids.move_id) or 0
    invoice_count = fields.Integer(compute='_invoice_count', string='Нэхэмжлэх')

    name = fields.Char('Reference', size=64, readonly=True, default='New', tracking=True, copy=False)
    type = fields.Selection(TYPE_Selection, 'Request Type', default='cash', tracking=True)
    user_id = fields.Many2one('res.users', 'Requester', required=True, readonly=True,
                              default=lambda self: self.env.user.id, states={'draft': [('readonly', False)]},
                              tracking=True)
    create_partner_id = fields.Many2one('res.partner', string="Хүсэлт гаргасан", default=lambda self: self.env.user.partner_id.id,required=True, readonly=True,)
    deadline = fields.Date("Deadline", readonly=True, states={'draft': [('readonly', False)]})
    priority = fields.Selection(PRIORITY_Selection, 'Priority', readonly=True, default='3',
                                states={'draft': [('readonly', False)]}, tracking=True)
    narration_id = fields.Many2one('payment.request.narration', 'Narration', readonly=True,
                                   states={'draft': [('readonly', False)]}, tracking=True, )
    payment_ref = fields.Char(string='Гүйлгээний утга')
    currency_id = fields.Many2one('res.currency', 'Currency', required=True, default=_default_currency, readonly=True,
                                  states={'draft': [('readonly', False)]}, tracking=True, )
    tax_ids = fields.Many2many('account.tax', 'payment_request_tax_rel', 'req_id', 'tax_id', 'Included Taxes',
                               readonly=True, states={'draft': [('readonly', False)]})
    create_user_id = fields.Many2one('res.users', 'Create User', required=True, default=lambda self: self.env.user.id)
    partner_id = fields.Many2one('res.partner', 'Partner', tracking=True)
    check_items = fields.One2many('payment.request.item', 'request_id', 'Accompaniments', default=_get_item_lines)
    state = fields.Char(string='Төлөв', compute='_compute_state', store=True, index=True, tracking=True)
    description = fields.Text('Additional description')
    department_id = fields.Many2one('hr.department', 'Department',
                                    tracking=True)
    not_date = fields.Date('Мэдэгдэл ирэх огноо',compute ='_compute_date_to', store=True, index=True)
    # department_manager_id = fields.Many2one("res.users", string="Department Manager", compute='_get_department_manager')
    bank_statement_line_id = fields.Many2one('account.bank.statement.line', 'Payment Ref.', readonly=True)
    # olon uuseh
    bank_statement_line_ids = fields.Many2many('account.bank.statement.line', 'payment_request_bsl_rel', 'item_id',
                                               'line_id', string='Хуулгууд')
    db_attach = fields.Binary('File')
    is_business_trip = fields.Boolean('Is business trip')
    approve_user_id = fields.Many2one('res.users', 'Approver')
    date = fields.Datetime("Creation Date", default=fields.Datetime.now, readonly=True,
                           states={'draft': [('readonly', False)]}, tracking=True, copy=False)
    complete_date = fields.Datetime('Confirmed Date', readonly=True)
    wkf_note_ids = fields.One2many('request.template.wkf.notes', 'request_id', 'Workflow History', readonly=True)
    history_flow_ids = fields.One2many('dynamic.flow.history', 'payment_request_id', 'Урсгалын түүхүүд')
    amount = fields.Float('Amount', required=True, readonly=True, states={'draft': [('readonly', False)]},
                          tracking=True, digits=(16, 2))
    branch_id = fields.Many2one('res.branch', 'Салбар', tracking=True)
    confirmed_amount = fields.Float('Цохсон дүн', tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, tracking=True)
    tulugdsun_dun = fields.Float('Төлөгдсөн дүн', compute='compute_tulugdsun', store=True)
    attachment_ids = fields.Many2many('ir.attachment', compute='compute_attach', compute_sudo=True)
    bank_id = fields.Many2one('res.bank', string='Харилцагчийн банк', tracking=True,)
    bank_partner_id = fields.Many2one('res.partner', string="Банкны харилцагч")
    bank_partner_ids = fields.Char(string="Банкны харилцагч")
    dans_id = fields.Many2one('res.partner.bank', string='Харилцагчийн данс', tracking=True)
    new_dans_id =fields.Char(string='Харилцагчийн данс', tracking=True)
    payment_type = fields.Selection([('dotood','Дотоод гүйлгээ'),('gadaad','Гадаад гүйлгээ')], string='Гүйлгээний төрөл')
    is_yurunhii_nybo = fields.Boolean(string='Ерөнхий нягтлан эсэх', compute='com_is_yurunhii_nybo')
    butsaalt_tailbar = fields.Text(string='Буцаалтын тайлбар', tracking=True, readonly=True)
    uglugiin_uldegdel = fields.Float(string='Өглөгийн үлдэгдэл', compute='com_uglugiin_uldegdel', store=True)
    confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='compute_user_ids',
                                        store=True)
    duusgahgui = fields.Boolean(string='Дуусгахгүй?', default=False)
    journal_id = fields.Many2one('account.journal', 'Журнал', tracking=True)
    ex_account_id = fields.Many2one('account.account', 'Зардлын данс', tracking=True)
    cash_type_id = fields.Many2one('account.cash.move.type', 'МГ төрөл', tracking=True)
    desc_line_ids = fields.One2many('payment.request.desc.line', 'payment_request_id', string='Тайлбарын мөр')
    amount_tax_pay = fields.Monetary(string='Нийт татвар', store=True, readonly=True, compute='_amount_all')
    amount_total_pay = fields.Monetary(string='Нийт дүн', store=True, readonly=True, compute='_amount_all', tracking=4)
    move_id = fields.Many2one('account.move', string='Related invoice', ondelete='cascade')
    account_move_ids = fields.Many2many('account.move','account_move_payment_req_rel','req_id','move_id','Payments',copy=False)    
    paid_date = fields.Date(string="Төлөх эцсийн огноо", store=True, copy=False)
    current_rate = fields.Float(string=u"Ханш", store=True)
    date_currency = fields.Date('Ханш бодох огноо', default=fields.Date.context_today)
    gadaad_currency = fields.Boolean(string=u"Валют гадаад эсэх", compute='_com_gadaad_currency')
    currency_company_id = fields.Many2one('res.currency', string=u"Валют Компани", related='company_id.currency_id', readonly=True)
    amount_str_mw = fields.Char(string="Amount str", compute="get_amount_str")
    warning_messages = fields.Html('Анхааруулга', compute='_compute_wc_messages')
    warning_messages_amount = fields.Html('Анхааруулга', compute='_compute_wc_messages_amount')
    expense_account_is = fields.Boolean (string='Зардлын данс эсэх', default=False, compute='_compute_expense_account_id')

    def copy(self, default=None):
        # TDE FIXME: should probably be copy_data
        self.ensure_one()
        if default is None:
            default = {}
        # if 'bank_statement_line_id' in default:
        default['bank_statement_line_id'] = False
        default['amount'] = 0
        return super(PaymentRequest, self).copy(default=default)


    def open_invoices(self):
        ids = []
        for line in self.desc_line_ids:
            if line.move_id:
                ids.append(line.move_id.id)
        return {
            'name': _('Нэхэмжлэхүүд'),
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', ids)],
        }

    @api.depends('ex_account_id')
    def _compute_expense_account_id(self):
        for item in self:
            if item.ex_account_id and item.ex_account_id.account_type =='expense':
                item.expense_account_is=True
            else:
                item.expense_account_is=False
    @api.depends('currency_id','currency_company_id')
    def _com_gadaad_currency(self):
        for item in self:
            if item.currency_id!=item.currency_company_id:
                item.gadaad_currency = True
            else:
                item.gadaad_currency = False
    # @api.constrains('payment_ref')
    # def _check_valid_payment_ref(self):
    #     for record in self:
    #         if ',' in record.payment_ref or '.' in record.payment_ref:
    #             raise ValidationError("Гүйлгээний утга дээр дараах тэмдэгтүүд ашиглах боломжгүй. ',' or '.'")    
    @api.onchange('currency_id','date_currency','state','company_id')
    def ochange_compute_curent_rate(self):
        for item in self:
            date_order = item.date_currency or fields.Datetime.now()
            if item.currency_id and item.company_id:
                rr = self.env['res.currency']._get_conversion_rate(item.currency_id, item.company_id.currency_id, item.company_id, date_order)
                item.current_rate = rr
            else:
                item.current_rate = 0

    @api.onchange('create_partner_id','create_uid')
    def compute_department(self):
        for payment in self:
            if payment.create_partner_id:
                emp = self.env['hr.employee'].search(
                [('partner_id', '=', payment.create_partner_id.id)], limit=1)
                if not payment.department_id:
                    payment.department_id = emp.department_id.id
                if not payment.branch_id:
                    payment.branch_id = emp.department_id.branch_id.id
    @api.depends('desc_line_ids.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.desc_line_ids:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax

            order.update({
                'amount_tax_pay': amount_tax,
                'amount_total_pay': amount_untaxed + amount_tax,
            })

    @api.onchange('desc_line_ids')
    def onch_amount_total(self):
        self.amount = self.amount_total_pay

    def get_move_product_line(self, ids):
        datas = []
        report_id = self.browse(ids)

        i = 1
        lines = report_id.desc_line_ids

        sum1 = 0
        sum2 = 0
        nbr = 1
        for line in lines:
            qty = line.qty
            price_unit = line.price_unit
            price_subtotal = line.price_total
            name = line.name
            temp = [
                u'<p style="text-align: center;">' + str(nbr) + u'</p>',
                u'<p style="text-align: left;">' + name + u'</p>',
                "{0:,.0f}".format(qty) or '',
                "{0:,.0f}".format(price_unit) or '',
                "{0:,.0f}".format(price_subtotal) or '',
            ]
            nbr += 1

            sum1 += qty
            sum2 += price_subtotal

            nbr += 1
            datas.append(temp)
            i += 1
        temp = [
            u'',
            u'<p style="text-align: center;">Нийт дүн</p>',
            u'',
            "{0:,.2f}".format(sum1) or '',
            "{0:,.2f}".format(sum2) or '',
        ]
        datas.append(temp)
        return datas

    def get_desc_line(self, ids):
        headers = [
            u'№',
            u'Тайлбар',
            u'Тоо хэмжээ',
            u'Нэгж үнэ',
            u'Нийт үнэ',
        ]
        datas = self.get_move_product_line(ids)
        if not datas:
            return ''
        res = {'header': headers, 'data': datas}
        return res

    @api.onchange('type')
    def _onchange_type(self):
        ttype = 'bank'
        for obj in self:
            if obj.type and obj.type == 'bank':
                ttype = 'bank'
            else:
                ttype = 'cash'
        return {
            'domain': {
                'journal_id': [('type', '=', ttype)]
            }
        }

    @api.depends('partner_id', 'create_partner_id')
    def _compute_wc_messages(self):
        for item in self:
            message = []
            if item.partner_id and item.company_id:
                sql_query = """
                    SELECT pr.name,pr.partner_id,pr.amount,pr.create_partner_id,pr.date,pr.stage_id,pr.id
                    FROM payment_request pr
                    left join res_partner rp on (rp.id=pr.partner_id)
                    left join res_company rc on (pr.company_id=rc.id)
                    WHERE pr.partner_id = %s and pr.company_id=%s and pr.date <'%s'
                    """ % (item.partner_id.id, item.company_id.id,item.date)
                self.env.cr.execute(sql_query)
                query_result = self.env.cr.dictfetchall()

                for qr in query_result:
                    val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><b>%s</b></td></tr>""" % (
                        qr['name'], qr['date'],
                        self.env['res.partner'].browse(qr['partner_id']).name, qr['amount'],self.env['res.partner'].browse(qr['create_partner_id']).name,self.env['dynamic.flow.line.stage'].browse(qr['stage_id']).name)
                    message.append(val)
            if not message:
                message = False
            else:
                message = u'<table style="width: 100%;"><tr><td colspan="2" style="text-align: center;">ӨМНӨ ТӨЛБӨРҮҮД</td></tr><tr style="width: 20%;"><td>Нэр</td><td style="width: 15%;">Огноо</td><td style="width: 15%;">Харилцагч</td><td style="width: 15%;">Дүн</td><td style="width: 15%;">Хариуцагч</td><td style="width: 15%;">Төлөв</td></tr>' + u''.join(
                    message) + u'</table>'
            item.warning_messages = message
    # @api.depends('partner_id', 'create_partner_id', 'amount')
    # def _compute_wc_messages_amount(self):
    #     for item in self:
    #         message = []
    #         if item.partner_id and item.company_id:
    #             sql_query = """
    #                 SELECT pr.name,pr.partner_id,pr.amount,pr.create_partner_id,pr.date,pr.stage_id,pr.id
    #                 FROM payment_request pr
    #                 left join res_partner rp on (rp.id=pr.partner_id)
    #                 left join res_company rc on (pr.company_id=rc.id)
    #                 WHERE pr.partner_id = %s and pr.company_id=%s and pr.date <'%s' and pr.amount = '%s'
    #                 """ % (item.partner_id.id, item.company_id.id,item.date,item.amount)
    #             self.env.cr.execute(sql_query)
    #             query_result = self.env.cr.dictfetchall()

    #             for qr in query_result:
    #                 val = u"""<tr><td><b>%s</b></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td><b>%s</b></td></tr>""" % (
    #                     qr['name'], qr['date'],
    #                     self.env['res.partner'].browse(qr['partner_id']).name, qr['amount'],self.env['res.partner'].browse(qr['create_partner_id']).name,self.env['dynamic.flow.line.stage'].browse(qr['stage_id']).name)
    #                 message.append(val)
    #         if not message:
    #             message = False
    #         else:
    #             message = u'<table style="width: 100%;"><tr><td colspan="2" style="text-align: center;">ИЖИЛ ДҮНТЭЙ ТӨЛБӨР БАЙНА!!!</td></tr><tr style="width: 20%;"><td>Нэр</td><td style="width: 15%;">Огноо</td><td style="width: 15%;">Харилцагч</td><td style="width: 15%;">Дүн</td><td style="width: 15%;">Хариуцагч</td><td style="width: 15%;">Төлөв</td></tr>' + u''.join(
    #                 message) + u'</table>'
    #         item.warning_messages_amount = message


    @api.depends('partner_id', 'create_partner_id', 'amount')
    def _compute_wc_messages_amount(self):
        for item in self:
            message = []
            if item.partner_id and item.company_id:
                sql_query = """
                    SELECT pr.name,pr.partner_id,pr.amount,pr.create_partner_id,pr.date,pr.stage_id,pr.id
                    FROM payment_request pr
                    left join res_partner rp on (rp.id=pr.partner_id)
                    left join res_company rc on (pr.company_id=rc.id)
                    WHERE pr.partner_id = %s and pr.company_id=%s and pr.date <'%s' and pr.amount = '%s'
                    """ % (item.partner_id.id, item.company_id.id,item.date,item.amount)
                self.env.cr.execute(sql_query)
                query_result = self.env.cr.dictfetchall()

                for qr in query_result:
                    val = """
                            <tr style="border: 2px solid red; background-color: yellow;">
                                <td>
                                    <b>%s</b>
                                </td>
                                <td>%s</td>
                                <td>%s</td>
                                <td>%s</td>
                                <td>%s</td>
                                <td><b>%s</b>
                                </td>
                            </tr>""" % (
                        qr['name'], qr['date'],
                        self.env['res.partner'].browse(qr['partner_id']).name, qr['amount'],self.env['res.partner'].browse(qr['create_partner_id']).name,self.env['dynamic.flow.line.stage'].browse(qr['stage_id']).name)
                    message.append(val)
            if not message:
                message = False
            else:
                message = """
                    <table style="width: 100%; border-color: #96D4D4;">
                        <tr style="border: 2px solid red; background-color: yellow;">
                            <td colspan="6" style="text-align: center; color:red;"><H1 style="text-align: center; color:red;">ЭНЭ ГҮЙЛГЭЭ ДАВХАЦСАН БАЙХ МАГАДЛАЛТАЙ ТУЛ, <br/>ХЯНАНА УУ!!!</H1></td>
                        </tr>
                        <tr style="width: 20%; border: 2px solid red; background-color: yellow;">
                            <td>Нэр</td>
                            <td style="width: 15%;">Огноо</td>
                            <td style="width: 15%;">Харилцагч</td>
                            <td style="width: 15%;">Дүн</td>
                            <td style="width: 15%;">Хариуцагч</td>
                            <td style="width: 15%;">Төлөв</td>
                        </tr>
                        """ + u''.join(message) + """
                    </table>
                """

            item.warning_messages_amount = message


    @api.depends('bank_statement_line_id')
    def compute_tulugdsun(self):
        for item in self:
            if item.bank_statement_line_id:
                item.tulugdsun_dun = item.bank_statement_line_id.amount*(-1)
            else:
                item.tulugdsun_dun = 0
    @api.depends('amount')
    def get_amount_str(self):
        for report_id in self:
            if report_id.amount > 0:
                report_id.amount_str_mw = verbose_format(abs(report_id.amount))
            else:
                report_id.amount_str_mw = False
    def change_history(self):
        obj_min = 5000
        obj = self.env['dynamic.flow.history']
        objs = self.env['request.template.wkf.notes'].search([
            ('create_ok', '=', False),
        ], limit=obj_min)
        i = len(objs)
        for item in objs:
            vals = {
                'user_id': item.user_id.id,
                'date': item.date,
                'flow_line_id': item.flow_line_id.id,
                'payment_request_id': item.request_id.id,
                'company_id': item.request_id.company_id.id,
            }
            obj_id = obj.create(vals)
            item.create_ok = True
            obj.compute_spend_time('payment_request_id', item.request_id)

            obj_id.create_date = item.create_date
            obj_id.create_uid = item.create_uid.id

            _logger.info('Payment request flow history shiljuuleh %s of %s' % (i, obj_min))
            i -= 1
    def action_date_noti_send(self, partner_id):
        # subject = 'Төлбөрийн хүсэлтийн сануулга'
        # html = u'<b><i style="color:red">Төлбөрийн хүсэлтийн сануулга</i></b><br/>'
        # html += u"""<b></b> - Төлбөрийн хүсэлтийн <b>"%s"</b> дугаартай баримтын төлөх хугацаа дуусахад 3 хоног үлдлээ. Төлөх эцсийн огноо <b>%s</b>!"""% (self.name,self.paid_date)
        # mail_obj = self.env['mail.mail'].sudo().create({
        #     'email_from': self.env.user.email_formatted,
        #     'email_to': partner_id.email,
        #     'subject': subject,
        #     'body_html': '%s' % html,
        #     # 'attachment_ids': attachment_ids
        # })
        # mail_obj.send()
        return
    @api.depends('paid_date')
    def _compute_date_to(self):
        day = timedelta(3)
        for item in self:
            if item.paid_date:
                item.not_date = item.paid_date - day

    def update_payment_info(self):
        today = date.today()
        payment_obj = self.env['payment.request'].search([('state','!=','done'),('not_date', '=', today)])
        for payment in payment_obj:
            payment.action_date_noti_send(partner_id = payment.create_partner_id)
    def all_compute_user_ids(self):
        for item in self.sudo().search([]):
            item.sudo().compute_user_ids()

    @api.depends('flow_line_id', 'flow_id.line_ids')
    def compute_user_ids(self):
        for item in self:
            user_id = item.user_id or item.create_uid
            ooo = item.flow_line_next_id._get_flow_users(item.branch_id, user_id.department_id, user_id)
            temp_users = ooo.ids if ooo else []
            item.confirm_user_ids = [(6, 0, temp_users)]

    @api.onchange('amount')
    def onch_amount(self):
        self.confirmed_amount = self.amount

    @api.depends('partner_id')
    def com_uglugiin_uldegdel(self):
        aml_obj = self.env['account.move.line']
        for item in self:
            if item.partner_id:
                amls = aml_obj.search(
                    [('partner_id', '=', item.partner_id.id), ('account_id.account_type', '=', 'liability_payable'),
                     ('move_id.state', '=', 'posted')])
                item.uglugiin_uldegdel = sum(amls.mapped('credit')) - sum(amls.mapped('debit'))
            else:
                item.uglugiin_uldegdel = 0

    def input_hariltsagchiin_uld(self):
        if self.partner_id:
            self.amount = self.uglugiin_uldegdel

    @api.onchange('bank_id', 'partner_id')
    def onch_bank_id(self):
        if self.partner_id and self.bank_id:
            obj_id = self.env['res.partner.bank'].search(
                [("bank_id", "=", self.bank_id.id), ("partner_id", "=", self.partner_id.id)])
            len1 = len(obj_id)
            if len1 == 1:
                self.dans_id = obj_id.id
        else:
            self.dans_id = False

    @api.onchange('narration_id')
    def onch_narration_id(self):
        if self.narration_id and self.narration_id.flow_hamaarah_id:
            self.flow_id = self.narration_id.flow_hamaarah_id.id

    def com_is_yurunhii_nybo(self):
        for item in self:
            if self.env.user.has_group("mw_account_payment_request.res_groups_account_general_accountant"):
                item.is_yurunhii_nybo = True
            else:
                item.is_yurunhii_nybo = False

    def name_get(self):
        res = []
        for partner in self:
            res_name = super(PaymentRequest, partner).name_get()
            if partner.narration_id:
                res_name = u'' + res_name[0][1] + u' (' + partner.narration_id.display_name + ')'
                res.append((partner.id, res_name))
            else:
                res.append(res_name[0])
        return res

    def get_tuple(self, obj):
        if len(obj) > 1:
            return str(tuple(obj))
        elif obj:
            return " (" + str(obj) + ") "
        else:
            return " "

    @api.depends('check_items')
    def compute_attach(self):
        for item in self:
            if item.sudo().mapped('check_items.data_ids'):
                item.sudo().attachment_ids = item.sudo().mapped('check_items.data_ids').ids
            else:
                item.attachment_ids = False

    def accountant_set(self, form):
        total = 0
        if self.assigned_ids:
            self.assigned_ids.unlink()
        for l in form.line_ids:
            if l.amount > 0:
                total += l.amount
                if not l.user_id:
                    raise UserError(u'Нягтлан сонгоогүй мөр байна.')
        if self.amount < total:
            is_more = True
        self.confirmed_amount = total
        # confirmed_more = is_more # TODO: Ашиглагдаагүй хувьсагч

    def get_bank_statement_line(self, request, amount, form):
        mnt = self.env['res.currency'].search([('name','=','MNT')], limit=1)
        if self.currency_id==mnt:
            vals = {
                'payment_ref': form.payment_ref if not form.payment_ref else request.payment_ref,
				'date':  form.date and form.date or time.strftime('%Y-%m-%d'),
                # 'date': request.date_currency or request.date_currency.strftime('%Y-%m-%d'),
                'amount': amount ,
                'partner_id': request.partner_id.id,
                'account_id': form.account_id.id or request.ex_account_id and request.ex_account_id.id,
                'journal_id': form.journal_id.id,
                'ref': str(request.display_name)+ " / " + str(request.description),
                'foreign_currency_id': self.currency_id.id,
                # 'amount_currency': self.currency_id.id,
                # 'note': '%s :\n %s' % (request.narration_id.name, request.narration_id.description or ''),
                'analytic_distribution': request.analytic_distribution  or False,
                # 'bank_account_id': request.dans_id and request.dans_id.id or False,
                'cash_type_id': (request.cash_type_id and request.cash_type_id.id) or (form.cash_type_id and form.cash_type_id.id) or False
            }
        else:
            vals = {
                'payment_ref': form.payment_ref if not form.payment_ref else request.payment_ref,
				'date':  form.date and form.date or time.strftime('%Y-%m-%d'),
                # 'date': request.date_currency or request.date_currency.strftime('%Y-%m-%d'),
                'amount': -(amount),
                'partner_id': request.partner_id.id,
                'account_id': form.account_id.id or request.ex_account_id and request.ex_account_id.id,
                'analytic_distribution': request.analytic_distribution  or False,
                'journal_id': form.journal_id.id,
                'ref': str(request.display_name)+ " / " + str(request.description),
                'foreign_currency_id': self.currency_id.id,
                'cash_type_id': (request.cash_type_id and request.cash_type_id.id) or (form.cash_type_id and form.cash_type_id.id) or False
            }

        return vals

    def create_payment(self, form):
        """ Төлбөрийн хүсэлтийн дугаа бэлэн мөнгөний зарлагын баримт,
            эсвэл төлбөрийн даалгавар үүсгэнэ.
        """
        statement_line_obj = self.env['account.bank.statement.line']
        cur_obj = self.env['res.currency']
        res = []
        ref =''
        for request in self:
            if request.state not in ['accountant', 'pay']:
                raise UserError(u'{} гүйлгээ хийх төлөвгүй байна!!!'.format(request.name))
            if self._context.get('multi',False):
                amount = request.confirmed_amount or request.amount
            else:
                amount = form.amount or request.confirmed_amount or request.amount
            # fact = ''
            if request.currency_id and form.journal_id and form.journal_id.currency_id and request.currency_id.id != form.journal_id.currency_id.id:
                amount = request.currency_id.compute(amount, form.journal_id.currency_id,  )
            # if request.check_items:
                # fact = u'%s :\n   ' % (request.check_items[0].name or '') # TODO: fact хувьсагч ашиглагдаагүй
            amount = -1 * amount
            # if request.amount and request.currency_id.id !='108':
            #     amount = request.amount * request.currency_id.rate *(-1) 
            new_line_id = statement_line_obj.create(request.get_bank_statement_line(request, amount, form))
            # new_line_id.onchange_account_id()
            res.append(new_line_id)
            # statement = new_line_id.statement_id
            # st_no = statement.name
            # if request.type == 'cash':
            #     p_type_str = _('Cash Statement')
            #     appr = u'%s : %s' % (_('Cash Accountant'), statement.user_id.name)
            # else:
            #     p_type_str = _('Bank Statement')
            #     appr = _('Bank Accountant') # TODO: appr, p_type_str, st_no хувьсагч ашиглагдаагүй
            request.write({'bank_statement_line_id': new_line_id.id}, )
            if self.ex_account_id:
                new_line_id.button_validate_line()
                statement_line_move_id = new_line_id.move_id
                if request.move_id:
                    move_line_ids = statement_line_move_id.line_ids | request.move_id.line_ids
                    move_line_ids = move_line_ids.filtered(lambda l: l.account_id.id == request.ex_account_id.id)
                    move_line_ids.reconcile()
                if request.desc_line_ids:
                    move_line_ids = statement_line_move_id.line_ids | request.desc_line_ids.filtered(lambda l: l.move_id is not False).mapped('move_id.line_ids')
                    move_line_ids = move_line_ids.filtered(lambda l: l.account_id.id == request.ex_account_id.id)
                    if request.ex_account_id.reconcile==True:
                        move_line_ids.reconcile()

            request.bank_statement_line_ids = request.bank_statement_line_ids.ids + [new_line_id.id]
            if request.duusgahgui and abs(request.confirmed_amount) > abs(request.tulugdsun_dun):
                continue
            else:
                request.write({'state': 'done'}, )

        return res

    def print_bank_order(self):
        self.ensure_one()
        if self.bank_statement_line_id:
            return self.bank_statement_line_id.print_bank_order()
        else:
            raise UserError(u'Төлбөр хийгдсэний дараа ТД хэвлэнэ')

    def unlink(self):
        """ Төлбөрийн хүсэлтийг устгах
        """
        for request in self:
            if request.state != 'draft':
                raise UserError('Ноорог төлөвтэй баримтыг устганэ %s ' % request.display_name)
        return super(PaymentRequest, self).unlink()

    def action_cancel(self):
        if self.bank_statement_line_id:
            raise UserError(u'Кассын бичилт хийгдсэн байна цуцлах боломжгүй %s' % (self.display_name))
        if self.flow_id:
            for w in self.flow_id.line_ids:
                if w.state_type == 'cancel':
                    self.flow_line_id = w.id

        self.write({'state': 'cancel'})

    def flow_domain(self):
        domain = {'flow_id': False}
        search_domain = [('model_id.model', '=', 'payment.request'), ('company_id', '=', self.env.user.company_id.id)]
        _logger.info(u'search_domain=====2: %s ' % search_domain)
        return search_domain

    # ------------flow -------
    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code(
                'account.payment.request') or '/'
        res = super(PaymentRequest, self).create(vals)
        for item in res:
            if item.flow_id:
                search_domain = [('flow_id', '=', item.flow_id.id)]
                re_flow = self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
                item.flow_line_id = re_flow
        return res

    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = [('model_id.model', '=', 'payment.request'), ('company_id', '=', self.env.company.id)]
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids',
                                             string='Харагдах төлөв')
    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id,
                                   copy=False)
    flow_id = fields.Many2one('dynamic.flow', string='Урсгал тохиргоо', tracking=True,
                              default=_get_default_flow_id,
                              copy=True, required=True, domain="[('model_id.model', '=', 'payment.request')]")
    flow_line_next_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True) 
    flow_line_back_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
    is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
                               string='Төлөв stage', store=True)
    accountant_id = fields.Many2one('res.users', string='Нягтлан', tracking=True, index=True, copy=False)

    @api.depends('flow_id')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                item.visible_flow_line_ids = self.env['dynamic.flow.line'].search(
                    [('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'payment.request')])
            else:
                item.visible_flow_line_ids = []

    @api.depends('flow_line_id.stage_id')
    def _compute_flow_line_id_stage_id(self):
        for item in self:
            item.stage_id = item.flow_line_id.stage_id

    # ------------------------------flow------------------
    @api.depends('flow_line_id')
    def _compute_state(self):
        for item in self:
            item.state = item.flow_line_id.state_type

    def flow_find(self, domain=[], order='sequence'):
        search_domain = []
        if self.flow_id:
            search_domain.append(('flow_id', '=', self.flow_id.id))

        search_domain.append(('flow_id.model_id.model', '=', 'payment.request'))
        return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find()
        else:
            self.flow_line_id = False

    @api.depends('flow_id', 'visible_flow_line_ids', 'flow_line_id')
    def _compute_flow_line_id(self):
        for item in self:
            item.flow_line_next_id = item._get_next_flow_line(item.visible_flow_line_ids)
            item.flow_line_back_id = item._get_back_flow_line(item.visible_flow_line_ids)

    def _get_next_flow_line(self, flow_line_ids=False):
        if self.id:
            if flow_line_ids:
                next_flow_line_id = self.env['dynamic.flow.line'].search([
                    ('flow_id', '=', self.flow_id.id),
                    ('id', '!=', self.flow_line_id.id),
                    ('sequence', '>', self.flow_line_id.sequence),
                    ('sequence', 'in', flow_line_ids.mapped('sequence')),
                    ('state_type', 'not in', ['cancel']),
                ], limit=1, order='sequence')
                return next_flow_line_id
            else:
                next_flow_line_id = self.env['dynamic.flow.line'].search([
                    ('flow_id', '=', self.flow_id.id),
                    ('id', '!=', self.flow_line_id.id),
                    ('sequence', '>', self.flow_line_id.sequence),
                    ('state_type', 'not in', ['cancel']),
                ], limit=1, order='sequence')
                return next_flow_line_id
        else:
            return False

    def _get_back_flow_line(self, flow_line_ids=False):
        if self.id:
            if flow_line_ids:
                back_flow_line_id = self.env['dynamic.flow.line'].search([
                    ('flow_id', '=', self.flow_id.id),
                    ('id', '!=', self.flow_line_id.id),
                    ('sequence', '<', self.flow_line_id.sequence),
                    ('sequence', 'in', flow_line_ids.mapped('sequence')),
                    ('state_type', 'not in', ['cancel']),
                ], limit=1, order='sequence desc')
                return back_flow_line_id
            else:
                back_flow_line_id = self.env['dynamic.flow.line'].search([
                    ('flow_id', '=', self.flow_id.id),
                    ('id', '!=', self.flow_line_id.id),
                    ('sequence', '<', self.flow_line_id.sequence),
                    ('state_type', 'not in', ['cancel']),
                ], limit=1, order="sequence desc")
            return back_flow_line_id
        return False

    def action_next_stage(self):
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if next_flow_line_id:
            if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
                check_next_flow_line_id = next_flow_line_id
                while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:

                    temp_stage = check_next_flow_line_id._get_next_flow_line()
                    if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
                        break
                    check_next_flow_line_id = temp_stage
                next_flow_line_id = check_next_flow_line_id

            if next_flow_line_id._get_check_ok_flow(self.branch_id, False):
                self.flow_line_id = next_flow_line_id
                if self.flow_line_id.state_type == 'done':
                    self.action_done()

                self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'payment_request_id', self)
                if self.flow_line_next_id:
                    self.env.user
                    send_users = self.flow_line_next_id._get_flow_users(self.branch_id, False, self.env.user)
                    if send_users:
                        self.send_chat_employee(send_users.mapped('partner_id'))
            else:
                self.env.user
                con_user = next_flow_line_id._get_flow_users(self.branch_id, False, self.env.user)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(con_user.mapped('display_name'))
                raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)



    def all_next_stage(self):
        for item in self:
            item.action_next_stage()

    def action_back_stage(self):
        if not self.env.context.get('force_back', False):
            obj_id = self.env['payment.request.butsaalt.tailbar'].create({
                'request_id': self.id,
            })
            return {
                'name': _('Буцаалтын тайлбар'),
                'view_mode': 'form',
                'res_model': 'payment.request.butsaalt.tailbar',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': obj_id.id,
                'context': self.env.context,
            }
        back_flow_line_id = self.flow_line_id._get_back_flow_line()
        if back_flow_line_id:
            if self.visible_flow_line_ids and back_flow_line_id.id not in self.visible_flow_line_ids.ids:
                check_next_flow_line_id = back_flow_line_id
                while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:

                    temp_stage = check_next_flow_line_id._get_back_flow_line()
                    if temp_stage.id == check_next_flow_line_id.id or not temp_stage:
                        break
                    check_next_flow_line_id = temp_stage
                back_flow_line_id = check_next_flow_line_id

            # if back_flow_line_id._get_check_ok_flow(self.branch_id, False):
            if back_flow_line_id:
                self.flow_line_id = back_flow_line_id
                self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'payment_request_id', self)
            # else:
            #     raise UserError(_('You are not back user'))

    def action_cancel_stage(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow(self.branch_id, False):
            return self.action_cancel()
        else:
            raise UserError(_('You are not cancel user'))

    def set_stage_cancel(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow(self.branch_id, False):
            self.flow_line_id = flow_line_id
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'payment_request_id', self)
        else:
            raise UserError(_('You are not cancel user'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state = 'draft'
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'payment_request_id', self)
        else:
            raise UserError(_('You are not draft user'))

    def action_done(self):
        pass
#         context = dict(self.env.context or {})
#         data_obj = self.env['ir.model.data']
#         view = data_obj.xmlid_to_res_id('mw_account_payment_request.view_account_payment_expense_form')
#         line = self.browse()
#         context = dict(self._context)
#         vals = {'company_id': self.env.user.company_id.id,
#                 'account_id': 1,
#                 'type': 'supplier',
#                 }
        # TODO: Ерөөсөө юу ч ашиглагдаагүй байна

    def send_chat_employee(self, partner_ids):
        state = self.flow_line_id.name
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_id = self.env.ref('mw_account_payment_request.action_view_payment_request_my').id
        html = u'<b>Мөнгө хүсэх өргөдөл</b><br/><i style="color: red">%s</i> Ажилтаны үүсгэсэн </br>' % (
            self.create_partner_id.name)
        html += u"""<b><a target="_blank"  href=%s/web#action=%s&id=%s&cids=%s&view_type=form&model=purchase.request>%s</a></b>, дугаартай Мөнгө хүсэх өргөдөл <b>%s</b> төлөвт орлоо. Та хянаж батална уу.""" % (
            base_url, action_id, self.id, self.company_id.id, self.display_name, state)
        attachment_ids = []
        if self.check_items:
            attachment_ids = self.sudo().mapped('check_items.data_ids').ids
        self.flow_line_id.send_chat(html, partner_ids)
        # self.flow_line_id.send_chat(html, partner_ids, obj_id=self, attachment_ids=attachment_ids)

    # ------------------------------flow------------------
    def update_attach(self):
        objs = self.env['payment.request.item'].sudo().search([('data', '!=', False)])
        len_obj = len(objs)
        i = len_obj
        for item in objs:
            query = "select array_agg(id) from ir_attachment where res_model='payment.request.item' and res_id = {0}".format(
                item.id)
            self.env.cr.execute(query)
            result_ids = self.env.cr.fetchone()
            ff_id = []
            if result_ids and result_ids[0]:
                ff_id = result_ids[0]
            attachment_ids = ff_id
            item.data_ids = attachment_ids
            item.data_ids.name = item.file_fname
            item.data_ids.res_field = False
            _logger.info(' DATA ATTACH payment.request.item %s of %s ' % (i, len_obj))
            i -= 1

    def request_print(self):
        model_id = self.env['ir.model'].sudo().search([('model','=','payment.request')], limit=1)
        template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id)], limit=1)
        if template:
            res = template.sudo().print_template(self.id)
            return res
        else:
            raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))

    def amount_str(self, ids):
        line = self.browse(ids)
        amountr_str = verbose_format(abs(line.amount))
        return amountr_str

    def amount_str_china(self, ids):
        line = self.browse(ids)
        amountr_str = verbose_format_china(abs(line.amount))
        return amountr_str

    def amount_str_china2(self, ids):
        line = self.browse(ids)
        amountr_str, mungu = num2cn2(abs(line.amount))
        if mungu:
            amountr_str = amountr_str + '.点' + mungu
        return amountr_str

    def dep_dire(self, ids):
        line = self.browse(ids)
        name = u'шаардлагагүй'
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'dep_directors':
                name = l.user_id.name
        return name

    def fin_man(self, ids):
        line = self.browse(ids)
        name = u'шаардлагагүй'
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'fin_manager':
                name = l.user_id.name
        return name

    def fin_dir(self, ids):
        line = self.browse(ids)
        name = u'шаардлагагүй'
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'fin_director':
                name = l.user_id.name
        return name

    def pre_ceo(self, ids):
        line = self.browse(ids)
        name = u'шаардлагагүй'
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'president_ceo':
                name = l.user_id.name
        return name

    def prt_ceo(self, ids):
        line = self.browse(ids)
        name = u'шаардлагагүй'
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'ceo':
                name = l.user_id.name
        return name

    def prt_cont(self, ids):
        line = self.browse(ids)
        name = ''
        for l in line.check_items:
            if l.name and l.name == 'Гэрээ' and l.checked:
                name = u'  Хавсаргав'
                break
            else:
                name = u'.................................'
        return name

    def prt_cont_akt(self, ids):
        line = self.browse(ids)
        name = ''
        for l in line.check_items:
            if l.name and l.name == 'Гэрээний гүйцэтгэлийн акт' and l.checked:
                name = u'  Хавсаргав'
                break
            else:
                name = u'.................................'
        return name

    def prt_budget(self, ids):
        line = self.browse(ids)
        name = ''
        for l in line.check_items:
            if l.name and l.name == 'Төсөв' and l.checked:
                name = u'  Хавсаргав'
                break
            else:
                name = u'.................................'
        return name

    def prt_inv(self, ids):
        line = self.browse(ids)
        name = ''
        for l in line.check_items:
            if l.name and l.name == 'Нэхэмжлэх' and l.checked:
                name = u'  Хавсаргав'
                break
            else:
                name = u'.................................'
        return name

    def prt_ebr(self, ids):
        line = self.browse(ids)
        name = ''
        for l in line.check_items:
            if l.name and l.name == 'И-баримт' and l.checked:
                name = u'  Хавсаргав'
                break
            else:
                name = u'.................................'
        return name

    def prt_other(self, ids):
        line = self.browse(ids)
        name = ''
        for l in line.check_items:
            if l.name and l.name == 'Бусад баримт' and l.checked:
                name = u'  Хавсаргав'
                break
            else:
                name = u'.................................'
        return name

    def get_budget(self, ids):
        line = self.browse(ids)
        name = ''
        for l in line:
            if l.budget_id and l.budget_id.code:
                name = l.budget_id.code
                break
            else:
                name = u'Төсвийн код шаардлагагүй'
        return name

    def general_account(self, ids):
        line = self.browse(ids)
        name = ''
        for a in line:
            for l in a.assigned_ids:
                if l.type:
                    name = l.create_uid.name
        return name

    def general_date(self, ids):
        line = self.browse(ids)
        name = ''
        for a in line:
            for l in a.assigned_ids:
                if l.type:
                    name = l.create_date.strftime("%Y-%m-%d %H:%M:%S")
        return name

    def get_tbank(self, ids):
        line = self.browse(ids)
        name = ''
        for a in line:
            for l in a.assigned_ids:
                if l.type and l.type == 'bank':
                    name = l.amount
                    break
                else:
                    name = u'.................................'
        return name

    def get_tcash(self, ids):
        line = self.browse(ids)
        name = ''
        for a in line:
            for l in a.assigned_ids:
                if l.type and l.type == 'cash':
                    name = l.amount
                    break
                else:
                    name = u'.................................'
        return name

    def get_tprett(self, ids):
        line = self.browse(ids)
        name = ''
        for a in line:
            for l in a.assigned_ids:
                if l.type:
                    if l.type == 'pretty':
                        name = l.amount
                    else:
                        name = u'.................................'
        return name

    def get_tcard(self, ids):
        line = self.browse(ids)
        name = ''
        for a in line:
            for l in a.assigned_ids:
                if l.type:
                    if l.type == 'credit_card':
                        name = l.amount
                    else:
                        name = u'.................................'
        return name

    def get_ttran(self, ids):
        line = self.browse(ids)
        name = ''
        for a in line:
            for l in a.assigned_ids:
                if l.type:
                    if l.type == 'transfer':
                        name = l.amount
                    else:
                        name = u'.................................'
        return name

    def user_date(self, ids):
        line = self.browse(ids)
        date = line.create_date.strftime("%Y-%m-%d %H:%M:%S")
        return date

    def dep_date(self, ids):
        line = self.browse(ids)
        date = ''
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'dep_directors':
                date = l.create_date.strftime("%Y-%m-%d %H:%M:%S")
        return date

    def fin_date(self, ids):
        line = self.browse(ids)
        date = ''
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'fin_director':
                date = l.create_date.strftime("%Y-%m-%d %H:%M:%S")
        return date

    def pre_ceo_date(self, ids):
        line = self.browse(ids)
        date = ''
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'president_ceo':
                date = l.create_date.strftime("%Y-%m-%d %H:%M:%S")
        return date

    def prt_ceo_date(self, ids):
        line = self.browse(ids)
        date = ''
        for l in line.wkf_note_ids:
            if l.flow_line_id and l.flow_line_id.state_type == 'ceo':
                date = l.create_date.strftime("%Y-%m-%d %H:%M:%S")
        return date

    def accountant1(self, ids):
        line = self.browse(ids)
        name = ''
        n = 0
        for p in line.assigned_ids:
            n += 1
            if n == 1 and p.user_id:
                name = p.user_id.name
        return name

    def accountant2(self, ids):
        line = self.browse(ids)
        name = ''
        n = 0
        for p in line.assigned_ids:
            n += 1
            if n == 2 and p.user_id:
                name = p.user_id.name
        return name

    def accountant_date1(self, ids):
        line = self.browse(ids)
        name = ''
        n = 0
        for p in line.assigned_ids:
            n += 1
            if n == 1 and p.paid_date:
                name = p.paid_date.strftime("%Y-%m-%d %H:%M:%S")
        return name

    def accountant_date2(self, ids):
        line = self.browse(ids)
        name = ''
        n = 0
        for p in line.assigned_ids:
            n += 1
            if n == 2 and p.paid_date:
                name = p.paid_date.strftime("%Y-%m-%d %H:%M:%S")
        return name

    def get_tailbars(self, ids):
        report_id = self.browse(ids)
        return ','.join(report_id.desc_line_ids.filtered(lambda r: r.name).mapped('name'))

    def get_company_logo(self, ids):
        report_id = self.browse(ids)
        image_buf = report_id.company_id.logo_web.decode('utf-8')
        image_str = ''
        if len(image_buf) > 10:
            image_str = '<img alt="Embedded Image" width="100" src="data:image/png;base64,%s" />' % image_buf
        return image_str

    onboarding_state = fields.Selection(
        [('not_done', "Not done"), ('just_done', "Just done"), ('done', "Done"), ('closed', "Closed")],
        string="State of the sale onboarding panel", default='not_done')

    @api.model
    def action_close_onboarding(self):
        context = dict(self.env.context or {})
        query = "update payment_request set onboarding_state='closed' \
                                where id in (select id from payment_request \
                                            where user_id =%s order by id desc limit 1 ) " % context.get('uid', 1)
        self.env.cr.execute(query)


class PaymentRequestItem(models.Model):
    """ Мөнгө хүссэн өргөдөлд дагалдах баримтууд
    """

    _name = 'payment.request.item'
    _description = 'Payment Request Accompaniments'

    def _amount_total(self):
        for req in self:
            req.subtotal = req.qty * req.price

    name = fields.Char(u'Төрөл', size=128, required=True)
    type = fields.Many2one('payment.request.item.type', 'Accompaniments Type', )
    description = fields.Text('Description')
    checked = fields.Boolean(u'Checked', compute='compute_check')
    request_id = fields.Many2one('payment.request', 'Request', index=True, ondelete='cascade')
    partner = fields.Char(u'Авах газар', size=64, )
    products = fields.Char(u'Бараа', size=64, )
    qty = fields.Float(u'Тоо', )
    price = fields.Float(u'Үнэ', )
    subtotal = fields.Float('Amount in', compute='_amount_total')
    image_1920 = fields.Binary('Image')
    data = fields.Binary('Data')
    data_ids = fields.Many2many('ir.attachment', 'payment_request_item_attach_rel', 'item_id', 'attach_id',
                                string='Files')
    file_fname = fields.Char(string='File name')
    @api.depends('data_ids')
    def compute_check(self):
        for item in self:
            if item.data_ids:
                item.checked =True
            else:
                item.checked =False
class PaymentRequestDescLine(models.Model):
    _name = 'payment.request.desc.line'
    _desc = 'payment.request.desc.line'
    _order = 'sequence desc'

    sequence = fields.Integer(string='Дараалал', default=1)
    payment_request_id = fields.Many2one('payment.request', string='Төлбөрийн хүсэлт', ondelete='cascade')
    name = fields.Char('Тайлбар', required=True)
    qty = fields.Float(string='Тоо хэмжээ', digits='Product Unit of Measure', required=True, default=1.0)
    price_unit = fields.Float('Нэгж үнэ', required=True, digits=(16,2), default=0.0)
    taxes_id = fields.Many2many('account.tax', string='Taxes')
    price_subtotal = fields.Float(compute='_compute_amount', string='Дэд дүн', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Татвар', readonly=True, store=True)
    price_total = fields.Float(compute='_compute_amount', string='Нийт дүн', readonly=True, store=True)
    move_line_id = fields.Many2one('account.move.line', string='Request line')
    move_id = fields.Many2one('account.move', string='Нэхэмжлэх')

    @api.depends('qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.taxes_id.compute_all(price, line.payment_request_id.company_id.currency_id, line.qty)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
