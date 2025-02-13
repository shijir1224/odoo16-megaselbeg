# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import datetime
import pandas

class MiningDashboard(models.TransientModel):
    _name = 'mining.dashboard'
    _description = 'Mining Dashboard'

    @api.model
    def _get_year(self):
        return datetime.date.today().year

    @api.model
    def _get_month(self):
        return datetime.date.today().month

    
    def _get_default_range_id(self):
        return self.env['date.range'].search([], limit=1).id
    
    
    group_by = fields.Selection([
            ('day', u'Өдөрөөр'), 
            ('week', u'Долоо хонгоор'), 
            ('month', u'Сараар'), 
            ('year', u'Жилээр'), 
        ], default='day', string=u'Бүлэглэх')

    
    date_range_id = fields.Many2one(
        comodel_name='date.range',
        string='Огнооны хязгаар',
        default=_get_default_range_id
    )
    date_from = fields.Date(string='Эхлэх огноо', required=True)
    date_to = fields.Date(string='Дуусах огноо', required=True)
    
    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    def get_blast_plan_datas(self, group_by, date_from, date_to):
        datas = {}
        # obj = self.env['maintenance.workorder'].browse(wo_id)
        categ_names = []
        color_names = []
        series = []
        series_drilldown = []
        idx = 1
        # if self.group_by:
        # where = 
        if group_by and date_from and date_to:
            query = """
                SELECT mbr.branch_id,extract({2} from date) as categ,SUM(blast_volume_plan),SUM(blast_volume_actual),SUM(blast_volume_plan_master)
                FROM mining_blast_report mbr
                WHERE date>='{0}' and date<='{1}'
                GROUP BY 1,2
                ORDER BY 1
                """.format(date_from,date_to,group_by)
            self.env.cr.execute(query)
            query_result = self.env.cr.fetchall()
            
            branch_ids = []
            group_by_type = []
            for item in query_result:
                branch_ids.append(item[0])
                group_by_type.append(item[1])

            branch_ids = list(set(branch_ids))
            group_by_type = list(set(group_by_type))
            # for item in branch_ids:
            ser_m_plan = []
            ser_plan = []
            ser_actual = []

            

            for cat in branch_ids:
                branch_name = self.env['res.branch'].browse(cat).name
                categ_names.append(branch_name)
                
                ser_m_plan_drilldown = []
                ser_plan_drilldown = []
                ser_actual_drilldown = []

                s_m_plan = 0
                s_plan = 0
                s_actual = 0
                for res in query_result:
                    if res[0]==cat:
                        s_m_plan += float(res[2])
                        s_plan += float(res[3])
                        s_actual += float(res[4])


                ser_m_plan.append({
                    'name': branch_name,
                     "y": s_m_plan,
                    "drilldown": 'm_'+str(cat)
                 })
                ser_plan.append({
                    "name": branch_name,
                     "y": s_plan,
                    "drilldown": 'p_'+str(cat)
                 })
                ser_actual.append({
                    "name": branch_name,
                     "y": s_actual,
                    "drilldown": 'a_'+str(cat)
                 })

                s_m_plan = 0
                s_plan = 0
                s_actual = 0
                for gr in group_by_type:
                    for res in query_result:
                        if res[0]==cat and gr==res[1]:
                            s_m_plan += float(res[2])
                            s_plan += float(res[3])
                            s_actual += float(res[4])
                    gr_str = gr
                    if group_by=='day':
                        gr_str = str(int(gr))+u' өдөр'
                    elif group_by=='month':
                        gr_str = str(int(gr))+u' сар'
                    elif group_by=='year':
                        gr_str = str(int(gr))+u' жил'
                    ser_m_plan_drilldown.append([gr_str, s_m_plan])
                    ser_plan_drilldown.append([gr_str, s_plan])
                    ser_actual_drilldown.append([gr_str, s_actual])

                series_drilldown.append({
                    "name": u"Мастер Төлөвлөгөө "+self.env['res.branch'].browse(cat).name,
                     "id": "m_"+str(cat),
                     "data": ser_m_plan_drilldown,
                    })
                series_drilldown.append({
                    "name": u"Төлөвлөгөө "+self.env['res.branch'].browse(cat).name,
                     "id": "p_"+str(cat),
                     "data": ser_plan_drilldown,
                    })
                series_drilldown.append({
                    "name": u"Гүйцэтгэл "+self.env['res.branch'].browse(cat).name,
                     "id": "a_"+str(cat),
                     "data": ser_actual_drilldown,
                    })
            
            series.append({
                'name': 'Мастер Төлөвлөгөө',
                'data': ser_m_plan,
                # 'data': d_series,
                 # "colorByPoint": True,
                # 'drilldown': 'master_plan'
                })
            series.append({
                'name': 'Төлөвлөгөө',
                'data': ser_plan,
                # 'drilldown': 'plan'
                })
            series.append({
                'name': 'Гүйцэтгэл',
                'data': ser_actual,
                # 'drilldown': 'actual'
                })

            

            
            
            datas['categories'] = categ_names
            # # datas['timesheet_colors'] = color_names
            datas['data_series'] = series
            datas['data_series_drilldown'] = series_drilldown
        return datas

    def get_mining_plan_datas(self, group_by, date_from, date_to):
        datas = {}
        categ_names = []
        color_names = []
        series = []
        series_drilldown = []
        idx = 1
        # if self.group_by:
        # where = 
        technic_obj = self.env['technic.equipment']
        save_group_by = group_by
        if group_by and date_from and date_to:
            str_group_by = ''
            if group_by=='day':
                group_by = "lpad(extract(month from date)::text, 2, '0')||'-'||lpad(extract(day from date)::text, 2, '0') "
            elif group_by == 'week':
                group_by = "lpad(extract(week from date)::text, 2, '0')"
            elif group_by =='month':
                group_by = "lpad(extract(month from date)::text, 2, '0')"
            else:
                group_by = 'extract(%s from date)'%(group_by)

            query = """
                SELECT {2} as categ, 
                SUM(coalesce(sum_m3_plan_master,0)) as sum_m3_plan_master, 
                SUM(coalesce(sum_m3_plan_exc,0)) as sum_m3_plan_exc, 
                SUM(coalesce(sum_m3,0)) as sum_m3, 
                SUM(coalesce(sum_m3_sur,0)) as sum_m3_sur,
                mpr.excavator_id,
                te.park_number
                FROM mining_production_report mpr
                left join technic_equipment te on (te.id=mpr.excavator_id)
                WHERE date>='{0}' and date<='{1}' and mpr.is_production=true
                and mpr.excavator_id is not null
                
                GROUP BY mpr.date,mpr.excavator_id,te.park_number
                ORDER BY mpr.date,mpr.excavator_id
                """.format(date_from,date_to,group_by)
            self.env.cr.execute(query)
            query_result = self.env.cr.dictfetchall()
            # if len(query_result)==0:
            #     return False
            df = pandas.DataFrame(query_result)
            catig_by_ids = []
            group_by_type = []
            try:
                catig_by_ids = sorted(df.groupby('categ').groups.keys())
                group_by_type = sorted(df.groupby('park_number').groups.keys())
            except Exception as e:
                series_drilldown = series_drilldown

            ser_m_plan = []
            ser_plan = []
            ser_actual = []
            ser_actual_sur = []
            ser_plan_ussun = []
            ser_actual_ussun = []

            ussun_dun_plan = 0
            ussun_dun_actual = 0
            for cat in catig_by_ids:
                cat_name = cat
                categ_names.append(cat_name)
                s_m_plan = sum(df.loc[ df['categ'] == cat, 'sum_m3_plan_master'])
                s_plan = sum(df.loc[ df['categ'] == cat, 'sum_m3_plan_exc'])
                s_actual = sum(df.loc[ df['categ'] == cat, 'sum_m3'])
                s_actual_sur = sum(df.loc[ df['categ'] == cat, 'sum_m3_sur'])
                
                ussun_dun_plan += s_plan
                ussun_dun_actual += s_actual

                ser_m_plan.append({
                    'name': cat_name,
                     "y": s_m_plan,
                    "drilldown": 'm_'+str(cat)
                 })
                ser_plan.append({
                    "name": cat_name,
                     "y": s_plan,
                    "drilldown": 'p_'+str(cat)
                 })
                ser_actual.append({
                    "name": cat_name,
                     "y": s_actual,
                    "drilldown": 'a_'+str(cat)
                 })
                ser_actual_sur.append({
                    "name": cat_name,
                     "y": s_actual_sur,
                    "drilldown": 's_'+str(cat)
                 })
                ser_plan_ussun.append({'name':cat_name,'y':ussun_dun_plan,'id': cat_name+'_per'})
                ser_actual_ussun.append({'name':cat_name,'y':ussun_dun_actual,'id': cat_name+'_per'})
                # ser_plan_ussun.append(
                #     ussun_dun_plan
                # )

                # ser_actual_ussun.append(
                #     ussun_dun_actual
                # )

                
                ser_m_plan_drilldown = []
                ser_plan_drilldown = []
                ser_actual_drilldown = []
                ser_actual_sur_drilldown = []
                for gr in group_by_type:
                    gr_str = gr.encode('utf-8').strip()
                    s_m_plan = sum(df.loc[ (df['categ'] == cat ) & (df['park_number']==gr_str), 'sum_m3_plan_master'])
                    s_plan = sum(df.loc[ (df['categ'] == cat ) & (df['park_number']==gr_str), 'sum_m3_plan_exc'])
                    s_actual = sum(df.loc[ (df['categ'] == cat) & (df['park_number']==gr_str), 'sum_m3'])
                    s_actual_sur = sum(df.loc[ (df['categ'] == cat) & (df['park_number']==gr_str), 'sum_m3_sur'])
                    
                    ser_m_plan_drilldown.append([gr_str, s_m_plan])
                    ser_plan_drilldown.append([gr_str, s_plan])
                    ser_actual_drilldown.append([gr_str, s_actual])
                    ser_actual_sur_drilldown.append([gr_str, s_actual_sur])

                series_drilldown.append({
                    "name": u"Мастер Төлөвлөгөө ",
                     "id": "m_"+str(cat),
                     "data": ser_m_plan_drilldown,
                    })
                series_drilldown.append({
                    "name": u"Төлөвлөгөө ",
                     "id": "p_"+str(cat),
                     "data": ser_plan_drilldown,
                    })
                series_drilldown.append({
                    "name": u"Гүйцэтгэл ",
                     "id": "a_"+str(cat),
                     "data": ser_actual_drilldown,
                    })
                series_drilldown.append({
                    "name": u"Гүйцэтгэл Хэмжилтээр ",
                     "id": "s_"+str(cat),
                     "data": ser_actual_sur_drilldown,
                    })
            
            series.append({
                'name': 'Мастер Төлөвлөгөө',
                'data': ser_m_plan,
                'type': 'column',
                'yAxis': 1,
                })
            series.append({
                'name': 'Төлөвлөгөө',
                'data': ser_plan,
                'type': 'column',
                'yAxis': 1,
                })
            series.append({
                'name': 'Гүйцэтгэл',
                'data': ser_actual,
                'type': 'column',
                'yAxis': 1,
                })
            series.append({
                'name': 'Гүйцэтгэл Хэмжилтээр',
                'data': ser_actual_sur,
                'type': 'column',
                'yAxis': 1,
                })
            series.append({
                'name': 'Төлөвлөгөө өссөн дүн ',
                'data': ser_plan_ussun,
                'type': 'spline',
                # 'yAxis': 1,
                })
            series.append({
                'name': 'Гүйцэтгэл өссөн дүн ',
                'data': ser_actual_ussun,
                'type': 'spline',
                # 'yAxis': 1,
                })

            

            
            
            datas['categories'] = categ_names
            datas['data_series'] = series
            datas['data_series_drilldown'] = series_drilldown
        return datas