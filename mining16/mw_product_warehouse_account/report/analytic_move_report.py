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
    _inherit = "analytic.move.report"

    branch_ids = fields.Many2many('res.branch', string='Салбар')
    account_ids = fields.Many2many('account.account', string='Данс')
    partner_ids = fields.Many2many('res.partner', string='Харилцагч')
    is_short = fields.Boolean(string=u'Товчоо', default=False)

    is_hide = fields.Boolean(string='Данстай', default=True)
    def export_report(self):
        def _get_data_float(data):
            if data == None or data == False:
                return 0.00
            else:
                return round(data,2) + 0.00
        domain=[('date','<=',self.date_end),('date','>=',self.date_start),('company_id','=',self.company_id.id)]
        if not self.account_ids and self.move_type=="debit":
            domain.append(('amount','>',0))
        elif not self.account_ids and self.move_type=="credit":
            domain.append(('amount','<',0))
        if self.branch_ids:
            domain.append(('branch_id','in',self.branch_ids.ids))
        if self.account_ids:
            domain.append(('general_account_id','in',self.account_ids.ids))
        if self.partner_ids:
            domain.append(('partner_id','in',self.partner_ids.ids))
        moves = self.env['account.analytic.line'].search(domain)
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
            branch = ''
            if self.branch_ids:
                for item in self.branch_ids:
                    branch +=   item.name + ' / '
            worksheet.merge_range(3, 1, 3, 3, u"Компанийн нэр: "+self.company_id.name,h2)
            worksheet.merge_range(4, 1, 4, 3,  u"Шинжилгээний дансны тайлан", h1)
            worksheet.merge_range(5, 1, 5, 3,  u"Хугацаа:" + str(self.date_start) +"  "+str(self.date_end), h2)
            worksheet.merge_range(6, 1, 6, 9,  u"Салбар:" + " / " + branch, h2)
            # TABLE HEADER
            row = 8
            sum_amount=0
            sum_debit=0
            sum_credit=0
            if self.is_hide and self.is_short ==False:
                worksheet.merge_range(8, 0, 9, 0, u'Огноо', header)
                worksheet.merge_range(8, 1, 9, 1, u'Код', header)
                worksheet.merge_range(8, 2, 9, 2, u'Салбар', header)
                worksheet.merge_range(8, 3, 9, 3, u'Шинжилгээний данс', header)
                worksheet.merge_range(8, 4, 9, 4, u'Дэд шинжилгээний данс', header)
                worksheet.merge_range(8, 5, 9, 5, u'Техник', header)
                worksheet.merge_range(8, 6, 9, 6, u'Тоног төхөөрөмж', header)
                worksheet.merge_range(8, 7, 9, 7, u'Дугаар', header)
                worksheet.merge_range(8, 8, 9, 8, u'Дансны дугаар', header)
                worksheet.merge_range(8, 9, 9, 9, u'Дансны нэр', header)
                # worksheet.write(8, 7, u'Дүн', header)
                worksheet.merge_range(8, 10, 8, 12, u'Дүн', header)
                
                worksheet.write(10, 10, u'Дт', header)
                worksheet.write(10, 11, u'Кт', header)
                worksheet.write(10, 12, u'Дүн', header)
            elif self.is_short and self.is_hide:
                worksheet.merge_range(8, 0, 9, 0, u'Огноо', header)
                worksheet.merge_range(8, 1, 9, 1, u'Код', header)
                worksheet.merge_range(8, 2, 9, 2, u'Салбар', header)
                worksheet.merge_range(8, 3, 9, 3, u'Шинжилгээний данс', header)
                worksheet.merge_range(8, 4, 9, 4, u'Дэд шинжилгээний данс', header)
                worksheet.merge_range(8, 5, 9, 5, u'Техник', header)
                worksheet.merge_range(8, 6, 9, 6, u'Тоног төхөөрөмж', header)
                worksheet.merge_range(8, 7, 9, 7, u'Дансны дугаар', header)
                worksheet.merge_range(8, 8, 9, 8, u'Дансны нэр', header)
                # worksheet.write(8, 7, u'Дүн', header)
                worksheet.merge_range(8, 9, 8, 11, u'Дүн', header)
                
                worksheet.write(10, 9, u'Дт', header)
                worksheet.write(10, 10, u'Кт', header)
                worksheet.write(10, 11, u'Дүн', header)


            elif self.is_short and self.is_hide ==False:
                worksheet.merge_range(8, 0, 9, 0, u'Огноо', header)
                worksheet.merge_range(8, 1, 9, 1, u'Код', header)
                worksheet.merge_range(8, 2, 9, 2, u'Салбар', header)
                worksheet.merge_range(8, 3, 9, 3, u'Шинжилгээний данс', header)
                worksheet.merge_range(8, 4, 9, 4, u'Дэд шинжилгээний данс', header)
                # worksheet.write(8, 7, u'Дүн', header)
                worksheet.merge_range(8, 5, 8, 7, u'Дүн', header)
                
                worksheet.write(10, 5, u'Дт', header)
                worksheet.write(10, 6, u'Кт', header)
                worksheet.write(10, 7, u'Дүн', header)
            elif self.is_short ==False and self.is_hide ==False:
                worksheet.merge_range(8, 0, 9, 0, u'Огноо', header)
                worksheet.merge_range(8, 1, 9, 1, u'Код', header)
                worksheet.merge_range(8, 2, 9, 2, u'Салбар', header)
                worksheet.merge_range(8, 3, 9, 3, u'Шинжилгээний данс', header)
                worksheet.merge_range(8, 4, 9, 4, u'Дэд шинжилгээний данс', header)
                worksheet.merge_range(8, 5, 9, 5, u'Дугаар', header)
                # worksheet.write(8, 7, u'Дүн', header)
                worksheet.merge_range(8, 6, 8, 8, u'Дүн', header)
                
                worksheet.write(10, 6, u'Дт', header)
                worksheet.write(10, 7, u'Кт', header)
                worksheet.write(10, 8, u'Дүн', header)
            worksheet.set_column('A:A', 10)
            worksheet.set_column('B:B', 10)
            worksheet.set_column('C:C', 20)
            worksheet.set_column('D:D', 20)
            worksheet.set_column('E:E', 20)
            worksheet.set_column('F:F', 20)
            worksheet.set_column('G:G', 20)
            worksheet.set_column('H:H', 20)
            worksheet.set_column('I:I', 20)
            worksheet.set_column('J:J', 20)
            worksheet.set_column('K:K', 20)
            worksheet.set_column('L:L', 20)
            worksheet.set_column('M:M', 20)
            worksheet.set_column('N:N', 20)
            worksheet.set_column('O:O', 20)
            worksheet.set_column('P:P', 20)
            worksheet.set_column('Q:Q', 20)
            worksheet.set_column('R:R', 20)
            worksheet.set_column('S:S', 20)
            worksheet.set_column('T:T', 20)
            worksheet.set_column('U:U', 20)
            worksheet.set_column('V:V', 20)
            worksheet.set_column('W:W', 20)
            worksheet.set_column('Y:Y', 20)
            worksheet.set_column('Z:Z', 20)
            worksheet.set_column('X:X', 20)            
            # DATA зурах
            ss=9
            if self.is_short:
                data={}
                tech_name =''
                for item in moves:
                    if data.get(item.general_account_id,False):
                        if data[item.general_account_id].get(item.account_id,False):
                            data[item.general_account_id][item.account_id]['amount']+=item.amount
                            data[item.general_account_id][item.account_id]['debit']+=item.move_line_id.debit
                            data[item.general_account_id][item.account_id]['credit']+=item.move_line_id.credit
                        else:
                            name = ''
                            if item.move_line_id and item.move_line_id.name:
                                name += item.move_line_id.move_id.name + ' ' + item.move_line_id.name
                            else:
                                if item.move_line_id:
                                    name+=item.move_line_id.move_id.name
                                else:
                                    name=''
                            if item.technic_id and item.technic_id.name:
                                tech_name += item.technic_id.name
                                if item.technic_id.state_number:
                                    tech_name+= ' ' + item.technic_id.state_number
                                elif item.technic_id.vin_number:
                                    tech_name+= ' ' + item.technic_id.vin_number
                            data[item.general_account_id][item.account_id]={'acc_code':item.account_id.code,
                                                       'acc_date':item.date,
                                                       'acc_name':item.account_id.name,
                                                       'branch':item.branch_id.name,
                                                       'gen_acc_code':item.general_account_id.code,
                                                       'gen_acc_name':item.general_account_id.name,
                                                       'technic_id':tech_name,
                                                       'equipment_id':hasattr(item, 'equipment_id') and item.equipment_id and item.equipment_id.name or '',
                                                       'amount':item.amount,
                                                       'plan':item.account_id.plan_id and item.account_id.plan_id.name or '',
                                                       'debit':item.move_line_id.debit,
                                                       'credit':item.move_line_id.credit,
                                                       'name':name
                                                       }
                    else:
                        name = ''
                        if item.move_line_id and item.move_line_id.name:
                            name += item.move_line_id.move_id.name + ' ' + item.move_line_id.name
                        else:
                            if item.move_line_id:
                                name+=item.move_line_id.move_id.name
                            else:
                                name=''
                        if item.technic_id and item.technic_id.name:
                            tech_name += item.technic_id.name
                            if item.technic_id.state_number:
                                tech_name+= ' ' + item.technic_id.state_number
                            elif item.technic_id.vin_number:
                                tech_name+= ' ' + item.technic_id.vin_number
                        data[item.general_account_id]={item.account_id:{'acc_code':item.account_id.code,
                                                       'acc_date':item.date,
                                                       'acc_name':item.account_id.name,
                                                       'branch':item.branch_id.name,
                                                       'gen_acc_code':item.general_account_id.code,
                                                       'gen_acc_name':item.general_account_id.name,
                                                       'technic_id':tech_name,
                                                       'equipment_id':hasattr(item, 'equipment_id') and item.equipment_id and item.equipment_id.name or '',
                                                       'plan':item.account_id.plan_id and item.account_id.plan_id.name or '',
                                                       'amount':item.amount,
                                                       'debit':item.move_line_id.debit,
                                                       'credit':item.move_line_id.credit,
                                                       'name':name
                                                       }
                                                       }
                for d in data:
                    if self.is_hide:
                        for dd in data[d]:
                            ss+=1
                            worksheet.write(ss,0,str(data[d][dd]['acc_date']),contest_center)
                            worksheet.write(ss,1,data[d][dd]['acc_code'],contest_center)
                            worksheet.write(ss,2,data[d][dd]['branch'],contest_center)
                            worksheet.write(ss,3,data[d][dd]['plan'],contest_center)
                            worksheet.write(ss,4,data[d][dd]['acc_name'],contest_center)
                            worksheet.write(ss,5,data[d][dd]['technic_id'],contest_center)
                            worksheet.write(ss,6,data[d][dd]['equipment_id'],contest_center)
                            worksheet.write(ss,7,data[d][dd]['gen_acc_code'],  contest_center)
                            worksheet.write(ss,8,data[d][dd]['gen_acc_name'],contest_center)
                            worksheet.write(ss,9,data[d][dd]['debit'],contest_center)
                            worksheet.write(ss,10,data[d][dd]['credit'],contest_center)
                            worksheet.write(ss,11,data[d][dd]['amount'],contest_center)
                            row = ss+1
                            
                            sum_amount += data[d][dd]['amount']
                            sum_debit +=data[d][dd]['debit']
                            sum_credit +=data[d][dd]['credit']

                            worksheet.write(9, 9, sum_debit, accounting_format_blue)
                            worksheet.write(9, 10, sum_credit, accounting_format_blue)
                            worksheet.write(9, 11, sum_amount, accounting_format_blue)
                    else:
                        for dd in data[d]:
                            ss+=1
                            worksheet.write(ss,0,str(data[d][dd]['acc_date']),contest_center)
                            worksheet.write(ss,1,data[d][dd]['acc_code'],contest_center)
                            worksheet.write(ss,2,data[d][dd]['branch'],contest_center)
                            worksheet.write(ss,3,data[d][dd]['plan'],contest_center)
                            worksheet.write(ss,4,data[d][dd]['acc_name'],contest_center)
                            worksheet.write(ss,5,data[d][dd]['debit'],contest_center)
                            worksheet.write(ss,6,data[d][dd]['credit'],contest_center)
                            worksheet.write(ss,7,data[d][dd]['amount'],contest_center)
                            row = ss+1
                            
                            sum_amount += data[d][dd]['amount']
                            sum_debit +=data[d][dd]['debit']
                            sum_credit +=data[d][dd]['credit']

                            worksheet.write(9, 5, sum_debit, accounting_format_blue)
                            worksheet.write(9, 6, sum_credit, accounting_format_blue)
                            worksheet.write(9, 7, sum_amount, accounting_format_blue)
            else:
                if self.is_hide:
                    for item in moves:
                        name = ''
                        tech_name =''
                        if item.move_line_id and item.move_line_id.name:
                            name += item.move_line_id.move_id.name + ' ' + item.move_line_id.name
                        else:
                            if item.move_line_id:
                                name+=item.move_line_id.move_id.name
                            else:
                                name=''
                        if item.technic_id and item.technic_id.name:
                            tech_name += item.technic_id.name
                            if item.technic_id.state_number:
                                tech_name+= ' ' + item.technic_id.state_number
                            elif item.technic_id.vin_number:
                                tech_name+= ' ' + item.technic_id.vin_number
                        ss+=1
                        worksheet.write(ss,0,str(item.date),contest_center)
                        worksheet.write(ss,1,item.account_id.code,contest_center)
                        worksheet.write(ss,2,item.branch_id and item.branch_id.name or '',contest_center)
                        worksheet.write(ss,3,item.account_id.plan_id and item.account_id.plan_id.name or '' ,contest_center)
                        worksheet.write(ss,4,item.account_id.name,contest_center)
                        worksheet.write(ss,5,tech_name ,contest_center)
                        worksheet.write(ss,6,hasattr(item, 'equipment_id') and item.equipment_id and item.equipment_id.name or '' ,contest_center)
                        worksheet.write(ss,7,name,contest_center)
                        worksheet.write(ss,8,item.general_account_id.code,  contest_center)
                        worksheet.write(ss,9,item.general_account_id.name,contest_center)
                        worksheet.write(ss,10,item.move_line_id.debit,contest_center)
                        worksheet.write(ss,11,item.move_line_id.credit,contest_center)
                        worksheet.write(ss,12,item.amount,contest_center)
                        row = ss+1
                            
                        sum_amount += item.amount
                        sum_debit +=item.move_line_id.debit
                        sum_credit +=item.move_line_id.credit

                        worksheet.write(9, 10, sum_debit, accounting_format_blue)
                        worksheet.write(9, 11, sum_credit, accounting_format_blue)
                        worksheet.write(9, 12, sum_amount, accounting_format_blue)
                else:
                    for item in moves:
                        ss+=1
                        worksheet.write(ss,0,str(item.date),contest_center)
                        worksheet.write(ss,1,item.account_id.code,contest_center)
                        worksheet.write(ss,2,item.branch_id and item.branch_id.name or '',contest_center)
                        worksheet.write(ss,3,item.account_id.plan_id and item.account_id.plan_id.name or '' ,contest_center)
                        worksheet.write(ss,4,item.account_id.name,contest_center)
                        worksheet.write(ss,5,item.move_line_id.move_id.name if item.move_line_id else '',contest_center)
                        worksheet.write(ss,6,item.move_line_id.debit,contest_center)
                        worksheet.write(ss,7,item.move_line_id.credit,contest_center)
                        worksheet.write(ss,8,item.amount,contest_center)
                        row = ss+1
                            
                        sum_amount += item.amount
                        sum_debit +=item.move_line_id.debit
                        sum_credit +=item.move_line_id.credit

                        worksheet.write(9, 6, sum_debit, accounting_format_blue)
                        worksheet.write(9, 7, sum_credit, accounting_format_blue)
                        worksheet.write(9, 8, sum_amount, accounting_format_blue)
            workbook.close()
            out = base64.encodebytes(output.getvalue())
            excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})

            return {
                    'type' : 'ir.actions.act_url',
                    'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
                    'target': 'new',
            }

