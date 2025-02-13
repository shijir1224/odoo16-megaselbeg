# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
try:
    # Python 2 support
    from base64 import encodestring
except ImportError:
    # Python 3.9.0+ support
    from base64 import encodebytes as encodestring
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models

class SalaryReport(models.TransientModel):
    _name = "salary.report"  


    salary_id= fields.Many2one('salary.order', 'Salary')
    type= fields.Selection([('all',u'Бүгд'),('working',u'Үндсэн ажилтан'),('experiment',u'Түр ажилтан')],'Ажилтны төлөв')

    
    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        # body = Element()

        sheet = workbook.add_worksheet(u'Salary report')
        worksheet_other = workbook.add_worksheet(u'Other info')

        file_name = 'Salary'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({'bold': 1})
        theader.set_font_size(9)
        theader.set_text_wrap()
        theader.set_font('Times new roman')
        theader.set_align('center')
        theader.set_align('vcenter')
        theader.set_border(style=4)
        theader.set_bg_color('#d9d9d9')

        theader1 = workbook.add_format({'bold': 1})
        theader1.set_font_size(9)
        theader1.set_text_wrap()
        theader1.set_font('Times new roman')
        theader1.set_align('center')
        theader1.set_align('vcenter')

        theader2 = workbook.add_format({})
        theader2.set_font_size(9)
        theader2.set_text_wrap()
        theader2.set_font('Times new roman')
        theader2.set_align('center')
        theader2.set_align('vcenter')

        theader3 = workbook.add_format({})
        theader3.set_font_size(9)
        theader3.set_text_wrap()
        theader3.set_font('Times new roman')
        theader3.set_align('center')
        theader3.set_align('vcenter')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_font('Times new roman')
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#d9d9d9')
        header.set_num_format('#,##0.00')

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
        contest_right.set_border(style=4)
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
        contest_left.set_border(style=4)

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
        months=0
        save_row=9
        if self.salary_id.month==1:
            months=1
        elif self.salary_id.month==2:
            months=2
        elif self.salary_id.month==3:
            months=3
        elif self.salary_id.month==4:
            months=4
        elif self.salary_id.month==5:
            months=5
        elif self.salary_id.month==6:
            months=6
        elif self.salary_id.month==7:
            months=7
        elif self.salary_id.month==8:
            months=9
        elif self.salary_id.month==9:
            months=9
        elif self.salary_id.month==90:
            months=10
        elif self.salary_id.month==91:
            months=11
        elif self.salary_id.month==92:
            months=12

        rowx=5

        sheet.merge_range(rowx, 0,rowx+2,0, u'Д/д', theader),
        sheet.merge_range(rowx,1,rowx+2,1, u'Албан тушаал', theader),
        sheet.merge_range(rowx,2,rowx+2,2, u'Овог', theader),
        sheet.merge_range(rowx,3,rowx+2,3, u'Нэр', theader),
        sheet.merge_range(rowx,4,rowx+2,4, u'РД', theader),
        sheet.merge_range(rowx,5,rowx+2,5, u'Банк', theader),
        sheet.merge_range(rowx,6,rowx+2,6, u'Данс', theader),
        sheet.merge_range(rowx,7,rowx+2,7, u'Ажилд томилогдсон огноо', theader),
        sheet.merge_range(rowx,8,rowx,9, u'Ажиллавал зохих', theader),
        sheet.merge_range(rowx+1,8,rowx+2,8, u'Хо', theader),
        sheet.merge_range(rowx+1,9,rowx+2,9, u'Цаг', theader),
        sheet.merge_range(rowx,10,rowx,11, u'Ажилласан', theader),
        sheet.merge_range(rowx+1,10,rowx+2,10, u'Хо', theader),
        sheet.merge_range(rowx+1,11,rowx+2,11, u'Цаг', theader),
        sheet.merge_range(rowx,12,rowx+2,12, u'Үндсэн цалин', theader),
        sheet.merge_range(rowx,13,rowx+2,13, u'Олговол зохих цалин', theader),
        sheet.merge_range(rowx,14,rowx+2,14, u'Цалингийн зөрүү', theader),
        sheet.merge_range(rowx,15,rowx+2,15, u'Урамшуулал', theader),
        sheet.merge_range(rowx,16,rowx+2,16, u'Ээлжийн амралт', theader),
        sheet.merge_range(rowx,17,rowx+2,17, u'Бусад нэмэгдэл', theader),
        sheet.merge_range(rowx,18,rowx+2,18, u'Нийт цалин ', theader),
        sheet.merge_range(rowx,19,rowx,22, u'Нийт цалин ', theader),
        sheet.merge_range(rowx+1,19,rowx+2,19, u' НД шимтгэл', theader),
        sheet.merge_range(rowx+1,20,rowx+2,20, u' НДЗ ', theader),
        sheet.merge_range(rowx+1,21,rowx+2,21, u' Ашиг тооцох дүн ', theader),
        sheet.merge_range(rowx+1,22,rowx+2,22, u' ХХОАТ ', theader),
        sheet.merge_range(rowx,23,rowx+2,23, u' Урьдчилгаа цалин ', theader),
        sheet.merge_range(rowx,24,rowx,26, u' Бусад суутгал ', theader),
        sheet.merge_range(rowx+1,24,rowx+2,24, u'  Бэлэн авсан урьдчилгаа  ', theader),
        sheet.merge_range(rowx+1,25,rowx+2,25, u' Авлага ', theader),
        sheet.merge_range(rowx+1,26,rowx+2,26, u' Ярианы төлбөр ', theader),
        sheet.merge_range(rowx,27,rowx+2,27, u'  Нийт суутгал ', theader),
        sheet.merge_range(rowx,28,rowx+2,28, u'  2022 оны татварын хөнгөлөлт ', theader),
        sheet.merge_range(rowx,29,rowx+2,29, u'  Гарт олгох нь ', theader),
                        
        
        sheet.freeze_panes(8, 6)
            
        n=1
        rowx+=3
        if self.salary_id.type=='advance':
            sheet.set_column('A:A', 4)
            sheet.set_column('B:B', 15)
            sheet.set_column('C:C', 15)
            sheet.set_column('D:D', 10)
            sheet.set_column('E:E', 10)
            sheet.set_column('F:F', 9)
            sheet.set_column('P:P', 15)
            sheet.merge_range(rowx-8,0,rowx-8,3, u'Компанийн нэр:'+ ' ' + self.salary_id.company_id.name, theader2),
            sheet.merge_range(rowx-6,0,rowx-6,12, self.salary_id.year + ' ' + u' ОНЫ' + ' ' + self.salary_id.month + ' ' +u' САРЫН УРЬДЧИЛГАА ЦАЛИНГИЙН ХҮСНЭГТ', theader1),
            sheet.merge_range(rowx-4,9,rowx-4,10, u'Тайлан хэвлэсэн огноо:', theader2),
            sheet.merge_range(rowx-4,11,rowx-4,12, time.strftime('%Y-%m-%d'), theader2),

            query="""SELECT
                he.name as hr_name,
                he.last_name as last_name,
                sum(bal.day_to_work) as day_to_work,
                sum(bal.hour_to_work) as hour_to_work,
                sum(bal.worked_day) as worked_day,
                sum(bal.worked_hour) as worked_hour,
                hj.name as hj_name,
                line.basic as basic,
                he.identification_id as identification_id,
                sum(line.amount_tootsson) as amount_tootsson,
                sum(line.amount_net) as amount_net,
                sum(line.amount_deduction) as amount_deduction,
                he.id as hr_id,
                he.passport_id as passport_id,
                sum(line.bndsh) as bndsh,
                he.engagement_in_company as engagement_in_company,
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=1)) as urid, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=3)) as othu,
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=2)) as sooau, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=4)) as shiu, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=5)) as pittu , 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=6)) as pitu, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=7)) as suuu
                FROM salary_order so
                LEFT JOIN salary_order_line line ON line.order_id=so.id
                LEFT JOIN hour_balance_line bal ON bal.order_balance_line_id=line.id
                LEFT JOIN hr_employee he ON he.id=line.employee_id
                LEFT JOIN hr_department rb ON rb.id=bal.department_id
                LEFT JOIN hr_job hj ON hj.id=bal.job_id
                WHERE so.id=%s
                GROUP BY he.id,hj.name,line.basic,he.engagement_in_company,he.passport_id"""%(self.salary_id.id)
            self.env.cr.execute(query)
            records = self.env.cr.dictfetchall()
            for record in records:
                sheet.write(rowx, 0, n,contest_left)
                sheet.write(rowx, 1,record['hj_name'],contest_left)
                sheet.write(rowx, 2,record['last_name'],contest_left)
                sheet.write(rowx, 3,record['hr_name'],contest_left)
                sheet.write(rowx, 4,record['passport_id'],contest_left)
                sheet.write(rowx, 5,'',contest_right)
                sheet.write(rowx, 6,'',contest_right)
                sheet.write(rowx, 7, str(record['engagement_in_company']),contest_right)
                sheet.write(rowx, 8,record['day_to_work'],contest_right)
                sheet.write(rowx, 9,record['hour_to_work'],contest_right)
                sheet.write(rowx, 10,record['worked_day'],contest_right)
                sheet.write(rowx, 11,record['worked_hour'],contest_right)
                sheet.write(rowx, 12,record['basic'],contest_right)
                sheet.write(rowx, 13,record['urid'],contest_right)
                sheet.write(rowx, 14,'',contest_right)
                sheet.write(rowx, 15,'',contest_right)
                sheet.write(rowx, 16,record['sooau'],contest_right)
                sheet.write(rowx, 17,record['othu'],contest_right)
                sheet.write(rowx, 18,record['amount_tootsson'],contest_right)
                sheet.write(rowx, 19,record['shiu'],contest_right)
                sheet.write(rowx, 20,record['bndsh'],contest_right)
                sheet.write(rowx, 21,record['amount_tootsson']-record['shiu'],contest_right)
                sheet.write(rowx, 22,record['pitu'],contest_right)
                sheet.write(rowx, 23,'',contest_right)
                sheet.write(rowx, 24,'',contest_right)
                sheet.write(rowx, 25,record['suuu'],contest_right)
                sheet.write(rowx, 26,'',contest_right)
                sheet.write(rowx, 27,record['amount_deduction'],contest_right)
                sheet.write(rowx, 28,record['pittu'],contest_right)
                sheet.write(rowx, 29,record['amount_net'],contest_right)
                # sheet.write_formula(rowx, 12,'{=('+self._symbol(rowx, 8)+'-'+self._symbol(rowx, 11)+')}',contest_right)
                rowx+=1
                n+=1
            sheet.merge_range(rowx,0,rowx,7, u"Нийт", header)
            sheet.write_formula(rowx, 8, '{=SUM('+self._symbol(save_row-1, 8) +':'+ self._symbol(rowx-1, 8)+')}', header)
            sheet.write_formula(rowx, 9, '{=SUM('+self._symbol(save_row-1, 9) +':'+ self._symbol(rowx-1, 9)+')}', header)
            sheet.write_formula(rowx, 10, '{=SUM('+self._symbol(save_row-1, 10) +':'+ self._symbol(rowx-1, 10)+')}', header)
            sheet.write_formula(rowx, 11, '{=SUM('+self._symbol(save_row-1, 11) +':'+ self._symbol(rowx-1, 11)+')}', header)
            sheet.write_formula(rowx, 12, '{=SUM('+self._symbol(save_row-1, 12) +':'+ self._symbol(rowx-1, 12)+')}', header)
            sheet.write_formula(rowx, 13, '{=SUM('+self._symbol(save_row-1, 13) +':'+ self._symbol(rowx-1, 13)+')}', header)
            sheet.write_formula(rowx, 14, '{=SUM('+self._symbol(save_row-1, 14) +':'+ self._symbol(rowx-1, 14)+')}', header)
            sheet.write_formula(rowx, 15, '{=SUM('+self._symbol(save_row-1, 15) +':'+ self._symbol(rowx-1, 15)+')}', header)
            sheet.write_formula(rowx, 16, '{=SUM('+self._symbol(save_row-1, 16) +':'+ self._symbol(rowx-1, 16)+')}', header)
            sheet.write_formula(rowx, 17, '{=SUM('+self._symbol(save_row-1, 17) +':'+ self._symbol(rowx-1, 17)+')}', header)
            sheet.write_formula(rowx, 18, '{=SUM('+self._symbol(save_row-1, 18) +':'+ self._symbol(rowx-1, 18)+')}', header)
            sheet.write_formula(rowx, 19, '{=SUM('+self._symbol(save_row-1, 19) +':'+ self._symbol(rowx-1, 19)+')}', header)
            sheet.write_formula(rowx, 20, '{=SUM('+self._symbol(save_row-1, 20) +':'+ self._symbol(rowx-1, 20)+')}', header)
            sheet.write_formula(rowx, 21, '{=SUM('+self._symbol(save_row-1, 21) +':'+ self._symbol(rowx-1, 21)+')}', header)
            sheet.write_formula(rowx, 22, '{=SUM('+self._symbol(save_row-1, 22) +':'+ self._symbol(rowx-1, 22)+')}', header)
            sheet.write_formula(rowx, 23, '{=SUM('+self._symbol(save_row-1, 23) +':'+ self._symbol(rowx-1, 23)+')}', header)
            sheet.write_formula(rowx, 24, '{=SUM('+self._symbol(save_row-1, 24) +':'+ self._symbol(rowx-1, 24)+')}', header)
            sheet.write_formula(rowx, 25, '{=SUM('+self._symbol(save_row-1, 25) +':'+ self._symbol(rowx-1, 25)+')}', header)
            sheet.write_formula(rowx, 26, '{=SUM('+self._symbol(save_row-1, 26) +':'+ self._symbol(rowx-1, 26)+')}', header)
            sheet.write_formula(rowx, 27, '{=SUM('+self._symbol(save_row-1, 27) +':'+ self._symbol(rowx-1, 27)+')}', header)
            sheet.write_formula(rowx, 28, '{=SUM('+self._symbol(save_row-1, 28) +':'+ self._symbol(rowx-1, 28)+')}', header)
            sheet.write_formula(rowx, 29, '{=SUM('+self._symbol(save_row-1, 29) +':'+ self._symbol(rowx-1, 29)+')}', header)
        elif self.salary_id.type=='final':
            sheet.set_column('A:A', 4)
            sheet.set_column('B:B', 25)
            sheet.set_column('C:C', 15)
            sheet.set_column('D:D', 10)
            sheet.set_column('E:E', 10)
            month_att=self.salary_id.month
            if month_att=='1':
                month_att='01'
            if month_att=='2':
                month_att='02'
            if month_att=='3':
                month_att='03'
            if month_att=='4':
                month_att='04'
            if month_att=='5':
                month_att='05'
            if month_att=='6':
                month_att='06'
            if month_att=='7':
                month_att='07'
            if month_att=='8':
                month_att='08'
            if month_att=='9':
                month_att='09'
            if month_att=='90':
                month_att='10'
            if month_att=='91':
                month_att='11'
            if month_att=='92':
                month_att='12'
            sheet.merge_range(rowx-8,0,rowx-8,3, u'Компанийн нэр:'+ ' ' + self.salary_id.company_id.name, theader3),
            sheet.merge_range(rowx-6,0,rowx-6,22, self.salary_id.year + ' ' + u' ОНЫ' + ' ' + month_att + ' ' +u' САРЫН СҮҮЛ ЦАЛИНГИЙН ХҮСНЭГТ', theader1),
            sheet.merge_range(rowx-4,18,rowx-4,20, u'Тайлан хэвлэсэн огноо:', theader2),
            sheet.merge_range(rowx-4,21,rowx-4,22, time.strftime('%Y-%m-%d'), theader3),
            query="""SELECT
                he.name as hr_name,
                he.last_name as last_name,
                sum(bal.day_to_work) as day_to_work,
                sum(bal.hour_to_work) as hour_to_work,
                sum(bal.worked_day) as worked_day,
                sum(bal.worked_hour) as worked_hour,
                hj.name as hj_name,
                line.basic as basic,
                he.identification_id as identification_id,
                sum(line.amount_tootsson) as amount_tootsson,
                sum(line.amount_net) as amount_net,
                sum(line.amount_deduction) as amount_deduction,
                he.id as hr_id,
                he.passport_id as passport_id,
                he.engagement_in_company as engagement_in_company,
                sum(line.bndsh) as bndsh,
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=8)) as bod,
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=9)) as zuruu,
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=10)) as uram, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=12)) as oth,
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=11)) as sooa, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=13)) as shi, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=14)) as pitt , 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=15)) as pit, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=16)) as urid_suu,
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=17)) as busuu,
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=18)) as suutgal, 
                sum((select coalesce(sum(amount),0) from salary_order_line_line where order_line_id1=line.id and category_id=19)) as phone
                FROM salary_order so
                LEFT JOIN salary_order_line line ON line.order_id=so.id
                LEFT JOIN hour_balance_line bal ON bal.order_balance_line_id=line.id
                LEFT JOIN hr_employee he ON he.id=line.employee_id
                LEFT JOIN hr_department rb ON rb.id=bal.department_id
                LEFT JOIN hr_job hj ON hj.id=bal.job_id
                WHERE so.id=%s
                GROUP BY he.id,hj.name,line.basic,he.engagement_in_company"""%(self.salary_id.id)
            self.env.cr.execute(query)
            records = self.env.cr.dictfetchall()
            for record in records:
                sheet.write(rowx, 0, n,contest_left)
                sheet.write(rowx, 1,record['hj_name'],contest_left)
                sheet.write(rowx, 2,record['last_name'],contest_left)
                sheet.write(rowx, 3,record['hr_name'],contest_left)
                sheet.write(rowx, 4,record['passport_id'],contest_left)
                sheet.write(rowx, 5,'',contest_right)
                sheet.write(rowx, 6,'',contest_right)
                sheet.write(rowx, 7,str(record['engagement_in_company']),contest_right)
                sheet.write(rowx, 8,record['day_to_work'],contest_right)
                sheet.write(rowx, 9,record['hour_to_work'],contest_right)
                sheet.write(rowx, 10,record['worked_day'],contest_right)
                sheet.write(rowx, 11,record['worked_hour'],contest_right)
                sheet.write(rowx, 12,record['basic'],contest_right)
                sheet.write(rowx, 13,record['bod'],contest_right)
                sheet.write(rowx, 14,record['zuruu'],contest_right)
                sheet.write(rowx, 15,record['uram'],contest_right)
                sheet.write(rowx, 16,record['sooa'],contest_right)
                sheet.write(rowx, 17,record['oth'],contest_right)
                sheet.write(rowx, 18,record['amount_tootsson'],contest_right)
                sheet.write(rowx, 19,record['shi'],contest_right)
                sheet.write(rowx, 20,record['bndsh'],contest_right)
                sheet.write(rowx, 21,record['amount_tootsson']-record['shi'],contest_right)
                sheet.write(rowx, 22,record['pit'],contest_right)
                sheet.write(rowx, 23,record['urid_suu'],contest_right)
                sheet.write(rowx, 24,record['busuu'],contest_right)
                sheet.write(rowx, 25,record['suutgal'],contest_right)
                sheet.write(rowx, 26,record['phone'],contest_right)
                sheet.write(rowx, 27,record['amount_deduction'],contest_right)
                sheet.write(rowx, 28,record['pitt'],contest_right)
                sheet.write(rowx, 29,record['amount_net'],contest_right)
                # sheet.write_formula(rowx, 12,'{=('+self._symbol(rowx, 8)+'-'+self._symbol(rowx, 11)+')}',contest_right)
                rowx+=1
                n+=1
            sheet.merge_range(rowx,0,rowx,7, u"Нийт", header)
            sheet.write_formula(rowx, 8, '{=SUM('+self._symbol(save_row-1, 8) +':'+ self._symbol(rowx-1, 8)+')}', header)
            sheet.write_formula(rowx, 9, '{=SUM('+self._symbol(save_row-1, 9) +':'+ self._symbol(rowx-1, 9)+')}', header)
            sheet.write_formula(rowx, 10, '{=SUM('+self._symbol(save_row-1, 10) +':'+ self._symbol(rowx-1, 10)+')}', header)
            sheet.write_formula(rowx, 11, '{=SUM('+self._symbol(save_row-1, 11) +':'+ self._symbol(rowx-1, 11)+')}', header)
            sheet.write_formula(rowx, 12, '{=SUM('+self._symbol(save_row-1, 12) +':'+ self._symbol(rowx-1, 12)+')}', header)
            sheet.write_formula(rowx, 13, '{=SUM('+self._symbol(save_row-1, 13) +':'+ self._symbol(rowx-1, 13)+')}', header)
            sheet.write_formula(rowx, 14, '{=SUM('+self._symbol(save_row-1, 14) +':'+ self._symbol(rowx-1, 14)+')}', header)
            sheet.write_formula(rowx, 15, '{=SUM('+self._symbol(save_row-1, 15) +':'+ self._symbol(rowx-1, 15)+')}', header)
            sheet.write_formula(rowx, 16, '{=SUM('+self._symbol(save_row-1, 16) +':'+ self._symbol(rowx-1, 16)+')}', header)
            sheet.write_formula(rowx, 17, '{=SUM('+self._symbol(save_row-1, 17) +':'+ self._symbol(rowx-1, 17)+')}', header)
            sheet.write_formula(rowx, 18, '{=SUM('+self._symbol(save_row-1, 18) +':'+ self._symbol(rowx-1, 18)+')}', header)
            sheet.write_formula(rowx, 19, '{=SUM('+self._symbol(save_row-1, 19) +':'+ self._symbol(rowx-1, 19)+')}', header)
            sheet.write_formula(rowx, 20, '{=SUM('+self._symbol(save_row-1, 20) +':'+ self._symbol(rowx-1, 20)+')}', header)
            sheet.write_formula(rowx, 21, '{=SUM('+self._symbol(save_row-1, 21) +':'+ self._symbol(rowx-1, 21)+')}', header)
            sheet.write_formula(rowx, 22, '{=SUM('+self._symbol(save_row-1, 22) +':'+ self._symbol(rowx-1, 22)+')}', header)
            sheet.write_formula(rowx, 23, '{=SUM('+self._symbol(save_row-1, 23) +':'+ self._symbol(rowx-1, 23)+')}', header)
            sheet.write_formula(rowx, 24, '{=SUM('+self._symbol(save_row-1, 24) +':'+ self._symbol(rowx-1, 24)+')}', header)
            sheet.write_formula(rowx, 25, '{=SUM('+self._symbol(save_row-1, 25) +':'+ self._symbol(rowx-1, 25)+')}', header)
            sheet.write_formula(rowx, 26, '{=SUM('+self._symbol(save_row-1, 26) +':'+ self._symbol(rowx-1, 26)+')}', header)
            sheet.write_formula(rowx, 27, '{=SUM('+self._symbol(save_row-1, 27) +':'+ self._symbol(rowx-1, 27)+')}', header)
            sheet.write_formula(rowx, 28, '{=SUM('+self._symbol(save_row-1, 28) +':'+ self._symbol(rowx-1, 28)+')}', header)
            sheet.write_formula(rowx, 29, '{=SUM('+self._symbol(save_row-1, 29) +':'+ self._symbol(rowx-1, 29)+')}', header)
           
        workbook.close()
        # out = base64.encodebytes(output.getvalue())
        out = encodestring(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})
        return {
            'name': 'Export Result',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'report.excel.output',
            'res_id': excel_id.id,
            'view_id': False,
#             'context': context,
            'type': 'ir.actions.act_window',
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



