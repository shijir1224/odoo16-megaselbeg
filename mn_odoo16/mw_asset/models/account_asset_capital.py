# -*- coding: utf-8 -*-
import calendar
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAssetCapital(models.Model):
    _name = "account.asset.capital"
    _inherit = 'mail.thread'
    _description = "Capital Asset"

    def _asset_count(self):
        for capital in self:
            capital.asset_count = len(capital.line_ids) or 0

    def _compute_is_creator(self):
        for capital in self:
            if capital.create_uid == self.env.user:
                capital.is_creator = True
            else:
                capital.is_creator = False
                

    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = [('model_id.model', '=', 'account.asset.capital'),
#                          ('branch_ids', 'in', [self.env.user.branch_id.id])
                         ]
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id
                

    name = fields.Char('Reference', default='/', copy=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    description = fields.Text('Description')
    date = fields.Date(default=fields.Date.context_today, string='Capital Date', tracking=True)
    asset_id = fields.Many2one('account.asset', related='line_ids.asset_id', string='Asset', readonly=False)
    asset_count = fields.Integer(compute='_asset_count', string='# Assets')
    partner_id = fields.Many2one('res.partner', string="Partner")
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('capital', 'Capital'),
                              ('cancel', 'Cancelled')], 'State', default='draft', tracking=True)
    line_ids = fields.One2many('account.asset.capital.line', 'capital_id', 'Assets')
    check_sequence = fields.Integer('Workflow Step', default=0, copy=False)
    is_creator = fields.Boolean(compute='_compute_is_creator')
    #flow
    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
                              default=_get_default_flow_id,
                              copy=True, required=True, domain="[('model_id.model', '=', 'account.asset.capital')]")

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id,
                                   copy=False,
                                   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'account.asset.capital')]")

    state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type', store=True)

    is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
    next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
    history_line_ids = fields.One2many('dynamic.flow.history', 'capital_id', 'Урсгалын түүхүүд')
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
                               string='Төлөв stage', store=True)
    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
    flow_line_next_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    flow_line_back_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)

    @api.depends('flow_id', 'visible_flow_line_ids', 'flow_line_id')
    def _compute_flow_line_id(self):
        for item in self:
            item.flow_line_next_id = item.flow_line_id._get_next_flow_line(item.visible_flow_line_ids)
            item.flow_line_back_id = item.flow_line_id._get_back_flow_line(item.visible_flow_line_ids)
    
    branch_id = fields.Many2one('res.branch', 'Салбар', tracking=True)
    move_count = fields.Integer(string="Move count", compute='_move_count')
    def _move_count(self):
        for asset in self:
            res = self.env['account.move'].search_count([('id', '=', asset.line_ids.move_id.ids)])
			# res = 0
            asset.move_count = res if res else 0
    def move_history_open(self):
        for asset in self:
            action = self.env.ref('account.action_move_journal_line').read()[0]
            action['domain'] = [('id','=', asset.line_ids.move_id.ids)]
            action['context'] = {}
            return action
    @api.depends('flow_id')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'account.asset.capital')])
            else:
                item.visible_flow_line_ids = []

    @api.depends('flow_line_id.stage_id')
    def _compute_flow_line_id_stage_id(self):
        for item in self:
            item.stage_id = item.flow_line_id.stage_id

    @api.depends('flow_line_id.is_not_edit')
    def _compute_is_not_edit(self):
        for item in self:
            item.is_not_edit = item.flow_line_id.is_not_edit

    @api.depends('flow_line_id')
    def _compute_state_type(self):
        for item in self:
            item.state_type = item.flow_line_id.state_type
        # item.is_cancel = True if item.flow_line_id.state_type=='cancel' else False

    @api.depends('flow_line_next_id.state_type')
    def _compute_next_state_type(self):
        for item in self:
            item.next_state_type = item.flow_line_next_id.state_type

    def flow_find(self, domain=None, order='sequence'):
        if domain is None:
            domain = []
        if self.flow_id:
            domain.append(('flow_id', '=', self.flow_id.id))
        domain.append(('flow_id.model_id.model', '=', 'account.asset.capital'))
        return self.env['dynamic.flow.line'].search(domain, order=order, limit=1).id

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find()
        else:
            self.flow_line_id = False

    def action_next_stage(self):
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        print ('next_flow_line_id1 ',next_flow_line_id)
        if next_flow_line_id:
            if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
                check_next_flow_line_id = next_flow_line_id
                while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
                    
                    temp_stage = check_next_flow_line_id._get_next_flow_line()
                    if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
                        break;
                    check_next_flow_line_id = temp_stage
                next_flow_line_id = check_next_flow_line_id

            if next_flow_line_id._get_check_ok_flow(self.branch_id, False):
                self.flow_line_id = next_flow_line_id
                if self.flow_line_id.state_type=='done':
                    self.action_done()

                self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'capital_id', self)
#                 if self.flow_line_next_id:
#                     send_users = self.flow_line_next_id._get_flow_users(self.branch_id, False)
#                     if send_users:
#                         self.send_chat_employee(send_users.mapped('partner_id'))
            else:
                print ('self.branch_id')
                con_user = next_flow_line_id._get_flow_users(self.branch_id, False)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(con_user.mapped('display_name'))
                raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
    
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
                    if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
                        break;
                    check_next_flow_line_id = temp_stage
                back_flow_line_id = check_next_flow_line_id
                
            if back_flow_line_id._get_check_ok_flow(self.branch_id, False):
                self.flow_line_id = back_flow_line_id
                self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'capital_id', self)
            else:
                raise UserError(_('You are not back user'))

    # def action_cancel_stage(self):
    #     flow_line_id = self.flow_line_id._get_cancel_flow_line()
    #     if flow_line_id._get_check_ok_flow(self.branch_id, False):
    #         return self.action_cancel()
    #     else:
    #         raise UserError(_('You are not cancel user'))

    def action_cancel_stage(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if not flow_line_id:
            raise UserError('Урсгал тохиргоо буруу байна. Системийн админд хандана уу!')
        if flow_line_id._get_check_ok_flow(False, False):
            # self.check_comparison_cancel()
            self.flow_line_id = flow_line_id
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'capital_id', self)
            self.state = 'cancel'
        else:
            cancel_user = flow_line_id._get_flow_users(False, False)
            raise UserError(_('Цуцлах хэрэглэгч биш байна!\nЦуцлах хэрэглэгчид: %s' %', '.join(cancel_user.mapped('display_name'))))

    def set_stage_cancel(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow(self.branch_id, False):
            self.flow_line_id = flow_line_id
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'capital_id', self)
        else:
            raise UserError(_('You are not cancel user'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'capital_id', self)
        else:
            raise UserError(_('You are not draft user'))
#         
    @api.onchange('description')
    def _onchange_description(self):
        for line in self.line_ids:
            line.description = self.description

    @api.model
    def default_get(self, default_fields):
        res = super(AccountAssetCapital, self).default_get(default_fields)
        context = dict(self._context or {})
        vals = []
        if context.get('active_model') == 'account.asset' and context.get('active_ids'):
            assets = self.env[context.get('active_model')].browse(context.get('active_ids'))
            for asset in assets:
                if asset.state == 'open':
                    line = [0, False, {'asset_id': asset.id,
                                       'state': 'draft',
                                       'code': asset.code,
                                       'partner_id':self.partner_id.id or False,
                                    #    'manufactured_date': asset.manufactured_date,
                                       'commissioned_date': asset.acquisition_date,
                                       'old_method_period': asset.method_period,
                                       'old_method_number': asset.method_number,
                                       'value': asset.value,
                                       'value_depreciated': asset.value_depreciated,
                                       'value_residual': asset.value_residual,
                                       'method_number': asset.method_number,
                                       'method_period': asset.method_period,
                                       }]
                    vals.append(line)
        res.update({'line_ids': vals})
        return res

    @api.model
    def create(self, values):
        # Нэрийг автомат дугаарлана
        res = super(AccountAssetCapital, self).create(values)
        if res.name == '/':
            res.write({'name': self.env['ir.sequence'].next_by_code('account.asset.capital')})
        return res

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй шилжилтийг л устгадаг байна
        for capital in self:
            if capital.state != 'draft':
                raise UserError(_('You cannot delete an asset capital which is not draft.'))
        return super(AccountAssetCapital, self).unlink()

    def open_assets(self):
        # Хөрөнгө рүү орох
        ids = []
        for line in self.line_ids:
            if line.asset_id:
                ids.append(line.asset_id.id)
        return {
            'name': _('Assets'),
            'view_mode': 'tree,form',
            'res_model': 'account.asset',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', ids)],
        }


    def action_done(self):
        self.line_ids.capital_button()
        self.write({'state': 'capital'})

    def action_cancel(self):
        # context = dict(self._context or {})
        # context['asset_move'] = True
        self.write({'state': 'cancel'})
    @api.model
    def get_import_templates(self):
        return [{
            'label': _('Import Template for Asset Capital'),
            'template': '/l10n_mn_account_asset/static/xls/asset_capital.xls'
        }]


class AccountAssetCapitalLine(models.Model):
    _name = "account.asset.capital.line"
    _description = "Capital Asset Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    asset_id = fields.Many2one('account.asset', 'Asset', required=True, domain = [('state', '!=', 'model')])
    code = fields.Char(string='Asset Code', size=32, readonly=True, related = 'asset_id.code')
    type = fields.Selection([('invoice_line', 'Capital with an Invoice Line'),
                             ('account', 'Capital with an Account')], string='Capital Type', required=True, default='account')
    account_id = fields.Many2one('account.account', 'Capital Account', domain=[('deprecated', '=', False)])
    capital_id = fields.Many2one('account.asset.capital', 'Capital Asset', ondelete='cascade')
    partner_id = fields.Many2one('res.partner', 'Performer Partner',related = 'capital_id.partner_id')
    invoice_line_id = fields.Many2one('account.move.line', 'Capital Invoice Line', ondelete='restrict')
    # domain=[('partner_id', '=', partner_id),('move_id.move_type', '=', 'in_invoice'), ('move_id.state', '!=', 'cancel'), ('price_unit', '>', 0)],
    asset_state = fields.Selection(related='asset_id.state', string='Asset State')
    manufactured_date = fields.Date(string='Manufactured Date', invisible=True)
    commissioned_date = fields.Date(string='Commissioned Date')
    old_method_number = fields.Integer(string='Old Number of Depreciations', required=True)
    old_method_period = fields.Integer(string='Old Period Length')
    value = fields.Float(string='Value')
    value_depreciated = fields.Float(string='Depreciated Value')
    value_residual = fields.Float(string='Residual Value')
    capital_amount = fields.Float('Capital Amount', help='If you want to increase asset value then set capital amount on this field')
    department_id = fields.Many2one('hr.department', 'Performer Department')
    method_number = fields.Integer(string='Number of Depreciations', required=True)
    method_period = fields.Integer(string='Period Length')
    date = fields.Date(string='Capital Date', related='capital_id.date', store=True)
    description = fields.Char('Description')
    move_id = fields.Many2one('account.move', 'Capital Account Move')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('capital', 'Capital'),
                              ('cancel', 'Cancelled')], 'State', default='draft', tracking=True)

    @api.onchange('asset_id')
    def onchange_asset(self):
        if self.asset_id:
            self.code = self.asset_id.code
            # self.manufactured_date = self.asset_id.manufactured_date
            self.commissioned_date = self.asset_id.acquisition_date
            self.old_method_number = self.asset_id.method_number
            self.old_method_period = self.asset_id.method_period
            self.value = self.asset_id.original_value
            # self.value_depreciated = self.asset_id.value_depreciated
            # self.value_residual = self.asset_id.value_residual
            self.method_number = self.asset_id.method_number
            self.method_period = self.asset_id.method_period

    @api.onchange('method_number')
    def onchange_method_number(self):
        if self.old_method_number > self.method_number:
            raise UserError(_('New Number of Depreciations is less than old number of depreciations'))

    @api.onchange('invoice_line_id')
    def onchange_invoice(self):
        if self.invoice_line_id:
            invoice_date = self.invoice_line_id.move_id.invoice_date
            capital_invoice_lines = self.search([('invoice_line_id', '=', self.invoice_line_id.id), ('id', '!=', self._origin.id)])
            capital_amount = self.invoice_line_id.price_subtotal
            for invoice_line in capital_invoice_lines:
                capital_amount -= invoice_line.capital_amount
            if capital_amount <= 0:
                raise UserError(_('Invoice line was previously capitalized!'))
            self.capital_amount = capital_amount

    @api.model
    def default_get(self, fields):
        res = super(AccountAssetCapitalLine, self).default_get(fields)
        context = self._context
        if context.get('description', False):
            res['description'] = context.get('description')
        if context.get('account_id', False):
            res['account_id'] = context.get('account_id')
        return res

    @api.model
    def create(self, values):
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'code': asset.code,
                # 'manufactured_date': asset.manufactured_date,
                'commissioned_date': asset.acquisition_date,
                'value': asset.original_value,
                # 'value_depreciated': asset.value_depreciated,
                # 'value_residual': asset.value_residual,
                'old_method_period': asset.method_period,
                'old_method_number': asset.method_number,
            })
        if 'old_method_number' in values.keys() and 'method_number' in values.keys():
            if values['old_method_number'] > values['method_number'] and asset.book_value > 0:
                raise UserError(_('New Number of Depreciations is less than old number of depreciations'))
        return super(AccountAssetCapitalLine, self).create(values)

    def write(self, values):
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'code': asset.code,
                # 'manufactured_date': asset.manufactured_date,
                'asquisition_date': asset.a,
                'original_value': asset.original_value,
                # 'value_depreciated': asset.value_depreciated,
                # 'value_residual': asset.value_residual,
                'old_method_period': asset.method_period,
                'old_method_number': asset.method_number,
            })
            new = values['method_number'] if 'method_number' in values else asset.method_number
            old = values['old_method_number'] if 'old_method_number' in values else asset.old_method_number
            if old > new:
                raise UserError(_('New Number of Depreciations is less than old number of depreciations'))
        return super(AccountAssetCapitalLine, self).write(values)

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй мөрийг л устгадаг байна
        for line in self:
            if line.state != 'draft':
                raise UserError(_('You cannot delete an asset capital line which is not draft.'))
        return super(AccountAssetCapitalLine, self).unlink()

    def get_check(self, asset, current_currency):
        self.write({'state': 'approved'})
#         # шалгах
#         check_day = False
#         if asset.method_number > self.method_number:
#             raise UserError(_('New Number of Depreciations is less than old number of depreciations'))
#         if self.capital_amount <= 0:
#             raise UserError(_('Capital amount cannot 0!'))
#         amount = current_currency._convert(self.capital_amount, asset.company_id.currency_id, asset.company_id, self.date, round=False)
#         date = self.date
# #         if self.capital_id.company_id.capital_depreciation == 'next_month':
#             # Хэрэв дараа сараас капиталжуулалтын дүнг тооцоолох бол
#         month_days = calendar.monthrange(date.year, date.month)[1]
#         date = date.replace(day=month_days)
#         asset.search_and_raise_line(date)
#         if asset.state != 'open':
#             raise UserError(_("%s asset state is not open. Only can capital assets with open state!" % asset.name))
#         history_ids = asset.history_ids.sorted(key=lambda l: l.date)
#         if history_ids and history_ids[-1].date:
#             history_date = history_ids[-1].date
#             if history_date > self.date:
#                 raise UserError(_("You cannot modify. %s capitalized %s after." % (asset.name, self.date)))
#             elif history_date == self.date:
#                 raise UserError(_("Depreciation cannot be changed more than once a day."))
#         before_capital = self.search([('asset_id', '=', asset.id), ('id', '!=', self.id), ('state', '=', 'capital')], order='date desc')
#         if before_capital and before_capital[0].date:
#             history_date = before_capital[0].date
#             if history_date > self.date:
#                 raise UserError(_("You cannot modify. %s capitalized %s after." % (asset.name, self.date)))
#             elif history_date == self.date:
#                 check_day = True
#         if self.invoice_line_id:
#             invoice_date = self.invoice_line_id.move_id.invoice_date
#             capital_invoice_lines = self.search([('invoice_line_id', '=', self.invoice_line_id.id), ('id', '!=', self.id)])
#             capital_amount = self.invoice_line_id.price_subtotal
#             for invoice_line in capital_invoice_lines:
#                 capital_amount -= invoice_line.capital_amount
#             if capital_amount <= 0:
#                 raise UserError(_('Cannot capitalize. Because this invoice line has already been capitalized!'))
#             if amount > capital_amount:
#                 if len(capital_invoice_lines) > 0:
#                     raise UserError(_('Cannot capitalize more than %s. Because this invoice line has already been capitalized!') % capital_amount)
#                 else:
#                     raise UserError(_('Capital amount cannot greater than invoice line subtotal!'))
#             if self.invoice_line_id and self.date < invoice_date:
#                 raise UserError(_('Capital date cannot less than invoice line date!'))
#         return check_day, date

#     def send_button(self):
#         for line in self:
#             asset = line.asset_id
#             current_currency = asset.currency_id or asset.company_id.currency_id
#             line.get_check(asset, current_currency)
#         self.write({'state': 'waiting'})

#     def approve_button(self):
#         self.write({'state': 'approved'})

    def capital_button(self):
        # Капиталжуулах
        move_obj = self.env['account.move']
        for line in self:
            line_ids = []
            asset = line.asset_id
            current_currency = asset.currency_id or asset.company_id.currency_id
            amount = current_currency._convert(line.capital_amount, asset.company_id.currency_id, asset.company_id, line.date, round=False)
            asset_value = line.capital_amount + asset.value_residual
            old_values = {'value': asset.original_value,
                          'method_number': asset.method_number,
                          }
            asset.write({'method_number': line.method_number,
                        })
            if line.capital_id.partner_id.id:
                partner_id = line.capital_id.partner_id.id
            else:
                partner_id = False
            # print('--------s-s----s-s-s--',partner_id)
            line_name = _('%s %s is capital' % (asset.name, asset.code))
            # Дт талын журналын мөр
            line_ids.append(asset._get_line_vals(line_name, asset.account_asset_id.id, partner_id, amount, amount, current_currency, line.date))
            # Кт талын журналын мөр
            if line.type == 'invoice_line':
                kt_account = line.invoice_line_id.account_id.id
            else:
                kt_account = line.account_id.id
            line_ids.append(asset._get_line_vals(line_name, kt_account, partner_id, -amount, -amount, current_currency, line.date))
            journal_id = asset.journal_id.id
#             if asset.company_id.asset_journal_settings == 'intersperse':
#                 if not asset.company_id.capital_asset_journal_id:
#                     raise UserError(_('Configure capital journal of asset in %s company!' % asset.company_id.name))
#                 journal_id = asset.company_id.capital_asset_journal_id.id
            # print('21421421512-5-125-125--215',line_ids)
            # print(s)
            move_vals = {'date': line.date,
                         'ref': line.capital_id.name,
                         'journal_id': journal_id,
                         'auto_post' :'no',
                         'line_ids': line_ids,
                         
                        }

            move_id = move_obj.create(move_vals)
            self.move_id = move_id.id
            move_id.action_post()
            for moves in move_id.asset_ids:
                if moves:
                    # print('safasfas', moves)
                    moves.unlink()
                # for move_line in moves.line_ids:
                #     asset_rel = self.env['asset.move.line.rel'].sudo().search([('line_id','=',move_line.id)])
                #     if asset_rel:
                #         asset_ids_rel = self.env['account.asset'].sudo().search([('id','=',asset_rel.asset_id)])
                #         if asset_ids_rel:
                #             asset_ids_rel.unlink()

                    		# obj = self.env[ self.env.context.get('model_id_model',self.model_id.model) ].sudo().search([('id','=',ids)])

                    # print('safsafasf',move_line.original_many_asset_ids)
                    # print('safsafasf',move_line.asset_id)
                    # if move_line.asset_id:
                    #     move_line.asset_id.unlink()
            # print('safsafasf',moves)
            # print('asdfasfasfsafsa',move_id.original_many_asset_ids)
                # if moves.asset_id:

                #     moves.asset_id.unlink()
            cap_amount=asset.capital_value+line.capital_amount
            asset.write({'capital_value': cap_amount, 'method_number':line.method_number})
            asset.compute_depreciation_board()
            # print(s)

            line.write({'state': 'capital'})
        return True

    def draft_button(self):
        self.write({'state': 'draft'})
class DynamicFlowHistory(models.Model):
    _inherit = 'dynamic.flow.history'

    capital_id = fields.Many2one('account.asset.capital', 'Capital', ondelete='cascade', index=True)
    asset_move_id = fields.Many2one('account.asset.move', 'Asset move', ondelete='cascade', index=True)
    revaluation_id = fields.Many2one('account.asset.revaluation', 'Asset revaluation', ondelete='cascade', index=True)
    asset_act_id = fields.Many2one('account.asset.act', 'Asset act', ondelete='cascade', index=True)
    asset_sell_id = fields.Many2one('account.asset.sell', 'Asset sell', ondelete='cascade', index=True)
