# -*- coding: utf-8 -*-
#!/usr/bin/python
from odoo import api, models, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

from datetime import datetime

import logging
_logger = logging.getLogger(__name__)


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def get_last_col(self):
        result = super(StockInventory, self).get_last_col()
        result = result+1
        return result
    def get_inv_header(self,row, wo_sheet, cell_style):
        result = super(StockInventory, self).get_inv_header(row, wo_sheet, cell_style)
        result.write(row, self.get_last_col(), u"Дуусгах хугацаа", cell_style)
        return result

    def get_inv_print_cel(self, row, wo_sheet, item, contest_left, cell_format2, contest_center):
        result = super(StockInventory, self).get_inv_print_cel(row, wo_sheet, item, contest_left, cell_format2, contest_center)
        life_date = ''
        if item.prod_lot_id.life_date:
            life_date = item.prod_lot_id.life_date.strftime(DEFAULT_SERVER_DATE_FORMAT)
        result.write(row, self.get_last_col(), str(life_date), cell_format2)
        return result
    
    def get_inv_header_pdf(self):
        result = super(StockInventory, self).get_inv_header_pdf()
        if self.get_stock_inv_pdf_lot_ok():
            result.insert(4, u'Дуусах хугацаа')
        return result

    def get_inv_data_pdf(self, number, line, qty_total):
        result = super(StockInventory, self).get_inv_data_pdf(number, line, qty_total)
        if self.get_stock_inv_pdf_lot_ok():
            if line:
                result.insert(4, '<p style="text-align: center;">' + (line.prod_lot_id and line.prod_lot_id.life_date and line.prod_lot_id.life_date.strftime(DEFAULT_SERVER_DATE_FORMAT) or '') + '</p>')
            else:
                result.insert(4, u'')
        return result
