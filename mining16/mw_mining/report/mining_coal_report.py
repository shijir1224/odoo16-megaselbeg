# -*- coding: utf-8 -*-

from odoo import fields, models, tools, api


class MiningCoalReport(models.Model):

	_name = "mining.coal.report"
	_auto = False
	_description = "Mining coal report"
	_rec_name = 'description'

	date = fields.Date('Date', readonly=True)
	description = fields.Char('Description', readonly=True)
	branch_id = fields.Many2one('res.branch', 'Branch', readonly=True)
	sum_sales_amount_m3 = fields.Float(string='Нийт Борлуулсан м3',readonly=True)
	sum_sales_amount_tn = fields.Float( string='Нийт Борлуулсан Дүн тонн', readonly=True)
	sum_res_count = fields.Integer(string='Нийт Ресс', readonly=True)
	state = fields.Selection([('draft', 'Ноорог'), ('approved', 'Батлагдсан')], 'State', readonly=True)

	mining_coal_sales_id = fields.Many2one('mining.coal.sales','Mining Coal Sales', readonly=True)
	type = fields.Selection([('sale', 'Борлуулалт'),('sub_coal', 'Хандивийн Нүүрс'),('other_coal','Бусад Нүүрс')],string='Type', readonly=True)
	partner_id = fields.Many2one('res.partner', string='Partner', readonly =True)
	pile_id = fields.Many2one('mining.pile', 'Piles', readonly = True)
	pile_material_id = fields.Many2one('mining.material', string='Material', readonly = True)
	total_balance_m3 = fields.Float(string="Овоолгын Үлдэгдэл Мэдээгээр м3", readonly= True)
	total_balance_tn = fields.Float(string="Овоолгын Үлдэгдэл тонн", readonly=True)
	sales_amount_m3 = fields.Float(string='Борлуулсан Дүн м3', readonly=True)
	sales_amount_tn = fields.Float('Sales Amount tn', readonly=True)
	res_count = fields.Integer('Res Count', readonly=True)

	def init(self):
		tools.drop_view_if_exists(self._cr, self._table)

		self._cr.execute("""CREATE or REPLACE view %s as(
			SELECT
				mcs.id,
				mcs.date,
				mcs.description,
				mcs.branch_id,
				mcs.sum_sales_amount_m3,
				mcs.sum_sales_amount_tn,
				mcs.sum_res_count,
				mcs.state,
				mcsl.type,
				mcsl.partner_id,
				mcsl.pile_id,
				mcsl.pile_material_id,
				mp.balance_by_report_m3 as total_balance_m3,
				mp.balance_by_report_tn as total_balance_tn,
				mcsl.sales_amount_m3,
				mcsl.sales_amount_tn,
				mcsl.res_count
				FROM mining_coal_sales_line as mcsl
				LEFT JOIN mining_coal_sales as mcs ON (mcs.id = mcsl.mining_coal_sales_id)
				LEFT JOIN mining_pile as mp ON (mp.id = mcsl.pile_id)
		)
		""" % self._table)