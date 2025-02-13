# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta

class AccountAssetMove(models.Model):
    _name = 'account.asset.move'
    _inherit = 'mail.thread'
    _description = "Asset move"

    def _asset_count(self):
        for move in self:
            move.asset_count = len(move.line_ids) or 0

    def _compute_is_creator(self):
        for move in self:
            if move.create_uid == self.env.user:
                move.is_creator = True
            else:
                move.is_creator = False

    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = [('model_id.model', '=', 'account.asset.move'),
                         ('branch_ids', 'in', [self.env.user.branch_id.id])
                         ]
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    name = fields.Char('Reference', default='/', copy=False)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.company)
    description = fields.Text('Тайлбар')
    move_date = fields.Date('Шилжүүлэх огноо', default=fields.Date.context_today, tracking=True)
    receipt_date = fields.Date('Огноо', required = True)
    asset_id = fields.Many2one('account.asset', related='line_ids.asset_id', string='Хөрөнгүүд', readonly=False)
    asset_count = fields.Integer(compute='_asset_count', string='# Assets')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('receipt', 'Receipted'),
                              ('cancel', 'Cancelled')], 'State', default='draft', tracking=True)
    line_ids = fields.One2many('account.asset.move.line', 'move_id', 'Assets')
#     workflow_id = fields.Many2one('workflow.config', 'Workflow', copy=False)
    check_sequence = fields.Integer('Workflow Step', default=0, copy=False)
#     is_validator = fields.Boolean(compute='_compute_is_validator')
    is_creator = fields.Boolean(compute='_compute_is_creator')
    new_owner_id = fields.Many2one('res.partner', 'Шинэ эзэмшигч', domain=[("employee", "=", True)])
    # new_branch_id = fields.Many2one('res.branch', 'New branch', )
    # new_analytic_account_id = fields.Many2one('account.analytic.account', 'New Analytic Account')
    move_goal = fields.Char('Шилжүүлгийн тайлбар', required = True)
    owner_emp_id = fields.Many2one('res.partner', 'Эзэмшигч', domain=[("employee", "=", True)])
    #flow
    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
                              default=_get_default_flow_id,
                              copy=True, required=True, domain="[('model_id.model', '=', 'account.asset.move')]")

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
                                   default=_get_dynamic_flow_line_id,
                                   copy=False,
                                   domain="[('flow_id', '=', flow_id),('flow_id.model_id.model', '=', 'account.asset.move')]")

    state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type', store=True)

    is_not_edit = fields.Boolean(compute='_compute_is_not_edit')
    next_state_type = fields.Char(string='Дараагийн төлөв', compute='_compute_next_state_type')
    history_line_ids = fields.One2many('dynamic.flow.history', 'asset_move_id', 'Урсгалын түүхүүд')
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
                               string='Төлөв stage', store=True)
    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')
    avail_asset_ids = fields.Many2many('account.asset', compute='_compute_unselected_expenses')
    branch_id = fields.Many2one('res.branch', 'Салбар', tracking=True)
    flow_line_next_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    flow_line_back_id = fields.Many2one('dynamic.flow.line', compute='_compute_flow_line_id', readonly=True)
    @api.depends('line_ids.asset_id')
    def _compute_unselected_expenses(self):
        if self.line_ids:
            for line in self.line_ids:
                if line.asset_id:
                    print('1231241242141',line.asset_id)
                    self.avail_asset_ids = [(4, line.asset_id.id)]
                    # line.avail_asset_ids = [(4, line.asset_id.id)]
                    print('safsafwqqfwqwrqwrf',self.avail_asset_ids )
        else:
            self.avail_asset_ids = False
            # self.line_ids.avail_asset_ids = False

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

    @api.depends('flow_id')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'account.asset.move')])
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
        domain.append(('flow_id.model_id.model', '=', 'account.asset.move'))
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

                self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'asset_move_id', self)
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
                self.env['dynamic.flow.history'].create_history(back_flow_line_id, 'asset_move_id', self)
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
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'asset_move_id', self)
        else:
            raise UserError(_('You are not cancel user'))

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
            self.env['dynamic.flow.history'].create_history(flow_line_id, 'asset_move_id', self)
        else:
            raise UserError(_('You are not draft user'))
#         
    @api.onchange('new_owner_id')
    def onchange_new_owner(self):
        for obj in self:
            for line in obj.line_ids:
                line.new_owner_id = obj.new_owner_id.id

    @api.onchange('new_branch_id')
    def onchange_new_branch(self):
        for obj in self:
            for line in obj.line_ids:
                line.new_branch_id = obj.new_branch_id.id

    @api.onchange('new_analytic_account_id')
    def onchange_new_analytic_account(self):
        for obj in self:
            for line in obj.line_ids:
                line.new_analytic_account_id = obj.new_analytic_account_id.id

    @api.onchange('move_goal')
    def onchange_move_goal(self):
        for obj in self:
            for line in obj.line_ids:
                line.move_goal = obj.move_goal

    @api.model
    def default_get(self, default_fields):
        # Хөрөнгүүдийг олноор нь сонгон шилжүүлэх үед мөр бүрт мэдээллийг оруулах
        res = super(AccountAssetMove, self).default_get(default_fields)
        context = dict(self._context or {})
        vals = []
        if context.get('active_model') == 'account.asset' and context.get('active_ids'):
            assets = self.env[context.get('active_model')].browse(context.get('active_ids'))
            for asset in assets:
                if asset.state == 'open' or asset.state == 'close':
                    line = [0, False, {'asset_id': asset.id,
                                       'state': 'draft',
                                       'old_owner_id': asset.owner_id.id,
                                       'old_department_id': asset.owner_department_id.id,
                                       'old_branch_id': asset.branch_id.id,
                                    #    'old_category_id': asset.category_id.id,
                                       'old_account_id':asset.account_depreciation_expense_id.id,
                                    #    'old_analytic_account_id': asset.account_analytic_id.id,
                                       'new_owner_id': asset.owner_id.id,
                                       'analytic_distribution': asset.analytic_distribution,
                                       'old_asset_type': asset.asset_type_id.id,
                                        'new_branch_id': asset.branch_id.id,}]
                                    #    'new_category_id': asset.category_id.id,
                                    #    'is_expense_split': asset.is_expense_split,
                                        # 'old_allocation_id': asset.allocation_id.id,
                                        # 'purchase_date':asset.purchase_date,
                    vals.append(line)
        res.update({'line_ids': vals})
        return res

    @api.model
    def create(self, values):
        # Хүлээн авсан огноо нь шилжүүлсэн огнооноос хойш байж болохгүй ба нэрийг автомат дугаарлана
        res = super(AccountAssetMove, self).create(values)
        if res.name == '/':
            res.write({'name': self.env['ir.sequence'].next_by_code('account.asset.move')})
        return res

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй шилжилтийг л устгадаг байна
        for move in self:
            if move.state != 'draft':
                raise UserError(_('You cannot delete an asset move which is not draft.'))
        return super(AccountAssetMove, self).unlink()

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
    def get_move_line(self,ids):
        html = """
		<table>	
			"""
        report_id = self.browse(ids)
        i = 1
        lines = report_id.line_ids
        if lines:
            html += """
				<table style="width:100%;font-size: 24pt;border: 1px solid ;border-collapse: collapse;font-family:Times New Roman">
					<tr style="border: 1px solid ;border-collapse: collapse;">
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 12pt;" rowspan="2" >№</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 12pt;" rowspan="2">Хөрөнгийн нэр</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 12pt;" rowspan="2">Бүртгэлийн дугаар</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 12pt;" rowspan="2">Хэмжих нэгж</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 12pt; " rowspan="2" >Тоо хэмжээ</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 12pt;" colspan="2" >Дүн</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 12pt;" colspan="2" >Шилжүүлж өгсөн</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 12pt;" colspan="2" >Шилжүүлж авсан</td>
                    </tr>
					<tr style="border: 1px solid ;border-collapse: collapse;">
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 10pt;">Өртөг</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 10pt;">Элэгдэл</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 10pt;">Байршил</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 10pt;">Эд хариуцагч</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 10pt;">Байршил</td>
						<td style="border: 1px solid ;border-collapse: collapse;text-align: center;font-size: 10pt;">Эд хариуцагч</td>
                    </tr>
			    """
            for line in lines:
                original_value = '0'
                if line.asset_id.original_value:
                    original_value = line.asset_id.original_value
                value_depreciated = '0'
                if line.asset_id.book_value:
                    value_depreciated = line.asset_id.original_value-line.asset_id.book_value
                asset_id = line.asset_id.name
                asset_code = line.asset_id.code
                old_branch = line.old_branch_id.name
                old_owner = line.old_owner_id.name
                new_branch = line.new_branch_id.name
                new_owner = line.new_owner_id.name
                qty = 'Ширхэг'
                quanty = '1'

		
                html += """
						<tr>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						<td style= "font-size: 9pt;text-align: center;border: 1px solid ;border-collapse: collapse;">
							%s
						</td>
						</tr>
				"""%((str(i)),asset_id,asset_code,qty,quanty,"{0:,.2f}".format(line.asset_id.initial_value),"{0:,.2f}".format(line.asset_id.value_depreciated),old_branch,old_owner,new_branch,new_owner)
                i += 1

            sum_unit = 0
            for line in lines:
                sum_unit += line.asset_id.initial_value
            sum_dep = 0
            for line in lines:
                sum_dep += line.asset_id.value_depreciated
            html +="""
				<tr>
					<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 9pt; " colspan="4" >Нийт</td>
					<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 9pt;"><b>%s</b></td>
					<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 9pt;"><b>%s</b></td>
					<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 9pt;"><b>%s</b></td>
					<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 9pt;"><b>%s</b></td>
					<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 9pt;"><b>%s</b></td>
					<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 9pt;"><b>%s</b></td>
					<td style="border: 1px solid ;border-collapse: collapse;text-align: center; font-size: 9pt;"><b>%s</b></td>
                </tr>
			"""%(" ","{0:,.2f}".format(int(sum_unit)),"{0:,.2f}".format(int(sum_dep))," "," "," "," ")
        html += """
			</>
		"""
        return html
    def get_request_user_signature(self,ids):
        report_id = self.browse(ids)
        html = '<table>'
        image_str = '_____________________'
        if report_id.create_uid.digital_signature_from_file:
            image_buf = (report_id.create_uid.digital_signature_from_file).decode('utf-8')
            image_str = '<img alt="Embedded Image" width="80" src="data:image/png;base64,%s" />'%(image_buf)
        html += u'<tr><td><p>Шилжүүлэг хийсэн ажилтан:</p></td><td><p>%s</p></td></tr>'%(image_str)
        html += '</table>'
        return html

    def get_user_signature(self,ids):
        report_id = self.browse(ids)
        html = '<table>'
        print_flow_line_ids = report_id.flow_id.line_ids.filtered(lambda r: r.is_print)
        history_obj = self.env['dynamic.flow.history']
        for item in print_flow_line_ids:
            his_id = history_obj.search([('flow_line_id','=',item.id),('asset_move_id','=',report_id.id)], order='date desc', limit=1)
            image_str = '_____________________'
            if his_id.user_id.digital_signature_from_file:
                image_buf = (his_id.user_id.digital_signature_from_file).decode('utf-8')
                image_str = '<img alt="Embedded Image" width="80" src="data:image/png;base64,%s" />'%(image_buf)
            user_str =  '________________________'
            if his_id.user_id:
                user_str = his_id.user_id.name
            html += u'<tr><td><p>%s:</p></td><td><p>%s</p></td><td><p>/%s/</p></td></tr>'%(item.name, user_str, image_str)
        html += '</table>'
        return html

    def request_print(self):
        model_id = self.env['ir.model'].sudo().search([('model','=','account.asset.move')], limit=1)
        # if not self.flow_id.is_between_account and not self.flow_id.is_cash and not self.flow_id.is_between_company:
        template = self.env['pdf.template.generator'].sudo().search([('model_id','=',model_id.id)], limit=1)
        if template:
            res = template.sudo().print_template(self.id)
            return res
        else:
            raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))
    def action_done(self):
        context = dict(self._context or {})
        context['asset_move'] = True
        for move in self:
            for line in move.line_ids:
                # Тухайн шижлүүлэлтээс хойш хийгдсэн шилжүүлэлт байгаа эсэхийг шалгах
                # receipt_lines = self.env['account.asset.move.line'].search([('asset_id', '=', line.asset_id.id), ('id', '!=', line.id), ('state', '=', 'receipt')])
                # for receipt_line in receipt_lines:
                    # if receipt_line.move_id.move_date > line.move_id.move_date:
                    #     raise UserError(_("You cannot asset move. Already %s asset moved after %s!" % (line.asset_id.name, line.move_id.move_date)))
                line.with_context(context).receipt_button()
            move.state = 'receipt'
            if not move.receipt_date:
                move.receipt_date = datetime.now()


    def create_lines(self, interval=1):
        line_obj = self.env['account.asset.move.line']
        asset_obj = self.env['account.asset']
        
        month = interval
        for item in self:
            if item.owner_emp_id or item.owner_emp_id:
                emps=(item.owner_emp_id and [item.owner_emp_id.id]) #or (item.owner_emp_ids and item.owner_emp_ids.ids)
                assets = asset_obj.search([('owner_id','in',emps)])#'|',,('owner_emp_ids','in',emps)
                if assets:
                    for asset in assets:
                        line=line_obj.create({
                            'asset_name': asset.name,
                            # 'description': asset.name,
                            'asset_id': asset.id,
                            'move_goal':'1',
                            'move_id': False,
                            'move_id': item.id,
                            # 'result': 'nocounted'
                        })                

        return True
	
class AccountAssetMoveLine(models.Model):
    _name = 'account.asset.move.line'
    _inherit = 'analytic.mixin' 
    _description = 'Asset Move information'
    _rec_name = 'asset_id'

    def _get_domain(self):
        print('self.move_id.avail_asset_ids.ids: ', self.move_id.avail_asset_ids.ids)
        return [('id','in',self.move_id.avail_asset_ids.ids)]

    asset_id = fields.Many2one('account.asset', 'Asset', ondelete='cascade', required=1)
    avail_asset_ids = fields.Many2many('account.asset', 'account_asset_account_asset_move_line_rel')
    asset_code = fields.Char('Asset Code', related= 'asset_id.code')
    asset_bar_code = fields.Char(string='Bar code')
    asset_name = fields.Char('Asset Name', related= 'asset_id.name')
    asset_commissioned_date = fields.Date('Commissioned Date', related= 'asset_id.acquisition_date')
    start_date = fields.Date('Start Date')
    move_id = fields.Many2one('account.asset.move', 'Asset Move')
    account_move_id = fields.Many2one('account.move', 'Account Move')
    depreciated_value = fields.Float(string="Depr Value")

    old_department_id = fields.Many2one('hr.department','Old department')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    new_department_id = fields.Many2one('hr.department', string='New Department')    
    old_owner_id = fields.Many2one('res.partner', 'Old Owner', domain=[("employee", "=", True)])
    new_owner_id = fields.Many2one('res.partner', 'New Owner', domain=[("employee", "=", True)])
    old_branch_id = fields.Many2one('res.branch', 'Old branch')
    new_branch_id = fields.Many2one('res.branch', 'New branch')
    old_category_id = fields.Many2one('account.asset', 'Old Category', domain = [('state', '=', 'model')])
    new_category_id = fields.Many2one('account.asset', 'New Category', domain = [('state', '=', 'model')])
    old_account_id  = fields.Many2one('account.account', 'Old expense account')
    new_account_id = fields.Many2one('account.account','New expense account')
    old_asset_type =fields.Many2one('account.asset.type', string="Old type")
    new_asset_type =fields.Many2one('account.asset.type', string="New type")
    is_expense_split = fields.Boolean('Зардал хуваах?')
    # old_allocation_id = fields.Many2one('account.allocation.expense.conf','Өмнөх зардал хуваах тохиргоо')
    # new_allocation_id = fields.Many2one('account.allocation.expense.conf','Шинэ зардал хуваах тохиргоо')
    # old_analytic_account_id = fields.Many2one('account.analytic.account', 'Old Analytic Account')
    # new_analytic_account_id = fields.Many2one('account.analytic.account', 'New Analytic Account')
    move_goal = fields.Char('Move Goal', related='move_id.move_goal')
    state = fields.Selection([('draft', 'Draft'),
                              ('waiting', 'Waiting'),
                              ('approved', 'Approved'),
                              ('receipt', 'Receipted'),
                              ('cancel', 'Cancelled')], 'State', default='draft')
    move_date = fields.Date('Move Date', related='move_id.move_date', readonly=True)
    receipt_date = fields.Date('Receipt Date', related='move_id.receipt_date', readonly=True)
    code = fields.Char('Document Number')
    old_location_id = fields.Many2one('account.asset.location', string='Old Location')
    new_location_id = fields.Many2one('account.asset.location', string='New Location')
    purchase_date = fields.Date(string='Purchase date')




    @api.onchange('asset_id')
    def onchange_asset(self):
        if not self.asset_id:
            return
        self.old_owner_id = self.asset_id.owner_id.id
        self.old_branch_id = self.asset_id.branch_id.id
        self.old_category_id = self.asset_id.model_id.id
        self.old_location_id = self.asset_id.location_id.id
        self.new_owner_id = self.asset_id.owner_id.id
        self.new_branch_id = self.asset_id.branch_id.id
        self.new_category_id = self.asset_id.model_id.id
        self.old_department_id = self.asset_id.owner_department_id.id
        self.old_account_id = self.asset_id.account_depreciation_expense_id.id
        self.purchase_date = self.asset_id.acquisition_date
        self.depreciated_value = self.asset_id.original_value - self.asset_id.book_value
        self.analytic_distribution = self.asset_id.analytic_distribution
    @api.onchange('asset_id', 'move_id.owner_emp_id')
    def onchange_user_id(self):
        search_domain=self.asset_domain()
        domain = {'asset_id': search_domain}
        return {'domain': domain}
    def asset_domain(self):
        search_domain=[]
        for item in self:
            search_domain = [
                    ('owner_id','=',item.move_id.owner_emp_id.id),('state','=','open'),
                ]
        return search_domain
    # @api.onchange("new_owner_id")
    # def _onchange_owner_partner(self):
    #     for item in self:
    #         if item.new_owner_id:
    #             employee_id =  item.env['hr.employee'].search([('passport_id', '=', item.new_owner_id.vat)])
    #             print('safsafsafsa', employee_id)
    #             if employee_id:
    #                 item.new_department_id = employee_id.department_id.id
    #             else:
    #                 item.new_department_id =False
    #         else:
    #             item.new_department_id =False

    @api.model
    def create(self, values):
        # Хөрөнгийг сонгосон тохиолдолд тухайн хөрөнгийн мэдээллээр мөрийг шинэчилж үүсгэх
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'old_owner_id': asset.owner_id.id,
                'old_branch_id': asset.branch_id.id,
                # 'old_category_id': asset.model_id.id,
                # 'old_analytic_account_id': asset.account_analytic_id.id,
                'old_location_id': asset.location_id.id,
                'purchase_date' : asset.acquisition_date,
                'old_department_id' : asset.owner_department_id.id,
                'old_account_id' : asset.account_depreciation_expense_id.id,
                'analytic_distribution' : asset.analytic_distribution,
                'old_asset_type':asset.asset_type_id.id
            })
        return super(AccountAssetMoveLine, self).create(values)

    def write(self, values):
        # Хөрөнгийг өөрчилсөн, шинээр бичсэн тохиолдолд тухайн хөрөнгийн мэдээллээр мөрийг шинэчилж үүсгэх
        if 'asset_id' in values:
            asset = self.env['account.asset'].browse(values['asset_id'])
            values.update({
                'old_owner_id': asset.owner_id.id,
                'old_branch_id': asset.branch_id.id,
                # 'old_category_id': asset.model_id.id,
                # 'old_analytic_account_id': asset.account_analytic_id.id,
                'old_location_id': asset.location_id.id,
                'purchase_date' : asset.acquisition_date,
                'old_department_id' : asset.owner_department_id.id,
                'old_account_id' : asset.account_depreciation_expense_id.id,
                'analytic_distribution' : asset.analytic_distribution,
                'old_asset_type':asset.asset_type_id.id
            })
        return super(AccountAssetMoveLine, self).write(values)

    def unlink(self):
        # Зөвхөн ноорог төлөвтэй мөрийг л устгадаг байна
        for line in self:
            if line.state != 'draft':
                raise UserError(_('You cannot delete an asset move line which is not draft.'))
        return super(AccountAssetMoveLine, self).unlink()

    def _prepare_move_line(self, account, analytic_account, debit=0, credit=0):
        # Журналын мөрүүд үүсгэх
        for line in self:
            return (0, 0, {'name': line.move_id.name,
                           'ref': line.id,
                           'account_id': account,
                           'debit': debit,
                           'credit': credit,
                           'journal_id': line.new_category_id.journal_id.id,
                           'date': line.move_id.move_date,
                           'analytic_account_id': analytic_account,
                           'asset_id': line.asset_id.id})

    def send_button(self):
        for line in self:
            if line.old_category_id != line.new_category_id:
                line.asset_id.search_and_raise_line(line.move_id.move_date)
        self.write({'state': 'waiting'})
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             
    def approve_button(self):
        self.write({'state': 'approved'})

    def get_line_vals(self, line):
        line_vals = {'state': 'receipt'}
        if line.new_owner_id.id != line.old_owner_id.id:
            date = line.move_id.receipt_date or datetime.now()
            line_vals.update({'code': self.env['ir.sequence'].next_by_code('asset.move.line.letter.sequence', date)})
        return line_vals

    def get_recieve_values(self):
        for asset in self:
            receipt_date = (asset.move_id.receipt_date - relativedelta(months=1) ).strftime('%Y-%m')
            if asset.asset_id.depreciation_move_ids:
                for move in asset.asset_id.depreciation_move_ids:
                    if move.state == 'draft':
                        move_date = move.date.strftime('%Y-%m')
                        if receipt_date == move_date:
                            raise UserError(u'Тухайн сарын элэгдэл батлагдаагүй байна "%s"'%move_date)
            # if asset.new_owner_id:
            #     employee_id =  self.env['hr.employee'].search([('passport_id', '=', self.new_owner_id.vat)])
            #     print('safsafsafsa', employee_id)
            #     if employee_id:
            #         self.new_department_id = employee_id.department_id.id
            #     else:
            #         raise UserError(_('Тухайн ажилтан / %s / дээрх Харилцах хаяг болон Ажилтаны бүртгэл дээрх регистерийн дугаар таарахгүй байна. '% (
            #                                 asset.new_owner_id.name,)))
        return {'owner_id': self.new_owner_id.id if self.new_owner_id else self.old_owner_id.id or False, 
                'branch_id': self.new_branch_id.id if self.new_branch_id else self.old_branch_id.id or False, 
                'owner_department_id':self.new_department_id.id if self.new_department_id else self.old_department_id.id or False,
                # 'model_id': self.new_category_id.id if self.new_category_id else self.old_category_id.id,
                'location_id': self.new_location_id.id if self.new_location_id else self.old_location_id.id or False,
                # 'account_depreciation_expense_id' : self.new_account_id.id if self.new_account_id else self.old_account_id.id or False,
                'asset_type_id':self.new_asset_type.id if self.new_asset_type else self.old_asset_type.id or False,
                'analytic_distribution' : self.analytic_distribution if self.analytic_distribution else self.asset_id.analytic_distribution or False}

    def receipt_button(self):
        # Хөрөнгийн шилжилт хөдөлгөөн хүлээн авах
        asset_move = self.env.context.get('asset_move', False)
        for line in self:
            line.asset_id.sudo().write(line.get_recieve_values())
            line_vals = self.get_line_vals(line)
            line.write(line_vals)
        return True

    def draft_button(self):
        self.write({'state': 'draft'})
        
    def get_cancel_values(self):
        return {'owner_id': self.old_owner_id and self.old_owner_id.id or False,
                'branch_id': self.old_branch_id.id,
                # 'account_analytic_id': self.old_analytic_account_id.id,
                'model_id': self.old_category_id.id}

    def cancel_button(self):
        asset_move = self.env.context.get('asset_move', False)
        for line in self:
            if line.state == 'receipt':
                if line.asset_id.state == 'close':
                    raise UserError(_("Cannot cancel asset move, because %s asset closed!" % line.asset_id.name))
                # Үндсэн хөрөнгийн шилжилтийг устгах үед тухайн хөрөнгөнд шилжүүлэлтийн журналын бичилтээс хойш ямарваа журналын бичилт үүссэн байвал устгах боломжгүй
                # мөн хамгийн сүүлийн шилжүүлэлт биш бол устгах боломжгүй байна
                line.asset_id.check_cancel(line, 'move')
                # Хөрөнгө шилжилтээс үүссэн ажил гүйлгээг устгах
                line.account_move_id.button_cancel()
                line.account_move_id.with_context(asset_unlink=True, force_delete=True).unlink()
                line.asset_id.write(line.get_cancel_values())
            if asset_move:
                line.write({'state': 'cancel', 'start_date': False})
            else:
                line.write({'state': 'draft', 'start_date': False})
        return True

    def asset_move_line_letter(self):
        if self.new_owner_id.id != self.old_owner_id.id:
            return self.env.ref('l10n_mn_account_asset.asset_move_line_letter_action').report_action(self)
