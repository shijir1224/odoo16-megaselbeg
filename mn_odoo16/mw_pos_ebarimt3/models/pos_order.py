from odoo import api, fields, models, _
import requests
import json
from odoo.addons.mw_base_ebarimt.models.constants import *
from odoo.exceptions import UserError

class PosOrder(models.Model):
    _inherit = "pos.order"


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _apply_invoice_payments(self):
        '''Төлбөр үүсгэж төлөхгүй
        '''
        return True

    bill_id = fields.Char(string='Bill ID', help="EBarimt Bill Id.")
    bill_printed_date = fields.Datetime(string='Bill Printed Date')
    bill_type = fields.Selection([(BILL_TYPE_NOTAX, 'No Tax'),
                                  (BILL_TYPE_INDIVIDUAL, 'Individual'),
                                  (BILL_TYPE_COMPANY, 'Company'),
                                  (BILL_TYPE_INVOICE, 'Invoice'),
                                  (BILL_TYPE_B2B_INVOICE,'Invoice C')], default=BILL_TYPE_INDIVIDUAL)
    bill_mac_address = fields.Char(string='Bill MAC Address')
    tax_type = fields.Char(string='Bill Tax Type', compute='_tax_type')
    amount_tax_vat = fields.Float(compute='_compute_taxes', string='Taxes VAT', digits=0)
    amount_tax_city = fields.Float(compute='_compute_taxes', string='Taxes City', digits=0)
    customer_register = fields.Char('Customer Register')
    customer_name = fields.Char('Customer Name')

    def _amount_tax(self, line, fiscal_position_id, ebarimt_tax_type_code):
        taxes = line.tax_ids.filtered(lambda
                                          t: t.company_id.id == line.order_id.company_id.id and t.ebarimt_tax_type_id.code == ebarimt_tax_type_code)
        print('55555555',taxes)
        print('555555556',line)
        print('555555557',ebarimt_tax_type_code)

    
        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes)

        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        cur = line.order_id.pricelist_id.currency_id
        taxes = \
            taxes.compute_all(price, cur, line.qty, product=line.product_id, partner=line.order_id.partner_id or False)[
                'taxes']
        val = 0.0
        print('4444444444',taxes)
        for c in taxes:
            val += c.get('amount', 0.0)
            print('33333333',val)
        return val

    @api.depends('lines.price_subtotal_incl', 'lines.discount', 'lines')
    def _compute_taxes(self):
        for order in self:
            # print(sfasafasf)
            currency = order.pricelist_id.currency_id
            order.amount_tax_vat = currency.round(
                sum(self._amount_tax(line, order.fiscal_position_id, 'TAX_TYPE_VAT') for line in order.lines))
            print('111111111111',order.amount_tax_vat)
            order.amount_tax_city = currency.round(
                sum(self._amount_tax(line, order.fiscal_position_id, 'TAX_TYPE_CITY') for line in order.lines))
            print('222222222222',order.amount_tax_city)
    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        order_fields['customer_register'] = ui_order.get('customerReg', False)
        order_fields['customer_name'] = ui_order.get('customerName', False)
        order_fields['bill_type'] = ui_order['bill_type']
        if order_fields.get('partner_id', False):
            if self.env['res.partner'].browse(order_fields['partner_id']).group_invoice:
                lines = order_fields['lines']
                for item in lines:
                    del item[2]['tax_ids']
        return order_fields

    @api.model
    def _payment_fields(self, order, ui_paymentline):
        order_fields = super(PosOrder, self)._payment_fields(order, ui_paymentline)

        if ui_paymentline.get('utga', False):
            order_fields.update({'name': ui_paymentline.get('utga', '')})
        return order_fields


    @api.depends('lines')
    def _tax_type(self):
        self.tax_type = None
        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code =='TAX_TYPE_VAT' for t in self.lines.tax_ids):
            self.tax_type = 'TAX_TYPE_VAT'
        if all(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == 'TAX_TYPE_CITY' for t in self.lines.tax_ids):
            self.tax_type = 'TAX_TYPE_CITY'
        if any(self.env['ebarimt.tax.type'].browse(t.ebarimt_tax_type_id.id).code == 'TAX_TYPE_VAT_ZERO' for t in self.lines.tax_ids):
            self.tax_type = 'TAX_TYPE_VAT_ZERO'
        if self.partner_id and self.partner_id.group_invoice:
            self.tax_type = 'TAX_TYPE_VAT_FREE'
        print('self.tax_type',self.tax_type)


    @api.model
    def get_ebarimt(self, server_ids , data=''):
        ebarimt_data = ''

        for s in server_ids:
            order = self.env['pos.order'].browse(s['id'])
            # if order.bill_type == BILL_TYPE_NOTAX:
            #     return ebarimt_data

            # if order.to_invoice:
            #     return ebarimt_data
            ebarimt_data = order.set_ebarimt(data)
            data=json.loads(ebarimt_data)
            dd=data.get("type",'')
            order.bill_id = data.get("id",'')
            order.bill_type= dd
            
        return ebarimt_data
    
    @api.model
    def set_ebarimt(self, data):
        print('vals',self)
        print ('data  ',data)
        # for d in data:
        #     print ('dddd ',d)
        self._tax_type()
        self._compute_taxes()
        # НӨАТ Чөлөөлөгдөх үед авах 
        if self.partner_id and self.partner_id.group_invoice == True and self.partner_id.vat:
            tin_url = "https://api.ebarimt.mn/api/info/check/getTinInfo?regNo={0}".format(self.partner_id.vat)
            tin_result = requests.get(tin_url)
            regNo = json.loads(tin_result.text).get('data') if tin_result.status_code == 200 else False
            data=json.loads(data)
            vat=0
            city_tax=0
            total_amount_vat=0
            total_amount=round(data.get('totalAmount',0),6)
            if total_amount:
                vat=round(total_amount/1.1,6)*0.1
                total_amount_vat = round(total_amount-vat,6)
            data['totalAmount']=total_amount_vat
            data['totalVAT']=0
            data['totalCityTax']=0
            data['customerTin']=regNo
            data['taxProductCode']="318"
            
            for d in data['receipts']:                                    
                d['totalAmount']=total_amount_vat
                d['totalVAT']=0
                d['totalCityTax']=0
                d['taxProductCode']="318"
                d['taxType']="VAT_FREE"
                for i in d['items']:
                    i['totalAmount']=total_amount_vat
                    i['totalVAT']=0
                    i['totalCityTax']=0
                    i['taxProductCode']="318"
                    i['unitPrice'] = total_amount_vat
            for p in data['payments']:
                p['paidAmount'] = total_amount_vat
        # НӨАТ 0 хувь үед авах 
        elif self.tax_type =="TAX_TYPE_VAT_ZERO":
            data=json.loads(data)
            vat=0
            city_tax=0
            total_amount_vat=0
            total_amount=round(data.get('totalAmount',0),6)
            data['totalAmount']=total_amount
            data['totalVAT']=0
            data['totalCityTax']=0
            data['taxProductCode']="501"
            
            for d in data['receipts']:                                    
                d['totalAmount']=total_amount
                d['totalVAT']=0
                d['totalCityTax']=0
                d['taxProductCode']="501"
                d['taxType']="VAT_ZERO"
                for i in d['items']:
                    i['totalAmount']=total_amount
                    i['totalVAT']=0
                    i['totalCityTax']=0
                    i['taxProductCode']="501"
                    i['unitPrice'] = total_amount
            for p in data['payments']:
                p['paidAmount'] = total_amount
        else:
            data=json.loads(data)
            vat=0
            city_tax=0
            total_amount=round(data.get('totalAmount',0),6)
            if self.amount_tax_vat:
                vat=round(total_amount/1.1,6)*0.1
            if self.amount_tax_city:
                city_tax=round(total_amount / 112*2,6)
            # if city_tax:
            #     total_amount+=city_tax
            data['totalAmount']=total_amount
            data['totalVAT']=vat
            data['totalCityTax']=city_tax
            if len(data.get('customerTin',''))>0:
                data['customerTin']=int(data['customerTin'])
            for d in data['receipts']:                                    
                d['totalAmount']=total_amount
                d['totalVAT']=vat
                d['totalCityTax']=city_tax
                for i in d['items']:
                    i['totalAmount']=total_amount
                    i['totalVAT']=vat
                    i['totalCityTax']=city_tax
        # url='http://203.34.37.106:7080/rest/receipt'
        url=''
        print ('url 1 ',url)
        if self.env.user.company_id.ebarimt_url:
            url=self.env.user.company_id.ebarimt_url+'/rest/receipt'
        aaa = json.dumps(data)
        print('aaaaaaaaa' , aaa)
        x = requests.post(url, json = data)
        print ('x.text ',x.text)
        return x.text
    
    def get_ebarimt_nuhuj(self ):
        ebarimt_data = ''

        for order in self:
            # if order.bill_type == BILL_TYPE_NOTAX:
            #     return ebarimt_data

            # if order.to_invoice:
            #     return ebarimt_data
            if order.bill_id:
                raise UserError(_('Аль хэдийн олгсоон байна.'))
            ebarimt_data = order.set_ebarimt_nuhuj(order)
            data=json.loads(ebarimt_data)
            dd=data.get("type",'')
            order.bill_id = data.get("id",'')
            order.bill_type= dd
            
        return ebarimt_data    
                

    def set_ebarimt_nuhuj(self,order):
        total_amount=order.amount_paid
        total_vat=round(total_amount/1.1,6)*0.1
        type=order.bill_type
        receipts=[]
        items=[]
        for line in order.lines:
            
            tmp={
                        "name": line.product_id.name,
                        "barCode": '',
                        "barCodeType": "UNDEFINED",
                        "classificationCode": "8843000",
                        "measureUnit": "ш",
                        "qty": line.qty,
                        "unitPrice": line.price_unit,
                        "totalBonus": 0,
                        "totalVAT": total_vat,
                        "totalCityTax": 0,
                        "totalAmount": total_vat,
                        # "tax_ids":taxes
                        }
            items.append(tmp)  

            tmp2={
                    "totalAmount":total_vat,
                    "totalVAT":total_vat,
                     "taxType": "VAT_ABLE",
                     "merchantTin":order.session_id.config_id.eb_tin,
                     "items":items,
                    }
            # paidAmount=amountTotal;
            receipts.append(tmp2)            
                 
        data={
                    "totalAmount": total_amount,
                    "totalVAT": total_vat,
                    "totalCityTax": 0,
                    "districtCode": order.session_id.config_id.eb_district_code,
                    "merchantTin": order.session_id.config_id.eb_tin,#"73101472838",
                    "branchNo": "001",
                    "posNo": "001",
                    "customerTin": "",
                    "consumerNo": "",
                    "type": type,
                    "inactiveId": "",
                    "reportMonth": '2024-01-15',
                        "receipts": receipts,
                    "payments": [
                        {
                            "code": "CASH",
                            "status": "PAID",
                            "paidAmount": total_amount
                        }
                    ]
                    };        
        # total_amount=round(data.get('totalAmount',0),6)
        # data['totalAmount']=total_amount
        # data['totalVAT']=round(total_amount/1.1,6)*0.1
        # if len(data.get('customerTin',''))>0:
        #     data['customerTin']=int(data['customerTin'])
        # for d in data['receipts']:                                    
        #     d['totalAmount']=round(d['totalAmount'],6)
        #     d['totalVAT']=round(d['totalAmount']/1.1,6)*0.1
        #     for i in d['items']:
        #         i['totalAmount']=round(i['totalAmount'],6)
        #         i['totalVAT']=round(i['totalAmount']/1.1,6)*0.1
                                                                     
        # url='http://203.34.37.106:7080/rest/receipt'
        url=''
        print ('datadata ',data)
        print ('url 1 ',url)
        if self.env.user.company_id.ebarimt_url:
            url=self.env.user.company_id.ebarimt_url+'/rest/receipt'
        x = requests.post(url, json = data)
        print ('x.text ',x.text)
        return x.text                
#         {
#     "totalAmount": 14000,
#     "totalVAT": 1272.73,
#     "totalCityTax": 0,
#     "districtCode": "2316",
#     "merchantTin": "73101472838",
#     "branchNo": "001",
#     "posNo": "001",
#     "customerTin": "",
#     "consumerNo": "",
#     "type": "B2C_RECEIPT",
#     "inactiveId": "",
#     "reportMonth": None,
#     "receipts": [
#         {
#             "totalAmount": 14000,
#             "totalBonus": 0,
#             "totalVAT": 1272.7299999999996,
#             "totalCityTax": 0,
#             "taxType": "VAT_ABLE",
#             "merchantTin": "73101472838",
#             "items": [
#                 {
#                     "name": "Цавуу /Жоби/",
#                     "barCode": "",
#                     "barCodeType": "UNDEFINED",
#                     "classificationCode": "0000000",
#                     "measureUnit": "ш",
#                     "qty": 1,
#                     "unitPrice": 14000,
#                     "totalVAT": 1272.7299999999996,
#                     "totalCityTax": 0,
#                     "totalAmount": 14000
#                 }
#             ]
#         }
#     ],
#     "payments": [
#         {
#             "code": "CASH",
#             "paidAmount": 14000,
#             "status": "PAID"
#         }
#     ],
#     "customerNo": "",
#     "taxType": "VAT_ABLE",
#     "customerName": ""
# }
        # print ('x.text ',x.text)
        

# '{"id":"","version":"3.1.22","totalAmount":100,"totalVAT":9.09,"totalCityTax":0,"branchNo":"001","districtCode":"1234","merchantTin":"73101472838","posNo":"001","customerTin":"","consumerNo":"","type":"B2C_RECEIPT","inactiveId":"123444444444555555556786544456788","reportMonth":"2024-01-09","receipts":[{"id":"","totalAmount":100,"taxType":"VAT_ABLE","items":[{"name":"[hibiki]  Виски /Hibiki ","barCode":"","barCodeType":"UNDEFINED","classificationCode":"8843000","measureUnit":"ш","qty":100,"unitPrice":100,"totalAmount":100,"totalVAT":9.090000000000003,"totalCityTax":0}],"merchantTin":"73101472838","totalVAT":9.090000000000003,"totalCityTax":0}],"payments":[{"code":"CASH","paidAmount":100,"status":"PAID"}],"posId":101315350,"status":"ERROR","message":"PosAPI-н ААН-н жагсаалтанд \'73101472838\' ТТД бүртгэлгүй байна.","date":"2024-02-01 08:59:46","easy":false}\n'
# >>> x = requests.post(url, json = data)
# >>> x.text
# '{"id":"073101472838001170677801410001681","version":"3.1.22","totalAmount":100,"totalVAT":9.09,"totalCityTax":0,"branchNo":"001","districtCode":"1234","merchantTin":"73101472838","posNo":"001","customerTin":"","consumerNo":"","type":"B2C_RECEIPT","inactiveId":"123444444444555555556786544456788","reportMonth":"2024-01-09","receipts":[{"id":"073101472838001170677801510001681","totalAmount":100,"taxType":"VAT_ABLE","items":[{"name":"[hibiki]  Виски /Hibiki ","barCode":"","barCodeType":"UNDEFINED","classificationCode":"8843000","measureUnit":"ш","qty":100,"unitPrice":100,"totalAmount":100,"totalVAT":9.090000000000003,"totalCityTax":0}],"merchantTin":"73101472838","totalVAT":9.090000000000003,"totalCityTax":0}],"payments":[{"code":"CASH","paidAmount":100,"status":"PAID"}],"posId":101314429,"status":"SUCCESS","qrData":"471343849951454553257368233962023443607118414362046383459715426296001695642482413445215121297175869549405897136673282067985103714437688863355405693544321226041951659473628661282640105660371908764","date":"2024-02-01 17:00:14","easy":false}\n'

    @api.model
    def get_merchant_info(self, urlInput):
        """ Get metchant info from ebarimt REST api """
        resp = requests.get(url=('http://info.ebarimt.mn/rest/merchant/info?regno=' + urlInput))
        try:
            data = json.loads(resp.text)
        except Exception as e:
            raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e.message)
        print ('data ',data)
        return data

    @api.model
    def get_merchant_tin(self, urlInput):
        """ Get metchant info from ebarimt REST api """
        resp = requests.get(url=('https://api.ebarimt.mn/api/info/check/getTinInfo?regNo=' + urlInput))
        try:
            data = json.loads(resp.text)
        except Exception as e:
            raise Warning(_('Error'), _('Could not connect to json device. \n%s') % e.message)
        return data




class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_res_company(self):
        params = super()._loader_params_res_company()
        params['search_params']['fields'].append('ebarimt_url')
        params['search_params']['fields'].append('is_ebarimt_offline')
        params['search_params']['fields'].append('is_with_ebarimt')
        
        return params


class PosConfig(models.Model):
    _inherit = 'pos.config'
    
    eb_district_code = fields.Char(string='districtCode',)
    eb_tin = fields.Char(string='merchantTin',)
    
