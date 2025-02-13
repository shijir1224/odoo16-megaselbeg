import base64
import os
from io import BytesIO# -*- coding: utf-8 -*-
from tempfile import NamedTemporaryFile
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, time, timedelta, date
import datetime
import xlrd
import xlsxwriter

class CampOrder(models.Model):
    _name = 'camp.order'
    _description = 'Camp Order'
    
    
    def default_name(self):
        # return False
        return self.env['ir.sequence'].next_by_code('camp.order')

    name = fields.Char(string='Name' , default=default_name , readonly=True)
    date = fields.Date(string='Огноо')
    partner_id = fields.Many2one('res.partner' , string='Харилцагч' , store=True , index=True)
    is_payment = fields.Boolean(string='Төлбөртэй эсэх', )
    payment_type = fields.Selection([('default','Үндсэн'),('nondefault','Гараар')] , string='Төлбөрийн төрөл' , store=True)
    company_id = fields.Many2one('res.company' , string='Компани' , store=True , index=True ,default=lambda self: self.env.company.id,)
    order_line = fields.One2many('camp.order.line','parent_id', string='Order line' ,)
    import_data = fields.Binary(string='Эксэл файл')
    invoice_id = fields.Many2one('account.move' , string='Нэхэмжлэл' , store=True , index=True)
    invoice_count = fields.Integer(compute='_invoice_count', string='Invoice count')
    
    def _get_dynamic_flow_line_id(self):
        return self.flow_find()

    def _get_default_flow_id(self):
        search_domain = []
        search_domain.append(('model_id.model', '=', 'camp.order'))
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    visible_flow_line_ids = fields.Many2many(
        'dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', track_visibility='onchange', index=True,
                                default=_get_dynamic_flow_line_id,
                                copy=False, domain="[('id','in',visible_flow_line_ids)]")

    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', track_visibility='onchange',
                           default=_get_default_flow_id,
                           copy=True, domain="[('model_id.model', '=', 'camp.order')]", index=True)
    flow_line_next_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
    flow_line_back_id = fields.Many2one(
        'dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    state = fields.Char(
        string='Төлөв', compute='_compute_state', store=True, index=True)
    categ_ids = fields.Many2many(
        'product.category', related='flow_id.categ_ids', readonly=True)
    is_not_edit = fields.Boolean(
        related="flow_line_id.is_not_edit", readonly=True)
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id',
                               string='Төлөв stage', store=True, index=True)
    state_type = fields.Char(string='Төлөвийн төрөл', compute='_compute_state_type', store=True)
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True), ('type_tax_use','=','sale')])
    total_amount = fields.Float(strin='Нийт Дүн ' , compute='_compute_total_price')
    tax_amount = fields.Float(strin='Татвар дүн' , compute='_compute_total_price')
    untax_amount = fields.Float(strin='Татваргүй дүн' , compute='_compute_total_price')	
    
    @api.depends('order_line.amount' , 'order_line.sub_total')
    def _compute_total_price(self):
        for obj in self:
            s_line = obj.order_line
            obj.total_amount = sum(s_line.mapped('sub_total'))
            obj.tax_amount = sum(s_line.mapped('price_tax'))
            obj.untax_amount = sum(s_line.mapped('price_subtotal'))

    @api.depends('flow_line_id')
    def _compute_state_type(self):
        for item in self:
            item.state_type = item.flow_line_id.state_type
   
    @api.depends('flow_id.line_ids', 'flow_id.is_amount')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                item.visible_flow_line_ids = self.env['dynamic.flow.line'].search(
                    [('flow_id', '=', item.flow_id.id), ('flow_id.model_id.model', '=', 'camp.order')])
            else:
                item.visible_flow_line_ids = []
    
    def flow_find(self, domain=[], order='sequence'):
        search_domain = []
        if self.flow_id:
            search_domain.append(('flow_id', '=', self.flow_id.id))
        search_domain.append(('flow_id.model_id.model', '=', 'camp.order'))
        return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find()
        else:
            self.flow_line_id = False
    
    def _invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_id.filtered(lambda x: x.type == 'in_refund'))
   
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

            if next_flow_line_id._get_check_ok_flow(False, False):
                self.flow_line_id = next_flow_line_id
                if self.flow_line_id.state_type == 'done':
                    self.action_done()
                    self.action_create_invoice()

                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(False, False)
            else:
                con_user = next_flow_line_id._get_flow_users(False, False)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(con_user.mapped('display_name'))
                raise UserError(
                    u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s' % confirm_usernames)
    
    def action_done(self):
        self.state = 'done'
    
    def action_draft(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
        else:
            raise UserError(_('You are not draft user'))
    
    def action_cancel(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
        else:
            raise UserError(_('You are not cancel user'))
        
                # raise UserError(_('You are not confirm user'))
    
    def view_invoice(self):
        action = {
            'name': _('Нэхэмжлэл'),
            'view_mode': 'form',
            'view_id': self.env.ref('account.view_move_form').id,
            'res_model': 'account.move',
            'context': "{'move_type':'out_invoice'}",
            'type': 'ir.actions.act_window',
            'res_id': self.invoice_id.id,
            }
        return action
    def action_create_invoice(self):
        # Хөрөнгө борлуулах
        move_obj = self.env['account.move']
        for item in self:
            if not item.partner_id.property_account_receivable_id:
                raise UserError(_("Харилцагч дээрх авлагын данс тохируулаагүй байна. %s !" % item.partner_id.display_name))
            line_vals = item.get_invoice_line()
            
            print('line_vals' , line_vals , type(line_vals))
            
            journal_id = self.env['account.journal'].search([('type','=','sale')] ,limit = 1)
            invoice_vals = {'partner_id': item.partner_id.id,
                            'ref': _('%s: %s sell' % (item.name, item.date)),
                            'date': item.date,
                            'invoice_date': item.date,
                            'move_type': 'out_invoice',
                            'invoice_user_id': self.env.uid,
                            'company_id': self.env.company.id,
                            'currency_id': self.env.company.currency_id.id,
                            'journal_id': journal_id.id,
                            'invoice_line_ids':line_vals,
                            }
            item.invoice_id = move_obj.create(invoice_vals)
            # Нэхэмжлэхийг баталж холбоотой журналын бичилт үүсэх
            item.invoice_id.action_post()
            # item.invoice_id = invoice_id.id
        # self.write({'state': 'sale'})

    
    @api.onchange('taxes_id')
    def onch_tax_id(self):
        for item in self:
            if item.taxes_id:
                for line in self.order_line:
                       line.tax_id = item.taxes_id.ids
    
    def import_data_line(self):
        """
        Эксэл файлаас ХА мөр импортлох функц
        """
        self.ensure_one()
        if not self.import_data:
            raise UserError(_('Please insert import data file'))
        if self.order_line and not self.env.context.get('base_wizard_confirmed', False):
            wizard = self.env['base.confirm.wizard'].create({'res_model': self._name,
                                                             'res_id': self.id,
                                                             'message': _('Үүссэн мөрүүд байна. Та оруулахдаа итгэлтэй байна уу?'),
                                                             'function_name': 'import_data_line'})

            action = self.sudo().env.ref('mw_base.action_base_confirm_wizard').read()[0]
            action['res_id'] = wizard.id
            return action
        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodebytes(self.import_data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise UserError(_('Reading file error. Checking for excel file!'))
        book = xlrd.open_workbook(fileobj.name)
        try:
            sheet = book.sheet_by_index(0)
        except:
            raise UserError(_("Sheet's number error"))
        nrows = sheet.nrows
        rowi = 1
        values = []
        price_unit = 0
        not_found_products = []
        for item in range(rowi, nrows):
            row = sheet.row(item)
            partner_name = str(row[0].value)
            room_name = str(row[1].value)
            block_name = str(row[2].value)
            if self.payment_type=='nondefault':
                price_unit = float(row[3].value)
            partner_id = self.env['res.partner'].search(['|', ('vat', '=', partner_name), ('name', 'ilike', partner_name)], limit=1)
            room_id = self.env['camp.room'].search(['|', ('name', '=', room_name), ('name', 'ilike', room_name)], limit=1)
            room_type = self.env['camp.room.type'].search(['|', ('name', '=', block_name), ('name', 'ilike', block_name)], limit=1)
            
            if not partner_id:
                not_found_products.append(partner_name)
                continue
            vals = {
                'parent_id': self.id,
                'partner_id': partner_id.id,
                'room_id': room_id.id,
                'room_type_id': room_type.id,
                'amount' :room_type.price_unit if price_unit else room_type.price_unit,
            }
            print('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' , vals)
            values.append((0, 0, vals))
        if not_found_products:
            raise UserError(_('Product with {0} code does not exist').format(str(list(set(not_found_products)))))
        self.update({'order_line': values})

    def get_invoice_line(self):
        line_vals=[]
        
        for item in self.order_line:
            tmp ={
                'quantity': 1,
                'price_unit': item.amount,
                'name': item.partner_id.display_name,
                'account_id' : item.room_type_id.revenue_account_id.id,
                'tax_ids': [(6, 0, item.tax_id.ids)]
            }
            line_vals.append((0,0, tmp))
        return line_vals
        
        
    def clear_lines(self):
        self.ensure_one()
        self.order_line = False

    def action_export_template(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'Импортлох загвар')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#9ad808')
        header.set_text_wrap()
        header.set_font_name('Arial')
        worksheet.write(0, 0, u"Харилцагч", header)
        worksheet.write(0, 1, u"Өрөө", header)
        worksheet.write(0, 2, u"Өрөөний төрөл", header)
        if self.payment_type == 'nondefault':
            worksheet.write(0, 3, u"Нийт дүн", header)
        workbook.close()

        out = base64.encodebytes(output.getvalue())
        file_name = self.name + '.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
            'type': 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(
                excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
        }		 
class CampOrderLine(models.Model):
    _name = 'camp.order.line'
    _description = 'Camp Order Line'
    
    name = fields.Char(string='Name')
    parent_id = fields.Many2one('camp.order' , string='Parent ID' , ondelete='cascade',)
    room_id = fields.Many2one('camp.room' , string='Өрөө' , store=True , index=True)
    room_type_id = fields.Many2one('camp.room.type' , string='Өрөөний төрөл',store=True , index=True)
    block_id = fields.Many2one(related='room_id.block_id' , string='Блок' , store=True , index=True) 
    date = fields.Date(string='Огноо')
    partner_id = fields.Many2one('res.partner' , string='Partner' , store=True , index=True)
    department_id = fields.Many2one(related='partner_id.camp_department_id', store=True , index=True)
    invoice_id = fields.Many2one(string='account.move' , store=True , index=True)
    amount = fields.Float(related='room_type_id.price_unit' , store=True)
    sub_total = fields.Float(string='Нийт дүн' ,compute='compute_total')
    price_tax = fields.Float(string='Татвар дүн',compute='compute_total')
    price_subtotal = fields.Float(string='Татвар шингээгүй' , compute='compute_total',)
    
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True),('type_tax_use','=','sale')] , store=True)
    payment_type = fields.Selection([('default','Үндсэн'),('nondefault','Гараар')] , string='Төлбөрийн төрөл' , store=True)
    gender = fields.Selection(related='partner_id.gender',store=True)
    
    @api.depends('amount', 'tax_id')
    def compute_total(self):
        for item in self:
            # item.sub_total = item.qty*item.price_unit
            parent_id = item.parent_id
            price = item.amount
            # Aagii neleed yum boljiij iim bolgov
            taxes = item.tax_id.compute_all(price, parent_id.company_id.currency_id, partner=parent_id.partner_id)
            item.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'sub_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        for item in self:
            if item.parent_id.payment_type or item.parent_id.taxes_id or item.parent_id.date:
                item.payment_type = item.parent_id.payment_type
                item.tax_id = item.parent_id.taxes_id
                item.date = item.parent_id.date
    
    @api.onchange('amount')
    def onchange_amount(self):
        for item in self:
            if item.amount:
                item.amount = item.amount