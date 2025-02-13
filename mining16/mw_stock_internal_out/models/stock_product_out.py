
# -*- coding: utf-8 -*-

from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError

from datetime import datetime, time
import collections
import time
import xlsxwriter
from io import BytesIO
import base64
try:
    # Python 2 support
    from base64 import encodestring
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodestring
    
from datetime import datetime, timedelta

import logging
_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    interout_id = fields.Many2one('stock.product.interout', 'Internal expense ID')

    def action_view_interout_id_mw(self):
        view = self.env.ref('mw_stock_internal_out.stock_product_interout_form_view')
        return {
            'name': 'Шаардах',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.product.interout',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            # 'target': 'new',
            'res_id': self.interout_id.id,
            'context': dict(
                self.env.context
            ),
        }

    def action_cancel(self):
        res = super(StockPicking, self).action_cancel()
        for item in self:
            if item.interout_id and item.interout_id.state!='cancelled' and not item.backorder_id:
                item.interout_id.action_to_cancel()
        return res

class StockProductOtherExpenseInterout(models.Model):
    _name = 'stock.product.interout'
    _description = 'Stock Product Internal expense'
    _order = 'date desc'
    _inherit = ['mail.thread','mail.activity.mixin','analytic.mixin']

    # ==================================
    confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True)

    @api.onchange('analytic_distribution')
    def _onchange_analytic_distribution(self):
        if self.analytic_distribution:
            for line in self.product_expense_line:
                line.analytic_distribution = self.analytic_distribution

    def print_word(self):
        # report = self.env['ir.actions.report']._get_report_from_name('test')
        # report=self.env['ir.actions.report'].browse(2278)
        report=self.env['ir.actions.report'].search([('model','=','stock.product.interout')],limit=1)
        context = dict(self.env.context)
        datas = self #.env['stock.product.interout'].search([('id', '=', 743)])
        data={}
        template_name='shaardah'
        file_name = self.name+'.pdf'
        pdf = report.with_context(context).render_doc_doc(datas, data=data)[0]
        options = {
            'page-size': 'A4',
            'encoding': "UTF-8",
        } 
        report_type='.pdf'
        out = encodestring(pdf)
        excel_id = self.env['report.pdf.output'].create({'data': out, 'name': template_name+report_type})
         
        return {
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.pdf.output&id=" + str(excel_id.id) + "&filename_field=filename&field=data&filename=" + excel_id.name,
            'target': 'new',
        }         
        

    @api.model
    def _get_user(self):
        return self.env.user.id

    # Columns
    ###### name-n readonly tur avav#############
    name = fields.Char(u'Дугаар', copy=False, readonly=True) 
    company_id = fields.Many2one('res.company', 'Компани', default=lambda self: self.env.user.company_id)
    branch_id = fields.Many2one('res.branch', 'Салбар', default=lambda self: self.env.user.branch_id, required=True)
    description = fields.Text(u'Description',
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    date = fields.Datetime(u'Үүсгэсэн огноо', default=datetime.now(), readonly=True)
    date_required = fields.Date(u'Товлосон огноо', required=True,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

    warehouse_id = fields.Many2one('stock.warehouse', 'Агуулах', required=True, copy=True,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    location_id = fields.Many2one(related='warehouse_id.lot_stock_id', readonly=True)

    user_id = fields.Many2one('res.users', 'Хэрэглэгч', default=_get_user, readonly=True)
    validator_id = fields.Many2one('res.users', 'Батласан Хэрэглэгч', readonly=True, copy=False,)

    partner_id = fields.Many2one('res.partner', u'Хариуцагч Харилцагч', default=lambda self: self.env.user.partner_id, copy=False,
        help=u"Хэрэв ажилтан сонгогдвол тухайн ажилтаны 'Ашиглалтанд байгаа хангамжийн материал'-ын бүртгэлд бүртгэгдэнэ.",
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    # Санхүү
    account_id = fields.Many2one('account.account', u'Данс', copy=False,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]},)
    branch_id = fields.Many2one('res.branch', u'Салбар', copy=True, required=False,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

    department_id = fields.Many2one('hr.department', u'Хэлтэс/нэгж', copy=True, help=u"Хэрэв хэлтэс дээрх зардал бол сонгоно", required=True)

    employee_id = fields.Many2one('hr.employee', u'Ажилтан',
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    
    date_user = fields.Datetime(u'User Date', readonly=True, copy=False,)
    date_validator = fields.Datetime(u'Батласан Огноо', readonly=True, copy=False,)

    product_expense_line = fields.One2many('stock.product.interout.line', 'parent_id', string=u'Expense line', copy=True,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]},
        help=u"Бараа зарлагадах мэдээлэл")


    categ_ids = fields.Many2many('product.category', string='Ангилал', )
    expense_picking_ids = fields.One2many('stock.picking', 'interout_id', u'Зарлага хийсэн хөдөлгөөнүүд', readonly=True, copy=False,)
    expense_picking_count = fields.Integer(u'Зарлагын баримтын тоо', readonly=True, compute='_comute_expense_picking_count')

    state = fields.Selection([
            ('cancelled', 'Цуцалсан'),
            ('draft', 'Ноорог'),
            ('confirmed', 'Баталсан'),
            ('done', 'Дууссан')],
            default='draft', string='State', tracking=True)
    history_ids = fields.One2many('stock.product.interout.history', 'expense_id', 'Түүхүүд')
    import_product_ids = fields.Many2many('product.product', string="Импортлох Бараанууд")
    import_employee_ids = fields.Many2many('hr.employee', string="Импортлох Ажилтанууд Буруу") # Хасагдах код
    import_partner_ids = fields.Many2many('res.partner', string="Импортлох Ажилтанууд", domain=([('employee','=',True)]))
    import_qty = fields.Float('Импортлох тоо хэмжээ', default=1)
    product_id = fields.Many2one(related='product_expense_line.product_id', string='Бараа')

    technic_id = fields.Many2one('technic.equipment', u'Техник', copy=False,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})

    equipment_id = fields.Many2one('factory.equipment', string='Equipment',  copy=False,
        states={'confirmed': [('readonly', True)], 'done': [('readonly', True)]})
    
    def change_accounts(self):
        for line in self.product_expense_line:
            if self.account_id:
                line.account_id = self.account_id.id
            if self.analytic_distribution:
                line.analytic_distribution = self.analytic_distribution

    def change_history(self):
        obj_min = 5000
        obj = self.env['dynamic.flow.history']
        objs = self.env['stock.product.interout.history'].search([
            ('create_ok','=',False),
            ], limit=obj_min)
        i = len(objs)

        for item in objs:
            obj_id = obj.create({
                'user_id': item.user_id.id,
                'shaardah_id': item.expense_id.id,
                'date': item.date,
                'flow_line_id': item.flow_line_id.id,
            })
            obj_id.create_date = item.create_date
            obj_id.create_uid = item.create_uid.id
            item.create_ok = True
            obj.compute_spend_time('shaardah_id', item.expense_id)
            _logger.info('flow history shiljuuleh %s of %s'%(i,obj_min))
            i -= 1

    @api.depends('expense_picking_ids')
    def _comute_expense_picking_count(self):
        for item in self:
            item.expense_picking_count = len(item.expense_picking_ids)

    @api.onchange('partner_id')
    def onchange_department_id_partner(self):
        for item in self:
            emp_obj = self.env['hr.employee']
            if item.partner_id:
                emp_id = emp_obj.search([('partner_id','=',item.partner_id.id)])
                if emp_id and emp_id.department_id:
                    item.department_id = emp_id.department_id.id


    def action_employee_import(self):
        if not self.import_product_ids:
            raise UserError(u'Импортлох бараагаа оруулна уу!!')

        if self.is_employee:
            if not self.import_partner_ids:
                raise UserError(u'Импортлох ажилтанаа оруулна уу!!')
            for item in self.import_product_ids:
                for emp in self.import_partner_ids:
                    line_id = self.env['stock.product.interout.line'].create({
                        'parent_id': self.id,
                        'res_partner_id': emp.id,
                        'product_id': item.id,
      # 'account_id': self.transaction_value_id.account_id.id if self.transaction_value_id and self.transaction_value_id.account_id else False,
                        'qty': self.import_qty or 1,
                        })
                    if self.account_analytic_ids:
                        line_id.account_analytic_ids = [(6,0,self.account_analytic_ids.ids)]
            self.import_partner_ids = False

        else:
            for item in self.import_product_ids:
                line_id = self.env['stock.product.interout.line'].create({
                    'parent_id': self.id,
                    'res_partner_id': self.partner_id.id,
                    'product_id': item.id,
     # 'account_id': self.transaction_value_id.account_id.id if self.transaction_value_id and self.transaction_value_id.account_id else False,
                    'qty': self.import_qty or 1
                    })
                if self.account_analytic_ids:
                    line_id.account_analytic_ids = [(6,0,self.account_analytic_ids.ids)]
        self.import_product_ids = False
        self.import_qty = 1


    def update_last_date(self):
        expense_line_obj = self.env['stock.product.interout.line']
        for item in self.product_expense_line:
            partner_id = item.sudo().res_partner_id or self.sudo().partner_id
            prod_search = ' prl.product_id=%s '%item.product_id.id
            if len(item.product_id.product_tmpl_id.product_variant_ids)>1:
                prod_search = ' prl.product_id in %s '%(str(tuple(item.product_id.product_tmpl_id.product_variant_ids.ids)))
            query ="""
            SELECT
                pr.date_required
                FROM stock_product_other_expense_line AS prl
                LEFT JOIN stock_product_other_expense AS pr on (pr.id=prl.parent_id)
                WHERE %s and prl.res_partner_id=%s and pr.id!=%s
                ORDER BY pr.date_required DESC
                LIMIT 1
                """%(prod_search,partner_id.id,self.id)
            self.env.cr.execute(query)
            records = self.env.cr.fetchall()
            if records:
                item.last_date = records[0][0]

    def update_available_qty(self):
        for item in self.product_expense_line:
            item.update_available_qty()

    @api.depends('product_expense_line')
    def _methods_compute(self):
        # Нийт тоог олгох
        for obj in self:
            tot = 0
            for line in obj.product_expense_line:
                tot += line.qty * line.price_unit
            obj.total_amount = tot

    total_amount = fields.Float(compute=_methods_compute, store=True, string=u'Нийт дүн')

    # asset_category_id = fields.Many2one(comodel_name='account.asset.category', string=u'Хөрөнгийн ангилал', domain=[('is_consumable_product','=',True)])

    #
    # def write(self, vals):
    #     res = super(StockProductOtherExpense, self).write(vals)
    #     p_ids = [ l.product_id for l in self.product_expense_line ]
    #     dup_ids = [item for item, count in collections.Counter(p_ids).items() if count > 1]
    #     if dup_ids:
    #         names = [d.name for d in dup_ids]
    #         raise UserError(_(u'"%s" бараанууд давхар бүртгэгдсэн байна!' % (', '.join(names))))

    #     return res

    def unlink(self):
        for s in self:
            if s.state not in ['draft','cancelled']:
                raise UserError(_(u'Ноорог болон Цуцлагдсан төлөвтэй бичлэгийг устгаж болно!'))
        return super(StockProductOtherExpense, self).unlink()

    # @api.onchange('department_id')
    # def onchange_department_id(self):
    #     if self.department_id:
    #         # self.description = self.transaction_value_id.name
    #         distribution_model =self.env['account.analytic.distribution.model'].search([('department_id','=',self.department_id.id),
    #                                                                                     ('company_id','=',self.env.company.id)],limit=1)
    #         print ('distribution_model ',distribution_model)
    #         self.analytic_distribution=distribution_model.analytic_distribution
    #         print(distribution_model.analytic_distribution, type(distribution_model.analytic_distribution))


    def action_to_draft(self):
        if self.expense_picking_ids:
            self.expense_picking_ids.filtered(lambda r: r.picking_type_id.code == 'outgoing').action_cancel()
            self.state = 'draft'
        elif not self.expense_picking_ids:
            self.state = 'draft'
        else:
            raise UserError(_(u'Хөдөлгөөн цуцлах боломжгүй, цуцлах шаардлагатай бол хөдөлгөөнийг эхлээд цуцлуулна уу!'))

    @api.onchange('user_id')
    def onchange_user(self):
        if self.user_id:
            emp = self.env['hr.employee'].sudo().search([('user_id','=',self.user_id.id)], limit=1)
            if emp:
                self.employee_id = emp.id
                self.department_id = emp.sudo().department_id.id
                self.onchange_employee_id()

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.sudo().employee_id.department_id.id
            self.partner_id = self.sudo().employee_id.partner_id.id
            self.branch_id = self.sudo().employee_id.user_id.branch_id.id or self.env.user.branch_id.id

    # @api.onchange('asset_category_id')
    # def onchange_asset_category_id(self):
    #     if self.asset_category_id:
    #         self.account_id = self.asset_category_id.account_asset_id.id
    #     else:
    #         self.account_id = False

    def action_to_cancel(self):
        self.state = 'cancelled'
        self.expense_picking_ids.filtered(lambda r: r.picking_type_id.code == 'outgoing').action_cancel()

    # CUSTOM

    def action_to_print(self):
        model_id = self.env['ir.model'].search([('model','=','stock.product.interout')], limit=1)
        template = self.env['pdf.template.generator'].search([('model_id','=',model_id.id)], limit=1)

        if template:
            res = template.print_template(self.id)
            return res
        else:
            raise UserError(_(u'Хэвлэх загварын тохиргоо хийгдээгүй байна, Системийн админд хандана уу!'))


    def action_to_send(self):
        if self.product_expense_line:
            _logger.info(u'-***********-NUMBER--*************%d %s \n' % (self.id, self.name))
            if not self.name:
                self.name = self.env['ir.sequence'].next_by_code('stock.product.interout')
            self.user_id = self.env.user.id
            self.date_user = datetime.now()
            self.state = 'sent'
        else:
            raise UserError(_(u'Бараа зарлагадах мэдээллийг оруулна уу!'))

        tran_value = ""
        if self.description:
            tran_value += self.description
        self.state = 'sent'

    def get_prepare_stock_move_line(self, line, sp_id, price_unit, desc, dest_loc):
        technic_id=(line.technic_id and line.technic_id.id) or (self.technic_id and self.technic_id.id) or False
        return {
                'name': desc,
                'picking_id': sp_id.id,
                'product_id': line.product_id.id,
                'product_uom': line.product_id.uom_id.id,
                'product_uom_qty': line.qty,
                'price_unit': price_unit,
                'location_id': self.warehouse_id.lot_stock_id.id,
                'location_dest_id': dest_loc.id,
                'state': 'draft',
                'interout_line_id': line.id,
                'technic_id2' : technic_id
            }

    def action_to_confirm(self):
        # Батлах - Агуулахын менежер батлах
        # if self.warehouse_id.confirm_user_id:
        #     if self.warehouse_id.confirm_user_id.id != self.env.user.id:
        #         raise UserError(_(u'Та зарлага хийх эрхгүй байна! \n "%s" хэрэглэгч батлах ёстой'%self.warehouse_id.confirm_user_id.name))
        if not self.name:
            self.name = self.env['ir.sequence'].next_by_code('stock.product.interout')

        # Гарах байрлалыг олох
        dest_loc = self.env['stock.location'].sudo().search(
                        [('usage','=','customer')], limit=1)

        if not dest_loc:
            raise UserError(_(u'Зарлагадах байрлал олдсонгүй!'))

        tran_value = ""
        if self.description:
            tran_value += self.description
        for item in self:
            accountant_id =False

        sp_id = self.env['stock.picking'].create(
            {'picking_type_id': self.warehouse_id.out_type_id.id,
             'state': 'draft',
             'move_type': 'one',
             'partner_id': self.partner_id.id or False,
             'scheduled_date': self.date_required,
             'location_id': self.warehouse_id.lot_stock_id.id,
             'location_dest_id': dest_loc.id,
             'origin': self.name if self.name else '' + u' - Бусад зарлага хийх, '+tran_value if tran_value else '',
             'interout_id': self.id,
             'stock_expense_accountant':accountant_id.id if accountant_id else False,
             'note':self.description if self.description else '',
             # 'technic_id':self.technic_id and self.technic_id.id or False
            })

        for line in self.product_expense_line:
            price_unit = 0
            line.price_unit = price_unit
            name =self.name and self.name or ''
            desc =name +' - '+tran_value
            vals = self.get_prepare_stock_move_line(line, sp_id, price_unit, desc, dest_loc)
            line_id = self.env['stock.move'].create(vals)

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
        self.state = 'confirmed'


    def action_to_done(self):
        if 'done' not in self.expense_picking_ids.mapped('state'):
            raise UserError(_(u'Барааны зарлагадах хөдөлгөөн дуусаагүй байна!'))

        self.message_post(body=u"Барааг зарлагадаж дууссан")
        self.state = 'done'
        return True


    def get_user_signature(self,ids):
        report_id = self.browse(ids)
        html = '<table>'
        print_flow_line_ids = report_id.flow_id.line_ids.filtered(lambda r: r.is_print)
        history_obj = self.env['dynamic.flow.history']
        for item in print_flow_line_ids:
            his_id = history_obj.search([('flow_line_id','=',item.id),('shaardah_id','=',report_id.id)], limit=1)
            image_str = '________________________'
            if his_id.user_id.digital_signature_from_file:
                image_buf = (his_id.user_id.digital_signature_from_file).decode('utf-8')
                image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />'%(image_buf)
            elif his_id.user_id.digital_signature:
                image_buf = (his_id.user_id.digital_signature).decode('utf-8')
                image_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />'%(image_buf)
            user_str = '________________________'
            if his_id.user_id:
                user_str = his_id.user_id.name
            html += u'<tr><td><p>%s</p></td><td>%s</td><td> <p>/%s/</p></td></tr>'%(item.display_name,image_str,user_str)
        html += '</table>'
        return html

    def get_line_ids(self, ids):
        headers = [
        u'Бараа',
        u'Хэмжих нэгж',
        u'Тоо',
        ]
        report_id = self.browse(ids)
        if report_id.is_employee:
            headers = [
            u'Бараа',
            u'Хэмжих нэгж',
            u'Тоо',
            u'Ажилтан',
            u'Гарын Үсэг',
            ]

        datas = []


        lines = report_id.product_expense_line

        sum1 = 0
        sum2 = 0
        sum3 = 0
        nbr = 1
        for line in lines:
            sum1 += line.qty
            if report_id.is_employee:
                temp = [
                u'<p style="text-align: left; height: 20px;">'+(line.product_id.display_name)+u'</p>',
                u'<p style="text-align: center;">'+(line.uom_id.name)+u'</p>',
                "{0:,.0f}".format(line.qty) or '',
                line.sudo().employee_id.display_name or '',
                '',
                ]
            else:
                temp = [
                u'<p style="text-align: left;">'+(line.product_id.display_name)+u'</p>',
                u'<p style="text-align: center;">'+(line.uom_id.name)+u'</p>',
                "{0:,.0f}".format(line.qty) or '',
                ]
            nbr += 1
            datas.append(temp)
        if report_id.is_employee:
            temp = [
            u'',
            u'<p style="text-align: center; font-weight: bold; ">Нийт дүн</p>',
            "{0:,.0f}".format(sum1) or '',
            '',
            ''
            ]
        else:
            temp = [
            u'',
            u'<p style="text-align: center; font-weight: bold; ">Нийт дүн</p>',
            "{0:,.0f}".format(sum1) or '',
            ]
        if not datas:
            return False
        datas.append(temp)
        res = {'header': headers, 'data':datas}
        return res

    def get_company_logo(self, ids):

        report_id = self.browse(ids)
        company_id = self.env.user.company_id
        image_buf = company_id.logo_web
        image_str = '<img alt="Embedded Image" width="100" src="data:image/png;base64,'+image_buf+'" />'
        return image_str

    def action_view_edit_expense_line(self):
        if not self.product_expense_line:
            return False

        context = {}
        context['create']= False
        tree_view_id = self.env.ref('mw_stock_moves.stock_product_other_expense_line_tree_view').id
        # form_view_id = self.env.ref('account.view_move_form').id
        action = {
                'name': self.name,
                'view_mode': 'tree',
                'res_model': 'stock.product.interout.line',
                'views': [(tree_view_id, 'tree')],
                'view_id': tree_view_id,
                'domain': [('id','in',self.product_expense_line.ids)],
                'type': 'ir.actions.act_window',
                'context': context,
                'target': 'current'
            }
        return action


    def action_view_expense_picking_ids(self):
        tree_view_id = self.env.ref('stock.vpicktree').id
        form_view_id = self.env.ref('stock.view_picking_form').id
        return {
            'name': 'Хөдөлгөөн',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(tree_view_id, 'tree'), (form_view_id, 'form')],
            'view_id': tree_view_id,
            'domain': [('id','in',self.expense_picking_ids.ids)],
            'context': {},
        }

    def set_partner(self):
        expenses =  self.env['stock.product.interout'].sudo().search([('id','!=',False)])
        for item in expenses:
            # item.partner_id = item.employee_id.partner_id
            for line in item.product_expense_line:
                line.res_partner_id = line.employee_id.partner_id

    def change_analytic_from_partner(self):
        for line in self.product_expense_line: 
            if line.res_partner_id and not line.technic_id:

                employee = self.env['hr.employee'].search([('partner_id','=',line.res_partner_id.id)], limit=1)
                department_id = employee and employee.department_id
                distribution_model =self.env['account.analytic.distribution.model'].search([
                                                                                ('department_id','=',department_id.id),
                                                                                ('company_id','=',self.env.company.id),
                                                                                ],limit=1)
                line.analytic_distribution=distribution_model.analytic_distribution
    def change_analytic_from_partner_new(self):
        if self.analytic_distribution:
            for line in self.product_expense_line:
                line.analytic_distribution = self.analytic_distribution

class StockProductInteroutLine(models.Model):
    _name = 'stock.product.interout.line'
    _description = 'Stock Product Internal expense Line'
    _inherit = ["analytic.mixin","mail.thread", "mail.activity.mixin"]

    @api.model
    def _get_default_partner(self):
        parent_id =False
        if self.env.context.get('params', False) and self.env.context['params'].get('model', False) == 'stock.product.interout':
            parent_id = self.env['stock.product.interout'].browse(self.env.context['params'].get('id', False))
        if parent_id and parent_id.partner_id:
            return parent_id.partner_id.id
        else:
            return False

    
    # Columns
    parent_id = fields.Many2one('stock.product.interout', 'Parent ID', ondelete='cascade')
    product_id = fields.Many2one('product.product', u'Бараа', required=True)
    product_standard_price = fields.Float(store=True, string='Барааны өртөг')
    product_total_price = fields.Float(store=True, string='Барааны нийт өртөг')
    product_sale_price = fields.Float(store=True, string='Барааны зарах үнэ')
    uom_id = fields.Many2one(related='product_id.uom_id', string=u'Хэмжих нэгж', store=True, readonly=True, )
    categ_id = fields.Many2one(related='product_id.categ_id', string=u'Ангилал', store=True, readonly=True, )
    qty = fields.Float(u'Тоо хэмжээ', required=True, default=1,)
    price_unit = fields.Float(u'Нэгж үнэ', required=True, default=0,)
    available_qty = fields.Float('Үлдэгдэл', readonly=True, store=True, compute='update_available_qty')
    available_qty_template = fields.Float('Үлдэгдэл Хөрвөх Нийт', readonly=True, store=True, compute='update_available_qty')
    reserved_qty = fields.Float('Нөөцлөгдсөн', readonly=True, store=True, compute='update_available_qty')
    diff_qty = fields.Float('Зөрүү', readonly=True, compute='_compute_diff_qty')
    employee_id = fields.Many2one('hr.employee', string=u'Ажилтан буруу')
    res_partner_id = fields.Many2one('res.partner', string=u'Ажилтан', domain=([('employee','=',True)]), default=_get_default_partner)
    last_date = fields.Date(string=u'Сүүлд авсан огноо')
    list_price = fields.Float('Нэгж Үнэ')
    sub_total = fields.Float('Дэд дүн', compute='_sum_sub_total', store=True)
    date_required = fields.Date(related='parent_id.date_required', readonly=True)
    branch_id = fields.Many2one('res.branch', related='parent_id.branch_id', readonly=True)
    department_id = fields.Many2one('hr.department', related='parent_id.department_id', readonly=True)
    account_id = fields.Many2one('account.account', u'Данс', copy=False)
    # account_analytic_ids = fields.Many2one('account.analytic.account', u'Аналитик данс', copy=False)
    # analytic_distribution = fields.
    # fleet_id = fields.Many2one('fleet.vehicle', 'Техник /Машин/')

 # technic_id = fields.Many2one(related='parent_id.technic_id')
    technic_id = fields.Many2one('technic.equipment', u'Техник', copy=False,)
    equipment_id = fields.Many2one('factory.equipment', string='Equipment',  copy=False,)
    



    @api.depends('parent_id', 
                'parent_id.analytic_distribution', 
                 'product_id',
                 'parent_id.department_id',
                  'technic_id',
                  'equipment_id'
                 )
    def _compute_analytic_distribution(self):
        for line in self:
            analytic_distribution=False
            if line.parent_id and line.parent_id.partner_id:
                line.res_partner_id = line.parent_id.partner_id.id
            account_id=False
            print ('line.product_id ',line.product_id)
            print ('line.product_idcateg_id ',line.product_id.categ_id)
            technic_id=False
            equipment_id=False
            if line.technic_id:
                technic_id=line.technic_id
            elif line.parent_id.technic_id:
                technic_id=line.parent_id.technic_id
            if line.equipment_id:
                equipment_id=line.equipment_id
            elif line.parent_id.equipment_id:
                equipment_id=line.parent_id.equipment_id
            print ('technic_id ',technic_id)
            if technic_id:
                product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                ('technic_ids','in',technic_id.id)], limit=1)
                _logger.info('product_account_obj ====== %s '%(product_account_obj))
                account_id = product_account_obj.account_id.id
                analytic_distribution=product_account_obj.analytic_distribution
            elif equipment_id:
                product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                ('equipment_ids','in',equipment_id.id)], limit=1)
                account_id = product_account_obj.account_id.id
                analytic_distribution=product_account_obj.analytic_distribution
            # elif line.parent_id.department_id:
            #     product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
            #                                                                     ('branch_ids','in',line.parent_id.branch_id.id),
            #                                                                     ('category_ids','in',line.product_id.categ_id.id),
            #                                                                     ('department_ids','in',line.parent_id.department_id.id),
            #                                                                     ('technic_ids','=',False),
            #                                                                     ('equipment_ids','=',False)
            #                                                                     ], limit=1)
            #     account_id = product_account_obj.account_id.id
            #     analytic_distribution=product_account_obj.analytic_distribution
            if not account_id: #technikgui
                product_account_obj = self.env['product.account.config'].search([('company_id','=',line.parent_id.company_id.id),
                                                                                ('branch_ids','in',line.parent_id.branch_id.id),
                                                                                ('category_ids','in',line.product_id.categ_id.id),
                                                                                ('technic_ids','=',False),
                                                                                #  ('department_ids','=',False),
                                                                                ('equipment_ids','=',False)], limit=1)
                account_id = product_account_obj.account_id.id
            if account_id:
                if not line.account_id:
                    line.account_id=account_id
            if analytic_distribution:
                line.write({'analytic_distribution':analytic_distribution})
            elif line.res_partner_id and not technic_id and analytic_distribution ==False:
                employee = self.env['hr.employee'].search([('partner_id','=',line.res_partner_id.id)], limit=1)
                department_id = employee and employee.department_id
                _logger.info('employee %s '%(employee))
                distribution_model =self.env['account.analytic.distribution.model'].search([
                                                                                ('department_id','=',department_id.id),
                                                                                ('company_id','=',self.env.company.id),
                                                                                ],limit=1)
                _logger.info('distribution_model %s '%(distribution_model))
                line.analytic_distribution=distribution_model.analytic_distribution
            elif line.parent_id and line.parent_id.analytic_distribution and not technic_id:
                _logger.info('elseee distribution_model %s '%(line.parent_id.analytic_distribution))
                line.analytic_distribution = line.parent_id.analytic_distribution
                
                
   #  @api.onchange('parent_id', 'parent_id.analytic_distribution','res_partner_id', 'product_id')
   #  def _compute_analytic_distribution(self):
   #      for line in self:
   #          print ('line+++ ',line)
   #          analytic_distribution=False
   #          if line.res_partner_id:
   #              employee = self.env['hr.employee'].search([('partner_id','=',line.res_partner_id.id)], limit=1)
   #              print('12341244214',employee)
   #              department_id = employee and employee.department_id
   #              print('saifjaosihfpaof',department_id)
   #              _logger.info('employee %s '%(employee))
   #              distribution_model =self.env['account.analytic.distribution.model'].search([('department_id','=',department_id.id),
   #                                                                                          ('company_id','=',self.env.company.id)],limit=1)
   #              print('2189r12gbr9823',distribution_model)
   #              _logger.info('distribution_model %s '%(distribution_model))
   #              analytic_distribution=distribution_model.analytic_distribution
   #          _logger.info('line.res_partner_id %s '%(line.res_partner_id))
   #          _logger.info('analytic_distribution %s '%(analytic_distribution))
   #          if analytic_distribution:
   #              line.analytic_distribution = analytic_distribution
   #          elif line.parent_id and line.parent_id.analytic_distribution:
   #              line.analytic_distribution = line.parent_id.analytic_distribution
   # # if line.parent_id and line.parent_id.transaction_value_id:
   # #     line.account_id = line.parent_id.transaction_value_id.account_id.id if line.parent_id.transaction_value_id else False
   #          print('analytic_distribution', line.parent_id.analytic_distribution, type(line.parent_id.analytic_distribution))

    # @api.depends('parent_id', 'paren')
    # def _compute_account(self):

    # @api.model
    # def create(self, values):
    #     res = super(StockProductInteroutLine, self).create(values)
    #     active = self.env.context.get('active_id')
    #     print('active aa: ', active, active._origin.id)
    #     return res

    @api.onchange('product_id')
    # @api.depends('product_id')
    def onchange_product_price(self):
        for obj in self:
            obj.product_standard_price = obj.product_id.standard_price
            obj.product_sale_price = obj.product_id.list_price

    @api.onchange('product_id','qty')
    # @api.depends('product_id','qty')
    def compute_total_price(self):
        for obj in self:
            obj.product_total_price = obj.product_id.standard_price*obj.qty
            

    @api.depends('parent_id.warehouse_id','product_id')
    def update_available_qty(self):
        quant_obj = self.env['stock.quant']
        for item in self:
            quant_ids = []
            quant_temp_ids = []
            domain = self.env['product.product'].get_qty_template_domain(item.product_id)
            if item.parent_id.warehouse_id:
                quant_ids = quant_obj.search([('product_id','=',item.product_id.id),('location_id.set_warehouse_id','=',item.parent_id.warehouse_id.id),('location_id.usage','=','internal')])
                domain+=[('location_id.set_warehouse_id','=',item.parent_id.warehouse_id.id),('location_id.usage','=','internal')]
                quant_temp_ids = quant_obj.search(domain)
            else:
                quant_ids = quant_obj.search([('product_id','=',item.product_id.id),('location_id.usage','=','internal')])
                domain+=[('location_id.usage','=','internal')]
                quant_temp_ids = quant_obj.search(domain)
            item.available_qty_template = sum(quant_temp_ids.mapped('quantity'))
            reserved_qty_template = sum(quant_temp_ids.mapped('quantity'))
            item.available_qty = sum(quant_ids.mapped('quantity'))
            item.reserved_qty = sum(quant_ids.mapped('reserved_quantity'))

    # def write(self, values):
    #     if 'qty' in values:
    #           for line in self:
    #               if line.parent_id.state != 'draft':
    #                   line.parent_id.message_post_with_view('mw_stock_moves.track_po_line_template',
    #                                                        values={'line': line, 'qty': values['qty']},
    #                                                    subtype_id=self.env.ref('mail.mt_note').id)
    #     return super(StockProductInteroutLine, self).write(values)

    def unlink(self):
        for item in self:
            if item.parent_id.state != 'draft':
                item.parent_id.message_post_with_view('mw_stock_moves.track_po_line_template_delete',
                                                        values={'line': item},
                                                        subtype_id=self.env.ref('mail.mt_note').id)
        return super(StockProductInteroutLine, self).unlink()

    @api.depends('list_price','qty')
    def _sum_sub_total(self):
        for item in self:
            item.sub_total = item.list_price*item.qty

    # Зарах үнэ харсан хараагүй цэнэглэдэг байх
    @api.onchange('product_id')
    def onchange_list_price(self):
        if self.product_id:
            self.price_unit = self.product_id.standard_price
            self.list_price = self.product_id.list_price or self.product_id.standard_price

    @api.depends('available_qty','qty')
    def _compute_diff_qty(self):
        for item in self:
            if item.available_qty > item.qty:
                item.diff_qty = item.available_qty - item.qty
            else:
                item.diff_qty = 0


class stock_product_exepense_history(models.Model):
    _name = 'stock.product.interout.history'
    _description = 'stock product exepense history'
    _order = 'date desc'

    expense_id = fields.Many2one('stock.product.interout','Хүсэлт', ondelete='cascade')
    user_id = fields.Many2one('res.users','Өөрчилсөн хэрэглэгч')
    date = fields.Datetime('Огноо', default=fields.Datetime.now)
    create_ok = fields.Boolean('Create ok', default=False)


class product_product(models.Model):
    _inherit = 'product.product'

    def get_qty_template_domain(self, product_id):
        return [('product_id.product_tmpl_id','=',product_id.product_tmpl_id.id),('product_id','!=',product_id.id)]
