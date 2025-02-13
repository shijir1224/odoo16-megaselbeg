# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import AccessError, UserError, ValidationError
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from io import BytesIO
import base64
from odoo.osv import osv
from tempfile import NamedTemporaryFile
import os, xlrd


# Борлуулалтын урамшуулал
class SalesSalary(models.Model):
    _name = 'sales.salary'
    _description = "sales salary"

    @api.depends('year','month')
    def _name_write(self):
        for obj in self:
            if obj.month=='90':
                month = '10'
            elif obj.month=='91':
                month = '11'
            elif obj.month=='92':
                month = '12'
            else:
                month = obj.month

            if obj.year and obj.month:
                obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u'сарын kpi урамшуулал'
            else:
                obj.name=''

    name = fields.Char(string=u'Нэр', index=True, compute='_name_write'  )
    date = fields.Date('Огноо')
    end_date = fields.Date('Цалин татах огноо')
    year = fields.Char('Жил')
    month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
            ('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
            ('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
    line_ids = fields.One2many('sales.salary.line','parent_id','Lines')
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
    department_id = fields.Many2one('hr.department', 'Хэлтэс')
    data = fields.Binary('Exsel file')
    file_fname = fields.Char(string='File name')
    is_salary=fields.Boolean('Олгосон эсэх')


    def create_sales_line(self):
        line_pool =  self.env['sales.salary.line']
        if self.line_ids:
            self.line_ids.unlink()
        for obj in self:
            query = """SELECT 
                hr.id as hr_id,
                hd.id as hd_id,
                hj.id as hj_id,
                sl.id as sl_id,
                sl.eval_salary as eval_salary
                FROM hr_employee hr
                LEFT JOIN hr_department hd ON hd.id=hr.department_id
                LEFT JOIN hr_contract hc ON hc.employee_id=hr.id
                LEFT JOIN salary_level sl ON sl.id=hc.level_id
                LEFT JOIN hr_job hj ON hj.id=hr.job_id
                WHERE hr.work_location_id=%s"""%(self.work_location_id.id)
            self.env.cr.execute(query)
            records = self.env.cr.dictfetchall()
            desc={}
            amount=0
            for rec in records:

                line_data_id = line_pool.create({
                    'department_id' : rec['hd_id'],
                    'job_id' : rec['hj_id'],
                    'employee_id' : rec['hr_id'],
                    'level_id':rec['sl_id'],
                    # 'uramshuulal':rec['eval_salary'],
                    # 'worked_month':rec['month'],
                    # 'worked_day':rec['day'],
                    # 'amount':amount,
                    'parent_id': obj.id,
                    # 'description': desc
                })

    def action_import_line(self):
        deductioin_line_pool =  self.env['sales.salary.line']
        if self.line_ids:
            self.line_ids.unlink()
        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodebytes(self.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise osv.except_osv(u'Aldaa')
        book = xlrd.open_workbook(fileobj.name)
        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Aldaa')
        nrows = sheet.nrows
        
        rowi = 0
        data = []
        r=0
        for item in range(2,nrows):
            row = sheet.row(item)
            default_code = row[1].value
            amount = row[2].value          
            employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code)])
            if employee_ids:
                deductioin_line_id = deductioin_line_pool.create({'employee_id':employee_ids.id,
                            'parent_id': self.id,
                            'department_id': employee_ids.department_id.id,
                            'job_id': employee_ids.job_id.id,
                            'amount':amount,                        
                            })
            else:
                raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))


    def print_sales_salary(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'Борлуулалтын урамшуулал')

        file_name = 'Борлуулалтын урамшуулал'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,10, 'БОРЛУУЛАЛТЫН УРАМШУУЛЛЫН ТООЦОО', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Албан нэгж', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Албан тушаал', theader),
        sheet.merge_range(rowx,7,rowx+3,7, u'Цалингийн код', theader),
        sheet.merge_range(rowx,8,rowx+3,8, u'Урамшууллын хэмжээ /нэг сарын/', theader),
        sheet.merge_range(rowx,9,rowx+3,9, u'Үнэлгээ', theader),
        sheet.merge_range(rowx,10,rowx+3,10, u'Тооцсон урамшууллын хэмжээ', theader),
        sheet.merge_range(rowx,11,rowx+3,11, u'НДШ', theader), 
        sheet.merge_range(rowx,12,rowx+3,12, u'ХХОАТ', theader),    
        sheet.merge_range(rowx,13,rowx+3,13, u'Гарт олгох', theader),    
        sheet.merge_range(rowx,14,rowx+3,14, u'Гарт олгох', theader),    
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:O', 10)
        n=1
        des=''
        status=''

        if self.department_id:
            sales_line = self.env['sales.salary.line'].search([('parent_id', '=', self.id), ('department_id', '=', self.department_id.id)])
        else:
            sales_line=self.line_ids

        for data in sales_line:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.name,contest_left)
            sheet.write(rowx, 4, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 5, data.employee_id.department_id.name,contest_left)
            sheet.write(rowx, 6, data.employee_id.job_id.name,contest_left)
            sheet.write(rowx, 7, data.level_id.name,contest_right)
            sheet.write(rowx, 8, data.uramshuulal,contest_right)
            sheet.write(rowx, 9, data.evaluation,contest_right)
            sheet.write(rowx, 10, data.amount,contest_right)
            sheet.write(rowx, 11, data.shi,contest_right)
            sheet.write(rowx, 12, data.pit,contest_right)
            sheet.write(rowx, 13, data.amount_net,contest_right)
            sheet.write(rowx, 14, data.amount_net_round,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

    def print_sales_bank(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'Банкны тайлан')

        file_name = ' Банкны тайлан'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,6, 'ТӨСЛИЙН ГҮЙЦЭТГЭЛИЙН УРАМШУУЛАЛ', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Дансны дугаар', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Гарт олгох', theader),
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:O', 10)
        n=1
        des=''
        status=''
        for data in self.line_ids:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.name,contest_left)
            sheet.write(rowx, 4, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 5, data.employee_id.account_number,contest_left)
            sheet.write(rowx, 6, data.amount_net_round,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

class SalesSalaryLine(models.Model):
    _name = 'sales.salary.line'
    _description = "sales salary Line"

    @api.depends('uramshuulal','evaluation')
    def _compute_amount(self):
        for obj in self:
            obj.amount = obj.uramshuulal*obj.evaluation/100

    @api.depends('amount')
    def _compute_shi_pit(self):
        for obj in self:
            obj.shi = obj.amount*11.5/100
            contracts=self.env['hr.contract'].search([('employee_id', '=', obj.employee_id.id),('active', '=', True)])
            obj.pit = 0 
            for rec in contracts:
                if rec.insured_type_id.is_compute_pit==True:
                    obj.pit=0
                else:
                    obj.pit = (obj.amount-obj.amount*11.5/100)*0.1




    @api.depends('amount','shi','pit')
    def _compute_amounnet(self):
        for obj in self:
            obj.amount_net = obj.amount-obj.shi-obj.pit
            obj.amount_net_round = (obj.amount-obj.shi-obj.pit)//1000*1000

    parent_id = fields.Many2one('sales.salary','Parent', ondelete='cascade')
    date = fields.Date('Огноо')
    employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
    department_id = fields.Many2one('hr.department','Хэлтэс')
    job_id = fields.Many2one('hr.job','Албан тушаал')
    level_id = fields.Many2one('salary.level','Цалин.шат код')
    code = fields.Char('Цалин.шат код')
    uramshuulal = fields.Float('Урамшууллын хэмжээ /нэг сарын/', digits=(16, 2))
    evaluation = fields.Float('Үнэлгээ', digits=(16, 2))
    amount = fields.Float('Тооцсон урамшууллын хэмжээ', digits=(16, 2), )
    shi = fields.Float('НДШ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    pit = fields.Float('ХХОАТ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    amount_net = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)
    amount_net_round = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id

# Гүйцэтгэлийн урамшуулал
class KpiSalary(models.Model):
    _name = 'kpi.salary'
    _description = "KPI salary"

    @api.depends('year','month')
    def _name_write(self):
        for obj in self:
            if obj.month=='90':
                month = '10'
            elif obj.month=='91':
                month = '11'
            elif obj.month=='92':
                month = '12'
            else:
                month = obj.month

            if obj.year and obj.month:
                obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u'сарын kpi урамшуулал'
            else:
                obj.name=''

    name = fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
    date = fields.Date('Огноо')
    end_date = fields.Date('Дуусах огноо')
    year = fields.Char('Жил') 
    month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
            ('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
            ('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
    line_ids = fields.One2many('kpi.salary.line','parent_id','Lines')
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
    department_id = fields.Many2one('hr.department','Хэлтэс')
    data = fields.Binary('Exsel file')
    file_fname = fields.Char(string='File name')
    is_salary= fields.Boolean('Олгосон эсэх')

    def create_perpormance_line(self):
        line_pool =  self.env['kpi.salary.line']
        if self.line_ids:
            self.line_ids.unlink()
        for obj in self:
            query = """SELECT 
                hr.id as hr_id,
                hd.id as hd_id,
                hj.id as hj_id,
                sl.id as sl_id,
                sl.amount as hour_wage
                FROM hr_employee hr
                LEFT JOIN hr_department hd ON hd.id=hr.department_id
                LEFT JOIN hr_contract hc ON hc.employee_id=hr.id
                LEFT JOIN salary_level sl ON sl.id=hc.level_id
                LEFT JOIN hr_job hj ON hj.id=hr.job_id
                WHERE hr.work_location_id=%s"""%(self.work_location_id.id)
            self.env.cr.execute(query)
            records = self.env.cr.dictfetchall()
            desc={}
            amount=0

            for rec in records:
                hour_line = self.env['hour.balance.dynamic.line'].search([
                    ('employee_id', '=', rec['hr_id']),
                    ('parent_id.date_to', '=', obj.end_date)
                ], limit=1)
                
     
                line_eva =  self.env['hr.evaluation.cons.line'].search([('employee_id','=',rec['hr_id']),('parent_id.date_to','=',obj.date)],limit=1)
                if line_eva and hour_line.hour_to_work_month>0:
                    line_data_id = line_pool.create({
                        'department_id' : rec['hd_id'],
                        'job_id' : rec['hj_id'],
                        'employee_id' : rec['hr_id'],
                        'level_id':rec['sl_id'],
                        'evaluation':line_eva.total_score,
                        'work_to': hour_line.hour_to_work_month,
                        'hour_wage':rec['hour_wage'],
                        'parent_id': obj.id,
                        # 'uramshuulal':rec['kpi_salary'] if self.work_location_id.id==2 else  hour_line.hour_to_work_month*rec['hour_wage']*0.3
                        # 'description': desc
                    })

    def print_kpi(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'KPI урамшуулал')

        file_name = 'KPI урамшуулал'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,10, 'KPI УРАМШУУЛЛЫН ТООЦОО', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Албан нэгж', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Албан тушаал', theader),
        sheet.merge_range(rowx,7,rowx+3,7, u'Цалингийн код', theader),
        sheet.merge_range(rowx,8,rowx+3,8, u'Урамшууллын хэмжээ /нэг сарын/', theader),
        sheet.merge_range(rowx,9,rowx+3,9, u'Үнэлгээ', theader),
        sheet.merge_range(rowx,10,rowx+3,10, u'Тооцсон урамшууллын хэмжээ', theader),
        sheet.merge_range(rowx,11,rowx+3,11, u'НДШ', theader), 
        sheet.merge_range(rowx,12,rowx+3,12, u'ХХОАТ', theader),    
        sheet.merge_range(rowx,13,rowx+3,13, u'Гарт олгох', theader),    
        sheet.merge_range(rowx,14,rowx+3,14, u'Гарт олгох', theader),    
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:O', 10)
        n=1
        des=''
        status=''

        if self.department_id:
            kpi_line = self.env['kpi.salary.line'].search([('parent_id', '=', self.id),('department_id', '=', self.department_id.id)])
        else:
            kpi_line=self.line_ids

        for data in kpi_line:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.name,contest_left)
            sheet.write(rowx, 4, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 5, data.employee_id.department_id.name,contest_left)
            sheet.write(rowx, 6, data.employee_id.job_id.name,contest_left)
            sheet.write(rowx, 7, data.level_id.name,contest_right)
            sheet.write(rowx, 8, data.uramshuulal,contest_right)
            sheet.write(rowx, 9, data.evaluation,contest_right)
            sheet.write(rowx, 10, data.amount,contest_right)
            sheet.write(rowx, 11, data.shi,contest_right)
            sheet.write(rowx, 12, data.pit,contest_right)
            sheet.write(rowx, 13, data.amount_net,contest_right)
            sheet.write(rowx, 14, data.amount_net_round,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

    def print_kpi_bank(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'KPI урамшуулал')

        file_name = 'KPI урамшуулал'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,6, 'KPI УРАМШУУЛАЛ', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Дансны дугаар', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Гарт олгох', theader),
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 20)
        sheet.set_column('H:O', 15)
        n=1
        des=''
        status=''
        for data in self.line_ids:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 4, data.employee_id.name,contest_left)
            sheet.write(rowx, 5, data.employee_id.account_number,contest_left)
            sheet.write(rowx, 6, data.amount_net_round,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }


class KpiSalaryLine(models.Model):
    _name = 'kpi.salary.line'
    _description = "kpi salary Line"

    @api.depends('uramshuulal','evaluation')
    def _compute_amount(self):
        for obj in self:
            obj.amount = obj.uramshuulal*obj.evaluation/100

    @api.depends('amount')
    def _compute_shi_pit(self):
        for obj in self:
            obj.shi = obj.amount*11.5/100
            obj.pit = (obj.amount-obj.amount*11.5/100)*0.1

    @api.depends('amount','shi','pit')
    def _compute_amounnet(self):
        for obj in self:
            obj.amount_net = obj.amount-obj.shi-obj.pit
            obj.amount_net_round = (obj.amount-obj.shi-obj.pit)//1000*1000

    parent_id = fields.Many2one('kpi.salary','Parent', ondelete='cascade')
    date = fields.Date('Огноо')
    employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
    department_id = fields.Many2one('hr.department','Хэлтэс')
    job_id = fields.Many2one('hr.job','Албан тушаал')
    level_id = fields.Many2one('salary.level','Цалин.шат код')
    code = fields.Char('Цалин.шат код')
    uramshuulal = fields.Float('Урамшууллын хэмжээ /нэг сарын/', digits=(16, 2), compute='compute_uramshuulal_amount')
    evaluation = fields.Float('Үнэлгээ', digits=(16, 2))
    amount = fields.Float('Тооцсон урамшууллын хэмжээ', digits=(16, 2), readonly=True, compute=_compute_amount)
    shi = fields.Float('НДШ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    pit = fields.Float('ХХОАТ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    amount_net = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)
    amount_net_round = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)
    work_to = fields.Float('АЗ цаг')
    hour_wage = fields.Float('Нэг цагийн үнэлгээ')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
    @api.depends('work_to', 'hour_wage')
    def compute_uramshuulal_amount(self):
        for i in self:
            if i.employee_id.work_location_id.id==2:
                i.uramshuulal=i.level_id.kpi_salary
            else:
                if i.hour_wage and i.work_to:
                    i.uramshuulal= i.hour_wage*i.work_to*0.3
                else:
                    i.uramshuulal=0


# Эцгийн чөлөөний олговор
class DadSalary(models.Model):
    _name = 'dad.salary'
    _description = "Dad salary"

    @api.depends('year','month')
    def _name_write(self):
        for obj in self:
            if obj.month=='90':
                month = '10'
            elif obj.month=='91':
                month = '11'
            elif obj.month=='92':
                month = '12'
            else:
                month = obj.month

            if obj.year and obj.month:
                obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u' сарын удаан жилийн тооцоолол'
            else:
                obj.name=''

    name = fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
    date = fields.Date('Эцгийн чөлөөний тооцох огноо')
    salary_date = fields.Date('Цалин татах огноо')
    end_date = fields.Date('Дуусах огноо')
    year = fields.Char('Жил')
    month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
            ('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
            ('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
    line_ids = fields.One2many('dad.salary.line','parent_id','Lines')
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
    data = fields.Binary('Exsel file')
    file_fname = fields.Char(string='File name')

    def create_dad_line(self):
        line_pool =  self.env['dad.salary.line']
        if self.line_ids:
            self.line_ids.unlink()
        order=self.env['hr.order'].search([('order_type_id', '=', 11), ('starttime', '<=', self.salary_date),('trainee_end_date', '>=', self.salary_date),('state','=', 'done')])
        for obj in order:
            query = """SELECT
                        sum(line.amount_tootsson) as amount_tootsson,
                        sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SUMH')) as worked_hour,
                        count(so.id) as so_id
                        FROM salary_order so
                        LEFT JOIN salary_order_line line ON line.order_id=so.id
                        WHERE line.employee_id=%s and so.type='final' and so.date_invoice>='%s' and so.date_invoice<'%s'""" % (
                        obj.order_employee_id.id,
                        self.date,
                        self.salary_date,
                    )
            self.env.cr.execute(query)
            treemonth = self.env.cr.dictfetchall()
            amount=0
            for tr in treemonth:
                if tr['amount_tootsson'] and tr['worked_hour']:
                    amount=tr['amount_tootsson']/tr['worked_hour']
                # if tr["so_id"]==3:
                #     tree_hour = tr["worked_hour"]
                #     tree_wage = tr["amount_tootsson"]
                #     if tree_hour:
                #         tree_average_wage = tree_wage / tree_hour
                # else:
                #     tree_hour = 0
                #     tree_wage = 0
                #     tree_average_wage = 0
              
                line_data_id = line_pool.create({
                    'department_id' : obj.order_department_id.id,
                    'job_id' : obj.order_job_id.id,
                    'employee_id' : obj.order_employee_id.id,
                    'amount':amount*8*10,
                    'parent_id': self.id,
                    # 'description': desc
                })

    # def create_dad_line(self):
    #     line_pool =  self.env['dad.salary.line']
    #     if self.line_ids:
    #         self.line_ids.unlink()
    #     for obj in self:
    #         query = """SELECT 
    #             hr.id as hr_id,
    #             hd.id as hd_id,
    #             hj.id as hj_id,
    #             hr.engagement_in_company as engagement_in_company,
    #             (select extract(year from age('%s',hr.engagement_in_company))) as year,
    #             (select extract(month from age('%s',hr.engagement_in_company))) as month,
    #             (select extract(day from age('%s',hr.engagement_in_company))) as day
    #             FROM hr_employee hr
    #             LEFT JOIN hr_department hd ON hd.id=hr.department_id
    #             LEFT JOIN hr_contract hc ON hc.employee_id=hr.id
    #             LEFT JOIN hr_job hj ON hj.id=hr.job_id
    #             WHERE hr.work_location_id=%s"""%(self.date,self.date,self.date,self.work_location_id.id)
    #         self.env.cr.execute(query)
    #         records = self.env.cr.dictfetchall()
    #         desc={}
    #         amount=0
    #         for rec in records:
    #             if rec['year']>=1 and rec['year']<2:
    #                 amount = 300000
    #             elif rec['year']>=2 and rec['year']<3:
    #                 amount = 400000
    #             elif rec['year']>=3 and rec['year']<6:
    #                 amount = 500000
    #             elif rec['year']>=6:
    #                 amount = 600000
    #             else:
    #                 amount = 0
    #             line_data_id = line_pool.create({
    #                 'department_id' : rec['hd_id'],
    #                 'job_id' : rec['hj_id'],
    #                 'employee_id' : rec['hr_id'],
    #                 'date':rec['engagement_in_company'],
    #                 'worked_year':rec['year'],
    #                 'worked_month':rec['month'],
    #                 'worked_day':rec['day'],
    #                 'amount':amount,
    #                 'parent_id': obj.id,
    #                 # 'description': desc
    #             })

    def print_dad_salary(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'Эцгийн чөлөөний олговор')

        file_name = 'Эцгийн чөлөөний олговор'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,10, 'Эцгийн чөлөөний олговор', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Алба нэгж', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Албан тушаал', theader),
        sheet.merge_range(rowx,7,rowx+3,7, u'Олгох дүн', theader),
        # sheet.merge_range(rowx,7,rowx+2,9, u'Компанид ажилласан хугацаа', theader), 
        # sheet.write(rowx+3,7, u'Жил', theader),  
        # sheet.write(rowx+3,8, u'Сар', theader),  
        # sheet.write(rowx+3,9, u'Өдөр', theader),  
        # sheet.merge_range(rowx,10,rowx+3,10, u'Удаан жилийн урамшуулал', theader), 
        # sheet.merge_range(rowx,11,rowx+3,11, u'НДШ', theader), 
        # sheet.merge_range(rowx,12,rowx+3,12, u'ХХОАТ', theader),    
        # sheet.merge_range(rowx,13,rowx+3,13, u'Гарт олгох', theader),    
        # sheet.merge_range(rowx,14,rowx+3,14, u'Гарт олгох', theader),    
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 15)
        sheet.set_column('H:J', 15)
        sheet.set_column('K:O', 10)
        n=1
        des=''
        status=''
        for data in self.line_ids:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.name,contest_left)
            sheet.write(rowx, 4, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 5, data.department_id.name,contest_left)
            sheet.write(rowx, 6, data.job_id.name,contest_left)
            sheet.write(rowx, 7, data.amount,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

class DadSalaryLine(models.Model):
    _name = 'dad.salary.line'
    _description = "dad salary Line"

    # @api.depends('amount')
    # def _compute_shi_pit(self):
    #     for obj in self:
    #         obj.shi = obj.amount*11.5/100
    #         obj.pit = (obj.amount-obj.amount*11.5/100)*0.1

    # @api.depends('amount','shi','pit')
    # def _compute_amounnet(self):
    #     for obj in self:
    #         obj.amount_net = obj.amount-obj.shi-obj.pit
    #         obj.amount_net_round = round((obj.amount-obj.shi-obj.pit), 3)

    parent_id = fields.Many2one('dad.salary','Parent', ondelete='cascade')
    
    employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
    department_id = fields.Many2one('hr.department','Хэлтэс')
    job_id = fields.Many2one('hr.job','Албан тушаал')
    year = fields.Float('Ажилласан жил', digits=(16, 2))
    date = fields.Date('Ажилд орсон огноо')
    worked_year = fields.Integer('Жил')
    worked_month = fields.Integer('Сар')
    worked_day = fields.Integer('Өдөр')
    amount = fields.Float('Олгох дүн', digits=(16, 2))
    # # shi = fields.Float('НДШ')
    # # pit = fields.Float('ХХОАТ')
    # shi = fields.Float('НДШ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    # pit = fields.Float('ХХОАТ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    # amount_net = fields.Float('Гарт олгох')
    # amount_net = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)
    # amount_net_round = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id


# Удаан жилийн нэмэгдэл
class LongYearSalary(models.Model):
    _name = 'long.year.salary'
    _description = "long year salary"

    @api.depends('year','month')
    def _name_write(self):
        for obj in self:
            if obj.month=='90':
                month = '10'
            elif obj.month=='91':
                month = '11'
            elif obj.month=='92':
                month = '12'
            else:
                month = obj.month

            if obj.year and obj.month:
                obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u' сарын удаан жилийн тооцоолол'
            else:
                obj.name=''

    name = fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
    date = fields.Date('Удаан жил тооцох огноо')
    salary_date = fields.Date('Цалин татах огноо')
    end_date = fields.Date('Дуусах огноо')
    year = fields.Char('Жил')
    month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
            ('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
            ('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
    line_ids = fields.One2many('long.year.salary.line','parent_id','Lines')
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
    department_id = fields.Many2one('hr.department', 'Хэлтэс')
    data = fields.Binary('Exsel file')
    file_fname = fields.Char(string='File name')
    is_salary = fields.Boolean('Олгосон эсэх')


    def create_long_year_line(self):
        line_pool =  self.env['long.year.salary.line']
        if self.line_ids:
            self.line_ids.unlink()
        data = self.env['long.year.approve'].search([('parent_id.date', '=', self.date), ('parent_id.state', '=', 'done')])
       
        if data:
            for i in data:
                # employee_id = self.env['hr.employee'].search([('id','=',i.employee_id.id)],limit=1)
                if i.l_year>=1 and i.l_year<2:
                    amount = 300000
                elif i.l_year>=2 and i.l_year<3:
                    amount = 400000
                elif i.l_year>=3 and i.l_year<4:
                    amount = 500000
                elif i.l_year>=4 and i.l_year<5:
                    amount = 600000
                elif i.l_year>=5:
                    amount =700000
                else:
                    amount = 0
                    
                line_data_id = line_pool.create({
                    'department_id' : i.employee_id.department_id.id,
                    'job_id' : i.job_id.id,
                    'employee_id' : i.employee_id.id,
                    'date':i.engagement_in_company,
            
                    'worked_year':i.l_year,
                    'worked_month':i.long_year_month,
                    'worked_day':i.long_year_day,
                    'amount':amount,
                    'parent_id': self.id,
                    # 'description': desc
                })
                
            # query = """SELECT 
            #     hr.id as hr_id,
            #     hd.id as hd_id,
            #     hj.id as hj_id,
            #     hr.engagement_in_company as engagement_in_company,
            #     (select extract(year from age('%s',hr.engagement_in_company))) as year,
            #     (select extract(month from age('%s',hr.engagement_in_company))) as month,
            #     (select extract(day from age('%s',hr.engagement_in_company))) as day
            #     FROM hr_employee hr
            #     LEFT JOIN hr_department hd ON hd.id=hr.department_id
            #     LEFT JOIN hr_contract hc ON hc.employee_id=hr.id
            #     LEFT JOIN hr_job hj ON hj.id=hr.job_id
            #     WHERE hr.work_location_id=%s and hc.is_not_long_year=True and hr.employee_type in ('employee', 'contractor')"""%(self.date,self.date,self.date,self.work_location_id.id)
            # self.env.cr.execute(query)
            # records = self.env.cr.dictfetchall()
            # desc={}
            # amount=0
            # for rec in records:
                
            #     employee_id = self.env['hr.employee'].search([('id','=',rec['hr_id'])],limit=1)
            #     if float(employee_id.long_year)>=1 and float(employee_id.long_year)<2:
            #         amount = 300000
            #     elif float(employee_id.long_year)>=2 and float(employee_id.long_year)<3:
            #         amount = 400000
            #     elif float(employee_id.long_year)>=3 and float(employee_id.long_year)<4:
            #         amount = 500000
            #     elif float(employee_id.long_year)>=4 and float(employee_id.long_year)<5:
            #         amount = 600000
            #     elif float(employee_id.long_year)>=5:
            #         amount =700000
            #     else:
            #         amount = 0
                    
            #     line_data_id = line_pool.create({
            #         'department_id' : rec['hd_id'],
            #         'job_id' : rec['hj_id'],
            #         'employee_id' : rec['hr_id'],
            #         'date':rec['engagement_in_company'],
            #         # 'worked_year':rec['year'],
            #         # 'worked_month':rec['month'],
            #         # 'worked_day':rec['day'],
            #         'worked_year':float(employee_id.long_year),
            #         'worked_month':float(employee_id.long_year_month),
            #         'worked_day':float(employee_id.long_year_day),
            #         'amount':amount,
            #         'parent_id': obj.id,
            #         # 'description': desc
            #     })

    def print_long_salary(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'Удаан жилийн урамшуулал')

        file_name = 'Удаан жилийн урамшуулал'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,10, 'УДААН ЖИЛИЙН УРАМШУУЛЛЫН ТООЦОО', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Хэлтэс', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Албан тушаал', theader),
        sheet.merge_range(rowx,7,rowx+3,7, u'Компанид ажилд орсон огноо', theader),
        sheet.merge_range(rowx,8,rowx+2,10, u'Компанид ажилласан хугацаа', theader), 
        sheet.write(rowx+3,8, u'Жил', theader),  
        sheet.write(rowx+3,9, u'Сар', theader),  
        sheet.write(rowx+3,10, u'Өдөр', theader),  
        sheet.merge_range(rowx,11,rowx+3,11, u'Удаан жилийн урамшуулал', theader), 
        sheet.merge_range(rowx,12,rowx+3,12, u'НДШ', theader), 
        sheet.merge_range(rowx,13,rowx+3,13, u'ХХОАТ', theader),    
        sheet.merge_range(rowx,14,rowx+3,14, u'Гарт олгох', theader),    
        sheet.merge_range(rowx,15,rowx+3,15, u'Гарт олгох', theader),    
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:J', 5)
        sheet.set_column('K:O', 10)

        if self.department_id:
            long_year_line = self.env['long.year.salary.line'].search([('parent_id', '=', self.id), ('department_id', '=', self.department_id.id)])
        else:
            long_year_line = self.line_ids

        n=1
        des=''
        status=''
        # for data in self.line_ids:
        for data in long_year_line:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.name,contest_left)
            sheet.write(rowx, 4, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 5, data.employee_id.department_id.name,contest_left)
            sheet.write(rowx, 6, data.employee_id.job_id.name,contest_left)
            sheet.write(rowx, 7, str(data.date),contest_right)
            sheet.write(rowx, 8, data.worked_year,contest_right)
            sheet.write(rowx, 9, data.worked_month,contest_right)
            sheet.write(rowx, 10, data.worked_day,contest_right)
            sheet.write(rowx, 11, data.amount,contest_right)
            sheet.write(rowx, 12, data.shi,contest_right)
            sheet.write(rowx, 13, data.pit,contest_right)
            sheet.write(rowx, 14, data.amount_net,contest_right)
            sheet.write(rowx, 15, data.amount_net_round,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

    def print_long_bank(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'Банкны тайлан')

        file_name = ' Банкны тайлан'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,6, 'ТӨСЛИЙН ГҮЙЦЭТГЭЛИЙН УРАМШУУЛАЛ', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Дансны дугаар', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Гарт олгох', theader),
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:O', 10)
        n=1
        des=''
        status=''
        for data in self.line_ids:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 4, data.employee_id.name,contest_left)
            sheet.write(rowx, 5, data.employee_id.account_number,contest_left)
            sheet.write(rowx, 6, data.amount_net_round,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }
class LongYearSalaryLine(models.Model):
    _name = 'long.year.salary.line'
    _description = "long year salary Line"

    @api.depends('amount')
    def _compute_shi_pit(self):
        for obj in self:
            obj.shi = obj.amount*11.5/100
            obj.pit = (obj.amount-obj.amount*11.5/100)*0.1

    @api.depends('amount','shi','pit')
    def _compute_amounnet(self):
        for obj in self:
            obj.amount_net = obj.amount-obj.shi-obj.pit
            obj.amount_net_round = (obj.amount-obj.shi-obj.pit)//1000*1000

    parent_id = fields.Many2one('long.year.salary','Parent', ondelete='cascade')
    
    employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
    department_id = fields.Many2one('hr.department','Хэлтэс')
    job_id = fields.Many2one('hr.job','Албан тушаал')
    year = fields.Float('Ажилласан жил', digits=(16, 2))
    date = fields.Date('Ажилд орсон огноо')
    worked_year = fields.Integer('Жил')
    worked_month = fields.Integer('Сар')
    worked_day = fields.Integer('Өдөр')
    amount = fields.Float('УЖ урамшуулал', digits=(16, 2))
    # shi = fields.Float('НДШ')
    # pit = fields.Float('ХХОАТ')
    shi = fields.Float('НДШ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    pit = fields.Float('ХХОАТ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    amount_net = fields.Float('Гарт олгох')
    amount_net = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)
    amount_net_round = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet, store=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
            self.work_location_id = self.employee_id.work_location_id.id

# Гүйцэтгэлийн урамшуулал
class PerpormanceSalary(models.Model):
    _name = 'perpormance.salary'
    _description = "perpormance salary"

    @api.depends('year','month')
    def _name_write(self):
        for obj in self:
            if obj.month=='90':
                month = '10'
            elif obj.month=='91':
                month = '11'
            elif obj.month=='92':
                month = '12'
            else:
                month = obj.month

            if obj.year and obj.month:
                obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u'сарын гүйцэтгэлийн урамшуулал'
            else:
                obj.name=''

    name = fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
    date = fields.Date('Огноо')
    end_date = fields.Date('Дуусах огноо')
    year = fields.Char('Жил')
    month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
            ('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
            ('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
    line_ids = fields.One2many('perpormance.salary.line','parent_id','Lines')
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
    department_id = fields.Many2one('hr.department','Хэлтэс')
    data = fields.Binary('Exsel file')
    file_fname = fields.Char(string='File name')
    is_salary=fields.Boolean('Олгосон эсэх')

    def create_perpormance_line(self):
        line_pool =  self.env['perpormance.salary.line']
        if self.line_ids:
            self.line_ids.unlink()
        for obj in self:
            query = """SELECT 
                hr.id as hr_id,
                hd.id as hd_id,
                hj.id as hj_id,
                sl.id as sl_id,
                sl.eval_salary as eval_salary
                FROM hr_employee hr
                LEFT JOIN hr_department hd ON hd.id=hr.department_id
                LEFT JOIN hr_contract hc ON hc.employee_id=hr.id
                LEFT JOIN salary_level sl ON sl.id=hc.level_id
                LEFT JOIN hr_job hj ON hj.id=hr.job_id
                WHERE hr.work_location_id=%s"""%(self.work_location_id.id)
            self.env.cr.execute(query)
            records = self.env.cr.dictfetchall()
            desc={}
            amount=0
            for rec in records:
                line_eva =  self.env['hr.project.evaluation.line'].search([('employee_id', '=',rec['hr_id'] ),('parent_id.date_to','=',obj.date)])
                if line_eva:
                    line_data_id = line_pool.create({
                        'department_id' : rec['hd_id'],
                        'job_id' : rec['hj_id'],
                        'employee_id' : rec['hr_id'],
                        'level_id':rec['sl_id'],
                        'uramshuulal':rec['eval_salary'],
                        # 'worked_month':rec['month'],
                        # 'worked_day':rec['day'],
                        'evaluation':line_eva.amount_score,
                        'parent_id': obj.id,
                        # 'description': desc
                    })
          

    def print_perpormance(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'Гүйцэтгэлийн урамшуулал')

        file_name = 'Гүйцэтгэлийн урамшуулал'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,10, 'ТӨСЛИЙН ГҮЙЦЭТГЭЛИЙН УРАМШУУЛЛЫН ТООЦОО', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Хэлтэс', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Албан тушаал', theader),
        sheet.merge_range(rowx,7,rowx+3,7, u'Цалингийн код', theader),
        sheet.merge_range(rowx,8,rowx+3,8, u'Урамшууллын хэмжээ /нэг сарын/', theader),
        sheet.merge_range(rowx,9,rowx+3,9, u'Үнэлгээ', theader),
        sheet.merge_range(rowx,10,rowx+3,10, u'Тооцсон урамшууллын хэмжээ', theader),
        sheet.merge_range(rowx,11,rowx+3,11, u'НДШ', theader), 
        sheet.merge_range(rowx,12,rowx+3,12, u'ХХОАТ', theader),    
        sheet.merge_range(rowx,13,rowx+3,13, u'Гарт олгох', theader),    
        sheet.merge_range(rowx,14,rowx+3,14, u'Гарт олгох', theader),    
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:O', 10)
        n=1
        des=''
        status=''

        if self.department_id:
            perpormance_line = self.env['perpormance.salary.line'].search([('parent_id','=', self.id),('department_id','=', self.department_id.id)])
        else:
            perpormance_line = self.line_ids

        for data in perpormance_line:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 4, data.employee_id.name,contest_left)
            sheet.write(rowx, 5, data.employee_id.department_id.name,contest_left)
            sheet.write(rowx, 6, data.employee_id.job_id.name,contest_left)
            sheet.write(rowx, 7, data.level_id.name,contest_right)
            sheet.write(rowx, 8, data.uramshuulal,contest_right)
            sheet.write(rowx, 9, data.evaluation,contest_right)
            sheet.write(rowx, 10, data.amount,contest_right)
            sheet.write(rowx, 11, data.shi,contest_right)
            sheet.write(rowx, 12, data.pit,contest_right)
            sheet.write(rowx, 13, data.amount_net,contest_right)
            sheet.write(rowx, 14, data.amount_net_round,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

    def print_perpormance_bank(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'Гүйцэтгэлийн урамшуулал')

        file_name = 'Гүйцэтгэлийн урамшуулал'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_right = workbook.add_format({'num_format': '###,###,###'})
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)


        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,6, 'ТӨСЛИЙН ГҮЙЦЭТГЭЛИЙН УРАМШУУЛАЛ', theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Ажилтны код', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Овог', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'Нэр', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Дансны дугаар', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Гарт олгох', theader),
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('C:C', 7)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('F:F', 20)
        sheet.set_column('G:G', 10)
        sheet.set_column('H:O', 10)
        n=1
        des=''
        status=''
        for data in self.line_ids:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 3, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 4, data.employee_id.name,contest_left)
            sheet.write(rowx, 5, data.employee_id.account_number,contest_left)
            sheet.write(rowx, 6, data.amount_net_round,contest_right)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

class PerpormanceSalaryLine(models.Model):
    _name = 'perpormance.salary.line'
    _description = "perpormance salary Line"

    @api.depends('uramshuulal','evaluation')
    def _compute_amount(self):
        for obj in self:
            obj.amount = obj.uramshuulal*obj.evaluation/100

    @api.depends('amount')
    def _compute_shi_pit(self):
        for obj in self:
            obj.shi = obj.amount*11.5/100
            obj.pit = (obj.amount-obj.amount*11.5/100)*0.1

    @api.depends('amount','shi','pit')
    def _compute_amounnet(self):
        for obj in self:
            obj.amount_net = obj.amount-obj.shi-obj.pit
            obj.amount_net_round = (obj.amount-obj.shi-obj.pit)//1000*1000

    parent_id = fields.Many2one('perpormance.salary','Parent', ondelete='cascade')
    date = fields.Date('Огноо')
    employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
    department_id = fields.Many2one('hr.department','Хэлтэс')
    job_id = fields.Many2one('hr.job','Албан тушаал')
    level_id = fields.Many2one('salary.level','Цалин.шат код')
    code = fields.Char('Цалин.шат код')
    uramshuulal = fields.Float('Урамшууллын хэмжээ /нэг сарын/', digits=(16, 2))
    evaluation = fields.Float('Үнэлгээ', digits=(16, 2))
    amount = fields.Float('Тооцсон урамшууллын хэмжээ', digits=(16, 2), readonly=True, compute=_compute_amount)
    shi = fields.Float('НДШ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    pit = fields.Float('ХХОАТ', digits=(16, 2), readonly=True, compute=_compute_shi_pit)
    amount_net = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)
    amount_net_round = fields.Float('Гарт олгох', digits=(16, 2), readonly=True, compute=_compute_amounnet)


    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
            self.work_location_id = self.employee_id.work_location_id.id


# Суутгалын төлөвлөгөө
class HealthInsurance(models.Model):
    _name = 'health.insurance'
    _description = "health insurance"

    @api.depends('year','month')
    def _name_write(self):
        for obj in self:
            if obj.month=='90':
                month = '10'
            elif obj.month=='91':
                month = '11'
            elif obj.month=='92':
                month = '12'
            else:
                month = obj.month

            if obj.year and obj.month:
                obj.name=obj.year+' ' + u'оны'+' '+month+' ' + u' сарын цалингийн урьдчилгаа'
            else:
                obj.name=''

    name = fields.Char(string=u'Нэр', index=True, readonly=True, compute=_name_write)
    date = fields.Date('Огноо')
    end_date = fields.Date('Дуусах огноо')
    year = fields.Char('Жил')
    month=fields.Selection([('1','1 сар'), ('2','2 сар'), ('3','3 сар'), ('4','4 сар'),
            ('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),
            ('90','10 сар'), ('91','11 сар'), ('92','12 сар')], u'Сар')
    line_ids = fields.One2many('health.insurance.line','parent_id','Lines')
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
    data = fields.Binary('Exsel file')
    file_fname = fields.Char(string='File name')

    employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
    department_id = fields.Many2one('hr.department','Хэлтэс')
    job_id = fields.Many2one('hr.job','Албан тушаал')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.department_id = self.employee_id.department_id.id
            self.job_id = self.employee_id.job_id.id
            self.work_location_id = self.employee_id.work_location_id.id

    @api.onchange('data')
    @api.depends('data','file_fname')

    def check_file_type(self):
        if self.data:
            filename,filetype = os.path.splitext(self.file_fname)

    def action_import_line(self):
        deductioin_line_pool =  self.env['health.insurance.line']
        if self.line_ids:
            self.line_ids.unlink()
        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodebytes(self.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise osv.except_osv(u'Aldaa')
        book = xlrd.open_workbook(fileobj.name)
        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Aldaa')
        nrows = sheet.nrows
        
        rowi = 0
        data = []
        r=0
        for item in range(7,nrows):

            row = sheet.row(item)
            default_code = row[6].value
            cont = row[2].value
            ball = row[3].value
            napt = row[4].value
            weight = row[10].value
            date = row[11].value
            difference = row[12].value
            tn_allounce = row[13].value
            car_number = row[9].value
            employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code)])
            if employee_ids:
                deductioin_line_id = deductioin_line_pool.create({'employee_id':employee_ids.id,
                            'parent_id': self.id,
                            'department_id': employee_ids.department_id.id,
                            'job_id': employee_ids.job_id.id,
                            'cont':cont,
                            'ball':ball,
                            'napt':napt,
                            'car_number':car_number,
                            'date':date,
                            # 'weight':weight,
                            'difference':difference,
                            'tn_allounce':tn_allounce,
                            })
            else:
                raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))

    def print_deductioin_plan(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        sheet = workbook.add_worksheet(u'РЭЙС')

        file_name = 'РЭЙС'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')


        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        rowx=0
        save_row=3
        
        sheet.merge_range(rowx+1,0,rowx+1,10, self.name, theader1),
        
        rowx=3
        sheet.merge_range(rowx,1,rowx+3,1, u'№', theader),
        sheet.merge_range(rowx,2,rowx+3,2, u'Гэрээ', theader),
        sheet.merge_range(rowx,3,rowx+3,3, u'Бөмбөлөг', theader),
        sheet.merge_range(rowx,4,rowx+3,4, u'НАБТ талбай', theader),
        sheet.merge_range(rowx,5,rowx+3,5, u'Регистр', theader),
        sheet.merge_range(rowx,6,rowx+3,6, u'Ажилтны код', theader),
        sheet.merge_range(rowx,7,rowx+3,7, u'Овог', theader),
        sheet.merge_range(rowx,8,rowx+3,8, u'Нэр', theader),
        sheet.merge_range(rowx,9,rowx+3,9, u'Машины дугаар', theader),
        sheet.merge_range(rowx,10,rowx+3,10, u'Цэвэр жин', theader),    
        sheet.merge_range(rowx,11,rowx+3,11, u'Буулгасан огноо', theader),
        sheet.merge_range(rowx,12,rowx+3,12, u'Зөрүү', theader),    
        sheet.merge_range(rowx,13,rowx+3,13, u'Тн тутмын нэмэгдэл', theader),   
        sheet.merge_range(rowx,14,rowx+3,14, u'Нийт нэмэгдэл', theader),    

        
        
        sheet.freeze_panes(7, 6)
        rowx+=4
        
        sheet.set_column('A:A', 1)
        sheet.set_column('B:B', 4)
        sheet.set_column('F:F', 12)
        sheet.set_column('D:D', 12)
        sheet.set_column('E:E', 12)
        sheet.set_column('H:U', 10)
        n=1
        des=''
        status=''
        for data in self.line_ids:

            sheet.write(rowx, 1, n,contest_left)
            sheet.write(rowx, 2, data.cont,contest_left)
            sheet.write(rowx, 3, data.ball,contest_left)
            sheet.write(rowx, 4, data.napt,contest_left)
            sheet.write(rowx, 5, data.employee_id.passport_id,contest_left)
            sheet.write(rowx, 6, data.employee_id.identification_id,contest_left)
            sheet.write(rowx, 7, data.employee_id.last_name,contest_left)
            sheet.write(rowx, 8, data.employee_id.name,contest_left)
            sheet.write(rowx, 9, data.car_number,contest_left)
            sheet.write(rowx, 10, data.weight,contest_left)
            sheet.write(rowx, 11, str(data.date),contest_left)
            sheet.write(rowx, 12, data.difference,contest_left)
            sheet.write(rowx, 13, data.tn_allounce,contest_left)
            sheet.write(rowx, 14, data.sum_alloune,contest_left)

            rowx+=1
            n+=1

        workbook.close()
        out = base64.encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }


class HealthInsuranceLine(models.Model):
    _name = 'health.insurance.line'
    _description = "health.insurance Line"

    # @api.depends('weight')
    # def _compute_difference(self):
    #   for obj in self:
    #       obj.difference=obj.weight*0.99

    # @api.depends('difference','tn_allounce')
    # def _compute_sum_alloune(self):
    #   for obj in self:
    #       obj.sum_alloune=obj.difference*obj.tn_allounce

    parent_id = fields.Many2one('health.insurance','Parent', ondelete='cascade')
    date = fields.Date('Огноо')
    amount = fields.Float('Суутгах дүн', digits=(16, 2))
    done_amount = fields.Float('Суутгасан дүн', digits=(16, 2))

#Цалингийн зардал
class hr_timetable_line_line(models.Model):
	_inherit = "hr.timetable.line.line"

	costline_line_id = fields.Many2one("salary.cost.line", string="Setup line", index=True)


class SalaryCost(models.Model):
    _name = 'salary.cost'
    _description = "salary cost"

    name = fields.Char(string=u'Нэр', index=True, readonly=True)
    year = fields.Char('Жил')
    end_date = fields.Date('Цалингийн огноо')
    work_location = fields.Many2one('hr.work.location', 'Үндсэн байршил')
    line_ids =fields.One2many('salary.cost.line', 'parent_id', 'line')
    month = fields.Selection([('1','1 сар'),('2','2 сар'), ('3','3 сар'), ('4','4 сар'), ('5','5 сар'), ('6','6 сар'), ('7','7 сар'), ('8','8 сар'), ('9','9 сар'),('90','10 сар'),('91','11 сар'),('92','12 сар')],'Сар')
    account_move_id = fields.Many2one('account.move', string='Цалин, НДШ бичилт',readonly=True)
    account_payable_id = fields.Many2one('account.account', string='Цалингийн өглөгийн данс')
    account_shi_id = fields.Many2one('account.account', string='НДШ өглөгийн данс')
    journal_id = fields.Many2one('account.journal', string='Журнал')
    data = fields.Binary('Exsel file')



    def import_line(self):
        cost_line_pool =  self.env['salary.cost.line']
        line_pool =  self.env['salary.cost.detail']
        if self.line_ids:
            self.line_ids.unlink()
        fileobj = NamedTemporaryFile('w+b')
        fileobj.write(base64.decodebytes(self.data))
        fileobj.seek(0)
        if not os.path.isfile(fileobj.name):
            raise osv.except_osv(u'Aldaa')
        book = xlrd.open_workbook(fileobj.name)
        
        try :
            sheet = book.sheet_by_index(0)
        except:
            raise osv.except_osv(u'Aldaa')
        nrows = sheet.nrows
        
        rowi = 0
        data = []
        r=0
        for item in range(3,nrows):
            row = sheet.row(item)
            default_code = row[1].value
            project_id = row[2].value          
            sum_hour = row[3].value          
            employee_ids = self.env['hr.employee'].search([('identification_id','=',default_code)])
            if employee_ids:
                obj=cost_line_pool.search([('employee_id', '=',employee_ids.id), ('parent_id','=', self.id)])
                print('=====ooooooiii', obj)
                for i in obj:
                    deductioin_line_id = line_pool.create({
                                'parent_id':i.id,
                                'project_id':project_id,
                                'sum_time':sum_hour,                                          
                                })
            else:
                raise UserError(_('%s дугаартай ажилтны мэдээлэл байхгүй байна.')%(default_code))



    def create_line(self):
        if self.line_ids:
            self.line_ids.unlink()
        mount_code = self.month
        salary = self.env['salary.order'].search([('month', '=', self.month), ('type', '=', 'final'), ('year', '=', self.year)])
        line_obf = self.env['salary.cost.line']
        detail_line = self.env['salary.cost.detail']
        for i in salary:
            for order_line in i.order_line:
                line = line_obf.create({
                    'name' : self.name,
                    'parent_id' : self.id,
                    'sum_tootsson_salary':order_line.amount_tootsson,
                    'tootsson_salary': order_line.amount_tootsson-order_line.project_salary-order_line.kpi_salary,
                    'reward_salary': order_line.project_salary,
                    'kpi_salary':order_line.kpi_salary,
                    'oshi_tootsson':order_line.bndsh,
                    # 'ndsh_tootsson':order_line.shi,
                    'worked_hour': order_line.total_hr,
                    'employee_id' : order_line.employee_id.id,
                    # 'huwisah_salary':order_line.amount_tootsson-line_obf.free_salary,
                    'bndsh': order_line.insured_type_id.o_shi_procent+order_line.employee_id.job_id.job_conf.percent,
            })
                # print('====len', len(line))
                for lines in line:
                    timetable = self.env['hr.timetable.line'].search([('year','=', self.year),('month', '=', self.month), ('employee_id', '=', lines.employee_id.id),('parent_id.state', '=', 'done')])
                    for timetables in timetable:
                            timetableline = self.env['hr.timetable.line.line'].search([('parent_id', '=',timetables.id ),('employee_id', '=', timetables.employee_id.id)])
                            project_mapped = timetableline.mapped('project_id')
                            for project in project_mapped:
                                tline = timetableline.filtered(lambda r: r.project_id.id == project.id)
                              
                                # for timetablelines in tline:
                                detail_lines = detail_line.create({
                                    'project_id' : project.id,
                                    'parent_id' : line.id,
                                    'worked_hour': sum([line.worked_salary_hour for line in tline]),
                                    'night_hour': sum([line.night_hour for line in tline]),
                                    'overtime':sum([line.overtime_hour for line in tline]) ,
                                    'busines_trip_hour':timetables.busines_trip_hour,
                                    'busines_trip_hour2':timetables.busines_trip_hour2,
                                    'holiday_worked_hour': sum([line.holiday_worked_hour for line in tline]),
                                    'tourist_hour': sum([line.tourist_hour for line in tline]),
                                    'weekend_night': sum([line.weekend_night for line in tline]),
                                    'free_wage_hour':sum([line.free_wage_hour for line in tline]),
                                    'z_hour':timetables.z_hour,
                                    'salary_ov_time':timetables.overtime,
                                    'hs_id': tline[0].shift_plan_id.id if tline else None ,                                      
                                })
                                  
    def print_salary_cost(self,context={}):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        
        file_name = 'Цалингийн зардалын задаргаа'

        # CELL styles тодорхойлж байна
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(11)
        h1.set_font('Times new roman')
        h1.set_align('center')
        h1.set_align('vcenter')

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(10)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        theader.set_bg_color('#c4d79b')

        content_right = workbook.add_format()
        content_right.set_text_wrap()
        content_right.set_font('Times new roman')
        content_right.set_font_size(9)
        content_right.set_border(style=1)
        content_right.set_align('right')

        content_left = workbook.add_format({'num_format': '###,###,###.##'})
        content_left.set_text_wrap()
        content_left.set_font('Times new roman')
        content_left.set_font_size(9)
        content_left.set_border(style=1)
        content_left.set_align('left')
    
    
        fooder = workbook.add_format({'bold': 1})
        fooder.set_font_size(10)
        fooder.set_text_wrap()
        fooder.set_font('Times new roman')
        fooder.set_align('center')
        fooder.set_align('vcenter')
        fooder.set_border(style=1)
        fooder.set_bg_color('#c4d79b')

        sheet = workbook.add_worksheet(u'Цалин')


        month_code=0
        if self.month=='1':
            month_code=1
        if self.month=='2':
            month_code=2
        if self.month=='3':
            month_code=3
        if self.month=='4':
            month_code=4
        if self.month=='5':
            month_code=5
        if self.month=='6':
            month_code=6
        if self.month=='7':
            month_code=7
        if self.month=='8':
            month_code=8 
        if self.month=='9':
            month_code=9
        if self.month=='90':
            month_code=10
        if self.month=='91':
            month_code=11
        if self.month=='92':
            month_code=12 

        # sheet.merge_range(0,0,0,3, u'Байгууллагын нэр:' content_right),
        sheet.merge_range(3, 0, 3, 8, u'%s ОНЫ %s-р ЗАРДЛЫН ХУВИАРЛАЛТ ХҮСНЭЛТ'%(self.year,month_code), h1)

        rowx=6
        # save_row=7
        sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
        sheet.merge_range(rowx,1,rowx+2,1, u'Код', theader),
        sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
        sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),
        sheet.merge_range(rowx,4,rowx+2,4, u'Алба нэгж', theader),
        sheet.merge_range(rowx,5,rowx+2,5, u'Албан тушаал', theader),
        sheet.merge_range(rowx,6,rowx+2,6, u'Регистрийн дугаар', theader),
        sheet.merge_range(rowx,7,rowx+2,7, u'Цалингаас татсан нийт цаг', theader),
        sheet.merge_range(rowx,8,rowx+2,8, u'Нийт ажилласан цаг', theader),
        sheet.merge_range(rowx,9,rowx+2,9, u'Ажилласан цаг', theader),
        sheet.merge_range(rowx,10,rowx+2,10, u'Шөнийн цаг', theader),
        sheet.merge_range(rowx,11,rowx+2,11, u'Баяр цаг', theader),
        sheet.merge_range(rowx,12,rowx+2,12, u'Илүү цаг', theader),
        sheet.merge_range(rowx,13,rowx+2,13, u'Томилолт', theader),
        sheet.merge_range(rowx,14,rowx+2,14, u'Аялалын цаг', theader),
        sheet.merge_range(rowx,15,rowx+2,15, u'Ажилласан цаг Уурхай Фонд', theader),
        sheet.merge_range(rowx,16,rowx+2,16, u'Ажилласан цаг UB Фонд', theader),
        sheet.merge_range(rowx,17,rowx+2,17, u'Уурхайн ИЦ', theader),
        sheet.merge_range(rowx,18,rowx+2,18, u'ИЦ/Цалин тооцох/', theader),

      
        n=1
        rowx+=3
        sheet.set_column('A:A', 5)
        sheet.set_column('B:B', 6)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 15)
        sheet.set_column('E:E', 25)
        sheet.set_column('F:F', 25)
        if self.line_ids:
            line = self.env['salary.cost.line'].search([('parent_id','=',self.id)])
            if line:
                for data in line:
                    last_sum = sum(data.line_ids.mapped('sum_time'))
                    last_worked_hour = sum(data.line_ids.mapped('worked_hour'))
                    last_night_hour = sum(data.line_ids.mapped('night_hour'))
                    last_holiday_worked_hour = sum(data.line_ids.mapped('holiday_worked_hour'))
                    last_overtime = sum(data.line_ids.mapped('overtime'))
                    last_busines_trip_hour = sum(data.line_ids.mapped('busines_trip_hour'))
                    last_tourist_hour = sum(data.line_ids.mapped('tourist_hour'))
                    last_fond_hour = sum(data.line_ids.mapped('fond_worked_hour'))

                    # for data in line_line.line_ids:
                    sheet.write(rowx, 0, n,content_left)
                    sheet.write(rowx, 1, data.employee_id.identification_id,content_left)
                    sheet.write(rowx, 2,data.employee_id.last_name,content_left)
                    sheet.write(rowx, 3,data.employee_id.name,content_left)
                    sheet.write(rowx, 4,data.employee_id.department_id.name,content_left)
                    sheet.write(rowx, 5,data.employee_id.job_id.name,content_left)
                    sheet.write(rowx, 6,data.employee_id.passport_id,content_left)
                    sheet.write(rowx, 7,data.worked_hour,content_left)
                    # for ll in data.line_ids:

                    sheet.write(rowx, 8,last_sum,content_left)
                    sheet.write(rowx, 9,last_worked_hour,content_left)
                    sheet.write(rowx, 10,last_night_hour,content_left)
                    sheet.write(rowx, 11,last_holiday_worked_hour,content_left)
                    sheet.write(rowx, 12,last_overtime,content_left)
                    sheet.write(rowx, 13,last_busines_trip_hour,content_left)
                    sheet.write(rowx, 14,last_tourist_hour,content_left)
                    sheet.write(rowx, 15,last_fond_hour,content_left)
                    sheet.write(rowx, 16,sum(data.line_ids.mapped('ub_fond_worked_hour')),content_left)
                    sheet.write(rowx, 17,sum(data.line_ids.mapped('uurkhai_ov')),content_left)
                    sheet.write(rowx, 18,sum(data.line_ids.mapped('wage_over_time')),content_left)
                        
                    rowx+=1
                    n+=1

        # sheet.merge_range(rowx, 0, rowx, 7, u'НИЙТ', fooder)
        # l=4
        # while l <= colx-1:
        #     sheet.write_formula(rowx, l, '{=SUM('+self._symbol(save_row-1, l) +':'+ self._symbol(rowx-1, l)+')}', fooder)
        #     l+=1
        # 	sheet.write_formula(rowx, 5, "{=SUM(F%d:F%d)}" % (5, rowx), center_bold)

        # rowx += 1

        # rowx+=2
        # sheet.write(rowx, 2, u'Бэлтгэсэн:', h2)
        # sheet.merge_range(rowx, 3, rowx, 5, u'Нягтлан бодогч:......................../%s.%s/'%(self.preparatory.last_name[:1],self.preparatory.name), h1)

        # sheet.write(rowx+1, 2, u'Хянасан:', h2)
        # sheet.merge_range(rowx+1, 3, rowx+1, 5, u'%s:....................../%s.%s/'%(self.compute_controller.job_id.name,self.compute_controller.last_name[:1],self.compute_controller.name), h1)
        
        # sheet.write(rowx+2, 2, u'Баталсан:', h2)
        # sheet.merge_range(rowx+2, 3, rowx+2, 5, u'Гүйцэтгэх захирал:.................../%s.%s/'%(self.done_director.last_name[:1],self.done_director.name), h1)
        
        workbook.close()
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'view_id': False,
            'type' : 'ir.actions.act_url',
            'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
            'target': 'new',
            'nodestroy': True,
        }

    def _symbol(self, row, col):
        return self._symbol_col(col) + str(row+1)

    def _symbol_col(self, col):
        excelCol = str()
        div = col+1
        while div:
            (div, mod) = divmod(div-1, 26)
            excelCol = chr(mod + 65) + excelCol
        return excelCol


    def create_expense_invoice_syl(self):
        move_pool = self.env['account.move']
        dep_id = self.env['hr.department']
        user_bool = self.env['res.users']
        partner_bool = self.env['res.partner']
        
        for obj in self:
            order_line = []
            debit_sum = 0.0
            credit_sum = 0.0
            # line_project_id=self.env['']
            if obj.month=='90':
                month='10'
            elif obj.month=='91':
                month='11'
            elif obj.month=='92':
                month='12'
            else:
                month=obj.month

            if obj.account_move_id:
                raise UserError(_("System in create journal"))
            else:
                move = {
                    'date': obj.end_date,
                    'ref': False,
                    'journal_id': obj.journal_id.id,
                }
            not_project_line = self.env['salary.cost.detail']
            project_line = self.env['salary.cost.detail']
            non_time_line=self.env['salary.cost.line']
            sum_amount = 0
            sum_amount_shi=0
            non_time_wage=0
            non_amount_shi=0
            for line in self.line_ids:
                not_project_line += line.line_ids.filtered(lambda r: not r.project_id)
                project_line += line.line_ids.filtered(lambda r: r.project_id)
                # if line.worked_hour==0:
                #     print('=====-----worked_hour', line.employee_id)
                #     non_time_emp.append(line)
                    # if line.sum_tootsson_salary>0:
                    #     project_emp=self.env['hr.project'].search([('id', '=', line.employee_id.hr_p_id.id)], limit=1)
                    #     debit_line = (0, 0, {
                    #         'name': obj.year + '-' + month + ' ' + u'Цалин'+'testoooooo',
                    #         'date': obj.end_date,
                    #         'partner_id': False,
                    #         'branch_id':False,
                    #         'account_id': project_emp.account_expense_id.id,
                    #         'journal_id': obj.journal_id.id,
                    #         'debit': line.sum_tootsson_salary,
                    #         'credit': 0
                    #     })
                    #     order_line.append(debit_line)
                    # else:
                    #     raise UserError(_('%s төсөлийн  Цалин зардлын данс тохируулна уу.')%(project_id.name))
           
            
            # project-toi dun
            project_obj = project_line.mapped('project_id')
            project_tusul_salary_dict = {}
            project_ndsh_salary_dict = {}
            project_project_wage_dict = {}
            project_project_ndsh_salary_dict = {}
            project_kpi_wage_dict = {}
            project_kpi_ndsh_salary_dict = {}

            for project in project_obj:
                pp_line = project_line.filtered(lambda r: r.project_id.id == project.id)
                lines_zero_hours = [line for line in self.line_ids if line.worked_hour == 0]
                cost_line = [line for line in lines_zero_hours if line.employee_id.hr_p_id.id == project.id]
           
                project_tusul_salary_dict[project.name] = round(sum([line.tusul_salary for line in pp_line]), 2)+round(sum([ll.sum_tootsson_salary for ll in cost_line]), 2)                 
                project_ndsh_salary_dict[project.name] = round(sum([line.ndsh_salary for line in pp_line]), 2)+round(sum([ll.oshi_tootsson for ll in cost_line]), 2)
                project_project_wage_dict[project.name] = round(sum([line.project_wage for line in pp_line]), 2)
                project_project_ndsh_salary_dict[project.name] = round(sum([line.project_ndsh_salary for line in pp_line]), 2)
                project_kpi_wage_dict[project.name] = round(sum([line.kpi_wage for line in pp_line]), 2)
                project_kpi_ndsh_salary_dict[project.name] = round(sum([line.kpi_ndsh_salary for line in pp_line]), 2)
                sum_amount += round(sum([line.tusul_salary for line in pp_line]), 2) + round(sum([line.project_wage for line in pp_line]), 2) + round(sum([line.kpi_wage for line in pp_line]), 2)+round(sum([ll.sum_tootsson_salary for ll in cost_line]), 2)
                sum_amount_shi +=  round(sum([line.ndsh_salary for line in pp_line]), 2)+  round(sum([line.project_ndsh_salary for line in pp_line]), 2) + round(sum([line.kpi_ndsh_salary for line in pp_line]), 2)+round(sum([ll.oshi_tootsson for ll in cost_line]), 2)

            for item in project_tusul_salary_dict:
                project_id = self.env['hr.project'].search([('name', '=', item)], limit=1)
                if project_id.account_expense_id:
                    if project_tusul_salary_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'Цалин' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': project_id.account_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': project_tusul_salary_dict[item],
                            'credit': 0
                        })
                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s төсөлийн  Цалин зардлын данс тохируулна уу.')%(project_id.name))

            for item in project_ndsh_salary_dict:
                project_id = self.env['hr.project'].search([('name', '=', item)], limit=1)
                if project_id.account_shi_expense_id:
                    if project_ndsh_salary_dict[item] >0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'НДШ' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': project_id.account_shi_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': project_ndsh_salary_dict[item],
                            'credit': 0
                        })

                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s төсөлийн  НДШ зардлын данс тохируулна уу.')%(project_id.name))


            for item in project_project_wage_dict:
                project_id = self.env['hr.project'].search([('name', '=', item)], limit=1)
                if project_id.account_expense_id:
                    if project_project_wage_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'Цалин төслийн-ТУ' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': project_id.account_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': project_project_wage_dict[item],
                            'credit': 0
                        })

                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s төсөлийн  ТУ Цалин зардлын данс тохируулна уу.')%(project_id.name))

            for item in project_project_ndsh_salary_dict:
                project_id = self.env['hr.project'].search([('name', '=', item)], limit=1)
                if project_id.account_shi_expense_id.id:
                    if project_project_ndsh_salary_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'НДШ төслийн-ТУ' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': project_id.account_shi_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': project_project_ndsh_salary_dict[item],
                            'credit': 0
                        })

                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s төсөлийн  ТУ НДШ зардлын данс тохируулна уу.')%(project_id.name))
                    
            for item in project_kpi_wage_dict:
                project_id = self.env['hr.project'].search([('name', '=', item)], limit=1)
                if project_id.account_expense_id:
                    if project_kpi_wage_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'Цалин төслийн-KPI' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': project_id.account_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': project_kpi_wage_dict[item],
                            'credit': 0
                        })

                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s төсөлийн  ТУ Цалин зардлын данс тохируулна уу.')%(project_id.name))
            
            for item in project_kpi_ndsh_salary_dict:
                project_id = self.env['hr.project'].search([('name', '=', item)], limit=1)
                if project_id.account_shi_expense_id.id:
                    if project_kpi_ndsh_salary_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'НДШ төслийн-KPI' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': project_id.account_shi_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': project_kpi_ndsh_salary_dict[item],
                            'credit': 0
                        })

                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s төсөлийн  ТУ НДШ зардлын данс тохируулна уу.')%(project_id.name))
               

            # department-tai dun
            department_obj = self.line_ids.mapped('department_id')
            department_tusul_salary_dict = {}
            department_ndsh_salary_dict = {}
            department_project_wage_dict = {}
            department_project_ndsh_salary_dict = {}
            department_kpi_wage_dict = {}
            department_kpi_ndsh_salary_dict = {}

            for department in department_obj:
                dd_line = not_project_line.filtered(lambda r: r.department_id.id == department.id)
                department_tusul_salary_dict[department.name] = round(sum([line.tusul_salary for line in dd_line]), 2)
                department_ndsh_salary_dict[department.name] = round(sum([line.ndsh_salary for line in dd_line]), 2)
                department_project_wage_dict[department.name] = round(sum([line.project_wage for line in dd_line]), 2)
                department_project_ndsh_salary_dict[department.name] = round(sum([line.project_ndsh_salary for line in dd_line]), 2)
                department_kpi_wage_dict[department.name] = round(sum([line.kpi_wage for line in dd_line]), 2)
                department_kpi_ndsh_salary_dict[department.name] = round(sum([line.kpi_ndsh_salary for line in dd_line]), 2)

                sum_amount += round(sum([line.tusul_salary for line in dd_line]), 2)  + round(sum([line.project_wage for line in dd_line]), 2) +round(sum([line.kpi_wage for line in dd_line]), 2)
                sum_amount_shi +=  round(sum([line.ndsh_salary for line in dd_line]), 2)  +round(sum([line.project_ndsh_salary for line in dd_line]), 2) + round(sum([line.kpi_ndsh_salary for line in dd_line]), 2)

            for item in department_tusul_salary_dict:
                department_id = self.env['hr.department'].search([('name','=',item)], limit=1)
                if department_id.account_expense_id:
                    if department_tusul_salary_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'Цалин' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': department_id.account_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': department_tusul_salary_dict[item],
                            'credit': 0
                        })
                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s хэлтэсийн  Цалин зардлын данс тохируулна уу.')%(department_id.name))
               

            for item in department_ndsh_salary_dict:
                department_id = self.env['hr.department'].search([('name','=',item)], limit=1)
                if department_id.account_shi_expense_id:
                    if department_ndsh_salary_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'НДШ' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': department_id.account_shi_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': department_ndsh_salary_dict[item],
                            'credit': 0
                        })
                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s хэлтэсийн  НДШ зардлын данс тохируулна уу.')%(department_id.name))

            for item in department_project_wage_dict:
                department_id = self.env['hr.department'].search([('name','=',item)], limit=1)
                if department_id.account_expense_id:
                    if department_project_wage_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'Цалин ТУ' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': department_id.account_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': department_project_wage_dict[item],
                            'credit': 0
                        })
                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s хэлтэсийн ТУ Цалин зардлын данс тохируулна уу.')%(department_id.name))

            for item in department_project_ndsh_salary_dict:
                department_id = self.env['hr.department'].search([('name','=',item)], limit=1)
                if department_id.account_shi_expense_id:
                    if department_project_ndsh_salary_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'НДШ ТУ' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': department_id.account_shi_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': department_project_ndsh_salary_dict[item],
                            'credit': 0
                        })
                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s хэлтэсийн ТУ НДШ зардлын данс тохируулна уу.')%(department_id.name))

            for item in department_kpi_wage_dict:
                department_id = self.env['hr.department'].search([('name','=',item)], limit=1)
                if department_id.account_expense_id:
                    if department_kpi_wage_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'Цалин KPI' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': department_id.account_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': department_kpi_wage_dict[item],
                            'credit': 0
                        })
                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s хэлтэсийн ТУ Цалин зардлын данс тохируулна уу.')%(department_id.name))


            for item in department_kpi_ndsh_salary_dict:
                department_id = self.env['hr.department'].search([('name','=',item)], limit=1)
                if department_id.account_shi_expense_id:
                    if department_kpi_ndsh_salary_dict[item]>0:
                        debit_line = (0, 0, {
                            'name': obj.year + '-' + month + ' ' + u'НДШ KPI' + ' ' + item,
                            'date': obj.end_date,
                            'partner_id': False,
                            'branch_id':False,
                            'account_id': department_id.account_shi_expense_id.id,
                            'journal_id': obj.journal_id.id,
                            'debit': department_kpi_ndsh_salary_dict[item],
                            'credit': 0
                        })
                        order_line.append(debit_line)
                else:
                    raise UserError(_('%s хэлтэсийн ТУ НДШ зардлын данс тохируулна уу.')%(department_id.name))
                
            # print('=======non_amount_shi_last', non_amount_shi)
            # print('=======non_amount_last', non_time_wage)
            credit_line = (0, 0, {
                'name': 'Цалингийн өглөг',
                'date': obj.end_date,
                'partner_id': False,
                'branch_id':False,
                'account_id': obj.account_payable_id.id,
                'journal_id': obj.journal_id.id,
                'debit': 0,
                'credit': sum_amount+non_time_wage,
            })
            order_line.append(credit_line)

            credit_line = (0, 0, {
                'name': 'НДШ өглөг',
                'date': obj.end_date,
                'partner_id': False,
                'branch_id':False,
                'account_id': obj.account_shi_id.id,
                'journal_id': obj.journal_id.id,
                'debit': 0,
                'credit': sum_amount_shi+non_amount_shi,
            })

            order_line.append(credit_line)
            move.update({'line_ids': order_line})
            move_id = move_pool.create(move)
            self.write({'account_move_id': move_id.id,})

        return True


class SalaryCostLine(models.Model):
    _name = 'salary.cost.line'
    _description = "salary cost Line"

    name = fields.Char(string=u'Нэр', index=True, readonly=True)
    parent_id = fields.Many2one('salary.cost','Parent', ondelete='cascade')
    # date = fields.Date('Огноо')
    employee_id = fields.Many2one('hr.employee','Ажилтан', required=True)
    department_id = fields.Many2one('hr.department','Алба нэгж',related='employee_id.department_id')
    job_id = fields.Many2one('hr.job','Албан тушаал',related='employee_id.job_id')
    work_location = fields.Many2one('hr.work.location', 'Үндсэн байршил', related= 'employee_id.work_location_id')
    sum_tootsson_salary = fields.Float('Нийт тооцсон цалин')
    tootsson_salary = fields.Float('Тооцсон цалин')
    reward_salary = fields.Float('ТУ цалин')
    kpi_salary = fields.Float('KPI цалин')
    free_salary = fields.Float('Сул зогсолтын цалин')
    huwisah_salary = fields.Float('Хувьсах цалин')
    worked_hour = fields.Float('Ажилласан цаг')
    line_ids= fields.One2many('salary.cost.detail', 'parent_id', 'line')
    timetable_line_ids = fields.One2many('hr.timetable.line.line', 'costline_line_id')
    ndsh_tootsson = fields.Float('НДШ дүн',compute="compute_ndsh", store=True)
    pro_ndsh_tootsson = fields.Float('ТУ НДШ дүн', compute="compute_pro_ndsh", store=True)
    kpi_ndsh_tootsson = fields.Float('KPI НДШ дүн', compute="compute_pro_ndsh", store=True)
    oshi_tootsson = fields.Float('АО НДШ дүн')
    bndsh=fields.Float('НДШ хувь')


    @api.depends('bndsh', 'reward_salary')
    def compute_pro_ndsh(self):
        for i in self:
            if i.bndsh and ('|',i.reward_salary, i.kpi_salary):
                i.pro_ndsh_tootsson = i.reward_salary * i.bndsh/100
                i.kpi_ndsh_tootsson = i.kpi_salary * i.bndsh/100
            else:
                i.pro_ndsh_tootsson=0
                i.kpi_ndsh_tootsson=0
    @api.depends('bndsh', 'tootsson_salary' )
    def compute_ndsh(self):
        for i in self:
            if i.bndsh and i.tootsson_salary:
                i.ndsh_tootsson = i.tootsson_salary * i.bndsh/100
            else:
                i.ndsh_tootsson=0

                    
class SalaryCostDetail(models.Model):
    _name= 'salary.cost.detail'
    _description = "salary cost detail"

    parent_id = fields.Many2one('salary.cost.line', 'Parent') 
    # employee_id = fields.Many2one('hr.employee','Ажилтан')
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил', related= 'parent_id.work_location')
    department_id = fields.Many2one('hr.department','Алба нэгж',related='parent_id.department_id')

    worked_hour = fields.Float('Ажилласан цаг')
    project_id = fields.Many2one('hr.project', 'Төсөл')
    tusul_salary = fields.Float('Цалин', compute='compute_tusul_salary', store=True)
    project_wage = fields.Float('ТУ цалин', compute='compute_project_salary', store=True)
    kpi_wage = fields.Float('KPI цалин', compute='compute_kpi_salary', store=True)
    ndsh_salary = fields.Float('НДШ Цалин', compute='compute_ndsh_salary', store=True)
    project_ndsh_salary = fields.Float('НДШ ТУ', compute='compute_pro_ndsh_salary', store=True)
    kpi_ndsh_salary = fields.Float('НДШ KPI', compute='compute_kpi_ndsh_salary', store=True)
    night_hour = fields.Float('Шөнө ажилласан цаг')
    overtime = fields.Float('Илүү цаг')
    busines_trip_hour = fields.Float('Томилолт илүү цаг орохгүй')
    busines_trip_hour2 = fields.Float('Томилолт нийт цаг')
    holiday_worked_hour = fields.Float('Баяр цаг')
    tourist_hour = fields.Float('Аялалын цаг')
    weekend_night = fields.Float('АБ шөнө')
    free_wage_hour = fields.Float('Цалинтай чөлөө')
    sum_time = fields.Float('Нийт төсөлийн цаг', compute = 'compute_project_sum_time', store=True)
    fond_worked_hour = fields.Float('Ажилласан цаг Уурхай Фонд', compute = 'project_sum_fond_time', store=True)
    ub_fond_worked_hour = fields.Float('Ажилласан цаг UB Фонд', compute = 'compute_project_sum_ub_fond_time', store=True)
    uurkhai_ov = fields.Float('Уурхайн ИЦ', compute = 'compute_project_sum_ovu_time', store=True)
    hs_id =fields.Many2one('hr.shift.time', 'Shift time')
    salary_ov_time = fields.Float('Цалин ИЦ')
    wage_over_time = fields.Float('ИЦ/Цалин тооцох/', compute = 'compute_salary_time', store=True)
    z_hour=fields.Float('Зөрүү цаг')

    @api.depends('worked_hour', 'night_hour', 'overtime', 'busines_trip_hour' )
    def project_sum_fond_time(self):
        for i in self:
            if i.work_location_id.id==2:
                hour= (i.worked_hour +i.busines_trip_hour+i.overtime+i.holiday_worked_hour+i.night_hour+i.tourist_hour- i.weekend_night)
                hour1=(i.night_hour + i.holiday_worked_hour+i.overtime)
                zuruu=0
                if hour>=hour1:
                    i.fond_worked_hour=hour-hour1
                else:
                    zuruu=hour-hour1
                    if zuruu<=0:
                        i.fond_worked_hour=0
                    else:
                        i.fond_worked_hour=hour
                # Төсөл нь оффис бөгөөд Уурхайн ажилчид дээр томилолтын цагтай бол шууд томилолтын цагийг авна
                if i.project_id.id == i.parent_id.employee_id.hr_p_id.id and i.busines_trip_hour2>0:
                    i.fond_worked_hour = i.busines_trip_hour2
                
    @api.depends('worked_hour', 'night_hour', 'overtime', 'busines_trip_hour' )
    def compute_project_sum_ub_fond_time(self):
        for i in self:
            if i.work_location_id.id==1:
                if i.project_id.id == i.parent_id.employee_id.hr_p_id.id:
                    # Фонд цаг гаргахын тулд амралтын өдрөөс бусад өдөр ажилласан томилолтын цагийг 8 цагаар тооцож фонд цаг гарна
                    bday = i.busines_trip_hour/11
                    i.ub_fond_worked_hour=(i.worked_hour+(bday*8))+i.z_hour
                    print('\n\n==7777777===',i.parent_id.employee_id.name,i.ub_fond_worked_hour,i.worked_hour,bday,i.z_hour) 
                else:
                    # Нийт цаг гаргахын тулд оффисын цагаас тусдаа төслийн цаг дээр зөвхөн томилолтын цаг орж ирэх ёстой
                    i.ub_fond_worked_hour = i.busines_trip_hour2
                    print('\n\n==6666666===',i.parent_id.employee_id.name,i.ub_fond_worked_hour,i.busines_trip_hour2) 
               

    @api.depends('overtime')
    def compute_project_sum_ovu_time(self):
        for i in self:
            if i.work_location_id.id==2:
                i.uurkhai_ov=i.overtime

    @api.depends('salary_ov_time')
    def compute_salary_time(self):
        for i in self:
            if i.work_location_id.id==1:
                i.wage_over_time=i.salary_ov_time
            
    @api.depends('fond_worked_hour', 'night_hour', 'overtime', 'holiday_worked_hour' )
    def compute_project_sum_time(self):
        for i in self:
            if i.project_id.id == i.parent_id.employee_id.hr_p_id.id:
                # Төсөл нь оффис бөгөөд УБ ажилчид дээр томилолтын цаг тухайн мөрөөс хасагдах ёстой тэгэхгүй бол давхардаж орж ирнэ
                sum = i.holiday_worked_hour+i.ub_fond_worked_hour+i.wage_over_time
                if i.busines_trip_hour2>0 and i.work_location_id.id==1:
                    if i.busines_trip_hour2 <= sum:
                        i.sum_time= sum - i.busines_trip_hour2
                else:
                    i.sum_time=i.night_hour+i.holiday_worked_hour+i.ub_fond_worked_hour+i.fond_worked_hour+i.uurkhai_ov+i.wage_over_time
            else:
                i.sum_time= i.night_hour+i.holiday_worked_hour+i.ub_fond_worked_hour+i.fond_worked_hour+i.uurkhai_ov 
            # print('\n\n==9999999===',i.parent_id.employee_id.name,i.ub_fond_worked_hour,i.fond_worked_hour,i.sum_time,i.busines_trip_hour2)
             



    @api.depends('parent_id.worked_hour', 'sum_time', 'parent_id.tootsson_salary')
    def compute_tusul_salary(self):
        for item in self:
            if item.parent_id.worked_hour and item.parent_id.tootsson_salary and item.sum_time:
                amount = item.parent_id.tootsson_salary/item.parent_id.worked_hour
                item.tusul_salary = amount*item.sum_time
            else:
                item.tusul_salary =0

    @api.depends('sum_time', 'parent_id.reward_salary', 'parent_id.worked_hour' )
    def compute_project_salary(self):
        for item in self:
            if item.parent_id.worked_hour and item.parent_id.reward_salary and item.sum_time:
                amount_pro = item.parent_id.reward_salary/item.parent_id.worked_hour
                item.project_wage = amount_pro*item.sum_time
            else:
                item.project_wage=0

    @api.depends('sum_time', 'parent_id.kpi_salary', 'parent_id.worked_hour' )
    def compute_kpi_salary(self):
        for item in self:
            if item.parent_id.worked_hour and item.parent_id.kpi_salary and item.sum_time:
                amount_pro = item.parent_id.kpi_salary/item.parent_id.worked_hour
                item.kpi_wage = amount_pro*item.sum_time
            else:
                item.kpi_wage=0

    @api.depends('parent_id.worked_hour','parent_id.ndsh_tootsson', 'sum_time')
    def compute_ndsh_salary(self):
        for item in self:
            if item.parent_id.worked_hour and item.parent_id.ndsh_tootsson and item.sum_time:
                item.ndsh_salary = (item.parent_id.ndsh_tootsson/item.parent_id.worked_hour)*item.sum_time
                # item.project_ndsh_salary = (item.parent_id.ndsh_tootsson/item.parent_id.worked_hour)*item.sum_time
            else:
                item.ndsh_salary =0
                # item.project_ndsh_salary =0
    @api.depends('parent_id.worked_hour','sum_time', 'parent_id.pro_ndsh_tootsson' )
    def compute_pro_ndsh_salary(self):
        for item in self:
            if item.parent_id.worked_hour and item.parent_id.pro_ndsh_tootsson and item.sum_time:
                item.project_ndsh_salary = (item.parent_id.pro_ndsh_tootsson/item.parent_id.worked_hour)*item.sum_time
            else:
                item.project_ndsh_salary =0

    @api.depends('parent_id.worked_hour','sum_time', 'parent_id.pro_ndsh_tootsson' )
    def compute_kpi_ndsh_salary(self):
        for item in self:
            if item.parent_id.worked_hour and item.parent_id.kpi_ndsh_tootsson and item.sum_time:
                item.kpi_ndsh_salary = (item.parent_id.kpi_ndsh_tootsson/item.parent_id.worked_hour)*item.sum_time
            else:
                item.kpi_ndsh_salary =0
class ReceivablePayable(models.Model):
    _inherit = "receivable.payable"

    date_invoice = fields.Date(string='Авлага татах огноо')

    def receivable_payable_line(self):
        line_pool =  self.env['receivable.payable.line']
        if self.line_ids:
            self.line_ids.unlink()
        for obj in self:
            employee_lines=self.env['hr.employee'].search([])
            for employee in employee_lines:
                # if employee.partner_id:
                #     query_drug = """SELECT l.partner_id, a.id, SUM(l.debit)-SUM(l.credit) as amount 
                #           FROM account_move_line l  
                #           left join account_move m on l.move_id=m.id 
                #           LEFT JOIN account_account a ON (l.account_id=a.id)
                #           WHERE 
                #           a.is_drug ='t'
                #           AND m.state='posted' 
                #           AND l.partner_id = %s and l.company_id=%s and m.date<='%s' 
                #           GROUP BY l.partner_id, a.id """%(employee.partner_id.id,self.company_id.id,self.end_date)
                #     self.env.cr.execute(query_drug)
                #     records = self.env.cr.dictfetchall()
                #     for rec in records:
                #         if rec['amount']>0:
                #             line_data_id = line_pool.create({
                #                 'department_id' : employee.department_id.id,
                #                 'job_id' : employee.job_id.id,
                #                 'employee_id' : employee.id,
                #                 'med_receivable' : rec['amount'],
                #                 'parent_id': obj.id,
                #             })

                partner=self.env['res.partner'].search([('id','=',employee.partner_id.id)])
                # if partner:
                if partner.receivable_payable>0 or partner.mobile_receivable>0 or partner.clotes_receivable>0 or partner.payment_receivable>0:
                    line_data_id = line_pool.create({
                        'department_id' : employee.department_id.id,
                        'job_id' : employee.job_id.id,
                        'employee_id' : employee.id,
                        'receivable_payable' : partner.receivable_payable,
                        'mobile_payable' : partner.mobile_receivable,
                        'clothes_payable' : partner.clotes_receivable,
                        'payment_payable' : partner.payment_receivable,
                        'parent_id': obj.id,
                    })
class ReceivablePayableline(models.Model):
    _inherit = "receivable.payable.line"

    mobile_payable= fields.Float('Утасны авлага', digits=(3, 2))
    clothes_payable= fields.Float('Хувцасны авлага', digits=(3, 2))
    payment_payable= fields.Float('Автомашины торгууль', digits=(3, 2))

    

   
