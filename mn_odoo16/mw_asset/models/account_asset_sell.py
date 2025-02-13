# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AccountAssetSell(models.Model):
    _name = 'account.asset.sell'
    _inherit = 'mail.thread'
    _description = 'Sell Asset'

    def _asset_count(self):
        for sell in self:
            sell.asset_count = len(sell.line_ids) or 0

    def _compute_is_creator(self):
        for sell in self:
            if sell.create_uid == self.env.user:
                sell.is_creator = True
            else:
                sell.is_creator = False

    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = [('model_id.model', '=', 'account.asset.sell'),
#                          ('branch_ids', 'in', [self.env.user.branch_id.id])
                         ]
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    name = fields.Char('Reference', default='/', copy=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    transaction = fields.Char('Transaction', required=True)
    description = fields.Text('Description')
    partner_id = fields.Many2one('res.partner', 'Partner', required=True, tracking=True)
    journal_id = fields.Many2one('account.journal', 'Sell Journal', required=True, domain=[('type', '=', 'sale')], tracking=True)
    invoice_id = fields.Many2one('account.move', 'Invoice')
    tax_id = fields.Many2one('account.tax', domain=[('type_tax_use', '=', 'sale')], string='Sell Tax', tracking=True)
    date = fields.Date(string='Sell Date', default=fields.Date.context_today, required=True, tracking=True)
    line_ids = fields.One2many('account.asset.sell.line', 'sell_id', 'Sell Asset', copy=False)
    asset_id = fields.Many2one('account.asset', related='line_ids.asset_id', string='Asset', readonly=False)
    asset_count = fields.Integer(compute='_asset_count', string='# Assets')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('sale', 'Sale'),
                              ('cancel', 'Cancelled')], 'State', default='draft', tracking=True)
    check_sequence = fields.Integer('Workflow Step', default=0, copy=False)
    is_partial_sell = fields.Boolean('Is Partial Sell', default=False)
    is_creator = fields.Boolean(compute='_compute_is_creator')
    entry_count = fields.Integer(compute='_entry_count', string='# Asset Entries')

 
    #flow
    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
                              default=_get_default_flow_id,
                              copy=True, required=True, domain="[('model_id.model', '=', 'account.asset.sell')]")

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id,
                                   copy=False,
                                   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'account.asset.sell')]")

    state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type', store=True)

    is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
    flow_line_next_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    flow_line_back_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
    history_line_ids = fields.One2many('dynamic.flow.history', 'asset_sell_id', 'Урсгалын түүхүүд')
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
                               string='Төлөв stage', store=True)
    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
    
    branch_id = fields.Many2one('res.branch', 'Салбар', tracking=True)

    gain_asset_account_id = fields.Many2one('account.account', string="Gain Account of Asset")
    loss_asset_account_id = fields.Many2one('account.account', string="Loss Account of Asset")
    moving_asset_account_id = fields.Many2one('account.account', string="Түр данс")

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
    def open_entries(self):
        move_ids = []
        for asset in self:
            # for line_id in asset:
            if asset.invoice_id:
                move_ids.append(asset.invoice_id.id)
            # if line_id.invoice_id:
            #     move_ids.append(line_id.invoice_id.id)
        return {
            'name': _('Journal Entries'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', move_ids)],
        }
    @api.depends('line_ids.move_id', 'line_ids.invoice_id')
    def _entry_count(self):
        for asset in self:
            move_ids = []
        for asset in self:
            # for line_id in asset:
            if asset.invoice_id:
                move_ids.append(asset.invoice_id.id)
            res = self.env['account.move'].search_count([('id', '=', (move_ids))])
            asset.entry_count = res or 0
    @api.depends('flow_id')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'account.asset.sell')])
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
        domain.append(('flow_id.model_id.model', '=', 'account.asset.sell'))
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
                    self.action_sell()

                self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'asset_sell_id', self)
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
                self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'asset_sell_id', self)
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
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'asset_sell_id', self)
        else:
            raise UserError(_('You are not cancel user'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'asset_sell_id', self)
        else:
            raise UserError(_('You are not draft user'))
#         
    @api.onchange('tax_id')
    def onchange_tax_id(self):
        for line in self.line_ids:
            line.tax_id = self.tax_id

    @api.onchange('description')
    def _onchange_description(self):
        for line in self.line_ids:
            line.description = self.description

    @api.model
    def default_get(self, default_fields):
        # Хөрөнгүүдийг олноор нь сонгон боловсруулах үед мөр бүрт мэдээллийг оруулах
        res = super(AccountAssetSell, self).default_get(default_fields)
        context = dict(self._context or {})
        move_vals = []
        if context.get('active_model') == 'account.asset.asset' and context.get('active_ids'):
            assets = self.env[context.get('active_model')].browse(context.get('active_ids'))
            for asset in assets:
                if asset.state == 'open':
                    move_vals.append((0, False, {'asset_id': asset.id,
                                                 'code': asset.code,
                                                 'manufactured_date': asset.manufactured_date,
                                                 'commissioned_date': asset.commissioned_date,
                                                 'value': asset.value,
                                                 'value_depreciated': asset.value_depreciated,
                                                 'value_residual': asset.value_residual,
                                                 'sell_value': asset.value_residual,
                                                 'product_id':False}))
        res.update({'line_ids': move_vals})
        return res

    @api.model
    def create(self, values):
        # Нэрийг автомат дугаарлана
        res = super(AccountAssetSell, self).create(values)
        if res.name == '/':
            res.write({'name': self.env['ir.sequence'].next_by_code('account.asset.sell')})
        return res

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй шилжилтийг л устгадаг байна
        for sell in self:
            if sell.state != 'draft':
                raise UserError(_('You cannot delete an asset sell which is not draft.'))
        return super(AccountAssetSell, self).unlink()

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
        for sell in self:
            employee = self.env['hr.employee'].search([('user_id', '=', self._uid)])
            if not employee:
                raise UserError(_("Can't find any related employee for your user. Only employee can create of asset sell."))
            workflow = self.env['workflow.config'].get_workflow('employee', 'account.asset.sell', employee.id, None)
            if not workflow:
                raise UserError(_('There is no workflow defined!'))
            sell.workflow_id = workflow
            if workflow:
                # Мөр байгаа эсэхийн шалгаж байна
                if sell.line_ids:
                    success, current_sequence = self.env['workflow.config'].send('account.asset.sell.workflow.history', 'sell_id', sell, self._uid)
                    if success:
                        sell.line_ids.send_button()
                        sell.check_sequence = current_sequence
                        sell.state = 'waiting'
                else:
                    raise UserError(_("You cannot receipt without line asset sell."))

    def action_approve(self):
        # Шилжилт хөдөлгөөнийг батална
        for sell in self:
            if sell.workflow_id:
                success, sub_success, current_sequence = self.env['workflow.config'].approve('account.asset.sell.workflow.history', 'sell_id', sell, self._uid)
                if success:
                    if sub_success:
                        sell.line_ids.approve_button()
                        sell.state = 'approved'
                    else:
                        sell.check_sequence = current_sequence

    def action_sell(self):
        # Хөрөнгө борлуулах
        move_obj = self.env['account.move']
        for sell in self:
            # if not sell.loss_asset_account_id:
            #     raise UserError(_("Гарзын данс сонгоно уу %s !" % sell.name))
            if not sell.gain_asset_account_id:
                raise UserError(_("Орлогын данс сонгоно уу %s!") % sell.name)
            # if not sell.moving_asset_account_id:
            #     raise UserError(_("Configure moving account of sell asset in %s company!") % sell.company_id.name)
            line_vals = sell.line_ids.get_invoice_line()
            invoice_vals = {'partner_id': sell.partner_id.id,
                            'ref': _('%s: %s sell' % (sell.name, sell.date)),
                            'date': sell.date,
                            'invoice_date': sell.date,
                            'move_type': 'out_invoice',
                            'invoice_user_id': self.env.uid,
                            'company_id': self.env.company.id,
                            'currency_id': self.env.company.currency_id.id,
                            'journal_id': sell.journal_id.id,
                            'invoice_line_ids': line_vals
                            }
            invoice_id = move_obj.create(invoice_vals)
            # Нэхэмжлэхийг баталж холбоотой журналын бичилт үүсэх
            # invoice_id.action_post()
            print('invoice_idinvoice_idinvoice_idinvoice_id',invoice_id)
            sell.line_ids.sell_modify(invoice_id)
            sell.invoice_id = invoice_id.id
            # print(m)
            invoice_id.action_post()
            self.write({'state': 'sale'})

    def action_cancel(self):
        # Үндсэн хөрөнгийн Борлуулалтыг цуцлах үед тухайн хөрөнгөнд ямарваа ажил гүйлгээ үүссэн байвал дагаж устгах
        context = dict(self._context or {})
        context['asset_move'] = True
        if self.workflow_id:
            success = self.env['workflow.config'].reject('account.asset.sell.workflow.history', 'sell_id', self, self._uid)
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


class AccountAssetSellLine(models.Model):
    _name = 'account.asset.sell.line'
    _description = 'Sell Asset Line'

    def _default_sell_value(self):
        if self.asset_id:
            return self.asset_id.value_residual
        else:
            if 'active_id' in self._context:
                asset_id = self.env['account.asset.asset'].browse(self._context.get('active_id'))
                return asset_id.value_residual
            return False

    sell_id = fields.Many2one('account.asset.sell', 'Sell Asset')
    asset_id = fields.Many2one('account.asset', 'Asset', required=True,domain = [('state', '!=', 'model')])
    product_id = fields.Many2one('product.product', 'Product')
    code = fields.Char(string='Asset Code', size=32, readonly=True)
    # asset_state = fields.Selection(related='asset_id.state', string='Asset State')
    date = fields.Date(string='Sell Date', related='sell_id.date')
    manufactured_date = fields.Date(string='Manufactured Date')
    commissioned_date = fields.Date(string='Commissioned Date')
    tax_id = fields.Many2one('account.tax', 'Sell Tax', domain=[('type_tax_use', '=', 'sale')])
    value = fields.Float('Value')
    value_depreciated = fields.Float(string='Depreciated Value')
    value_residual = fields.Float(string='Residual Value')
    is_partial_sell = fields.Boolean(string='Is Partial Sell', related='sell_id.is_partial_sell')
    partial_sell_amount = fields.Float(string='Amount Sell Partly', digits=(16, 2))
    sold_part_residual = fields.Float(string='Residual Cost for Sold Part', digits=(16, 2))
    sell_value = fields.Float('Sell Value', required=True, default=_default_sell_value)
    # close_state = fields.Selection(related='asset_id.close_state', string='Remove Status')
    description = fields.Char('Description')
    move_id = fields.Many2one('account.move', 'Sale Account Move')
    invoice_id = fields.Many2one('account.move','Sale Invoice')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('sale', 'Sale'),
                              ('cancel', 'Cancelled')], 'State', default='draft')

    @api.onchange('asset_id')
    def onchange_asset(self):
        if self.asset_id:
            self.code = self.asset_id.code
            self.manufactured_date = self.asset_id.acquisition_date
            self.commissioned_date = self.asset_id.acquisition_date
            self.value = self.asset_id.original_value
            self.value_depreciated = self.asset_id.original_value - self.asset_id.book_value
            self.value_residual = self.asset_id.original_value
            self.sell_value = self.asset_id.original_value
            self.product_id = False
            self.is_partial_sell = False
            self.sold_part_residual = 0
            self.partial_sell_amount = 0

    @api.onchange('partial_sell_amount')
    def onchange_partial_sell_amount(self):
        if not self.is_partial_sell:
            self.sold_part_residual = 0
            self.partial_sell_amount = 0
        if not self.asset_id:
            return 0
        if self.partial_sell_amount >= self.asset_id.value:
            raise ValidationError(_('Amount sell partly must be less than value of asset'))
        if self.is_partial_sell:
            if self.asset_id.value != 0:
                self.sold_part_residual = self.asset_id.salvage_value * self.partial_sell_amount / self.asset_id.value
            else:
                self.sold_part_residual = 0

    @api.model
    def default_get(self, fields):
        res = super(AccountAssetSellLine, self).default_get(fields)
        context = self._context
        if context.get('description', False):
            res['description'] = context.get('description')
        if context.get('tax_id', False):
            res['tax_id'] = context.get('tax_id')
        return res
    def sell_modify(self, invoice_ids):
        for line in self:
            print('invoice_id22222',invoice_ids)
            if invoice_ids:
                invoice_line_ids = self.env['account.move.line'].sudo().search([
                    ('move_id','=',invoice_ids.id),
                    ('asset_id','=',line.asset_id.id)
                ])
                print('invoice_line_ids22222',invoice_line_ids)
                if invoice_line_ids:
                    self.env['asset.modify'].create({
                        'asset_id': line.asset_id.id,
                        'name': line.sell_id.transaction, 
                        'modify_action':'sell',
                        'invoice_ids':invoice_ids.ids,
                        'invoice_line_ids':invoice_line_ids.ids,
                        # 'loss_account_id': line.act_id.account_id.id, 
                        'date': line.sell_id.date}).sell_dispose()
        # print(s)
        return True
    @api.model
    def create(self, values):
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            if 'is_partial_sell' in values and values['is_partial_sell'] and 'partial_sell_amount' in values and values['partial_sell_amount'] >= asset.value:
                raise ValidationError(_('Amount sell partly must be less than value of asset'))
            values.update({
                'code': asset.code,
                'manufactured_date': asset.acquisition_date,
                # 'acquisition_date': asset.acquisition_date,
                'value': asset.original_value,
                # 'value_depreciated': asset.value_depreciated,
                'value_residual': asset.book_value,
            })
            # asset.write({'close_state': 'draft'})
        return super(AccountAssetSellLine, self).create(values)

    def write(self, values):
        asset = self.asset_id
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'code': asset.code,
                'manufactured_date': asset.acquisition_date,
                # 'acquisition_date': asset.acquisition_date,
                'value': asset.original_value,
                # 'value_depreciated': asset.value_depreciated,
                'value_residual': asset.book_value,
            })
        partial_sell = values['is_partial_sell'] if 'is_partial_sell' in values else self.is_partial_sell
        partial_sell_amount = values['partial_sell_amount'] if 'partial_sell_amount' in values else self.partial_sell_amount
        if partial_sell and partial_sell_amount >= asset.value:
            raise ValidationError(_('Amount sell partly must be less than value of asset'))
        return super(AccountAssetSellLine, self).write(values)

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй мөрийг л устгадаг байна
        for line in self:
            if line.state != 'draft':
                raise UserError(_('You cannot delete an asset sell line which is not draft.'))
            # line.asset_id.write({'close_state': 'not_exc'})
        return super(AccountAssetSellLine, self).unlink()

    def send_button(self):
        for line in self:
            # Борлуулах огноонд тохирох элэгдлийн самбарын мөр батлагдсан эсэхийг шалгах үүднээс
            line.asset_id.search_and_raise_line(line.sell_id.date)
            # line.asset_id.write({'close_state': 'sent'})
        self.write({'state': 'waiting'})

    def approve_button(self):
        # for line in self:
        #     # line.asset_id.write({'close_state': 'acting'})
        # self.write({'state': 'approved'})
        return
    def _prepare_invoice_line(self, asset, sell):
        self.ensure_one()
        name = _('%s sell: %s' % (asset.name, sell.transaction))
        return (0, 0, {'name': name,
                       'account_id': sell.gain_asset_account_id.id,
                       'analytic_distribution': asset.analytic_distribution  or False,
                       'quantity': 1,
                       'price_unit': self.sell_value,
                       'tax_ids': [(6, 0, (self.tax_id.id,))] if self.tax_id else False,
                       'asset_id': asset.id,
                      })

    def _get_account_move_vals(self, invoice_id, depr):
        # Хөрөнгө борлуулахад үүсэх журналын бичилтийн утга буцаах функц
        invoice_line_obj = self.env['account.move.line']
        line_ids = []
        sell = self.sell_id
        asset = self.asset_id
        current_currency = asset.currency_id
        name = _('%s sell: %s' % (asset.name, sell.transaction))
        # Дт талын журналын мөр - ЗЯХ
        inv_line = invoice_line_obj.search([('move_id', '=', invoice_id.id), ('asset_id', '=', asset.id)], limit=1)
        sell_amount = self.sell_value
        if self.tax_id and inv_line:
            sell_amount = inv_line.price_subtotal
#         sell_amount = self.currency_id.round(sell_amount)
        move_amount = current_currency._convert(sell_amount, asset.company_id.currency_id, asset.company_id, sell.date, round=False)
        analytic_distribution = asset.analytic_distribution or False
        line_ids.append(self._get_line_vals(name, sell.moving_asset_account_id.id, analytic_distribution, move_amount, sell_amount, current_currency, sell.date))
        print('line_ids.append',move_amount)
        depr = self.value_depreciated
#         depr = self.currency_id.round(depr)
        if depr > 0:
            # Дт талын журналын мөр - Хур элэгдэл
            amount = current_currency._convert(depr, asset.company_id.currency_id, asset.company_id, sell.date, round=False)
            analytic_distribution = asset.analytic_distribution or False
            line_ids.append(self._get_line_vals(name, asset.account_depreciation_id.id, analytic_distribution, amount, depr, current_currency, sell.date))
        # Кт талын журналын мөр - Хөрөнгө
        value = asset.original_value
#         value = self.currency_id.round(value)
        amount = current_currency._convert(value, asset.company_id.currency_id, asset.company_id, sell.date, round=False)
        analytic_distribution = asset.analytic_distribution or False
        line_ids.append(self._get_line_vals(name, asset.account_asset_id.id, analytic_distribution, -amount, -value, current_currency, sell.date))
        value_residual = value - depr
        diff = sell_amount - value_residual
        if diff > 0:
            # Кт талын журналын мөр - Хөрөнгө зарсан олз
            amount = current_currency._convert(diff, asset.company_id.currency_id, asset.company_id, sell.date, round=False)
            analytic_distribution = asset.analytic_distribution or False
            line_ids.append(self._get_line_vals(name, sell.gain_asset_account_id.id, analytic_distribution, -amount, -diff, current_currency, sell.date))
        elif diff < 0:
            # Дт талын журналын мөр - Хөрөнгө зарсан гарз
            amount = current_currency._convert(abs(diff), asset.company_id.currency_id, asset.company_id, sell.date, round=False)
            analytic_distribution = asset.analytic_distribution or False
            line_ids.append(self._get_line_vals(name, sell.loss_asset_account_id.id, analytic_distribution, amount, abs(diff), current_currency, sell.date))
        journal_id = asset.journal_id.id
#         if asset.company_id.asset_journal_settings == 'intersperse':
#             if not asset.company_id.sale_asset_journal_id:
#                 raise UserError(_('Configure sale journal of asset in %s company!' % asset.company_id.name))
#             journal_id = asset.company_id.sale_asset_journal_id.id
        move_vals = {
            'date': sell.date,
            'journal_id': journal_id,
            'line_ids': line_ids
        }
        return move_vals
            # _get_line_vals(name, sell.moving_asset_account_id.id, analytic_distribution, move_amount, sell_amount, current_currency, sell.date))
    def _get_line_vals(self, name, account, analytic_distribution, asset_amount, currency_amount, current_currency, entry_date):
        # Журналын мөр үүсгэх
        context = self._context or {}
        vals={'name': name,
                       'ref': name,
                       'account_id': account,
                       'debit': asset_amount if asset_amount > 0 else 0,
                       'credit': abs(asset_amount) if asset_amount < 0 else 0,
                       'partner_id': self.sell_id.partner_id and self.sell_id.partner_id.id or False,
                       'currency_id': current_currency and current_currency.id or False,
                       'amount_currency': currency_amount if current_currency and self.asset_id.company_id.currency_id.id == current_currency.id else 0.0,
                    #    'analytic_account_id': analytic_account,
                       'date': entry_date,
                       'balance':asset_amount,
                       'analytic_distribution':analytic_distribution
                       }
        if asset_amount>0 and context.get("src_account_id", False):
            vals.update({
            'asset_ids': [(6,0,[self.id])]
            })
        return (0, 0, vals)
    
    
    def get_invoice_line(self):
        line_vals = []
        product_ids = []
        for line in self:
            sell = line.sell_id
            asset = line.asset_id
            if asset.state != 'open':
                raise UserError(_("%s asset state is not open. Only can sell assets with open state!" % asset.name))
            # if asset.product_id.id not in product_ids or not asset.product_id:
            #     if line.asset_id.product_id:
            #         product_ids.append(line.asset_id.product_id.id)
            #     # Борлуулах хөрөнгийн нэхэмжлэл үүсэх
            else:
                line_vals.append(line._prepare_invoice_line(asset, sell))
            # else:
            #     for val in line_vals:
            #         if val[2]['product_id'] == asset.product_id.id and val[2]['price_unit'] == line.sell_value:
            #             val[2]['quantity'] += 1
        return line_vals

    def get_asset_vals(self, line, asset, vals, invoice_id):
        move_obj = self.env['account.move']
        partial_sell = line.is_partial_sell
        partial_sell_amount = line.partial_sell_amount
        depr = 0
        if partial_sell:
            depr, residual, salvage = asset.with_context(
                date=line.sell_id.date, close=True, partial_sell=partial_sell,
                partial_sell_amount=partial_sell_amount).compute_depreciation_board()
            vals.update({'partly_sold': partial_sell_amount, 'value': asset.value - partial_sell_amount, 'salvage_value': salvage, 'sell_asset' : True})
        else:
            asset.with_context(date=line.sell_id.date, close=True, partial_sell=partial_sell, sell_asset = True,
                               partial_sell_amount=partial_sell_amount).compute_depreciation_board()
        ccc=line._get_account_move_vals(invoice_id, depr)
        print ('ccc ',ccc)
        move_id = move_obj.create(ccc)
        return vals, move_id
    
    def sell_button(self, invoice_id):
        # Хөрөнгө борлуулах
        for line in self:
            vals = {}
            asset = line.asset_id
            # Хөрөнгийг хааж холбоотой бичилтийг үүсгэх
            asset.search_and_raise_line(line.sell_id.date)
            last_depr=asset.asset_close_before_board(line.sell_id.date,'sell')
            if last_depr:
                last_depr.create_move()
            
            # Элэгдлийн самбар дээрээс элэгдүүлэхээр тооцоолж хөрөнгийн үлдэгдэл дүнгээс хассан дүнг тооцоолох
            vals, move_id = self.get_asset_vals(line, asset, vals, invoice_id)
            # if asset.category_id.open_asset:
            move_id.action_post()
            if line.is_partial_sell:
                close_state = 'partly_sold'
            else:
                close_state = 'sale'
                # asset.set_to_close()
            vals.update({'state': 'close',
                        #  'close_move_id': move_id,
                        #  'close_invoice_id': invoice_id,
                        #  'type_of_close': 'sell',
                        #  'close_state': close_state,
                        #  'sell_asset' : True
                         })
            asset.write(vals)
            line.write({'state': 'sale', 'move_id': move_id, 'invoice_id' : invoice_id})

    def draft_button(self):
        # for line in self:
        #     line.asset_id.write({'close_state': 'draft'})
        # self.write({'state': 'draft'})
        return
    def cancel_button(self):
        for line in self:
            context = dict(self._context or {})
            context.update({'partial_sell': line.is_partial_sell,
                            'partial_sell_amount': line.partial_sell_amount})
            line.asset_id.with_context(context).set_to_open()
            # line.asset_id.write({'close_state': 'cancel'})
        self.write({'state': 'cancel'})
        return True

