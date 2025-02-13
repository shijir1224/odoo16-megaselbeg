# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, tools, api

from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
import collections
from calendar import monthrange
from io import BytesIO
import base64
import xlsxwriter
from xlsxwriter.utility import xl_rowcol_to_cell
from tempfile import NamedTemporaryFile
import os,xlrd

class mining_cost_selection(models.Model):
    _name = 'mining.cost.selection'
    _description = 'Mining cost selection'
    
    type =  fields.Selection([('year','Year'),('month','Month')], 'Төрөл', required=True)
    name = fields.Char('Нэр', required=True, size=4)

class mining_cost_report_wizard(models.TransientModel):
    _name = 'mining.cost.report.wizard'
    _description = 'Mining cost report wizard'

    # year = fields.Selection([('2018','2018'),('2019','2019'),('2020','2020')], 'Жил', required=True)
    year_ids = fields.Many2many('mining.cost.selection', 'mining_cost_selection_year_rel','report_id','sel_id', string='Жил')
    month_ids = fields.Many2many('mining.cost.selection', 'mining_cost_selection_month_rel','report_id','sel_id', string='Сар')

    def get_value(self, technic_id):
        values = {}
        # year = self.year
        cost_date_obj = self.env['mining.cost.report.date']
        for year in self.year_ids.mapped('name'):
            for month in self.month_ids.mapped('name'):
                days = monthrange(int(year),int(month))[1]
                ds = year+'-'+str(month)+'-01'
                de = year+'-'+str(month)+'-'+str(days)
                cost_ids = cost_date_obj.search([('date','>=',ds), ('date','<=',de),('technic_id','=',technic_id.id)])
                sub_v = {}
                sub_v['01'] = sum(cost_ids.mapped('fuel_amount'))
                sub_v['02'] = sum(cost_ids.mapped('selbeg_amount'))
                sub_v['03'] = sum(cost_ids.mapped('oil_amount'))
                sub_v['04'] = sum(cost_ids.mapped('dep_amount'))
                sub_v['05'] = sum(cost_ids.mapped('insurance_amount'))
                sub_v['06'] = sum(cost_ids.mapped('tax_amount'))
                sub_v['07'] = sum(cost_ids.mapped('contract_amount'))
                sub_v['14'] = sum(cost_ids.mapped('sum_m3_sur'))
                
                # sub_v['06'] = sum(cost_ids.mapped('oil_amount'))
                # sub_v['07'] = sum(cost_ids.mapped('oil_amount'))
                # sub_v['08'] = sum(cost_ids.mapped('oil_amount'))
                # sub_v['09'] = sum(cost_ids.mapped('oil_amount'))
                # sub_v['10'] = sum(cost_ids.mapped('oil_amount'))
                # sub_v['11'] = sum(cost_ids.mapped('oil_amount'))
                # sub_v['12'] = sum(cost_ids.mapped('oil_amount'))
                # sub_v['13'] = sum(cost_ids.mapped('oil_amount'))
                
                values[str(year+str(month))] = sub_v
        return values

    
    def action_view(self):
        tools.drop_view_if_exists(self._cr, 'mining_cost_report_month_config')
        self._cr.execute("""
            CREATE OR REPLACE VIEW mining_cost_report_month_config AS (
select
mcc_date.date,
mcc_date.technic_id,
sum(aml.debit-aml.credit)*max(mcc_date.percent)/100 as amount
from 
(
select generate_series(
           (mcc.date_start)::date,
           (mcc.date_end)::date,
           interval '1 day'
         )::date as date,
         mccl.technic_id,
         mcc.id as mcc_id,
         min(mcc.date_end),
         min(mcc.date_start),
         --array_agg(mccar.account_id) as account_ids,
         max(mccl."percent"/(DATE_PART('day', mcc.date_end::date) - DATE_PART('day', mcc.date_start::date) +1)) as percent
         from
      mining_cost_config as mcc 
left join mining_cost_config_line as mccl on (mcc.id=mccl.parent_id or mcc.id=mccl.parent_id2)
where mcc."type" in ('indirect_cost')
group by 1,2,3
having max(mccl."percent"/(DATE_PART('day', mcc.date_end::date) - DATE_PART('day', mcc.date_start::date) +1))>0
order by 1
) as mcc_date
left join mining_cost_config_account_account_rel as mccar on (mccar.cost_id=mcc_date.mcc_id)
left join account_move_line as aml on (aml.date=mcc_date.date and aml.account_id=mccar.account_id)
left join account_move as am on (aml.move_id=am.id)
where am.state='posted'
group by 1,2
having sum(aml.debit-aml.credit)>0
order by 1)
        """)
        

    def action_export(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(9)
        h1.set_align('center')
        h1.set_font_name('Arial')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#9ad808')
        header.set_text_wrap()
        header.set_font_name('Arial')
        
        header_wrap = workbook.add_format({'bold': 1})
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(11)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        # header_wrap.set_fg_color('#6495ED')

        contest_left = workbook.add_format({'bold': 1})
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)


        contest_left_color = workbook.add_format({'bold': 1})
        contest_left_color.set_text_wrap()
        contest_left_color.set_font_size(9)
        contest_left_color.set_align('left')
        contest_left_color.set_align('vcenter')
        contest_left_color.set_border(style=1)
        contest_left_color.set_bg_color('#C0D6ED')

        contest_left_color1 = workbook.add_format({'bold': 1})
        contest_left_color1.set_text_wrap()
        contest_left_color1.set_font_size(9)
        contest_left_color1.set_align('left')
        contest_left_color1.set_align('vcenter')
        contest_left_color1.set_border(style=1)
        contest_left_color1.set_bg_color('#E4D7B7')

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_num_format('#,##0.00')

        contest_right_per = workbook.add_format()
        contest_right_per.set_text_wrap()
        contest_right_per.set_font_size(9)
        contest_right_per.set_align('right')
        contest_right_per.set_align('vcenter')
        contest_right_per.set_border(style=1)
        contest_right_per.set_num_format('0%')


        contest_right_color = workbook.add_format()
        contest_right_color.set_text_wrap()
        contest_right_color.set_font_size(9)
        contest_right_color.set_align('right')
        contest_right_color.set_align('vcenter')
        contest_right_color.set_border(style=1)
        contest_right_color.set_num_format('#,##0.00')
        contest_right_color.set_bg_color('#C0D6ED')

        contest_right_per_color = workbook.add_format()
        contest_right_per_color.set_text_wrap()
        contest_right_per_color.set_font_size(9)
        contest_right_per_color.set_align('right')
        contest_right_per_color.set_align('vcenter')
        contest_right_per_color.set_border(style=1)
        contest_right_per_color.set_num_format('0%')
        contest_right_per_color.set_bg_color('#C0D6ED')


        contest_right_color1 = workbook.add_format()
        contest_right_color1.set_text_wrap()
        contest_right_color1.set_font_size(9)
        contest_right_color1.set_align('right')
        contest_right_color1.set_align('vcenter')
        contest_right_color1.set_border(style=1)
        contest_right_color1.set_num_format('#,##0.00')
        contest_right_color1.set_bg_color('#E4D7B7')

        contest_right_per_color1 = workbook.add_format()
        contest_right_per_color1.set_text_wrap()
        contest_right_per_color1.set_font_size(9)
        contest_right_per_color1.set_align('right')
        contest_right_per_color1.set_align('vcenter')
        contest_right_per_color1.set_border(style=1)
        contest_right_per_color1.set_num_format('0%')
        contest_right_per_color1.set_bg_color('#E4D7B7')

        contest_center = workbook.add_format()
        contest_center.set_text_wrap()
        contest_center.set_font_size(9)
        contest_center.set_align('center')
        contest_center.set_align('vcenter')
        contest_center.set_border(style=1)
        contest_center.set_font_name('Arial')

        cell_format2 = workbook.add_format({
        'border': 1,
        'align': 'right',
        'font_size':9,
        'font_name': 'Arial',
        # 'text_wrap':1,
        'num_format':'#,####0'
        })
        worksheet_bcm_cost = workbook.add_worksheet(u'BCM cost')
        
        worksheet_sum_usd = workbook.add_worksheet(u'Summary USD')
        worksheet_sum_mnt = workbook.add_worksheet(u'Summary MNT')
        
        worksheet_exca_usd = workbook.add_worksheet(u'USD EXE')
        worksheet_dump_usd = workbook.add_worksheet(u'USD truck')
        worksheet_exca = workbook.add_worksheet(u'MNTEXE')
        worksheet_dump = workbook.add_worksheet(u'MNTtruck')
        
        def get_sheet_bcm_cost(worksheet, sum_exac_ids, sum_dump_ids):
            row = 0
            value_type = {
        '00': 'Salary',
        '01': 'Fuel',
        '02': 'Spare parts',
        '03': 'Oil',
        '04': 'Depreciation',
        '05': 'Insurance',
        '06': 'TAX',
        '07': 'Contract service',
        '08': 'Sub direct Cost',
        '09': 'Indirect Cost',
        '10': 'Overhead',
        '11': 'Ancilliary equipment',
        '12': 'Sub Indirect Cost',
        '13': 'Unit digg cost'
        }
            tech_type_ids = ['Digging','Trucking','Loading']
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May','Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            merge_col = 13
            row += 1
            col = 3
            for year in self.year_ids.mapped('name'):
                for month in self.month_ids.mapped('name'):
                    worksheet.write(row-1, col, '4.36', contest_center)
                    worksheet.write(row, col, year, contest_center)
                    worksheet.write(row+1, col, months[int(month)-1], contest_center)
                    col+=1
                worksheet.write(row-1, col, '4.36', contest_center)
                worksheet.write(row, col, year, contest_center)
                worksheet.write(row+1, col, 'Average', contest_center)
                col+=1
                worksheet.write(row-1, col, '4.36', contest_center)
                worksheet.write(row, col, year, contest_center)
                worksheet.write(row+1, col, 'Percentage', contest_center)
                col+=1

            row += 2
            save_first_row = row
            for item in tech_type_ids:
                worksheet.merge_range(row, 0, row+merge_col, 1, item, contest_center)
                f_col = 2
                worksheet.write(row, f_col, value_type['00'], contest_left)
                worksheet.write(row+1, f_col, value_type['01'], contest_left)
                worksheet.write(row+2, f_col, value_type['02'], contest_left)
                worksheet.write(row+3, f_col, value_type['03'], contest_left)
                worksheet.write(row+4, f_col, value_type['04'], contest_left)
                worksheet.write(row+5, f_col, value_type['05'], contest_left)
                worksheet.write(row+6, f_col, value_type['06'], contest_left)
                worksheet.write(row+7, f_col, value_type['07'], contest_left)
                worksheet.write(row+8, f_col, value_type['08'], contest_left_color)
                worksheet.write(row+9, f_col, value_type['09'], contest_left)
                worksheet.write(row+10, f_col, value_type['10'], contest_left)
                worksheet.write(row+11, f_col, value_type['11'], contest_left)
                worksheet.write(row+12, f_col, value_type['12'], contest_left_color)
                worksheet.write(row+13, f_col, value_type['13'], contest_left_color1)
                
                
                save_merge_col = 1
                for mm in range(row,row+merge_col+1):
                    save_f_col = f_col
                    for year in self.year_ids.mapped('name'):
                        merge_save_coctest = contest_right 
                        merge_save_coctest_per = contest_right_per
                        if save_merge_col in [9]:
                            merge_save_coctest = contest_right_color
                            merge_save_coctest_per = contest_right_per_color
                            worksheet.write_formula(mm, save_f_col+len(self.month_ids)+1,'{=SUM('+xl_rowcol_to_cell(mm-8, save_f_col+len(self.month_ids)+1)+':'+xl_rowcol_to_cell(mm-1, save_f_col+len(self.month_ids)+1)+')}', merge_save_coctest)
                            # worksheet.write_formula(mm, save_f_col+len(self.month_ids)+2,'{=SUM('+xl_rowcol_to_cell(mm-8, save_f_col+len(self.month_ids)+2)+':'+xl_rowcol_to_cell(mm-1, save_f_col+len(self.month_ids)+2)+')}', merge_save_coctest_per)
                            worksheet.write_formula(mm, save_f_col+len(self.month_ids)+2,'{=('+xl_rowcol_to_cell(mm, save_f_col+len(self.month_ids)+1)+'/'+xl_rowcol_to_cell(row+merge_col, save_f_col+len(self.month_ids)+1)+')}', merge_save_coctest_per)
                        elif save_merge_col in [13]:
                            merge_save_coctest = contest_right_color
                            merge_save_coctest_per = contest_right_per_color
                            worksheet.write_formula(mm, save_f_col+len(self.month_ids)+1,'{=SUM('+xl_rowcol_to_cell(mm-4, save_f_col+len(self.month_ids)+1)+':'+xl_rowcol_to_cell(mm-1, save_f_col+len(self.month_ids)+1)+')}', merge_save_coctest)
                            # worksheet.write_formula(mm, save_f_col+len(self.month_ids)+2,'{=SUM('+xl_rowcol_to_cell(mm-4, save_f_col+len(self.month_ids)+2)+':'+xl_rowcol_to_cell(mm-1, save_f_col+len(self.month_ids)+2)+')}', merge_save_coctest_per)
                            worksheet.write_formula(mm, save_f_col+len(self.month_ids)+2,'{=('+xl_rowcol_to_cell(mm, save_f_col+len(self.month_ids)+1)+'/'+xl_rowcol_to_cell(row+merge_col, save_f_col+len(self.month_ids)+1)+')}', merge_save_coctest_per)
                        else:
                            if save_merge_col in [14]:
                                merge_save_coctest = contest_right_color1
                                merge_save_coctest_per = contest_right_per_color1
                                worksheet.write_formula(mm, save_f_col+len(self.month_ids)+2,'{=SUM('+xl_rowcol_to_cell(mm-merge_col, save_f_col+len(self.month_ids)+2)+':'+xl_rowcol_to_cell(mm-1, save_f_col+len(self.month_ids)+2)+')/2}', merge_save_coctest_per)
                                worksheet.write_formula(mm, save_f_col+len(self.month_ids)+1,'{=('+xl_rowcol_to_cell(mm-5, save_f_col+len(self.month_ids)+1)+'+'+xl_rowcol_to_cell(mm-1, save_f_col+len(self.month_ids)+1)+')}', merge_save_coctest)
                            else:
                                worksheet.write_formula(mm, save_f_col+len(self.month_ids)+2,'{=('+xl_rowcol_to_cell(mm, save_f_col+len(self.month_ids)+1)+'/'+xl_rowcol_to_cell(row+merge_col, save_f_col+len(self.month_ids)+1)+')}', merge_save_coctest_per)
                                worksheet.write_formula(mm, save_f_col+len(self.month_ids)+1,'{=AVERAGE('+xl_rowcol_to_cell(mm, save_f_col+1)+':'+xl_rowcol_to_cell(mm, save_f_col+len(self.month_ids))+')}', merge_save_coctest)

                        save_f_col += len(self.month_ids)+2
                        
                    save_merge_col+=1
                    
                save_row = row
                row+=1
                sheet_name = False
                tech_len = 0
                if item=='Digging':
                    sheet_name = "'USD EXE'!"
                    tech_len = len(sum_exac_ids)*17+5
                elif item=='Trucking':
                    sheet_name = "'USD truck'!"
                    tech_len = len(sum_dump_ids)*17+5
                s_f_col = f_col
                for year in self.year_ids.mapped('name'):
                    for month in self.month_ids.mapped('name'):
                        month = int(month)
                        rowcol = xl_rowcol_to_cell(row-1, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+2, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+1, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+4, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        
                        rowcol = xl_rowcol_to_cell(row+2, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+6, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+3, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+8, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                
                        rowcol = xl_rowcol_to_cell(row+4, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+10, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+5, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+12, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+6, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+14, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+7, f_col+month)
                        cell_val = '{=SUM('+xl_rowcol_to_cell(row-1, f_col+month)+':'+xl_rowcol_to_cell(row+6, f_col+month)+')}'
                        worksheet.write_formula(rowcol, cell_val, contest_right_color)

                        rowcol = xl_rowcol_to_cell(row+8, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+18, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+9, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+20, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+10, f_col+month)
                        if sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+22, f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+11, f_col+month)
                        cell_val = '{=SUM('+xl_rowcol_to_cell(row+8, f_col+month)+':'+xl_rowcol_to_cell(row+10, f_col+month)+')}'
                        worksheet.write_formula(rowcol, cell_val, contest_right_color)

                        rowcol = xl_rowcol_to_cell(row+12, f_col+month)
                        cell_val = '{=SUM('+xl_rowcol_to_cell(row+7, f_col+month)+'+'+xl_rowcol_to_cell(row+11, f_col+month)+')}'
                        worksheet.write_formula(rowcol, cell_val, contest_right_color1)
                    f_col+=1
                    f_col+=1
                    
                    f_col += len(self.month_ids)
                    
                row = save_row
                row += merge_col+1
                


            
                
            worksheet.freeze_panes(3, 3)
            worksheet.set_column('D:P', 13)
            worksheet.set_column('C:C', 22)
            worksheet.set_column('B:B', 7)
            return worksheet

        def get_sheet_sum(worksheet, is_usd, sum_exac_ids, sum_dump_ids):
            row = 0
            value_type = {
        '00': 'BCM Production ',
        '01': 'Salary',
        '02': 'Fuel',
        '03': 'Spare parts',
        '04': 'Oil',
        '05': 'Depreciation',
        '06': 'Insurance',
        '07': 'TAX',
        '08': 'Contract service',
        '09': 'Indirect Cost',
        '10': 'Overhead',
        '11': 'Ancilliary equipment',
        '12': 'Total',
        }
            tech_type_ids = ['Digging','Trucking','Loading']
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May','Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            merge_col = 12
            row += 1
            col = 3
            for year in self.year_ids.mapped('name'):
                for month in self.month_ids.mapped('name'):
                    if is_usd:
                        worksheet.write(row-1, col, '2000', contest_center)
                    worksheet.write(row, col, year, contest_center)
                    worksheet.write(row+1, col, months[int(month)-1], contest_center)
                    col+=1
                if is_usd:
                    worksheet.write(row-1, col, '2000', contest_center)
                worksheet.write(row, col, year, contest_center)
                worksheet.write(row+1, col, 'Total', contest_center)
                col+=1

            row += 2
            save_first_row = row
            for item in tech_type_ids:
                worksheet.merge_range(row, 0, row+merge_col, 1, item, contest_center)
                f_col = 2
                worksheet.write(row, f_col, value_type['00'], contest_left_color1)
                worksheet.write(row+1, f_col, value_type['01'], contest_left)
                worksheet.write(row+2, f_col, value_type['02'], contest_left)
                worksheet.write(row+3, f_col, value_type['03'], contest_left)
                worksheet.write(row+4, f_col, value_type['04'], contest_left)
                worksheet.write(row+5, f_col, value_type['05'], contest_left)
                worksheet.write(row+6, f_col, value_type['06'], contest_left)
                worksheet.write(row+7, f_col, value_type['07'], contest_left)
                worksheet.write(row+8, f_col, value_type['08'], contest_left)
                worksheet.write(row+9, f_col, value_type['09'], contest_left)
                worksheet.write(row+10, f_col, value_type['10'], contest_left)
                worksheet.write(row+11, f_col, value_type['11'], contest_left)
                worksheet.write(row+12, f_col, value_type['12'], contest_left_color)
                
                
                save_merge_col = 1
                for mm in range(row,row+merge_col+1):
                    save_f_col = f_col
                    for year in self.year_ids.mapped('name'):
                        merge_save_coctest = contest_right 
                        if save_merge_col in [1]:
                            merge_save_coctest = contest_right_color1
                        elif save_merge_col in [13]:
                            merge_save_coctest = contest_right_color
                        
                        worksheet.write_formula(mm, save_f_col+len(self.month_ids)+1,'{=SUM('+xl_rowcol_to_cell(mm, save_f_col+1)+':'+xl_rowcol_to_cell(mm, save_f_col+len(self.month_ids))+')}', merge_save_coctest)
                        save_f_col += len(self.month_ids)+1
                    save_merge_col+=1

                save_row = row
                row+=1
                sheet_name = False
                tech_len = 0
                if item=='Digging':
                    sheet_name = 'MNTEXE!'
                    tech_len = len(sum_exac_ids)*16+12
                elif item=='Trucking':
                    sheet_name = 'MNTtruck!'
                    tech_len = len(sum_dump_ids)*16+12+22
                s_f_col = f_col
                for year in self.year_ids.mapped('name'):
                    for month in self.month_ids.mapped('name'):
                        month = int(month)
                        rowcol = xl_rowcol_to_cell(row-1, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+26, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right_color1)

                        rowcol = xl_rowcol_to_cell(row, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        
                        rowcol = xl_rowcol_to_cell(row+1, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+2, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+2, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+4, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+3, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+6, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+4, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+8, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # 
                        rowcol = xl_rowcol_to_cell(row+5, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+10, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+6, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+12, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+7, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+14, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)


                        # other 
                        rowcol = xl_rowcol_to_cell(row+8, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+18, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+9, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+20, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+10, f_col+month)
                        if is_usd:
                            cell_val = "='"+is_usd+"'!"+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month)
                        elif sheet_name:
                            cell_val = '='+sheet_name+xl_rowcol_to_cell(tech_len+22, s_f_col+month)
                        else:
                            cell_val = ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)

                        rowcol = xl_rowcol_to_cell(row+11, f_col+month)
                        cell_val = '=SUM('+xl_rowcol_to_cell(row, f_col+month)+':'+xl_rowcol_to_cell(row+10, f_col+month)+')'
                        worksheet.write_formula(rowcol, cell_val, contest_right_color)

                    f_col+=1
                    s_f_col+=2
                    
                    f_col += len(self.month_ids)
                    s_f_col += len(self.month_ids)
                row = save_row
                row += merge_col+1
                


            
                
            worksheet.freeze_panes(3, 3)
            worksheet.set_column('D:P', 13)
            worksheet.set_column('C:C', 22)
            worksheet.set_column('B:B', 7)
            return worksheet
        
       
        def get_sheet(worksheet, tech_ids, sheet_name=False):
            row = 0
            value_type = {
        '00': 'Salary',
        '01': 'Fuel',
        '02': 'Spare parts',
        '03': 'Oil',
        '04': 'Depreciation',
        '05': 'Insurance',
        '06': 'TAX',
        '07': 'Contract service',
        '08': 'Subtotal direct expences',
        '09': 'BCM  direct unit cost',
        '10': 'Indirect Cost',
        '11': 'Overhead',
        '12': 'Ancilliary equipment',
        '13': 'Subtotal indirect expences',
        '14': 'Total per month',
        '15': 'BCM Quantity',
        '16': 'unit BCM total cost'
        }
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May','Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            merge_col = 16
            row += 1
            col = 3
            for year in self.year_ids.mapped('name'):
                for month in self.month_ids.mapped('name'):
                    if sheet_name:
                        worksheet.write(row-1, col, '2000', contest_center)
                    worksheet.write(row, col, year, contest_center)
                    worksheet.write(row+1, col, months[int(month)-1], contest_center)
                    col+=1
                if sheet_name:
                    worksheet.write(row-1, col, '2000', contest_center)
                worksheet.write(row, col, year, contest_center)
                worksheet.write(row+1, col, 'Total', contest_center)
                col+=1
                if sheet_name:
                    worksheet.write(row-1, col, '2000', contest_center)
                worksheet.write(row, col, year, contest_center)
                worksheet.write(row+1, col, '%', contest_center)
                col+=1

            row += 2
            save_first_row = row
            for item in tech_ids:
                worksheet.merge_range(row, 0, row+merge_col, 0, item.park_number, contest_center)
                values = self.get_value(item)
                f_col = 2
                worksheet.write(row, f_col, value_type['00'], contest_left)
                worksheet.write(row+1, f_col, value_type['01'], contest_left)
                worksheet.write(row+2, f_col, value_type['02'], contest_left)
                worksheet.write(row+3, f_col, value_type['03'], contest_left)
                worksheet.write(row+4, f_col, value_type['04'], contest_left)
                worksheet.write(row+5, f_col, value_type['05'], contest_left)
                worksheet.write(row+6, f_col, value_type['06'], contest_left)
                worksheet.write(row+7, f_col, value_type['07'], contest_left)
                worksheet.write(row+8, f_col, value_type['08'], contest_left_color)
                worksheet.write(row+9, f_col, value_type['09'], contest_left_color1)
                worksheet.write(row+10, f_col, value_type['10'], contest_left)
                worksheet.write(row+11, f_col, value_type['11'], contest_left)
                worksheet.write(row+12, f_col, value_type['12'], contest_left)
                worksheet.write(row+13, f_col, value_type['13'], contest_left_color)
                worksheet.write(row+14, f_col, value_type['14'], contest_left)
                worksheet.write(row+15, f_col, value_type['15'], contest_left)
                worksheet.write(row+16, f_col, value_type['16'], contest_left_color1)
                
                save_merge_col = 1
                for mm in range(row,row+merge_col+1):
                    worksheet.write(mm, f_col-1, item.program_code, contest_left)
                    save_f_col = f_col
                    for year in self.year_ids.mapped('name'):
                        merge_save_coctest = contest_right 
                        if save_merge_col in [9,14]:
                            merge_save_coctest = contest_right_color
                        
                        worksheet.write_formula(mm, save_f_col+len(self.month_ids)+1,'{=SUM('+xl_rowcol_to_cell(mm, save_f_col+1)+':'+xl_rowcol_to_cell(mm, save_f_col+len(self.month_ids))+')}', merge_save_coctest)
                        save_f_col += len(self.month_ids)+2
                    save_merge_col+=1

                save_row = row
                row+=1
                for year in self.year_ids.mapped('name'):
                    for month in self.month_ids.mapped('name'):
                        index_year_month = year+month
                        month = int(month)
                        rowcol = xl_rowcol_to_cell(row-1, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        
                        f1 = values[str(index_year_month)]['01']
                        rowcol = xl_rowcol_to_cell(row, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else str(f1)
                        # worksheet.write(rowcol, cell_val, contest_right)
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        f1 = values[str(index_year_month)]['02']
                        rowcol = xl_rowcol_to_cell(row+1, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else str(f1)
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+1, f_col+month, f1, contest_right)
                        f1 = values[str(index_year_month)]['03']
                        rowcol = xl_rowcol_to_cell(row+2, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else str(f1)
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+2, f_col+month, f1, contest_right)
                        f1 = values[str(index_year_month)]['04']
                        rowcol = xl_rowcol_to_cell(row+3, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else str(f1)
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+3, f_col+month, f1, contest_right)
                        f1 = values[str(index_year_month)]['05']
                        rowcol = xl_rowcol_to_cell(row+4, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else str(f1)
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+4, f_col+month, f1, contest_right)
                        f1 = values[str(index_year_month)]['06']
                        rowcol = xl_rowcol_to_cell(row+5, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else str(f1)
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+5, f_col+month, f1, contest_right)
                        f1 = values[str(index_year_month)]['07']
                        rowcol = xl_rowcol_to_cell(row+6, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else str(f1)
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+6, f_col+month, f1, contest_right)
                        rowcol = xl_rowcol_to_cell(row+7, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else '{=SUM('+xl_rowcol_to_cell(row-1, f_col+month)+':'+xl_rowcol_to_cell(row+6, f_col+month)+')}'
                        worksheet.write_formula(rowcol, cell_val, contest_right_color)
                        # worksheet.write_formula(row+7, f_col+month,, contest_right_color)
                        rowcol = xl_rowcol_to_cell(row+8, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+7, f_col+month)+'/'+xl_rowcol_to_cell(row+14, f_col+month)+'),0)}'
                        worksheet.write_formula(rowcol, cell_val, contest_right_color1)
                        # worksheet.write_formula(row+8, f_col+month,, contest_right_color1)
                        rowcol = xl_rowcol_to_cell(row+9, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+9, f_col+month, '', contest_right)
                        rowcol = xl_rowcol_to_cell(row+10, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+10, f_col+month, '', contest_right)
                        rowcol = xl_rowcol_to_cell(row+11, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else ''
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+11, f_col+month, '', contest_right)
                        rowcol = xl_rowcol_to_cell(row+12, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else '{=SUM('+xl_rowcol_to_cell(row+9, f_col+month)+':'+xl_rowcol_to_cell(row+11, f_col+month)+')}'
                        worksheet.write_formula(rowcol, cell_val, contest_right_color)
                        # worksheet.write_formula(row+12, f_col+month,'{=SUM('+xl_rowcol_to_cell(row+9, f_col+month)+':'+xl_rowcol_to_cell(row+11, f_col+month)+')}', contest_right_color)
                        rowcol = xl_rowcol_to_cell(row+13, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else '{=('+xl_rowcol_to_cell(row+7, f_col+month)+'+'+xl_rowcol_to_cell(row+12, f_col+month)+')}'
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write_formula(row+13, f_col+month,'{=('+xl_rowcol_to_cell(row+7, f_col+month)+'+'+xl_rowcol_to_cell(row+12, f_col+month)+')}', contest_right)
                        f1 = values[str(index_year_month)]['14']
                        rowcol = xl_rowcol_to_cell(row+14, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else str(f1)
                        worksheet.write_formula(rowcol, cell_val, contest_right)
                        # worksheet.write(row+14, f_col+month, f1, contest_right)
                        rowcol = xl_rowcol_to_cell(row+15, f_col+month)
                        cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+13, f_col+month)+'/'+xl_rowcol_to_cell(row+14, f_col+month)+'),0)}'
                        worksheet.write_formula(rowcol, cell_val, contest_right_color1)
                        # worksheet.write_formula(row+15, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+13, f_col+month)+'/'+xl_rowcol_to_cell(row+14, f_col+month)+'),0)}', contest_right_color1)
                    
                    f_col+=1
                    month = len(self.month_ids)
                    worksheet.write_formula(row+8, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+7, f_col+month)+'/'+xl_rowcol_to_cell(row+14, f_col+month)+'),0)}', contest_right_color1)
                    worksheet.write_formula(row+15, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+13, f_col+month)+'/'+xl_rowcol_to_cell(row+14, f_col+month)+'),0)}', contest_right_color1)
                    
                    f_col+=1
                    worksheet.write_formula(row-1, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row-1, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+1, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+1, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+2, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+2, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+3, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+3, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+4, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+4, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+5, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+5, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+6, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+6, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+7, f_col+month,'{=SUM('+xl_rowcol_to_cell(row-1, f_col+month)+':'+xl_rowcol_to_cell(row+6, f_col+month)+')}', contest_right_per_color)
                    worksheet.write(row+8, f_col+month, '', contest_right_per_color1)
                    worksheet.write_formula(row+9, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+9, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+10, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+10, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+11, f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+11, f_col+month-1)+'/'+xl_rowcol_to_cell(row+13, f_col+month-1)+'),0)}', contest_right_per)
                    worksheet.write_formula(row+12, f_col+month,'{=SUM('+xl_rowcol_to_cell(row+9, f_col+month)+':'+xl_rowcol_to_cell(row+11, f_col+month)+')}', contest_right_per_color)
                    worksheet.write_formula(row+13, f_col+month,'{=('+xl_rowcol_to_cell(row+7, f_col+month)+'+'+xl_rowcol_to_cell(row+12, f_col+month)+')}', contest_right_per)
                    worksheet.write(row+14, f_col+month, '', contest_right_per)
                    worksheet.write(row+15, f_col+month, '', contest_right_per_color1)
                    
                    f_col += len(self.month_ids)

                row = save_row
                row += merge_col+1

            value_type = {
                '00': 'Salary',
                '01': 'BCM cost Salary',
                '02': 'Fuel',
                '03': 'BCM cost Fuel',
                '04': 'Maintenance',
                '05': 'BCM cost Maintenance',
                '06': 'Oil',
                '07': 'BCM cost Oil',
                '08': 'Depreciation',
                '09': 'BCM cost Dep',
                '10': 'Insurance',
                '11': 'BCM cost Insurance',
                '12': 'TAX',
                '13': 'BCM cost TAX',
                '14': 'Contract service',
                '15': 'BCM cost Contract',
                '16': 'Subtotal direct expences',
                '17': 'Operational cost',
                '18': 'Indirect Salary & accomdation',
                '19': 'BCM cost Indirect Sal&Accom',
                '20': 'Other overhead expences',
                '21': 'BCM cost Overhead',
                '22': 'Ancilliary equipment',
                '23': 'BCM cost Ancilliary',
                '24': 'Subtotal indirect expences',
                '25': 'Total cost',
                '26': 'BCM Quantity',
                '27': 'BCM unit cost',
            }

            f_col = 2
            row += 1
            merge_col = 27
            worksheet.merge_range(row, 0, row+merge_col, 1, 'check', contest_center)
            worksheet.write(row, f_col, value_type['00'], contest_left)
            worksheet.write(row+1, f_col, value_type['01'], contest_left)
            worksheet.write(row+2, f_col, value_type['02'], contest_left)
            worksheet.write(row+3, f_col, value_type['03'], contest_left)
            worksheet.write(row+4, f_col, value_type['04'], contest_left)
            worksheet.write(row+5, f_col, value_type['05'], contest_left)
            worksheet.write(row+6, f_col, value_type['06'], contest_left)
            worksheet.write(row+7, f_col, value_type['07'], contest_left)
            worksheet.write(row+8, f_col, value_type['08'], contest_left)
            worksheet.write(row+9, f_col, value_type['09'], contest_left)
            worksheet.write(row+10, f_col, value_type['10'], contest_left)
            worksheet.write(row+11, f_col, value_type['11'], contest_left)
            worksheet.write(row+12, f_col, value_type['12'], contest_left)
            worksheet.write(row+13, f_col, value_type['13'], contest_left)
            worksheet.write(row+14, f_col, value_type['14'], contest_left)
            worksheet.write(row+15, f_col, value_type['15'], contest_left)
            worksheet.write(row+16, f_col, value_type['16'], contest_left_color)
            worksheet.write(row+17, f_col, value_type['17'], contest_left_color1)
            worksheet.write(row+18, f_col, value_type['18'], contest_left)
            worksheet.write(row+19, f_col, value_type['19'], contest_left)
            worksheet.write(row+20, f_col, value_type['20'], contest_left)
            worksheet.write(row+21, f_col, value_type['21'], contest_left)
            worksheet.write(row+22, f_col, value_type['22'], contest_left)
            worksheet.write(row+23, f_col, value_type['23'], contest_left)
            worksheet.write(row+24, f_col, value_type['24'], contest_left_color)
            worksheet.write(row+25, f_col, value_type['25'], contest_left)
            worksheet.write(row+26, f_col, value_type['26'], contest_left)
            worksheet.write(row+27, f_col, value_type['27'], contest_left_color1)
            
            # row
            s_f_col = f_col
            for year in range(0,len(self.year_ids)):
                for month in range(1,len(self.month_ids)+2):
                    sum_salary = []
                    sum_fuel = []
                    sum_part = []
                    sum_oil = []
                    sum_dep = []
                    sum_ins = []
                    sum_tax = []
                    sum_cont = []
                    sum_ind = []
                    sum_over = []
                    sum_ans = []
                    sum_total = []
                    s_row = save_first_row
                    for tech in range(0,len(tech_ids)):
                        sum_salary.append(xl_rowcol_to_cell(s_row, s_f_col+month))
                        sum_fuel.append(xl_rowcol_to_cell(s_row+1, s_f_col+month))
                        sum_part.append(xl_rowcol_to_cell(s_row+2, s_f_col+month))
                        sum_oil.append(xl_rowcol_to_cell(s_row+3, s_f_col+month))
                        sum_dep.append(xl_rowcol_to_cell(s_row+4, s_f_col+month))
                        sum_ins.append(xl_rowcol_to_cell(s_row+5, s_f_col+month))
                        sum_tax.append(xl_rowcol_to_cell(s_row+6, s_f_col+month))
                        sum_cont.append(xl_rowcol_to_cell(s_row+7, s_f_col+month))
                        
                        sum_ind.append(xl_rowcol_to_cell(s_row+10, s_f_col+month))
                        sum_over.append(xl_rowcol_to_cell(s_row+11, s_f_col+month))
                        sum_ans.append(xl_rowcol_to_cell(s_row+12, s_f_col+month))
                        sum_total.append(xl_rowcol_to_cell(s_row+15, s_f_col+month))

                        s_row += 17
                    rowcol = xl_rowcol_to_cell(row, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_salary)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+2, s_f_col+month,'{=IFERROR(('+'+'.join(sum_salary)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+1, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+1, s_f_col+month, '{=IFERROR(('+xl_rowcol_to_cell(row, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+2, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_fuel)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+2, s_f_col+month,'{=IFERROR(('+'+'.join(sum_fuel)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+3, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+2, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+3, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+2, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+4, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_part)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+4, s_f_col+month,'{=IFERROR(('+'+'.join(sum_part)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+5, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+4, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+5, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+4, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+6, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_oil)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+6, s_f_col+month,'{=IFERROR(('+'+'.join(sum_oil)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+7, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+6, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+7, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+6, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+8, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_dep)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+8, s_f_col+month,'{=IFERROR(('+'+'.join(sum_dep)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+9, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+8, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+9, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+8, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+10, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_ins)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+10, s_f_col+month,'{=IFERROR(('+'+'.join(sum_ins)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+11, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+10, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+11, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+10, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+12, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_tax)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+12, s_f_col+month,'{=IFERROR(('+'+'.join(sum_tax)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+13, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+12, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+13, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+12, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+14, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_cont)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+14, s_f_col+month,'{=IFERROR(('+'+'.join(sum_cont)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+15, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+14, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+15, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+14, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    
                    sub_direct_ex = [xl_rowcol_to_cell(row, s_f_col+month),
                    xl_rowcol_to_cell(row+2, s_f_col+month),
                    xl_rowcol_to_cell(row+4, s_f_col+month),
                    xl_rowcol_to_cell(row+6, s_f_col+month),
                    xl_rowcol_to_cell(row+8, s_f_col+month),
                    xl_rowcol_to_cell(row+10, s_f_col+month),
                    xl_rowcol_to_cell(row+12, s_f_col+month),
                    xl_rowcol_to_cell(row+14, s_f_col+month)]
                    rowcol = xl_rowcol_to_cell(row+16, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sub_direct_ex)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right_color)
                    # worksheet.write_formula(row+16, s_f_col+month,'{=IFERROR(('+'+'.join(sub_direct_ex)+'),0)}', contest_right_color)
                    rowcol = xl_rowcol_to_cell(row+17, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+16, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right_color1)
                    # worksheet.write_formula(row+17, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+16, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right_color1)
                    
                    rowcol = xl_rowcol_to_cell(row+18, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_ind)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+18, s_f_col+month,'{=IFERROR(('+'+'.join(sum_ind)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+19, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+18, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+19, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+18, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+20, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_over)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+20, s_f_col+month,'{=IFERROR(('+'+'.join(sum_over)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+21, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+20, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+21, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+20, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+22, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sum_ans)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+22, s_f_col+month,'{=IFERROR(('+'+'.join(sum_ans)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+23, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+22, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+23, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+22, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right)
                    
                    sub_indirect_ex = [
                    xl_rowcol_to_cell(row+18, s_f_col+month),
                    xl_rowcol_to_cell(row+20, s_f_col+month),
                    xl_rowcol_to_cell(row+22, s_f_col+month),
                    ]
                    rowcol = xl_rowcol_to_cell(row+24, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(sub_indirect_ex)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right_color)
                    # worksheet.write_formula(row+24, s_f_col+month,'{=IFERROR(('+'+'.join(sub_indirect_ex)+'),0)}', contest_right_color)
                    
                    total_cost = [
                    xl_rowcol_to_cell(row+16, s_f_col+month),
                    xl_rowcol_to_cell(row+24, s_f_col+month),
                    ]
                    rowcol = xl_rowcol_to_cell(row+25, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+'+'.join(total_cost)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+25, s_f_col+month,'{=IFERROR(('+'+'.join(total_cost)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+26, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol if sheet_name else '{=IFERROR(('+'+'.join(sum_total)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right)
                    # worksheet.write_formula(row+26, s_f_col+month,'{=IFERROR(('+'+'.join(sum_total)+'),0)}', contest_right)
                    rowcol = xl_rowcol_to_cell(row+27, s_f_col+month)
                    cell_val = '='+sheet_name+rowcol+'/'+xl_rowcol_to_cell(0, s_f_col+month) if sheet_name else '{=IFERROR(('+xl_rowcol_to_cell(row+25, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}'
                    worksheet.write_formula(rowcol, cell_val, contest_right_color1)
                    # worksheet.write_formula(row+27, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+25, s_f_col+month)+'/'+xl_rowcol_to_cell(row+26, s_f_col+month)+'),0)}', contest_right_color1)
                    
                s_f_col+=1
                worksheet.write_formula(row, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+1, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+2, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+2, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+3, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+4, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+4, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+5, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+6, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+6, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+7, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+8, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+8, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+9, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+10, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+10, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+11, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+12, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+12, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+13, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+14, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+14, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+15, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+16, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+16, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per_color)
                worksheet.write(row+17, s_f_col+month, '', contest_right_per_color1)
                worksheet.write_formula(row+18, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+18, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+19, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+20, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+20, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+21, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+22, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+22, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per)
                worksheet.write(row+23, s_f_col+month, '', contest_right_per)
                worksheet.write_formula(row+24, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+24, s_f_col+month-1)+'/'+xl_rowcol_to_cell(row+25, s_f_col+month-1)+'),0)}', contest_right_per_color)
                worksheet.write_formula(row+25, s_f_col+month,'{=IFERROR(('+xl_rowcol_to_cell(row+16, s_f_col+month)+'+'+xl_rowcol_to_cell(row+24, s_f_col+month)+'),0)}', contest_right_per)
                worksheet.write(row+26, s_f_col+month, '', contest_right_per)
                worksheet.write(row+27, s_f_col+month, '', contest_right_per_color1)

                s_f_col += len(self.month_ids)+1
                
            worksheet.freeze_panes(3, 3)
            worksheet.set_column('D:P', 13)
            worksheet.set_column('C:C', 22)
            worksheet.set_column('B:B', 7)
            return worksheet

        cost_date_obj = self.env['mining.cost.report.date']
        technic_obj = self.env['technic.equipment']
        # date_start = self.year+'-01-01'
        # date_end = self.year+'-12-31'
        technic_ids = []
        for year in self.year_ids.mapped('name'):
            for month in self.month_ids.mapped('name'):
                days = monthrange(int(year),int(month))[1]
                ds = year+'-'+str(month)+'-01'
                de = year+'-'+str(month)+'-'+str(days)
                technic_ids += cost_date_obj.search([('date','>=',ds), ('date','<=',de), ('technic_id.owner_type','in',['own_asset'])]).mapped('technic_id').ids
        
        # technic_ids = list(set(technic_ids))

        exca_type = ['excavator']
        dump_type = ['dump']
        
        exac_ids = technic_obj.search([('id','in',technic_ids), ('technic_type','in',exca_type)], order='report_order desc')
        dump_ids = technic_obj.search([('id','in',technic_ids), ('technic_type','in',dump_type)], order='report_order desc')
        
        worksheet_exca = get_sheet(worksheet_exca, exac_ids)
        worksheet_dump = get_sheet(worksheet_dump, dump_ids)
        worksheet_exca_usd = get_sheet(worksheet_exca_usd, exac_ids, 'MNTEXE!')
        worksheet_dump_usd = get_sheet(worksheet_dump_usd, dump_ids, 'MNTtruck!')
        worksheet_sum_mnt = get_sheet_sum(worksheet_sum_mnt, False, exac_ids, dump_ids)
        worksheet_sum_usd = get_sheet_sum(worksheet_sum_usd, 'Summary MNT', exac_ids, dump_ids)
        worksheet_bcm_cost = get_sheet_bcm_cost(worksheet_bcm_cost, exac_ids, dump_ids)
        

        

        workbook.close()

        out = base64.encodebytes(output.getvalue())
        file_name = 'BCM Year '+', '.join(self.year_ids.mapped('name'))+' Month '+', '.join(self.month_ids.mapped('name'))+'.xlsx'
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }