# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models

class SalesmanRouteReport(models.Model):
	_name = "salesman.route.report"
	_description = "Salesman route report"
	_auto = False
	_order = 'partner_id'

	partner_id = fields.Many2one('res.partner', string='Partner', readonly=True, index=True )
	user_id = fields.Many2one('res.users', string='Salesman', readonly=True, index=True )
	date_order = fields.Date(u'Date', readonly=True, index=True)
	check_route = fields.Selection([
			('yes',u'Тийм'), 
			('no',u'Үгүй'),
		], string='Маршрутын дагуу эсэх',)

	successful = fields.Integer('Successful', readonly=True, )
	unsuccessful = fields.Integer('Unsuccessful', readonly=True, )

	right_route = fields.Integer('Right route', readonly=True, )
	total = fields.Integer('Total', readonly=True, )

	state = fields.Selection([
			('successful','Successful'), 
			('closed','Closed'),
			('no_order','No order'),
			('other','Other'),
		], string='Type',)

	def init(self):
		tools.drop_view_if_exists(self.env.cr, self._table)
		self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
		SELECT  
			    ll.id as id,
			    ll.partner_id as partner_id,
				ll.user_id as user_id,
				ll.date_order as date_order,
				(CASE WHEN ll.check_route = 't' THEN 'yes' ELSE 'no' END) as check_route,
				(CASE WHEN ll.check_route = 't' THEN 1 ELSE 0 END) as right_route,
				(CASE WHEN ll.state = 'successful' THEN 1 ELSE 0 END) as successful,
				(CASE WHEN ll.state != 'successful' THEN 1 ELSE 0 END) as unsuccessful,
				ll.state as state,
				1 as total
			FROM salesman_route_performance_line as ll
		)""" % self._table)
