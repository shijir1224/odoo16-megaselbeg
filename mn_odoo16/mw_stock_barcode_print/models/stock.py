# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from barcode.writer import ImageWriter
# try:
#     from cStringIO import StringIO
# except:

import base64

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def get_pick_name(self):
        return self.name
    
    def get_pick_name_bar(self, ids):
        report_id = self.browse(ids)
        if report_id:
            p_name = report_id.get_pick_name()
            if p_name and report_id.picking_type_id.with_barcode_print:
                from StringIO import StringIO
                fp = StringIO()
                barcode.generate('code128', u''+p_name, writer=ImageWriter(), output=fp, writer_options={'write_text':False})
                img_str = base64.b64encode(fp.getvalue())
                if img_str:
                    image_str = '<img alt="Embedded Image" width="300" height="60" src="data:image/png;base64,'+img_str+'" />'
                    return image_str
        return ''

class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    with_barcode_print = fields.Boolean(string='Баркодтой Хэвлэх Баримтын нэрийг', default=False)
