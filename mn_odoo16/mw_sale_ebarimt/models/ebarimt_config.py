# -*- coding: utf-8 -*-

from odoo import api, models, fields
import time
# import vatbridge
import logging
_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    # get_ebarimt_info_from_input = fields.Boolean(string="Е-баримтын мэдээллийг гараас", default=False, 
    #     help="Е-баримтын мэдээллийг гараас бөглөж илгээх бол сонгоно уу, Үгүй бол харилцагч дээрх мэдээллийг авна")
    #
    # ebarimt_so_url = fields.Char('EBarimt URL', default='https://services.elibrary.mn/noatus/put?lib=')
    # aimag_district_code = fields.Char(string="Aimag/District code")
    # branch_so_no = fields.Char(string="Branch No", required=True, default="001")
    # pos_so_no = fields.Char(string="POS No", required=True, default="0001")

    is_with_ebarimt_so = fields.Boolean(string='Ebarimt олгох?')
    ebarimt_url_so = fields.Char(string='Ebarimt url')
    is_ebarimt_offline_so = fields.Boolean(string='Is offline?')
    

    eb_district_code_so = fields.Char(string='districtCode',)
    eb_tin_so = fields.Char(string='merchantTin',)
        
class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # get_ebarimt_info_from_input = fields.Boolean(related="company_id.get_ebarimt_info_from_input",
    #     string="Е-баримтын мэдээллийг гараас", readonly=False, 
    #     help="Е-баримтын мэдээллийг гараас бөглөж илгээх бол сонгоно уу, Үгүй бол харилцагч дээрх мэдээллийг авна", )
    #
    # ebarimt_so_url = fields.Char(related='company_id.ebarimt_so_url', string='EBarimt URL', readonly=False)
    # aimag_district_code = fields.Char(related='company_id.aimag_district_code', string='Aimag/District code', readonly=False)


    ebarimt_url_so = fields.Char(related='company_id.ebarimt_url_so', string='Ebarimt url', readonly=False)
    is_ebarimt_offline_so = fields.Boolean(related='company_id.is_ebarimt_offline_so', string='Is offline', readonly=False)

    is_with_ebarimt_so = fields.Boolean(related='company_id.is_with_ebarimt_so', string='Ebarimt олгох?', readonly=False)

    eb_district_code_so = fields.Char(related='company_id.eb_district_code_so', string='districtCode', readonly=False)
    eb_tin_so = fields.Char(related='company_id.eb_tin_so', string='merchantTin', readonly=False)

class EbarimtSendDataLog(models.Model):
    _name = 'ebarimt.send.data.log'

    request_url = fields.Char(string='Request URL')
    response_data = fields.Text(string='Response data')
    response_status = fields.Text()


# class vat_config_so(models.Model):
#     _name = "vat.config.so"
#     _description = "VAT DATA SEND"
#
#     date = fields.Datetime('Огноо', select=True, required=True,default=time.strftime('%Y-%m-%d %H:%M:%S'))
#     text= fields.Text('Тайлбар')
#     company_id = fields.Many2one('res.company','Company')
#
#     def action_getInformation(self):
#         _logger.info('action_getInformation')
#         data = vatbridge.getInformation()
#         _logger.info('VAT: GET INFORMATION ----> : %s' % data)
#         return self.write({'text':data})
#
#     def action_checkAPI(self):
#         _logger.info('action_checkAPI')
#         data = vatbridge.checkApi()
#
#         _logger.info('VAT: GET checkApi ----> : %s' % data)
#         return self.write({'text':data})
#
#     def action_callFunction(self):
#         data = vatbridge.callFunction()
#         return self.write({'text':data})
#
#     def action_returnBill(self, cr, uid, ids, context=None):
#         data = vatbridge.returnBill()
#         return self.write({'text':data})
#
#     def action_sendData(self):
#         data = vatbridge.sendData()
#         _logger.info('VAT: GET sendData ----> : %s' % data)
#         return self.write({'text':data})
#
#     def _action_sendData(self):
#         for item in self.env['vat.config.so'].search([]):
#             item.action_sendData()
#
#     def get_datas(self, id, context=None):
#         datas = {}
#         temp = []
#         obj = self.browse(id)
#         for pa in obj:
#                 temp.append(pa)
#         datas['datas'] = temp
#         _logger.info("----------------- Routes ===%s=== ",str(datas))
#         return datas

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    nuat_no = fields.Boolean('НӨАТ-өөс чөлөөлөгдсөн', default=False, copy=False, help=u'НӨАТ-өөс чөөлөгдсөн бол чагтална')
    tin_type = fields.Selection([('company','Company'),('person','Person'),('none','none')], default='person', string='Tin type')

class StockPicking(models.Model):
    _inherit = "stock.picking"
    
    def get_sale_qrdata(self, ids):
        report_id = self.browse(ids)
        sale_id = report_id.sale_id

        if sale_id:
#             tax_with = self.env.context.get('is_with_tax', False)
#             if tax_with:
#                 sale_id.create_ebarimt()
            # if sale_id.ebarimt_type in ['person']:
            if sale_id.qrdata:
                image_buf = sale_id.generate_qrcode()
                image_str = '<img alt="Embedded Image" width="120" src="data:image/png;base64,'+image_buf+'" />'
                return image_str
            
        return ''

    def get_sale_ddtd(self, ids):
        report_id = self.browse(ids)
        sale_id = report_id.sale_id

        if sale_id:
#             tax_with = self.env.context.get('is_with_tax', False)
#             if tax_with:
#                 sale_id.create_ebarimt()
            if sale_id.ddtd:
                return u'ДДТД: '+sale_id.ddtd
            
        return ''

    def get_sale_lottery(self, ids):
        report_id = self.browse(ids)
        sale_id = report_id.sale_id

        if sale_id:
#             tax_with = self.env.context.get('is_with_tax', False)
#             if tax_with:
#                 sale_id.create_ebarimt()
            if sale_id.lottery:
                return u'Сугалааны дугаар: '+sale_id.lottery
            
        return ''