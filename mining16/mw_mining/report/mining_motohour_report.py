# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

class report_mining_motohour(models.Model):
	_name = 'report.mining.motohour'
	_description = 'Motohour entry report'
	_auto = False
	_order = 'date desc'

	date = fields.Date(string='Date', readonly=True)
	branch_id = fields.Many2one('res.branch', string='Branch', readonly=True)
	technic_id = fields.Many2one('technic.equipment', string='Technic', readonly=True)
	shift = fields.Selection([('day', 'Өдөр'),('night', 'Шөнө')], string='Shift', readonly=True)
	cause_id = fields.Many2one('mining.motohours.cause', string='Cause', readonly=True)
	diff_time = fields.Float(string='Cause time', readonly=True)
	technic_type = fields.Selection(TECHNIC_TYPE, string='Technic type', readonly=True)
	location_id = fields.Many2one('mining.location', string='Location', readonly=True)
	part = fields.Char(string='Part', readonly=True)
	owner_type = fields.Selection(OWNER_TYPE, string='Owner type',readonly=True)
	percentage = fields.Integer(string='Percentage', readonly=True)
	cause_name = fields.Char(string='Cause name', readonly=True)
	description = fields.Char('Description', readonly=True)
	repair_system_id = fields.Many2one('maintenance.damaged.type', string='Зогссон систем', readonly=True)

	def _select(self):
		return """
			SELECT
					min(mcl.id) as id,
					mcl.cause_id  as cause_id,
					mcl.location_id,
					min(ml.technic_type) as technic_type,
					min(mmc.cause_name) as cause_name,
					sum(mcl.diff_time) as diff_time,
					min(mcl.percentage) as percentage,
					te.owner_type,
					md.date,
					md.part,
					md.shift,
					ml.technic_id,
					md.branch_id,
					mcl.repair_system_id,
					mcl.description
		"""

	def _from(self):
		return """
			FROM mining_motohour_entry_cause_line mcl
			LEFT JOIN mining_motohour_entry_line ml ON (mcl.motohour_cause_id = ml.id)
			LEFT JOIN mining_daily_entry md on (md.id = ml.motohour_id)
			LEFT JOIN technic_equipment te on (te.id = ml.technic_id)
			LEFT JOIN mining_motohours_cause mmc ON (mmc.id = mcl.cause_id)
		"""

	def _where(self):
		return """
		"""

	def _group_by(self):
		return """
			GROUP BY
					mcl.id,
					mcl.location_id,
					mcl.cause_id,
					md.branch_id,
					md.part,
					md.shift,
					md.date,
					te.owner_type,
					ml.technic_id,
					mcl.repair_system_id,
					mcl.description
		"""

	def _order_by(self):
		return """
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE or REPLACE view {0} as
			{1}
			{2}
			{3}
			{4}
			{5}
			""".format(self._table,self._select(),self._from(),self._where(),self._group_by(),self._order_by()))