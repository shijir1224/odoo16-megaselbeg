# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules
from odoo.addons import decimal_precision as dp
from datetime import datetime
from io import BytesIO
import base64
import pdfkit
import pytz
from odoo.modules.module import get_module_resource
from reportlab.graphics.barcode import createBarcodeDrawing
from odoo.tools import check_barcode_encoding

class Warehouse(models.Model):
    _name = 'stock.warehouse'
    _inherit = ['stock.warehouse', 'mail.thread']

    def _default_name(self):
        count = self.env['stock.warehouse'].with_context(active_test=False).search_count([('company_id', '=', self.env.company.id)])
        return "%s - warehouse # %s" % (self.env.company.name, count + 1) if count else self.env.company.name

    name = fields.Char('Агуулах', required=True, default=_default_name, tracking=True)
    
    def name_get(self):
        ret_list = []
        for wh in self:
            orig_location = wh
            name = wh.name
            if wh.code:
              name = '['+wh.code+'] '+wh.name
            ret_list.append((wh.id, name))
        return ret_list

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        """ search full name and barcode """
        if args is None:
            args = []
        recs = self.search(['|', ('name', operator, name), ('code', operator, name)] + args, limit=limit)
        return recs.name_get()

class StockBarcodePrintLine(models.TransientModel):
    _name = 'stock.barcode.print.line'
    _description = u'Print barcode line'

    parent_id = fields.Many2one('stock.barcode.print', string='Parent', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Бараа')
    qty = fields.Integer(string='Тоо ширхэг', default=1)

class StockBarcodePrint(models.TransientModel):
    _name = 'stock.barcode.print'
    _description = u'Print barcode'

    product_ids = fields.Many2many('product.product', 'stock_barcode_print_rel' ,'s_id', 'p_id', 'Products')
    name = fields.Char('Name')
    data = fields.Binary('Download File')
    type_size = fields.Selection([('big','60x40'), ('small','40x30'), ('small2','50x20'), ('small3','50x25')], string='Хэмжээ', required=True, default='big')
    
    width = fields.Integer(string='Өргөн')
    height = fields.Integer(string='Өндөр')
    is_many_print = fields.Boolean('Тоо хэмжээгээр хэвлэх', default=False)
    is_with_date = fields.Boolean('Огноотой хэвлэх', default=False)
    is_with_partner = fields.Boolean('Нийлүүлэгчтэй хэвлэх', default=False)
    stock_move_ids = fields.Many2many('stock.move', 'stock_barcode_print_stock_move_rel', 'barcode_id', 'move_id', string='Stock moves')
    custom_date = fields.Datetime(string='Огноо', default=fields.Datetime.now)
    is_with_time = fields.Boolean('Цагтай Хамт', default=False)
    
    custom_partner = fields.Many2one('res.partner', string='Харилцагч', )
    line_ids = fields.One2many('stock.barcode.print.line', 'parent_id', string='Stock barcode lines')

    def _xmlcharref_encode(self, unicode_data, encoding):
        chars = []
        for char in unicode_data:
            try:
                chars.append(char.encode(encoding, 'strict'))
            except UnicodeError:
                chars.append('&#%i;' % ord(char))
        return ''.join(chars)

    def encode_for_xml(self, unicode_data, encoding='ascii'):
        try:
            return unicode_data.encode(encoding, 'xmlcharrefreplace')
        except ValueError:
            return _xmlcharref_encode(unicode_data, encoding)

    # hemjee uurchluh Vanchgaa
    @api.onchange('type_size')
    def onchange_type_size(self):
        if self.type_size == 'big':
            self.width = 60
            self.height = 40
        elif self.type_size == 'small':
            self.width = 40
            self.height = 30
        elif self.type_size == 'small2':
            self.width = 50
            self.height = 20
        elif self.type_size == 'small3':
            self.width = 50
            self.height = 25

    def get_product_html(self, nbr, bom_ids, s_date, categ_ids):
          return '',nbr
    def get_bom_ok(self):
          return False
    def get_barcode(self, product):
        return product.barcode or product.default_code
    
    def get_date_time(self, date, product_id):
        return date

    def get_body_style(self):
        return ''
    def action_print(self):
        # print modules.get_module_resource('mw_stock', 'static/lib/JsBarcode/dist/JsBarcode.all.js')
        if self.line_ids or self.get_bom_ok():
            html="""
            <!DOCTYPE HTML>
                <html lang="en-US">
                <body>  """
            # font_name = 'static/AuberCFMedium-Medium.ttf'
            font_name = 'static/Ubuntu-R.ttf'
            font_url = modules.get_module_resource('mw_stock', font_name)
            # try:
            #     createBarcodeDrawing('Code128', value='foo', format='png', width=100, height=100, humanReadable=1).asString('png')
            # except Exception:
            #     pass
            # defaults = {
            #     'width': (600, int),
            #     'height': (100, int),
            #     'humanreadable': (False, lambda x: bool(int(x))),
            #     'quiet': (True, lambda x: bool(int(x))),
            #     'mask': (None, lambda x: x),
            #     'barBorder': (4, int),
            #     # The QR code can have different layouts depending on the Error Correction Level
            #     # See: https://en.wikipedia.org/wiki/QR_code#Error_correction
            #     # Level 'L' – up to 7% damage   (default)
            #     # Level 'M' – up to 15% damage  (i.e. required by l10n_ch QR bill)
            #     # Level 'Q' – up to 25% damage
            #     # Level 'H' – up to 30% damage
            #     'barLevel': ('L', lambda x: x in ('L', 'M', 'Q', 'H') and x or 'L'),
            # }
            # kwargs = {k: validator(kwargs.get(k, v)) for k, (v, validator) in defaults.items()}
            # kwargs['humanReadable'] = kwargs.pop('humanreadable')

            # if barcode_type == 'UPCA' and len(value) in (11, 12, 13):
            #     barcode_type = 'EAN13'
            #     if len(value) in (11, 12):
            #         value = '0%s' % value
            # elif barcode_type == 'auto':
            #     symbology_guess = {8: 'EAN8', 13: 'EAN13'}
            #     barcode_type = symbology_guess.get(len(value), 'Code128')
            # elif barcode_type == 'DataMatrix':
            #     # Prevent a crash due to a lib change from pylibdmtx to reportlab
            #     barcode_type = 'ECC200DataMatrix'
            # elif barcode_type == 'QR':
            #     # for `QR` type, `quiet` is not supported. And is simply ignored.
            #     # But we can use `barBorder` to get a similar behaviour.
            #     if kwargs['quiet']:
            #         kwargs['barBorder'] = 0

            # if barcode_type in ('EAN8', 'EAN13') and not check_barcode_encoding(value, barcode_type):
            #     # If the barcode does not respect the encoding specifications, convert its type into Code128.
            #     # Otherwise, the report-lab method may return a barcode different from its value. For instance,
            #     # if the barcode type is EAN-8 and the value 11111111, the report-lab method will take the first
            #     # seven digits and will compute the check digit, which gives: 11111115 -> the barcode does not
            #     # match the expected value.
            #     barcode_type = 'Code128'
            # barcode = createBarcodeDrawing(barcode_type, value=value, format='png', **kwargs)
            # print(barcode)
            # print('barcode: ',type(barcode))
            html="""
            <!DOCTYPE HTML>
                <html lang="en-US">
                <head>
                    <meta charset="UTF-8">
                    <title></title>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/jsbarcode/3.11.3/JsBarcode.all.min.js"></script>
                <style  type="text/css" media="all">    
                    @font-face { font-family: ElectronMon; src: url('"""+font_url+"""') format('truetype'); }
                    body{
                        font-family: ElectronMon;
                        text-align: center;
                        %s
                    }
                    .break { page-break-before: always; }
                    
                </style>
                </head>
              <body>  """%(self.get_body_style())

            nbr = 1
            get_bom_html, nbr = self.get_product_html(nbr, False, self.custom_date, [])
            html += get_bom_html
            for ll in self.line_ids:
                item = ll.product_id
                barcode = self.get_barcode(item)
                if barcode:
                    lenn = 1
                    stock_move_id = self.stock_move_ids.filtered(lambda r: r.product_id.id==item.id)
                    if self.is_many_print:
                        lenn = ll.qty

                    for ran in range(0, lenn):

                        html+=u"""
                        <table style='width:%smm;max-height:%smm; text-align: center;' cellspacing="0" cellpadding="0" class="break">
                        """ % (self.width, self.height)

                        format='format: "EAN13",'
                        if len(barcode)!=13:
                            format=''
                        height_bar='48'

                        if self.is_many_print:
                            html +=u"""<tr><td style='font-size:78px;width:100%;'>&nbsp;</td></tr>"""
                        
                        html+=u"""<tr>
                                    <td style='text-align: center; font-size:16px; width:100%; font-weight: bold;' colspan="3">
                                    """+str(item.display_name)+u"""
                                    </td>
                                </tr>
                                """
                                
                        html += u"""
                                <tr>
                                    <td colspan="3" style="text-align: center; ">
                                    <svg id='barcode"""+str(nbr)+"""' style='width:100%;'/>
                                    <script>
                                    JsBarcode('#barcode"""+str(nbr)+"""', '"""+str(barcode)+"""',{
                                    """+format+"""
                                    height:"""+str(height_bar)+""",
                                    margin: 0,
                                    displayValue: false,
                                    });
                                    </script>
                                    </td>
                                </tr>"""
                        html+=u"""        <tr >
                                    <td style='text-align: center; font-size:16px; width:100%; font-weight: bold;' colspan="3">
                                    """+str(barcode)+u"""
                                    </td>
                                </tr>
                                """
                    html+=u"""<tr >"""
                    # print('GETTO: ', html)
                    if self.is_with_date:
                        date = self.custom_date or stock_move_id[0].date_expected
                        tz = self.env.user.tz or 'Asia/Ulaanbaatar'
                        timezone = pytz.timezone(tz)
                        if date:
                            date = date.replace(tzinfo=pytz.timezone('UTC')).astimezone(timezone)
                            
                        if self.is_with_time and date:
                            date = datetime.strftime(date, '%Y-%m-%d %H:%M:%S')
                        else:
                            date = datetime.strftime(date, '%Y-%m-%d')
                        date = self.get_date_time(date, ll.product_id)
                        html+=u"""
                                <td style='font-size:12px; font-weight: bold;'>
                                """+date+u"""
                                </td>
                            """
                    if self.is_with_partner:
                        partner_id = self.custom_partner
                        partner_name = partner_id.ref or partner_id.name or ''
                        html+=u"""
                                <td style='font-size:102x; font-weight: bold;'>
                                """+partner_name+u"""
                                </td>
                            """
                                    
                    html+=u"""</tr>"""
                    html+="""
                        </table>
                    """
                    nbr+=1
                    # html +=u'<div>'+unicode(item.name)+'<img id="barcode1"/><script>JsBarcode("#barcode1", "'+unicode(item.barcode)+'" );</script></div>'
            html +="""</body></html>"""
            print ('html222 ', html)
            # html =self.encode_for_xml(html, 'ascii')
            
            options = {
                # 'page-size': 'A8',
                # 'page-width': '60mm',
                # 'page-heigth': '40mm',
                'page-width': '%smm' %(self.width), 
                'page-height': '%smm' %(self.height),
                # 'page-width': '60mm', 
                # 'page-height': '40mm',
                # 'orientation': 'Landscape',
                'margin-top': '0mm',
                'margin-bottom': '0mm',
                'margin-right': '0mm',
                'margin-left': '0mm',
                'encoding': "UTF-8",
                # 'no-outline': None,
                # 'header-html': base_url+u'/insurance/static/cancel_header.html',
                # 'header-spacing': 1,
            } 
            output = BytesIO(pdfkit.from_string(html,False,options=options)) 
            out = base64.encodebytes(output.getvalue())
            file_name = 'Barcode.pdf'
            excel_id = self.write({'data': out, 'name': file_name})
            
            return {
                'type' : 'ir.actions.act_url',
                'url': "web/content/?model=stock.barcode.print&id=" + str(self.id) + "&filename_field=filename&field=data&filename=" + self.name,
                'target': 'new',
            }