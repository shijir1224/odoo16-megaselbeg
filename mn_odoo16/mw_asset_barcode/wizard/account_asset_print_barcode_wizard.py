# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, modules
from odoo.addons import decimal_precision as dp
from datetime import datetime
from io import BytesIO
import base64
import pdfkit

import pytz
import logging
_logger = logging.getLogger(__name__)

class AssetBarcodePrintLine(models.TransientModel):
    _name = 'asset.barcode.print.line'
    _description = u'Print barcode line'

    parent_id = fields.Many2one('asset.barcode.print', string='Parent', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Бараа', required=True,)
    qty = fields.Integer(string='Тоо ширхэг', default=1)

class AssetBarcodePrint(models.TransientModel):
    _name = 'asset.barcode.print'
    _description = u'Print barcode'

    asset_ids = fields.Many2many('account.asset', 'asset_barcode_print_rel' ,'s_id', 'a_id', 'Assets')
    name = fields.Char('Name')
    data = fields.Binary('Download File')
    type_size = fields.Selection([('big','60x40'), ('small','40x30')], string='Хэмжээ', required=True, default='big')
    is_owner = fields.Boolean('Ажилтан хэвлэх', default=False)

    width = fields.Integer(string='Өргөн')
    height = fields.Integer(string='Өндөр')
    is_many_print = fields.Boolean('Тоо хэмжээгээр хэвлэх', default=False)
    is_with_date = fields.Boolean('Огноотой хэвлэх', default=False)
    is_with_partner = fields.Boolean('Нийлүүлэгчтэй хэвлэх', default=False)
    company_id = fields.Many2one('res.company', string='Компани', default=lambda self: self.env.company, readonly=True)

    @api.model
    def default_get(self, default_fields):
        # Хөрөнгүүдийг олноор нь сонгон шилжүүлэх үед мөр бүрт мэдээллийг оруулах
        res = super(AssetBarcodePrint, self).default_get(default_fields)
        context = dict(self._context or {})
        vals = []
        if context.get('active_model') == 'account.asset' and context.get('active_ids'):
            assets = self.env[context.get('active_model')].browse(context.get('active_ids'))
            # for asset in assets:
            #     asset_ids = [0, False, {'id': asset.id,}]
            #                         # 'state': 'draft',
            #                         # 'owner_id': asset.owner_partner_id.id,
            #                         # 'old_branch_id': asset.branch_id.id,
            #                         # 'category_id': asset.category_id.id,
            #                         # 'old_account_id':asset.account_depreciation_expense_id.id,
            #                         # 'old_analytic_account_id': asset.account_analytic_id.id,
            #                         # 'new_owner_id': asset.owner_partner_id.id,
            #                         # 'new_branch_id': asset.branch_id.id,
            #                         # 'new_category_id': asset.category_id.id,
            #                         # 'is_expense_split': asset.is_expense_split,
            #                         # 'old_allocation_id': asset.allocation_id.id,
            #                         # 'purchase_date':asset.purchase_date,
            #                         # 'new_analytic_account_id': asset.account_analytic_id.id,
            #                         # 'old_department':asset.owner_department_id.id
            #     vals.append(assets)
        res.update({'asset_ids': assets})
        return res


#     stock_move_ids = fields.Many2many('stock.move', 'stock_barcode_print_stock_move_rel', 'barcode_id', 'move_id', 'Stock moves')
    # 
    # @api.model
    # def _get_date(self):
    #   if 'custom_date' in self.env.context:
    #     print '========', self.env.context
    #     return self.env.context['custom_date']
    #   else:
    #     return False
    # @api.model
    # def _get_partner(self):
    #   if 'custom_partner' in self.env.context:
    #     return self.env.context['custom_partner']
    #   else:
    #     return False
    custom_date = fields.Date(string='Огноо', )
    custom_partner = fields.Many2one('res.partner', string='Харилцагч', )
    line_ids = fields.One2many('asset.barcode.print.line', 'parent_id', string='Stock moves')

    def encode_for_xml(self, unicode_data, encoding='ascii'):
        try:
            return unicode_data.encode(encoding, 'xmlcharrefreplace')
        except ValueError:
            return _xmlcharref_encode(unicode_data, encoding)

    def _xmlcharref_encode(self, unicode_data, encoding):
        chars = []
        for char in unicode_data:
            try:
                chars.append(char.encode(encoding, 'strict'))
            except UnicodeError:
                chars.append('&#%i;' % ord(char))
        return ''.join(chars)
   

    # hemjee uurchluh Vanchgaa
    @api.onchange('type_size')
    def onchange_type_size(self):
        if self.type_size == 'big':
            self.width = 40
            self.height = 60
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
        return product.barcode
    def get_code(self, product):
        return product.code

    def get_body_style(self):
        return ''
    def action_print(self):
        # print modules.get_module_resource('mw_stock', 'static/lib/JsBarcode/dist/JsBarcode.all.js')
        if self.asset_ids:
#             html="""
#             <!DOCTYPE HTML>
#                 <html lang="en-US">
#                 <body>  """
            # font_name = 'static/AuberCFMedium-Medium.ttf'
            font_name = 'static/Ubuntu-R.ttf'
            font_url = modules.get_module_resource('mw_asset_barcode', font_name)
#             html="""
#             <!DOCTYPE HTML>
#                 <html lang="en-US">
#                 <head>
#                     <meta charset="UTF-8">
#                     <title></title>
#                     <script src='"""+modules.get_module_resource('mw_asset_barcode', 'static/lib/JsBarcode/dist/JsBarcode.all.js')+"""' charset="utf-8"></script>
#                 <style  type="text/css" media="all">    
#                     @font-face { font-family: ElectronMon; src: url('"""+font_url+"""'); }
#                     body{
#                         font-family: ElectronMon;
#                         text-align: center;
#                         %s
#                     }
#                     .break { page-break-before: always; }
#                     
#                 </style>
#                 </head>
#               <body>  """%(self.get_body_style())
              
#             html="""
#             <!DOCTYPE HTML>
#                 <html lang="en-US">
#                 <head>
#                     <meta charset="UTF-8">
#                     <title></title>
#                     <script src='"""+modules.get_module_resource('mw_stock', 'static/lib/JsBarcode/dist/JsBarcode.all.js')+"""' charset="utf-8"></script>
#               <style  type="text/css" media="all">    
#                   body{
#                       font-family: arial sans-serif;
#                   }
#                   .break { page-break-before: always; }
#                      
#               </style>
#                 </head>
#                 <body>
#              
#                         """              
            html="""
            <!DOCTYPE HTML>
                <html lang="en-US">
                <body>  """
            # font_name = 'static/AuberCFMedium-Medium.ttf'
            font_name = 'static/Ubuntu-R.ttf'
            font_url = modules.get_module_resource('mw_stock', font_name)
                                # <script src="https://cdnjs.cloudflare.com/ajax/libs/jsbarcode/3.11.3/JsBarcode.all.min.js"></script>
                    # <script src='"""+modules.get_module_resource('mw_stock', 'static/lib/JsBarcode/bin/JsBarcode.js')+"""' charset="utf-8"></script>

            html="""
            <!DOCTYPE HTML>
                <html lang="en-US">
                <head>
                    <meta charset="UTF-8">
                    <title></title>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/jsbarcode/3.11.3/JsBarcode.all.min.js"></script>
                <style  type="text/css" media="all">    
                    @font-face { font-family: ElectronMon; src: url('"""+font_url+"""'); }
                    body{
                        font-family: ElectronMon;
                        text-align: center;
                        
                    }
                    .break { page-break-before: always; }
                    
                </style>
                </head>
              <body>  """


            nbr = 1
            get_bom_html, nbr = self.get_product_html(nbr, False, self.custom_date, [])
            html += get_bom_html
            for ll in self.asset_ids:
                item = ll
                barcode = self.get_barcode(item)
                _logger.info(u'barcode %s '%(barcode))
                code = self.get_code(item)
                _logger.info(u'code %s '%(code))
                if self.is_owner and ll.owner_id:
                    name_d = ll.owner_id.name
                else:
                    name_d = item.name
                    
                if barcode:
                    lenn = 1
                    stock_move_id = False#self.stock_move_ids.filtered(lambda r: r.product_id.id==item.id)
                    if self.is_many_print:
                        lenn = ll.qty

                    for ran in range(0, lenn):

                        html+=u"""
                        <table style='width:%smm;max-height:%smm; text-align: center;' cellspacing="0" cellpadding="0" class="break">
                        """ % (self.width, self.height)

                        # format='format: "EAN13",'
                        format=''
                        if len(barcode)!=13:
                            format=''
                        height_bar='48'
                        

                        if self.is_many_print:


                            
                            html +=u"""<tr><td style='font-size:78px;width:100%;'>&nbsp;</td></tr>"""
                        html+=u"""<tr>

                                    <td style='text-align: left; font-size:20px; width:100%; font-weight: bold; font-style: italic;padding: 2px; margin: 2px;' colspan="3">
                                    """+'"'+str(self.company_id.name)+'"'+u"""
                                    </td>
                                </tr>
                                """

                        html+=u"""

                                <tr >
                                    <td style='text-align: left; font-size:16px; width:100%; font-weight: bold;padding: 2px; margin: 2px;' colspan="3">
                                    """+'Хөрөнгийн код:     '+str(code if code else '')+u"""
                                    </td>
                                </tr>
                                <tr>

                                    <td style='text-align: left; font-size:16px; width:100%; font-weight: bold;padding: 2px; margin: 2px;' colspan="3">
                                    """+str(name_d)+u"""
                                    </td>
                                </tr>
                                """
                        # print(s/)
                        html += u"""
                                <td>
                                </td>
                                <tr style='weight:50px;'>
                                    <td colspan="3" style="text-align: left; ">
                                    <svg id='barcode"""+str(nbr)+"""' style='width:5px;'/>
                                    <script>
                                    JsBarcode('#barcode"""+str(nbr)+"""', '"""+str(barcode)+"""',{
                                    """+format+"""
                                    height:"""+str(height_bar)+""",
                                    displayValue: false,
                                    margin:0,
                                    });
                                    </script>
                                    </td>
                                </tr>"""
                        html+=u"""
                                <tr >
                                    <td style='text-align: center; font-size:16px; width:100%; font-weight: bold;padding: 2px; margin: 2px;' colspan="3">
                                    """+str(barcode)+u"""
                                    </td>
                                </tr>                                
                                """
                    html+=u"""<tr >"""
                    
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
#             html="""<html lang="en">
# <head>
#  <script src="https://cdnjs.cloudflare.com/ajax/libs/jsbarcode/3.11.3/JsBarcode.all.min.js"></script>
# </head>
# <body>
#
#   <div class="content">
#     <input type="text" id="text">
#     <svg id="barcode"></svg>
#      <script>
#       JsBarcode("#barcode", 'aa');
#       </script>
#     <button id="btn">Generate</button>
#   </div>
#
# </body>
# </html>
            # """
            print ('html', html)
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
                "enable-local-file-access": ""
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
                'url': "web/content/?model=asset.barcode.print&id=" + str(self.id) + "&filename_field=filename&field=data&filename=" + self.name,
                'target': 'new',
            }   
            
class AccountAsset(models.Model):
    _inherit = 'account.asset'


    barcode = fields.Char(string='Баркод')