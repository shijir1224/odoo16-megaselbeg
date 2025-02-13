# -*- coding: utf-8 -*-
#!/usr/bin/python
from odoo import api, models, fields
from odoo import _, tools
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import collections
import time

import json, requests
import qrcode
import base64
from io import StringIO, BytesIO
from PIL import Image  
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import pdfkit
from odoo.addons.mw_base_ebarimt.models.constants import *
import logging
_logger = logging.getLogger(__name__)

# Буцаалтын дэлгэц
class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'
    # Борлуулалтын ебаримт шалгах
    # Хэрэв ебаримт өгсөн бол төлвийг шалгаж буцаадаг байх
    def create_returns(self):
        if self.picking_id.sale_id and self.picking_id.sale_id.ebarimt_state == 'sent':
            raise UserError("Е-баримтыг эхлээд буцаана уу!")

        res = super(ReturnPicking, self).create_returns()
        return res

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.depends('move_ids','move_ids.state')
    def _compute_get_delivered_qty(self):
        for item in self:
            qty = 0.0
            for move in item.move_ids.filtered(lambda r: r.state != 'cancel' and not r.scrapped and r.location_dest_id.usage!='customer'):
                qty += move.product_uom._compute_quantity(move.product_uom_qty, item.product_uom)
            item.return_qty_non_store = qty
    # Columns
    return_qty_non_store = fields.Float(string=u'Буцах ёстой', readonly=True, compute='_compute_get_delivered_qty')

class SaleOrder(models.Model):
    _inherit = "sale.order"

    ebarimt_type = fields.Selection([
            ('none','None'),
            ('person','Person'),
            ('company','Company')], 
        'Ибаримт төрөл', states={'draft': [('readonly', False)]})    
    ebarimt_inv_type = fields.Selection([
            ('ebarimt','Ибаримт'),
            ('invoice','Нэхэмжлэх'),
            ], 
        'Ибаримт нэхэмжлэх төрөл', states={'draft': [('readonly', False)]}, default='ebarimt')        
    lottery = fields.Char('Lottery', copy=False)
    qrdata = fields.Char('QR data', copy=False)
    ddtd = fields.Char('DDTD', copy=False)
    total_vat = fields.Float('Total vat', copy=False)
    total_citytax = fields.Float('Total cityTax', copy=False)
    ebarimt_state = fields.Selection([('draft','Draft'), ('sent','Sent'), ('return','Returned')],'Ebarimt State', default='draft', copy=False, tracking=True)
    return_success = fields.Char('Return success', copy=False)
    ebarimt_note = fields.Char('Ebarimt note', copy=False)

    noat_amount = fields.Float('Total vat', copy=False)

    total_ebarimt = fields.Float('Total ebarimt', copy=False)
    # Logger
    ebarimt_log_note = fields.Text(string='Ebarimt LOG note', copy=False, readonly=True, default='')

    is_zahialsan_toonoos_ebarimt = fields.Boolean(string=u'Захиалсан тооноос ибаримт өгөх' , default=False)

    @api.depends('order_line.return_qty_non_store')
    def _return_amount_all(self):
        for order in self:
            return_tot_not_store = 0
            for line in order.order_line:
                if line.return_qty_non_store != 0:
                    return_tot_not_store += line.price_unit * line.return_qty_non_store
                        
            order.update({
                'ebarimt_return_amount': order.amount_total-return_tot_not_store if return_tot_not_store>0 else 0
            })
    ebarimt_return_amount = fields.Monetary(string=u'Ибармтад Засварлагдах Дүн', readonly=True, compute='_return_amount_all',)

    # Гараас сонгодог талбарууд ================
    is_free_tax_type = fields.Boolean(string=u'Татвараас чөлөөлөгдөх эсэх', default=False, 
        states={'sale': [('readonly', True)],'done': [('readonly', False)]}
        )
    organization_name = fields.Char(string=u'Байгууллагын нэр', copy=False )
    organization_register = fields.Char(string=u'Байгууллагын регистер', size=10, copy=False )

    amount_tax_vat = fields.Float(compute='_compute_taxes', string='Taxes VAT', digits=0)
    amount_tax_city = fields.Float(compute='_compute_taxes', string='Taxes City', digits=0)
    
    def _amount_tax(self, line, fiscal_position_id, ebarimt_tax_type_code):
        print ('ebarimt_tax_type_code ',ebarimt_tax_type_code)
        taxes = line.tax_id.filtered(lambda
                                          t: t.company_id.id == line.order_id.company_id.id and t.ebarimt_tax_type_id.code == ebarimt_tax_type_code)
        print('55555555',taxes)
        print('555555556',line)
        print('555555557',ebarimt_tax_type_code)
        
        
        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes)
        
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        cur = line.order_id.pricelist_id.currency_id
        taxes = \
            taxes.compute_all(price, cur, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id or False)[
                'taxes']
        val = 0.0
        print('4444444444',taxes)
        for c in taxes:
            val += c.get('amount', 0.0)
            print('33333333',val)
        return val
    @api.depends('order_line.price_subtotal', 'order_line.discount', 'order_line')
    def _compute_taxes(self):
        for order in self:
            # print(sfasafasf)
            currency = order.pricelist_id.currency_id
            order.amount_tax_vat = currency.round(
                sum(self._amount_tax(line, order.fiscal_position_id, TAX_TYPE_VAT) for line in order.order_line))
            print('111111111111',order.amount_tax_vat)
            order.amount_tax_city = currency.round(
                sum(self._amount_tax(line, order.fiscal_position_id, TAX_TYPE_CITY) for line in order.order_line))
            print('222222222222',order.amount_tax_city)
            
    tax_type = fields.Char(string='Bill Tax Type', compute='_tax_type')

    @api.depends('order_line')
    def _tax_type(self):
        self.tax_type = None
        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code ==TAX_TYPE_VAT for t in self.order_line.tax_id):
            self.tax_type = TAX_TYPE_VAT
        if all(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == TAX_TYPE_CITY for t in self.order_line.tax_id):
            self.tax_type = TAX_TYPE_CITY
        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == TAX_TYPE_VAT_ZERO for t in self.order_line.tax_id):
            self.tax_type = TAX_TYPE_VAT_ZERO
        if self.partner_id and self.partner_id.group_invoice:
            self.tax_type = TAX_TYPE_VAT_FREE
        print('self.tax_type',self.tax_type)
        
    @api.onchange('partner_id')
    def onchange_partner_id_ebarimt(self):
        for obj in self:
            obj.ebarimt_type = obj.partner_id.tin_type
            obj.organization_register = obj.partner_id.vat
            if obj.partner_id.parent_id:
                obj.organization_register = obj.partner_id.parent_id.vat
                obj.ebarimt_type = obj.partner_id.parent_id.tin_type
            obj.onchange_organization_register()

    # Байгууллагын нэр авах ====================
    @api.onchange('organization_register')
    def onchange_organization_register(self):
        if self.organization_register:
            ur = "http://info.ebarimt.mn/rest/merchant/info?regno="+self.organization_register+""
            try:
                res = requests.get(ur)
                n = res.json()
                name = n['name']
                name = name.replace('\n',' ')
                self.organization_name = name
            except Exception:
                self.organization_name = ""

    def create_ebarimt(self):
        '''
        Ибаримт үүсгэх
        :return:
        '''
        _logger.info("--- Ebarimt create request")
        if self.state not in ['sale','done']:
            raise UserError(u"Борлуулалт батладаагүй байна!")

        if self._check_ebarimt_type() and self.ebarimt_state in ['draft', 'return']:
            _logger.info("--- Ebarimt tin type: %s"%(self.ebarimt_type))
            # # Е-баримтын бодлого шалгах - Гараас оруулах эсвэл Харилцагчаас авах
            res_config = self.env['res.config.settings']
            if not self.organization_register and self.ebarimt_type == 'company':
                raise UserError(u"Байгууллагын регистерийг оруулна уу!")

   # # Нэхэмжлэлийн бодлого шалгах
   # delivery_policy = res_config.sudo().create({}).default_invoice_policy
   # if delivery_policy == 'delivery':
   #     if self.picking_ids and 'done' not in self.picking_ids.mapped('state'):
   #         raise UserError(u"Захиалгын хүргэлт дуусаагүй байна, Зарлага гарсны дараа Е-баримт өгнө!")

            consumerNo = ""
            customerTin=""
            billType = "B2C_RECEIPT"
            if self.ebarimt_inv_type=='invoice':
                   billType = "B2C_INVOICE"
            
            if self.ebarimt_type == 'company':
                if self.ebarimt_inv_type=='ebarimt':
                    billType = "B2B_RECEIPT"
                    customerTin = str(self.organization_register)
    
                    tin_url = "https://api.ebarimt.mn/api/info/check/getTinInfo?regNo={0}".format(self.organization_register)
                    tin_result = requests.get(tin_url)
                    regNo = json.loads(tin_result.text).get('data') if tin_result.status_code == 200 else False
                    customerTin = regNo
                elif self.ebarimt_inv_type=='invoice':
                       billType = "B2B_INVOICE"
            taxType = "VAT_ABLE"
            # Хэрэв чөлөөлөгдөх бол
            if self.partner_id.nuat_no:
                taxtype = "2"

            stocks = []
            total_amount=self.amount_total
            total_vat=round(total_amount/1.1,6)*0.1
            receipts=[]
            items=[]

            vat=0
            city_tax=0
            if self.amount_tax_vat:
                vat=round(total_amount/1.1*0.1,2)
            if self.amount_tax_city:
                city_tax=round(total_amount / 112*2,6)
                            
            for line in self.order_line:
                ttt =round(line.price_total,2)
                vat_sub=0
                if self.amount_tax_vat:
                    vat_sub=round(ttt/1.1*0.1,2)
                
                tmp={
                            "name": line.product_id.name,
                            "barCode": '',
                            "barCodeType": "UNDEFINED",
                            "classificationCode": "8843000",
                            "measureUnit":line.product_uom.name,
                            "qty": line.product_uom_qty,
                            "unitPrice": line.price_unit,
                            "totalBonus": 0,
                            "totalVAT": vat_sub,
                            "totalCityTax": 0,
                            "totalAmount": ttt,
                            # "tax_ids":taxes
                            }
                items.append(tmp)  
                print ('self.order_id.company_id.eb_tin_so ',self.company_id.eb_tin_so)
            tmp2={
                        "totalAmount":total_amount,
                        "totalVAT":vat,
                         "taxType": "VAT_ABLE",
                         "merchantTin":self.company_id.eb_tin_so,
                         "items":items,
                        }
                # paidAmount=amountTotal;
            receipts.append(tmp2)            
                     
            data={
                        "totalAmount": total_amount,
                        "totalVAT": vat,
                        "totalCityTax": 0,
                         "districtCode":self.company_id.eb_district_code_so,
                        "merchantTin": self.company_id.eb_tin_so,#"73101472838",
                        "branchNo": "001",
                        "posNo": "001",
                        "customerTin": customerTin,
                        "consumerNo": consumerNo,
                        "type": billType,
                        "inactiveId": "",
      # "reportMonth": None,
                            "receipts": receipts,

                        }    
            if billType not in ('B2B_INVOICE','B2C_INVOICE'):
            	data.update({"payments": [
							{
								"code": "CASH",
								"status": "PAID",
								"paidAmount": total_amount
							}
						]}) 
            # print ('data12345 ',data)
            _logger.info("--- Ebarimt data: %s", data)
    
            if self.env.user.company_id.ebarimt_url_so:
                url=self.env.user.company_id.ebarimt_url_so+'/rest/receipt'
            else:
                raise UserError(u'Компаний тохиргоон дээр ибаримт url тохируулаагүй байна!!!')
   # data=json.loads(data)
            response = requests.post(url, json = data)
            print ('response.text ',response.text)
            data = {}
            _logger.info("--- Ebarimt put response status code: %s", response.status_code)
            if response.status_code == 200:
                data = response.json()
                _logger.info("Ebarimt put response json --- : %s", data)
                
            # p1 = ctypes.c_char_p(put_data.encode('utf-8'))
            else:
                d = response.json()
                raise UserError(d['message'])                
    # raise UserError(_('Ebarimt connection error! status code: %s' % (response.status_code)))
            d=data
            name=''
            lottery=''
            if self.ebarimt_type == 'company' and d.get('lottery',False):
                lottery = d['lottery']
            self.lottery = lottery
            self.qrdata = d['qrData']
            if self.ddtd != d['id']:
                name = name+'  before ddtd'+ d['id']
            self.ddtd = d['id']
            self.total_vat = d['totalVAT']
            self.total_citytax = d['totalCityTax']
            self.total_ebarimt = d['totalAmount']
            
            # if retB:
            #     self.ebarimt_state = 'return'
            # else:    
            self.ebarimt_state = 'sent'
            self.write_ebarimt_log_note(d['id'])
            
            if self.ebarimt_note:
                self.ebarimt_note = self.ebarimt_note+'  |  '+self.name+' '+name
            else:
                self.ebarimt_note = self.name+' '+ name
            
   # return x.text 

        else:
            _logger.info("--- Ebarimt put request, don't send SO: %s, ebarimt type: %s, state: %s"%(self.id, self.ebarimt_type, self.ebarimt_state))
            raise UserError('Ebarimt олгосон байнэ, Эсвэл баримт олгох төрлөө сонгоогүй байна.!!')            

       
    # ==========================================
    def action_ebarimt_draft(self):
        self.ebarimt_state = 'draft'

    # E-TAX URL авах
    def _get_etax_url(self):
        # Компани мэдээлэл дээрээс etax URL авах
        if self.company_id.ebarimt_url_so:
            return self.company_id.ebarimt_url_so
        else:
            return False
        
 # def action_returnBill(self):
 #     _logger.info('VAT: GET str(br.bill_id) ----> : %s' % str(self.ddtd))
 #     r = u"{ \"returnBillId\":\""+str(self.ddtd)+"\",\
 #                       \"date\": \""+str(self.date_order)+"\"}"
 #     if self.ddtd and self.ebarimt_state=='sent':
 #         data = ''
 #         etax_url = self._get_etax_url()
 #         if not etax_url:
 #             raise UserError("Е-баримтын сервэрийн IP-г тохируулж өгнө үү!")
 #         _logger.info(u'=================E tax URL----------------- {0}'.format(etax_url))
 #         header = {'Content-Type':'application/json; charset=utf-8'}
 #         data = requests.post(etax_url+'/posapi_returnbill', data=r.encode('utf-8'), headers=header)
 #
 #         _logger.info('VAT: GET action_returnBill ----> : %s' % data)
 #         ebarimt_note = ''
 #         if self.ebarimt_note:
 #             ebarimt_note = self.ebarimt_note+' | '+'REFUND FULL '+self.ddtd
 #         else:
 #             ebarimt_note = self.name+' | '+'REFUND FULL '+self.ddtd
 #         return self.write({'ebarimt_note':ebarimt_note, 'ebarimt_state':'return', 'return_success':data})

#####################EBarimt butsaah #####################
    def generate_return_bill_json(self):
        data = {}
        data['id'] = self.ddtd
        data['date'] = self.date_order.strftime('%Y-%m-%d %H:%M:%S')
        # data['amount'] = '%s'%(self.amount_paid)
        return data
    
    def action_returnBill(self):
        r = self.generate_return_bill_json()
        _logger.info('VAT: GET data ----> : %s' % r)
        if self.ddtd :
            data = ''
            etax_url = self.env.user.company_id.ebarimt_url_so
            if not etax_url:
                raise UserError("Е-баримтын сервэрийн IP-г тохируулж өгнө үү!")
            _logger.info(u'=================E tax URL----------------- {0}'.format(etax_url+'/rest/receipt'))
            headers = {
                'Content-Type': 'application/json'
            }
            # _logger.info(u'=================E tax json data----------------- {0}'.format(json.dumps(r['data'])))
            # print('daaataaa',r['data'])
            response = requests.delete(etax_url+'/rest/receipt', headers=headers, data=json.dumps(r), verify=True)
            _logger.info('VAT: GET action_returnBill ----> : %s' % response)
            if response.status_code == 200:
                # print ('response.content::: ',response.content)
                # data = response.json()
                _logger.info("Ebarimt send response json --- : %s", data)
            else:
                _logger.info("Ebarimt send response error --- : %s", response.content)
                raise UserError(_('Ebarimt connection error! status code: %s' % response.status_code))
            ebarimt_note = ''
            if self.ebarimt_note:
                ebarimt_note = self.ebarimt_note+' | '+'REFUND FULL '+self.ddtd
            else:
                ebarimt_note = self.name+' | '+'REFUND FULL '+self.ddtd
            return self.write({'ebarimt_note':ebarimt_note,'ebarimt_state':'return' ,  'return_success':data})
   
    def _get_etax_url(self):
        # Компани мэдээлэл дээрээс etax URL авах
        if self.env.user.company_id.ebarimt_url:
            return self.env.user.company_id.ebarimt_url
        else:
            return False
        
    def _action_sendData(self):
        etax_url = self._get_etax_url()
        for company in etax_url:
            etax_url = etax_url+'/sendData'
            _logger.info(u'=================E tax URL----------------- {0}'.format(etax_url))
            header = {'Content-Type':'application/json'}
            send_data_log = self.env['ebarimt.send.data.log'].create({'request_url': etax_url})
            response = requests.get(etax_url, data={}, headers=header)
            data = response.json()
            send_data_log.write({'response_data': data, 'response_status': response.content})
            _logger.info(u'=================E tax Send RESPONSE json data----------------- {0}'.format(data))
            _logger.info(u'=================E tax Send RESPONSE----------------- {0}'.format(response.content))


    def modify_ebarimt(self):
        _logger.info('MODIFY_EBARIMT %s'%(self.name))
        if self._check_ebarimt_type() and self.ebarimt_state=='sent' and self.ebarimt_return_amount!=0 and self.ddtd:
            _logger.info('************ MODIFY_EBARIMT%s'%(self.name))
            self.action_put(self, self.ddtd)
        elif self._check_ebarimt_type() and self.ebarimt_state=='sent' and self.ebarimt_return_amount==0 and self.ddtd and sum(self.order_line.mapped('return_qty_non_store'))==sum(self.order_line.mapped('product_uom_qty')):
            self.action_returnBill()

    def _check_ebarimt_type(self):
        if self.ebarimt_type in ['person','company']:
            return True
        else:
            return False

    # E баримтын лог хөтлөх
    def write_ebarimt_log_note(self, billId=''):
        if self.ebarimt_log_note:
            self.ebarimt_log_note += str(datetime.now())+': %s &**& ' % self.env.user.login +billId+'\n'
        else:
            self.ebarimt_log_note = str(datetime.now())+': %s ' % self.env.user.login +billId+'\n'

    def print_ebarimt(self):
        message = '' #'_("<p>Эрхэм харилцагч %s танаа,<br/>Here is your electronic ticket for the %s. </p>") % (self.partner_id.name, name)
        registr=''
        suff=''
        if self.ebarimt_type=='company':
            registr=u'Регистрийн дугаар: {0}'.format(self.partner_id.vat)
        row_data=''

        for line in self.order_line:
            ttt =round(line.price_total,2)
            vat_sub=0
            if self.amount_tax_vat:
                vat_sub=round(ttt/1.1*0.1,2)
            row_data+='<tr>\
                <td>{0}</td>\
                <td>{1}</td>\
                <td>{2}</td>\
            </tr>'.format(str(line.product_id.name),line.price_unit,ttt)
            
        rro='''
             <table class="ck-table-resized">
                    <colgroup>
                        <col style="width:55.27%;">
                        <col style="width:27.01%;">
                        <col style="width:17.72%;">
                    </colgroup>
                    <tbody>
                        <tr>
                            <td><strong>Бараа</strong></td>
                            <td><strong>Нэгж үнэ</strong></td>
                            <td><strong>Нийт</strong></td>
                        </tr>
                        {0}
                    </tbody>
                </table> '''.format(row_data)
                  
        message+='''
        <div style="max-width:400px;background:#fff;box-sizing:border-box;margin-top:30px;outline:1px rgba(0,0,0,.1) solid;line-height:18px">
                    <div style="padding:16px">
                      <div style="margin-top:16px">
                        <div style="font-size:12px;color:#333333;margin-bottom:7px">
                          {0} оны {1} сарын {2} ны өдрийн {3} төгрөгийн 
                          <span style="color:green"><span class="il">Ибаримт</span>
                        </div>
                        <div style="font-size:14px">
                          <div>
                            <table style="background:#fff;border-spacing:0;border-collapse:collapse;font-size:14px;width:100%">
        <tbody><tr><td>Дугаар:
        </td><td>{8}</td></tr><tr><td>Мөнгөн дүн:
        </td><td>{7}₮</td></tr><tr><td>НӨАТ:</td><td>{10} ₮</td></tr><tr><td><b><span style="font-size:9.0pt;color:#555555">НИЙТ МӨНГӨН ДҮН:
        </span></b></td><td><b>{7}₮</b></td></tr></tbody>                    </table>
                          </div>
                        </div>
                      </div>
                      {11}
                      <div>
                        <table>
                          <tbody><tr>
                            <td>
                                <div style="margin-top:16px;font-size:12px;color:#999">
                                  <img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={4}" class="mb-4"/>
                                </div>
                            </td>
                            <td> 
                            </td>
                          </tr>
                        </tbody>
                        </table>
         <div style="margin-top:8px;font-size:12px;color:#555555">
                           <span>{9}</span>
                           <span>Сугалааны дугаар:</span><span style="color:#333333">{5}</span>
                          </div>
                          <div style="margin-top:8px;font-size:12px;color:#555555">
                          <span><span class="il">Ebarimt</span> дүн:</span><span style="color:#333333">{7}</span>
                          </div>
                          <div style="margin-top:8px;font-size:12px;color:#555555">
                          <span>ДДТД:</span><span style="color:#333333">{6}<wbr></span>
                          </div>
                        </div>
                        
                      </div>
                    </div>
        '''.format(self.date_order.year,self.date_order.month,self.date_order.day,self.total_ebarimt,self.qrdata,self.lottery,self.ddtd,self.total_ebarimt,suff,registr,self.total_vat,rro)
                                # <div style="margin-top:16px;font-size:12px;color:#999">
                                #   <img src=https://chart.googleapis.com/chart?chs=150x150&amp;cht=qr&amp;chl={4} height="150px" width="150px" class="CToWUd">
                                # </div>
                          
                          # <div style="margin-top:8px;font-size:12px;color:#555555">
                          # <span><span class="il">Жич: уг имэйл нь автомат тул хариу ирүүлэх шаардлагагүй.</span><span style="color:#333333"></span>
                          # </div>        
        file_name = u"%s  ebarimt" % ( self.date_order)
        options = {
                'margin-top': '20mm',
                'margin-right': '1mm',
                'margin-bottom': '8mm',
                'margin-left': '1mm',
                'encoding': "UTF-8",
                'header-spacing': 2,
                'orientation': 'Landscape',
                'page-size': 'A3',  
                }
        # print ('message`3 ',message)
        html = self.encode_for_xml(message, 'ascii')
        
        output = BytesIO(pdfkit.from_string(html.decode('utf-8'), False, options=options))
        out = base64.encodebytes(output.getvalue())
        excel_id = self.env['report.excel.output'].create({
                    'data': out,
                    'name': file_name
        })
        return {
                    'type':'ir.actions.act_url',
                    'url':"web/content/?model=report.excel.output&id=" + str(excel_id.id) +"&filename_field=filename&download=true&field=data&filename=" +excel_id.name,
                    'target':'new',
        }                
        
    def encode_for_xml(self, unicode_data, encoding='ascii'):
        try:
            return unicode_data.encode(encoding, 'xmlcharrefreplace')
        except ValueError:
            return self._xmlcharref_encode(unicode_data, encoding)
                    
    # QR код бэлдэж зургаар хадгалах
    def generate_qrcode(self):
        if self.qrdata:
            text = self.qrdata
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=0,
            )
            qr.add_data(text)
            qr.make(fit=True)
            img = qr.make_image(fill_color="#010101", back_color="white")
            buffered = BytesIO()
            img.save(buffered)
            img_str = base64.b64encode(buffered.getvalue())
            return img_str
        return False

    # Е-баримт илгээх КРОН =====================================================
    def _action_sendData(self):
        companies = self.env['res.company'].sudo().search([('etax_url','!=',False)])
        for company in companies:
            etax_url = company.etax_url+'/sendData'
            _logger.info(u'=================E tax URL----------------- {0}'.format(etax_url))
            header = {'Content-Type':'application/json'}
            send_data_log = self.env['ebarimt.send.data.log'].create({'request_url': etax_url})
            response = requests.get(etax_url, data={}, headers=header)
            data = response.json()
            send_data_log.write({'response_data': data, 'response_status': response.content})
            _logger.info(u'=================E tax Send RESPONSE json data----------------- {0}'.format(data))
            _logger.info(u'=================E tax Send RESPONSE----------------- {0}'.format(response.content))
        