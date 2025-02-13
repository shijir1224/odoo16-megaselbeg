# -*- coding: utf-8 -*-
# Copyright 2014 ABF OSIELL <http://osiell.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from odoo import api, fields, models
_logger = logging.getLogger(__name__)


class BaseClearQueryCron(models.TransientModel):
    _name = 'base.clear.query.cron'
    _description = 'Base Clear Query Cron'
    
    # clear query cron
    @api.model
    def _clear_db_cron(self):

        query = """
        delete from report_pdf_output;
        delete from report_excel_output;
        """
        query = self.env['ir.config_parameter'].sudo().get_param('mw_base_clear_query')
        _logger.info('--db clear cron query start %s \n '%query)
        self.env.cr.execute(query)
        _logger.info('--db clear cron query end \n ')
