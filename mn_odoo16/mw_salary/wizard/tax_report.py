# -*- coding: utf-8 -*-

import time
import xlsxwriter
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, timedelta

from odoo import tools
from odoo import api, fields, models

class TaxSalaryReport(models.TransientModel):
    _name = "tax.salary.report"  

    year= fields.Char(method=True, store=True, type='char', string='Жил', size=8)
    s_month=fields.Selection([('1','January'), ('2','February'), ('3','March'), ('4','April'),
            ('5','May'), ('6','June'), ('7','July'), ('8','August'), ('9','September'),
            ('90','October'), ('91','November'), ('92','December')], u'Эхлэх сар')
    e_month=fields.Selection([('1','January'), ('2','February'), ('3','March'), ('4','April'),
            ('5','May'), ('6','June'), ('7','July'), ('8','August'), ('9','September'),
            ('90','October'), ('91','November'), ('92','December')], u'Дуусах сар')
    season = fields.Char('Улирал')

    def export_report(self):
        ctx = dict(self._context)
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)

        sheet = workbook.add_worksheet(u'ХХОАТ тайлан')

        file_name = 'xtraReport'

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(12)

        theader = workbook.add_format({})
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
        theader1.set_align('right')
        theader1.set_align('vcenter')

        theader2 = workbook.add_format({'bold': 1})
        theader2.set_font_size(9)
        theader2.set_font('Times new roman')
        theader2.set_align('left')
        theader2.set_align('vcenter')

        center_register = workbook.add_format({})
        center_register.set_font_size(9)
        center_register.set_font('Times new roman')
        center_register.set_align('center')
        center_register.set_align('vcenter')
        center_register.set_border(style=1)

        theader3 = workbook.add_format({})
        theader3.set_font_size(9)
        theader3.set_font('Times new roman')
        theader3.set_align('left')
        theader3.set_align('vcenter')

        theaderdate = workbook.add_format({})
        theaderdate.set_font_size(9)
        theaderdate.set_font('Times new roman')
        theaderdate.set_align('center')
        theaderdate.set_align('vcenter')

        theaderdate1 = workbook.add_format({})
        theaderdate1.set_font_size(9)
        theaderdate1.set_font('Times new roman')
        theaderdate1.set_align('center')
        theaderdate1.set_align('vcenter')
        theaderdate1.set_bottom(1)

        theaderdate2 = workbook.add_format({})
        theaderdate2.set_font_size(9)
        theaderdate2.set_font('Times new roman')
        theaderdate2.set_align('center')
        theaderdate2.set_align('vcenter')
        theaderdate2.set_bottom(1)
        theaderdate2.set_left(1)

        theader4 = workbook.add_format({'bold': 1})
        theader4.set_font_size(12)
        theader4.set_font('Times new roman')
        theader4.set_align('center')
        theader4.set_align('vcenter')

        theader5 = workbook.add_format({'bold': 1})
        theader5.set_font_size(12)
        theader5.set_font('Times new roman')
        theader5.set_align('center')
        theader5.set_align('vcenter')
        theader5.set_bottom(5)

        theader6 = workbook.add_format({'bold': 1})
        theader6.set_font_size(12)
        theader6.set_font('Times new roman')
        theader6.set_align('left')
        theader6.set_align('vcenter')
        theader6.set_bottom(5)

        left_border = workbook.add_format({})
        left_border.set_font_size(12)
        left_border.set_font('Times new roman')
        left_border.set_align('left')
        left_border.set_align('vcenter')
        left_border.set_left(1)

        theader7 = workbook.add_format({})
        theader7.set_font_size(9)
        theader7.set_font('Times new roman')
        theader7.set_align('right')
        theader7.set_align('vcenter')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_font('Times new roman')
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
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
        # GET warehouse loc ids
        save_row=20
        rowx=14
        sheet.merge_range(rowx-13, 0,rowx-13, 36, u'ТЕГ-ын даргын 2011- оны 10 дугаар сарын 12-ны', theader7),
        sheet.merge_range(rowx-12, 0,rowx-12, 36, u'өдрийн 584 дүгээр тушаалын 1-р хавсралт', theader7),
        sheet.merge_range(rowx-10, 0,rowx-10, 5, u'Маягт ТТ-11(1)', theader6),
        sheet.merge_range(rowx-10, 6,rowx-10, 36, u'ҮНДЭСНИЙ ТАТВАРЫН АЛБА', theader5),
        sheet.merge_range(rowx-10, 9,rowx-10, 11, u'', theader5),
        sheet.merge_range(rowx-9, 0,rowx-9, 36, u'Үндсэн цалин, хөдөлмөрийн хөлс болон түүнтэй адилтгах', theader4),
        sheet.merge_range(rowx-8, 0,rowx-8, 36, u'орлогоос  суутгасан албан татварын тайлан', theader4),
        sheet.merge_range(rowx-7, 0,rowx-7, 3,u'ТТД:', theader2),
        sheet.write(rowx-7, 4,u'2', center_register),
        sheet.write(rowx-7, 5,u'0', center_register),
        sheet.write(rowx-7, 6,u'8', center_register),
        sheet.write(rowx-7, 7,u'8', center_register),
        sheet.write(rowx-7, 8,u'6', center_register),
        sheet.write(rowx-7, 9,u'0', center_register),
        sheet.write(rowx-7, 10,u'6', center_register),
        sheet.merge_range(rowx-5, 0,rowx-5, 3, u'Нэр:', theader2),
        sheet.merge_range(rowx-5, 4,rowx-5, 10, u'БОДЬ ДААТГАЛ', theader3),
        sheet.merge_range(rowx-4, 0,rowx-4, 6, u'Тайлангийн хугацаа:', theader2),
        sheet.merge_range(rowx-4, 7,rowx-4, 8, self.year, center_register),
        sheet.write(rowx-4, 9,u'он', theader2),
        sheet.write(rowx-4, 10, self.season, center_register),
        sheet.merge_range(rowx-4, 11,rowx-4, 12, u'-р улирал', theader2),
        sheet.merge_range(rowx-3, 0,rowx-3, 11, u'(Тайлангийн үзүүлэлтүүдийг оны эхнээс өссөн дүнгээр бөглөнө)', theader3),
        sheet.merge_range(rowx-1, 0,rowx-1, 6, u'(өссөн дүгээр)', theader2),
        sheet.write(rowx-1, 11, u'(мянган төгрөгөөр)', theader1),

        sheet.write(rowx-7, 15,'', left_border),
        sheet.write(rowx-6, 15,'', left_border),
        sheet.write(rowx-5, 15,'', left_border),
        sheet.write(rowx-4, 15,'', left_border),
        sheet.write(rowx-3, 15,'', left_border),

        sheet.merge_range(rowx-7, 16,rowx-7, 30, u'Зөвхөн татварын албан ажлын хэрэгцээнд', theader3),
        sheet.merge_range(rowx-6, 16,rowx-6, 18, u'БТД:', theader3),
        sheet.write(rowx-6, 19,u'', center_register),
        sheet.write(rowx-6, 20,u'', center_register),
        sheet.write(rowx-6, 21,u'', center_register),
        sheet.write(rowx-6, 22,u'', center_register),
        sheet.write(rowx-6, 23,u'', center_register),
        sheet.write(rowx-6, 24,u'', center_register),
        sheet.write(rowx-6, 25,u'', center_register),
        sheet.write(rowx-6, 26,u'', center_register),
        sheet.write(rowx-6, 27,u'', center_register),
        sheet.write(rowx-6, 28,u'', center_register),
        sheet.write(rowx-6, 29,u'', center_register),
        sheet.write(rowx-6, 30,u'', center_register),
        sheet.write(rowx-6, 31,u'', center_register),
        sheet.merge_range(rowx-5, 16,rowx-5, 21, u'Татварын байцаагч:', theader3),
        sheet.write(rowx-5, 22,u'', center_register),
        sheet.write(rowx-5, 23,u'', center_register),
        sheet.write(rowx-5, 24,u'', center_register),
        sheet.write(rowx-5, 25,u'', center_register),
        sheet.write(rowx-5, 26,u'', center_register),
        sheet.merge_range(rowx-4, 16,rowx-4, 21, u'Хүлээн авсан', theaderdate),
        sheet.write(rowx-3, 15,u'', theaderdate2),
        sheet.merge_range(rowx-3, 16,rowx-3, 21, u'он.сар.өдөр', theaderdate1),
        sheet.merge_range(rowx-3, 22,rowx-3, 32, '', theaderdate1),
        sheet.merge_range(rowx-8, 15,rowx-8, 32, '', theaderdate1),
        sheet.write(rowx-7, 33,'', left_border),
        sheet.write(rowx-6, 33,'', left_border),
        sheet.write(rowx-5, 33,'', left_border),
        sheet.write(rowx-4, 33,'', left_border),
        sheet.write(rowx-3, 33,'', left_border),


        sheet.merge_range(rowx, 0,rowx+4,1, u'Д/д', theader),
        sheet.merge_range(rowx, 2,rowx,11, u'Суутгагчийн', theader),
        sheet.merge_range(rowx+1, 2,rowx+3,5, u'Регистрийн дугаар', theader),
        sheet.merge_range(rowx+1, 6,rowx+3,8, u'Овог', theader),
        sheet.merge_range(rowx+1, 9,rowx+3,11, u'Нэр', theader),
        sheet.merge_range(rowx, 12,rowx+3,13, u'Үндсэн болон нэмэгдэл цалин(ХХОАТТХ-ний 11.1.1 дэх заалт)', theader),
        sheet.merge_range(rowx, 14,rowx+3,17, u'ЭМД болон НДШ-ийн дүн(4*10%)', theader),
        sheet.merge_range(rowx, 18,rowx+3,21, u'ЭМД болон НДШ-ийг хассан дүн(4-5)', theader),
        sheet.merge_range(rowx, 22,rowx+3,23, u'Шууд бус орлого', theader),
        sheet.merge_range(rowx, 24,rowx+3,26, u'Татвар ногдуулах нийт орлогын дүн(6+7)', theader),
        sheet.merge_range(rowx, 27,rowx+3,29, u'Ногдуулсан татвар(8*10%)', theader),
        sheet.merge_range(rowx, 30,rowx+3,32, u'Хөнгөлөгдөх татварын дүн', theader),
        sheet.merge_range(rowx, 33,rowx+3,36, u'Төлөх татварын дүн(9-10)', theader),

        sheet.merge_range(rowx+4, 2,rowx+4, 5, u'1', theader),
        sheet.merge_range(rowx+4, 6,rowx+4, 8, u'2', theader),
        sheet.merge_range(rowx+4, 9,rowx+4, 11, u'3', theader),
        sheet.merge_range(rowx+4, 12,rowx+4, 13, u'4', theader),
        sheet.merge_range(rowx+4, 14,rowx+4, 17, u'5', theader),
        sheet.merge_range(rowx+4, 18,rowx+4, 21, u'6', theader),
        sheet.merge_range(rowx+4, 22,rowx+4, 23, u'7', theader),
        sheet.merge_range(rowx+4, 24,rowx+4, 26, u'8', theader),
        sheet.merge_range(rowx+4, 27,rowx+4, 29, u'9', theader),
        sheet.merge_range(rowx+4, 30,rowx+4, 32, u'10', theader),
        sheet.merge_range(rowx+4, 33,rowx+4, 36, u'11', theader),
        rowx+=5
        
        sheet.set_column('A:D', 1)
        sheet.set_column('E:L', 3)
        sheet.set_column('M:O', 4)
        sheet.set_column('P:R', 1)
        sheet.set_column('S:S', 1)
        sheet.set_column('T:AF', 3)
        sheet.set_column('AG:AK', 1.5)

        query="""SELECT  he.name as name,
            he.last_name as last_name,
            he.passport_id as register,
            sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PITDIS')) as dis,
            sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='SHI')) as shi,
            sum((select coalesce(sum(amount),0) from salary_order_line_line ll left join hr_allounce_deduction_category cat ON cat.id=ll.category_id where ll.order_line_id1=line.id and cat.code='PIT')) as pit,
            sum(line.amount_tootsson) as amount_tootsson
            FROM salary_order so
            LEFT JOIN salary_order_line line ON line.order_id=so.id
            LEFT JOIN hour_balance_line bal ON bal.order_balance_line_id=line.id
            LEFT JOIN hr_employee he ON he.id=line.employee_id
            LEFT JOIN hr_department hd ON he.department_id=hd.id
            LEFT JOIN hr_job hj ON hj.id=he.job_id
            LEFT JOIN hr_contract hc ON hc.employee_id=he.id
            LEFT JOIN insured_type it ON line.insured_type_id=it.id
            WHERE so.type='final' and so.month>='%s' and so.month<='%s'  and so.year='%s'
            GROUP BY he.name,he.last_name,he.passport_id"""%(self.s_month,self.e_month,self.year)
        self.env.cr.execute(query)
        records = self.env.cr.dictfetchall()
        # rowx+=1
        pay=0
        hungulult=0
        n=1
        for record in records:
            # pay=record[5]-record[5]*0.115
            # hhoat=(record[5]-record[5]*0.115)*0.1
            sheet.merge_range(rowx, 0,rowx, 1,n,theader)
            sheet.merge_range(rowx, 2,rowx, 5,record['register'],contest_left)
            sheet.merge_range(rowx, 6,rowx, 8,record['last_name'],contest_left)
            sheet.merge_range(rowx, 9,rowx, 11,record['name'],contest_left)
            sheet.merge_range(rowx, 12,rowx, 13,record['amount_tootsson'],contest_right)
            sheet.merge_range(rowx, 14,rowx, 17,record['shi'],contest_right)
            sheet.merge_range(rowx, 18,rowx, 21,record['amount_tootsson']-record['shi'],contest_right)
            sheet.merge_range(rowx, 22,rowx, 23,'',contest_right)
            sheet.merge_range(rowx, 24,rowx, 26,record['amount_tootsson']-record['shi'],contest_right)
            sheet.merge_range(rowx, 27,rowx, 29,record['pit'],contest_right)
            sheet.merge_range(rowx, 30,rowx, 32,record['dis'],contest_right)
            sheet.merge_range(rowx, 33,rowx, 36,record['pit']-record['dis'],contest_right)

            rowx+=1
            n+=1
        sheet.merge_range(rowx,0, rowx,1, u"", header)
        sheet.merge_range(rowx,2, rowx,5, u"", header)
        sheet.merge_range(rowx,6, rowx,8, u"", header)
        sheet.merge_range(rowx,9, rowx,11,  u"ДҮН", header)
        sheet.merge_range(rowx, 12,rowx, 13,'{=SUM('+self._symbol(save_row-1, 12) +':'+ self._symbol(rowx-1, 13)+')}', header)
        sheet.merge_range(rowx, 14,rowx, 17, '{=SUM('+self._symbol(save_row-1, 14) +':'+ self._symbol(rowx-1, 17)+')}', header)
        sheet.merge_range(rowx, 18,rowx, 21, '{=SUM('+self._symbol(save_row-1, 18) +':'+ self._symbol(rowx-1, 21)+')}', header)
        sheet.merge_range(rowx, 22,rowx, 23, '{=SUM('+self._symbol(save_row-1, 22) +':'+ self._symbol(rowx-1, 23)+')}', header)
        sheet.merge_range(rowx, 24,rowx, 26, '{=SUM('+self._symbol(save_row-1, 24) +':'+ self._symbol(rowx-1, 26)+')}', header)
        sheet.merge_range(rowx, 27,rowx, 29, '{=SUM('+self._symbol(save_row-1, 27) +':'+ self._symbol(rowx-1, 29)+')}', header)
        sheet.merge_range(rowx, 30,rowx, 32, '{=SUM('+self._symbol(save_row-1, 30) +':'+ self._symbol(rowx-1, 32)+')}', header)
        sheet.merge_range(rowx, 33,rowx, 36, '{=SUM('+self._symbol(save_row-1, 33) +':'+ self._symbol(rowx-1, 36)+')}', header)

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

