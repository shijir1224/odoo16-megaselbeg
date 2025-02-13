# -*- coding: utf-8 -*-

from odoo import api, models, _
import logging
_logger = logging.getLogger(__name__)

class es_report_pos_receipt(models.AbstractModel):
    _name = 'report.mw_pos.report_receipt'
    _description = 'Report POS Receipt'

    @api.model
    def _get_report_values(self, docids, data=None):
        active_ids = self.env.context.get('active_ids', [])
        docs = self.env[data['model']].browse(active_ids)
        return {
            'doc_ids': active_ids,
            'doc_model': data['model'],
            'data': data,
            'docs': docs
        }
