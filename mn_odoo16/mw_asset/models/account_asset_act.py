# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountAssetAct(models.Model):
    _name = "account.asset.act"
    _inherit = 'mail.thread'
    _description = "Act Asset"

    def _asset_count(self):
        for act in self:
            act.asset_count = len(act.line_ids) or 0

    def _compute_is_creator(self):
        for act in self:
            if act.create_uid == self.env.user:
                act.is_creator = True
            else:
                act.is_creator = False


    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = [('model_id.model', '=', 'account.asset.act'),
#                          ('branch_ids', 'in', [self.env.user.branch_id.id])
                         ]
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    name = fields.Char('Reference', default='/', copy=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    transaction = fields.Char('Transaction', required=True)
    account_id = fields.Many2one('account.account', 'Act Account', domain=[('deprecated', '=', False)], )
    description = fields.Text('Description')
    date = fields.Date(default=fields.Date.context_today, string='Act Date', tracking=True)
    asset_id = fields.Many2one('account.asset', related='line_ids.asset_id', string='Asset', readonly=False)
    asset_count = fields.Integer(compute='_asset_count', string='# Assets')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('act', 'Acted'),
                              ('cancel', 'Cancelled')], 'State', default='draft', tracking=True)
    line_ids = fields.One2many('account.asset.act.line', 'act_id', 'Assets', copy=False)
    workflow_id = fields.Many2one('workflow.config', 'Workflow', copy=False)
    check_sequence = fields.Integer('Workflow Step', default=0, copy=False)
    is_partial_act = fields.Boolean('Is Partial Act', default=False)
    is_creator = fields.Boolean(compute='_compute_is_creator')
    act_type = fields.Selection([('act', 'Актласан'),
                              ('donate', 'Хандивласан'),
                              ('other', 'Бусад зарлага'),
                              ('free', 'Үнэгүй өгсөн')], 'Хаалтын төрөл', tracking=True, required=True)

    #flow
    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
                              default=_get_default_flow_id,
                              copy=True, required=True, domain="[('model_id.model', '=', 'account.asset.act')]")

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id,
                                   copy=False,
                                   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'account.asset.act')]")

    state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type', store=True)

    is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
    flow_line_next_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
    flow_line_back_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    history_line_ids = fields.One2many('dynamic.flow.history', 'asset_act_id', 'Урсгалын түүхүүд')
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
                               string='Төлөв stage', store=True)
    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
    
    branch_id = fields.Many2one('res.branch', 'Салбар', tracking=True)

    @api.depends('flow_id', 'visible_flow_line_ids', 'flow_line_id')
    def _compute_flow_line_id(self):
        for item in self:
            item.flow_line_next_id = item.flow_line_id._get_next_flow_line(item.visible_flow_line_ids)
            item.flow_line_back_id = item.flow_line_id._get_back_flow_line(item.visible_flow_line_ids)


    @api.depends('flow_id')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'account.asset.act')])
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
        domain.append(('flow_id.model_id.model', '=', 'account.asset.act'))
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
                    self.action_act()

                self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'asset_act_id', self)
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
                self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'asset_act_id', self)
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
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'asset_act_id', self)
        else:
            raise UserError(_('You are not cancel user'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'asset_act_id', self)
        else:
            raise UserError(_('You are not draft user'))
#         

    @api.onchange('description')
    def _onchange_description(self):
        for line in self.line_ids:
            line.description = self.description

    @api.onchange('account_id')
    def onchange_account_id(self):
        for line in self.line_ids:
            line.account_id = self.account_id

    @api.model
    def default_get(self, default_fields):
        # Хөрөнгүүдийг олноор нь сонгон шилжүүлэх үед мөр бүрт мэдээллийг оруулах
        res = super(AccountAssetAct, self).default_get(default_fields)
        context = dict(self._context or {})
        vals = []
        if context.get('active_model') == 'account.asset' and context.get('active_ids'):
            assets = self.env[context.get('active_model')].browse(context.get('active_ids'))
            for asset in assets:
                if asset.state == 'open' :
                    line = [0, False, {'asset_id': asset.id,
                                       'state': 'draft',
                                    #    'code': asset.code,
                                    #    'manufactured_date': asset.manufactured_date,
                                    #    'commissioned_date': asset.commissioned_date,
                                    #    'value': asset.value,
                                    #    'value_depreciated': asset.value_depreciated,
                                    #    'value_residual': asset.value_residual}
                                        'code': asset.code,
                                        # 'manufactured_date': asset.manufactured_date,
                                        'commissioned_date': asset.acquisition_date,
                                        'value': asset.original_value,
                                        # 'value_depreciated': asset.value_depreciated,
                                        'value_residual': asset.book_value,}]
                    vals.append(line)
        res.update({'line_ids': vals})
        return res

    @api.model
    def create(self, values):
        # Нэрийг автомат дугаарлана
        
        res = super(AccountAssetAct, self).create(values)
        if res.name == '/':
            res.write({'name': self.env['ir.sequence'].next_by_code('account.asset.act')})
        return res

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй шилжилтийг л устгадаг байна
        for act in self:
            if act.state != 'draft':
                raise UserError(_('You cannot delete an asset act which is not draft.'))
        return super(AccountAssetAct, self).unlink()

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
        for act in self:
            employee = self.env['hr.employee'].search([('user_id', '=', self._uid)])
            if not employee:
                raise UserError(_("Can't find any related employee for your user. Only employee can create of asset act."))
            workflow = self.env['workflow.config'].get_workflow('employee', 'account.asset.act', employee.id, None)
            if not workflow:
                raise UserError(_('There is no workflow defined!'))
            act.workflow_id = workflow
            if workflow:
                # Мөр байгаа эсэхийн шалгаж байна
                if act.line_ids:
                    success, current_sequence = self.env['workflow.config'].send('account.asset.act.workflow.history', 'act_id', act, self._uid)
                    if success:
                        act.line_ids.send_button()
                        act.check_sequence = current_sequence
                        act.state = 'waiting'
                else:
                    raise UserError(_("You cannot receipt without line asset act."))

    def action_approve(self):
        # Шилжилт хөдөлгөөнийг батална
        for act in self:
            if act.workflow_id:
                success, sub_success, current_sequence = self.env['workflow.config'].approve('account.asset.act.workflow.history', 'act_id', act, self._uid)
                if success:
                    if sub_success:
                        act.line_ids.approve_button()
                        act.state = 'approved'
                    else:
                        act.check_sequence = current_sequence

    def action_act(self):
        self.line_ids.act_button()
        self.write({'state': 'act'})

    def action_cancel(self):
        # Хүлээн авсан үндсэн хөрөнгийг цуцлах үед тухайн хөрөнгөнд ямарваа ажил гүйлгээ үүссэн байвал дагаж устгах
        context = dict(self._context or {})
        context['asset_move'] = True
        if self.workflow_id:
            success = self.env['workflow.config'].reject('account.asset.act.workflow.history', 'act_id', self, self._uid)
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


class AccountAssetActLine(models.Model):
    _name = "account.asset.act.line"
    _description = "Act Asset Line"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    asset_id = fields.Many2one('account.asset', 'Asset', required=True)
    code = fields.Char(string='Asset Code', size=32, readonly=True)
    account_id = fields.Many2one('account.account', 'Act Account', required=True, domain=[('deprecated', '=', False)])
    asset_state = fields.Selection(related='asset_id.state', string='Asset State')
    manufactured_date = fields.Date(string='Manufactured Date')
    commissioned_date = fields.Date(string='Commissioned Date')
    value = fields.Float(string='Value')
    value_depreciated = fields.Float(string='Depreciated Value')
    value_residual = fields.Float(string='Residual Value')
    is_partial_act = fields.Boolean(string='Is Partial Act', related='act_id.is_partial_act')
    partial_act_amount = fields.Float(string='Amount Act Partly', digits=(16, 2))
    acted_part_residual = fields.Float(string='Residual Cost for Acted Part', digits=(16, 2))
    date = fields.Date(string='Act Date', related='act_id.date')
    description = fields.Char('Description')
    move_id = fields.Many2one('account.move', 'Act Account Move')
    act_id = fields.Many2one('account.asset.act', 'Act Asset', ondelete='cascade')
    # close_state = fields.Selection(related='asset_id.close_state', string='Remove Status')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('act', 'Acted'),
                              ('cancel', 'Cancelled')], 'State', default='draft', tracking=True)

    @api.onchange('asset_id')
    def onchange_asset(self):
        if self.asset_id:
            self.code = self.asset_id.code
            # self.manufactured_date = self.asset_id.manufactured_date
            self.commissioned_date = self.asset_id.acquisition_date
            self.value = self.asset_id.original_value
            self.value_depreciated = self.asset_id.initial_value
            self.value_residual = self.asset_id.book_value
            self.is_partial_act = False
            # self.acted_part_residual = 0
            # self.partial_act_amount = 0

    @api.onchange('partial_act_amount')
    def onchange_partial_act_amount(self):
        if not self.is_partial_act:
            self.acted_part_residual = 0
            self.partial_act_amount = 0
        if not self.asset_id:
            return 0
        if self.partial_act_amount >= self.asset_id.value:
            raise ValidationError(_('Amount act partly must be less than value of asset'))
        if self.is_partial_act:
            if self.asset_id.value != 0:
                self.acted_part_residual = self.asset_id.salvage_value * self.partial_act_amount / self.asset_id.value
            else:
                self.acted_part_residual = 0

    # @api.onchange('is_partial_act')
    # def onchange_is_partial_act(self):
    #     if not self.is_partial_act:
    #         self.acted_part_residual = 0
    #         self.partial_act_amount = 0
    #     if not self.asset_id:
    #         return 0
    #     if self.partial_act_amount >= self.asset_id.value:
    #         raise ValidationError(_('Amount act partly must be less than value of asset'))
    #     if self.is_partial_act:
    #         if self.asset_id.value != 0:
    #             self.acted_part_residual = self.asset_id.salvage_value * self.partial_act_amount / self.asset_id.value
    #         else:
    #             self.acted_part_residual = 0

    @api.model
    def default_get(self, fields):
        res = super(AccountAssetActLine, self).default_get(fields)
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
            if 'is_partial_act' in values and values['is_partial_act'] and 'partial_act_amount' in values and values['partial_act_amount'] >= asset.value:
                raise ValidationError(_('Amount act partly must be less than value of asset'))
            values.update({
                'code': asset.code,
                # 'manufactured_date': asset.manufactured_date,
                'commissioned_date': asset.acquisition_date,
                'value': asset.original_value,
                # 'value_depreciated': asset.value_depreciated,
                'value_residual': asset.book_value,
            })
            # asset.write({'close_state': 'draft'})
        return super(AccountAssetActLine, self).create(values)

    def write(self, values):
        asset = self.asset_id
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'code': asset.code,
                # 'manufactured_date': asset.manufactured_date,
                'commissioned_date': asset.acquisition_date,
                'value': asset.original_value,
                # 'value_depreciated': asset.value_depreciated,
                'value_residual': asset.book_value,
            })
        partial_act = values['is_partial_act'] if 'is_partial_act' in values else self.is_partial_act
        partial_act_amount = values['partial_act_amount'] if 'partial_act_amount' in values else self.partial_act_amount
        if partial_act and partial_act_amount >= asset.value:
            raise ValidationError(_('Amount act partly must be less than value of asset'))
        return super(AccountAssetActLine, self).write(values)

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй мөрийг л устгадаг байна
        for line in self:
            if line.state != 'draft':
                raise UserError(_('You cannot delete an asset act line which is not draft.'))
            # line.asset_id.write({'close_state': 'not_exc'})
        return super(AccountAssetActLine, self).unlink()

    def send_button(self):
        for line in self:
            line.asset_id.search_and_raise_line(line.act_id.date)
            # line.asset_id.write({'close_state': 'sent'})
        self.write({'state': 'waiting'})

    def approve_button(self):
        for line in self:
            line.asset_id.write({'close_state': 'acting'})
        self.write({'state': 'approved'})

    def get_asset_vals(self, vals):
        return vals

    def act_button(self):
        for line in self:
            self.env['asset.modify'].create({'asset_id': line.asset_id.id, 'name': line.act_id.name, 'modify_action':'dispose','loss_account_id': line.act_id.account_id.id, 'date': line.act_id.date}).sell_dispose()
        return True

    def draft_button(self):
        for line in self:
            line.asset_id.write({'close_state': 'draft'})
        self.write({'state': 'draft'})

    def cancel_button(self):
        for line in self:
            context = dict(self._context or {})
            context.update({'partial_act': line.is_partial_act,
                            'partial_act_amount': line.partial_act_amount})
            line.asset_id.with_context(context).set_to_open()
            line.asset_id.write({'close_state': 'cancel'})
        self.write({'state': 'cancel'})

    def act_line_report(self):
        return self.env.ref('l10n_mn_account_asset.asset_act_line_report_action').report_action(self)


class AccountAssetActWorkflowHistory(models.Model):
    _name = 'account.asset.act.workflow.history'
    _description = 'Act Asset Move Workflow History'
    _order = 'act_id, sent_date'

    STATE_SELECTION = [('waiting', 'Waiting'),
                       ('confirmed', 'Confirmed'),
                       ('approved', 'Approved'),
                       ('rejected', 'Cancelled')]

    act_id = fields.Many2one('account.asset.act', 'Act Asset', readonly=True, ondelete='cascade')
    line_sequence = fields.Integer('Workflow Step')
    name = fields.Char('Verification Step', readonly=True)
    user_ids = fields.Many2many('res.users', 'res_users_asset_act_history_ref', 'asset_history_id', 'user_id', 'Validators')
    sent_date = fields.Datetime('Sent Date', required=True, readonly=True)
    user_id = fields.Many2one('res.users', 'Validator', readonly=True)
    action_date = fields.Datetime('Action Date', readonly=True)
    action = fields.Selection(STATE_SELECTION, 'Action', readonly=True)