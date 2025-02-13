# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api
from odoo.exceptions import UserError, ValidationError
import base64
import xlsxwriter
from io import BytesIO
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
import logging
_logger = logging.getLogger(__name__)


class report_mining_mrp_wizard(models.TransientModel):
    _name = "report.mining.mrp.wizard"  
    _description = "report mining wizard"
    
    date_start = fields.Date(string=u'Эхлэх огноо', default=fields.Date.context_today)
    date_end = fields.Date(string=u'Дуусах огноо',default=fields.Date.context_today)
    date_range_id = fields.Many2one('date.range',string='Огнооны хязгаар')
    branch_ids = fields.Many2many('res.branch', string=u'Салбарууд')
    conf_ids = fields.Many2many('mining.cost.mrp.config', string=u'Тохиргоонууд')
    group_type = fields.Selection([('day','Day'),('month','Month'),('year','Year')], string=u'Group type', default='day')

    @api.onchange('date_start','date_end')
    def onch_date(self):
        if self.date_start and self.date_end:
            diff_date = (self.date_end-self.date_start)
            if diff_date.days<=365 and diff_date.days>=45:
                self.group_type = 'month'
            elif diff_date.days>=366:
                self.group_type = 'month'
        else:
            self.group_type = 'day'
            
    def get_day_between(self, group_type, s_date, e_date):
        d_cols = []
        d_cols_r = []
        delta = relativedelta(days=1)
        if group_type=='month':
            delta = relativedelta(months=1)
        elif group_type=='year':
            delta = relativedelta(years=1)
        while s_date <= e_date:
            if group_type=='day':
                d_cols.append(s_date.strftime("%Y-%m-%d"))
                d_cols_r.append(s_date.strftime("%a")+'.'+s_date.strftime("%b-%d"))
            elif group_type=='month':
                d_cols.append(s_date.strftime("%Y-%m"))
            elif group_type=='year':
                d_cols.append(s_date.strftime("%Y"))
            s_date += delta

        return d_cols,d_cols_r

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        self.date_start = self.date_range_id.date_start
        self.date_end = self.date_range_id.date_end

    def get_domain(self):
        domain = []
        domain.append(('date','>=',self.date_start))
        domain.append(('date','<=',self.date_end))
        if self.branch_ids:
            domain.append(('branch_id','in',self.branch_ids.ids))
        return domain
        
    def open_analyze(self):
 # self.get_tuple(branch_ids.ids), view_type_where
        wheres=''
        if self.conf_ids:
            if len(self.conf_ids)==1:
                wheres += " and c.id  = %s " %self.conf_ids[0].id
            if len(self.conf_ids)>1:
                wheres = " and c.id in ("+','.join(map(str,self.conf_ids.ids))+") "
        #
        # query = """
        #     select sum(debit-credit) as debit, 
        #             c.product_id,
        #             l.branch_id,l.id,
        #             l.account_id,
        #             l.date
        #             from mining_cost_mrp_config c left join 
        #                 mining_cost_mrp_config_account_account_rel r on r.cost_id=c.id left join 
        #                 account_move_line l on l.account_id=r.account_id and c.product_id notnull 
        #                 where l.date between '{0}' and '{1}' {2}
        #                 group by c.product_id,l.id
        # """.format(str(self.date_start), str(self.date_end),wheres)
        

        query = """
                select     
                --sum(debit-credit) as debit,
                sum(al.amount) as debit, 
                    c.product_id,
                  --  l.branch_id,l.id,
                  --  l.account_id,
                  --  l.date,al.id,
                    al.date,
                    al.account_id as analytic_account,
                    al.general_account_id as account_id,
                    al.branch_id,
                    al.move_line_id as id
                    from mining_cost_mrp_config c left join 
                        mining_cost_mrp_config_account_account_rel r on r.cost_id=c.id 
                        left join 
                        mining_cost_mrp_config_account_analytic_rel ar on ar.cost_id=c.id 
                        left join                         
                        mining_cost_mrp_config_res_branch_rel br on br.cost_id=c.id 
                        left join 
                        account_analytic_line al on (al.account_id=ar.account_id and al.general_account_id=r.account_id and br.branch_id=al.branch_id) 
                        --left join 
--                        account_move_line l on l.account_id=r.account_id and c.product_id notnull 
                        where al.date between '{0}' and '{1}' {2} and al.id notnull
                        group by c.product_id,
                        --l.id,
                        al.id  
        """.format(str(self.date_start), str(self.date_end),wheres)        
        print ('query ',query)
        self.env.cr.execute(query)
        
# left join mining_material mm on mm.product_id=c.product_id left join  mining_production_report mr on mr.material_id=mm.id        
        print('===  get_buteel_dundaj  ', query)
        datas = self.env.cr.dictfetchall()
        print ('datas ',datas)
        created_data=[]
        for data in datas:
            if data.get('product_id',False):
                if data['product_id'] in created_data:
                #     continue
                    m_data=[{'sum_m3_petram':0,
                             'sum_m3':0,
                             'sum_tn':0,
                             'sum_m3_sur':0,
                             'sum_tn_sur':0,
                             'sum_tn_petram':0,
                             'sum_m3_avg':0,
                             'sum_tn_avg':0,
                             }]
                else:
                    created_data.append(data['product_id'])
                    query = """
                            select 
                                    sum(sum_m3) as sum_m3,
                                    sum(sum_m3_petram) as sum_m3_petram,
                                    sum(res_count) as res_count,
                                    sum(sum_tn) as sum_tn,
                                    sum(sum_m3_sur) as sum_m3_sur,
                                    sum(sum_tn_petram) as sum_tn_petram,
                                    sum(sum_tn_avg) as sum_tn_avg,
                                    sum(sum_m3_avg) as sum_m3_avg,
                                    sum(sum_tn_sur) as sum_tn_sur,
                                    m.product_id 
                                    from 
                                    mining_production_report r left join 
                                    mining_material m on r.material_id=m.id 
                                where date between '{0}' and '{1}' and m.product_id={2}
                                group by m.product_id
                    """.format(str(self.date_start), str(self.date_end),data['product_id']) 
                    print ('query22 ',query)
                    self.env.cr.execute(query)  
                    m_data = self.env.cr.dictfetchall()
                print ('m_data ',m_data)
                if m_data:
                    vals={'date':data['date'],
                          'branch_id':data['branch_id'],
                          'account_amount':data['debit'],
                          'sum_m3_petram':m_data[0]['sum_m3_petram'],
                          'sum_m3':m_data[0]['sum_m3'],
                          'sum_tn':m_data[0]['sum_tn'],
                          'sum_m3_sur':m_data[0]['sum_m3_sur'],
                          'sum_tn_sur':m_data[0]['sum_tn_sur'],
                          'sum_tn_petram':m_data[0]['sum_tn_petram'],
                          'sum_m3_avg':m_data[0]['sum_m3_avg'],
                          'sum_tn_avg':m_data[0]['sum_tn_avg'],
                          # 'sum_tn_petram':m_data[0]['sum_tn_petram'],
                          'wizard_id':self.id,
                          'product_id':data['product_id'],
                          'aml_id':data['id'],
                          'gl_acc':data['account_id'],
                          'analytic_acc':data['analytic_account'],
                          
                          
                          }
    
    
                    self.env['report.mining.mrp.cost.analyze'].create(vals)
        action = self.env.ref('mw_mining_cost.action_mining_report_mrp_cost_tree')
        vals = action.read()[0]
        vals['domain'] = [('wizard_id','=',self.id)]
        vals['context'] = {}
        # vals = action.read()[0]
        # vals['domain'] = self.get_domain()
        # vals['context'] = {}
        return vals
    
    def get_tuple(self, obj):
        if len(obj) > 1:
            return str(tuple(obj))
        else:
            return "("+str(obj[0])+") "

    def get_buteel_dundaj(self, date_start, date_end, branch_ids, group_type, view_type_where):
        # case when (coalesce(sum(tt.plan_run_hour),0)+coalesce(sum(tt.plan_repair_hour))>=coalesce(sum(tt.sum_repair_time),0) then (coalesce(sum(tt.plan_run_hour),0)+coalesce(sum(tt.plan_repair_hour))-coalesce(sum(tt.sum_repair_time),0) else 0 end as js_plan,
        # case when coalesce(sum(tt.plan_run_hour),0)>=coalesce(sum(tt.sum_repair_time),0) then coalesce(sum(tt.plan_run_hour),0)-coalesce(sum(tt.sum_repair_time),0) else 0 end as js_plan,

        query = """
            SELECT
                te.name as technic_name,
                te.id as technic_id,
                tt.date as date,
                coalesce(tt.sum_production*tt.haul_distance,0)  as niit_urj,
                coalesce(tt.sum_production, 0) as sum_production,
                coalesce(tt.haul_distance, 0) as haul_distance
                from report_mining_technic_analyze as tt
                left join technic_equipment as te on (te.id=tt.technic_id)
                where tt.date>='{0}' and tt.date<='{1}' and tt.branch_id in {2}
                and te.id is not null {3}
        """.format(str(date_start), str(date_end), self.get_tuple(branch_ids.ids), view_type_where)
        self.env.cr.execute(query)
        print('===  get_buteel_dundaj  ', query)
        plans = self.env.cr.dictfetchall()
        return plans
    
    def get_plan_actual(self, group_type, date, tech_id, vals):
        def get_date(item_date):
            item_date = datetime.strptime(str(item_date), "%Y-%m-%d")
            if group_type=='month':
                item_date = item_date.strftime( "%Y-%m")
            elif group_type=='year':
                item_date = item_date.strftime( "%Y")
            else:
                item_date = item_date.strftime("%Y-%m-%d")
            return str(item_date)
        sum_production = 0
        niit_urj = 0
        for item in vals:
            if str(item['technic_id'])==str(tech_id) and get_date(item['date']) == str(date):
                # plan += float(item['js_plan'])
                niit_urj += float(item['niit_urj'])
                sum_production += float(item['sum_production'])
        haul_distance_w = niit_urj/sum_production if sum_production!=0 else 0
        datas = {
            'haul_distance_w': haul_distance_w,
            'sum_production': sum_production,
        }
        return datas
        
    def open_analyze_ta_download(self):
        datas = self.get_buteel_dundaj(self.date_start, self.date_end, self.branch_ids, self.group_type, '')
        if datas:
            sd = self.date_start
            ed = self.date_end
            date_cols, date_cols_real = self.get_day_between(self.group_type, sd, ed)

            tech_ids = []
            for pp in datas:
                tech_ids.append(pp['technic_id'])
            tech_ids = list(set(tech_ids))
            tech_ids = self.env['technic.equipment'].search([('id','in',tech_ids)])

            output = BytesIO()
            workbook = xlsxwriter.Workbook(output)
            file_name = 'Талын зайн жигнэсэн '+str(self.date_start)+'->'+str(self.date_end)+'%s'%(','.join(self.branch_ids.mapped('display_name')))
            
            h1 = workbook.add_format({'bold': 1})
            h1.set_font_size(12)

            header = workbook.add_format({'bold': 1})
            header.set_font_size(9)
            header.set_align('center')
            header.set_align('vcenter')
            header.set_border(style=1)
            header.set_bg_color('#E9A227')

            header_wrap = workbook.add_format({'bold': 1})
            header_wrap.set_text_wrap()
            header_wrap.set_font_size(9)
            header_wrap.set_align('center')
            header_wrap.set_align('vcenter')
            header_wrap.set_border(style=1)
            header_wrap.set_bg_color('#eff8fe')

            
            contest_right = workbook.add_format({'italic':1})
            contest_right.set_text_wrap()
            contest_right.set_font_size(9)
            contest_right.set_align('right')
            contest_right.set_align('vcenter')
            contest_right.set_border(style=1)
            contest_right.set_num_format('#,##0.0')

            contest_right_do = workbook.add_format({'italic':1})
            contest_right_do.set_text_wrap()
            contest_right_do.set_font_size(9)
            contest_right_do.set_align('right')
            contest_right_do.set_align('vcenter')
            contest_right_do.set_border(style=1)
            contest_right_do.set_bg_color('#d6d5ff')
            contest_right_do.set_num_format('#,##0.0')

            contest_right_d_check = workbook.add_format({'italic':1})
            contest_right_d_check.set_text_wrap()
            contest_right_d_check.set_font_size(9)
            contest_right_d_check.set_align('right')
            contest_right_d_check.set_align('vcenter')
            contest_right_d_check.set_border(style=1)
            contest_right_d_check.set_bg_color('#20fa24')
            contest_right_d_check.set_num_format('#,##0.0')

            contest_left = workbook.add_format()
            contest_left.set_text_wrap()
            contest_left.set_font_size(9)
            contest_left.set_align('left')
            contest_left.set_align('vcenter')
            contest_left.set_border(style=1)
            contest_left.set_num_format('#,##0.0')

            contest_center = workbook.add_format()
            contest_center.set_text_wrap()
            contest_center.set_font_size(9)
            contest_center.set_align('center')
            contest_center.set_align('vcenter')
            contest_center.set_border(style=1)
            contest_center.set_num_format('#,##0.0')

            worksheet = workbook.add_worksheet(file_name)
            worksheet.set_zoom(80)
            worksheet.write(0,2, u"%s" %(file_name), h1)
            row = 1

            worksheet.merge_range(row, 0, row+1, 0, u'Техникийн нэр', header_wrap)
            
            worksheet.set_column('A:A', 25)
            # worksheet.set_column('B:B', 10)
            worksheet.freeze_panes(3, 1)
            col = 1
            for dd in date_cols:
                worksheet.merge_range(row, col, row, col+1, dd, header_wrap)
                worksheet.write(row+1, col, 'Жигнэсэн дундаж', header_wrap)
                worksheet.write(row+1, col+1, 'Бүтээл', header_wrap)
                col += 2
                
            row += 2
            for tech in tech_ids:
                technic_obj_id = tech
                worksheet.write(row, 0, technic_obj_id.name, header_wrap)
                col = 1
                for dd in date_cols:
                    pp_df = self.get_plan_actual(self.group_type, dd, technic_obj_id.id, datas)
                    worksheet.write(row, col, float(pp_df['haul_distance_w']) or '', contest_right)
                    worksheet.write(row, col+1, float(pp_df['sum_production']) or '', contest_right)
                    col += 2
                row += 1

            # =============================
            workbook.close()
            out = base64.encodebytes(output.getvalue())
            excel_id = self.env['report.excel.output'].create({'data': out, 'name': file_name+'.xlsx'})

            return {
                    'type' : 'ir.actions.act_url',
                    'url': "web/content/?model=report.excel.output&id=%d&filename_field=filename&download=true&field=data&filename=%s"%(excel_id.id,excel_id.name),
                    'target': 'new',
            }
        else:
            raise UserError(_(u'Бичлэг олдсонгүй!'))
           
           
           
