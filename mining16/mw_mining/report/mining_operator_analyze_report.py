# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api

class ReportOperatorProductionAnalyze(models.Model):
	_name = "report.operator.production.analyze"
	# _auto = False
	_description = "Report operator production analyze"
	# _rec_name = 'id'

	# cnt = fields.Integer(string=u'CNT', readonly=True)

	date = fields.Date('Date', readonly=True)
	branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
	shift = fields.Selection([('day', 'Өдөр'),('night', 'Шөнө')], 'Shift', readonly=True)
	part = fields.Char('Part', readonly=True)
	operator_id = fields.Many2one('hr.employee',string='Operator', readonly=True)
	technic_id = fields.Many2one('technic.equipment',string='Technic', readonly=True)
	report_wizard_id = fields.Integer(string=u'wizar id', readonly=True)
	dump_production_m3 = fields.Float(string='Dump Production m3', readonly=True)
	exca_production_m3 = fields.Float(string='Excavator Production m3', readonly=True)
	production_id = fields.Integer(string=u'Production id', readonly=True)

	# def init(self):
	# 	tools.drop_view_if_exists(self._cr, self._table)
	# 	self._cr.execute("""
	# 		CREATE or REPLACE view report_operator_production_analyze as (
	# 		SELECT mde.id as id,
	# 			count(mel.motohour_id) as cnt,
	# 			mde.date,
	# 			mde.branch_id,
	# 			mde.shift,
	# 			mde.part,
	# 			meol.operator_id,
	# 							mpel.dump_id as technic_id
	# 		FROM mining_motohour_entry_line AS mel
	# 		LEFT JOIN mining_motohour_entry_operator_line meol on (mel.id = meol.motohour_cause_id)
	# 					LEFT JOIN mining_production_entry_line mpel on (mpel.dump_id = mel.technic_id)
	# 		LEFT JOIN mining_daily_entry mde on (mde.id = mel.motohour_id)
	# 		group by mde.date, mde.branch_id, mde.shift, mde.part, meol.operator_id, mde.id
	# )""")

class report_mining_operator_analyze(models.Model):
	_name = 'report.mining.operator.analyze'
	_description = 'Report Mining Operator'
	_auto = False
	_order = 'date desc'

	date = fields.Date('Date', readonly=True)
	branch_id = fields.Many2one('res.branch', string='Branch', readonly=True)
	technic_id = fields.Many2one('technic.equipment', string='Technic', readonly=True)
	shift = fields.Selection([('day', 'Өдөр'),('night', 'Шөнө')], string='Shift', readonly=True)
	part = fields.Char(string='Part', readonly=True)
	operator_id = fields.Many2one('hr.employee',string='Operator', readonly=True)
	last_odometer_value = fields.Float(string='Last Odometer', readonly=True, group_operator='avg')
	first_odometer_value = fields.Float(string='First Odometer', readonly=True, group_operator='avg')
	# o_motohour_time = fields.Float(string='Мотоцаг гүйсэн', readonly=True)

	work_diff_time = fields.Float(string='Sum Hour',readonly=True)
	motohour_time = fields.Float(string='Motohour Time', readonly=True)
	repair_time = fields.Float(string='Repair Time', readonly=True)
	work_time = fields.Float(string='Work Time', readonly=True)
	diff_time = fields.Float(string='Other Time', readonly=True)
	production_time = fields.Float(string='Production Time', readonly=True)
	dump_production_m3 = fields.Float(string='Dump Production m3', readonly=True)
	exca_production_m3 = fields.Float(string='Exca Production m3', readonly=True)

	hr_type = fields.Selection([('main_emp', 'Main Employee'),('no_main_emp', 'ETT')], string='Operator Type', readonly=True)
	report_wizard_id = fields.Integer('wizar id', readonly=True)
	
	def _select(self):
		return """
			SELECT
				mol.id,
				md.branch_id,
				md.date,
				md.shift,
				md.part,
				mel.technic_id,
				mol.operator_id,
				mol.first_odometer_value,
				mol.last_odometer_value,
				-- mol.o_motohour_time,
				null::char as hr_type,
				-- CASE WHEN he.status in ('working','experiment','contract','maternity') THEN 'main_emp' ELSE 'no_main_emp' END as hr_type,
				sum(mel.work_diff_time)/count(mel.id) as work_diff_time,
				sum(mel.motohour_time)/count(mel.id) as motohour_time,
				sum(mel.repair_time)/count(mel.id) as repair_time,
				sum(mel.work_time)/count(mel.id) as work_time,
				sum(mel.work_time)/count(mel.id) - sum(mel.production_time)/count(mel.id) as diff_time,
				sum(mel.production_time)/count(mel.id) as production_time,
				null::int as report_wizard_id,
				0 as dump_production_m3,
				0 as exca_production_m3
		"""

	def _from(self):
		return """
			FROM mining_motohour_entry_operator_line mol
				left join mining_motohour_entry_line mel on (mol.motohour_cause_id = mel.id)
				left join mining_daily_entry md on (mel.motohour_id = md.id)
				left join hr_employee he on (he.id=mol.operator_id)
		"""

	def _where(self):
		return """
			WHERE
				mol.operator_id is not null
		"""

	def _group_by(self):
		return """
			group by
				mol.id,
				md.branch_id,
				md.date,
				md.shift,
				md.part,
				mel.technic_id,
				mol.operator_id,
				mol.first_odometer_value,
				mol.last_odometer_value,
				mol.o_motohour_time,
				-- he.status,
				hr_type
		"""

	def _order_by(self):
		return """
		"""
	
	def _select2(self):
		return """
			SELECT
				ropa.id*-300,
				md.branch_id,
				md.date,
				md.shift,
				md.part,
				ropa.technic_id,
				ropa.operator_id,
				0 as first_odometer_value,
				0 as last_odometer_value,
				null::char as hr_type,
				0 as work_diff_time,
				0 as motohour_time,
				0 as repair_time,
				0 work_time,
				0 as diff_time,
				0 as production_time,
				ropa.report_wizard_id,
				sum(ropa.dump_production_m3) as dump_production_m3,
				sum(ropa.exca_production_m3) as exca_production_m3
		"""

	def _from2(self):
		return """
			FROM report_operator_production_analyze ropa
				left join mining_daily_entry md on (ropa.production_id = md.id)
		"""

	def _where2(self):
		return """
			WHERE
				ropa.technic_id is not null
		"""

	def _group_by2(self):
		return """
			group by
				1,2,3,4,5,6,7,8,9,10,ropa.report_wizard_id
		"""

	def _order_by2(self):
		return """
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		self._cr.execute("""
			CREATE or REPLACE view {0} as
			SELECT *FROM (
			{1}
			{2}
			{3}
			{4}
			{5}
			union all
			{6}
			{7}
			{8}
			{9}
			{10}
			) as foo_operator
			""".format(self._table,self._select(),self._from(),self._where(),self._group_by(),self._order_by(),
					self._select2(),self._from2(),self._where2(),self._group_by2(),self._order_by2()))