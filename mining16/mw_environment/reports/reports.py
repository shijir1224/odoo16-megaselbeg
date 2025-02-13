# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime

class mw_environment_monthly_report(models.Model):
    _name = 'env.monthly.report'
    _description = 'Сарын мэдээний тайлан'
      

    def _get_year(self):
        year_list = []
        current_year = datetime.now().year
        for j in range(current_year, current_year - 10, -1):
            year_list.append((str(j), str(j)))
        return year_list

    def default_location(self):
        location = self.env['env.mining'].search([('id', '>=', 1)], limit=1)
        if location:
            return location.id
        else:
            return False

    year = fields.Selection(string='Он', selection=_get_year, required=True)
    mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', default=default_location, domain="[('is_active', '=', 'active')]")
    month = fields.Selection([
        ('01', '1-р сар'), ('02', '2-р сар'), ('03', '3-р сар'),
        ('04', '4-р сар'), ('05', '5-р сар'), ('06', '6-р сар'),
        ('07', '7-р сар'), ('08', '8-р сар'), ('09', '9-р сар'),
        ('10', '10-р сар'), ('11', '11-р сар'), ('12', '12-р сар'), ], string='Сар', required=True)

    _defaults = {
        'year': str(datetime.now().year),
        'month': str(datetime.now().month) if datetime.now().month >= 10 else '0'+str(datetime.now().month),
    }

    # @api.model
    # def create(self, vals):
    #     value = self.search([('mining_location', '=', vals['mining_location']), ('year', '=', vals['year']),
    #                          ('month', '=', vals['month'])])
    #     if value:
    #         raise Warning(_(u'Анхааруулга!!'),
    #                       _(u'Сонгосон уурхайд, сонгосон онд, сонгосон сарын тайлан үүссэн байгаа тул дахин үүсгэх боломжгүй.'))
    #
    #     res = super(mw_environment_monthly_report, self).create(vals)
    #     return res
    #
    # @api.model
    # def name_get(self):
    #     result = []
    #     for obj in self:
    #        if obj.mining_location:
    #           result.append((obj.id, obj.mining_location.name + ' : ' + obj.year + ' оны ' + obj.month + ' сар' ))
    #        else:
    #           result.append((obj.year + ' оны ' + obj.month + ' сар'))
    #     return result

    def action_monthly_report(self):
        datas = {
            'year': self.year,
            'month': self.month,
            'mining_location': self.mining_location.id,
            'mining': self.mining_location.name,
            'type': 'month'
        }
        # return self.env['report'].get_action('env_monthly_report_template', datas)
        return self.env.ref('mw_environment.env_monthly_report_template').action_monthly_report(self, data=datas)
        # return self.env.ref('mw_environment.env_monthly_report_template').action_monthly_report(self)
    
    def print_report(self):
        report_obj = self.env['env.training'].search([]).ids
        datas = {
            'year': self.year,
            'month': self.month,
            'mining_location': self.mining_location.id,
            'mining': self.mining_location.name,
            'type': 'month'
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'module_name.report_id',
            'datas': datas,
        }
        

class mw_environment_seasonal_report(models.TransientModel):
    _name = 'env.seasonal.report'
    _description = "Environmental Seasonal Report Wizard"

    def _get_year(self):
        year_list = []
        current_year = datetime.now().year
        for j in range(current_year, current_year - 10, -1):
            year_list.append((str(j), str(j)))
        return year_list

    year = fields.Selection(string='Он', selection=_get_year, required=True)
    season = fields.Selection([
        ('1', '1-р улирал'), ('2', '2-р улирал'), ('3', '3-р улирал'),
        ('4', '4-р улирал') ], string='Season')
    mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', domain="[('is_active', '=', 'active')]")

    _defaults = {
        'year': str(datetime.now().year),
    }

    def action_print_report(self):
        datas = {
            'year': self.year,
            'month': self.season if self.season else 'all',
            'mining_location': self.mining_location.id,
            'mining': self.mining_location.name,
            'type': 'season'
        }
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [],
                                              'env_monthly_report_template', datas)

class abstract_monthly_report(models.AbstractModel):
    _name = 'report.env.monthly.report.template'
    _description = 'Report env monthly report template'

    def render_html(self, docids, data=None):

        report_obj = self.env['report']
        report = report_obj._get_report_from_name('env_monthly_report_template')
        if data['type'] == 'season':
            if data['month'] == 'all':
                last = '12'
                current = "(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)"
            elif data['month'] == '1':
                last = '03'
                current = "(1, 2, 3)"
            elif data['month'] == '2':
                last = '06'
                current = "(4, 5, 6)"
            elif data['month'] == '3':
                last = '09'
                current = "(7, 8, 9)"
            else:
                last = '12'
                current = "(10, 11, 12)"
        else:
            current = "(" + data['month'] + ")"
            last = data['month']
        if data['mining_location']:
            where = " WHERE mining_location = " + str(data['mining_location']) + " AND "
        else:
            where =" WHERE "

        self._cr.execute("""SELECT p.name as topic, CASE t.trainee_type WHEN 'employees' THEN 'Ажилтнууд' 
                                                                     WHEN 'contracts' THEN 'Гэрээт'
                                                                     WHEN 'visitors' THEN 'Зочид' END as trainee_type, 
                                   t.alltraining, tmp.len, COALESCE(t.notraining,0) notraining
                            FROM (SELECT topic_id, trainee_type, COUNT(*) alltraining,
                                        COUNT(CASE WHEN DATE_PART('month', training_date) IN """ + current + """ THEN 1 END) notraining
                                        FROM env_training """ + where +
                                        """ DATE_PART('year', training_date)=""" + data['year'] +
                                        """ AND DATE_PART('month', training_date)<=""" + last +
                                        """ GROUP BY trainee_type, topic_id) t
                            LEFT JOIN (SELECT COUNT(DISTINCT topic_id) len, trainee_type
                                        FROM env_training """ + where +
                                        """ DATE_PART('year', training_date)=""" + data['year'] +
                                        """ AND DATE_PART('month', training_date)<=""" + last +
                                        """ GROUP BY trainee_type) tmp ON t.trainee_type=tmp.trainee_type
                            LEFT JOIN env_parameter p ON t.topic_id=p.id
                            ORDER BY trainee_type ASC """
                         )
        training = self._cr.dictfetchall()

        self._cr.execute("""SELECT CASE t.inspector_category WHEN 'internal' THEN 'Дотоод хяналт шалгалт' 
                                                 WHEN 'external' THEN 'Хөндлөнгийн байгууллагын шалгалт' END category, 
                                        CASE t.inspector WHEN 'department' THEN 'Үйлдвэр уурхай, нэгж хэсэг' 
                                                 WHEN 'company' THEN 'Компанийн төв оффисоос'
                                                 WHEN 'city' THEN 'Сумаас'
                                                 WHEN 'state' THEN 'Аймгаас'
                                                 WHEN 'country' THEN 'Улсаас' END inspector, 
                                           t.allinspection, tmp.len, COALESCE(t.noinspection,0) noinspection
                                    FROM (SELECT inspector_category, inspector, COUNT(*) allinspection,
                                            COUNT(CASE WHEN DATE_PART('month', inspection_date) IN """ + current + """ THEN 1 END) noinspection
                                            FROM env_inspection """ + where +
                                             """ DATE_PART('year', inspection_date)=""" + data['year'] +
                                             """ AND DATE_PART('month', inspection_date)<=""" + last +
                                             """ GROUP BY inspector_category, inspector) t
                                    LEFT JOIN (SELECT COUNT(DISTINCT inspector) len, inspector_category
                                                 FROM env_inspection """ + where +
                                                 """ DATE_PART('year', inspection_date)=""" + data['year'] +
                                                 """ AND DATE_PART('month', inspection_date)<=""" + last +
                                                 """ GROUP BY inspector_category) tmp ON t.inspector_category=tmp.inspector_category
                                    ORDER BY category ASC, inspector ASC """
                        )
        inspection = self._cr.dictfetchall()

        self._cr.execute("""SELECT p.name as voilation, t.allviolation, t.fixed fixedviolation, t.noviolation
                            FROM (SELECT violation, COUNT(*) allviolation, 
                                COUNT(CASE WHEN DATE_PART('month', accident_date) IN """ + current + """ AND is_fixed THEN 1 END) fixed,
                                COUNT(CASE WHEN DATE_PART('month', accident_date) IN """ + current + """ THEN 1 END) noviolation
                                FROM env_accident """ + where +
                                """ DATE_PART('year', accident_date)=""" + data['year'] +
                                """ AND DATE_PART('month', accident_date)<=""" + last +
                                """ GROUP BY violation) t
                            LEFT JOIN env_parameter p ON t.violation=p.id
                            ORDER BY p.name ASC """
                         )
        accident = self._cr.dictfetchall()

        self._cr.execute("""SELECT p.name as dedication, p1.name as source, t.allwater, tmp.len, t.nowater
                                    FROM (SELECT w.water_well, l.water_source, SUM(l.amount) as allwater, 
                                                SUM(CASE WHEN CAST(l.month AS INTEGER) IN """ + current + """ THEN l.amount ELSE 0 END) nowater 
                                                FROM env_water_line as l
                                                LEFT JOIN env_water w ON l.water_id=w.id """ + where +
                                                 """ w.water_type='usage' AND w.year='""" + data['year'] +"""' AND l.month<='""" + last +
                                                 """' GROUP BY w.water_well, l.water_source) t
                                    LEFT JOIN (SELECT w.water_well, COUNT(DISTINCT COALESCE(l.water_source,0)) len
                                                FROM env_water_line as l
                                                LEFT JOIN env_water w ON l.water_id=w.id """ + where +
                                                 """ w.water_type='usage' AND w.year='""" + data['year'] +"""' AND l.month<='""" + last +
                                                 """' GROUP BY w.water_well) tmp ON t.water_well=tmp.water_well
                                    LEFT JOIN env_parameter p ON t.water_well=p.id
                                    LEFT JOIN env_parameter p1 ON t.water_source=p1.id
                                    ORDER BY p.name ASC, p1.name ASC """
                         )
        water = self._cr.dictfetchall()

        self._cr.execute("""SELECT w.water_type, SUM(l.amount) as allwater, 
                                    SUM(CASE WHEN CAST(l.month AS INTEGER) IN """ + current + """ THEN l.amount ELSE 0 END) as nowater 
                                    FROM env_water_line as l
                                    LEFT JOIN env_water as w ON l.water_id=w.id """ + where +
                         """ w.water_type='dirty' AND w.year='""" + data['year'] + """' AND l.month<='""" + last +
                         """' GROUP BY w.water_type """
                         )
        used_water = self._cr.dictfetchall()

        self._cr.execute("""SELECT p.name as waste, t.amount, t.reused_amount, t.allamount,
                                CASE t.waste_category WHEN 'waste1' THEN 'Ахуйн' 
                                     WHEN 'waste2' THEN 'Дахин боловсруулах'
                                     WHEN 'waste3' THEN 'Аюултай'
                                     WHEN 'waste4' THEN 'Дахин ашиглах'
                                     WHEN 'waste5' THEN 'Дахин ашиглах боломжгүй' END category
                                FROM (SELECT waste_category, waste_type, SUM(amount) allamount, 
                                        SUM(CASE WHEN CAST(SUBSTRING(year_month,6) AS INTEGER) IN """ + current + """ THEN amount ELSE 0 END) amount, 
                                        SUM(CASE WHEN CAST(SUBSTRING(year_month,6) AS INTEGER) IN """ + current + """ THEN reused_amount ELSE 0 END) reused_amount
                                    FROM env_waste  """ + where +
                                    """ SUBSTRING(year_month,1,4)='""" + data['year'] +
                                    """' AND SUBSTRING(year_month,6)<='""" + last +
                                    """' GROUP BY waste_category, waste_type) t 
                                    LEFT JOIN env_parameter p ON t.waste_type=p.id 
                                    ORDER BY t.waste_category ASC, p.name ASC """
                         )
        waste = self._cr.dictfetchall()

        self._cr.execute("""SELECT p.name as location, SUM(l.amount) as allamount,
                                SUM(CASE WHEN CAST(l.month AS INTEGER) IN """ + current + """ THEN l.amount ELSE 0 END) amount
                                FROM env_rehab_land l
                                LEFT JOIN env_rehab r ON r.id=l.rehab_id
                                LEFT JOIN env_parameter p ON r.rehab_location=p.id """ + where +
                                """ r.year='""" + data['year'] + """' AND l.month<='""" + last +
                                """' GROUP BY p.name ORDER BY p.name ASC """
                         )
        land = self._cr.dictfetchall()

        self._cr.execute("""SELECT p.name as location, p2.name as type, t.amount, t.allamount, tmp.len, tmp2.len len2,
                                        CASE t.rehab_category WHEN 'rehab1' THEN 'Биологийн' 
                                            WHEN 'rehab2' THEN 'Техникийн' END category
                                    FROM (
                                        SELECT r.rehab_location, l.rehab_type, SUM(l.amount) as allamount, l.rehab_category,
                                            SUM(CASE WHEN CAST(l.month AS INTEGER) IN """ + current + """ THEN l.amount ELSE 0 END) amount
                                            FROM env_rehab_line l
                                            LEFT JOIN env_rehab r ON r.id=l.rehab_id
                                        """ + where + """  r.year='""" + data['year'] + """' AND l.month<='""" + last +
                                        """' GROUP BY r.rehab_location, l.rehab_category, l.rehab_type
                                    )t
                                    LEFT JOIN (SELECT r.rehab_location, COUNT(DISTINCT l.rehab_type) len FROM env_rehab_line l
                                               LEFT JOIN env_rehab r ON r.id=l.rehab_id
                                               """ + where + """  r.year='""" + data['year'] + """' AND l.month<='""" + last +
                                               """' GROUP BY r.rehab_location
                                              ) AS tmp ON tmp.rehab_location=t.rehab_location
                                    LEFT JOIN (SELECT r.rehab_location, l.rehab_category, COUNT(DISTINCT l.rehab_type) len 
                                               FROM env_rehab_line l
                                               LEFT JOIN env_rehab r ON r.id=l.rehab_id
                                               """ + where + """  r.year='""" + data['year'] + """' AND l.month<='""" + last +
                                               """' GROUP BY r.rehab_location, l.rehab_category
                                               ) AS tmp2 ON tmp2.rehab_location=t.rehab_location AND tmp2.rehab_category=t.rehab_category
                                    LEFT JOIN env_parameter p ON t.rehab_location=p.id
                                    LEFT JOIN env_parameter p2 ON t.rehab_type=p2.id  
                                ORDER BY p.name ASC, t.rehab_category, p2.name """
                         )
        rehab = self._cr.dictfetchall()

        self._cr.execute("""SELECT p.name as animal, SUM(a.number) as allanimal,
                                        SUM(CASE WHEN CAST(SUBSTRING(year_month,6) AS INTEGER) IN """ + current + """ THEN a.number ELSE 0 END) as noanimal
                                        FROM env_animal a
                                        LEFT JOIN env_parameter p ON a.animal=p.id """ + where +
                                            """  SUBSTRING(a.year_month,1,4)='""" + data['year'] +
                                            """' AND SUBSTRING(a.year_month,6)<='""" + last +
                         """' GROUP BY p.name ORDER BY p.name ASC """
                         )
        animal = self._cr.dictfetchall()

        self._cr.execute("""SELECT p.name as type,t.allamount, t.amount,
                                        CASE t.expense_category WHEN 'expense1' THEN 'Хуулийн нийцлийг хангах' 
                                             WHEN 'expense2' THEN 'Ногоон байгууламж'
                                             WHEN 'expense3' THEN 'Нөхөн сэргээлт'
                                             WHEN 'expense4' THEN 'Бусад ажлууд' END category
                                 FROM (SELECT expense_type, expense_category, SUM(amount) allamount, 
                                                    SUM(CASE WHEN DATE_PART('month', expense_date) IN """ + current +""" THEN amount ELSE 0 END) amount
                                                    FROM env_expense  """ + where +
                                                     """ DATE_PART('year', expense_date)=""" + data['year'] +
                                                     """ AND DATE_PART('month', expense_date)<=""" + last +
                                                     """ GROUP BY expense_type, expense_category) t 
                                 LEFT JOIN env_parameter p ON t.expense_type=p.id 
                                 ORDER BY t.expense_category ASC, p.name ASC """
                         )
        expense = self._cr.dictfetchall()

        self._cr.execute("""SELECT p.name as activity, g.garden_location, g.amount,
                                CASE g.uom WHEN 'garden3' THEN 'ширхэг' 
                                WHEN 'garden4' THEN 'метр2' END uom
                           FROM env_garden g 
                           LEFT JOIN env_parameter p ON g.garden_activity=p.id """ + where +
                         """ SUBSTRING(g.year_month,1,4)='""" + data['year'] +
                         """' AND CAST(SUBSTRING(g.year_month,6) AS INTEGER) IN """ + current +
                         """ ORDER BY p.name ASC """
                         )
        garden = self._cr.dictfetchall()

        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': self,
            'mining': data['mining'],
            'title': "Байгаль орчны сарын мэдээ" if data['type']=='month' else "Байгаль орчны улирлын мэдээ",
            'year_month': data['year']+" оны "+data['month']+" сар" if data['type']=='month' else data['year']+" оны "+data['month']+"-р улирал" if data['month']!='all' else data['year'],
            'base_url': self.env['ir.config_parameter'].get_param('report.url'),
            'heading': "Энэ сард" if data['type']=='month' else "Энэ улиралд",
            'training': training,
            'inspection': inspection,
            'accident': accident,
            'water': water,
            'used_water': used_water,
            'waste': waste,
            'land': land,
            'rehab': rehab,
            'animal': animal,
            'expense': expense,
            'garden': garden
        }

        return report_obj.render('env_monthly_report_template', docargs)

class mw_environment_monitor_report(models.TransientModel):
    _name = 'env.monitor.report'
    _description = "Environmental Monitor Report Wizard"

    mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', domain="[('is_active', '=', 'active')]")
    monitor_category = fields.Selection([
        ('monitor3', 'Агаар'),
        ('monitor1', 'Ус'),
        ('monitor2', 'Хөрс')], string='Шинжилгээний ангилал', required=True)
    monitor_type = fields.Many2one('env.parameter', string='Шинжлүүлсэн үзүүлэлт', required=True, domain="[('type','=','monitor_type'),('category','=',monitor_category),('is_active', '=', 'active')]")
    monitor_location = fields.Many2one('env.mining.line', string='Monitor Location', required=True, domain="[('mining_id','=',mining_location),('monitor_category','=',monitor_category),('is_active','=', 'active')]")
    
    @api.depends('mining_location','monitor_category','monitor_location','monitor_type')
    def _get_dates(self):
        if self.mining_location and self.monitor_category and self.monitor_location and self.monitor_type:
            self.monitors = self.env['env.monitor'].search([('mining_location','=',self.mining_location.id),('monitor_category','=',self.monitor_category),('monitor_location','=', self.monitor_location.id),('monitor_type','=', self.monitor_type.id)], limit=10, order ="monitor_date DESC")

    def _after_dates_set(self):
        """
        Hook that fires after a user manually sets the field themselves. For this field, we don't need to do anything.
        """
    monitors = fields.Many2many('env.monitor', string='Monitors', required=True, compute=_get_dates, inverse="_after_dates_set", store = True, domain="[('mining_location','=',mining_location),('monitor_category','=',monitor_category),('monitor_location','=', monitor_location),('monitor_type','=', monitor_type)]")


    def action_print_report(self):
        dates = []
        for monitor in self.monitors:
            dates.append(monitor.monitor_date)
        dates.sort()

        datas = {
            'mining_name': self.mining_location.name,
            'location_name': self.monitor_location.code + " (" + self.monitor_location.name + ")",
            'type_name': dict(self._fields['monitor_category'].selection).get(self.monitor_category) +', ' + self.monitor_type.name,
            'monitors': self.monitors.ids,
            'dates': dates
        }
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [],'env_monitor_report_template', datas)

class abstract_monitor_report(models.AbstractModel):
    _name = 'report.env.monitor.report.template'
    _description = 'report env monitor report template'


    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('env_monitor_report_template')

        strdates =""
        for date in data['dates']:
            strdates += ', "' + date + '" text '

        where = " WHERE m.id IN " + str(data["monitors"]).replace("[","(").replace("]",")")

        self._cr.execute("""
                        SELECT ct.*, s.name, s.uom, s.normal_start, s.normal_end 
                        FROM  crosstab(
                                'SELECT c.indicator, m.monitor_date, c.amount
                                    FROM env_monitor_component c
									LEFT JOIN env_monitor m ON c.monitor_id=m.id """ + where + """
                                    ORDER BY c.indicator ASC, m.monitor_date ASC',
								'SELECT monitor_date FROM env_monitor m """ + where +""" ORDER BY m.monitor_date ASC'
                            ) AS ct ("indicator" integer"""+strdates+""")
                        LEFT JOIN env_standard s ON ct.indicator=s.id
                        """)
        rows = self._cr.dictfetchall()

        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': self,
            'mining_name': data['mining_name'],
            'location_name': data['location_name'],
            'monitor_name': data['type_name'],
            'base_url': self.env['ir.config_parameter'].get_param('report.url'),
            'cols': data["dates"],
            'rows': rows,
        }

        return report_obj.render('env_monitor_report_template', docargs)

class mw_environment_tree_report(models.TransientModel):
    _name = 'env.tree.report'
    _description = "Environmental Tree Report Wizard"

    def _get_year(self):
        year_list = []
        current_year = datetime.now().year
        for j in range(current_year, current_year - 10, -1):
            year_list.append((str(j), str(j)))
        return year_list

    year = fields.Selection(string='Он', selection=_get_year, required=True)
    mining_location = fields.Many2one('env.mining', string='Үйлдвэр, Уурхай', domain="[('is_active', '=', 'active')]")

    _defaults = {
        'year': str(datetime.now().year),
    }

    def action_print_report(self):
        datas = {
            'year': self.year,
            'mining_location': self.mining_location.id,
            'mining': "Бүгд" if not self.mining_location else self.mining_location.name
        }
        return self.pool['report'].get_action(self.env.cr, self.env.uid, [],
                                              'env_tree_report_template', datas)

class abstract_tree_report(models.AbstractModel):
    _name = 'report.env.tree.report.template'
    _description = "Report env tree report template"

    def render_html(self, docids, data=None):

        report_obj = self.env['report']
        report = report_obj._get_report_from_name('env_tree_report_template')

        if data['mining_location']:
            where = " WHERE mining_location = " + str(data['mining_location'])
        elif self.env.user.has_group('group_env_general'):
            where = " WHERE 1=1"
        else:
            where = " WHERE m.sector_id = " + str(self.env.user.sector_id.id)


        lastyear=int(data['year'])-1
        self._cr.execute("""
                        SELECT p.name AS tree_name, m.name AS location_name, COALESCE(spring.new_number,0) AS nspring, COALESCE(fall.new_number,0) AS nfall,
                        COALESCE(lastyear.number,0) AS lastyear, COALESCE(spring.number,0) AS spring, COALESCE(fall.number,0) AS fall, 
                        COALESCE(spring.number,0)+COALESCE(spring.new_number,0) AS tspring,
                        CASE WHEN COALESCE(lastyear.number,0)>0 THEN COALESCE(spring.number,0)*100/COALESCE(lastyear.number,0) ELSE 0 END AS spercent,
                        CASE WHEN COALESCE(spring.number,0)>0 THEN COALESCE(fall.number,0)*100/(COALESCE(spring.number,0)+COALESCE(spring.new_number,0)) ELSE 0 END AS fpercent
                        FROM (SELECT DISTINCT mining_location, tree FROM env_tree) t
                        LEFT JOIN env_parameter p ON t.tree=p.id
                        LEFT JOIN env_mining m ON t.mining_location=m.id
                        LEFT JOIN (
                                SELECT tree, mining_location as location, number + COALESCE(new_number) number
                                FROM env_tree 
                                WHERE year='""" + str(lastyear) + """' AND season='fall' 
                            )lastyear ON t.tree= lastyear.tree AND t.mining_location=lastyear.location
                        LEFT JOIN (
                                SELECT tree, mining_location as location, number, new_number
                                FROM env_tree 
                                WHERE year='""" + data['year'] + """' AND season='spring' 
                            )spring ON t.tree= spring.tree AND t.mining_location=spring.location
                        LEFT JOIN (
                                SELECT tree, mining_location as location, number, new_number
                                FROM env_tree 
                                WHERE year='""" + data['year'] + """' AND season='fall' 
                            )fall ON t.tree= fall.tree AND t.mining_location=fall.location """ + where+
                        """ ORDER BY m.name ASC, p.name ASC """
                        )
        rows = self._cr.dictfetchall()

        docargs = {
            'doc_ids': self.ids,
            'doc_model': report.model,
            'docs': self,
            'mining': data['mining'],
            'year': data['year'],
            'base_url': self.env['ir.config_parameter'].get_param('report.url'),
            'rows': rows,
        }
        return report_obj.render('env_tree_report_template', docargs)



