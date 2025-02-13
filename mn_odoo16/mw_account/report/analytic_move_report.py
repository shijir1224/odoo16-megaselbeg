from odoo import fields, models, tools, api
import xlsxwriter
import xlwt
from xlsxwriter.utility import xl_rowcol_to_cell
from odoo.exceptions import UserError, AccessError
from io import BytesIO
import base64
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import locale

class AnalyticMoveReport(models.Model):
    """Analytic Move REPORT """
    _name = "analytic.move.report"
    _description = "Analytic Move REPORT"

    date_end = fields.Date(required=True, string=u'Тайлангийн огноо', default=fields.Date.context_today)
    date_start = fields.Date(required=True, string=u'Тайлангийн огноо', default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Компани', required=True, default=lambda self: self.env.company)
    move_type = fields.Selection(
        [("debit", "Кредит гүйлгээ"), ("credit", "Дэбит гүйлгээ"), ("all_move", "Бүх гүйлгээ")],
        string="Гүйлгээний төрөл",
        required=True,
        default="debit",
    )
    
    def export_report(self):
        def _get_data_float(data):
            if data == None or data == False:
                return 0.00
            else:
                return round(data,2) + 0.00

        if self.move_type=="debit":
            # pos_order = self.env['pos.order'].search([('date_order','>=',self.date_start),('date_order','<=',self.date_end)], order='date_order asc')
            # for pop in pos_order:
            moves = self.env['account.analytic.line'].search([('date','<=',self.date_end),('date','>=',self.date_start),('company_id','=',self.company_id.id),('amount','>',0)])
        elif self.move_type=="credit":
            # pos_order = self.env['pos.order'].search([('date_order','>=',self.date_start),('date_order','<=',self.date_end)], order='date_order asc')
            # for pop in pos_order:
            moves = self.env['account.analytic.line'].search([('date','<=',self.date_end),('date','>=',self.date_start),('company_id','=',self.company_id.id),('amount','<',0)])
        else:
            moves = self.env['account.analytic.line'].search([('date','<=',self.date_end),('date','>=',self.date_start),('company_id','=',self.company_id.id)])
        if not moves:
            raise UserError(u'Тухайн огноонд үүссэн шинжилгээний бичилт олдсонгүй огноогоо шалгана уу!')
        else:
            year = self.date_end.year
            month = self.date_end.month
            day = self.date_end.day
            date_name = '%s оны %s сарын %s өдрийн'%(year, month, day)


            # Generate EXCEL
            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            file_name = 'Шинжилгээний тайлан'+'.xlsx'

            h1 = workbook.add_format({'bold': 1})
            h1.set_font_size(18)

            h2 = workbook.add_format({'bold': 1})
            h2.set_font_size(12)

            header = workbook.add_format({'bold': 1})
            header.set_text_wrap()
            header.set_font_size(10)
            header.set_align('center')
            header.set_align('vcenter')
            header.set_border(style=1)
            header.set_bg_color('80d8ff')

            header_wrap = workbook.add_format({'bold': 1})
            header_wrap.set_text_wrap()
            header_wrap.set_font_size(9)
            header_wrap.set_align('center')
            header_wrap.set_align('vcenter')
            header_wrap.set_border(style=1)
            header_wrap.set_bg_color('#E9A227')

            number_right = workbook.add_format()
            number_right.set_text_wrap()
            number_right.set_font_size(9)
            number_right.set_align('right')
            number_right.set_align('vcenter')
            number_right.set_border(style=1)

            contest_left = workbook.add_format()
            contest_left.set_text_wrap()
            contest_left.set_font_size(9)
            contest_left.set_align('left')
            contest_left.set_align('vcenter')
            contest_left.set_border(style=1)

            contest_right = workbook.add_format()
            contest_right.set_text_wrap()
            contest_right.set_font_size(9)
            contest_right.set_align('right')
            contest_right.set_align('vcenter')
            contest_right.set_border(style=1)

            locale.setlocale(locale.LC_ALL, '')

            accounting_format = workbook.add_format({
                'num_format': '#,##0.00_);[Red](#,##0.00)',
                'text_wrap': True,
                'font_size': 12,
                'align': 'right',
                'valign': 'vright',
                'border': 1,
            })      
            accounting_format_blue = workbook.add_format({
                'num_format': '#,##0.00_);[Red](#,##0.00)',
                'text_wrap': True,
                'font_size': 12,
                'align': 'right',
                'valign': 'vright',
                'border': 1,
            })    
            accounting_format_blue.set_bg_color('80d8ff')
            last_accounting_format = workbook.add_format({
                'num_format': '#,##0.00_);[Red](#,##0.00)',
                'text_wrap': True,
                'bold': True,
                'font_size': 12,
                'align': 'left',
                'valign': 'vleft',
                'border': 1,
            })            
            contest_center = workbook.add_format()
            contest_center.set_text_wrap()
            contest_center.set_font_size(9)
            contest_center.set_align('left')
            contest_center.set_align('vleft')
            contest_center.set_border(style=1)

            header_center = workbook.add_format()
            header_center.set_text_wrap()
            header_center.set_font_size(72)
            header_center.set_align('left')
            header_center.set_align('vleft')
            header_center.set_bold()

            header_center_last = workbook.add_format()
            header_center_last.set_text_wrap()
            header_center_last.set_font_size(72)
            header_center_last.set_align('left')
            header_center_last.set_align('vleft')

            excel_date = xlwt.XFStyle()
            excel_date.num_format_str = 'yyyy-mm-dd HH:mm:ss' 
            
            sub_total_90 = workbook.add_format({'bold': 1})
            sub_total_90.set_text_wrap()
            sub_total_90.set_font_size(9)
            sub_total_90.set_align('center')
            sub_total_90.set_align('vcenter')
            sub_total_90.set_border(style=1)
            sub_total_90.set_bg_color('#F7EE5E')
            sub_total_90.set_rotation(90)
            
            worksheet = workbook.add_worksheet(u'Report')
            worksheet.set_zoom(100)
            row=0
            row = +3
            worksheet.merge_range(3, 1, 3, 3, u"Компанийн нэр: "+self.company_id.name,h2)
            worksheet.merge_range(4, 1, 4, 3,  u"Шинжилгээний дансны тайлан", h1)
            worksheet.merge_range(5, 1, 5, 3,  u"Хугацаа:" + str(self.date_start) +"  "+str(self.date_end), h2)

            # TABLE HEADER
            row = 8
            sum_amount=0
            worksheet.merge_range(8, 0, 9, 0, u'Код', header)
            worksheet.merge_range(8, 1, 9, 1, u'Шинжилгээний данс', header)
            worksheet.merge_range(8, 2, 9, 2, u'Дугаар', header)
            worksheet.merge_range(8, 3, 9, 3, u'Дансны дугаар', header)
            worksheet.merge_range(8, 4, 9, 4, u'Дансны нэр', header)
            worksheet.merge_range(8, 5, 8, 7, u'Дүн', header)
            worksheet.write(9, 5, u'Дт', header)
            worksheet.write(9, 6, u'Кт', header)
            worksheet.write(9, 7, u'Дүн', header)
            
            worksheet.set_column('A:A', 10)
            worksheet.set_column('B:B', 20)
            worksheet.set_column('C:C', 40)
            worksheet.set_column('D:D', 15)
            worksheet.set_column('E:E', 40)
            worksheet.set_column('F:F', 15 )
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 20)
            worksheet.set_column('I:I', 20)
            worksheet.set_column('J:J', 20)
            worksheet.set_column('K:K', 20)
            worksheet.set_column('L:L', 20)
            worksheet.set_column('M:M', 20)
            worksheet.set_column('N:N', 20)
            worksheet.set_column('O:O', 20)
            worksheet.set_column('P:P', 15)
            worksheet.set_column('Q:Q', 15)
            worksheet.set_column('R:R', 15)
            worksheet.set_column('S:S', 15)
            worksheet.set_column('T:T', 15)
            worksheet.set_column('U:U', 15)
            worksheet.set_column('V:V', 40)
            worksheet.set_column('W:W', 20)
            worksheet.set_column('Y:Y', 20)
            worksheet.set_column('Z:Z', 20)
            worksheet.set_column('X:X', 20)            
            # DATA зурах
            ss=9
            for item in moves:
                ss+=1
                worksheet.write(ss,0,item.account_id.code,contest_center)
                worksheet.write(ss,1,item.account_id.name,contest_center)
                worksheet.write(ss,2,item.ref,contest_center)
                worksheet.write(ss,3,item.general_account_id.code,  contest_center)
                worksheet.write(ss,4,item.general_account_id.name,contest_center)
                worksheet.write(ss,5,item.amount,accounting_format)
                row = ss+1
                    
                sum_amount += item.amount
            worksheet.write(9, 5, sum_amount, accounting_format_blue)
            workbook.close()
            out = base64.encodebytes(output.getvalue())
            excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

            return {
                    'type' : 'ir.actions.act_url',
                    'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
                    'target': 'new',
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
