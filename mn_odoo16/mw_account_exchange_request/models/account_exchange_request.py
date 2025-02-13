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


class ResBank(models.Model):
    _inherit = 'res.bank'

    is_exchange = fields.Boolean('Арилжаа?')


class ExchangeRequest(models.Model):
    """ Мөнгө хүссэн өргөдөл
    """

    _name = 'exchange.request'
    _description = 'Exchange Request'
    _order = 'create_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin','analytic.mixin']


    def _get_mail_thread_data_attachments(self):
        self.ensure_one()
        res = super()._get_mail_thread_data_attachments()
        # thread.check_items
        item_ids = self.check_items
        item_ids = self.env['ir.attachment'].search([('res_id', 'in', item_ids.ids), ('res_model', '=', 'exchange.request.item')], order='id desc')
        return res | item_ids

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

    def _get_total_amount(self, ids):
        # Нийт тоог олох
        obj = self.env['exchange.request'].browse(ids)
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

    def _default_department(self):
        return self.env['hr.department'].search([('id', '=', self.env.user.department_id.id)], limit=1)

    @api.depends('user_id')
    def _compute_dep_branch(self):
        for item in self:
            item.branch_id = item.user_id.branch_id.id
            item.department_id = item.user_id.department_id.id

    @api.model
    def _get_item_lines(self):
        res = []
        items = ['Гэрээ', 'Гэрээний гүйцэтгэлийн акт', 'Төсөв', 'Нэхэмжлэх', 'И-Баримт', 'Бусад баримт']
        for rs in items:
            dct = {
                'name': rs,
                'checked': False,
                'data_ids': False,
            }
            res.append(dct)
        return res

    @api.model
    def _get_line_lines(self):
        res = []
        bank_obj=self.env['res.bank']
        items=bank_obj.search([('is_exchange','=',True)])
        # items = ['Гэрээ', 'Гэрээний гүйцэтгэлийн акт', 'Төсөв', 'Нэхэмжлэх', 'И-Баримт', 'Бусад баримт']
        for rs in items:
            dct = {
                'bank_id': rs.id,
                'checked': False,
                'price_unit': 0,
            }
            res.append(dct)
        return res

    name = fields.Char('Reference', size=64, readonly=True, default='New', tracking=True, copy=False)
    company = fields.Char('Арилжаа хийх Компани', size=64, copy=False)
    company = fields.Char('Арилжаа хийх Компани', size=64, copy=False)
    type = fields.Selection(TYPE_Selection, 'Request Type', default='cash', tracking=True)
    user_id = fields.Many2one('res.users', 'Requester', required=True, readonly=True,
                              default=lambda self: self.env.user.id, states={'draft': [('readonly', False)]},
                              tracking=True)
    create_partner_id = fields.Many2one('res.partner', string="Хүсэлт гаргасан", default=lambda self: self.env.user.partner_id.id,required=True, readonly=True,)
    deadline = fields.Date("Deadline", readonly=True, states={'draft': [('readonly', False)]})
    priority = fields.Selection(PRIORITY_Selection, 'Priority', readonly=True, default='3',
                                states={'draft': [('readonly', False)]}, tracking=True)
    payment_ref = fields.Char(string='Тайлбар')
    currency_id = fields.Many2one('res.currency', 'Зарах валют', required=True, default=_default_currency, readonly=True,
                                  states={'draft': [('readonly', False)]}, tracking=True, )
    to_currency_id = fields.Many2one('res.currency', 'Авах валют', required=True, default=_default_currency, readonly=True,
                                  states={'draft': [('readonly', False)]}, tracking=True, )
    create_user_id = fields.Many2one('res.users', 'Create User', required=True, default=lambda self: self.env.user.id)
    partner_id = fields.Many2one('res.partner', 'Partner', tracking=True)
    check_items = fields.One2many('exchange.request.item', 'request_id', 'Accompaniments', default=_get_item_lines)
    state = fields.Selection([('draft','Ноорог'),
                              ('sent','Илгээсэн'),
                              ('confirm','Баталсан'),
                              ('calc','Арилжаа хийх'),
                              ('done','Гүйцэтгэсэн'),
                              ('cancel','Цуцалсан')
                              ], string='Төлөв', tracking=True, default='draft')
    description = fields.Text('Additional description')
    department_id = fields.Many2one('hr.department', 'Department', compute="compute_department",
                                    tracking=True)
    not_date = fields.Date('Мэдэгдэл ирэх огноо',compute ='_compute_date_to', store=True)
    bank_statement_line_id = fields.Many2one('account.bank.statement.line', 'Payment Ref.', readonly=True)
    # olon uuseh
    bank_statement_line_ids = fields.Many2many('account.bank.statement.line', 'exchange_request_bsl_rel', 'item_id',
                                               'line_id', string='Хуулгууд')
    db_attach = fields.Binary('File')
    is_business_trip = fields.Boolean('Is business trip')
    approve_user_id = fields.Many2one('res.users', 'Approver')
    date = fields.Datetime("Creation Date", default=fields.Datetime.now, readonly=True,
                           states={'draft': [('readonly', False)]}, tracking=True, copy=False)
    complete_date = fields.Datetime('Confirmed Date', readonly=True)
    # wkf_note_ids = fields.One2many('request.template.wkf.notes', 'request_id', 'Workflow History', readonly=True)
    amount = fields.Float('Amount', readonly=True, states={'draft': [('readonly', False)]},
                          tracking=True, digits=(16, 2))

    branch_id = fields.Many2one('res.branch', 'Салбар', tracking=True)
    confirmed_amount = fields.Float('Цохсон дүн', tracking=True)
    company_id = fields.Many2one('res.company', string='Арилжаа хийх компани', default=lambda self: self.env.company, tracking=True)
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
    duusgahgui = fields.Boolean(string='Дуусгахгүй?', default=False)
    journal_id = fields.Many2one('account.journal', 'Журнал')
    ex_account_id = fields.Many2one('account.account', 'Зардлын данс')
    cash_type_id = fields.Many2one('account.cash.move.type', 'МГ төрөл')
    desc_line_ids = fields.One2many('exchange.request.desc.line', 'payment_request_id', string='Тайлбарын мөр',default=_get_line_lines)
    amount_tax_pay = fields.Monetary(string='Нийт татвар', store=True, readonly=True, compute='_amount_all')
    amount_total_pay = fields.Monetary(string='Нийт дүн', store=True, readonly=True, compute='_amount_all', tracking=4)
    move_id = fields.Many2one('account.move', string='Related invoice', ondelete='cascade')
    account_move_ids = fields.Many2many('account.move','account_move_exchange_req_rel','req_id','move_id','Payments',copy=False)    
    paid_date = fields.Date(string="Гүйцэтгэх эцсийн огноо")
    current_rate = fields.Float(string=u"Ханш", store=True)
    date_currency = fields.Date('Ханш бодох огноо', default=fields.Date.context_today)
    gadaad_currency = fields.Boolean(string=u"Валют гадаад эсэх", compute='_com_gadaad_currency')
    currency_company_id = fields.Many2one('res.currency', string=u"Валют Компани", related='company_id.currency_id', readonly=True)
    amount_str_mw = fields.Char(string="Amount str", compute="get_amount_str")
    
    cross_rate = fields.Float(string=u"Сонгосон ханш", store=True,compute="compute_cross", digits=(16, 4)) #
    buy_amount = fields.Float('Нийт авах дүн', readonly=True, states={'draft': [('readonly', False),('calc', False)]},
                          tracking=True, digits=(16, 2))

    sell_amount = fields.Float('Нийт зарах дүн', readonly=True, states={'draft': [('readonly', False)]},
                          tracking=True, digits=(16, 2))
    bank_id = fields.Many2one('res.bank', string='Сонгосон банк', ondelete='cascade')
    
    
    bank_id = fields.Many2one('res.bank', string='Сонгосон банк', ondelete='cascade')
    bank_ids = fields.Many2many('res.bank', 'exchange_request_bsl_bank_rel', 'item_id',
                                               'line_id', string='Банк:  /сонголтууд байх/')
    bank_dansuud = fields.Char(string='Данс:')
    
    comment_huleen_avah = fields.Text('Валют хүлээн авах тайлбар')
    
    phone = fields.Char(string='Холбогдох утас')
    decs3 = fields.Char(string='Арилжаа хийсэн хэрэглэгчийн тайлбар')
    # buy_rate = fields.Float(string=u"Ханш" ,compute="compute_rate",)
    # sell_rate = fields.Float(string=u"Ханш", compute="compute_rate",)

    calc_selection = [
        ('v1', u'Зарах дүн/Сонгосон ханш'),
        ('v2', u'Зарах дүн*Сонгосон ханш'),
        ('v3', u'Авах дүн/Сонгосон ханш'),
        ('v4', u'Авах дүн*Сонгосон ханш'),
    ]
    type_calc = fields.Selection(calc_selection, 'Тооцоолох арга', default='v1',)
    
    @api.onchange('type_calc','state','company_id')
    def ochange_compute_type(self):
        for item in self:
            print ('item.calc_selection ',item.type_calc)
            if item.type_calc =='v1' and item.sell_amount!=0 and item.cross_rate!=0:
                item.buy_amount = item.sell_amount/item.cross_rate
            elif item.type_calc =='v2' and item.sell_amount!=0 and item.cross_rate!=0:
                item.buy_amount = item.sell_amount*item.cross_rate
            elif item.type_calc =='v3' and item.buy_amount!=0:
                item.sell_amount = item.buy_amount/item.cross_rate
            if item.type_calc =='v4' and item.buy_amount!=0:
                item.sell_amount = item.buy_amount*item.cross_rate
    # def compute_rate(self):
    #     for item in self:
    #         if item.desc_line_ids:
    #             for i in item.desc_line_ids:
    #                 if i.checked:
    #                     item.buy_rate=i.price_unit
    #                     item.sell_rate=0
    #         else:
    #                     item.buy_rate=0
    #                     item.sell_rate=0
                
                        
    #
    @api.depends('sell_amount','desc_line_ids','desc_line_ids.price_unit')
    def compute_cross(self):
        for item in self:
            if item.desc_line_ids:
                for i in item.desc_line_ids:
                    if i.checked:
                        item.cross_rate=i.price_unit
                        if i.price_unit!=0:
                            if item.sell_amount>0:
                                item.buy_amount=item.sell_amount*i.price_unit
                            elif item.buy_amount>0:
                                item.sell_amount=item.buy_amount/i.price_unit
                        if i.bank_id:
                            item.bank_id=i.bank_id.id
            # if item.buy_rate>0 and item.sell_rate>0:
            #     # if item.buy_amount>item.sell_amount:
            #         item.cross_rate=item.buy_rate/item.sell_rate
            #     # else:
            #     #     item.cross_rate=item.sell_amount/item.buy_amount
            else:
                item.cross_rate = 0
                
                    
    @api.depends('currency_id','currency_company_id')
    def _com_gadaad_currency(self):
        for item in self:
            if item.currency_id!=item.currency_company_id:
                item.gadaad_currency = True
            else:
                item.gadaad_currency = False
    @api.constrains('payment_ref')
    def _check_valid_payment_ref(self):
        for record in self:
            if ',' in record.payment_ref or '.' in record.payment_ref:
                raise ValidationError("Гүйлгээний утга дээр дараах тэмдэгтүүд ашиглах боломжгүй. ',' or '.'")    
    @api.onchange('currency_id','date_currency','state','company_id')
    def ochange_compute_curent_rate(self):
        for item in self:
            date_order = item.date_currency or fields.Datetime.now()
            if item.currency_id and item.company_id:
                rr = self.env['res.currency']._get_conversion_rate(item.currency_id, item.company_id.currency_id, item.company_id, date_order)
                item.current_rate = rr
            else:
                item.current_rate = 0

    @api.depends('create_partner_id','create_uid')
    def compute_department(self):
        for payment in self:
            if payment.create_partner_id:
                emp = self.env['hr.employee'].search(
                [('partner_id', '=', payment.create_partner_id.id)], limit=1)
                payment.department_id = emp.department_id.id
                payment.branch_id = emp.department_id.branch_id.id
    @api.depends('desc_line_ids.price_subtotal')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            # for line in order.desc_line_ids:
            #     amount_untaxed += line.price_subtotal
                # amount_tax += line.price_tax

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
            price_subtotal = line.price_subtotal
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

    @api.depends('bank_statement_line_id')
    def compute_tulugdsun(self):
        for item in self:
            if item.bank_statement_line_id:
                item.tulugdsun_dun = item.bank_statement_line_id.amount*(-1)
            else:
                item.tulugdsun_dun = 0
    @api.depends('tulugdsun_dun')
    def get_amount_str(self):
        for report_id in self:
            if report_id.tulugdsun_dun > 0:
                report_id.amount_str_mw = verbose_format(abs(report_id.tulugdsun_dun))
            else:
                report_id.amount_str_mw = False
    def change_history(self):
        obj_min = 5000
        objs = self.env['request.template.wkf.notes'].search([
            ('create_ok', '=', False),
        ], limit=obj_min)
        i = len(objs)
        for item in objs:
            vals = {
                'user_id': item.user_id.id,
                'date': item.date,
                'payment_request_id': item.request_id.id,
                'company_id': item.request_id.company_id.id,
            }
            item.create_ok = True
            obj.compute_spend_time('payment_request_id', item.request_id)

            obj_id.create_date = item.create_date
            obj_id.create_uid = item.create_uid.id

            _logger.info('Payment request flow history shiljuuleh %s of %s' % (i, obj_min))
            i -= 1
    def action_date_noti_send(self, partner_id):
        subject = 'Төлбөрийн хүсэлтийн сануулга'
        html = u'<b><i style="color:red">Төлбөрийн хүсэлтийн сануулга</i></b><br/>'
        html += u"""<b></b> - Төлбөрийн хүсэлтийн <b>"%s"</b> дугаартай баримтын төлөх хугацаа дуусахад 3 хоног үлдлээ. Төлөх эцсийн огноо <b>%s</b>!"""% (self.name,self.paid_date)
        mail_obj = self.env['mail.mail'].sudo().create({
            'email_from': self.env.user.email_formatted,
            'email_to': partner_id.email,
            'subject': subject,
            'body_html': '%s' % html,
            # 'attachment_ids': attachment_ids
        })
        mail_obj.send()

    @api.depends('paid_date')
    def _compute_date_to(self):
        day = timedelta(3)
        for item in self:
            if item.paid_date:
                item.not_date = item.paid_date - day

    def update_payment_info(self):
        today = date.today()
        payment_obj = self.env['exchange.request'].search([('state','!=','done'),('not_date', '=', today)])
        for payment in payment_obj:
            payment.action_date_noti_send(partner_id = payment.create_partner_id)
    def all_compute_user_ids(self):
        for item in self.sudo().search([]):
            item.sudo().compute_user_ids()

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

    def com_is_yurunhii_nybo(self):
        for item in self:
            if self.env.user.has_group("mw_account_exchange_request.res_groups_account_general_accountant"):
                item.is_yurunhii_nybo = True
            else:
                item.is_yurunhii_nybo = False

    # def name_get(self):
    #     res = []
    #     for partner in self:
    #         res_name = super(ExchangeRequest, partner).name_get()
    #         if partner.narration_id:
    #             res_name = u'' + res_name[0][1] + u' (' + partner.narration_id.display_name + ')'
    #             res.append((partner.id, res_name))
    #         else:
    #             res.append(res_name[0])
    #     return res

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
                'account_id': form.account_id.id or request.ex_account_id and request.ex_account_id.id ,
                'journal_id': form.journal_id.id,
                'ref': str(request.display_name)+ " / " + str(request.description),
                'foreign_currency_id': self.currency_id.id,
                # 'amount_currency': self.currency_id.id,
                # 'note': '%s :\n %s' % (request.narration_id.name, request.narration_id.description or ''),
                # 'analytic_account_id': form.analytic_id and form.analytic_id.id or False,
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
        
        for request in self:
            if request.state not in ['accountant', 'pay']:
                raise UserError(u'{} гүйлгээ хийх төлөвгүй байна!!!'.format(request.name))
            if self._context.get('multi',False):
                amount = request.confirmed_amount or request.amount
            else:
                amount = form.amount or request.confirmed_amount or request.amount
            # fact = ''
            if form.journal_id and form.journal_id.currency_id and request.currency_id.id != form.journal_id.currency_id.id:
                amount = cur_obj.compute(request.currency_id, form.journal_id.currency_id, amount, )
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
        return super(ExchangeRequest, self).unlink()

    def action_cancel(self):
        if self.bank_statement_line_id:
            raise UserError(u'Кассын бичилт хийгдсэн байна цуцлах боломжгүй %s' % (self.display_name))

        self.write({'state': 'cancel'})

    def action_draft(self):
        self.write({'state': 'draft'})
        
    def action_send(self):
        self.write({'state': 'sent'})

    def action_confirm(self):
        self.write({'state': 'confirm'})
    def action_calc(self):
        self.write({'state': 'calc'})
    def action_done(self):
        self.write({'state': 'done'})


    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].with_company(company_id).next_by_code(
                'account.exchange.request') or '/'
        res = super(ExchangeRequest, self).create(vals)
        return res

    accountant_id = fields.Many2one('res.users', string='Нягтлан', tracking=True, index=True, copy=False)

    # ------------------------------flow------------------
    def update_attach(self):
        objs = self.env['exchange.request.item'].sudo().search([('data', '!=', False)])
        len_obj = len(objs)
        i = len_obj
        for item in objs:
            query = "select array_agg(id) from ir_attachment where res_model='exchange.request.item' and res_id = {0}".format(
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
            _logger.info(' DATA ATTACH exchange.request.item %s of %s ' % (i, len_obj))
            i -= 1

    def request_print(self):
        model_id = self.env['ir.model'].sudo().search([('model','=','exchange.request')], limit=1)
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


class ExchangeRequestItem(models.Model):
    """ Мөнгө хүссэн өргөдөлд дагалдах баримтууд
    """

    _name = 'exchange.request.item'
    _description = 'Payment Request Accompaniments'

    def _amount_total(self):
        for req in self:
            req.subtotal = req.qty * req.price

    name = fields.Char(u'Төрөл', size=128, required=True)
    description = fields.Text('Description')
    checked = fields.Boolean(u'Checked', compute='compute_check')
    request_id = fields.Many2one('exchange.request', 'Request', index=True, ondelete='cascade')
    partner = fields.Char(u'Авах газар', size=64, )
    products = fields.Char(u'Бараа', size=64, )
    qty = fields.Float(u'Тоо', )
    price = fields.Float(u'Үнэ', )
    subtotal = fields.Float('Amount in', compute='_amount_total')
    image_1920 = fields.Binary('Image')
    data = fields.Binary('Data')
    data_ids = fields.Many2many('ir.attachment', 'payment_exchange_item_attach_rel', 'item_id', 'attach_id',
                                string='Files')
    file_fname = fields.Char(string='File name')
    @api.depends('data_ids')
    def compute_check(self):
        for item in self:
            if item.data_ids:
                item.checked =True
            else:
                item.checked =False
class ExchangeRequestDescLine(models.Model):
    _name = 'exchange.request.desc.line'
    _desc = 'exchange.request.desc.line'
    _order = 'sequence desc'

    sequence = fields.Integer(string='Дараалал', default=1)
    payment_request_id = fields.Many2one('exchange.request', string='Төлбөрийн хүсэлт', ondelete='cascade')
    bank_id = fields.Many2one('res.bank', string='Банк', ondelete='cascade')
    name = fields.Char('Тайлбар',)
    qty = fields.Float(string='Тоо хэмжээ', digits='Product Unit of Measure', required=True, default=1.0)
    price_unit = fields.Float('Анх ирүүлсэн ханш', required=True, digits=(16,4), default=0.0)
    price_unit2 = fields.Float('Өссөн ханш', digits=(16,4), default=0.0)
    price_subtotal = fields.Float(compute='_compute_amount', string='Дэд дүн', readonly=True, store=True)
    move_line_id = fields.Many2one('account.move.line', string='Request line')
    move_id = fields.Many2one('account.move', string='Нэхэмжлэх')
    currency_id = fields.Many2one('res.currency', string='Валют')
    
    checked = fields.Boolean('Сонгосон ханш')
    
    @api.depends('qty', 'price_unit')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit*line.qty
            # taxes = line.taxes_id.compute_all(price, line.payment_request_id.company_id.currency_id, line.qty)
            line.update({
                'price_subtotal': price,
            })
