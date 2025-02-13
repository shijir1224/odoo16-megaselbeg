# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
import datetime
import pandas
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE

class OilFuelDashboard(models.TransientModel):
    _name = 'oil.fuel.dashboard'
    _description = 'Oil Fuel Dashboard'

    
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
    technic_type = fields.Selection(TECHNIC_TYPE, 
        string ='Техникийн төрөл')
    technic_id = fields.Many2one('technic.equipment',string='Техникийн')
    technic_ids = fields.Many2many('technic.equipment', 'oil_fuel_dashboard_technic_rel', 'dash_id', 'tech_id', string='Техникүүд')
    technic_setting_id = fields.Many2one('technic.equipment.setting', 'Техникийн Төрөл')
    
    @api.onchange('technic_type')
    def onchange_technic_type(self):
        """Handle date range change."""
        domain = {}
        if self.technic_type:
            self.technic_ids = self.env['technic.equipment'].search([('technic_type','=',self.technic_type),('owner_type','=','own_asset')])
            domain['technic_ids'] = [('technic_type', '=', self.technic_type)]
        else:
            self.technic_ids = False

        return {'domain': domain}

    @api.onchange('technic_setting_id')
    def onchange_technic_setting_id(self):
        """Handle date range change."""
        domain = {}
        if self.technic_setting_id:
            self.technic_ids = self.env['technic.equipment'].search([('technic_setting_id','=',self.technic_setting_id.id),('owner_type','=','own_asset')])
            domain['technic_ids'] = [('technic_setting_id', '=', self.technic_setting_id.id)]
        else:
            self.technic_ids = False

        return {'domain': domain}

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        self.date_from = self.date_range_id.date_start
        self.date_to = self.date_range_id.date_end

    
    def get_fuel_prod_datas_datas(self, save_group_by, group_by, date_from, date_to, technic_ids, technic_setting_id, get_type='shift'):
        datas = {}
        categ_names = []
        series_date_fuel = []
        series_date_res = []
        series_date_prod = []
        series_day_fuel = []
        series_day_res = []
        series_day_prod = []
        series_night_fuel = []
        series_night_res = []
        series_night_prod = []

        real_group_by = 'GROUP BY 1,2'
        real_sel = 'ofr.shift,'
        # if get_type=='day':
        #     real_group_by = 'GROUP BY 1'
        #     real_sel = ''
        
        p_ids = ""
        if len(technic_ids)>1:
            p_ids = str(tuple(technic_ids.ids))
        elif len(technic_ids)==1:
            p_ids = "("+str(technic_ids[0].id)+")"

        query = """
            SELECT {2} as categ, 
            {4}
            sum(coalesce(ofr.product_qty,0)) as product_qty,
            coalesce(avg(ofr.avg_epx),0) as avg_epx,
            sum(coalesce(ofr.run_hour,0)) as run_hour,
            sum(coalesce(ofr.res_count,0)) as res_count,
            sum(coalesce(ofr.production_amount,0)) as production_amount
            FROM oil_fuel_fuel_report ofr
            left join technic_equipment te on (te.id=ofr.technic_id)
            WHERE ofr.date>='{0}' and ofr.date<='{1}' and ofr.technic_id in {3}
            {5}
            having sum(coalesce(ofr.product_qty,0))>0 or sum(coalesce(ofr.res_count,0))>0 or sum(coalesce(ofr.production_amount,0))>0
            ORDER BY 1
            """.format(date_from, date_to, group_by, p_ids, real_sel, real_group_by)
        print('query',query)
        self.env.cr.execute(query)
        query_result = self.env.cr.dictfetchall()
        df = pandas.DataFrame(query_result)
        catig_by_ids = []
        group_by_type = []
        try:
            catig_by_ids = sorted(df.groupby('categ').groups.keys())
        except Exception as e:
            print('error',e)
        
        for cat in catig_by_ids:
            cat_name = cat
            categ_names.append(cat_name)
            
            lens = len(df.loc[ (df['categ'] == cat) , 'avg_epx'])
            series_date_fuel.append(sum(df.loc[ (df['categ'] == cat) , 'avg_epx'])/lens)
            series_date_res.append(sum(df.loc[ (df['categ'] == cat) , 'res_count']))
            series_date_prod.append(sum(df.loc[ (df['categ'] == cat) , 'production_amount']))
            lens = len(df.loc[ (df['categ'] == cat) & (df['shift']=='day'), 'avg_epx']) or 1
            series_day_fuel.append(sum(df.loc[ (df['categ'] == cat) & (df['shift']=='day'), 'avg_epx'])/lens)
            series_day_res.append(sum(df.loc[ (df['categ'] == cat) & (df['shift']=='day'), 'res_count']))
            series_day_prod.append(sum(df.loc[ (df['categ'] == cat) & (df['shift']=='day'), 'production_amount']))
            lens = len(df.loc[ (df['categ'] == cat) & (df['shift']=='night'), 'avg_epx']) or 1
            series_night_fuel.append(sum(df.loc[ (df['categ'] == cat) & (df['shift']=='night'), 'avg_epx'])/lens)
            series_night_res.append(sum(df.loc[ (df['categ'] == cat) & (df['shift']=='night'), 'res_count']))
            series_night_prod.append(sum(df.loc[ (df['categ'] == cat) & (df['shift']=='night'), 'production_amount']))
        
        datas['gr_by'] = dict(self.fields_get()['group_by']['selection'])[save_group_by]
        datas['categ_names'] = categ_names
        datas['fuel_idle'] = {
        'min': self.env['technic.equipment.setting'].browse(technic_setting_id).fuel_low_idle, 
        'mid': self.env['technic.equipment.setting'].browse(technic_setting_id).fuel_medium_idle,
        'max': self.env['technic.equipment.setting'].browse(technic_setting_id).fuel_high_idle
        }
        datas['data_series'] = {}
        datas['data_series']['series_date_fuel'] = series_date_fuel
        datas['data_series']['series_date_res'] = series_date_res
        datas['data_series']['series_date_prod'] = series_date_prod

        datas['data_series']['series_day_fuel'] = series_day_fuel
        datas['data_series']['series_day_res'] = series_day_res
        datas['data_series']['series_day_prod'] = series_day_prod

        datas['data_series']['series_night_fuel'] = series_night_fuel
        datas['data_series']['series_night_res'] = series_night_res
        datas['data_series']['series_night_prod'] = series_night_prod

        datas['technic_name'] = ', '.join(technic_ids.mapped('display_name'))
        return datas
        # get_fuel_prod_datas()

    
    def get_fuel_prod_datas(self, group_by, date_from, date_to, technic_ids, technic_setting_id, get_type='shift'):
        if technic_ids:
            technic_ids = self.env['technic.equipment'].browse(technic_ids)
        datas = False
        
        technic_obj = self.env['technic.equipment']
        
        if not technic_setting_id and technic_ids:
            technic_setting_id = technic_ids[0].technic_setting_id.id
        save_group_by = group_by
        if group_by and date_from and date_to and technic_ids and technic_setting_id:
            str_group_by = ''
            if group_by=='day':
                group_by = "lpad(extract(month from date)::text, 2, '0')||'-'||lpad(extract(day from date)::text, 2, '0') "
            elif group_by == 'week':
                group_by = "lpad(extract(week from date)::text, 2, '0')"
            elif group_by =='month':
                group_by = "lpad(extract(month from date)::text, 2, '0')"
            else:
                group_by = 'extract(%s from date)'%(group_by)

            datas = self.get_fuel_prod_datas_datas(save_group_by, group_by, date_from, date_to, technic_ids, technic_setting_id)
            
        return datas



