# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from datetime import datetime
import time
from odoo.osv import expression

import time
from io import BytesIO
import xlsxwriter
from odoo.addons.mw_asset.report.report_excel_cell_styles import ReportExcelCellStyles
import base64

import logging
_logger = logging.getLogger(__name__)


class AccountAssetInventory(models.Model):
    _name = "account.asset.inventory"
    _description = "Budget configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True, tracking=True)
    description = fields.Char(tracking=True)
    
    line_ids = fields.One2many(
        comodel_name="account.asset.inventory.line", inverse_name="parent_id", copy=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
#     date_range_id = fields.Many2one(comodel_name="date.range", string="Date range")
    date = fields.Date(
        required=True, string="From Date", tracking=True
    )
#     date_to = fields.Date(required=True, string="To Date", tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
        required=True,
        default="draft",
    )
    
    branch_id = fields.Many2one('res.branch','Branch')
    owner_dep_id = fields.Many2one('hr.department', 'Owner department', )
    owner_emp_id = fields.Many2one('res.partner', 'Owner', domain=[("employee", "=", True)])
    # category_id = fields.Many2one('account.asset.category', 'Category')
    location_id = fields.Many2one('account.asset.location', 'Location')
    all_asset = fields.Boolean('All Asset')
    asset_model = fields.Many2one('account.asset', domain=[("state", "=", 'model')], string="Хөрөнгийн загвар")
    asset_type_id = fields.Many2one('account.asset.type', string="Хөрөнгийн төрөл")
    def create_lines(self, interval=1):
        self.line_ids.unlink()    
        line_obj = self.env['account.asset.inventory.line']
        asset_obj = self.env['account.asset']
        
        month = interval
        assets = asset_obj
        domains = []
        for item in self:
            if item.owner_emp_id or item.owner_emp_id:
                emps=(item.owner_emp_id and [item.owner_emp_id.id]) #or (item.owner_emp_ids and item.owner_emp_ids.ids)
                domains.append(('owner_id','in',emps))#'|',,('owner_emp_ids','in',emps)
                # if assets:
                #     for asset in assets:
                #         line=line_obj.create({
                #             'name': asset.name,
                #             'description': asset.name,
                #             'asset_id': asset.id,
                #             'parent_id': False,
                #             'parent_id': item.id,
                #             'result': 'nocounted'
                #         })                
            if item.owner_dep_id:
                domains.append(('owner_department_id','=',item.owner_dep_id.id))
            if item.asset_model:
                domains.append(('model_id','=',item.asset_model.id))
            if item.asset_type_id:
                domains.append(('asset_type_id','=',item.asset_type_id.id))
                # if assets:
                #     for asset in assets:
                #         line=line_obj.create({
                #             'name': asset.name,
                #             'description': asset.name,
                #             'asset_id': asset.id,
                #             'parent_id': False,
                #             'parent_id': item.id,
                #             'result': 'nocounted'
                #         })                
            # if item.category_id:
            #     domains.append(('category_id','=',item.category_id.id))
                # if assets:
                #     for asset in assets:
                #         line=line_obj.create({
                #             'name': asset.name,
                #             'description': asset.name,
                #             'asset_id': asset.id,
                #             'parent_id': False,
                #             'parent_id': item.id,
                #             'result': 'nocounted'
                #         })   
            # if item.branch_id:
            #     domains.append(('branch_id','=',item.branch_id.id))
                # if assets:
                #     for asset in assets:
                #         line=line_obj.create({
                #             'name': asset.name,
                #             'description': asset.name,
                #             'asset_id': asset.id,
                #             'parent_id': False,
                #             'parent_id': item.id,
                #             'result': 'nocounted'
                #         })    
            if item.location_id:
                domains.append(('location_id','=',item.location_id.id))
                # if assets:
                #     for asset in assets:
                #         line=line_obj.create({
                #             'name': asset.name,
                #             'description': asset.name,
                #             'asset_id': asset.id,
                #             'parent_id': False,
                #             'parent_id': item.id,
                #             'result': 'nocounted'
                #         })    
            if item.all_asset==True:
                assets = asset_obj.search([])#'|',,('owner_emp_ids','in',emps)
                for asset in assets:
                    line=line_obj.create({
                        'name': asset.name,
                        'description': asset.name,
                        'asset_id': asset.id,
                        'code':asset.code,
                        'parent_id': False,
                        'parent_id': item.id,
                        'result': 'nocounted'
                    })                
            asset_domain = assets.search(domains)
            for asset in asset_domain:
                line=line_obj.create({
                    'name': asset.name,
                    'description': asset.name,
                    'asset_id': asset.id,
                    'parent_id': False,
                    'code':asset.code,
                    'parent_id': item.id,
                    'result': 'nocounted'
                })                
        return True
    def action_open_inventory_lines(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('mw_asset.view_account_asset_inventory_line_tree').id, 'tree')],
            'view_mode': 's',
            'name': _('Inventory Lines'),
            'res_model': 'account.asset.inventory.line',
        }
        context = {
#             'default_is_editable': True,
            'default_parent_id': self.id,
#             'default_company_id': self.company_id.id,
        }
        # Define domains and context
        domain = [
            ('parent_id', '=', self.id),
#             ('location_id.usage', 'in', ['internal', 'transit'])
        ]
#         if self.location_ids:
#             context['default_location_id'] = self.location_ids[0].id
#             if len(self.location_ids) == 1:
#                 if not self.location_ids[0].child_ids:
#                     context['readonly_location_id'] = True
# 
#         if self.product_ids:
#             if len(self.product_ids) == 1:
#                 context['default_product_id'] = self.product_ids[0].id

        action['context'] = context
        action['domain'] = domain
        return action    
    
    @api.onchange("date_range_id")
    def _onchange_date_range(self):
        for rec in self:
            if rec.date_range_id:
                rec.date_from = rec.date_range_id.date_start
                rec.date_to = rec.date_range_id.date_end

    @api.onchange("date_from", "date_to")
    def _onchange_dates(self):
        for rec in self:
            if rec.date_range_id:
                if (
                    rec.date_from != rec.date_range_id.date_start
                    or rec.date_to != rec.date_range_id.date_end
                ):
                    rec.date_range_id = False
    

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancelled"

    def action_confirm(self):
        for rec in self:
            rec.state = "confirmed"
            

    def action_print(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
        datas = self
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'Inventory')

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)
        
        h2 = workbook.add_format()
        h2.set_font_size(9)

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#6495ED')

        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(9)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        header_wrap.set_bg_color('#6495ED')

        footer = workbook.add_format({'bold': 1})
        footer.set_text_wrap()
        footer.set_font_size(9)
        footer.set_align('right')
        footer.set_align('vcenter')
        footer.set_border(style=1)
        footer.set_bg_color('#F0FFFF')
        footer.set_num_format('#,##0.00')
        

        content_color_float = workbook.add_format()
        content_color_float.set_text_wrap()
        content_color_float.set_font_size(9)
        content_color_float.set_align('right')
        content_color_float.set_align('vcenter')
        content_color_float.set_border(style=1)
        content_color_float.set_bg_color('#87CEFA')
        content_color_float.set_num_format('#,##0.00')        

        format_name = {
            'font_name': 'Times New Roman',
            'font_size': 14,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter'
        }
        # create formats
        format_content_text_footer = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'align': 'vcenter',
        'valign': 'vcenter',
        }
        format_content_right = {
        'font_name': 'Times New Roman',
        'font_size': 9,
        'align': 'right',
        'valign': 'vcenter',
        'border': 1,
        'num_format': '#,##0.00'
        }
        format_group_center = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        }
        format_group = {
        'font_name': 'Times New Roman',
        'font_size': 10,
        'bold': True,
        'align': 'center',
        'valign': 'vcenter',
        'border': 1,
        'bg_color': '#CFE7F5',
        'num_format': '#,##0.00'
        }
    
        format_title = {
            'font_name': 'Times New Roman',
            'font_size': 12,
            'bold': True,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'text_wrap': 1,
            'bg_color': '#b3c6ff'
        }
        

        format_group_left_l = {
            'font_name': 'Times New Roman',
            'font_size': 9,
            'bold': False,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
#             'bg_color': '#CFE7F5'
        }

        format_group_left_b = {
            'font_name': 'Times New Roman',
            'font_size': 11,
            'bold': False,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
#             'bg_color': '#CFE7F5'
        }        
        
        format_group_center = workbook.add_format(format_group_center)
        format_name = workbook.add_format(format_name)
        format_content_text_footer = workbook.add_format(format_content_text_footer)
        format_filter = workbook.add_format(ReportExcelCellStyles.format_filter)
        format_title = workbook.add_format(format_title)
        format_group_right = workbook.add_format(ReportExcelCellStyles.format_group_right)
        format_group_float = workbook.add_format(ReportExcelCellStyles.format_group_float)
        format_group_left = workbook.add_format(format_group_left_b)
        format_content_text = workbook.add_format(ReportExcelCellStyles.format_content_text)
        format_content_number = workbook.add_format(ReportExcelCellStyles.format_content_number)
        format_content_float = workbook.add_format(ReportExcelCellStyles.format_content_float)
        format_content_center = workbook.add_format(ReportExcelCellStyles.format_content_center)
        format_group = workbook.add_format(format_group)

        format_group_little_left = workbook.add_format(format_group_left_l)

        format_content_right = workbook.add_format(format_content_right)             
#         duration = self.get_period(cr, uid, form)
        
#         worksheet.write(0, 1, u'Маягт ГБ', h2)
#         worksheet.write(0, 5, u'Байгууллагын нэр: %s' %(self.company_id.name), h2)
        
        worksheet.write(1, 0, u'Үндсэн хөрөнгийн тооллого', h1)
#         worksheet.row(1).height = 400
#         worksheet.write(3, 1, u'Дугаар:', h2)
#         worksheet.write(3, 6, u'Огноо: %s' %(time.strftime('%Y-%m-%d'),), h2)
        worksheet.write(3, 0, u'Тайлан хугацаа: %s '%
#                 (datetime.strptime(data['form']['date_from'][0],'%Y-%m-%d').strftime('%Y.%m.%d'),
#                  datetime.strptime(data['form']['date_to'][0],'%Y-%m-%d').strftime('%Y.%m.%d')
                (self.date,
#                  self.date_to
                 ),h2)
#        date_str = '%s-%s' % (
#            datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
#            datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
#        )
#         worksheet.write(row, 0, row, last_col, item_cat.name, contest_left_bold)

        rowx = 5
        worksheet.write(rowx, 0, u'№', format_title)
        worksheet.write(rowx, 1, u'Хөрөнгийн нэр', format_title)
        worksheet.write(rowx, 2, u'Дугаар', format_title)
        worksheet.write(rowx, 3, u'Ангилал', format_title)
        worksheet.write(rowx, 4, u'Орлого авсан огноо', format_title)
        worksheet.write(rowx, 5, u'Эзэмшигч', format_title)
        worksheet.write(rowx, 6, u'Branch', format_title)
        worksheet.write(rowx, 7, u'Байшил', format_title)
        worksheet.write(rowx, 8, u'Анхны өртөг', format_title)
        worksheet.write(rowx, 9,  u'Элэгдэл', format_title)
        worksheet.write(rowx, 10, u'Үлдэгдэл өртөг', format_title)
        worksheet.write(rowx, 11, u'Алба', format_title)
        worksheet.write(rowx, 12, u'Валют', format_title)
        worksheet.write(rowx, 13,  u'Төлөв', format_title)
        worksheet.write(rowx, 14, u'Тооллогын үр дүн', format_title)

        rowx += 1
#         worksheet.write(rowx, 1, u'Төсвийн утга', format_title)
#         worksheet.write(rowx, 2, u'Нэгжийн код', format_title)
#         worksheet.write(rowx, 3, u'Зардлын задаргааны дугаар', format_title)
#         worksheet.write(rowx, 4, u'Дэс дугаар', format_title)

#         worksheet.write(rowx, 9, u'{0}.01'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 10, u'{0}.02'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 11, u'{0}.03'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 12, u'{0}.04'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 13, u'{0}.05'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 14, u'{0}.06'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 15, u'{0}.07'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 16, u'{0}.08'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 17, u'{0}.09'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 18, u'{0}.10'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 19, u'{0}.11'.format(self.date_from.year), format_title)
#         worksheet.write(rowx, 20, u'{0}.12'.format(self.date_from.year), format_title)

        
        rowx += 1
#         
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 20)
        worksheet.set_column('C:C', 11)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('H:U', 15)

        worksheet.set_column('E:G', 18)

        date_format = '%Y-%m-%d'
        def get_date_format(date):
            if date:
    #                 date = datetime.strptime(date, DEFAULT_SERVER_DATE_FORMAT)
                date = date.strftime(date_format)
            return date
#               
        n=1
        for l in self.line_ids:
#             for l  in line.line_ids:
            if l.asset_id:
                partner=''
                state=''
                if l.result=='counted':
                    state='Тоологдсон'
                elif l.result=='nocounted':
                    state='Тоологдоогүй' 
                value = 0
                book_value = 0
                if l.asset_id.original_value:
                    value=l.asset_id.original_value
                if l.asset_id.book_value:
                    book_value=l.asset_id.book_value
                depreciated_amount = value-book_value
                worksheet.write(rowx, 0, n, format_group_left)
                worksheet.write(rowx, 1, l.asset_id.name, format_group_left)
                worksheet.write(rowx, 2, l.asset_id.code and l.asset_id.code or '', format_group_left)
                worksheet.write(rowx, 3, l.asset_id.model_id and l.asset_id.model_id.name or '', format_group_left)
                worksheet.write(rowx, 4, get_date_format(l.asset_id.acquisition_date), format_group_left)
#                 worksheet.write(rowx, 5,  l.asset_id.owner_emp_ids and l.asset_id.owner_emp_ids[0].name or '', format_group_left)
                worksheet.write(rowx, 5,  l.asset_id.owner_id and l.asset_id.owner_id.name +" " + "/" + str(l.asset_id.owner_id.vat if l.asset_id.owner_id.vat else ' ') + "/" or '', format_group_left)
                worksheet.write(rowx, 6, l.asset_id.branch_id and l.asset_id.branch_id.name or '', format_group_left)
                worksheet.write(rowx, 7, l.asset_id.location_id and l.asset_id.location_id.name or '', format_group_left)
                worksheet.write(rowx, 8, value, format_content_float)
                worksheet.write(rowx, 9, depreciated_amount, format_content_float)
                worksheet.write(rowx, 10, value-depreciated_amount, format_content_float)
                worksheet.write(rowx, 11, l.asset_id.owner_department_id and l.asset_id.owner_department_id.name or '', format_group_left)
                worksheet.write(rowx, 12, 'MNT', format_group_left)
                worksheet.write(rowx, 13, l.asset_id.state, format_group_left)
                worksheet.write(rowx, 14, state, format_group_left)
                rowx += 1
            n+=1
                        
#                 rowx += 1
                    
        #sheet.set_panes_frozen(True) # frozen headings instead of split panes
        #sheet.set_horz_split_pos(2) # in general, freeze after last heading row
        #sheet.set_remove_splits(True) # if user does unfreeze, don't leave a split there
        #sheet.set_col_default_width(True)
        inch = 3000
         
        worksheet.write(rowx+2, 2, u'Боловсруулсан нягтлан бодогч.........................................../\
                                                 /',h2)
        worksheet.write(rowx+4, 2, u'Хянасан ерөнхий нягтлан бодогч....................................../\
                                                 /', h2)
#         from StringIO import StringIO
        from io import StringIO
#         output = BytesIO()
        
        file_name = "Үндсэн хөрөнгийн тооллого%s.xlsx" % (time.strftime('%Y%m%d_%H%M'),)
        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
                                            
                                                        
class AccountBudgetLine(models.Model):
    _name = "account.asset.inventory.line"
    _description = "Asset inventory line"
    _inherit = ["mail.thread", "mail.activity.mixin"]
#     _rec_name= "conf_line_id"
    
    name = fields.Char("Name")
    code = fields.Char("Code", related="asset_id.code")
    
    description = fields.Char("description")

    asset_id = fields.Many2one('account.asset','Asset', domain = [('state', '!=', 'model')])
    # model_asset_id = fields.Many2one('account.asset.category','Category',related='asset_id.category_id')
    # branch_id = fields.Many2one('res.branch','Branch',related='asset_id.branch_id')
    owner_dep_id = fields.Many2one('hr.department', 'Owner department')
    owner_emp_id = fields.Many2one('res.partner', 'Owner')
    date = fields.Date(string="Date")
    model_id = fields.Many2one('account.asset', string='Хөрөнгийн загвар', related='asset_id.model_id')
    asset_type=fields.Many2one('account.asset.type', string='Хөрөнгийн төрөл',related='asset_id.asset_type_id')
    partner_id = fields.Many2one('res.partner','Partner')
    act_desc = fields.Char(string='Тайлбар')
#     date_to = fields.Date(required=True, string="To Date")
#     repair_hour = fields.Float(compute='_compute_run_hour', string='Repair hour', store = True, tracking=True)

    parent_id = fields.Many2one("account.asset.inventory","Budget",ondelete="cascade",)

#     period_line_ids = fields.One2many(
#         comodel_name="account.asset.inventory.period.line", inverse_name="parent_line_id", copy=True
#     )
    
#     analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic account')


#     original_value = fields.Float(string="Анхны өртөг",related='asset_id.original_value',store=True)
    # original_value = fields.Float(string='Анхны өртөг', store=True, 
    #     compute='_compute_total_amount')


    # depreciation_value = fields.Float(string='Хуримтлагдсан элэгдэл', store=True, 
    #     compute='_compute_total_amount')
    # balance = fields.Float(string="Үлдэгдэл", store=True, 
    #     compute='_compute_total_amount')
    
    state = fields.Selection(
        [("draft", "Ноорог"), ("open", "хэвийн"), ("close", "Хаагдсан")],
        # related='asset_id.state'
    )
        

    result = fields.Selection(
        [("counted", "Тоологдсон"), ("nocounted", "Тоологдоогүй"), ("manual", "Гараар оруулсан"),("act", "Актлах"),],
        required=True,
        default="nocounted",
        tracking=True,
    )
            

    @api.depends(
                'asset_id',
                'original_value',
                )

    def button_count_line(self):
        for rec in self:
            rec.result = "counted"
#             rec.description = vals
    def undo_button_count_line(self):
        for rec in self:
            rec.result = "nocounted"
#             rec.description = vals
    def count(self):
        self.button_count_line()
    def undo_count(self):
        self.undo_button_count_line()