# -*- coding: utf-8 -*-

from odoo import fields, models

class StockLocation(models.Model):
	_inherit = "stock.location"

	stock_account_output_id = fields.Many2one('account.account', 'Гарч буй барааны өртөгийн данс')

class StockMove(models.Model):
	_inherit = "stock.move"

	def _get_accounting_data_for_valuation(self):
		'''
		Агуулахаас бараа зарлагдах үед гарч буй
		байрлал дээр гарах барааны данс байвал тус дансруу дебит бичилт хийгдэнэ.
		:return:
		'''
		journal_id, acc_src, acc_dest, acc_valuation = super(StockMove, self)._get_accounting_data_for_valuation()
		if self.picking_type_id.code == 'outgoing' and self.location_id.stock_account_output_id:
			acc_dest = self.location_id.stock_account_output_id.id
		return journal_id, acc_src, acc_dest, acc_valuation