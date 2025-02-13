# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)
  
class ResUsers(models.Model):
	_inherit = 'res.users'
	_description = 'Res users'

	# Columns
	cash_journal_id = fields.Many2one('account.journal', string='Cash journal', domain=[('type', 'in', ['bank','cash'])])
	team_type = fields.Selection([
			('salesman', u'Борлуулагч - Агуулахтай'), # Нарантуултай адилхан
			('supermarket', u'Супермаркет'), 
			('small', u'Жижиглэн'),
			('small_market', u'Жижиг зах'),
			('merchan', u'Мерчин'),
			('driver', u'Жолооч'),
			('oron_nutag', u'Орон нутаг'),
			('toollogo', u'Тооллого'),
			('picking', u'Цуглуулагч'),
		], string=u'Сувгийн төрөл', )

	crm_team_id = fields.Many2one('crm.team', string=u'Суваг', )

class ResCompany(models.Model):
	_inherit = 'res.company'

	available_qty_on_mobile = fields.Boolean(string="Утсан дээр зөвхөн үлдэгдэлтэй барааг харуулах", default=False)
	see_barcode_on_mobile = fields.Boolean(string="Барааны мэдээлэл(нэр) дээр баркод харах эсэх", default=False)
	main_price_unit_on_mobile = fields.Boolean(string="Барааны үндсэн үнийг татах эсэх", default=False)

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	available_qty_on_mobile = fields.Boolean(related="company_id.available_qty_on_mobile", readonly=False)
	see_barcode_on_mobile = fields.Boolean(related="company_id.see_barcode_on_mobile", readonly=False)
	main_price_unit_on_mobile = fields.Boolean(related="company_id.main_price_unit_on_mobile", readonly=False)

# class StockWarehouse(models.Model):
#	 _inherit = 'stock.warehouse'
#	 _description = 'Stock warehouse'

#	 # Columns
#	 user_ids = fields.Many2many('res.users','user_warehouses_rel','warehouse_id','user_id',
#		 string='Access users',)
