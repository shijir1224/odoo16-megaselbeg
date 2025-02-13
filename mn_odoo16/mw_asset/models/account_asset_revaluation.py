# -*- coding: utf-8 -*-
import calendar
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAssetRevaluation(models.Model):
    _name = "account.asset.revaluation"
    _inherit = 'mail.thread'
    _description = "Revaluation Asset"

    def _asset_count(self):
        for revaluation in self:
            revaluation.asset_count = len(revaluation.line_ids) or 0

    def _compute_is_creator(self):
        for revaluation in self:
            if revaluation.create_uid == self.env.user:
                revaluation.is_creator = True
            else:
                revaluation.is_creator = False


    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = [('model_id.model', '=', 'account.asset.revaluation'),
#                          ('branch_ids', 'in', [self.env.user.branch_id.id])
                         ]
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    name = fields.Char('Reference', default='/', copy=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    transaction = fields.Char('Transaction', required=True)
    description = fields.Text('Description')
    date = fields.Date(default=fields.Date.context_today, string='Revaluation Date', tracking=True)
    asset_id = fields.Many2one('account.asset', related='line_ids.asset_id', string='Asset', readonly=False)
    asset_count = fields.Integer(compute='_asset_count', string='# Assets')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('revaluation', 'Revaluation'),
                              ('cancel', 'Cancelled')], 'State', default='draft', tracking=True)
    line_ids = fields.One2many('account.asset.revaluation.line', 'revaluation_id', 'Assets')
    check_sequence = fields.Integer('Workflow Step', default=0, copy=False)
    is_creator = fields.Boolean(compute='_compute_is_creator')
    #flow
    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
                              default=_get_default_flow_id,
                              copy=True, required=True, domain="[('model_id.model', '=', 'account.asset.revaluation')]")

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id,
                                   copy=False,
                                   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'account.asset.revaluation')]")

    state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type', store=True)

    is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
    next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
    history_line_ids = fields.One2many('dynamic.flow.history', 'revaluation_id', 'Урсгалын түүхүүд')
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
                               string='Төлөв stage', store=True)
    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
    # flow_line_next_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    # flow_line_back_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)


    
    branch_id = fields.Many2one('res.branch', 'Салбар', tracking=True)

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    deduction_reval_asset_account_id = fields.Many2one('account.account', 'Deducaiton account')
    addition_reval_asset_account_id = fields.Many2one('account.account', 'Addition account')

    type = fields.Selection([('value', 'Анхны өртөг'),
                              ('value_residual', 'Үлдэгдэл өртөг'),], 'Төрөл', default='value', tracking=True)
    
    flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
    flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)

    @api.depends('flow_id')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'account.asset.revaluation')])
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

    def flow_find(self, domain=None, order='sequence'):
        if domain is None:
            domain = []
        if self.flow_id:
            domain.append(('flow_id', '=', self.flow_id.id))
        domain.append(('flow_id.model_id.model', '=', 'account.asset.revaluation'))
        return self.env['dynamic.flow.line'].search(domain, order=order, limit=1).id

    @api.depends('flow_line_next_id.state_type')
    def _compute_next_state_type(self):
        for item in self:
            item.next_state_type = item.flow_line_next_id.state_type

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
                    self.action_revaluation()

                self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'revaluation_id', self)
                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(self.branch_id, False)
                    if send_users:
                        self.send_chat_employee(send_users.mapped('partner_id'))
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
                self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'revaluation_id', self)
            else:
                raise UserError(_('You are not back user'))

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
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'revaluation_id', self)
        else:
            raise UserError(_('You are not cancel user'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'revaluation_id', self)
        else:
            raise UserError(_('You are not draft user'))
#         
    @api.onchange('description')
    def _onchange_description(self):
        for line in self.line_ids:
            line.description = self.description

    @api.model
    def default_get(self, default_fields):
        # Хөрөнгүүдийг олноор нь сонгон шилжүүлэх үед мөр бүрт мэдээллийг оруулах
        res = super(AccountAssetRevaluation, self).default_get(default_fields)
        context = dict(self._context or {})
        vals = []
        if context.get('active_model') == 'account.asset' and context.get('active_ids'):
            assets = self.env[context.get('active_model')].browse(context.get('active_ids'))
            for asset in assets:
                if asset.state == 'open':
                    line = [0, False, {'asset_id': asset.id,
                                       'state': 'draft',
                                       'code': asset.code,
                                       # 'manufactured_date': asset.manufactured_date,
                                       # 'commissioned_date': asset.commissioned_date,
                                       'old_method_period': asset.method_period,
                                       'old_method_number': asset.method_number,
                                       'value': asset.original_value,
                                       'value_depreciated': asset.original_value-asset.book_value,
                                       'value_residual': asset.book_value,
                                       'method_number': asset.method_number,
                                       'method_period': asset.method_period,
                                       }]
                    vals.append(line)
        res.update({'line_ids': vals})
        return res

    @api.model
    def create(self, values):
        # Нэрийг автомат дугаарлана
        res = super(AccountAssetRevaluation, self).create(values)
        if res.name == '/':
            res.write({'name': self.env['ir.sequence'].next_by_code('account.asset.revaluation')})
        return res

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй шилжилтийг л устгадаг байна
        for revaluation in self:
            if revaluation.state != 'draft':
                raise UserError(_('You cannot delete an asset revaluation which is not draft.'))
        return super(AccountAssetRevaluation, self).unlink()

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

    def action_send(self):
        # Шилжилт хөдөлгөөн илгээх
        for revaluation in self:
            employee = self.env['hr.employee'].search([('user_id', '=', self._uid)])
            if not employee:
                raise UserError(_("Can't find any related employee for your user. Only employee can create of asset revaluation."))
            workflow = self.env['workflow.config'].get_workflow('employee', 'account.asset.revaluation', employee.id, None)
            if not workflow:
                raise UserError(_('There is no workflow defined!'))
            revaluation.workflow_id = workflow
            if workflow:
                # Мөр байгаа эсэхийн шалгаж байна
                if revaluation.line_ids:
                    success, current_sequence = self.env['workflow.config'].send('account.asset.revaluation.workflow.history', 'revaluation_id', revaluation, self._uid)
                    if success:
                        revaluation.line_ids.send_button()
                        revaluation.check_sequence = current_sequence
                        revaluation.state = 'waiting'
                else:
                    raise UserError(_("You cannot revaluation without line."))

    def action_approve(self):
        # Шилжилт хөдөлгөөнийг батална
        for revaluation in self:
            if revaluation.workflow_id:
                success, sub_success, current_sequence = self.env['workflow.config'].approve('account.asset.revaluation.workflow.history', 'revaluation_id', revaluation, self._uid)
                if success:
                    if sub_success:
                        revaluation.line_ids.approve_button()
                        revaluation.state = 'approved'
                    else:
                        revaluation.check_sequence = current_sequence

    def action_revaluation(self):
        self.line_ids.revaluation_button()
        self.write({'state': 'revaluation'})

    def action_cancel(self):
        # Хүлээн авсан үндсэн хөрөнгийг цуцлах үед тухайн хөрөнгөнд ямарваа ажил гүйлгээ үүссэн байвал дагаж устгах
        context = dict(self._context or {})
        context['asset_move'] = True
        if self.workflow_id:
            success = self.env['workflow.config'].reject('account.asset.revaluation.workflow.history', 'revaluation_id', self, self._uid)
            if success:
                self.line_ids.with_context(context).cancel_button()
                self.write({'state': 'cancel'})
        else:
            self.line_ids.with_context(context).cancel_button()
            self.write({'state': 'cancel'})

    def action_draft(self):
        # Цуцлагдсан төлөвтэй шилжих хөдөлгөөнийг Ноорог болгох
        self.line_ids.draft_button()
        return self.write({'state': 'draft', 'check_sequence': 0, 'workflow_id': False})


class AccountAssetRevaluationLine(models.Model):
    _name = "account.asset.revaluation.line"
    _description = "Revaluation Asset Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    asset_id = fields.Many2one('account.asset', 'Asset', required=True, domain = [('state', '!=', 'model')])
    code = fields.Char(string='Asset Code', size=32, readonly=True)
    type = fields.Selection([('invoice_line', 'revaluation with an Invoice Line'),
                             ('account', 'revaluation with an Account')], string='revaluation Type', required=True, default='account')
    # asset_state = fields.Selection( string='Asset State')
    manufactured_date = fields.Date(string='Manufactured Date')
    commissioned_date = fields.Date(string='Commissioned Date')
    old_method_number = fields.Integer(string='Old Number of Depreciations', required=True)
    old_method_period = fields.Integer(string='Old Period Length')
    value = fields.Float(string='Value')
    value_depreciated = fields.Float(string='Depreciated Value')
    value_residual = fields.Float(string='Residual Value')
    type = fields.Selection([('gross_amount', 'Revaluation for Gross Amount'),
                             ('depreciation_amount', 'Revaluation for Depreciated Amount')], 'Revaluation Method', default='gross_amount', required=True)
    revaluation_amount = fields.Float('Revaluation Amount', help='If you want to increase asset value then set revaluation amount on this field')
    difference = fields.Float('Difference Amount')
    method_number = fields.Integer(string='Number of Depreciations', required=True)
    method_period = fields.Integer(string='Period Length')
    date = fields.Date(string='Revaluation Date', related='revaluation_id.date')
    description = fields.Char('Description')
    move_id = fields.Many2one('account.move', 'Revaluation Account Move')
    revaluation_id = fields.Many2one('account.asset.revaluation', 'Revaluation Asset', ondelete='cascade')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('revaluation', 'Revaluation'),
                              ('cancel', 'Cancelled')], 'State', default='draft', tracking=True)

    @api.onchange('asset_id')
    def onchange_asset(self):
        if self.asset_id:
            self.code = self.asset_id.code
            # self.manufactured_date = self.asset_id.manufactured_date
            # self.commissioned_date = self.asset_id.commissioned_date
            self.old_method_number = self.asset_id.method_number
            self.old_method_period = self.asset_id.method_period
            self.value = self.asset_id.original_value
            self.value_depreciated = self.asset_id.original_value - self.asset_id.book_value #self.asset_id.value_depreciated
            self.value_residual = self.asset_id.book_value
            self.method_number = self.asset_id.method_number
            self.method_period = self.asset_id.method_period

    @api.model
    def default_get(self, fields):
        res = super(AccountAssetRevaluationLine, self).default_get(fields)
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
                # 'commissioned_date': asset.commissioned_date,
                'value': asset.original_value,
                'value_depreciated': asset.original_value-asset.book_value,
                'value_residual': asset.book_value,
                'old_method_period': asset.method_period,
                'old_method_number': asset.method_number,
            })
        return super(AccountAssetRevaluationLine, self).create(values)

    def write(self, values):
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'code': asset.code,
                # 'manufactured_date': asset.manufactured_date,
                # 'commissioned_date': asset.commissioned_date,
                'value': asset.original_value,
                'value_depreciated': asset.original_value-asset.book_value,
                'value_residual': asset.book_value,
                'old_method_period': asset.method_period,
                'old_method_number': asset.method_number,
            })
        return super(AccountAssetRevaluationLine, self).write(values)

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй мөрийг л устгадаг байна
        for line in self:
            if line.state != 'draft':
                raise UserError(_('You cannot delete an asset revaluation line which is not draft.'))
        return super(AccountAssetRevaluationLine, self).unlink()

    def get_check(self, asset):
        if self.revaluation_amount < 0:
            raise UserError(_('Revaluation amount less than 0!'))
        if self.revaluation_amount == asset.original_value:
            raise UserError(_('Revaluation amount may not equal %s asset value!' % asset.name))
        asset.search_and_raise_line(self.date)
        if asset.state != 'open':
            raise UserError(_("%s asset state is not open. Only can revaluation assets with open state!" % asset.name))
        history_ids = asset.history_ids.sorted(key=lambda l: l.date)
        if history_ids and history_ids[-1].date:
            history_date = history_ids[-1].date
            if history_date > self.date:
                raise UserError(_("You cannot line. %s revaluationized %s after." % (asset.name, self.date)))
            elif history_date == self.date:
                raise UserError(_("Depreciation cannot be changed more than once a day."))
        before_revaluation = self.search([('asset_id', '=', asset.id), ('id', '!=', self.id)], order='date desc, id desc')
        if before_revaluation and before_revaluation[-1].date:
            history_date = before_revaluation[-1].date
            if history_date > self.date:
                raise UserError(_("You cannot line. %s revaluationized %s after." % (asset.name, self.date)))
            elif history_date == self.date:
                raise UserError(_("Depreciation cannot be changed more than once a day."))

    def send_button(self):
        for line in self:
            asset = line.asset_id
            line.asset_id.search_and_raise_line(line.revaluation_id.date)
            line.get_check(asset)
        self.write({'state': 'waiting'})

    def approve_button(self):
        self.write({'state': 'approved'})

    def revaluation_button(self):
        # Капиталжуулах
        move_obj = self.env['account.move']
        for line in self:
            line_ids = []
            asset = line.asset_id
            current_currency = asset.currency_id or asset.company_id.currency_id
            line.get_check(asset)
            old_values = {'value': asset.original_value,
                          'method_number': asset.method_number,
                          'method_period': asset.method_period
                          }
            asset.write({'method_number': line.method_number,
                         'method_period': line.method_period
                         })
            move_date = line.date
            unposted_depreciation_line_ids = asset.depreciation_line_ids.filtered(lambda x: not x.move_check).sorted(key=lambda l: l.depreciation_date)
            if unposted_depreciation_line_ids and unposted_depreciation_line_ids[0].depreciation_date == line.date:
                # Хэрвээ капиталжуулах / дахин үнэлэх огноо элэгдлийн самбарын элэгдээгүй эхний мөрийн элэгдэх огноотой тэнцүү байвал тухайн элэгдлийг батална
                unposted_depreciation_line_ids[0].create_move()
                move_date += relativedelta(days=1)
            dt_account = kt_account = False
            asset_value = line.revaluation_amount
            diff_depreciate = (asset.original_value-asset.book_value) / asset.original_value * line.revaluation_amount - (asset.original_value-asset.book_value)
            name = _('%s revaluation: %s' % (asset.name, line.revaluation_id.transaction))
            if line.type == 'gross_amount' and line.revaluation_amount != asset.original_value:
                if line.revaluation_amount > asset.original_value:
                    if not line.revaluation_id.addition_reval_asset_account_id:
                        raise UserError(_('Configure addition account of asset revaluation on %s company!' % asset.company_id.name))
                    dt_account = asset.account_asset_id
                    kt_account = line.revaluation_id.addition_reval_asset_account_id
                else:
                    if not line.revaluation_id.deduction_reval_asset_account_id:
                        raise UserError(_('Configure deduction account of asset revaluation on %s company!' % asset.company_id.name))
                    dt_account = line.revaluation_id.deduction_reval_asset_account_id
                    kt_account = asset.account_asset_id
            if line.type == 'depreciation_amount' and diff_depreciate != 0:
                if diff_depreciate > 0:
                    dt_account = line.revaluation_id.deduction_reval_asset_account_id
                    kt_account = asset.account_depreciation_id
                else:
                    dt_account = asset.account_depreciation_expense_id
                    kt_account = line.revaluation_id.addition_reval_asset_account_id
            if dt_account and kt_account:
                amount = current_currency._convert(line.revaluation_amount - asset.original_value, asset.company_id.currency_id, asset.company_id, line.date, round=False)
                # Дт талын журналын мөр
                line_ids.append(asset._get_line_vals(name, dt_account.id, False, abs(amount), abs(line.revaluation_amount - asset.original_value), current_currency, line.date))
                # Кт талын журналын мөр
                line_ids.append(asset._get_line_vals(name, kt_account.id, False, -abs(amount), -abs(line.revaluation_amount - asset.original_value), current_currency, line.date))
                journal_id = asset.journal_id.id
#                 if asset.company_id.asset_journal_settings == 'intersperse':
#                     if not asset.company_id.revaluation_asset_journal_id:
#                         raise UserError(_('Configure revaluation journal of asset in %s company!' % asset.company_id.name))
#                     journal_id = asset.company_id.revaluation_asset_journal_id.id
                move_vals = {'date': line.date,
                             'ref': name,
                             'journal_id': journal_id,
                             'line_ids': line_ids,
                             }
                move_id = move_obj.create(move_vals)
                if asset.category_id.open_asset:
                    move_id.action_post()
                revaluation_value = asset.revaluation_value + amount
                if line.revaluation_amount == 0:
                    # Хэрэв дахин үнэлгээний дүн 0 бол
                    amount = -asset.book_value
                    revaluation_value = -asset.book_value
                    asset_value = asset.original_value - asset.book_value
                elif line.revaluation_amount < (asset.original_value-asset.book_value):
                    # Хэрэв дахин үнэлгээний дүн 0 элэгдсэн дүнгээс бага бол
                    amount = -asset.book_value + line.revaluation_amount
                    revaluation_value = -asset.book_value + line.revaluation_amount
                    asset_value = asset.original_value - asset.book_value + line.revaluation_amount
                asset.with_context(date=move_date, modify=True, amount=amount).compute_depreciation_board()
                if line.revaluation_id.type=='value':
                    asset.write({'value': asset_value, 'revaluation_value': revaluation_value})
                tracked_fields = self.env['account.asset'].fields_get(['value', 'method_number', 'method_period'])
#                 changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
#                 if changes:
#                     asset.message_post(subject=_('Depreciation board modified'), body=line.revaluation_id.name, tracking_value_ids=tracking_value_ids)
                line.write({'state': 'revaluation', 'move_id': move_id, 'difference': amount})
            else:
                raise UserError(_('Revaluation amount may not equal %s asset value!' % asset.name))
        return True

    def draft_button(self):
        self.write({'state': 'draft'})

    def cancel_button(self):
        for line in self:
            asset = line.asset_id
            asset.check_cancel(line, 'revaluation')
            if line.move_id:
                line.move_id.button_cancel()
                line.move_id.with_context(asset_unlink=True, force_delete=True).unlink()
            dep_line = asset.depreciation_line_ids.filtered(lambda x: x.depreciation_date == line.date and x.split_check)
            dep_line.with_context(delete=True).cancel_move()
            if len(dep_line) == 0:
                #  Сарын сүүлийн өдрөөр элэгдэх бол
                depreciation_date = line.date
                if asset.date_first_depreciation == 'last_day_period':
                    month_days = calendar.monthrange(depreciation_date.year, depreciation_date.month)[1]
                    depreciation_date = depreciation_date.replace(day=month_days)
                dep_line = asset.depreciation_line_ids.filtered(lambda x: x.depreciation_date == depreciation_date and x.split_check)
                dep_line.with_context(delete=True).cancel_move()
            value = asset.original_value
            revaluation_value = asset.revaluation_value - (line.revaluation_amount - line.value)
            if line.revaluation_amount == 0 or line.revaluation_amount < (asset.original_value-asset.book_value):
                revaluation_value = asset.revaluation_value - line.difference
            asset.write({'method_number': line.old_method_number,
                         'method_period': line.old_method_period,
                         'value': line.value,
                         'revaluation_value': revaluation_value,
                         })
            asset.message_post(body=_("Canceled revaluation. Value: %s -- %s") % (value, asset.original_value))
            line.asset_id.compute_depreciation_board()
        self.write({'state': 'cancel'})

