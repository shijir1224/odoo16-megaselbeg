# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from odoo.exceptions import UserError, RedirectWarning, ValidationError

import time
from io import BytesIO
import xlsxwriter
from odoo.addons.account_financial_report.report.report_excel_cell_styles import ReportExcelCellStyles
import base64
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class AccountCompanyBudget(models.Model):
    _name = "mw.account.company.budget"
    _description = "Budget of Company /cash based/"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Төсвийн нэр", required=True, tracking=True)
    description = fields.Char(tracking=True)
    
    line_ids = fields.One2many(
        comodel_name="mw.account.budget", inverse_name="budget_id", copy=False
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Компани",
        default=lambda self: self.env.company,
    )
    date_range_id = fields.Many2one(comodel_name="date.range", string="Огноо сонгох")
    date_from = fields.Date(
        required=True, string="Эхлэх огноо", tracking=True
    )
    date_to = fields.Date(required=True, string="Дуусах огноо", tracking=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
        required=True,
        default="draft",
        tracking=True,
    )

    budget_total = fields.Float(string='Нийт төсөв', store=True, 
        compute='_compute_total_amount')

    real_total = fields.Float(string='Нийт гүйцэтгэл', store=True, 
        compute='_compute_total_amount')
    
    balance = fields.Float(string="Үлдэгдэл", store=True, 
        compute='_compute_total_amount')
    
    history_ids=fields.One2many('budget.flow.history','budget_com_id','Workflow History', readonly=True)

    close_state = fields.Selection(
        [("open", "Нээлттэй"), ("closed", "Хаагдсан")],
        default="open",
        tracking=True,
    )

    @api.depends(
                'line_ids',
                'line_ids.real_total',
                'line_ids.budget_total',
                )
    def _compute_total_amount(self):
        for item in self:
            total_budget=0
            real_total=0
            for line in item.line_ids:
                total_budget+=line.budget_total
                real_total += line.real_total
            print ('real_total ',real_total)
            item.budget_total = total_budget
            item.real_total = real_total
            item.balance=total_budget-real_total
                

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
                          
    def action_change_stage(self):
        for line in self.line_ids:  
            line.write({'close_state':self.close_state})
            
    def action_print(self):
        ''' Тайлангийн загварыг боловсруулж өгөгдлүүдийг
            тооцоолж байрлуулна.
        '''
        datas = self
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet(u'Budget')

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
        
        worksheet.write(1, 0, u'ЖИЛИЙН НЭГДСЭН ТӨСӨВ', h1)
#         worksheet.row(1).height = 400
#         worksheet.write(3, 1, u'Дугаар:', h2)
#         worksheet.write(3, 6, u'Огноо: %s' %(time.strftime('%Y-%m-%d'),), h2)
        worksheet.write(3, 0, u'Тайлан хугацаа: %s - %s'%
#                 (datetime.strptime(data['form']['date_from'][0],'%Y-%m-%d').strftime('%Y.%m.%d'),
#                  datetime.strptime(data['form']['date_to'][0],'%Y-%m-%d').strftime('%Y.%m.%d')
                (self.date_from,
                 self.date_to
                 ),h2)
#        date_str = '%s-%s' % (
#            datetime.strptime(data['date_from'],'%Y-%m-%d').strftime('%Y.%m.%d'),
#            datetime.strptime(data['date_to'],'%Y-%m-%d').strftime('%Y.%m.%d')
#        )
#         worksheet.merge_range(row, 0, row, last_col, item_cat.name, contest_left_bold)

        rowx = 5
        worksheet.merge_range(rowx, 0,rowx+1,  0, u'№', format_title)
        worksheet.merge_range(rowx, 1,rowx+1,  1, u'Дэд дугаар', format_title)
        worksheet.merge_range(rowx, 2,rowx+1,  2, u'Жилийн нэгдсэн төсвийн код', format_title)
        worksheet.merge_range(rowx, 3, rowx+1, 3, u'Төсвийн зориулалт', format_title)
        worksheet.merge_range(rowx, 4, rowx+1, 4, u'Нэгж', format_title)
        worksheet.merge_range(rowx, 5, rowx+1, 5, u'Төсвийн хариуцагч', format_title)
        worksheet.merge_range(rowx, 6, rowx+1, 6, u'Хамааралтай "Тухайлсан төсвийн код"', format_title)
        worksheet.merge_range(rowx, 7, rowx+1, 7, u'Хамааралтай үйл ажиллагааны төлөвлөгөөний код, ногдох хувь', format_title)
        worksheet.merge_range(rowx, 8, rowx+1, 8, u'Хамааралтай төслийн код, ногдох хувь', format_title)
        worksheet.merge_range(rowx, 9,rowx,  20, u'Төсвийн хамрах сар', format_title)
        worksheet.merge_range(rowx, 21, rowx+1, 21, u'Тайлбар, тэмдэглэл', format_title)

        rowx += 1
#         worksheet.write(rowx, 1, u'Төсвийн утга', format_title)
#         worksheet.write(rowx, 2, u'Нэгжийн код', format_title)
#         worksheet.write(rowx, 3, u'Зардлын задаргааны дугаар', format_title)
#         worksheet.write(rowx, 4, u'Дэс дугаар', format_title)

        worksheet.write(rowx, 9, u'{0}.01'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 10, u'{0}.02'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 11, u'{0}.03'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 12, u'{0}.04'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 13, u'{0}.05'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 14, u'{0}.06'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 15, u'{0}.07'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 16, u'{0}.08'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 17, u'{0}.09'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 18, u'{0}.10'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 19, u'{0}.11'.format(self.date_from.year), format_title)
        worksheet.write(rowx, 20, u'{0}.12'.format(self.date_from.year), format_title)

        
        rowx += 1
#         
        worksheet.set_column('A:A', 5)
        worksheet.set_column('B:B', 10)
        worksheet.set_column('C:C', 11)
        worksheet.set_column('D:D', 20)
        worksheet.set_column('J:U', 15)

        worksheet.set_column('E:F', 18)

#               
        n=1
        for line in self.line_ids:
            rowx += 1
            for l  in line.line_ids:
                worksheet.write(rowx, 0, n, format_group_left)
                worksheet.write(rowx, 1, '', format_group_left)
                worksheet.write(rowx, 2, l.code and l.code or '', format_group_left)
#                 worksheet.write(rowx, 2, line.department_id and line.department_id.code, format_group_left)
#                 worksheet.write(rowx, 3, l.code and l.code[2:], format_group_left)
#                 worksheet.write(rowx, 4, '00', format_group_left)
                worksheet.write(rowx, 3, l.name, format_group_left)
                worksheet.write(rowx, 4, line.department_id and line.department_id.name, format_group_left)
                worksheet.write(rowx, 5,  l.create_uid.name and l.create_uid.name.split(' ')[0] or '', format_group_left)
                worksheet.write(rowx, 6, '', format_group_left)
                worksheet.write(rowx, 7, '', format_group_left)
                worksheet.write(rowx, 8, '', format_group_left)
                worksheet.write(rowx, 9, l.budget_01, format_group_float)
                worksheet.write(rowx, 10, l.budget_02, format_group_float)
                worksheet.write(rowx, 11, l.budget_03, format_group_float)
                worksheet.write(rowx, 12, l.budget_04, format_group_float)
                worksheet.write(rowx, 13, l.budget_05, format_group_float)
                worksheet.write(rowx, 14, l.budget_06, format_group_float)
                worksheet.write(rowx, 15, l.budget_07, format_group_float)
                worksheet.write(rowx, 16, l.budget_08, format_group_float)
                worksheet.write(rowx, 17, l.budget_09, format_group_float)
                worksheet.write(rowx, 18, l.budget_10, format_group_float)
                worksheet.write(rowx, 19, l.budget_11, format_group_float)
                worksheet.write(rowx, 20, l.budget_12, format_group_float)
                rowx += 1
                nn=1
                for ll  in l.period_line_ids:
                    worksheet.write(rowx, 0, '', format_group_left)
                    worksheet.write(rowx, 1, str(n)+'.'+str(nn), format_group_left)
#                     worksheet.write(rowx, 1, ll.code and ll.code[:2], format_group_little_left)
                    worksheet.write(rowx, 2, ll.code and ll.code or '', format_group_little_left)
                    worksheet.write(rowx, 3, ll.name, format_group_little_left)
                    worksheet.write(rowx, 4, line.department_id and line.department_id.name, format_group_little_left)

                    worksheet.write(rowx, 5,  l.create_uid.name and l.create_uid.name.split(' ')[0] or '', format_group_little_left)
                    worksheet.write(rowx, 6, '', format_group_little_left)
                    worksheet.write(rowx, 7, '', format_group_little_left)
                    worksheet.write(rowx, 8, '', format_group_little_left)

                    worksheet.write(rowx, 9, ll.budget_01, format_content_float)
                    worksheet.write(rowx, 10, ll.budget_02, format_content_float)
                    worksheet.write(rowx, 11, ll.budget_03, format_content_float)
                    worksheet.write(rowx, 12, ll.budget_04, format_content_float)
                    worksheet.write(rowx, 13, ll.budget_05, format_content_float)
                    worksheet.write(rowx, 14, ll.budget_06, format_content_float)
                    worksheet.write(rowx, 15, ll.budget_07, format_content_float)
                    worksheet.write(rowx, 16, ll.budget_08, format_content_float)
                    worksheet.write(rowx, 17, ll.budget_09, format_content_float)
                    worksheet.write(rowx, 18, ll.budget_10, format_content_float)
                    worksheet.write(rowx, 19, ll.budget_11, format_content_float)
                    worksheet.write(rowx, 20, ll.budget_12, format_content_float)
                    rowx += 1
                    nnn=1
                    for lll  in ll.period_line_line_ids:
                        worksheet.write(rowx, 0, '', format_group_left)
                        worksheet.write(rowx, 1, str(n)+'.'+str(nn)+'.'+str(nnn), format_group_left)
    #                     worksheet.write(rowx, 1, ll.code and ll.code[:2], format_group_little_left)
                        worksheet.write(rowx, 2, lll.code and lll.code or '', format_group_little_left)
                        worksheet.write(rowx, 3, lll.name, format_group_little_left)
                        worksheet.write(rowx, 4, line.department_id and line.department_id.name, format_group_little_left)
    
                        worksheet.write(rowx, 5, l.create_uid.name and l.create_uid.name.split(' ')[0] or '', format_group_little_left)
                        worksheet.write(rowx, 6, '', format_group_little_left)
                        worksheet.write(rowx, 7, '', format_group_little_left)
                        worksheet.write(rowx, 8, '', format_group_little_left)
    
                        worksheet.write(rowx, 9, lll.budget_01, format_content_float)
                        worksheet.write(rowx, 10, lll.budget_02, format_content_float)
                        worksheet.write(rowx, 11, lll.budget_03, format_content_float)
                        worksheet.write(rowx, 12, lll.budget_04, format_content_float)
                        worksheet.write(rowx, 13, lll.budget_05, format_content_float)
                        worksheet.write(rowx, 14, lll.budget_06, format_content_float)
                        worksheet.write(rowx, 15, lll.budget_07, format_content_float)
                        worksheet.write(rowx, 16, lll.budget_08, format_content_float)
                        worksheet.write(rowx, 17, lll.budget_09, format_content_float)
                        worksheet.write(rowx, 18, lll.budget_10, format_content_float)
                        worksheet.write(rowx, 19, lll.budget_11, format_content_float)
                        worksheet.write(rowx, 20, lll.budget_12, format_content_float)
                        rowx += 1
                        nnn+=1
                    nn+=1
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
        
        file_name = "budget_%s.xlsx" % (time.strftime('%Y%m%d_%H%M'),)
        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        # print '-----------------done------------------'
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
        
#------------flow -------
    @api.model
    def create(self, val):
        res  =  super(AccountCompanyBudget, self).create(val)
        for item in res:
            if item.flow_id:
                search_domain = [('flow_id','=',item.flow_id.id)]
                re_flow =  self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
                item.flow_line_id = re_flow
        return res

    def _get_dynamic_flow_line_id(self):
        return self.flow_find()
    
#     def flow_domain(self):
#         domain = {'flow_id': False}
#         search_domain=[]
#         dapartments=[]
#         for rec in self:
#             if rec.department_id:
#                 dapartments=[rec.department_id.id]+rec.department_id.child_ids.ids
#             elif rec.user_id and rec.user_id.department_id:
#                 dapartments=[rec.user_id.department_id.id]+rec.user_id.department_id.id.child_ids.ids
# #                 search_domain =  ['|',('department_id', '=', rec.user_id.department_id.id),('department_id', '=', False)]
#         search_domain = ['|',('department_ids', 'in', dapartments),('department_ids', '=', False)]
#         search_domain.append(('model_id.model','=','mw.account.budget'))   
#         return search_domain

    def flow_domain(self):
        domain = {'flow_id': False}
        search_domain=[]
        search_domain.append(('model_id.model','=','mw.account.company.budget'))  
        _logger.info(u'search_domain=====: %s '%(search_domain))
        
        return search_domain
        

    def action_done(self):
        self.write({'state':'done'})
#                 
    
    def _get_default_flow_id(self):
        search_domain = []
#         search_domain.append(('model_id.model','=','mw.account.budget'))
        search_domain=self.flow_domain()
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
        default=_get_dynamic_flow_line_id,
         copy=False, domain="[('id','in',visible_flow_line_ids)]")

    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
        default=_get_default_flow_id,
         copy=True, required=True, domain="[('model_id.model', '=', 'mw.account.company.budget')]")
    
    flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
    flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    state = fields.Char(string='Төлөв', compute='_compute_state', store=True, tracking=True)
    categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
    is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True)

    @api.depends('flow_id.line_ids', 'flow_id.is_amount', 'budget_total')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                if item.flow_id.is_amount:
                    flow_line_ids = []
                    for fl in item.flow_id.line_ids:
                        if fl.state_type in ['draft','cancel']:
                            flow_line_ids.append(fl.id)
                        elif fl.amount_price_min==0 and fl.amount_price_max==0:
                            flow_line_ids.append(fl.id)
                        elif fl.amount_price_min<=item.budget_total and fl.amount_price_max>=item.budget_total:
                            flow_line_ids.append(fl.id)
                    item.visible_flow_line_ids = flow_line_ids
                else:
                    item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'mw.account.company.budget')])
            else:
                item.visible_flow_line_ids = []

    @api.depends('flow_line_id.stage_id')
    def _compute_flow_line_id_stage_id(self):
        for item in self:
            item.stage_id = item.flow_line_id.stage_id

    #------------------------------flow------------------
    @api.depends('flow_line_id','flow_line_id.state_type')
    def _compute_state(self):
        for item in self:
            item.state = item.flow_line_id.state_type

    def flow_find(self, domain=[], order='sequence'):
        search_domain = []
        if self.flow_id:
            search_domain.append(('flow_id','=',self.flow_id.id))
            
        search_domain.append(('flow_id.model_id.model','=','mw.account.company.budget'))
        return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find()
        else:
            self.flow_line_id = False

    def action_next_stage(self):
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
        if next_flow_line_id:
            if self.visible_flow_line_ids and next_flow_line_id.id not in self.visible_flow_line_ids.ids:
                check_next_flow_line_id = next_flow_line_id
                while check_next_flow_line_id.id not in self.visible_flow_line_ids.ids:
                    
                    temp_stage = check_next_flow_line_id._get_next_flow_line()
                    if temp_stage.id==check_next_flow_line_id.id or not temp_stage:
                        break;
                    check_next_flow_line_id = temp_stage
                next_flow_line_id = check_next_flow_line_id

            if next_flow_line_id._get_check_ok_flow(False, False):
                self.flow_line_id = next_flow_line_id
                if self.flow_line_id.state_type=='done':
                    self.action_done()

                # History uusgeh
                self.env['budget.flow.history'].create_history(next_flow_line_id,False, self,'next')

                # chat ilgeeh
                # for item in self.sudo().order_line.mapped('pr_line_many_ids.request_id.employee_id.user_id.partner_id'):
                #     self.send_chat_employee(item)
                

                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(False, False)
#                     if send_users:
#                         self.send_chat_next_users(send_users.mapped('partner_id'))
            else:
                con_user = next_flow_line_id._get_flow_users(False, False)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(con_user.mapped('display_name'))
                raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
                # raise UserError(_('You are not confirm user'))
    
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
                
            if back_flow_line_id._get_check_ok_flow(False, False):
                self.flow_line_id = back_flow_line_id
                # History uusgeh
                self.env['budget.flow.history'].create_history(back_flow_line_id, False, self,'back')
            
                # chat ilgeeh
                # for item in self.sudo().order_line.mapped('pr_line_many_ids.request_id.employee_id.user_id.partner_id'):
                #     self.send_chat_employee(item)
                
            else:
                raise UserError(_('You are not back user'))

    def action_cancel_stage(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow(False, False):
            
            return self.action_cancel()
        else:
            raise UserError(_('You are not cancel user'))

    def set_stage_cancel(self):
        flow_line_id = self.flow_line_id._get_cancel_flow_line()
        if flow_line_id._get_check_ok_flow(False, False):
            
            self.flow_line_id = flow_line_id
            # History uusgeh
            self.env['budget.flow.history'].create_history(flow_line_id, False, self,'cancel')
        else:
            raise UserError(_('You are not cancel user'))
        

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
            self.env['budget.flow.history'].create_history(flow_line_id ,False, self,'back')
        else:
            raise UserError(_('You are not draft user'))
        
        
                                            
class AccountBudget(models.Model):
    _name = "mw.account.budget"
    _description = "Budget of Department /cash based/"
    _inherit = ["mail.thread", "mail.activity.mixin"]


#------------flow -------
    @api.model
    def create(self, val):
        res  =  super(AccountBudget, self).create(val)
        for item in res:
            if item.flow_id:
                search_domain = [('flow_id','=',item.flow_id.id)]
                re_flow =  self.env['dynamic.flow.line'].search(search_domain, order='sequence', limit=1).id
                item.flow_line_id = re_flow
        return res

    def _get_dynamic_flow_line_id(self):
        return self.flow_find()
    
#     def flow_domain(self):
#         domain = {'flow_id': False}
#         search_domain=[]
#         dapartments=[]
#         for rec in self:
#             if rec.department_id:
#                 dapartments=[rec.department_id.id]+rec.department_id.child_ids.ids
#             elif rec.user_id and rec.user_id.department_id:
#                 dapartments=[rec.user_id.department_id.id]+rec.user_id.department_id.id.child_ids.ids
# #                 search_domain =  ['|',('department_id', '=', rec.user_id.department_id.id),('department_id', '=', False)]
#         search_domain = ['|',('department_ids', 'in', dapartments),('department_ids', '=', False)]
#         search_domain.append(('model_id.model','=','mw.account.budget'))   
#         return search_domain

    def flow_domain(self):
        domain = {'flow_id': False}
        search_domain=[]
        dapartments=[]
        for rec in self:
            if rec.department_id:
                dapartments=[rec.department_id.id]+rec.department_id.child_ids.ids
            elif rec.create_uid and rec.create_uid.department_id:
                dapartments=[rec.create_uid.department_id.id]+rec.create_uid.department_id.id.child_ids.ids
#                 search_domain =  ['|',('department_id', '=', rec.user_id.department_id.id),('department_id', '=', False)]
        deps=[]
        for de in dapartments:
            d=self.env['hr.department'].browse(de)
            deps.append(d.id)
            parent=d.parent_id
            while parent:
                deps.append(parent.id)
                parent=parent.parent_id
#         print ('deps ',deps)
        search_domain = ['|',('department_ids', 'in', deps),('department_ids', '=', False)]
#         search_domain = ['|',('department_ids', 'in', dapartments),('department_ids', '=', False)]
        search_domain.append(('model_id.model','=','mw.account.budget'))  
        _logger.info(u'search_domain=====: %s '%(search_domain))
        
        return search_domain
        
    
    def _get_default_flow_id(self):
        search_domain = []
#         search_domain.append(('model_id.model','=','mw.account.budget'))
        search_domain=self.flow_domain()
        return self.env['dynamic.flow'].search(search_domain, order='sequence', limit=1).id

    visible_flow_line_ids = fields.Many2many('dynamic.flow.line', compute='_compute_visible_flow_line_ids', string='Харагдах төлөв')

    flow_line_id = fields.Many2one('dynamic.flow.line', string='Төлөв', tracking=True, index=True,
        default=_get_dynamic_flow_line_id,
         copy=False,domain="[('id','in',visible_flow_line_ids)]")

    flow_id = fields.Many2one('dynamic.flow', string='Урсгал Тохиргоо', tracking=True,
        default=_get_default_flow_id,
         copy=True, required=True, domain="[('id', 'in', flow_ids)]")#domain="[('model_id.model', '=', 'mw.account.budget')]")
    
    flow_line_next_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_next_id', readonly=True)
    flow_line_back_id = fields.Many2one('dynamic.flow.line', related='flow_line_id.flow_line_back_id', readonly=True)
    state = fields.Char(string='Төлөв', compute='_compute_state', store=True, tracking=True)
    categ_ids = fields.Many2many('product.category', related='flow_id.categ_ids', readonly=True)
    is_not_edit = fields.Boolean(related="flow_line_id.is_not_edit", readonly=True)
    stage_id = fields.Many2one('dynamic.flow.line.stage', compute='_compute_flow_line_id_stage_id', string='Төлөв stage', store=True)

    flow_ids = fields.Many2many('dynamic.flow', 'mw_account_budget_request_flow_rel','request_id','flow_id',
                                  string='Зөвшөөрөгдсэн урсгалууд', compute='_compute_flow_ids', store=True, readonly=True)


    close_state = fields.Selection(
        [("open", "Нээлттэй"), ("closed", "Хаагдсан")],
        default="open",
        tracking=True,
    )

    @api.depends('department_id')
    def _compute_flow_ids(self):
        for item in self:
            search_domain=self.flow_domain()
            print ('search_domain ',search_domain)
            flows=self.env['dynamic.flow'].search(search_domain)
            temp_flows=[]
            if item.department_id:
                temp_flows=flows.ids
            item.flow_ids = temp_flows
    
    @api.depends('flow_id.line_ids', 'flow_id.is_amount', 'budget_total')
    def _compute_visible_flow_line_ids(self):
        for item in self:
            if item.flow_id:
                if item.flow_id.is_amount:
                    flow_line_ids = []
                    for fl in item.flow_id.line_ids:
                        if fl.state_type in ['draft','cancel']:
                            flow_line_ids.append(fl.id)
                        elif fl.amount_price_min==0 and fl.amount_price_max==0:
                            flow_line_ids.append(fl.id)
                        elif fl.amount_price_min<=item.budget_total and fl.amount_price_max>=item.budget_total:
                            flow_line_ids.append(fl.id)
                    item.visible_flow_line_ids = flow_line_ids
                else:
                    item.visible_flow_line_ids = self.env['dynamic.flow.line'].search([('flow_id', '=', item.flow_id.id),('flow_id.model_id.model', '=', 'mw.account.budget')])
            else:
                item.visible_flow_line_ids = []

    @api.depends('flow_line_id.stage_id')
    def _compute_flow_line_id_stage_id(self):
        for item in self:
            item.stage_id = item.flow_line_id.stage_id

    #------------------------------flow------------------
    @api.depends('flow_line_id','flow_line_id.state_type')
    def _compute_state(self):
        for item in self:
            item.state = item.flow_line_id.state_type

    def flow_find(self, domain=[], order='sequence'):
        search_domain = []
        if self.flow_id:
            search_domain.append(('flow_id','=',self.flow_id.id))
            
        search_domain.append(('flow_id.model_id.model','=','mw.account.budget'))
        return self.env['dynamic.flow.line'].search(search_domain, order=order, limit=1).id

    @api.onchange('flow_id')
    def _onchange_flow_id(self):
        if self.flow_id:
            if self.flow_id:
                self.flow_line_id = self.flow_find()
        else:
            self.flow_line_id = False

    def action_next_stage(self):
        next_flow_line_id = self.flow_line_id._get_next_flow_line()
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

                # History uusgeh
                self.env['budget.flow.history'].create_history(next_flow_line_id, self, False, 'next')

                # chat ilgeeh
                # for item in self.sudo().order_line.mapped('pr_line_many_ids.request_id.employee_id.user_id.partner_id'):
                #     self.send_chat_employee(item)
                

                if self.flow_line_next_id:
                    send_users = self.flow_line_next_id._get_flow_users(self.branch_id, False)
#                     if send_users:
#                         self.send_chat_next_users(send_users.mapped('partner_id'))
            else:
                con_user = next_flow_line_id._get_flow_users(self.branch_id, False)
                confirm_usernames = ''
                if con_user:
                    confirm_usernames = ', '.join(con_user.mapped('display_name'))
                raise UserError(u'Та батлах хэрэглэгч биш байна\n Батлах хэрэглэгчид %s'%confirm_usernames)
                # raise UserError(_('You are not confirm user'))
    
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
                # History uusgeh
                self.env['budget.flow.history'].create_history(back_flow_line_id, self, False, 'back')
                # chat ilgeeh
                # for item in self.sudo().order_line.mapped('pr_line_many_ids.request_id.employee_id.user_id.partner_id'):
                #     self.send_chat_employee(item)
                
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
            # History uusgeh
            self.env['budget.flow.history'].create_history(flow_line_id, self, False, 'cancel')
        else:
            raise UserError(_('You are not cancel user'))
        

    def action_draft_stage(self):
        flow_line_id = self.flow_line_id._get_draft_flow_line()
        if flow_line_id._get_check_ok_flow():
            self.flow_line_id = flow_line_id
            self.state='draft'
            self.env['budget.flow.history'].create_history(flow_line_id , self, False, 'back')
        else:
            raise UserError(_('You are not draft user'))
        

    def action_done(self):
        context = dict(self.env.context or {})
        budget_obj = self.env['mw.account.company.budget']
        budget_com= budget_obj.search([('date_from','>=',self.date_from),('date_from','<=',self.date_to)])
        if budget_com:
            self.write({'budget_id':budget_com.id})
#         
        
    #------------------------------flow------------------
    def _default_department(self):
        return self.env['hr.department'].search([('id', '=', self.env.user.department_id.id)], limit=1)
            
    name = fields.Char( string="Төсвийн нэр", required=True, tracking=True,states={'draft': [('readonly', False)]}, readonly=True)
    description = fields.Char(tracking=True,states={'draft': [('readonly', False)]}, readonly=True)
    
    line_ids = fields.One2many(
        comodel_name="mw.account.budget.line", inverse_name="parent_id", copy=True,states={'draft': [('readonly', False)]}, readonly=True
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Компани",
        default=lambda self: self.env.company,states={'draft': [('readonly', False)]}, readonly=True
    )
    date_range_id = fields.Many2one(comodel_name="date.range", string="Огноо сонгох",states={'draft': [('readonly', False)]}, readonly=True)
    date_from = fields.Date(
        required=True, string="Эхлэх огноо", tracking=True,states={'draft': [('readonly', False)]}, readonly=True
    )
    date_to = fields.Date(required=True, string="Дуусах огноо", tracking=True,states={'draft': [('readonly', False)]}, readonly=True)
#     state = fields.Selection(
#         [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancelled", "Cancelled")],
#         required=True,
#         default="draft",
#         tracking=True,
#     )
    
    conf_id = fields.Many2one("mw.account.budget.configuration","Config",states={'draft': [('readonly', False)]}, readonly=True)

    type = fields.Selection(
        [("period", "Period"), ("month", "Month"), ("season", "Season")],
        required=True,
        default="month",
        tracking=True,states={'draft': [('readonly', False)]}, readonly=True
    )
    
    budget_id = fields.Many2one("mw.account.company.budget","Компаний төсөв",readonly=True)#states={'draft': [('readonly', False)]}, 
    
    
    analytic_account_id = fields.Many2one('account.analytic.account', 'Шинжилгээний данс',states={'draft': [('readonly', False)]}, readonly=True)
    department_id = fields.Many2one('hr.department', 'Хэлтэс', default=_default_department, tracking=True,)#readonly=True, states={'draft':[('readonly',False)]}, tur

    budget_total = fields.Float(string='Нийт төсөв', store=True, 
        compute='_compute_total_amount')

    real_total = fields.Float(string='Нийт гүйцэтгэл', store=True, 
        compute='_compute_total_amount')
    
    balance = fields.Float(string="Үлдэгдэл", store=True, 
        compute='_compute_total_amount')
    
    branch_id = fields.Many2one("res.branch","Branch",states={'draft': [('readonly', False)]}, readonly=True)

    root_dep_id = fields.Many2one('hr.department', string='Толгой хэлтэс', readonly=True, store=True, compute='_compute_root_dep_id')

    confirm_user_ids = fields.Many2many('res.users', string='Батлах хэрэглэгчид', compute='_compute_user_ids', store=True, readonly=True)

    history_ids=fields.One2many('budget.flow.history','budget_id','Workflow History', readonly=True)

    @api.depends('flow_line_id','flow_id.line_ids')#, 'flow_id.is_amount', 'amount'
    def _compute_user_ids(self):
        for item in self:
            temp_users = []
            if item.flow_id:
                for w in item.flow_id.line_ids:
                    temp = []
#                     print ('item.flow_id.is_amount ',item.flow_id.is_amount)
                    if item.flow_id.is_amount:
                        if w.amount_price_min==0 and w.amount_price_max==0:
#                             flow_line_ids.append(fl.id)
                            try:
            #                     print ('w.state_type ',w.state_type)
                                if w.state_type!='draft':
                                    temp = w._get_flow_users(item.branch_id,item.sudo().user_id.department_id, item.sudo().user_id).ids
                            except:
                                pass
                        elif w.amount_price_min<=item.amount and w.amount_price_max>=item.amount:
#                             flow_line_ids.append(fl.id)
                            try:
            #                     print ('w.state_type ',w.state_type)
                                if w.state_type!='draft':
                                    temp = w._get_flow_users(item.branch_id,item.sudo().user_id.department_id, item.sudo().user_id).ids
                            except:
                                pass
                    else:
                        try:
        #                     print ('w.state_type ',w.state_type)
                            if w.state_type!='draft':
                                users=w._get_flow_users(item.branch_id,item.sudo().create_uid.department_id, item.sudo().create_uid)
                                if users:
                                    temp = users.ids
                        except:
                            pass
#                             print ('temp ',temp)
                    temp_users+=temp
            
            item.confirm_user_ids = temp_users
            
            
    @api.depends('department_id',
                 'department_id.parent_id')
    def _compute_root_dep_id(self):
        for item in self:
            root_id=False
            if item.department_id:
                if item.department_id.parent_id and item.department_id.parent_id.parent_id:
                    root_id=item.department_id.parent_id.parent_id.id
                elif item.department_id.parent_id:
                    root_id=item.department_id.parent_id.id
                else:
                    root_id=item.department_id.id
            item.root_dep_id = root_id
            
            
    @api.depends(
                'line_ids',
                'line_ids.real_total',
                'line_ids.budget_total',
                )
    def _compute_total_amount(self):
        for item in self:
            total_budget=0
            real_total=0
            for line in item.line_ids:
                total_budget+=line.budget_total
                real_total += line.real_total
            item.budget_total = total_budget
            item.real_total = real_total
            item.balance=total_budget-real_total
                

    def create_lines(self, interval=1):
        period_line_obj = self.env['mw.account.budget.period.line']
        line_obj = self.env['mw.account.budget.line']
        period_line_line_obj = self.env['mw.account.budget.period.line.line']
        
        month = interval
        if self.type=='season':
            month=3
        for b in self:
            for conf in b.conf_id.line_ids:
                line=line_obj.create({
                    'description': conf.name,
                    'date_from': b.date_from,
                    'date_to': b.date_to,
                    'conf_line_id': conf.id,
                    'parent_id': b.id,
                })                
    
                for cl in conf.item_ids:
                    period_line=period_line_obj.create({
                        'name': conf.name,
                        'date_from': b.date_from,
                        'date_to': b.date_to,
                        'items_id': cl.id,
                        'parent_line_id': line.id,
                    })                                        
                    ds = b.date_from
        #             while ds.strftime('%Y-%m-%d') < fy.date_to:
                    while ds < b.date_to:
                        de = ds + relativedelta(months=month, days=-1)
        #                 if de.strftime('%Y-%m-%d') > fy.date_to:
                        if de > b.date_to:
        #                     de = datetime.strptime(fy.date_to, '%Y-%m-%d')
                            de = b.date_to
        
                        period_line_line_obj.create({
                            'name': ds.strftime('%m/%Y'),
                            'date_from': ds.strftime('%Y-%m-%d'),
                            'date_to': de.strftime('%Y-%m-%d'),
                            'period_line_id': period_line.id,
                        })
                        ds = ds + relativedelta(months=month)
        return True
    
    
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
            
class AccountBudgetLine(models.Model):
    _name = "mw.account.budget.line"
    _description = "Budget line"
    _order = 'code'    
#     _rec_name= "conf_line_id"
    

    @api.depends('period_line_ids',
                                    'period_line_ids.budget_01',
                                    'period_line_ids.budget_02',
                                    'period_line_ids.budget_03',
                                    'period_line_ids.budget_04',
                                    'period_line_ids.budget_05',
                                    'period_line_ids.budget_06',
                                    'period_line_ids.budget_07',
                                    'period_line_ids.budget_08',
                                    'period_line_ids.budget_09',
                                    'period_line_ids.budget_10',
                                    'period_line_ids.budget_11',
                                    'period_line_ids.budget_12',
                                    )
    def _compute_amount(self):
        for item in self:
            budget_01=0
            budget_02=0
            budget_03=0
            budget_04=0
            budget_05=0
            budget_06=0
            budget_07=0
            budget_08=0
            budget_09=0
            budget_10=0
            budget_11=0
            budget_12=0
#             if item.period_line_ids:
            for line in item.period_line_ids:
                budget_01 += line.budget_01
                budget_02 += line.budget_02
                budget_03 += line.budget_03
                budget_04 += line.budget_04
                budget_05 += line.budget_05
                budget_06 += line.budget_06
                budget_07 += line.budget_07
                budget_08 += line.budget_08
                budget_09 += line.budget_09
                budget_10 += line.budget_10
                budget_11 += line.budget_11
                budget_12 += line.budget_12     
            item.budget_01 = budget_01
            item.budget_02 = budget_02
            item.budget_03 = budget_03
            item.budget_04 = budget_04
            item.budget_05 = budget_05
            item.budget_06 = budget_06
            item.budget_07 = budget_07
            item.budget_08 = budget_08
            item.budget_09 = budget_09
            item.budget_10 = budget_10
            item.budget_11 = budget_11
            item.budget_12 = budget_12
            
            

    @api.depends('period_line_ids',
                    'period_line_ids.real_01',
                    'period_line_ids.real_02',
                    'period_line_ids.real_03',
                    'period_line_ids.real_04',
                    'period_line_ids.real_05',
                    'period_line_ids.real_06',
                    'period_line_ids.real_07',
                    'period_line_ids.real_08',
                    'period_line_ids.real_09',
                    'period_line_ids.real_10',
                    'period_line_ids.real_11',
                    'period_line_ids.real_12',
                                    )
    def _compute_real_amount(self):
        for item in self:
            real_01 = 0 
            real_02 = 0 
            real_03 = 0 
            real_04 = 0 
            real_05 = 0 
            real_06 = 0 
            real_07 = 0 
            real_08 = 0 
            real_09 = 0 
            real_10 = 0 
            real_11 = 0 
            real_12 = 0 
#             if item.period_line_ids:
            for line in item.period_line_ids:
                real_01 += line.real_01
                real_02 += line.real_02
                real_03 += line.real_03
                real_04 += line.real_04
                real_05 += line.real_05
                real_06 += line.real_06
                real_07 += line.real_07
                real_08 += line.real_08
                real_09 += line.real_09
                real_10 += line.real_10
                real_11 += line.real_11
                real_12 += line.real_12 
            item.real_01 = real_01
            item.real_02 = real_02
            item.real_03 = real_03
            item.real_04 = real_04
            item.real_05 = real_05
            item.real_06 = real_06
            item.real_07 = real_07
            item.real_08 = real_08
            item.real_09 = real_09
            item.real_10 = real_10
            item.real_11 = real_11
            item.real_12 = real_12         
                
    name = fields.Char("Төсвийн зориулалт")
    code = fields.Char("Код")
    
    description = fields.Char(tracking=True)
#     date_from = fields.Date(required=True, string="From Date")
#     date_to = fields.Date(required=True, string="To Date")
#     repair_hour = fields.Float(compute='_compute_run_hour', string='Repair hour', store = True, tracking=True)

    budget_01 = fields.Float(string="01 төсөв",compute='_compute_amount',store = True)
    real_01 = fields.Float(string="01 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_02 = fields.Float(string="02 төсөв",compute='_compute_amount',store = True)
    real_02 = fields.Float(string="02 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_03 = fields.Float(string="03 төсөв",compute='_compute_amount',store = True)
    real_03 = fields.Float(string="03 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_04 = fields.Float(string="04 төсөв",compute='_compute_amount',store = True)
    real_04 = fields.Float(string="04 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_05 = fields.Float(string="05 төсөв",compute='_compute_amount',store = True)
    real_05 = fields.Float(string="05 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_06 = fields.Float(string="06 төсөв",compute='_compute_amount',store = True)
    real_06 = fields.Float(string="06 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_07 = fields.Float(string="07 төсөв",compute='_compute_amount',store = True)
    real_07 = fields.Float(string="07 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_08 = fields.Float(string="08 төсөв",compute='_compute_amount',store = True)
    real_08 = fields.Float(string="08 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_09 = fields.Float(string="09 төсөв",compute='_compute_amount',store = True)
    real_09 = fields.Float(string="09 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_10 = fields.Float(string="10 төсөв",compute='_compute_amount',store = True)
    real_10 = fields.Float(string="10 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_11 = fields.Float(string="11 төсөв",compute='_compute_amount',store = True)
    real_11 = fields.Float(string="11 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_12 = fields.Float(string="12 төсөв",compute='_compute_amount',store = True)
    real_12 = fields.Float(string="12 гүйцэтгэл",compute='_compute_real_amount',store = True)
    balance = fields.Float(string="Үлдэгдэл")

    conf_line_id = fields.Many2one("mw.account.budget.configuration.line","Line")
    budget_amount = fields.Float(string="Amount budget")
    real_amount = fields.Float(string="Amount real")

    parent_id = fields.Many2one("mw.account.budget","Budget",ondelete="cascade",)

    period_line_ids = fields.One2many(
        comodel_name="mw.account.budget.period.line", inverse_name="parent_line_id", copy=True
    )
    
    analytic_account_id = fields.Many2one('account.analytic.account', 'Шинжилгээний данс')


    budget_total = fields.Float(string='Нийт төсөв', store=True, 
        compute='_compute_total_amount')

    real_total = fields.Float(string='Нийт гүйцэтгэл', store=True, 
        compute='_compute_total_amount')
    
    balance = fields.Float(string="Үлдэгдэл", store=True, 
        compute='_compute_total_amount')
    
    year = fields.Char(string='Жил', store=True, 
        compute='_compute_year')

    @api.depends(
                'budget_01',
                'budget_02',
                'budget_03',
                'budget_04',
                'budget_05',
                'budget_06',
                'budget_07',
                'budget_08',
                'budget_09',
                'budget_10',
                'budget_11',
                'budget_12',
                'real_01',
                'real_02',
                'real_03',
                'real_04',
                'real_05',
                'real_06',
                'real_07',
                'real_08',
                'real_09',
                'real_10',
                'real_11',
                'real_12',                
                )
    def _compute_total_amount(self):
        for item in self:
            total_budget=item.budget_01+item.budget_02+item.budget_03+item.budget_04+item.budget_05+item.budget_06+item.budget_07+item.budget_08+item.budget_09+item.budget_10+item.budget_11+item.budget_12
            real_total = item.real_01+item.real_02+item.real_03+item.real_04+item.real_05+item.real_06+item.real_07+item.real_08+item.real_09+item.real_10+item.real_11+item.real_12
            item.budget_total = total_budget
            item.real_total = real_total
            item.balance=total_budget-real_total


    @api.depends(
                'parent_id',
                'parent_id.date_from',
                )
    def _compute_year(self):
        for item in self:
            item.year=item.parent_id.date_from and str(item.parent_id.date_from.year) or ''
                        
class AccountBudgetPeriodLine(models.Model):
    _name = "mw.account.budget.period.line"
    _description = "Budget period line"
    _order = 'code'    

    @api.depends('period_line_line_ids',
                                    'period_line_line_ids.budget_01',
                                    'period_line_line_ids.budget_02',
                                    'period_line_line_ids.budget_03',
                                    'period_line_line_ids.budget_04',
                                    'period_line_line_ids.budget_05',
                                    'period_line_line_ids.budget_06',
                                    'period_line_line_ids.budget_07',
                                    'period_line_line_ids.budget_08',
                                    'period_line_line_ids.budget_09',
                                    'period_line_line_ids.budget_10',
                                    'period_line_line_ids.budget_11',
                                    'period_line_line_ids.budget_12',
                                    )
    def _compute_amount(self):
        for item in self:
            budget_01=0
            budget_02=0
            budget_03=0
            budget_04=0
            budget_05=0
            budget_06=0
            budget_07=0
            budget_08=0
            budget_09=0
            budget_10=0
            budget_11=0
            budget_12=0
#             if item.period_line_line_ids:
            for line in item.period_line_line_ids:
                budget_01 += line.budget_01
                budget_02 += line.budget_02
                budget_03 += line.budget_03
                budget_04 += line.budget_04
                budget_05 += line.budget_05
                budget_06 += line.budget_06
                budget_07 += line.budget_07
                budget_08 += line.budget_08
                budget_09 += line.budget_09
                budget_10 += line.budget_10
                budget_11 += line.budget_11
                budget_12 += line.budget_12     
            item.budget_01 = budget_01
            item.budget_02 = budget_02
            item.budget_03 = budget_03
            item.budget_04 = budget_04
            item.budget_05 = budget_05
            item.budget_06 = budget_06
            item.budget_07 = budget_07
            item.budget_08 = budget_08
            item.budget_09 = budget_09
            item.budget_10 = budget_10
            item.budget_11 = budget_11
            item.budget_12 = budget_12
                


    @api.depends('period_line_line_ids',
                    'period_line_line_ids.real_01',
                    'period_line_line_ids.real_02',
                    'period_line_line_ids.real_03',
                    'period_line_line_ids.real_04',
                    'period_line_line_ids.real_05',
                    'period_line_line_ids.real_06',
                    'period_line_line_ids.real_07',
                    'period_line_line_ids.real_08',
                    'period_line_line_ids.real_09',
                    'period_line_line_ids.real_10',
                    'period_line_line_ids.real_11',
                    'period_line_line_ids.real_12',
                                    )
    def _compute_real_amount(self):
        for item in self:
            real_01 = 0 
            real_02 = 0 
            real_03 = 0 
            real_04 = 0 
            real_05 = 0 
            real_06 = 0 
            real_07 = 0 
            real_08 = 0 
            real_09 = 0 
            real_10 = 0 
            real_11 = 0 
            real_12 = 0 
#             if item.period_line_ids:
            for line in item.period_line_line_ids:
                real_01 += line.real_01
                real_02 += line.real_02
                real_03 += line.real_03
                real_04 += line.real_04
                real_05 += line.real_05
                real_06 += line.real_06
                real_07 += line.real_07
                real_08 += line.real_08
                real_09 += line.real_09
                real_10 += line.real_10
                real_11 += line.real_11
                real_12 += line.real_12 
            item.real_01 = real_01
            item.real_02 = real_02
            item.real_03 = real_03
            item.real_04 = real_04
            item.real_05 = real_05
            item.real_06 = real_06
            item.real_07 = real_07
            item.real_08 = real_08
            item.real_09 = real_09
            item.real_10 = real_10
            item.real_11 = real_11
            item.real_12 = real_12 
                            
    name = fields.Char("Төсвийн зориулалт")
    code = fields.Char("Код")
    note = fields.Char("Тэмдэглэл")
##     date_from = fields.Date(required=True, string="From Date")
#     date_to = fields.Date(required=True, string="To Date")
# 
#     budget_amount = fields.Float(string="Amount budget")
#     real_amount = fields.Float(string="Amount real")

    budget_01 = fields.Float(string="01 төсөв",compute='_compute_amount',store = True)
    real_01 = fields.Float(string="01 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_02 = fields.Float(string="02 төсөв",compute='_compute_amount',store = True)
    real_02 = fields.Float(string="02 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_03 = fields.Float(string="03 төсөв",compute='_compute_amount',store = True)
    real_03 = fields.Float(string="03 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_04 = fields.Float(string="04 төсөв",compute='_compute_amount',store = True)
    real_04 = fields.Float(string="04 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_05 = fields.Float(string="05 төсөв",compute='_compute_amount',store = True)
    real_05 = fields.Float(string="05 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_06 = fields.Float(string="06 төсөв",compute='_compute_amount',store = True)
    real_06 = fields.Float(string="06 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_07 = fields.Float(string="07 төсөв",compute='_compute_amount',store = True)
    real_07 = fields.Float(string="07 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_08 = fields.Float(string="08 төсөв",compute='_compute_amount',store = True)
    real_08 = fields.Float(string="08 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_09 = fields.Float(string="09 төсөв",compute='_compute_amount',store = True)
    real_09 = fields.Float(string="09 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_10 = fields.Float(string="10 төсөв",compute='_compute_amount',store = True)
    real_10 = fields.Float(string="10 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_11 = fields.Float(string="11 төсөв",compute='_compute_amount',store = True)
    real_11 = fields.Float(string="11 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_12 = fields.Float(string="12 төсөв",compute='_compute_amount',store = True)
    real_12 = fields.Float(string="12 гүйцэтгэл",compute='_compute_real_amount',store = True)
    
    parent_line_id = fields.Many2one("mw.account.budget.line","Parent",ondelete="cascade",)

    period_line_line_ids = fields.One2many(
        comodel_name="mw.account.budget.period.line.line", inverse_name="period_line_id", copy=True
    )
    items_id = fields.Many2one("mw.account.budget.items","Items")
    
    budget_total = fields.Float(string='Нийт төсөв', store=True, 
        compute='_compute_total_amount')

    real_total = fields.Float(string='Нийт гүйцэтгэл', store=True, 
        compute='_compute_total_amount')
    
    balance = fields.Float(string="Үлдэгдэл", store=True, 
        compute='_compute_total_amount')
    
    year = fields.Char(string='Жил', store=True, 
        compute='_compute_year')

    @api.depends(
                'parent_line_id',
                'parent_line_id.year',
                )
    def _compute_year(self):
        for item in self:
            item.year=item.parent_line_id.year or ''
            
    @api.depends(
                'budget_01',
                'budget_02',
                'budget_03',
                'budget_04',
                'budget_05',
                'budget_06',
                'budget_07',
                'budget_08',
                'budget_09',
                'budget_10',
                'budget_11',
                'budget_12',
                'real_01',
                'real_02',
                'real_03',
                'real_04',
                'real_05',
                'real_06',
                'real_07',
                'real_08',
                'real_09',
                'real_10',
                'real_11',
                'real_12',                   
                )
    def _compute_total_amount(self):
        for item in self:
            total_budget=item.budget_01+item.budget_02+item.budget_03+item.budget_04+item.budget_05+item.budget_06+item.budget_07+item.budget_08+item.budget_09+item.budget_10+item.budget_11+item.budget_12
            real_total = item.real_01+item.real_02+item.real_03+item.real_04+item.real_05+item.real_06+item.real_07+item.real_08+item.real_09+item.real_10+item.real_11+item.real_12
            item.budget_total = total_budget
            item.real_total = real_total
            item.balance=total_budget-real_total
                
                
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('parent_line_id.name', '=ilike', '%' + name + '%'), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()

    @api.depends('name', 'parent_line_id.name')
    def name_get(self):
        result = []
        for account in self:
            parent=account.parent_line_id and account.parent_line_id.name or ''
            name = parent + ' - ' + account.name
            result.append((account.id, name))
        return result
    
    
class AccountBudgetPeriodLineLine(models.Model):
    _name = "mw.account.budget.period.line.line"
    _description = "Budget period line line"
    _order = 'code'
    

# select id,real_01, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=1 and state='done') as bud1,
# real_02, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=2 and state='done') as bud2,
# real_03, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=3 and state='done') as bud3,
# real_04,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=4 and state='done') as bud4,
# real_05,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=5 and state='done') as bud5,
# real_06, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=6 and state='done') as bud6,
# real_07,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=7 and state='done') as bud7,
# real_08,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=8 and state='done') as bud8,
# real_09,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=9 and state='done') as bud9,
# real_10, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=10 and state='done') as bud10,
# real_11,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=11 and state='done') as bud11,
# real_12,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=12 and state='done') as bud12
#  from mw_account_budget_period_line_line l order by id;
 
 
# update mw_account_budget_period_line_line set real_12=foo.bud12 from (
# select id,real_01, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=1 and state='done') as bud1,
# real_02, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=2 and state='done') as bud2,
# real_03, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=3 and state='done') as bud3,
# real_04,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=4 and state='done') as bud4,
# real_05,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=5 and state='done') as bud5,
# real_06, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=6 and state='done') as bud6,
# real_07,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=7 and state='done') as bud7,
# real_08,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=8 and state='done') as bud8,
# real_09,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=9 and state='done') as bud9,
# real_10, (select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=10 and state='done') as bud10,
# real_11,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=11 and state='done') as bud11,
# real_12,(select sum(amount) from payment_request where budget_id=l.id and EXTRACT(month from (date + interval '8 hour'))=12 and state='done') as bud12
#  from mw_account_budget_period_line_line l 
#  ) as foo where mw_account_budget_period_line_line.id=foo.id
 
 
     
    @api.depends('payment_ids',
                    'payment_ids.amount',
                    'payment_ids.date',
                    'payment_ids.state',
                                    )
    def _compute_real_amount(self):
        for item in self:
            real_01 = 0 
            real_02 = 0 
            real_03 = 0 
            real_04 = 0 
            real_05 = 0 
            real_06 = 0 
            real_07 = 0 
            real_08 = 0 
            real_09 = 0 
            real_10 = 0 
            real_11 = 0 
            real_12 = 0 
            real_all_total=0
#             if item.period_line_ids:
            for line in item.payment_ids:
                if line.state not in ('cancel','draft'):
                    real_all_total+=line.amount
                if line.state=='done':
                    if line.date:
                        print ('line.date.month ',line.date.month)
                        if int(line.date.month)==1:
                            real_01 += line.amount
                        if int(line.date.month)==2:
                            real_02 += line.amount
                        if int(line.date.month)==3:
                            real_03 += line.amount
                        if int(line.date.month)==4:
                            real_04 += line.amount
                        if int(line.date.month)==5:
                            real_05 += line.amount
                        if int(line.date.month)==6:
                            real_06 += line.amount
                        if int(line.date.month)==7:
                            real_07 += line.amount
                        if int(line.date.month)==8:
                            real_08 += line.amount
                        if int(line.date.month)==9:
                            real_09 += line.amount
                        if int(line.date.month)==10:
                            real_10 += line.amount
                        if int(line.date.month)==11:
                            real_11 += line.amount
                        if int(line.date.month)==12:
                            real_12 += line.amount                             
                    elif line.create_date:
                        if int(line.create_date.month)==1:
                            real_01 += line.amount
                        if int(line.create_date.month)==2:
                            real_02 += line.amount
                        if int(line.create_date.month)==3:
                            real_03 += line.amount
                        if int(line.create_date.month)==4:
                            real_04 += line.amount
                        if int(line.create_date.month)==5:
                            real_05 += line.amount
                        if int(line.create_date.month)==6:
                            real_06 += line.amount
                        if int(line.create_date.month)==7:
                            real_07 += line.amount
                        if int(line.create_date.month)==8:
                            real_08 += line.amount
                        if int(line.create_date.month)==9:
                            real_09 += line.amount
                        if int(line.create_date.month)==10:
                            real_10 += line.amount
                        if int(line.create_date.month)==11:
                            real_11 += line.amount
                        if int(line.create_date.month)==12:
                            real_12 += line.amount                         
#                 line.date.month
#                 real_01 += line.real_01
            item.real_01 = real_01
            item.real_02 = real_02
            item.real_03 = real_03
            item.real_04 = real_04
            item.real_05 = real_05
            item.real_06 = real_06
            item.real_07 = real_07
            item.real_08 = real_08
            item.real_09 = real_09
            item.real_10 = real_10
            item.real_11 = real_11
            item.real_12 = real_12 
            item.real_all_total=real_all_total
                
    name = fields.Char("Төсвийн зориулалт")
    code = fields.Char("Код")
    note = fields.Char("Тэмдэглэл")    
#     date_from = fields.Date(required=True, string="From Date")
#     date_to = fields.Date(required=True, string="To Date")
# 
#     budget_amount = fields.Float(string="Amount budget")
#     real_amount = fields.Float(string="Amount real")
    def _compute_edit(self):
        for bud in  self:
            is_can=True
            if not self.env.user.has_group('mw_account_budget.group_mn_budget_write_only'):
                is_can=False
            bud.can_edit_group  = is_can
            
    can_edit_group = fields.Boolean(string="ЗасахЮ",compute='_compute_edit')
    budget_01 = fields.Float(string="01 төсөв")
    real_01 = fields.Float(string="01 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_02 = fields.Float(string="02 төсөв")
    real_02 = fields.Float(string="02 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_03 = fields.Float(string="03 төсөв")
    real_03 = fields.Float(string="03 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_04 = fields.Float(string="04 төсөв")
    real_04 = fields.Float(string="04 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_05 = fields.Float(string="05 төсөв")
    real_05 = fields.Float(string="05 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_06 = fields.Float(string="06 төсөв")
    real_06 = fields.Float(string="06 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_07 = fields.Float(string="07 төсөв")
    real_07 = fields.Float(string="07 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_08 = fields.Float(string="08 төсөв")
    real_08 = fields.Float(string="08 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_09 = fields.Float(string="09 төсөв")
    real_09 = fields.Float(string="09 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_10 = fields.Float(string="10 төсөв")
    real_10 = fields.Float(string="10 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_11 = fields.Float(string="11 төсөв")
    real_11 = fields.Float(string="11 гүйцэтгэл",compute='_compute_real_amount',store = True)
    budget_12 = fields.Float(string="12 төсөв")
    real_12 = fields.Float(string="12 гүйцэтгэл",compute='_compute_real_amount',store = True)

    period_line_id = fields.Many2one("mw.account.budget.period.line","Parent",ondelete="cascade",)

#     change_line_id = fields.Many2one("mw.account.budget.change.line","Parent")
    
    budget_total = fields.Float(string='Нийт төсөв', store=True, 
        compute='_compute_amount')

    real_total = fields.Float(string='Нийт гүйцэтгэл', store=True, 
        compute='_compute_amount')
    
    balance = fields.Float(string="Үлдэгдэл", store=True, 
        compute='_compute_amount')
    
    all_balance = fields.Float(string="Нийт үлдэгдэл", store=True, 
        compute='_compute_amount')    
    
    payment_ids = fields.One2many(
        comodel_name="payment.request", inverse_name="budget_id", copy=False
    )    

    year = fields.Char(string='Жил', store=True, 
        compute='_compute_year')
    
    real_all_total = fields.Float(string='Нийт бүх гүйцэтгэл', store=True, 
        compute='_compute_real_amount')
    
    to_change_ids = fields.One2many(
        comodel_name="mw.account.budget.change.line", inverse_name="to_budget_id", copy=False
    )
    
    from_change_ids = fields.One2many(
        comodel_name="mw.account.budget.change.line", inverse_name="budget_id", copy=False
    )
    
    

    @api.depends(
                'period_line_id',
                'period_line_id.year',
                )
    def _compute_year(self):
        for item in self:
            item.year=item.period_line_id.year or ''
            
    @api.depends(
                'budget_01',
                'budget_02',
                'budget_03',
                'budget_04',
                'budget_05',
                'budget_06',
                'budget_07',
                'budget_08',
                'budget_09',
                'budget_10',
                'budget_11',
                'budget_12',
                'real_01',
                'real_02',
                'real_03',
                'real_04',
                'real_05',
                'real_06',
                'real_07',
                'real_08',
                'real_09',
                'real_10',
                'real_11',
                'real_12',)
    def _compute_amount(self):
        for item in self:
            total_budget=item.budget_01+item.budget_02+item.budget_03+item.budget_04+item.budget_05+item.budget_06+item.budget_07+item.budget_08+item.budget_09+item.budget_10+item.budget_11+item.budget_12
            real_total = item.real_01+item.real_02+item.real_03+item.real_04+item.real_05+item.real_06+item.real_07+item.real_08+item.real_09+item.real_10+item.real_11+item.real_12
            item.budget_total = total_budget
            item.real_total = real_total
            item.balance=total_budget-real_total
            item.all_balance=total_budget-item.real_all_total
                

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|',
                      ('period_line_id.parent_line_id.parent_id.name', '=ilike', '%' + name + '%'),
                      ('period_line_id.parent_line_id.name', '=ilike', '%' + name + '%'),
                      ('period_line_id.name', '=ilike', '%' + name + '%'),
                       ('name', operator, name),
                       ('code', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        accounts = self.search(domain + args, limit=limit)
        return accounts.name_get()

    @api.depends('name','code', 'parent_line_id.name','balance',
                 'period_line_id',
                 'period_line_id.name',
                 'period_line_id.parent_line_id',
                 'period_line_id.parent_line_id.name',
                 'period_line_id.parent_id.name',
                 'period_line_id.parent_line_id.parent_id.name',)
    def name_get(self):
        result = []
        for account in self:
            code=''
            parent=account.period_line_id and account.period_line_id.name or ''
            parent_parent=account.period_line_id and account.period_line_id.parent_line_id and account.period_line_id.parent_line_id.name or ''
            parent_parent_parent=account.period_line_id and account.period_line_id.parent_line_id and account.period_line_id.parent_line_id.parent_id and account.period_line_id.parent_line_id.parent_id.name or ''
            date = account.period_line_id and account.period_line_id.parent_line_id and account.period_line_id.parent_line_id.parent_id and account.period_line_id.parent_line_id.parent_id.date_from or ''
            year=date.year
            name_year=''
            balance=''
            if account.balance:
                balance=u' |үлдэгдэл: '+str(account.balance)+'| '
            if year:
                name_year=str(year)+u' оны '
            if account.code:
                code=' /'+account.code+'/'
            name=''
            if name_year:
                name += name_year
            if parent_parent_parent:
                name+=parent_parent_parent +': - '
            if parent_parent:
                name+= parent_parent+ ' - '
            if parent:
                name+=parent 
            if  account.name:
                name+=' - ' + account.name
            name+= code+balance
            result.append((account.id, name))
        return result    
    


class budget_flow_history(models.Model):
    _name = 'budget.flow.history'
    _description = 'Workflow Notes of budget'
    _order = 'date'
    
    
    name=    fields.Char('Name', size=64, required=True, translate=True)
    notes=    fields.Char('notes', size=64,)
    user_id=fields.Many2one('res.users', 'User', required=True)
    date=fields.Datetime('Date', required=True)
    amount=fields.Float('Amount')
    action=fields.Selection([('next','Next'),('back','Back'),('cancel','Cancel')],'Action', required=True)
    budget_id=fields.Many2one('mw.account.budget', 'Budget',  ondelete="cascade")
    flow_line_id = fields.Many2one('dynamic.flow.line', 'Төлөв')
    budget_com_id=fields.Many2one('mw.account.company.budget', 'Budget', ondelete="cascade")
    
    def create_history(self,flow_line_id,budget,budget_com,action,amount=0):
        context = self.env.context
        budget_com_id=False
        request_id=False
        if budget:
            request_id = budget.id  
            request_obj = budget
#             notes = budget.description
            desc = budget.name
        if budget_com:
            budget_com_id = budget_com.id  
            request_obj = budget_com
#             notes = budget_com.description
            desc = budget_com.name
        
        val = {
               'name' : _(desc),
               'user_id' : self.env.user.id,
               'action' : action,
               'notes' : 'notes',
               'amount':amount,
               'budget_id' : request_id,
               'budget_com_id':budget_com_id,
               'date':time.strftime('%Y-%m-%d %H:%M:%S'),
               'flow_line_id':flow_line_id.id
        }
        note_id = self.env['budget.flow.history'].create(val)

            
    