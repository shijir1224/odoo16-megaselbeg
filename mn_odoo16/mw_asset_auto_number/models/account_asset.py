# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import calendar
from dateutil.relativedelta import relativedelta
from math import copysign

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_compare, float_is_zero, float_round
from datetime import date,datetime,timedelta
from odoo.osv import expression

class AccountAsset(models.Model):
    _inherit = 'account.asset'


    asset_code_sequence_id = fields.Many2one('ir.sequence', string='Asset code sequence')

    @api.model_create_multi
    def create(self, vals_list):
        print (vals_list)
        for vals in vals_list:
            # print('ssssss',vals.get('model_id'))
            if vals.get('model_id'):
                model_id = self.env['account.asset'].browse(vals['model_id'])
                if not model_id.asset_code_sequence_id:
                    raise UserError(("Хөрөнгийн загвар дээр дугаарлалт тохиргоо хийнэ үү."))
                # print('sadsadadasdas',model_id.asset_code_sequence_id.id)
                code = model_id.asset_code_sequence_id.next_by_id(model_id.asset_code_sequence_id.id)
                # print('sadsadadasdas',code)
                vals.update({'code': code})

            if vals.get('code'):
                if self.search([('code', '=', vals.get('code')), ('company_id', '=', self.env.user.company_id.id)]):
                    raise UserError(("%s дугаар дээр хөрөнгө бүртгэгдсэн байна."%(vals.get('code'))))

            # else:
            #     raise UserError(("Хөрөнгө үүсгэхийн тулд дугаар заавал оруулах шаардлагтай."))

        return super(AccountAsset, self).create(vals_list)

    def write(self, vals):
        model_id = False
        if self:
            for i in self:
                if vals.get('model_id'):
                    model_id = self.env['account.asset'].browse(vals['model_id'])
                    # print('1111111111111',model_id)
                    if not model_id.asset_code_sequence_id:
                        raise UserError(("Хөрөнгийн загвар дээр дугаарлалт тохиргоо хийнэ үү."))
                    code = model_id.asset_code_sequence_id.next_by_id(model_id.asset_code_sequence_id.id)
                    # print('1111111111111111222',code)
                    vals.update({'code': code})
                    model_id = vals.get('model_id')
                    # print('11111111111111112223',vals)
                else:
                    model_id = i.model_id.id

                if vals.get('code'):
                    if self.search([('code', '=', vals.get('code')), ('id', '!=', i.id), ('company_id', '=', self.env.user.company_id.id)]):
                        raise UserError(("%s дугаар дээр хөрөнгө бүртгэгдсэн байна." % (vals.get('code'))))

        return super(AccountAsset, self).write(vals)
    
                                    