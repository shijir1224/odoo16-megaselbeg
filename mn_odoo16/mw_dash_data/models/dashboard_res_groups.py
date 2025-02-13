# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools

class mw_dash_menu_group(models.Model):
    _name = 'mw.dash.menu.groups'
    _auto = False
    _description = 'Menu groups report'
    _order = 'menu_name'

    _rec_name = 'id'

#     group_name = fields.Char(string='Групп', readonly=True)
    menu_name = fields.Char(string='ЦЭС', readonly=True)
    user_name = fields.Char(string='Хэрэглэгч', readonly=True)
    
#     group_name = fields.Char(string='Групп', readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
            select menu as menu_name,login as user_name,id  
            from 
                (select max(g.id) as id, u.login,g.name, m.name as menu 
                from res_groups_users_rel r 
                    left join res_groups g on r.gid=g.id 
                    left join res_users u on r.uid=u.id 
                    left join ir_ui_menu_group_rel mr on mr.gid=g.id 
                    left join ir_ui_menu m on mr.menu_id=m.id  
                    group by login,g.name,m.name) 
            as foo group by menu,login,id
            )
        """ % (self._table)
        )