# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class AccountAssetAssetValidateAll(models.TransientModel):
    _name = 'account.asset.validate.all'
    _description = 'Asset Validate All'

    def _default_purchase_date(self):
        asset_id = self._context.get('active_id', False)
        if asset_id:
            return self.env['account.asset'].browse(asset_id).prorata_date
        return False
    
    account_id = fields.Many2one('account.account', string='Source Account')
    purchase_date = fields.Date(string='Purchase Date', default=_default_purchase_date)
    not_aml = fields.Boolean(string='Санхүү бичилт үүсгэхгүй')
    
    def validate_all(self):
        '''Сонгосон үндсэн хөрөнгөнүүдийг батлах товч дарахад гарч ирэх wizard-ны батлах товчийг дарахад тухайн 
        wizard-наас данс болон огноог context-д оноож хөрөнгүүдийг нэг,нэгээр нь батлах '''
        context=dict(self._context)
        active_ids = self._context.get('active_ids', False) or []
        asset_obj = self.env['account.asset']
        for wizard in self:
            if wizard.not_aml:
                for asset in asset_obj.browse(active_ids):
                    asset.with_context(src_account_id=wizard.account_id.id,create_aml=True,not_create_asset=True).validate()
            else:
                for asset in asset_obj.browse(active_ids):
                    context.update({'src_account_id': wizard.account_id.id,
                                    'entry_date': wizard.purchase_date
                                    })
                    asset.with_context(src_account_id=wizard.account_id.id,create_aml=True,not_create_asset=True).validate()
        return True


    def validate_all_onlys(self):
        context=dict(self._context)
        active_ids = self._context.get('active_ids', False) or []
        asset_obj = self.env['account.asset']
        for wizard in self:
            for asset in asset_obj.browse(active_ids):
                context.update({'src_account_id': wizard.account_id.id,
                                'entry_date': wizard.purchase_date
                                })
                asset.with_context(src_account_id=wizard.account_id.id,create_aml=True,not_create_asset=True).validate_new()

