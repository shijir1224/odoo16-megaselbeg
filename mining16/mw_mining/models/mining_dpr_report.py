

# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules, _
from odoo.addons import decimal_precision as dp
from datetime import datetime, time, timedelta
import calendar
from io import BytesIO
from io import StringIO
import base64
import pdfkit
# import imgkit
from xlsxwriter.utility import xl_rowcol_to_cell
import xlsxwriter
from tempfile import NamedTemporaryFile
import os,xlrd
from odoo.exceptions import UserError, ValidationError
import pytz
from odoo.tools.float_utils import float_is_zero
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
import calendar

class mining_dpr_report(models.TransientModel):
    _name = 'mining.dpr.report'
    _description = 'mining dpr report'
    
    date = fields.Date('Date', default=fields.Date.context_today, required=True)
    # end_date = fields.Date('End date', default=fields.Date.context_today, required=True)
    branch_id = fields.Many2one('res.branch', string='Branch', required=True)
    branch_ids = fields.Many2many('res.branch', string='Branchs')

    def get_exac_ids(self):
        technic_ids = self.env['technic.equipment'].search([
        ('technic_type','in',['excavator','loader']),
        ('branch_id','=',self.branch_id.id),
        ('is_tbb_mining','=',True),
        ])
        return technic_ids

        # dom = [('branch_id','=',self.branch_id.id),('date','=',self.date)]
        # excas = self.env['mining.production.report'].search(dom).mapped('excavator_id')
        # technic_ids = self.env['technic.equipment'].search([
        # ('technic_type','in',['excavator','loader']),
        # ('branch_id','=',self.branch_id.id),
        # ('is_tbb_mining','=',True),
        # ('id','not in', excas.ids)
        # ])+excas
        # return technic_ids
    def get_dump_ids(self, sett):
        technic_ids = self.env['technic.equipment'].search([
        ('technic_type','in',['dump']),
        ('branch_id','=',self.branch_id.id),
        ('technic_setting_id','=',sett.id),
        ('is_tbb_mining','=',True),
        ])
        return technic_ids

        # dom = [('branch_id','=',self.branch_id.id),('date','=',self.date),('dump_id.technic_setting_id','=',sett.id)]
        # dumps = self.env['mining.production.report'].search(dom).mapped('dump_id')
        # technic_ids = self.env['technic.equipment'].search([
        # ('technic_type','in',['dump']),
        # ('branch_id','=',self.branch_id.id),
        # ('technic_setting_id','=',sett.id),
        # ('is_tbb_mining','=',True),
        # ('id','not in', dumps.ids)
        # ])+dumps
        # return technic_ids

    def get_week_date(self, week_hed):
        c = calendar.Calendar()
        w = 1
        s_date = False
        e_date = False
        for weeks in c.monthdayscalendar(self.date.year, self.date.month):
            # print(weeks)
            # X = [0,5,0,0,3,1,15,0,12]
            weeks = [i for i in weeks if i != 0]
            if w==week_hed:
                s_date = str(self.date.year)+'-'+str(self.date.month).zfill(2)+'-'+str(weeks[0]).zfill(2)
                e_date = str(self.date.year)+'-'+str(self.date.month).zfill(2)+'-'+str(weeks[len(weeks)-1]).zfill(2)
                return s_date,e_date
                # for item in weeks:
                #     if item!=0:
                    
            w += 1
        return s_date,e_date

    def get_but(self, reps, m_type, s_date=False, e_date=False, week_hed=False, map_sum=False):
        if s_date and e_date:
            s_date = str(s_date)[0:10]
            e_date = str(e_date)[0:10]
            if m_type:
                if map_sum == 'sum_m3':
                    sum_dun = sum(reps.filtered(lambda r: r.material_id.mining_product_type==m_type and (r.material_id.is_productivity==True or r.material_id.mining_product_type=='engineering_work') and str(r.date)>=str(s_date) and str(r.date)<=str(e_date)).mapped(map_sum))
                else:
                    sum_dun = sum(reps.filtered(lambda r: r.material_id.mining_product_type==m_type and str(r.date)>=str(s_date) and str(r.date)<=str(e_date)).mapped(map_sum))
            else:
                if map_sum == 'sum_m3':
                    sum_dun = sum(reps.filtered(lambda r: (r.material_id.is_productivity==True or r.material_id.mining_product_type=='engineering_work') and str(r.date)>=str(s_date) and str(r.date)<=str(e_date)).mapped(map_sum))
                else:
                    sum_dun = sum(reps.filtered(lambda r: str(r.date)>=str(s_date) and str(r.date)<=str(e_date)).mapped(map_sum))
        else:
            date = str(self.date)
            month_start = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-01',  '%Y-%m-%d').date()
            m_end_day = calendar.monthrange(self.date.year, self.date.month)[1]
            month_end = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-'+str(calendar.monthrange(self.date.year, self.date.month)[1]),  '%Y-%m-%d').date()
            month_start_week = month_start + relativedelta(weeks=week_hed-1)
            month_end_week = month_start + relativedelta(weeks=week_hed)
            
            
            s_date, e_date = self.get_week_date(week_hed)
            # s_date = str(month_start_week)[0:10]
            # e_date = str(month_end_week)[0:10]
            real_date = str(month_end)[0:10]

            print ('==========================s_date',s_date, '************',e_date)
            # print (blblbl)
            if m_type:
                if map_sum == 'sum_m3':
                    sum_dun = sum(reps.filtered(lambda r: r.material_id.mining_product_type==m_type and (r.material_id.is_productivity==True or r.material_id.mining_product_type=='engineering_work') and str(r.date)>=str(s_date) and str(r.date)<=str(e_date) and str(r.date)<=str(real_date)).mapped(map_sum))
                else:
                    sum_dun = sum(reps.filtered(lambda r: r.material_id.mining_product_type==m_type and str(r.date)>=str(s_date) and str(r.date)<=str(e_date) and str(r.date)<=str(real_date)).mapped(map_sum))
            else:
                if map_sum == 'sum_m3':
                    sum_dun = sum(reps.filtered(lambda r: (r.material_id.is_productivity==True or r.material_id.mining_product_type=='engineering_work') and str(r.date)>=str(s_date) and str(r.date)<=str(e_date) and str(r.date)<=str(real_date)).mapped(map_sum))
                else:
                    sum_dun = sum(reps.filtered(lambda r: str(r.date)>=str(s_date) and str(r.date)<=str(e_date) and str(r.date)<=str(real_date)).mapped(map_sum))
        return sum_dun
    
    def get_dom(self, exca_dump_ids, is_dump=False):
        date = str(self.date)
        month_start = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-01',  '%Y-%m-%d').date()
        m_end_day = calendar.monthrange(self.date.year, self.date.month)[1]
        month_end = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-'+str(calendar.monthrange(self.date.year, self.date.month)[1]),  '%Y-%m-%d').date()
        domain_plan = [('branch_id','=',self.branch_id.id),('date','>=',month_start),('date','<=',month_end)]
        if type(exca_dump_ids) != list:
            exca_dump_ids = exca_dump_ids.ids

        if is_dump:
            domain_plan+=[('dump_id','in',exca_dump_ids)]
        else:
            domain_plan+=[('excavator_id','in',exca_dump_ids)]
        print ('exca_dump_ids',exca_dump_ids)
        return domain_plan
    
    def get_buteel(self, exca_dump_ids, dump=False):
        date = str(self.date)
        month_start = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-01',  '%Y-%m-%d')
        m_end_day = calendar.monthrange(self.date.year, self.date.month)[1]
        month_end = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-'+str(m_end_day),  '%Y-%m-%d')
        domain_plan = self.get_dom(exca_dump_ids, dump)
        plans = self.env['mining.production.report'].search(domain_plan)
        
        eng = self.get_but(plans,'engineering_work',date, date, False, 'sum_m3')
        eng_plan = self.get_but(plans,'engineering_work',date, date, False, 'sum_m3_plan')
        eng_w1 = self.get_but(plans,'engineering_work', False,False, 1, 'sum_m3')
        eng_w2 = self.get_but(plans,'engineering_work', False,False, 2, 'sum_m3')
        eng_w3 = self.get_but(plans,'engineering_work', False,False, 3, 'sum_m3')
        eng_w4 = self.get_but(plans,'engineering_work', False,False, 4, 'sum_m3')
        eng_w5 = self.get_but(plans,'engineering_work', False,False, 5, 'sum_m3')
        eng_sariin_ehnees= self.get_but(plans,'engineering_work',month_start, date, False, 'sum_m3')
        eng_plan_ehnees= self.get_but(plans,'engineering_work', month_start,date, False, 'sum_m3_plan')
        eng_plan_sar = self.get_but(plans,'engineering_work',month_start,month_end, False, 'sum_m3_plan')

        mineral = self.get_but(plans,'mineral',date, date, False, 'sum_m3')
        mineral_plan = self.get_but(plans,'mineral',date, date, False, 'sum_m3_plan')
        mineral_w1 = self.get_but(plans,'mineral', False,False, 1, 'sum_m3')
        mineral_w2 = self.get_but(plans,'mineral', False,False, 2, 'sum_m3')
        mineral_w3 = self.get_but(plans,'mineral', False,False, 3, 'sum_m3')
        mineral_w4 = self.get_but(plans,'mineral', False,False, 4, 'sum_m3')
        mineral_w5 = self.get_but(plans,'mineral', False,False, 5, 'sum_m3')
        mineral_sariin_ehnees= self.get_but(plans,'mineral',month_start, date, False, 'sum_m3')
        mineral_plan_ehnees= self.get_but(plans,'mineral', month_start,date, False, 'sum_m3_plan')
        mineral_plan_sar = self.get_but(plans,'mineral',month_start,month_end, False, 'sum_m3_plan')

        soil = self.get_but(plans,'soil',date, date, False, 'sum_m3')
        soil_plan = self.get_but(plans,'soil',date, date, False, 'sum_m3_plan')
        soil_w1 = self.get_but(plans,'soil', False,False, 1, 'sum_m3')
        soil_w2 = self.get_but(plans,'soil', False,False, 2, 'sum_m3')
        soil_w3 = self.get_but(plans,'soil', False,False, 3, 'sum_m3')
        soil_w4 = self.get_but(plans,'soil', False,False, 4, 'sum_m3')
        soil_w5 = self.get_but(plans,'soil', False,False, 5, 'sum_m3')
        soil_sariin_ehnees= self.get_but(plans,'soil',month_start, date, False, 'sum_m3')
        soil_plan_ehnees= self.get_but(plans,'soil', month_start,date, False, 'sum_m3_plan')
        soil_plan_sar = self.get_but(plans,'soil',month_start,month_end, False, 'sum_m3_plan')

        print ('eng_w1+mineral_w1+soil_w1--------',eng_w1,mineral_w1,soil_w1,'  aaallll ',eng_w1+mineral_w1+soil_w1)
        return {
            'eng_sariin_ehnees':self.get_hum(eng_sariin_ehnees),
            'eng_plan_ehnees': self.get_hum(eng_plan_ehnees),
            'eng_plan_sar': self.get_hum(eng_plan_sar),
            'mineral_sariin_ehnees': self.get_hum(mineral_sariin_ehnees),
            'mineral_plan_ehnees': self.get_hum(mineral_plan_ehnees),
            'mineral_plan_sar': self.get_hum(mineral_plan_sar),
            'soil_sariin_ehnees': self.get_hum(soil_sariin_ehnees),
            'soil_plan_ehnees': self.get_hum(soil_plan_ehnees),
            'soil_plan_sar':self.get_hum(soil_plan_sar),
            'eng_plan': self.get_hum(eng_plan), 
            'mineral_plan': self.get_hum(mineral_plan),
            'soil_plan': self.get_hum(soil_plan), 
            'eng': self.get_hum(eng), 
            'mineral': self.get_hum(mineral),
            'soil': self.get_hum(soil), 
            'eng_w1': self.get_hum(eng_w1),
            'eng_w2': self.get_hum(eng_w2),
            'eng_w3': self.get_hum(eng_w3),
            'eng_w4': self.get_hum(eng_w4),
            'eng_w5': self.get_hum(eng_w5),
            'mineral_w1': self.get_hum(mineral_w1),
            'mineral_w2': self.get_hum(mineral_w2),
            'mineral_w3': self.get_hum(mineral_w3),
            'mineral_w4': self.get_hum(mineral_w4),
            'mineral_w5': self.get_hum(mineral_w5),
            'soil_w1': self.get_hum(soil_w1),
            'soil_w2': self.get_hum(soil_w2),
            'soil_w3': self.get_hum(soil_w3),
            'soil_w4': self.get_hum(soil_w4),
            'soil_w5': self.get_hum(soil_w5),
            'all_w1': self.get_hum(eng_w1+mineral_w1+soil_w1),
            'all_w2': self.get_hum(eng_w2+mineral_w2+soil_w2),
            'all_w3': self.get_hum(eng_w3+mineral_w3+soil_w3),
            'all_w4': self.get_hum(eng_w4+mineral_w4+soil_w4),
            'all_w5': self.get_hum(eng_w5+mineral_w5+soil_w5),
        }
    
    def get_tech_times(self, technic, is_dump=False):
        
        
        date = str(self.date)
        month_start = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-01',  '%Y-%m-%d').date()
        m_end_day = calendar.monthrange(self.date.year, self.date.month)[1]
        month_end = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-'+str(calendar.monthrange(self.date.year, self.date.month)[1]),  '%Y-%m-%d').date()

        domain = [('branch_id','=',self.branch_id.id), ('technic_id','in',technic.ids),('date','=',date)]
        obj_ids = self.env['report.mining.technic.analyze'].search(domain)
        domain_plan = self.get_dom(technic, is_dump)
        print ('domain_plan^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^domain_plan',domain_plan)
        plans = self.env['mining.production.report'].search(domain_plan)
        
        print ('obj_ids',obj_ids)
        repair_time = sum(obj_ids.mapped('sum_repair_time'))
        sum_work_time = sum(obj_ids.mapped('sum_work_time'))
        sum_production_time = sum(obj_ids.mapped('sum_production_time'))
        buteel = sum(obj_ids.mapped('sum_production'))

        plan = self.get_but(plans, False, date, date, False, 'sum_m3_plan')
        plan_sariin_ehnees = self.get_but(plans, False, month_start, date, False, 'sum_m3_plan')
        buteel_sariin_ehnees = self.get_but(plans, False, month_start, date, False, 'sum_m3')
        sariin_buteel = self.get_but(plans, False, month_start, month_end, False, 'sum_m3')
        sariin_plan = self.get_but(plans, False, month_start, month_end, False, 'sum_m3_plan')
        
        guitsetgel_w1 = self.get_but(plans, False, False, False, 1, 'sum_m3')
        guitsetgel_w2 = self.get_but(plans, False, False, False, 2, 'sum_m3')
        guitsetgel_w3 = self.get_but(plans, False, False, False, 3, 'sum_m3')
        guitsetgel_w4 = self.get_but(plans, False, False, False, 4, 'sum_m3')
        guitsetgel_w5 = self.get_but(plans, False, False, False, 5, 'sum_m3')
        
        repair_time_day = sum(obj_ids.filtered(lambda r:r.shift=='day').mapped('sum_repair_time'))
        sum_work_time_day = sum(obj_ids.filtered(lambda r:r.shift=='day').mapped('sum_work_time'))
        sum_production_time_day = sum(obj_ids.filtered(lambda r:r.shift=='day').mapped('sum_production_time'))
        buteel_day = sum(obj_ids.filtered(lambda r:r.shift=='day' and (r.production_line_id.material_id.mining_product_type=='engineering_work' or r.production_line_id.material_id.is_productivity==True)).mapped('sum_production'))
        sul_time_day = 12*len(technic)-sum_production_time_day-repair_time_day
        
        repair_time_night = sum(obj_ids.filtered(lambda r:r.shift=='night').mapped('sum_repair_time'))
        sum_work_time_night = sum(obj_ids.filtered(lambda r:r.shift=='night').mapped('sum_work_time'))
        sum_production_time_night = sum(obj_ids.filtered(lambda r:r.shift=='night').mapped('sum_production_time'))
        buteel_night = sum(obj_ids.filtered(lambda r:r.shift=='night' and (r.production_line_id.material_id.mining_product_type=='engineering_work' or r.production_line_id.material_id.is_productivity==True)).mapped('sum_production'))
        sul_time_night = 12*len(technic)-sum_production_time_night-repair_time_night
        
        return {
            'repair_time': '%.2f' % (repair_time),
            'sul_time': '%.2f' % (sum_work_time-sum_production_time-repair_time),
            'repair_time_day': '%.2f' % (repair_time_day),
            'sul_time_day': '%.2f' % (sul_time_day),
            'repair_time_night': '%.2f' % (repair_time_night),
            'sul_time_night': '%.2f' % (sul_time_night),
            'sum_work_time_day': '%.2f' % (sum_work_time_day),
            'sum_work_time_night': '%.2f' % (sum_work_time_night),
            'buteel_night':"{0:,.0f}".format(buteel_night),
            'buteel_day':"{0:,.0f}".format(buteel_day),
            'buteel_night_hour':"{0:,.0f}".format(buteel_night/sum_work_time_night if sum_work_time_night!=0 else 0),
            'buteel_day_hour':"{0:,.0f}".format(buteel_day/sum_work_time_day if sum_work_time_day!=0 else 0),
            'buteel': self.get_hum(buteel),
            'plan': self.get_hum(plan),
            'guitsetgel_w1': self.get_hum(guitsetgel_w1),
            'guitsetgel_w2': self.get_hum(guitsetgel_w2),
            'guitsetgel_w3': self.get_hum(guitsetgel_w3),
            'guitsetgel_w4': self.get_hum(guitsetgel_w4),
            'guitsetgel_w5': self.get_hum(guitsetgel_w5),
            'plan_sariin_ehnees': self.get_hum(plan_sariin_ehnees),
            'buteel_sariin_ehnees': self.get_hum(buteel_sariin_ehnees),
            'sariin_buteel': self.get_hum(sariin_buteel),
            'sariin_plan': self.get_hum(sariin_plan),
            'sum_production_time_day': '%.2f' % (sum_production_time_day),
            'sum_production_time_night': '%.2f' % (sum_production_time_night),
        }
    def get_float(self, strf):
        strf = strf.replace(',','')
        strf = strf.replace('-','')
        try:
            return float(strf)
        except Exception as e:
            return 0
    def get_hum(self, flo):
        return "{0:,.0f}".format(flo) if flo>0 else '-'
    def export_report_html_value(self):
        html = """
        <!DOCTYPE HTML>
                <html lang="en-US">
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
            <script src="https://code.highcharts.com/highcharts.js"></script>
            <script src="https://code.highcharts.com/modules/exporting.js"></script>
            <script src="https://code.highcharts.com/modules/export-data.js"></script>
            <script src="https://code.highcharts.com/modules/drilldown.js"></script>
            <script src="https://code.highcharts.com/modules/accessibility.js"></script>
            <style  type="text/css" media="all">    
                #container {
                    height: 400px; 
                }

            .highcharts-figure, .highcharts-data-table table {
            min-width: 310px; 
            margin: 1em auto;
            }

            .highcharts-data-table table {
            font-family: Verdana, sans-serif;
            border-collapse: collapse;
            border: 1px solid #EBEBEB;
            margin: 10px auto;
            text-align: center;
            width: 100%;
            }
            .highcharts-data-table caption {
            padding: 1em 0;
            font-size: 1.2em;
            color: #555;
            }
            .highcharts-data-table th {
                font-weight: 600;
            padding: 0.5em;
            }
            .highcharts-data-table td, .highcharts-data-table th, .highcharts-data-table caption {
            padding: 0.5em;
            }
            .highcharts-data-table thead tr, .highcharts-data-table tr:nth-child(even) {
            background: #f8f8f8;
            }
            .highcharts-data-table tr:hover {
            background: #f1f7ff;
            }
            </style>
            </head>
            <body>
                <table cellspacing="0" border="0">
                    <colgroup span="20" width="86"></colgroup>
        """
        logo_id = self.env['mining.dpr.logo'].search([('branch_id','=',self.branch_id.id)], limit=1)
        logo_str = ''
        if logo_id.logo:
            image_buf = logo_id.logo.decode('utf-8')
            if len(image_buf)>10:
                logo_str = '<img alt="Embedded Image" width="240" src="data:image/png;base64,%s" />'%(image_buf)
            
        html += """<tr>
                        <td colspan=5 style="border-top: 1px solid #000000; border-left: 1px solid #000000" height="27" align="left" valign=middle bgcolor="#FFFFFF">%s</td>
                        """%(logo_str)
        html +="""
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=10 rowspan=2 align="center" valign=middle bgcolor="#FFFFFF"><b><font face="Times New Roman" size=4 color="#000000">ӨДӨР ТУТМЫН ГҮЙЦЭТГЭЛИЙН МЭДЭЭ</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=4 align="center" valign=middle bgcolor="#FFFFFF" sdnum="1033;0;[$-F800]DDDD\, MMMM DD\, YYYY"><b><u><font face="Times New Roman" size=2 color="#000000">{1}</font></u></b></td>
                        <td align="left" valign=bottom><font face="Times New Roman" color="#000000"><br></font></td>
                    </tr>
                    <tr>
                        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000" height="27" align="center" valign=middle bgcolor="#FFFFFF"><b><font face="Times New Roman" color="#000000"><br></font></b></td>
                        <td style="border-bottom: 1px solid #000000" align="center" valign=middle bgcolor="#FFFFFF"><b><font face="Times New Roman" color="#000000"><br></font></b></td>
                        <td style="border-bottom: 1px solid #000000" align="center" valign=middle bgcolor="#FFFFFF"><b><font face="Times New Roman" color="#000000"><br></font></b></td>
                        <td style="border-bottom: 1px solid #000000" align="center" valign=middle bgcolor="#FFFFFF"><b><font face="Times New Roman" color="#000000"><br></font></b></td>
                        <td style="border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFFFF"><b><font face="Times New Roman" color="#000000"><br></font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=4 align="center" valign=middle bgcolor="#FFFFFF" sdval="44228" sdnum="1033;0;[$-F800]DDDD\, MMMM DD\, YYYY"><b><u><font face="Times New Roman" size=2 color="#000000">{0}</font></u></b></td>
                        <td align="left" valign=bottom><font face="Times New Roman" color="#000000"><br></font></td>
                    </tr>
        """.format(self.date.strftime('%a %b %d %Y'), self.branch_id.name)
        html +="""<tr>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" rowspan=2 height="43" align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Техник</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Тоног төхөөрөмжийн дугаар</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Ажиллах ээлж</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Засварын цаг</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Сул зогсолтын цаг</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Ажилласан цаг</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Ээлжийн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Цагийн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Хоногийн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Хоногийн төлөвлөсөн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">1-р долоо хоногийн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">2-р долоо хоногийн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">3-р долоо хоногийн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">4-р долоо хоногийн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">5-р долоо хоногийн бүтээл</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Сарын эхнээс (гүйцэтгэл)</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Сарын эхнээс (төлөвлөгөө)</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2">Сарын төлөвлөгөө</font></b></td>
                        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#002060"><b><font face="Times New Roman" size=2 color="#F2F2F2"><br></font></b></td>
                        <td align="left" valign=bottom><font face="Times New Roman" color="#000000"><br></font></td>
                    </tr>
                    <tr>
                        <td align="left" valign=bottom><font face="Times New Roman"><br></font></td>
                    </tr>
        """
        first_row = True
        objs = self.get_exac_ids()
        excaguud = objs
        dumpuud = []
        bgcolor_tegsh = "#DEEBF7"
        bgcolor_sondgoi = "#FFFFFF"
        bg_col = bgcolor_tegsh
        all_buteel = 0
        all_plan = 0
        all_plan_sariin_ehnees = 0
        all_buteel_sariin_ehnees = 0
        all_sariin_buteel = 0
        all_sariin_plan = 0
        for exca in objs:
            if bg_col==bgcolor_tegsh:
                bg_col = bgcolor_sondgoi
            else:
                bg_col = bgcolor_tegsh
            obs = self.get_tech_times(exca)
            repair_time = obs['repair_time']
            sul_time = obs['sul_time']
            repair_time_day = obs['repair_time_day']
            sul_time_day = obs['sul_time_day']
            repair_time_night = obs['repair_time_night']
            sul_time_night = obs['sul_time_night']
            sum_work_time_night = obs['sum_work_time_night']
            sum_work_time_day = obs['sum_work_time_day']
            sum_production_time_night = obs['sum_production_time_night']
            sum_production_time_day = obs['sum_production_time_day']
            buteel_night = obs['buteel_night']
            buteel_day = obs['buteel_day']
            buteel_night_hour = obs['buteel_night_hour']
            buteel_day_hour = obs['buteel_day_hour']
            buteel = obs['buteel']
            plan = obs['plan']
            sariin_plan = obs['sariin_plan']
            
            guitsetgel_w1 = obs['guitsetgel_w1']
            guitsetgel_w2 = obs['guitsetgel_w2']
            guitsetgel_w3 = obs['guitsetgel_w3']
            guitsetgel_w4 = obs['guitsetgel_w4']
            guitsetgel_w5 = obs['guitsetgel_w5']
            plan_sariin_ehnees = obs['plan_sariin_ehnees']
            buteel_sariin_ehnees = obs['buteel_sariin_ehnees']
            sariin_buteel = obs['sariin_buteel']
            
            html += """<tr>"""
            if first_row:
                html += """
                <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=%s height="90" align="center" valign=middle><b><font face="Times New Roman" size=2 color="#000000">Ачигч техникүүд</font></b></td>"""%(len(objs)*2)
            
            first_row = False
            html += """
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="left" valign=middle bgcolor="{bg_col}"><b><font face="Times New Roman" size=2>{exca_name}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}"><font face="Times New Roman" size=2 color="#000000">Өдөр</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdval="12" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{repair_time_day}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{sul_time_day}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{sum_production_time_day}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.0"><font face="Times New Roman" size=2 color="#000000">{buteel_day}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdnum="1033;0;#,##0"><font face="Times New Roman" size=2 color="#000000">{buteel_day_hour}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#FFC7CE" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#9C0006">{buteel}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="22632" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{plan}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="30640" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w1}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="64040" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w2}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w3}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w4}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w5}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="94680" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{buteel_sariin_ehnees}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="701592" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{plan_sariin_ehnees}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="701592" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{sariin_plan}</font></b></td>
            <td align="left" valign=bottom><font face="Times New Roman"><br></font></td>
        </tr>
        <tr>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}"><font face="Times New Roman" size=2 color="#000000">Шөнө</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdval="12" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{repair_time_night}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{sul_time_night}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{sum_production_time_night}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.0"><font face="Times New Roman" size=2 color="#000000">{buteel_night}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdnum="1033;0;#,##0"><font face="Times New Roman" size=2 color="#000000">{buteel_night_hour}</font></td>
            <td align="left" valign=bottom><font face="Times New Roman"><br></font></td>
        </tr>
        """.format(exca_name=exca.display_name, repair_time_day=repair_time_day, repair_time_night=repair_time_night, sul_time_day=sul_time_day, sul_time_night=sul_time_night, 
        sum_work_time_day=sum_work_time_day, sum_work_time_night=sum_work_time_night, buteel_day=buteel_day, buteel_night=buteel_night, buteel_day_hour=buteel_day_hour, buteel_night_hour=buteel_night_hour,
        buteel=buteel, plan=plan, guitsetgel_w1=guitsetgel_w1, guitsetgel_w2=guitsetgel_w2, guitsetgel_w3=guitsetgel_w3, guitsetgel_w4=guitsetgel_w4, guitsetgel_w5=guitsetgel_w5, buteel_sariin_ehnees=buteel_sariin_ehnees, plan_sariin_ehnees=plan_sariin_ehnees, sariin_buteel=sariin_buteel, bg_col=bg_col, all_plan=all_plan, sariin_plan=sariin_plan, sum_production_time_night = sum_production_time_night,
            sum_production_time_day = sum_production_time_day)
        
            all_buteel += self.get_float(buteel_day)+self.get_float(buteel_night)
            all_plan += self.get_float(plan)
            all_plan_sariin_ehnees += self.get_float(plan_sariin_ehnees)
            all_buteel_sariin_ehnees += self.get_float(buteel_sariin_ehnees)
            all_sariin_buteel += self.get_float(sariin_buteel)
            all_sariin_plan += self.get_float(sariin_plan)

        all_buteel = self.get_hum(all_buteel)
        all_plan = self.get_hum(all_plan)
        all_plan_sariin_ehnees = self.get_hum(all_plan_sariin_ehnees)
        all_buteel_sariin_ehnees = self.get_hum(all_buteel_sariin_ehnees)
        all_sariin_buteel = self.get_hum(all_sariin_buteel)
        all_sariin_plan = self.get_hum(all_sariin_plan)

        buteeluud = self.get_buteel(excaguud.ids)
        eng = buteeluud['eng']
        eng_plan = buteeluud['eng_plan']
        eng_w1 = buteeluud['eng_w1']
        eng_w2 = buteeluud['eng_w2']
        eng_w3 = buteeluud['eng_w3']
        eng_w4 = buteeluud['eng_w4']
        eng_w5 = buteeluud['eng_w5']

        mineral = buteeluud['mineral']
        mineral_plan = buteeluud['mineral_plan']
        mineral_w1 = buteeluud['mineral_w1']
        mineral_w2 = buteeluud['mineral_w2']
        mineral_w3 = buteeluud['mineral_w3']
        mineral_w4 = buteeluud['mineral_w4']
        mineral_w5 = buteeluud['mineral_w5']

        soil = buteeluud['soil']
        soil_plan = buteeluud['soil_plan']
        soil_w1 = buteeluud['soil_w1']
        soil_w2 = buteeluud['soil_w2']
        soil_w3 = buteeluud['soil_w3']
        soil_w4 = buteeluud['soil_w4']
        soil_w5 = buteeluud['soil_w5']

        all_w1 = buteeluud['all_w1']
        all_w2 = buteeluud['all_w2']
        all_w3 = buteeluud['all_w3']
        all_w4 = buteeluud['all_w4']
        all_w5 = buteeluud['all_w5']

        eng_sariin_ehnees = buteeluud['eng_sariin_ehnees']
        eng_plan_ehnees = buteeluud['eng_plan_ehnees']
        eng_plan_sar = buteeluud['eng_plan_sar']
        mineral_sariin_ehnees = buteeluud['mineral_sariin_ehnees']
        mineral_plan_ehnees = buteeluud['mineral_plan_ehnees']
        mineral_plan_sar = buteeluud['mineral_plan_sar']
        soil_sariin_ehnees = buteeluud['soil_sariin_ehnees']
        soil_plan_ehnees = buteeluud['soil_plan_ehnees']
        soil_plan_sar = buteeluud['soil_plan_sar']

        html += """
        <tr>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=8 height="31" align="center" valign=middle bgcolor="#92D050"><b><font face="Times New Roman" size=2>Инженерийн ажил, м3</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_plan}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_w1}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="4300" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_w2}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_w3}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="3000" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_w4}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="55" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_w5}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="7355" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_sariin_ehnees}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2><br></font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_plan_ehnees}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#92D050" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{eng_plan_sar}</td>
        <td align="center" valign=middle><font face="Times New Roman" color="#000000"></td>
        </tr>
        <tr>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=8 height="31" align="center" valign=middle bgcolor="#A9D18E"><b><font face="Times New Roman" size=2>Олборлосон нүүрс, м3</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral_plan}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral_w1}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral_w2}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral_w3}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral_w4}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral_w5}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral_sariin_ehnees}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{mineral_plan_sar}</td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{mineral_plan_sar}</td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#A9D18E" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2></td>
        <td align="center" valign=middle><font face="Times New Roman" color="#000000"></td>
        </tr>
        <tr>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=8 height="31" align="center" valign=middle bgcolor="#9BBCFF"><b><font face="Times New Roman" size=2>Хөрс, м3</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdval="27090" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdval="46513.3965062366" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil_plan}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdval="77485" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil_w1}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdval="182315" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil_w2}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdval="166950" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil_w3}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdval="195930" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil_w4}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdval="187980" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil_w5}</font></b></td>
        <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdval="810660" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil_sariin_ehnees}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{soil_plan_ehnees}</td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2><br></font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#9BBCFF" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{soil_plan_sar}</td>
        <td align="center" valign=middle><font face="Times New Roman" color="#000000"><br></font></td>
        </tr>
        <tr>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=8 height="31" align="center" valign=middle bgcolor="#FFFF00"><b><font face="Times New Roman" size=2>Нийт ачсан уулын цул, м3</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FF6600" sdval="27090" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#FFFF00">{all_buteel}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="46513.3965062366" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_plan}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="77485" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w1}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="186615" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w2}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="166950" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w3}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="198930" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w4}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="188035" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w5}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FF6600" sdval="818015" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#FFFF00">{all_buteel_sariin_ehnees}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="1360000.38353333" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_plan_sariin_ehnees}</font></b></td>
        <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#FFFF00" sdval="1359999.99505333" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_sariin_plan}</font></b></td>
        
        </tr>
        """.format(eng=eng, eng_plan=eng_plan, eng_w1=eng_w1, eng_w2=eng_w2, eng_w3=eng_w3, eng_w4=eng_w4, eng_w5=eng_w5, eng_sariin_ehnees=eng_sariin_ehnees, eng_plan_ehnees=eng_plan_ehnees, eng_plan_sar=eng_plan_sar,
        mineral=mineral, mineral_plan=mineral_plan, mineral_w1=mineral_w1, mineral_w2=mineral_w2, mineral_w3=mineral_w3, mineral_w4=mineral_w4, mineral_w5=mineral_w5, mineral_sariin_ehnees=mineral_sariin_ehnees, mineral_plan_sar=mineral_plan_sar, soil=soil, soil_plan=soil_plan, soil_w1=soil_w1, soil_w2=soil_w2, soil_w3=soil_w3, soil_w4=soil_w4, soil_w5=soil_w5, soil_sariin_ehnees=soil_sariin_ehnees, soil_plan_ehnees=soil_plan_ehnees, soil_plan_sar=soil_plan_sar,
        all_buteel=all_buteel, all_plan=all_plan, all_w1=all_w1, all_w2=all_w2, all_w3=all_w3, all_w4=all_w4, all_w5=all_w5, all_plan_sariin_ehnees=all_plan_sariin_ehnees,all_buteel_sariin_ehnees=all_buteel_sariin_ehnees , all_sariin_buteel=all_sariin_buteel,all_sariin_plan=all_sariin_plan)
        
        first_row = True
        objs = self.env['technic.equipment.setting'].search([('technic_type','=','dump'),('is_tbb_mining','=',True),('company_id','=',self.branch_id.company_id.id)])
        bgcolor_tegsh = "#DEEBF7"
        bgcolor_sondgoi = "#FFFFFF"
        bg_col = bgcolor_tegsh
        all_buteel = 0
        all_plan = 0
        all_plan_sariin_ehnees = 0
        all_buteel_sariin_ehnees = 0
        all_sariin_buteel = 0
        all_sariin_plan = 0
        print(objs.mapped('name'))
        for sett in objs:
            if bg_col==bgcolor_tegsh:
                bg_col = bgcolor_sondgoi
            else:
                bg_col = bgcolor_tegsh
            dumps = self.get_dump_ids(sett)
            dumpuud += dumps.ids
            obs = self.get_tech_times(dumps, is_dump=True)
            repair_time = obs['repair_time']
            sul_time = obs['sul_time']
            repair_time_day = obs['repair_time_day']
            sul_time_day = obs['sul_time_day']
            repair_time_night = obs['repair_time_night']
            sul_time_night = obs['sul_time_night']
            sum_work_time_night = obs['sum_work_time_night']
            sum_work_time_day = obs['sum_work_time_day']
            sum_production_time_night = obs['sum_production_time_night']
            sum_production_time_day = obs['sum_production_time_day']
            
            buteel_night = obs['buteel_night']
            buteel_day = obs['buteel_day']
            buteel_night_hour = obs['buteel_night_hour']
            buteel_day_hour = obs['buteel_day_hour']
            buteel = obs['buteel']
            plan = obs['plan']
            sariin_plan = obs['sariin_plan']
            guitsetgel_w1 = obs['guitsetgel_w1']
            guitsetgel_w2 = obs['guitsetgel_w2']
            guitsetgel_w3 = obs['guitsetgel_w3']
            guitsetgel_w4 = obs['guitsetgel_w4']
            guitsetgel_w5 = obs['guitsetgel_w5']
            plan_sariin_ehnees = obs['plan_sariin_ehnees']
            buteel_sariin_ehnees = obs['buteel_sariin_ehnees']
            sariin_buteel = obs['sariin_buteel']
            
            html += """<tr>"""
            if first_row:
                html += """
                <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=%s height="90" align="center" valign=middle><b><font face="Times New Roman" size=2 color="#000000">Өөрөө буулгагч</font></b></td>"""%(len(objs)*2)
            
            first_row = False
            html += """
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="left" valign=middle bgcolor="{bg_col}"><b><font face="Times New Roman" size=2>{model_name}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}"><font face="Times New Roman" size=2 color="#000000">Өдөр</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdval="12" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{repair_time_day}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{sul_time_day}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{sum_production_time_day}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.0"><font face="Times New Roman" size=2 color="#000000">{buteel_day}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdnum="1033;0;#,##0"><font face="Times New Roman" size=2 color="#000000">{buteel_day_hour}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="#FFC7CE" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#9C0006">{buteel}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="22632" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{plan}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="30640" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w1}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="64040" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w2}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w3}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w4}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{guitsetgel_w5}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="94680" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{buteel_sariin_ehnees}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="701592" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=2 color="#000000">{plan_sariin_ehnees}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 rowspan=2 align="center" valign=middle bgcolor="{bg_col}" sdval="701592" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2>{sariin_plan}</font></b></td>
            <td align="left" valign=bottom><font face="Times New Roman"><br></font></td>
        </tr>
        <tr>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}"><font face="Times New Roman" size=2 color="#000000">Шөнө</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdval="12" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{repair_time_night}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{sul_time_night}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.00"><font face="Times New Roman" size=2>{sum_production_time_night}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="{bg_col}" sdval="0" sdnum="1033;0;0.0"><font face="Times New Roman" size=2 color="#000000">{buteel_night}</font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="{bg_col}" sdnum="1033;0;#,##0"><font face="Times New Roman" size=2 color="#000000">{buteel_night_hour}</font></td>
            <td align="left" valign=bottom><font face="Times New Roman"><br></font></td>
        </tr>
        """.format(model_name=sett.model_id.modelname + '['+ str(len(dumps))+']', repair_time_day=repair_time_day, repair_time_night=repair_time_night, sul_time_day=sul_time_day, sul_time_night=sul_time_night, 
        sum_work_time_day=sum_work_time_day, sum_work_time_night=sum_work_time_night, buteel_day=buteel_day, buteel_night=buteel_night, buteel_day_hour=buteel_day_hour, buteel_night_hour=buteel_night_hour,
        buteel=buteel, plan=plan, guitsetgel_w1=guitsetgel_w1, guitsetgel_w2=guitsetgel_w2, guitsetgel_w3=guitsetgel_w3, guitsetgel_w4=guitsetgel_w4, guitsetgel_w5=guitsetgel_w5, buteel_sariin_ehnees=buteel_sariin_ehnees, plan_sariin_ehnees=plan_sariin_ehnees, sariin_buteel=sariin_buteel, bg_col=bg_col,sariin_plan=sariin_plan, sum_production_time_night=sum_production_time_night,sum_production_time_day=sum_production_time_day)

            all_buteel += self.get_float(buteel_day)+self.get_float(buteel_night)
            all_plan += self.get_float(plan)
            all_sariin_plan += self.get_float(sariin_plan)
            all_plan_sariin_ehnees += self.get_float(plan_sariin_ehnees)
            all_buteel_sariin_ehnees += self.get_float(buteel_sariin_ehnees)
            all_sariin_buteel += self.get_float(sariin_buteel)
            

        all_buteel = self.get_hum(all_buteel)
        all_plan = self.get_hum(all_plan)
        all_sariin_plan = self.get_hum(all_sariin_plan)
        all_plan_sariin_ehnees = self.get_hum(all_plan_sariin_ehnees)
        all_buteel_sariin_ehnees = self.get_hum(all_buteel_sariin_ehnees)
        all_sariin_buteel = self.get_hum(all_sariin_buteel)
        dumpuud = list(set(dumpuud))
        buteeluud = self.get_buteel(dumpuud, True)
        all_w1 = buteeluud['all_w1']
        all_w2 = buteeluud['all_w2']
        all_w3 = buteeluud['all_w3']
        all_w4 = buteeluud['all_w4']
        all_w5 = buteeluud['all_w5']

        html+="""
        <tr>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=8 height="31" align="center" valign=middle bgcolor="#FFFF00"><b><font face="Times New Roman" size=2>Нийт тээвэрлэсэн уулын цул, м3</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FF6600" sdval="27090" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#FFFF00">{all_buteel}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="46513.3965062366" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_plan}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="77485" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w1}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="186615" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w2}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="166950" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w3}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="198930" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w4}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="188035" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_w5}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FF6600" sdval="818015" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#FFFF00">{all_buteel_sariin_ehnees}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="1360000.38353333" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_plan_sariin_ehnees}</font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#FFFF00" sdval="1359999.99505333" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=2 color="#000000">{all_sariin_plan}</font></b></td>
            
        </tr>
        """.format(all_buteel=all_buteel, all_plan=all_plan, all_w1=all_w1, all_w2=all_w2, all_w3=all_w3, all_w4=all_w4, all_w5=all_w5, all_plan_sariin_ehnees=all_plan_sariin_ehnees, all_buteel_sariin_ehnees=all_buteel_sariin_ehnees, all_sariin_buteel=all_sariin_buteel, all_sariin_plan=all_sariin_plan)
        g_data = self.graph_data()
        html += """
        <tr>
        <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=19>
<figure class="highcharts-figure">
  <div id="container" style="width: 100%;"></div>
  <script type="text/javascript">
    Highcharts.chart('container', {
    title: {
        text: 'Уулын ажлын үзүүлэлтийн граффик'
    },
        """
        html += """xAxis: {
        type: 'category'
    },
    labels: {
        items: [{
            style: {
                left: '50px',
                top: '18px',
                color: ( // theme
                    Highcharts.defaultOptions.title.style &&
                    Highcharts.defaultOptions.title.style.color
                ) || 'black'
            }
        }]
    },
    yAxis: [{ //--- Primary yAxis
    title: {
        text: 'Бүтээл'
    }
    }, { //--- Secondary yAxis
        title: {
            text: 'Өссөн дүн'
        },
        opposite: true
    }],
    series: [{
        type: 'column',
        name: 'Төлөвлөгөө',
        data: %s,
    }, {
        type: 'column',
        name: 'Гүйцэтгэл',
        data: %s,
        drilldown: null,
    },  {
        type: 'spline',
        yAxis: 1,
        name: 'Өссөн Төлөвлөгөө',
        data: %s,
        marker: {
            lineWidth: 2,
            lineColor: Highcharts.getOptions().colors[3],
            fillColor: 'white'
        },
    }, {
        type: 'spline',
        yAxis: 1,
        name: 'Өссөн Гүйцэтгэл',
        data: %s,
        """%(str(g_data['plan']),str(g_data['buteel']),str(g_data['uss_plan']),str(g_data['uss_buteel']))
        html+="""
        marker: {
            lineWidth: 2,
            lineColor: Highcharts.getOptions().colors[3],
            fillColor: 'white'
        },
    },
    ],"""
        html+="""
    drilldown: {
        series: """+str(g_data['drill_data'])+"""
    }
});
    </script>
</figure>
</td>
    </tr>
        """

        def get_p_replace(notes_day_dd):
            notes_day_dd = notes_day_dd.replace('<p>','<span>')
            notes_day_dd = notes_day_dd.replace('</p>','</span><br/>')
            return notes_day_dd

        notes_day = self.env['mining.daily.entry'].search([('branch_id','=',self.branch_id.id),('date','=',self.date),('shift','=','day')], limit=1).notes or ''
        notes_day = get_p_replace(notes_day)
        notes_night = self.env['mining.daily.entry'].search([('branch_id','=',self.branch_id.id),('date','=',self.date),('shift','=','night')], limit=1).notes or ''
        notes_night = get_p_replace(notes_night)
        hab_info = self.env['mining.daily.entry'].search([('branch_id','=',self.branch_id.id),('date','=',self.date),('hab_info','!=',False)], limit=1).hab_info or ''
        hab_info = get_p_replace(hab_info)
        foot_infot = self.env['mining.daily.entry'].search([('branch_id','=',self.branch_id.id),('date','=',self.date),('foot_info','!=',False)], limit=1).foot_info or ''
        foot_infot = get_p_replace(foot_infot)
        repair_day = self.env['mining.daily.entry'].search([('branch_id','=',self.branch_id.id),('date','=',self.date),('shift','=','day')], limit=1).repair_info or ''
        repair_day = get_p_replace(repair_day)
        repair_night = self.env['mining.daily.entry'].search([('branch_id','=',self.branch_id.id),('date','=',self.date),('shift','=','night')], limit=1).repair_info or ''
        repair_night = get_p_replace(repair_night)
        html += """
        <tr>
            <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=4>Ерөнхий мэдээлэл:</td>
            <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000; font-size: 11px;" colspan=7>"""+notes_day+"""
            </td>
            <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000; font-size: 11px;" colspan=8>"""+notes_night+"""
            </td>
        </tr>
        <tr>
            <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=4>ХАБЭАБО-н мэдээлэл:</td>
            <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000; font-size: 11px;" colspan=15>"""+hab_info+"""
            </td>
        </tr>
        <tr>
            <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=4>Засварын мэдээлэл:</td>
            <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000; font-size: 11px;" colspan=7>"""+repair_day+"""
            </td>
            <td style="width: 100%; border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000; font-size: 11px;" colspan=8>"""+repair_night+"""
            </td>
        </tr>
        """
        def get_d_str(ddd):
            return ddd.strftime('%Y-%m-%d')
        
        dt = self.date
        start_date = dt - timedelta(days=dt.weekday())
        end_date = start_date + timedelta(days=6)
        dailys = self.env['mining.daily.entry'].search([('branch_id','=',self.branch_id.id),('date','>=',start_date),('date','<=',end_date)])
        hab_lines = dailys.mapped('hab_line')
        hab_cat_ids = dailys.mapped('hab_line.categ_id')

        d1 = start_date
        d2 = start_date+timedelta(days=1)
        d3 = start_date+timedelta(days=2)
        d4 = start_date+timedelta(days=3)
        d5 = start_date+timedelta(days=4)
        d6 = start_date+timedelta(days=5)
        d7 = start_date+timedelta(days=6)
        
        html += """
	<tr>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=3 rowspan=3 height="93" align="center" valign=middle bgcolor="#CCC1DA"><b><font face="Times New Roman" size=4 color="#000000">Хүн хүчний мэдээлэл</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Даваа</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Мягмар</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Лхагва</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Пүрэв</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Баасан</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=3 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Бямба</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Ням</font></td>
		<td style="border-top: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00"><b><font face="Times New Roman" size=4 color="#000000">Total</font></b></td>
	</tr>
	<tr>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{0}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{1}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{2}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{3}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{4}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=3 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{5}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{6}</font></td>
		<td style="border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
	</tr>
        """.format(get_d_str(d1),get_d_str(d2),get_d_str(d3),get_d_str(d4),get_d_str(d5),get_d_str(d6),get_d_str(d7))
        
        html+="""
        <tr>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdnum="1033;0;D-MMM"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdnum="1033;0;D-MMM"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdnum="1033;0;D-MMM"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdnum="1033;0;D-MMM"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdnum="1033;0;D-MMM"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" align="left" valign=bottom sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#B7DEE8"><font face="Times New Roman" size=4 color="#000000"><br></font></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdnum="1033;0;D-MMM"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
            <td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
        </tr>
        """
        # hab_lines
        def get_h(ttt, sh, c_id):
            if ttt and sh and c_id:
                return sum(hab_lines.filtered(lambda r:str(r.daily_id.date)==str(ttt) and r.daily_id.shift==sh and r.categ_id==c_id).mapped('qty'))
            elif not ttt and not sh and c_id:
                return sum(hab_lines.filtered(lambda r: r.categ_id==c_id).mapped('qty'))
            elif ttt and not sh and not c_id:
                return sum(hab_lines.filtered(lambda r: str(r.daily_id.date)==str(ttt)).mapped('qty'))
            else:
                return sum(hab_lines.mapped('qty'))
        for hab in hab_cat_ids:
            html += """
	<tr>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" height="31" align="center" valign=middle bgcolor="#CCC1DA" sdval="1" sdnum="1033;"><b><font face="Times New Roman" size=4 color="#000000">1</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" align="left" valign=middle bgcolor="#CCC1DA"><b><font face="Times New Roman" size=4 color="#000000">{0}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="left" valign=middle bgcolor="#CCC1DA"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdval="81" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{1}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdval="38" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{2}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdval="81" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{3}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdval="38" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{4}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdval="81" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{5}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdval="38" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{6}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdval="81" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{7}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdval="38" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{8}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdval="81" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{9}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdval="38" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{10}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" align="left" valign=bottom sdval="75" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=4 color="#000000">{11}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#B7DEE8" sdval="43" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{12}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdval="75" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{13}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#B7DEE8" sdval="43" sdnum="1033;"><font face="Times New Roman" size=4 color="#000000">{14}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="831" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><font face="Times New Roman" size=4 color="#000000">{15}</font></td>
	</tr>
    """.format(hab.display_name,get_h(d1,'day',hab),get_h(d1,'night',hab),get_h(d2,'day',hab),get_h(d2,'night',hab),get_h(d3,'day',hab),get_h(d3,'night',hab),get_h(d4,'day',hab),get_h(d4,'night',hab),get_h(d5,'day',hab),get_h(d5,'night',hab),get_h(d6,'day',hab),get_h(d6,'night',hab),get_h(d7,'day',hab),get_h(d7,'night',hab),get_h(False,False,hab))
        
        html+="""
	<tr>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=3 height="31" align="center" valign=middle bgcolor="#FFFF00"><b><font face="Times New Roman" size=4 color="#000000">Нийт хүний тоо</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#FFFF00" sdval="298" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{0}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#FFFF00" sdval="298" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{1}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#FFFF00" sdval="298" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{2}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#FFFF00" sdval="270" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{3}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#FFFF00" sdval="270" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{4}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=3 align="center" valign=middle bgcolor="#FFFF00" sdval="279" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{5}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#FFFF00" sdval="265" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{6}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00" sdval="1978" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"> {7}</font></b></td>
	</tr>""".format(get_h(d1,False,False),get_h(d2,False,False),get_h(d3,False,False),get_h(d4,False,False),get_h(d5,False,False),get_h(d6,False,False),get_h(d7,False,False),get_h(False,False,False))

        html += """
	<tr>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" rowspan=4 height="124" align="center" valign=middle bgcolor="#F2F2F2"><b><font face="Times New Roman" size=4 color="#000000">Түлшний мэдээ</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 rowspan=2 align="center" valign=middle bgcolor="#F2F2F2"><b><font face="Times New Roman" size=4 color="#000000">Огноо</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Даваа</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Мягмар</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Лхагва</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Пүрэв</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Баасан</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=3 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Бямба</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;D-MMM"><font face="Times New Roman" size=4 color="#000000">Ням</font></td>
		<td style="border-top: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00"><b><font face="Times New Roman" size=4 color="#000000">Total</font></b></td>
	</tr>"""
        html += """
	<tr>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{0}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{1}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{2}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{3}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{4}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=3 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{5}</font></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#D7E4BD" sdnum="1033;0;M/D/YYYY"><font face="Times New Roman" size=4 color="#000000">{6}</font></td>
		<td style="border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle bgcolor="#FFFF00"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
	</tr>""".format(get_d_str(d1),get_d_str(d2),get_d_str(d3),get_d_str(d4),get_d_str(d5),get_d_str(d6),get_d_str(d7))
        of = self.env['oil.fuel.fuel.report']
        rmt = self.env['report.mining.technic.analyze']
        def get_f(g_date_g):
            if g_date_g:
                return self.get_hum(sum(rmt.search([('branch_id','=',self.branch_id.id),('date','=',g_date_g.strftime('%Y-%m-%d'))]).mapped('sum_fuel')))
            else:
                return self.get_hum(sum(rmt.search([('branch_id','=',self.branch_id.id),('date','>=',str(start_date)),('date','<=',str(end_date))]).mapped('sum_fuel')))
        month_begin_day = datetime.strptime('%s-%s-01' % (str(self.date.year), str(self.date.month)), '%Y-%m-%d').date()
        print(month_begin_day,self.date)
        m3_zar_tulsh = sum(rmt.search([('branch_id','=',self.branch_id.id),('date','>=',month_begin_day),('date','<=',self.date),('owner_type','=','own_asset')]).mapped('sum_fuel'))
        m3_zar_buteel = sum(rmt.search([('branch_id','=',self.branch_id.id),('date','>=',month_begin_day),('date','<=',self.date)]).mapped('sum_production'))
        # print(of.search([('branch_id','=',self.branch_id.id),('date','>=',month_begin_day),('date','<=',self.date)]).mapped('technic_type'))
        m3_zar_buteel_old = sum(rmt.search([('branch_id','=',self.branch_id.id),('date','>=',month_begin_day),('date','<=',self.date),('owner_type','=','own_asset'),('technic_type','=','dump')]).mapped('sum_production'))
        print(m3_zar_tulsh,m3_zar_buteel,m3_zar_buteel_old)
        print('<<<<<<<<<<<<<<<<<<<<<<<<<')
        print(m3_zar_tulsh,'/',m3_zar_buteel)
        m3_zar = "{0:,.2f}".format(m3_zar_tulsh/m3_zar_buteel_old) if m3_zar_buteel_old!=0 else 0
        html+="""
	<tr>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#F2F2F2"><b><font face="Times New Roman" size=4 color="#000000">Хоногийн түлшний хэрэглээ, л</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="right" valign=middle sdval="34368" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{0}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle sdval="20145" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{1}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle sdval="36807" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{2}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle sdval="37401" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{3}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle sdval="35030" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{4}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=3 align="center" valign=middle sdval="34675" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{5}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle sdval="32508" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{6}</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle bgcolor="#FFFF00" sdval="984942" sdnum="1033;0;_(* #,##0_);_(* \(#,##0\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"> {7}</font></b></td>
	</tr>""".format(get_f(d1),get_f(d2),get_f(d3),get_f(d4),get_f(d5),get_f(d6),get_f(d7),get_f(False))
        html += """
	<tr>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" colspan=2 align="center" valign=middle bgcolor="#F2F2F2"><b><font face="Times New Roman" size=4 color="#000000">1м3-д зарцуулсан түлшний хэмжээ</font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-right: 1px solid #000000" align="center" valign=middle sdnum="1033;0;_(* #,##0.000_);_(* \(#,##0.000\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000"><br></font></b></td>
		<td style="border-top: 1px solid #000000; border-bottom: 1px solid #000000; border-left: 1px solid #000000; border-right: 1px solid #000000" align="right" valign=middle sdval="0" sdnum="1033;0;_(* #,##0.00_);_(* \(#,##0.00\);_(* &quot;-&quot;??_);_(@_)"><b><font face="Times New Roman" size=4 color="#000000">{0}</font></b></td>
	</tr>""".format(m3_zar)
        html+="""
    <tr>
        <td height="128" align="left" valign=bottom><font face="Times New Roman" size=3 color="#000000"><br></font></td>
		<td align="left" valign=bottom><font face="Times New Roman" size=3 color="#000000"><br></font></td>
		<td align="left" valign=bottom><font face="Times New Roman" size=3 color="#000000"><br></font></td>
		<td align="left" valign=bottom><font face="Times New Roman" size=3 color="#000000"> </font></td>
        <td style="width: 100%; border-top: 0px solid #000000; border-bottom: 0px solid #000000; border-left: 0px solid #000000; border-right: 0px solid #000000" colspan=4></td>
        <td style="width: 100%; border-top: 0px solid #000000; border-bottom: 0px solid #000000; border-left: 0px solid #000000; border-right: 0px solid #000000" align="center" valign=middle colspan=4><font face="Times New Roman" size=4 color="#000000">"""+foot_infot+"""</td>
        <td style="width: 100%; border-top: 0px solid #000000; border-bottom: 0px solid #000000; border-left: 0px solid #000000; border-right: 0px solid #000000; font-size: 11px;" colspan=15></td>
        <td align="left" valign=bottom><font face="Times New Roman" size=3 color="#000000"><br></font></td>
		<td align="left" valign=bottom><font face="Times New Roman" size=3 color="#000000"><br></font></td>
		<td align="left" valign=bottom><font face="Times New Roman" size=3 color="#000000"><br></font></td>
    </tr>
        """
        html += """</table></body></html>"""
        
        return html

    def graph_data(self):
        date = str(self.date)
        month_start = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-01',  '%Y-%m-%d')
        m_end_day = calendar.monthrange(self.date.year, self.date.month)[1]
        month_end = datetime.strptime(str(self.date.year)+'-'+str(self.date.month)+'-'+str(m_end_day),  '%Y-%m-%d')
        dom = [('branch_id','=',self.branch_id.id)
        # ,('is_production','=',True)
        ,'|'
        ,('technic_type','in',['excavator','loader'])
        ,('technic_type2','in',['excavator','loader'])
        ]
        objs = self.env['mining.production.report']
        datas = {'categories':[],'plan':[],'buteel':[],'uss_plan':[],'uss_buteel':[],'drill_data':[]}
        uss_plan = 0
        uss_buteel = 0
        
        for single_date in (month_start + timedelta(n) for n in range(m_end_day)):
            bb_dd = single_date.strftime('%d-%b')
            datas['categories'].append(bb_dd)
            domain = dom+[('date','=',single_date.strftime('%Y-%m-%d'))]
            obj_ids = objs.search(domain)
            plan = sum(obj_ids.mapped('sum_m3_plan'))
            buteel = sum(obj_ids.mapped('sum_m3'))
            uss_plan += plan
            uss_buteel += buteel
            datas['plan'].append({'name':bb_dd, 'y':plan,'drilldown': "plan_drill"+bb_dd})
            datas['buteel'].append({'name':bb_dd, 'y':buteel,'drilldown': "buteel_drill"+bb_dd})
            datas['uss_plan'].append({'name':bb_dd, 'y':uss_plan,'drilldown': "null"})
            datas['uss_buteel'].append({'name':bb_dd, 'y':uss_buteel,'drilldown': "null"})
            ex_ids = obj_ids.filtered(lambda r:r.sum_m3>0).mapped('excavator_id')
            dril_d = []
            
            for ex in ex_ids:
                dril_d.append([ex.display_name, sum(obj_ids.filtered(lambda r:r.excavator_id==ex).mapped('sum_m3'))])
                
            dril_p = []
            ex_ids = obj_ids.filtered(lambda r:r.sum_m3_plan>0).mapped('excavator_id')
            for ex in ex_ids:
                dril_p.append([ex.display_name, sum(obj_ids.filtered(lambda r:r.excavator_id==ex).mapped('sum_m3_plan'))])

            datas['drill_data'].append({'name': "Бүтээл Экскаватор",'id':'buteel_drill'+bb_dd, 'data':dril_d})
            datas['drill_data'].append({'name': "Төлөвлөгөө Экскаватор",'id':'plan_drill'+bb_dd, 'data':dril_p})
        return datas
    
    def get_last_col(self):
        return 30
    
    def export_report_html(self):
        html = self.export_report_html_value()
        file_name = 'DPR %s %s.html'%(self.date, self.branch_id.display_name)
        bytIO = BytesIO()
        bytIO.write(html.encode('utf-8'))
        out = base64.encodebytes(bytIO.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
    
    def export_report_pdf(self):
        html = self.export_report_html_value()
        file_name = 'DPR %s %s.pdf'%(self.date, self.branch_id.display_name)
        # bytIO = BytesIO()
        # bytIO.write(html.encode('utf-8'))
        # out = base64.encodebytes(bytIO.getvalue())
        options = {
            'margin-top': '0mm',
            'margin-right': '0mm',
            'margin-bottom': '0mm',
            'margin-left': '0mm',
            'encoding': "UTF-8",
            'header-spacing': 5,
            'orientation': 'Portrait',
        }
        # output = BytesIO(imgkit.from_string(html, False))
        output = BytesIO(pdfkit.from_string(html,False,options=options))
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
        

    def export_report(self):
        context = self.env.context
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output)
        file_name = u'Inventory'
        worksheet = workbook.add_worksheet('Total')
        worksheet_diff = workbook.add_worksheet('Diffrence')
        # worksheet_not_diff = workbook.add_worksheet(u'Зөрүүгүй')

        h1 = workbook.add_format({'bold': 1})
        h1.set_font_size(9)
        h1.set_align('center')
        h1.set_font_name('Arial')

        header = workbook.add_format({'bold': 1})
        header.set_font_size(9)
        header.set_align('center')
        header.set_align('vcenter')
        header.set_border(style=1)
        header.set_bg_color('#D3D3D3')
        header.set_text_wrap()
        header.set_font_name('Arial')

        header_wrap = workbook.add_format()
        header_wrap.set_text_wrap()
        header_wrap.set_font_size(9)
        header_wrap.set_align('center')
        header_wrap.set_align('vcenter')
        header_wrap.set_border(style=1)
        header_wrap.set_font_name('Arial')
        header_wrap.set_color('red')
        header_wrap.set_bold(True)

        contest_right_no_bor = workbook.add_format()
        contest_right_no_bor.set_text_wrap()
        contest_right_no_bor.set_font_size(9)
        contest_right_no_bor.set_align('right')
        contest_right_no_bor.set_align('vcenter')
        contest_right_no_bor.set_font_name('Arial')

        contest_left_no_bor = workbook.add_format()
        contest_left_no_bor.set_text_wrap()
        contest_left_no_bor.set_font_size(9)
        contest_left_no_bor.set_align('left')
        contest_left_no_bor.set_align('vcenter')
        contest_left_no_bor.set_font_name('Arial')

        contest_left = workbook.add_format()
        contest_left.set_text_wrap()
        contest_left.set_font_size(9)
        contest_left.set_align('left')
        contest_left.set_align('vcenter')
        contest_left.set_border(style=1)
        contest_left.set_font_name('Arial')

        contest_left_bold = workbook.add_format()
        contest_left_bold.set_bold(True)
        contest_left_bold.set_text_wrap()
        contest_left_bold.set_font_size(9)
        contest_left_bold.set_align('left')
        contest_left_bold.set_align('vcenter')
        contest_left_bold.set_border(style=1)
        contest_left_bold.set_font_name('Arial')
        contest_left_bold.set_bg_color('#B9CFF7')

        contest_right = workbook.add_format()
        contest_right.set_text_wrap()
        contest_right.set_font_size(9)
        contest_right.set_align('right')
        contest_right.set_align('vcenter')
        contest_right.set_border(style=1)
        contest_right.set_font_name('Arial')

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
        'num_format':'#,##0.00'
        })

        cell_format_no_border = workbook.add_format({
        'border': 0,
        'align': 'right',
        'font_size':9,
        'font_name': 'Arial',
        # 'text_wrap':1,
        'num_format':'#,##0.00'
        })

        tz = self.env['res.users'].sudo().browse(self.env.user.id).tz or 'Asia/Ulaanbaatar'
        timezone = pytz.timezone(tz)
        # f_date = ''
        # if self.date:
        #     f_date = self.date
        #     f_date = str(f_date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone))[0:20]
            
        row = 0
        last_col = self.get_last_col()
        worksheet.merge_range(row, 0, row, last_col, _('Material inventory sheet'), contest_center)
        row += 1
        worksheet.write(row, 0,_("Warehouse:"), contest_right)
        
        workbook.close()

        out = base64.encodebytes(output.getvalue())
        # file_name = self.name+'.xlsx'
        file_name = 'DPR %s %s.xlsx'%(self.date, self.branch_id.display_name)
        excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name})
        return {
             'type' : 'ir.actions.act_url',
             'url': "web/content/?model=report.excel.output&id=" + str(excel_id.id) + "&filename_field=filename&download=true&field=data&filename=" + excel_id.name,
             'target': 'new',
        }
    