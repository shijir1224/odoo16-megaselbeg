# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api
from odoo.addons.mw_technic_equipment.models.technic_equipment import TECHNIC_TYPE
from odoo.addons.mw_technic_equipment.models.technic_equipment import OWNER_TYPE

class OilFuelReport(models.Model):
	_name = 'oil.fuel.report'
	_auto = False
	_description = 'Oil fuel report'
	_order = 'date, shift'

	_rec_name = 'id'

	date = fields.Datetime('Огноо', readonly=True)
	line_id = fields.Many2one('oil.fuel.line',string='Мөр', readonly=True)
	oil_id = fields.Many2one('oil.fuel',string='Бүртгэл', readonly=True)
	shift = fields.Selection([('day','Өдөр'), ('night','Шөнө')], string='Ээлж', readonly=True)
	state = fields.Selection([('draft','Ноорог'), ('done','Дууссан')], readonly=True, string='Төлөв')
	picking_id = fields.Many2one('stock.picking', string='Зарлагын баримт', readonly=True)
	partner_id = fields.Many2one('res.partner',string='Нийлүүлэгч', readonly=True)
	# branch_id = fields.Many2one('res.branch', string='Салбар', readonly=True)
	location_id = fields.Many2one('stock.location', string='Байрлал', readonly=True)
	product_id = fields.Many2one('product.product', string='Бараа', readonly=True)
	categ_id = fields.Many2one('product.category', string='Барааны Ангилал', readonly=True)
	technic_id = fields.Many2one('technic.equipment', string='Техник', readonly=True)
	product_qty = fields.Float(string='Авсан тос', readonly=True)

	technic_type = fields.Selection(TECHNIC_TYPE, string ='Техникийн төрөл', readonly=True, required=False)
	model_id = fields.Many2one('technic.model.model', string=u'Модел', readonly=True,)
	owner_type = fields.Selection(OWNER_TYPE, 
		string=u'Эзэмшлийн төрөл', readonly=True,)
	oil_type = fields.Selection([('add','ADD'),('pm','PM'),('rpc','RPC')],string='Тосны төрөл')
	oil_type_from = fields.Selection([('oil','Тосны Бүртгэл'),('wo','Work order агуулахын бүртгэл')], string='Хаанаас зарлагадсан')
	technic_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техникийн тохиргоо', readonly=True,)
	technic_partner_id = fields.Many2one('res.partner', string='Technic Partner', readonly=True)
	res_count = fields.Float(string='Ресс', readonly=True)
	production_amount = fields.Float(string='Бүтээл', readonly=True)
	avg_epx = fields.Float(string='1МЦЗ', readonly=True, group_operator='avg')

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)

		self._cr.execute("""
			CREATE OR REPLACE VIEW %s AS (
				SELECT
					ofl.id,
					ofl.id as line_id,
					ofl.parent_id as oil_id,
					ofl.oil_type as oil_type,
					of.shift,
					of.state,
					(of.date::text||' 00:00:00')::timestamp as date,
					of.partner_id,
					of.picking_id,
					of.warehouse_id,
					of.location_id,
					ofl.product_id,
					pt.categ_id,
					ofl.technic_id,
					te.owner_type,
					te.technic_type,
					te.model_id,
					te.technic_setting_id,
					te.partner_id as technic_partner_id,
					'oil' as oil_type_from,
					ofl.product_qty,
					0 as res_count,
					0 as production_amount,
					ofl.avg_epx as avg_epx
					FROM oil_fuel_line AS ofl 
					LEFT JOIN oil_fuel AS of ON (ofl.parent_id=of.id)
					LEFT JOIN product_product AS pp ON (ofl.product_id=pp.id)
					LEFT JOIN product_template AS pt ON (pp.product_tmpl_id=pt.id)
					LEFT JOIN technic_equipment AS te ON (te.id=ofl.technic_id)
				WHERE of.type='oil'
				UNION ALL
				SELECT
					sml.id*-1,
					null::int as line_id,
					null::int as oil_id,
					'pm' as oil_type,
					null::text as shift,
					null::text as state,
					sm.date,
					null::int as partner_id,
					sm.picking_id,
					sl.set_warehouse_id,
					sml.location_id,
					sm.product_id,
					pt.categ_id,
					sm.technic_id,
					te.owner_type,
					te.technic_type,
					te.model_id,
					te.technic_setting_id,
					te.partner_id as technic_partner_id,
					'wo' as oil_type_from,
					sml.qty_done as product_qty,
					0 as res_count,
					0 as production_amount,
					null::int as avg_epx
					FROM stock_move_line AS sml
					LEFT JOIN stock_move AS sm ON (sml.move_id=sm.id)
					LEFT JOIN product_product AS pp ON (sm.product_id=pp.id)
					LEFT JOIN product_template AS pt ON (pp.product_tmpl_id=pt.id)
					LEFT JOIN technic_equipment AS te ON (te.id=sm.technic_id)
					LEFT JOIN stock_location AS sl ON (sl.id=sml.location_id)
					LEFT JOIN stock_location AS sl2 ON (sl2.id=sml.location_dest_id)
				WHERE sm.state='done' and ((sl.usage='internal' and sl2.usage!='internal') or (sl.usage!='internal' and sl2.usage='internal'))
				and pt.categ_id in (select categ_id from oil_report_product_category_rel)
				and sm.picking_id not in (select picking_id from oil_fuel where picking_id is not null)
				UNION ALL
				SELECT
					mpr.id,
					null::int as line_id,
					null::int as oil_id,
					null as oil_type,
					mpr.shift as shift,
					null::char state,
					mpr.date as date,
					null::int partner_id,
					null::int picking_id,
					null::int warehouse_id,
					null::int location_id,
					null::int as product_id,
					null::int categ_id,
					te.id as technic_id,
					te.owner_type,
					te.technic_type,
					te.model_id,
					te.technic_setting_id,
					te.partner_id as technic_partner_id,
					null as oil_type_from,
					0 as product_qty,
					mpr.res_count as res_count,
					mpr.sum_m3 as production_amount,
					null::int as avg_epx
					FROM mining_production_report AS mpr 
					LEFT JOIN technic_equipment AS te ON (te.id=mpr.excavator_id or te.id=mpr.dump_id)
					LEFT JOIN technic_equipment_setting AS tes ON (tes.id=te.technic_setting_id)
				WHERE mpr.excavator_id is not null or mpr.dump_id is not null
				
			)
		""" % (self._table)
		)


class oil_fuel_fuel_report(models.Model):
	_name = 'oil.fuel.fuel.report'
	_auto = False
	_description = 'Oil fuel fuel report'
	_order = 'date, shift'

	_rec_name = 'id'

	date = fields.Date(string='Огноо', readonly=True)
	line_id = fields.Many2one('oil.fuel.line',string='Мөр', readonly=True)
	oil_id = fields.Many2one('oil.fuel',string='Бүртгэл', readonly=True)
	shift = fields.Selection([('day','Өдөр'), ('night','Шөнө')], string='Ээлж', readonly=True)
	state = fields.Selection([('draft','Ноорог'), ('done','Дууссан')], readonly=True, string='Төлөв')
	picking_id = fields.Many2one('stock.picking', string='Зарлагын баримт', readonly=True)
	partner_id = fields.Many2one('res.partner', string='Нийлүүлэгч', readonly=True)
	branch_id = fields.Many2one('res.branch', string='Салбар', readonly=True)
	tech_branch_id = fields.Many2one('res.branch', string='ТХ Салбар', readonly=True)
	location_id = fields.Many2one('stock.location', string='Байрлал', readonly=True)
	product_id = fields.Many2one('product.product', string='Бараа', readonly=True)
	categ_id = fields.Many2one('product.category', string='Барааны Ангилал', readonly=True)
	technic_id = fields.Many2one('technic.equipment', string='Техник', readonly=True)
	product_qty = fields.Float(string='Авсан түлш', readonly=True)

	technic_type = fields.Char(string ='Техникийн төрөл', readonly=True, required=False)
	model_id = fields.Many2one('technic.model.model', string=u'Модел', readonly=True,)
	technic_setting_id = fields.Many2one('technic.equipment.setting', string=u'Техникийн тохиргоо', readonly=True,)
	owner_type = fields.Selection(OWNER_TYPE, 
		string=u'Эзэмшлийн төрөл', readonly=True,)
	# norm_diff = fields.Float('Нормын зөрүү', readonly=True)
	moto_hour = fields.Float('Мотоцаг', readonly=True)
	current_km = fields.Float('КМ', readonly=True)
	run_hour = fields.Float('АМЦ', readonly=True)
	
	fuel_low_idle = fields.Float(string='Fuel low idle', group_operator='avg')
	fuel_medium_idle = fields.Float(string='Fuel medium idle', group_operator='avg')
	fuel_high_idle = fields.Float(string='Fuel high idle', group_operator='avg')
	avg_epx = fields.Float(string='1МЦЗ', readonly=True, group_operator='avg')
	res_count = fields.Float(string='Ресс', readonly=True)
	production_amount = fields.Float(string='Бүтээл', readonly=True)
	technic_partner_id = fields.Many2one('res.partner', string='Technic Partner', readonly=True)
	display_name = fields.Char(string='Display name')

	def _select(self):
		return """
			SELECT
				ofl.id,
				ofl.id as line_id,
				ofl.parent_id as oil_id,
				of.shift,
				of.state,
				of.date,
				of.partner_id,
				of.picking_id,
				of.warehouse_id,
				of.location_id,
				sw.branch_id,
				te.branch_id as tech_branch_id,
				of.type,
				ofl.product_id,
				pt.categ_id,
				ofl.technic_id,
				te.owner_type,
				te.technic_type,
				te.model_id,
				ofl.moto_hour,
				ofl.current_km,
				ofl.run_hour,
				ofl.product_qty,
				-- ofl.norm_diff,
				te.technic_setting_id,
				te.partner_id as technic_partner_id,
				ofl.avg_epx as avg_epx,
				0  as res_count,
				0 as production_amount,
				tes.fuel_low_idle,
				tes.fuel_medium_idle,
				tes.fuel_high_idle,
				'' as display_name
		"""
	def _from(self):
		return """
			FROM oil_fuel_line AS ofl 
				LEFT JOIN oil_fuel AS of ON (ofl.parent_id=of.id)
				LEFT JOIN stock_location AS sl ON (of.location_id=sl.id)
				LEFT JOIN stock_warehouse AS sw ON (sl.set_warehouse_id=sw.id)
				LEFT JOIN product_product AS pp ON (ofl.product_id=pp.id)
				LEFT JOIN product_template AS pt ON (pp.product_tmpl_id=pt.id)
				LEFT JOIN technic_equipment AS te ON (te.id=ofl.technic_id)
				LEFT JOIN technic_equipment_setting AS tes ON (tes.id=te.technic_setting_id)
		"""
	def _where(self):
		return """
			WHERE of.type='fuel'
		"""
	def union(self):
		return """
			UNION ALL
		"""
	def _select1(self):
		return """
			SELECT
				mpr.id*-1,
				null::int as line_id,
				null::int as oil_id,
				mpr.shift as shift,
				null::char state,
				mpr.date as date,
				null::int as partner_id,
				null::int as picking_id,
				null::int as warehouse_id,
				null::int as location_id,
				mpr.branch_id,
				te.branch_id as tech_branch_id,
				null::char as type,
				null::int as product_id,
				null::int as categ_id,
				mpr.dump_id as technic_id,
				te.owner_type,
				te.technic_type,
				te.model_id,
				0 as moto_hour,
				0 as current_km,
				0 as run_hour,
				0 as product_qty,
				te.technic_setting_id,
				te.partner_id as technic_partner_id,
				null::int as avg_epx,
				mpr.res_count as res_count,
				mpr.sum_m3 as production_amount,
				tes.fuel_low_idle,
				tes.fuel_medium_idle,
				tes.fuel_high_idle,
				'' as display_name
		"""
	def _from1(self):
		return """
			FROM mining_production_report AS mpr 
				LEFT JOIN technic_equipment AS te ON (te.id=mpr.dump_id)
				LEFT JOIN technic_equipment_setting AS tes ON (tes.id=te.technic_setting_id)
		"""
	def _where1(self):
		return """
			WHERE mpr.dump_id is not null
		"""
	def union1(self):
		return """
			UNION ALL
		"""
	
	def _select2(self):
		return """
			SELECT
				mpr.id*-2,
				null::int as line_id,
				null::int as oil_id,
				mpr.shift as shift,
				null::char state,
				mpr.date as date,
				null::int as partner_id,
				null::int as picking_id,
				null::int as warehouse_id,
				null::int as location_id,
				mpr.branch_id,
				te.branch_id as tech_branch_id,
				null::char as type,
				null::int as product_id,
				null::int as categ_id,
				mpr.excavator_id as technic_id,
				te.owner_type,
				te.technic_type,
				te.model_id,
				0 as moto_hour,
				0 as current_km,
				0 as run_hour,
				0 as product_qty,
				te.technic_setting_id,
				te.partner_id as technic_partner_id,
				null::int as avg_epx,
				mpr.res_count as res_count,
				mpr.sum_m3 as production_amount,
				tes.fuel_low_idle,
				tes.fuel_medium_idle,
				tes.fuel_high_idle,
				'' as display_name
		"""
	def _from2(self):
		return """
			FROM mining_production_report AS mpr 
				LEFT JOIN technic_equipment AS te ON (te.id=mpr.excavator_id)
				LEFT JOIN technic_equipment_setting AS tes ON (tes.id=te.technic_setting_id)
		"""
	def _where2(self):
		return """
			WHERE mpr.excavator_id is not null
		"""

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)
		print(self._select())
		self._cr.execute("""
			CREATE OR REPLACE VIEW {0} AS (
					{1}
					{2}
					{3}
					{4}
					{5}
					{6}
					{7}
					{8}
					{9}
					{10}
					{11}
				)
		""".format(self._table, 
				self._select(), self._from(), self._where(), self.union(),
				self._select1(), self._from1(), self._where1(), self.union1(),
				self._select2(), self._from2(), self._where2()
				)
		)
# SELECT
# 					ofl.id,
# 					ofl.id as line_id,
# 					ofl.parent_id as oil_id,
# 					of.shift,
# 					of.state,
# 					of.date,
# 					of.partner_id,
# 					of.picking_id,
# 					of.warehouse_id,
# 					of.location_id,
# 					sw.branch_id,
# 					of.type,
# 					ofl.product_id,
# 					pt.categ_id,
# 					ofl.technic_id,
# 					te.owner_type,
# 					te.technic_type,
# 					te.model_id,
# 					-- ofl.moto_hour,
# 					ofl.run_hour,
# 					ofl.product_qty,
# 					-- ofl.norm_diff,
# 					te.technic_setting_id,
# 					te.partner_id as technic_partner_id,
# 					ofl.avg_epx as avg_epx,
# 					0  as res_count,
# 					0 as production_amount,
# 					tes.fuel_low_idle,
# 					tes.fuel_medium_idle,
# 					tes.fuel_high_idle
					
# 					FROM oil_fuel_line AS ofl 
# 					LEFT JOIN oil_fuel AS of ON (ofl.parent_id=of.id)
# 					LEFT JOIN stock_location AS sl ON (of.location_id=sl.id)
# 					LEFT JOIN stock_warehouse AS sw ON (sl.set_warehouse_id=sw.id)
# 					LEFT JOIN product_product AS pp ON (ofl.product_id=pp.id)
# 					LEFT JOIN product_template AS pt ON (pp.product_tmpl_id=pt.id)
# 					LEFT JOIN technic_equipment AS te ON (te.id=ofl.technic_id)
# 					LEFT JOIN technic_equipment_setting AS tes ON (tes.id=te.technic_setting_id)
# 				WHERE of.type='fuel'
# 				UNION ALL
# 				SELECT
# 					mpr.id*-1,
# 					null::int as line_id,
# 					null::int as oil_id,
# 					mpr.shift as shift,
# 					null::char state,
# 					mpr.date as date,
# 					null::int as partner_id,
# 					null::int as picking_id,
# 					null::int as warehouse_id,
# 					null::int as location_id,
# 					mpr.branch_id,
# 					null::char as type,
# 					null::int as product_id,
# 					null::int as categ_id,
# 					mpr.dump_id as technic_id,
# 					te.owner_type,
# 					te.technic_type,
# 					te.model_id,
# 					0 as run_hour,
# 					0 as product_qty,
# 					te.technic_setting_id,
# 					te.partner_id as technic_partner_id,
# 					null::int as avg_epx,
# 					mpr.res_count as res_count,
# 					mpr.sum_m3 as production_amount,
# 					tes.fuel_low_idle,
# 					tes.fuel_medium_idle,
# 					tes.fuel_high_idle
					
# 					FROM mining_production_report AS mpr 
# 					LEFT JOIN technic_equipment AS te ON (te.id=mpr.dump_id)
# 					LEFT JOIN technic_equipment_setting AS tes ON (tes.id=te.technic_setting_id)
# 				WHERE mpr.dump_id is not null

# 				UNION ALL
# 				SELECT
# 					mpr.id*-2,
# 					null::int as line_id,
# 					null::int as oil_id,
# 					mpr.shift as shift,
# 					null::char state,
# 					mpr.date as date,
# 					null::int as partner_id,
# 					null::int as picking_id,
# 					null::int as warehouse_id,
# 					null::int as location_id,
# 					mpr.branch_id,
# 					null::char as type,
# 					null::int as product_id,
# 					null::int as categ_id,
# 					mpr.excavator_id as technic_id,
# 					te.owner_type,
# 					te.technic_type,
# 					te.model_id,
# 					0 as run_hour,
# 					0 as product_qty,
# 					te.technic_setting_id,
# 					te.partner_id as technic_partner_id,
# 					null::int as avg_epx,
# 					mpr.res_count as res_count,
# 					mpr.sum_m3 as production_amount,
# 					tes.fuel_low_idle,
# 					tes.fuel_medium_idle,
# 					tes.fuel_high_idle
					
# 					FROM mining_production_report AS mpr 
# 					LEFT JOIN technic_equipment AS te ON (te.id=mpr.excavator_id)
# 					LEFT JOIN technic_equipment_setting AS tes ON (tes.id=te.technic_setting_id)
# 				WHERE mpr.excavator_id is not null

class report_mining_technic_analyze(models.Model):
	_inherit = "report.mining.technic.analyze"


	def _union4(self):
		return	""" UNION ALL """
	def _select4(self):
		return """ 
			SELECT 
			50000000000000000+ofl.id as id,
			null::int as production_line_id,
            null::int as motorhour_line_id,
			of.date as date,
			te.branch_id as branch_id,
			te.id as technic_id,
			te.owner_type,
			te.technic_type,
			te.technic_setting_id,
			null::int as sum_motohour_time,
			null::int as sum_diff_odometer_value,
			null::int as sum_work_time,
			null::int as sum_repair_time,
			null::int as sum_production_time,
			0 as sum_production,
			ofl.product_qty as sum_fuel,
			0 as sum_expense,
			null::int as first_odometer_value,
			null::int as last_odometer_value,
			null::int as last_km,
			null::int as tbbk,
			null::float as technic_working_percent,
			null as is_tbbk,
			null::int  as run_day,
			null as shift,
			null as part,
			te.partner_id,
			null as daily_entry_id,
			null::float as plan_production,
			null::float as plan_repair_hour,
			null::float as plan_run_hour,
			null::float as plan_run_hour_util,
			null::float as plan_hour_prod,
			null::float as haul_distance,
            null::float as average_haul_distance
			"""
	def _group_by4(self):
		return """
		"""
	def _from4(self):
		return """
		FROM oil_fuel_line as ofl
		LEFT JOIN oil_fuel of on of.id = ofl.parent_id
		LEFT JOIN technic_equipment te ON te.id = ofl.technic_id
		"""

class MiningProductionReport(models.Model):
	_inherit = "mining.production.report"

	fuel = fields.Float(string='Зарцуулсан түлш', readonly=True)

	def _union7(self):
		return	""" UNION ALL """


	def _select7(self):
		return  """ SELECT
					ofl.id*-37 as id,
					null as production_id,
					case when te.technic_type='dump' then te.id else null end as dump_id,
					true as is_production,
					0 as sum_m3,
					0 as sum_tn,
					0 as res_count,
					case when te.technic_type='excavator' then te.id else null end as excavator_id,
					null as material_id,
					of.date as date,
					null as shift,
					null as part,
					te.branch_id as branch_id,
					null as from_location,
					null as for_pile,
					null as for_location,
					null as from_pile,
					null as level,
					null as master_id,
					null as is_stone,
					null as coal_layer,
					null as state,
					null as sum_m3_plan,
					0 as sum_tn_plan,
					0 as sum_m3_plan_exc,
					0 as sum_tn_plan_exc,
					0 as sum_m3_sur,
					0 as sum_tn_sur,
					0 as sum_m3_sur_petram,
					0 as sum_tn_sur_petram,
					0 as sum_m3_sur_puu,
					0 as sum_tn_sur_puu,
					0 as sum_m3_avg,
					0 as sum_tn_avg,
					0 as sum_m3_plan_master,
					0 as sum_tn_plan_master,
					te.owner_type,
					te.technic_type,
					te.partner_id,
					te.technic_setting_id,

					te.owner_type as owner_type2,
					te.technic_type as technic_type2,
					te.partner_id as partner_id2,
					te.technic_setting_id as technic_setting_id2,

					null::int as haul_distance,
					ofl.product_qty as fuel """

	def _group_by7(self):
		return """
		"""

	def _from7(self):
		return """ 
		FROM oil_fuel_line as ofl
		LEFT JOIN oil_fuel of on of.id = ofl.parent_id
		LEFT JOIN technic_equipment te on te.id = ofl.technic_id
		"""

	def _where7(self):
		return """
		where of.type='fuel'
		"""
