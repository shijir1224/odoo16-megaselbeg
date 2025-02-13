# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models
from odoo.tools.misc import get_lang


class PittGrewNewReport(models.TransientModel):
    _name = "pit.grew.new.report"  

    company_id= fields.Many2one('res.company', "Компани",required=True)
    year= fields.Char(method=True, store=True, type='char', string='Жил', size=8)
    s_month=fields.Selection([('1','January'), ('2','February'), ('3','March'), ('4','April'),
            ('5','May'), ('6','June'), ('7','July'), ('8','August'), ('9','September'),
            ('90','October'), ('91','November'), ('92','December')], u'Эхлэх сар')
    e_month=fields.Selection([('1','January'), ('2','February'), ('3','March'), ('4','April'),
            ('5','May'), ('6','June'), ('7','July'), ('8','August'), ('9','September'),
            ('90','October'), ('91','November'), ('92','December')], u'Дуусах сар')
    work_location_id = fields.Many2one('hr.work.location', 'Ажлын байршил')
    department_id = fields.Many2one('hr.department','Хэлтэс')

    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet(u'ХХОАТ тайлан')

        file_name = 'ХХОАТ тайлан'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=1)
        # theader.set_bg_color('#6495ED')

        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(10)
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        theader2 = workbook.add_format({'bold': 1})
        theader2.set_font_size(9)
        theader2.set_font('Times new roman')
        theader2.set_align('right')
        theader2.set_align('vcenter')

        theader3 = workbook.add_format({'bold': 1})
        theader3.set_font_size(9)
        theader3.set_font('Times new roman')
        theader3.set_align('left')
        theader3.set_align('vcenter')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_font('Times new roman')
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#A8C3F4')

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
        footer.set_bg_color('#6495ED')
        footer.set_num_format('#,##0.00')

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_font('Times new roman')
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_num_format('#,##0.00')

        contest_right_red = workbook.add_format()
        contest_right_red.set_text_wrap()
        contest_right_red.set_font_size(9)
        contest_right_red.set_font('Times new roman')
        contest_right_red.set_align('right')
        contest_right_red.set_align('vcenter')
        contest_right_red.set_font_color('red')
        contest_right_red.set_num_format('#,##0.00')

        contest_right_green = workbook.add_format()
        contest_right_green.set_text_wrap()
        contest_right_green.set_font_size(9)
        contest_right_green.set_align('right')
        contest_right_green.set_align('vcenter')
        contest_right_green.set_font_color('green')
        contest_right_green.set_num_format('#,##0.00')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_font('Times new roman')
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)

        contest_left0 = workbook.add_format()
        contest_left0.set_font_size(9)
        contest_left0.set_align('left')
        contest_left0.set_align('vcenter')

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_font('Times new roman')
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)

        categ_name = workbook.add_format({'bold': 1})
        categ_name.set_font_size(9)
        categ_name.set_align('left')
        categ_name.set_align('vcenter')
        categ_name.set_border(style=1)
        categ_name.set_bg_color('#B9CFF7')

        categ_right = workbook.add_format({'bold': 1})
        categ_right.set_font_size(9)
        categ_right.set_align('right')
        categ_right.set_align('vcenter')
        categ_right.set_border(style=1)
        categ_right.set_bg_color('#B9CFF7')
        categ_right.set_num_format('#,##0.00')

        rowx=0
        sheet.write(rowx, 0, u'ТИН дугаар', theader),
        sheet.write(rowx, 1, u'Овог', theader),
        sheet.write(rowx,2, u'Нэр', theader),
        sheet.write(rowx,3, u'Хуулийн 7.1.1', theader),
        sheet.write(rowx,4, u'Хуулийн 7.1.2, 7.1.3, 7.1.4, 7.1.5, 7.1.7', theader),
        sheet.write(rowx,5, u'Хуулийн 7.1.6', theader),
        sheet.write(rowx,6, u'Нийт (1+2+3)', theader),
        sheet.write(rowx,7, u'ЭМД, НДШ Хувь', theader),
        sheet.write(rowx,8, u'ЭМД, НДШ Дүн (Хуулийн 7,1,1-5, 7,1,7)', theader),
        sheet.write(rowx,9, u'ЭМД, НДШ Дүн (Хуулийн 7,1,6)', theader),
        sheet.write(rowx,10, u'Хуулийн 7.1-д заасан орлогод татвар ногдуулах орлого (4-6-7)', theader),
        sheet.write(rowx,11, u'Орлогын төрөл', theader),
        sheet.write(rowx,12, u'Орлого', theader),
        sheet.write(rowx,13, u'Нийт татвар ногдуулах орлого', theader),
        sheet.write(rowx,14, u'Шатлал', theader),
        sheet.write(rowx,15, u'Хуулийн 7.1.1, 7.1.5, 7.1.7-д заасан орлогод Ногдуулсан татвар', theader),
        sheet.write(rowx,16, u'Орлого хүлээн авсан сарын тоо /ажилласан сар/', theader),
        sheet.write(rowx,17, u'Хуулийн 23.1-т заасан хөнгөлөлт сард ногдох', theader),
        sheet.write(rowx,18, u'Хуулийн 23.1-т заасан хөнгөлөлт нийт', theader),
        sheet.write(rowx,19, u'Хуулийн 7,1-д заасан орлогод ногдуулсан Хөнгөлөлтийн дараах татварын дүн', theader),
        sheet.write(rowx,20, u'Хуулийн 7.1.6-д заасан орлогод ногдуулсан дүн', theader),
        sheet.write(rowx,21, u'Шууд бус орлогод ногдуулсан албан татвар', theader),
        sheet.write(rowx,22, u'Нийт суутгуулсан албан татварын дүн', theader),

        rowx+=1
        
        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 15)
        sheet.set_column('C:C', 15)
        sheet.set_column('D:D', 20)
        sheet.set_column('K:K', 15)
        sheet.set_column('E:T', 11)
        lang = self.env.user.lang or get_lang(self.env).code

        if self.work_location_id:
            if self.department_id:
                query="""SELECT 
                    COALESCE(he.name->> '%s', he.name->>'en_US') as name, 
                    --he.name as name,
                    he.last_name as last_name,
                    he.passport_id as register,
                    he.ttd_number as ttd_number,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PITDIS')) as dis,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SHI')) as shi,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PIT')) as pit,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='TOOTS')) as amount_tootsson,
                    count(he.id) as hr_id,
                    he.id as emp_id
       
                    FROM salary_order so
                    LEFT JOIN salary_order_line line ON line.order_id=so.id
                    LEFT JOIN hr_employee he ON he.id=line.employee_id
                    LEFT JOIN hr_department hd ON he.department_id=hd.id
                    LEFT JOIN hr_job hj ON hj.id=he.job_id
                    --LEFT JOIN hr_contract hc ON hc.employee_id=he.id
                    --LEFT JOIN insured_type it ON hc.insured_type_id=it.id
                    WHERE so.type='final' and so.month>='%s' and so.month<='%s'  and so.year='%s' and so.work_location_id=%s and he.department_id=%s so.state='done'
                    GROUP BY emp_id, he.name,he.last_name,he.passport_id,he.ttd_number"""%(lang,self.s_month,self.e_month,self.year,self.work_location_id.id,self.department_id.id)
                self.env.cr.execute(query)
                records = self.env.cr.dictfetchall()
            else:
                query="""SELECT 
                    COALESCE(he.name->> '%s', he.name->>'en_US') as name, 
                    --he.name as name,
                    he.last_name as last_name,
                    he.passport_id as register,
                    he.ttd_number as ttd_number,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PITDIS')) as dis,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SHI')) as shi,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PIT')) as pit,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='TOOTS')) as amount_tootsson,
                    count(he.id) as hr_id,
                    he.id as emp_id
                    --it.id as it_id
                    FROM salary_order so
                    LEFT JOIN salary_order_line line ON line.order_id=so.id
                    LEFT JOIN hr_employee he ON he.id=line.employee_id
                    LEFT JOIN hr_department hd ON he.department_id=hd.id
                    LEFT JOIN hr_job hj ON hj.id=he.job_id
                    --LEFT JOIN hr_contract hc ON hc.employee_id=he.id
                    --LEFT JOIN insured_type it ON hc.insured_type_id=it.id
                    WHERE so.type='final' and so.month>='%s' and so.month<='%s'  and so.year='%s' and so.work_location_id=%s and so.state='done'
                    GROUP BY emp_id, he.name,he.last_name,he.passport_id,he.ttd_number"""%(lang,self.s_month,self.e_month,self.year,self.work_location_id.id)
                self.env.cr.execute(query)
                records = self.env.cr.dictfetchall()
        else:
            if self.department_id:
                query="""SELECT  
                    COALESCE(he.name->> '%s', he.name->>'en_US') as name, 
                    --he.name as name,
                    he.last_name as last_name,
                    he.passport_id as register,
                    he.ttd_number as ttd_number,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PITDIS')) as dis,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SHI')) as shi,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PIT')) as pit,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='TOOTS')) as amount_tootsson,
                    count(he.id) as hr_id,
                    he.id as emp_id
                    --it.id as it_id
                    FROM salary_order so
                    LEFT JOIN salary_order_line line ON line.order_id=so.id
                    LEFT JOIN hr_employee he ON he.id=line.employee_id
                    LEFT JOIN hr_department hd ON he.department_id=hd.id
                    LEFT JOIN hr_job hj ON hj.id=he.job_id
                    --LEFT JOIN hr_contract hc ON hc.employee_id=he.id
                    --LEFT JOIN insured_type it ON hc.insured_type_id=it.id
                    WHERE so.type='final' and so.month>='%s' and so.month<='%s'  and so.year='%s' and he.department_id=%s
                    GROUP BY emp_id, he.name,he.last_name,he.passport_id,he.ttd_number"""%(lang,self.s_month,self.e_month,self.year,self.department_id.id)
                self.env.cr.execute(query)
                records = self.env.cr.dictfetchall()
            else:
                query="""SELECT  
                    COALESCE(he.name->> '%s', he.name->>'en_US') as name, 
                    --he.name as name,
                    he.last_name as last_name,
                    he.passport_id as register,
                    he.ttd_number as ttd_number,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PITDIS')) as dis,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SHI')) as shi,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PIT')) as pit,
                    sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='TOOTS')) as amount_tootsson,
                    count(he.id) as hr_id,
                    he.id as emp_id
                    --it.id as it_id
                    FROM salary_order so
                    LEFT JOIN salary_order_line line ON line.order_id=so.id
                    LEFT JOIN hr_employee he ON he.id=line.employee_id
                    LEFT JOIN hr_department hd ON he.department_id=hd.id
                    LEFT JOIN hr_job hj ON hj.id=he.job_id
                    --LEFT JOIN hr_contract hc ON hc.employee_id=he.id
                    --LEFT JOIN insured_type it ON hc.insured_type_id=it.id
                    WHERE so.type='final' and so.month>='%s' and so.month<='%s'  and so.year='%s' and so.state='done'
                    GROUP BY emp_id, he.name,he.last_name,he.passport_id,he.ttd_number"""%(lang,self.s_month,self.e_month,self.year)
                self.env.cr.execute(query)
                records = self.env.cr.dictfetchall()
        # rowx+=1
        pay=0
        hungulult=0
        l=0
        for record in records:
            # pay=record[5]-record[5]*0.115
            # hhoat=(record[5]-record[5]*0.115)*0.1
            hc_id = self.env['hr.contract'].search([('employee_id','=',record['emp_id']),('active','=',True)],limit=1)
            # it_pool = self.env['insured.type'].search([('id','=',record['it_id'])],limit=1)
            sheet.write(rowx, 0,record['ttd_number'],contest_left)
            sheet.write(rowx, 1,record['last_name'],contest_left)
            sheet.write(rowx, 2,record['name'],contest_left)
            sheet.write(rowx, 3,round(record['amount_tootsson']),contest_right)
            sheet.write(rowx, 4,'0',contest_right)
            sheet.write(rowx, 5,'0',contest_right)
            sheet.write(rowx, 6,round(record['amount_tootsson']),contest_right)
            sheet.write(rowx, 7,hc_id.insured_type_id.shi_procent,contest_right)
            sheet.write(rowx, 8,round(record['shi']),contest_right)
            sheet.write(rowx, 9,'0',contest_right)
            sheet.write(rowx, 10,round(record['amount_tootsson']-record['shi']),contest_right)
            sheet.write(rowx, 11,'0',contest_right)
            sheet.write(rowx, 12,'0',contest_right)
            sheet.write(rowx, 13,round(record['amount_tootsson']-record['shi']),contest_right)
            sheet.write(rowx, 14,'0',contest_right)
            sheet.write(rowx, 15,record['pit']+record['dis'],contest_right)
            sheet.write(rowx, 16,int(record['hr_id']),contest_right)
            sheet.write(rowx, 17,'999',contest_right)
            sheet.write(rowx, 18,record['dis'],contest_right)
            sheet.write(rowx, 19,record['pit'],contest_right)
            sheet.write(rowx, 20,'0',contest_right)
            sheet.write(rowx, 21,'0',contest_right)
            sheet.write(rowx, 22,record['pit'],contest_right)
            rowx+=1

        
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

