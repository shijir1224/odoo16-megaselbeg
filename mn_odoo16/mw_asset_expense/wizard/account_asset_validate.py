# -*- coding: utf-8 -*-
from odoo import fields, models, _


class AccountAssetAssetValidate(models.TransientModel):
    _name = 'account.asset.validate'
    _description = 'Asset Validate'

    def _default_purchase_date(self):
        # Форм харагдац дээр бөглөсөн огноог deafult-р авах, өөрчлөх боломжтой
        asset_id = self._context.get('active_id', False)
        if asset_id:
            return self.env.get('account.asset').browse(asset_id).date
        return False

    account_id = fields.Many2one('account.account', 'Source Account',)
    purchase_date = fields.Date('Purchase Date', default=_default_purchase_date)

    def validate(self):
        # Үндсэн хөрөнгийг батлах товч дарахад гарч ирэх wizard-ны батлах товчийг дарахад тухайн wizard-наас данс болон огноог context-д оноох
        context = dict(self._context)
        asset_obj = self.env.get('account.asset')
        asset_id = context.get('active_id', False)
        if asset_id:
            asset = asset_obj.browse(asset_id)
            context.update({'src_account_id': self.account_id.id,
                            'entry_date': self.purchase_date
                            })
            asset.validate(context)
        return True


class AccountAssetAssetValidateAll(models.TransientModel):
    _name = 'account.asset.validate.all'
    _description = 'Asset Validate All'

    def _default_purchase_date(self):
        asset_id = self._context.get('active_id', False)
        if asset_id:
            return self.env.get('account.asset').browse(asset_id).date
        return False
    
    account_id = fields.Many2one('account.account', 'Source Account', )
    purchase_date = fields.Date('Purchase Date', default=_default_purchase_date)
    asset_each_date = fields.Boolean('Asset Each Date')

    def validate_all(self):
        ''' Сонгосон үндсэн хөрөнгөнүүдийг батлах товч дарахад гарч ирэх wizard-ны батлах товчийг дарахад тухайн
            wizard-наас данс болон огноог context-д оноож хөрөнгүүдийг нэг,нэгээр нь батлах '''
        context = dict(self._context)
        active_ids = self._context.get('active_ids', False) or []
        asset_obj = self.env['account.asset']
        for wizard in self:
            for asset in asset_obj.browse(active_ids):
                if self.asset_each_date:
                    # Хөрөнгө тус бүрийн огноогоор батлах үед хөрөнгүүдийн худалдан авалтын огноогоор журналын огноо үүснэ
                    context.update({'src_account_id': wizard.account_id.id,
                                    'entry_date': asset.purchase_date
                                    })
                else:
                    context.update({'src_account_id': wizard.account_id.id,
                                    'entry_date': wizard.purchase_date
                                    })
                asset.validate(context)
        return True
