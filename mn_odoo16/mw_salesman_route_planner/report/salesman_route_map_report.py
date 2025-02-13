# -*- coding: utf-8 -*-

from odoo import tools
from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)

class SalesmanRouteMapReport(models.TransientModel):
	_name = "salesman.route.map.report"
	_description = "Salesman route map report"

	salesman_id = fields.Many2one('res.users', string=u'Борлуулагч', required=True, )
	date = fields.Date(u'Огноо', required=True,)

	# Salesman дата бэлдэх
	def get_user_location(self, user_id, date, context=None):
		datas = []
		dddd = date+'%'
		query = """
			SELECT lng, lat 
			FROM res_user_gps_location 
			WHERE create_date::text ilike '%s' and
			      user_id = %d and
			      lng > 0 and lat > 0
		""" % (dddd, user_id)
		self.env.cr.execute(query)
		result = self.env.cr.dictfetchall()
		for loc in result:
			datas.append({
				'lat': loc['lat'],
				'lng': loc['lng'],
			})
		_logger.info("----------------- Routes map data===%s=== %s",str(datas), query)
		return datas
