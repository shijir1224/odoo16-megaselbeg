# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):
	_inherit = 'stock.picking'
	
	def action_done_transfer_barcode(self, picking_ids):
		transfer = self.env['stock.immediate.transfer']
		transfer_id = transfer.create({'pick_ids':[]})
		transfer_id.pick_ids = [picking_ids]
		transfer_id.process()

	def on_barcode_scanned(self, barcode):
		if self.env.company.nomenclature_id:
			parsed_result = self.env.company.nomenclature_id.parse_barcode(barcode)
			if parsed_result['type'] == 'cashier':
				uid = self.env['res.users'].search([('partner_id.barcode','=',parsed_result['base_code'])], limit=1)
				if uid and self.state=='assigned':
					self_id = self.id or self._origin.id
					self.with_user(uid).action_done_transfer_barcode(self_id)
					return {'type': 'ir.actions.act_window_close'}
					# utasnaas shuud batlahiig ni boliulav ddd
					# self.with_user(uid).action_done()
				else:
					raise UserError('%s баркодтой Батлах хэрэглэгч олдсонгүй эсвэл баримт БЭЛЭН төлөвд байхгүй байна'%(barcode, ))
		return super(StockPicking, self).on_barcode_scanned(barcode)

	def action_client_action_mw(self):
		""" Open the mobile view specialized in handling barcodes on mobile devices.
		"""
		self.ensure_one()
		action = self.env["ir.actions.actions"]._for_xml_id("stock_barcode.stock_barcode_picking_client_action")
		# print('cdcdscdc', action)
		return {
			'type': 'ir.actions.client',
			'tag': 'stock_barcode_client_action',
			'target': 'fullscreen',
			'params': {
				'model': 'stock.picking',
				'inventory_id': self.id,
			}
		}