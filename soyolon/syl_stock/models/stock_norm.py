from odoo import fields, models , api
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
import pandas as pd

import logging
_logger = logging.getLogger(__name__)

class StockNorm(models.Model):
    _name = 'stock.norm'
    _description = 'Шаардах дээрх норм'
    _rec_name = 'norm_type'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    branch_id = fields.Many2one('res.branch',string='Байршил',tracking=True)
    department_id = fields.Many2one('hr.department', string='Хэлтэс', tracking=True)
    norm_types = fields.Many2one('stock.norm.types', string='Төрөл' ,domain="[('active_is','=',True)]")
    date_start = fields.Date(string='Эхлэх огноо',tracking=True)
    date_end = fields.Date(string='Дуусах огноо', required=True,tracking=True)
    line_ids = fields.One2many('stock.norm.line','parent_id',string='Мөрүүд')
    norm_type = fields.Selection([('branch','Оффис'),('department','Салхит')],tracking=True, string='Норм төрөл', default='branch')
    state = fields.Selection([('draft','Үүссэн'),('approved','Түгжигдсэн')], string='Төлөв', default='draft', tracking=True)
    is_type_check = fields.Boolean(default=False, copy=False)

    # Төрлөөс хамаарч таобар нуух
    @api.onchange('norm_type')
    def get_norm_types_check(self):
        for i in self:
            if i.norm_type == 'branch':
                i.is_type_check = False
            else:
                i.is_type_check = True

    # Норм түгжих
    def action_approve(self):
        self.update({'state': 'approved'})

class StockNormLine(models.Model):
    _name = 'stock.norm.line'
    _description = 'Шаардах дээрх норм'
    _rec_name = 'parent_id'
    
    parent_id = fields.Many2one('stock.norm', string='Parent ID', ondelete='cascade')
    norm_type = fields.Selection([('branch','Оффис'),('department','Салхит')],tracking=True, string='Норм төрөл', related='parent_id.norm_type')
    state = fields.Selection([('draft','Үүссэн'),('approved','Түгжигдсэн')], string='Төлөв',related='parent_id.state')
    product_id = fields.Many2one('product.product', string='Бараа', required=True)
    uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж', related='product_id.uom_id')
    norm_qty = fields.Float(string='Норм', default=0)
    reference_qty    = fields.Float(string='Гүйцэтгэл')
    branch_id = fields.Many2one('res.branch',string='Байршил',tracking=True)
    department_id = fields.Many2one('hr.department', string='Хэлтэс', tracking=True)
    employee_jobid = fields.Many2one('hr.job', string='Албан тушаал')
    employee_id = fields.Many2one('hr.employee', string='Ажилтан', domain="[('partner_id.employee','=',True),('job_id','=',employee_jobid)]")

class InheritStockProductExpensiveLine(models.Model):
    _inherit = 'stock.product.other.expense.line'

    norm_qty = fields.Float(string='Норм')
    reference_qty = fields.Float(string='Гүйцэтгэл')
    description = fields.Char(string='Тайлбар')
    norm_id = fields.Many2one('stock.norm.line', string='Норм дугаар')
    check_norm = fields.Boolean(default=False, copy=False)
    product_id = fields.Many2one('product.product', string='Бараа', required=True)
    uom_id = fields.Many2one('uom.uom', string='Хэмжих нэгж', related='product_id.uom_id')
    default_code = fields.Char(string='Product Code', related='product_id.default_code')
    product_code = fields.Char(string='Product Code', related='product_id.product_code')
    product_name = fields.Many2one('product.product', string='Product Name', related='product_id')
    unit_cost = fields.Float(string='Unit Cost', related='product_standard_price')
    no_qty = fields.Float(string='Norm QTY', related='norm_qty')
    no_cost = fields.Float(string='Norm COST', compute='get_ext_info')
    spe_qty = fields.Float(string='Spending QTY', compute='get_ext_info')
    spe_cost = fields.Float(string='Spending COST', compute='get_ext_info')
    ext_qty    = fields.Float(string='Extra QTY', compute='get_ext_info')
    ext_cost    = fields.Float(string='Extra Cost', compute='get_ext_info')
    reason = fields.Char(string='Reason', related='description')
    check_types = fields.Boolean(default=False, copy=False)
    check_location    = fields.Boolean(default=False, copy=False)
    partner_id = fields.Many2one('res.partner', string='Ажилтан', domain="[('employee','=',True)]")
    job_position = fields.Many2one('hr.job', string='Job position', related='partner_id.user_ids.employee_id.job_id')
    approved_qty = fields.Float(string='Зөвшөөрсөн тоо', copy=False)
    done_qty = fields.Float(string='Олгосон тоо', compute='get_done_qty', copy=False)
    required_qty = fields.Float(string='Хүссэн тоо', copy=False)
    qty = fields.Float(u'Тоо хэмжээ', compute='get_real_qty', copy=False )
    norm_type = fields.Selection([('branch','Оффис'),('department','Салхит')],tracking=True, string='Норм төрөл', related='parent_id.norm_type', copy=False)
    branch_id = fields.Many2one('res.branch',string='Байршил',tracking=True)
    department_id = fields.Many2one('hr.department', string='Хэлтэс', tracking=True)

    # Агуулхын баримтын үүсэж буй тоо хэмжээг өөрчилөх
    @api.onchange('required_qty','approved_qty')
    def get_real_qty(self):
        for i in self:
            if i.approved_qty > 0.0:
                i.qty = i.approved_qty
            else:
                i.qty = i.required_qty

    # Батлагдсан агуулхын баримтаас тоо хэмжээ дуудах
    @api.depends('parent_id','parent_id.expense_picking_ids')
    def get_done_qty(self):
        for item in self:
            # picking_ids = item.parent_id.expense_picking_ids.filtered(lambda r: r.state == 'done')
            # move_ids = picking_ids.mapped('move_ids_without_package') if picking_ids else []
            # match_move_ids = move_ids.filtered(lambda r: r.product_id == item.product_id and r.state == 'done') if move_ids else []
            if item.move_ids.filtered(lambda r: r.state=='done'):
                item.done_qty = sum(item.move_ids.filtered(lambda r: r.state=='done').mapped('quantity_done'))
                # item.unit_cost = sum(item.move_ids.filtered(lambda r: r.state=='done').price_unit)
            else:
                item.done_qty = 0 
            # for move in move_ids:
            #     move
        # for i in self:
        #     if i.parent_id.expense_picking_ids:
        #         for line in i.parent_id.expense_picking_ids:
        #             for l in line.move_ids_without_package:
        #                 if i.product_id == l.product_id:
        #                     i.done_qty += l.quantity_done
        #                     i.unit_cost = l.price_unit
        #                 else:
        #                     i.done_qty = 0.0
        #             else:
        #                 i.done_qty = 0.0
        #         else:
        #             i.done_qty = 0.0
        #     else:
        #         i.done_qty = 0.0
                    
    # Тайлан мэдээлэл дуудах
    def get_ext_info(self):
        for i in self:
            i.spe_qty = i.qty + i.reference_qty
            ext_qty = i.spe_qty - i.no_qty
            i.no_cost = i.unit_cost * i.no_qty
            i.spe_cost = i.unit_cost * i.spe_qty
            if ext_qty >= 0:
                i.ext_qty = ext_qty
                i.ext_cost = i.unit_cost * i.ext_qty
            else:
                i.ext_qty = 0.0
                i.ext_cost = 0.0

    # Нормын гүйцэтгэлээс давж байгаа эсэх шалгах
    @api.onchange('required_qty','product_id')
    def process_sum_qty(self):
        if self.norm_qty == 0.0:
            self.check_norm = False
        else:
            sums = 0.0
            sums =  self.reference_qty + self.required_qty
            if sums >= self.norm_qty:
                self.check_norm = True
            else:
                self.check_norm = False

    # Бараанаас хамаарч норм мэдээлэл дуудах
    @api.onchange('product_id')
    def get_product_norm(self):
        self.norm_qty = 0.0
        self.reference_qty = 0.0
        self.description = ''
        if self.parent_id.norm_type == 'branch':
            request_ids = self.env['stock.norm.line'].search([('parent_id.state','=','approved'),('parent_id.norm_type','=','branch'),('branch_id','=',self.parent_id.branch_id.id),('department_id','=',self.parent_id.department_id.id)])
            for request_id in request_ids:
                if request_id.parent_id.date_start <= self.parent_id.date_required:
                    if request_id.parent_id.date_end >= self.parent_id.date_required:
                        if request_id:
                            for line in request_id.parent_id.line_ids:
                                if self.product_id == line.product_id:
                                    self.norm_qty = line.norm_qty
                                    self.reference_qty = line.reference_qty
                                    self.norm_id = line
                                    if line.reference_qty >= line.norm_qty:
                                        self.check_norm = True
                                        if line.norm_qty == 0.0:
                                            self.check_norm = False
                                    else:
                                        self.check_norm = False
                        else:
                            self.check_norm = False
        else:
            request_ids = self.env['stock.norm.line'].search([('parent_id.state','=','approved'),('parent_id.norm_type','=','department'),('employee_id.partner_id','=',self.res_partner_id.id)])
            for request_id in request_ids:
                if request_id.parent_id.date_start <= self.parent_id.date_required:
                    if request_id.parent_id.date_end >= self.parent_id.date_required:
                        if request_id:
                            for line in request_id.parent_id.line_ids:
                                if self.product_id == line.product_id:
                                    self.norm_qty = line.norm_qty
                                    self.reference_qty = line.reference_qty
                                    self.norm_id = line
                                    if line.reference_qty >= line.norm_qty:
                                        self.check_norm = True
                                        if line.norm_qty == 0.0:
                                            self.check_norm = False
                                    else:
                                        self.check_norm = False
                        else:
                            self.check_norm = False

    @api.depends('parent_id', 'parent_id.analytic_distribution', 
                 'product_id', 'parent_id.transaction_value_id',
                 'parent_id.department_id', 'parent_id.technic_id',
                 )
    def _compute_analytic_distribution(self):
        for line in self:
            analytic_distribution=False
            if line.parent_id and line.parent_id.partner_id and not line.res_partner_id:
                line.res_partner_id = line.parent_id.partner_id.id
            account_id=False
            # if line.parent_id.transaction_value_id.is_default_account == False:
            if line.parent_id.technic_id:
                product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                ('technic_ids','in',line.parent_id.technic_id.id)], limit=1)
                account_id = product_account_obj.account_id.id
                analytic_distribution=product_account_obj.analytic_distribution
            elif line.parent_id.equipment_id:
                product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                ('equipment_ids','in',line.parent_id.equipment_id.id)], limit=1)
                account_id = product_account_obj.account_id.id
                analytic_distribution=product_account_obj.analytic_distribution
            elif line.parent_id.department_id:
                product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                ('department_ids','in',line.parent_id.department_id.id),
                                                                                ('technic_ids','=',False),
                                                                                ('equipment_ids','=',False)
                                                                                ], limit=1)
                account_id = product_account_obj.account_id.id
                analytic_distribution=product_account_obj.analytic_distribution
            if not line.parent_id.equipment_id and not line.parent_id.technic_id \
                    and line.parent_id.branch_id and line.parent_id.department_id and not account_id:
                product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                ('department_ids','in',line.parent_id.department_id.id),
                                                                                ('technic_ids','=',False),
                                                                                ('equipment_ids','=',False)
                                                                                ], limit=1)
                if not product_account_obj:
                    product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                # ('department_ids','in',line.parent_id.department_id.id),
                                                                                ('technic_ids','=',False),
                                                                                ('equipment_ids','=',False)
                                                                                ], limit=1)
                    
                account_id = product_account_obj.account_id.id
                analytic_distribution=product_account_obj.analytic_distribution
            if not account_id:
                if line.parent_id.transaction_value_id and line.parent_id.transaction_value_id.account_id:
                    account_id = line.parent_id.transaction_value_id.account_id.id
            if not account_id: #technikgui
                product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                ('technic_ids','=',False),
                                                                                #  ('department_ids','=',False),
                                                                                ('equipment_ids','=',False)], limit=1)
                account_id = product_account_obj.account_id.id
            _logger.info('account_idaccount_id %s '%(account_id))
            _logger.info('analytic_distribution %s '%(analytic_distribution))
            if account_id:
                line.account_id=account_id
            if not line.analytic_distribution:
                if analytic_distribution:
                    line.write({'analytic_distribution':analytic_distribution})
                elif line.res_partner_id and not line.parent_id.technic_id and analytic_distribution ==False:
                    employee = self.env['hr.employee'].search([('partner_id','=',line.res_partner_id.id)], limit=1)
                    department_id = employee and employee.department_id
                    _logger.info('employee %s '%(employee))
                    distribution_model =self.env['account.analytic.distribution.model'].search([
                                                                                    ('department_id','=',department_id.id),
                                                                                    ('company_id','=',self.env.company.id),
                                                                                    ],limit=1)
                    _logger.info('distribution_model %s '%(distribution_model))
                    line.analytic_distribution=distribution_model.analytic_distribution
                elif line.parent_id and line.parent_id.analytic_distribution and not line.parent_id.technic_id:
                    _logger.info('elseee distribution_model %s '%(line.parent_id.analytic_distribution))
                    line.analytic_distribution = line.parent_id.analytic_distribution

class InheritStockProductExpensive(models.Model):
    _inherit = 'stock.product.other.expense'

    norm_type = fields.Selection([('branch','Оффис'),('department','Салхит')],tracking=True, string='Норм төрөл', default='branch')
    norm_types = fields.Many2one('stock.norm.types', string='Төрөл' ,domain="[('active_is','=',True)]")
    norm_type_emp_check = fields.Boolean(default=False, copy=False)
    check_approve_qty = fields.Boolean(default=False, copy=False)
    account_partner_id = fields.Many2one(related="branch_id.partner_id", string="Төслийн харилцагч", store=True)
    
    def all_other_expense_done_qty(self):
        other_ids = self.env['stock.product.other.expense'].search([])
        for item in other_ids:
            item.product_expense_line.get_done_qty()
 
    # Норм төрлөөс хамаарч талбар гаргах
    @api.onchange('norm_type')
    def get_norn_type_check(self):
        for i in self:
            if i.norm_type == 'branch':
                i.norm_type_emp_check = False
            elif i.norm_type == 'department':
                i.norm_type_emp_check = True
            else:
                i.norm_type_emp_check = False

    @api.onchange('transaction_value_id')
    def onchange_transaction_value_id(self):
        if self.transaction_value_id:
            self.description = self.transaction_value_id.name
            self.account_id = self.transaction_value_id.account_id.id
   # if self.transaction_value_id.analytic_distribution:
   #     self.account_analytic_id=self.transaction_value_id.account_analytic_id.id
            if self.transaction_value_id.analytic_distribution:
                self.analytic_distribution=self.transaction_value_id.analytic_distribution
            if self.norm_type:
                self.norm_type = self.transaction_value_id.norm_type
    
    @api.onchange('norm_type')
    def onchange_norm_type_id(self):
        if self.norm_type == '':
            self.is_employee = True
            
    # Бараа материалын шаардахаас удамшуусан
    def action_next_stage(self):
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if next_flow_line_id:
            user_id = self.env['res.users'].sudo().search([('partner_id','=',self.partner_id.id)]) or self.create_uid
            if next_flow_line_id._get_check_ok_flow(self.branch_id, False, self.create_uid):
                if next_flow_line_id.state_type == 'sent':
                    self.check_approve_qty = True
                    self.action_to_send()
                if next_flow_line_id.state_type == 'done':
                    self.action_to_confirm()
                    # Батлаглагдах үед нормын гүйцэтгэл нэмэгдэх
                    for line in self.product_expense_line:
                        if line.approved_qty <= 0.0:
                            raise UserError('Зөвшөөрсөн тоо хэмжээг бүртгэнэ үү!')
                        else:
                            line.norm_id.reference_qty += line.qty
                    #  
                if next_flow_line_id.state_type!='done':
                    self.update_available_qty()
                self.flow_line_id = next_flow_line_id
                self.env['dynamic.flow.history'].create_history(next_flow_line_id, 'shaardah_id', self)
                self.send_chat_employee(self.sudo().partner_id)
                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(self.branch_id, self.sudo().user_id.department_id, self.create_uid)
                    if send_users:
                        self.send_chat_next_users(send_users.mapped('partner_id'))
            else:
                raise UserError('Та батлах хэрэглэгч биш байна')

    # Бараа материалын шаардахаас удамшуусан
    def action_to_cancel(self):
        # Цуцлах үед нормын гүйцэтгэл хасах
        if self.state == 'confirmed':
            for line in self.product_expense_line:
                line.norm_id.reference_qty -= line.qty
        self.state = 'cancelled'
        self.expense_picking_ids.action_cancel()

    parent_id = fields.Many2one('stock.norm', string='Parent ID', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Бараа', required=True)
    norm_qty = fields.Float(string='Норм', default=0)
    
    #Гүйлгээний утга сонгохоор харилцач сонгогдоно
    @api.onchange('transaction_value_id')
    def onchange_norm_type_id(self):
        if self.transaction_value_id and self.transaction_value_id.partner_id:
            self.partner_id = self.transaction_value_id.partner_id.id

    def action_to_confirm(self):
        # Батлах - Агуулахын менежер батлах
        # if self.warehouse_id.confirm_user_id:
        #     if self.warehouse_id.confirm_user_id.id != self.env.user.id:
        #         raise UserError(_(u'Та зарлага хийх эрхгүй байна! \n "%s" хэрэглэгч батлах ёстой'%self.warehouse_id.confirm_user_id.name))

        # Гарах байрлалыг олох
        dest_loc = self.env['stock.location'].sudo().search(
                        [('usage','=','customer')], limit=1)

        if not dest_loc:
            raise UserError(_(u'Зарлагадах байрлал олдсонгүй!'))

        tran_value = ""
        if self.transaction_value_id:
            tran_value = self.transaction_value_id.name +', '
        if self.description:
            tran_value += self.description
        for item in self:
            accountant_id =False
            if item.history_flow_ids:
                for history_line in item.history_flow_ids:
                    history_ids = self.env['dynamic.flow.history'].search([('shaardah_id','=',item.id)])
                    dynamic_id = self.env['dynamic.flow.line'].search([('id','in',history_ids.ids),('state_type','=','done')], limit=1)
                    real_user_id = self.env['dynamic.flow.history'].search([('flow_line_id','=',dynamic_id.id)], limit=1)
                    if real_user_id:
                        accountant_id = real_user_id.user_id

        sp_id = self.env['stock.picking'].create(
            {'picking_type_id': self.warehouse_id.out_type_id.id,
             'state': 'draft',
             'move_type': 'one',
             'partner_id': self.account_partner_id.id if self.account_partner_id and self.is_partner == True else self.partner_id.id if self.parent_id else False,
             'eh_barimt_user_id': self.create_uid.id,
             'shaardah_partner_id': self.partner_id.id,
             'scheduled_date': self.date_required,
             'location_id': self.warehouse_id.lot_stock_id.id,
             'location_dest_id': dest_loc.id,
             'origin': self.name if self.name else '' + u' - Бусад зарлага хийх, '+tran_value if tran_value else '',
             'other_expense_id': self.id,
             'stock_expense_accountant':accountant_id.id if accountant_id else False,
             'note':self.description if self.description else '',
            })

        for line in self.product_expense_line:
            price_unit = 0
            line.price_unit = price_unit

            desc = self.name+' - '+tran_value
            vals = self.get_prepare_stock_move_line(line, sp_id, price_unit, desc, dest_loc)
            line_id = self.env['stock.move'].create(vals)
            line.move_ids = [(4, line_id.id)]

        con = dict(self._context)
        con['from_code'] = True

        sp_id.with_context(con).action_confirm()
        sp_id.scheduled_date = self.date_required
        # sp_id.action_assign()
        # self.expense_picking_id = sp_id.id

        # Батлах
        self.validator_id = self.env.user.id
        self.date_validator = datetime.now()
        self.message_post(body=u"%s - батлагдлаа" % self.validator_id.name)
        self.state = 'done'

class mnTransactionValue(models.Model):
    _inherit = 'mn.transaction.value'

    norm_type = fields.Selection([('branch','Оффис'),('department','Салхит')],tracking=True, string='Норм төрөл', default='branch')
    partner_id = fields.Many2one('res.partner', string=u'Харилцагч')

class resPartner(models.Model):
    _inherit = 'res.branch'

    partner_id = fields.Many2one('res.partner', string="Харилцагч")