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

class AnalyticPeriodReport(models.Model):
    """Analytic Period REPORT """
    _name = "analytic.period.report"
    _description = "Analytic Move REPORT"

    date_end = fields.Date(required=True, string=u'Тайлангийн огноо', default=fields.Date.context_today)
    date_start = fields.Date(required=True, string=u'Тайлангийн огноо', default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Компани', required=True, default=lambda self: self.env.company)
    branch_ids = fields.Many2many('res.branch', string='Салбар')
    account_ids = fields.Many2many('account.account', string='Данс')
    by_dtcr = fields.Boolean(u'Дебит Кредит', default=False)
    
        # current_year = 2024
        # for month in range(1, 13):
        #     num_days = monthrange(current_year, month)[1]
        #     date_object = datetime(current_year, month, num_days)
        #     date_last = date_object.strftime("%Y-%m-%d")
        #     date_first = date_object.replace(day=1).strftime("%Y-%m-%d")
        #     print('month:', month, 'day:', num_days, 'first date: ', date_first, 'last date: ', date_last)
            
                
    def export_report(self):
        def _get_data_float(data):
            if data == None or data == False:
                return 0.00
            else:
                return round(data,2) + 0.00
        account_where=""
        if self.account_ids:
            account_where+=' and aml.account_id in ('+','.join(map(str,self.account_ids.ids))+')'
        if self.branch_ids:
            account_where+=' and aml.branch_id in ('+','.join(map(str,self.branch_ids.ids))+')'
        # query = """select sum(anl.amount) as amount,sum(aml.debit-aml.credit) as debit,
        #                     a.code,a.name as account,an.code as an_code, 
        #                     an.name as analytic_acc,
        #                     --anl.date,aml.date,
        #                     date_part('year',aml.date)::text || '-' || date_part('month',aml.date)::text as year,
        #                     date_part('year',aml.date)::text as year_year,
        #                     an.id as an_id,
        #                     a.id as a_id,
        #                     case when aml.technic_id notnull then 
        #                         '[' || ' ' || (select state_number from technic_equipment where id=aml.technic_id) || ' ' || ' ]' ||                        
        #                         '[' || ' ' || (select vin_number from technic_equipment where id=aml.technic_id) || ' ' || ' ]'     ||    ' ' || 
        #                         (select name from technic_equipment where id=aml.technic_id)    
        #                      when aml.technic_id isnull and aml.equipment_id  notnull then 
        #                         '[' || ' ' || (select vin_number from factory_equipment where id=aml.equipment_id) || ' ' || ' ]' ||
        #                         (select name from factory_equipment where id=aml.equipment_id)
        #                     else an.name end as technic ,
        #                     aml.technic_id as t_id,
        #                     aml.equipment_id as e_id                            
        #              from account_analytic_line anl left join 
        #                     account_move_line aml on anl.move_line_id=aml.id left join 
        #                     account_account a on aml.account_id=a.id left join 
        #                     account_analytic_account an on anl.account_id=an.id 
        #              where aml.date between '{0}' and '{1}' {2} and aml.company_id={3}
        #              group by a.code,a.name, an.name,date_part('year',aml.date) ,
        #                  date_part('month',aml.date),an.code, an.id, a.id,
        #                     aml.technic_id,
        #                     aml.equipment_id
        #              order by an.name,a.code
        #
        #         """.format(self.date_start,self.date_end,account_where,self.company_id.id)
        query = """select sum(anl.amount) as amount,sum(aml.debit-aml.credit) as debit_amount1,
                            sum(aml.debit) as debit_amount,
                            sum(aml.credit) as credit_amount,
                            a.code,a.name as account,an.code as an_code, 
                            an.name as analytic_acc,
                            --anl.date,aml.date,
                            date_part('year',aml.date)::text || '-' || date_part('month',aml.date)::text as year,
                            date_part('year',aml.date)::text as year_year,
                            an.id as an_id,
                            a.id as a_id,
--                             case when aml.technic_id notnull then 
--                                 '[' || ' ' || (select state_number from technic_equipment where id=aml.technic_id) || ' ' || ' ]' ||                        
--                                 '[' || ' ' || (select vin_number from technic_equipment where id=aml.technic_id) || ' ' || ' ]'     ||    ' ' || 
--                                 (select name from technic_equipment where id=aml.technic_id)    
--                              when aml.technic_id isnull and aml.equipment_id  notnull then 
--                                 '[' || ' ' || (select vin_number from factory_equipment where id=aml.equipment_id) || ' ' || ' ]' ||
--                                 (select name from factory_equipment where id=aml.equipment_id)
--                             else an.name end as technic ,
                            case when t.id notnull then 
                                '[' || ' ' || (select case when t.state_number notnull then t.state_number else '' end as nnn) || ' ' || ' ]' ||               
                                '[' || ' ' || (select case when t.vin_number notnull then t.vin_number else '' end as ddd) || ' ' || ' ]' ||               
                                t.name
                                when t.id isnull and e.id notnull then
                                    '[' || ' ' ||  e.vin_number  || ' ' || ' ]' ||
                                    e.name
                                else an.name end as technic ,
                            t.id as t_id,
                            e.id as e_id                              
                     from account_analytic_line anl left join 
                            account_move_line aml on anl.move_line_id=aml.id left join 
                            account_account a on aml.account_id=a.id left join 
                            account_analytic_account an on anl.account_id=an.id    left join
                            technic_equipment t on aml.technic_id=t.id   left join 
                            factory_equipment e on aml.equipment_id= e.id
                     where aml.date between '{0}' and '{1}' {2} and aml.company_id={3}
                     group by a.code,a.name, an.name,date_part('year',aml.date) ,
                         date_part('month',aml.date),an.code, an.id, a.id,
                            t.id,
                            e.id
                     order by an.name,a.code
                     
                """.format(self.date_start,self.date_end,account_where,self.company_id.id)        
        # print ('query ',query)
        self.env.cr.execute(query)
        result = self.env.cr.dictfetchall()  
        # print ('resultresultresult ',result)
        if not result:
            raise UserError(u'Тухайн огноонд үүссэн шинжилгээний бичилт олдсонгүй огноогоо шалгана уу!')
        else:
            datas={}
            years=[]
            for data in result:
                cdata=data
                if datas.get(data['an_id'],False):
                    datas[data['an_id']].append(data)
                else:
                    datas[data['an_id']] = [data]
                years.append(data['year'])
            # print ('datas123 ',datas)
            # print ('datas123l ',len(datas))
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
            # worksheet.merge_range(8, 0, 9, 0, u'Код', header)
            # worksheet.merge_range(8, 1, 9, 1, u'Шинжилгээний данс', header)
            # worksheet.merge_range(8, 2, 9, 2, u'Дугаар', header)
            # worksheet.merge_range(8, 3, 9, 3, u'Дансны нэр', header)
            # worksheet.merge_range(8, 4, 9, 4, u'Техник ТТ', header)
            worksheet.write(8, 0, u'Код', header)
            worksheet.write(8, 1, u'Шинжилгээний данс', header)
            worksheet.write(8, 2, u'Дугаар', header)
            worksheet.write(8, 3, u'Дансны нэр', header)
            worksheet.write(8, 4, u'Техник ТТ', header)
            if self.by_dtcr:
                worksheet.write(8, 5, u'1-р сар /dt/', header)
                worksheet.write(8, 6, u'1-р сар /cr/', header)
                worksheet.write(8, 7, u'2-р сар /dt/', header)
                worksheet.write(8, 8, u'2-р сар /cr/', header)
                worksheet.write(8, 9, u'3-р сар /dt/', header)
                worksheet.write(8, 10, u'3-р сар /cr/', header)
                worksheet.write(8, 11, u'4-р сар /dt/', header)
                worksheet.write(8, 12, u'4-р сар /cr/', header)
                worksheet.write(8, 13, u'5-р сар /dt/', header)
                worksheet.write(8, 14, u'5-р сар /cr/', header)
                worksheet.write(8, 15, u'6-р сар /dt/', header)
                worksheet.write(8, 16, u'6-р сар /cr/', header)
                worksheet.write(8, 17, u'7-р сар /dt/', header)
                worksheet.write(8, 18, u'7-р сар /cr/', header)
                worksheet.write(8, 19, u'8-р сар /dt/', header)
                worksheet.write(8, 20, u'8-р сар /cr/', header)
                worksheet.write(8, 21, u'9-р сар /dt/', header)
                worksheet.write(8, 22, u'9-р сар /cr/', header)
                worksheet.write(8, 23, u'10-р сар /dt/', header)
                worksheet.write(8, 24, u'10-р сар /cr/', header)
                worksheet.write(8, 25, u'11-р сар /dt/', header)
                worksheet.write(8, 26, u'11-р сар /cr/', header)
                worksheet.write(8, 27, u'12-р сар /dt', header)
                worksheet.write(8, 28, u'12-р сар /cr/', header)
                worksheet.write(8, 29, u'Нийт', header)

                worksheet.set_column('A:A', 10)
                worksheet.set_column('B:B', 25)
                worksheet.set_column('C:C', 20)
                worksheet.set_column('D:D', 30)
                worksheet.set_column('E:E', 20)
                worksheet.set_column('F:F', 20 )
                worksheet.set_column('G:AD', 20)
            else:
                worksheet.write(8, 5, u'1-р сар', header)
                worksheet.write(8, 6, u'2-р сар', header)
                worksheet.write(8, 7, u'3-р сар', header)
                worksheet.write(8, 8, u'4-р сар', header)
                worksheet.write(8, 9, u'5-р сар', header)
                worksheet.write(8, 10, u'6-р сар', header)
                worksheet.write(8, 11, u'7-р сар', header)
                worksheet.write(8, 12, u'8-р сар', header)
                worksheet.write(8, 13, u'9-р сар', header)
                worksheet.write(8, 14, u'10-р сар', header)
                worksheet.write(8, 15, u'11-р сар', header)
                worksheet.write(8, 16, u'12-р сар', header)
                worksheet.write(8, 17, u'Нийт', header)
                    
                worksheet.set_column('A:A', 10)
                worksheet.set_column('B:B', 25)
                worksheet.set_column('C:C', 20)
                worksheet.set_column('D:D', 30)
                worksheet.set_column('E:E', 20)
                worksheet.set_column('F:F', 20 )
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
            for item in datas:
                # ss+=1
                # print ('item ',item)
                check_data=[]
                dd={}
                ddd=[]
                for i in datas[item]:
                    if dd.get(str(i['an_id'])+':'+str(i['a_id'])+':'+str(i['t_id'])+':'+str(i['e_id'])):
                        dd[str(i['an_id'])+':'+str(i['a_id'])+':'+str(i['t_id'])+':'+str(i['e_id'])][i['year']]=i['amount']
                        dd[str(i['an_id'])+':'+str(i['a_id'])+':'+str(i['t_id'])+':'+str(i['e_id'])][i['year']+'-c']=i['credit_amount']
                        dd[str(i['an_id'])+':'+str(i['a_id'])+':'+str(i['t_id'])+':'+str(i['e_id'])][i['year']+'-d']=i['debit_amount']
                    else:
                        dd[str(i['an_id'])+':'+str(i['a_id'])+':'+str(i['t_id'])+':'+str(i['e_id'])]={i['year']:i['amount'],
                                                                                                      i['year']+'-c':i['credit_amount'],
                                                                                                      i['year']+'-d':i['debit_amount'],
                                                                                                      'data':i}
                    ddd.append(i)
                    # if d['code'] in check_data:
                    #     print ('a')
                    # else:
                    #     check_data.append(d['code'])
                    # worksheet.write(ss,0,d['an_code'],contest_center)
                    # worksheet.write(ss,1,d['analytic_acc'],contest_center)
                    # worksheet.write(ss,2,d['code'],contest_center)
                    # worksheet.write(ss,3,d['account'],  contest_center)
                    # for x in range(4,16):
                    #
                    #     if str(x-3)==d['year'].split('-')[1]:
                    #         worksheet.write(ss,x,-d['amount'],accounting_format)
                    #         # worksheet.write(ss,x,-d[d['year']],accounting_format)                            
                    #     else:
                    #         worksheet.write(ss,x,0,accounting_format)
                    # ss+=1
                    # row = ss+1                    
                for d in dd:
                    worksheet.write(ss,0,dd[d]['data']['an_code'],contest_center)
                    worksheet.write(ss,1,dd[d]['data']['analytic_acc'],contest_center)
                    worksheet.write(ss,2,dd[d]['data']['code'],contest_center)
                    worksheet.write(ss,3,dd[d]['data']['account'],  contest_center)
                    worksheet.write(ss,4,dd[d]['data']['technic'],  contest_center)
                    ind=5
                    # for x in years:
                    if self.by_dtcr:
                        for x in range(4,16):
                            if dd[d].get(dd[d]['data']['year_year']+'-'+str(x-3)+'-c',False) or dd[d].get(dd[d]['data']['year_year']+'-'+str(x-3)+'-d',False):
                                # print ('1231 ',dd[d])
                                    # print ('1212312 ',dd[d][dd[d]['data']['year_year']+'-'+str(x-3)])
                            # if dd[d].get(dd[d]['data']['year_year'],False):                   
                            # if str(x-3)==dd[d]['data']['year'].split('-')[1]:
                                # if dd[d].get(x,False):
                                if dd[d].get(dd[d]['data']['year_year']+'-'+str(x-3)+'-d',False):
                                    worksheet.write(ss,ind,dd[d][dd[d]['data']['year_year']+'-'+str(x-3)+'-d'],accounting_format)
                                else:
                                    worksheet.write(ss,ind,0,accounting_format)
                                    
                                if dd[d].get(dd[d]['data']['year_year']+'-'+str(x-3)+'-c',False):
                                    worksheet.write(ss,ind+1,-dd[d][dd[d]['data']['year_year']+'-'+str(x-3)+'-c'],accounting_format)
                                else:
                                    worksheet.write(ss,ind+1,0,accounting_format)
                                    # worksheet.write(ss,x,-d[d['year']],accounting_format)                            
                            else:
                                    worksheet.write(ss,ind,0,accounting_format)
                                    worksheet.write(ss,ind+1,0,accounting_format)
                            # sheet.write_formula(row, 7, '{='+ xl_rowcol_to_cell(row, 6) + '-' + xl_rowcol_to_cell(row, 2) +'}', contest_right)
                            ind+=2
                        # worksheet.write_formula(ss, 17, '{sum('+ xl_rowcol_to_cell(ss, 5) + ':' + xl_rowcol_to_cell(ss, 16) +')}', contest_right)
                        worksheet.write(ss, 29, '{=SUM('+self._symbol(ss, 5) +':'+ self._symbol(ss, 28)+')}', accounting_format)
                        ss+=1
                        row = ss+1
                    else:
                        for x in range(4,16):
                            if dd[d].get(dd[d]['data']['year_year']+'-'+str(x-3),False):
                            # if dd[d].get(dd[d]['data']['year_year'],False):                   
                            # if str(x-3)==dd[d]['data']['year'].split('-')[1]:
                                # if dd[d].get(x,False):
                                    worksheet.write(ss,ind,dd[d][dd[d]['data']['year_year']+'-'+str(x-3)],accounting_format)
                                    # worksheet.write(ss,x,-d[d['year']],accounting_format)                            
                            else:
                                    worksheet.write(ss,ind,0,accounting_format)
                            # sheet.write_formula(row, 7, '{='+ xl_rowcol_to_cell(row, 6) + '-' + xl_rowcol_to_cell(row, 2) +'}', contest_right)
                            ind+=1
                        # worksheet.write_formula(ss, 17, '{sum('+ xl_rowcol_to_cell(ss, 5) + ':' + xl_rowcol_to_cell(ss, 16) +')}', contest_right)
                        worksheet.write(ss, 17, '{=SUM('+self._symbol(ss, 5) +':'+ self._symbol(ss, 16)+')}', accounting_format)
                        ss+=1
                        row = ss+1                        
                # sum_amount += item.amount
            # worksheet.write(9, 5, sum_amount, accounting_format_blue)
            
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
