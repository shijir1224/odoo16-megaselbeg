# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAssetAssetValidateAll(models.TransientModel):
	_name = 'consume.order.validate.all'
	_description = 'Asset Validate All'

	def _default_purchase_date(self):
		asset_id = self._context.get('active_id', False)
		if asset_id:
			return self.env['consumable.material.in.use'].browse(asset_id).date
		return False
	
	account_id = fields.Many2one('account.account', 'Source Account')
	purchase_date = fields.Date('Purchase Date', default=_default_purchase_date)
	not_aml = fields.Boolean('Санхүү бичилт үүсгэхгүй')
	
	def validate_all(self):
		'''Сонгосон үндсэн хөрөнгөнүүдийг батлах товч дарахад гарч ирэх wizard-ны батлах товчийг дарахад тухайн 
		wizard-наас данс болон огноог context-д оноож хөрөнгүүдийг нэг,нэгээр нь батлах '''
		context=dict(self._context)
		active_ids = self._context.get('active_ids', False) or []
		asset_obj = self.env['consumable.material.in.use']
		for wizard in self:
			if wizard.not_aml:
				for asset in asset_obj.browse(active_ids):
					asset.with_context(src_account_id=False,create_aml=False,not_create_asset=True).button_progress()
			else:
				for asset in asset_obj.browse(active_ids):
					context.update({'src_account_id': wizard.account_id.id,
									'entry_date': wizard.purchase_date
									})
					asset.with_context(src_account_id=wizard.account_id.id,create_aml=True,not_create_asset=True).button_progress()
		return True
