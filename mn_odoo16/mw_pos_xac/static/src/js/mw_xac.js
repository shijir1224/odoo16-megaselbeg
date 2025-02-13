odoo.define('mw_pos_xac.mw_xac', function (require) {
"use strict";
var screens = require('point_of_sale.screens');
var PaymentScreenWidget = screens.PaymentScreenWidget;
var PopupWidget = require('point_of_sale.popups');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var chrome = require('point_of_sale.chrome');
var gui = require('point_of_sale.gui');
var rpc = require('web.rpc');
var models = require('point_of_sale.models');
var _super_paymentline = models.Paymentline.prototype;
models.load_fields('pos.payment.method',['xac_ok']);

var AgainXacPopupWidget = PopupWidget.extend({
    template: 'AgainXacPopupWidget',
});
gui.define_popup({name:'againxac', widget: AgainXacPopupWidget});

models.Paymentline = models.Paymentline.extend({    
    initialize: function() {
        _super_paymentline.initialize.apply(this,arguments);
        this.xac_status = false;
        this.xac_textresponse = false;
        this.xac_pan = false;
        this.xac_authorizationcode = false;
        this.xac_terminalid = false;
        this.xac_merchantid = false;
        this.xac_amount = false;
        this.xac_referencenumber = false;
    },
    export_as_JSON: function() {
        var json = _super_paymentline.export_as_JSON.apply(this,arguments);
        json.xac_status = this.xac_status;
        json.xac_textresponse = this.xac_textresponse;
        json.xac_pan = this.xac_pan;
        json.xac_authorizationcode = this.xac_authorizationcode;
        json.xac_terminalid = this.xac_terminalid;
        json.xac_merchantid = this.xac_merchantid;
        json.xac_amount = this.xac_amount;
        json.xac_referencenumber = this.xac_referencenumber;
        return json;
    },
});

// END XAC POS 
PaymentScreenWidget.include({
    // START XAC POS 
    get_db_ref_no: function(paid_line){
        var order = this.pos.get_order();
        console.log('paid_line',paid_line)
        var order_name = order.name
        // +paid_line.id.toString();
        // order_name = order_name.split(' ')[1]
        order_name = order_name.replace('-', '');
        order_name = order_name.replace('-', '');
        // order_name = parseInt(order_name)+100000000000;
        return order_name.toString();
    },
    get_xac_ok_unpaid_payment: function(){
        var order = this.pos.get_order();
        var plines = order.get_paymentlines();
        var sum_bank_amount = 0;
        for (var i = 0; i < plines.length; i++) {
            if (!plines[i].xac_paid_ok && plines[i].payment_method.xac_ok) {
                return {'unpaid_amount':plines[i].amount, 'pline':plines[i]}
            }
        }
        return false;
    },
    get_xac_ok_payment: function(){
        var order = this.pos.get_order();
        var plines = order.get_paymentlines();
        for (var i = 0; i < plines.length; i++) {
            if (plines[i].payment_method.xac_ok && this.pos.config.xac_ok) {
                return true;
            }
        }
        return false;
    },
    b64DecodeUnicode: function( str ) {
        return decodeURIComponent(escape(window.atob( str )));;
    },
    click_xac_sent: function(sum_bank_amount, paid_line){
        var self = this;
        var order = this.pos.get_order();
        // if (!order.xac_db_ref_no || isNaN(order.xac_db_ref_no)){
        //     order.xac_db_ref_no = self.get_db_ref_no(paid_line);
        // }
        var send_amount = sum_bank_amount;
        // .toFixed(2).toString();
        var data = order.get_xac_data("Sale", send_amount, order.name);
        // var main_data = Base64.btoa(data_dict2);
        // var data = main_data;
        this.uiLock();
        var settings = order.get_xac_settings(data);
        console.log('xac settings',settings);
        $.ajax(settings).done(function (response) { 
            var result = response;
            console.log('xac -res ',result);
            if (result.status=='200'){

                var res_data = result.ecrResult;
                paid_line.xac_status = result.status;
                paid_line.xac_textresponse = res_data.RespCode + ' '+ res_data.HostRespCode;
                paid_line.xac_pan = res_data.AID;
                paid_line.xac_authorizationcode = res_data.ECRRefNo;
                paid_line.xac_terminalid = res_data.TerminalID;
                paid_line.xac_merchantid = res_data.MerchantID;
                paid_line.xac_amount = res_data.TransAmount;
                paid_line.xac_referencenumber = res_data.TraceNumber;
                
                
                paid_line.xac_paid_ok = true;
                order.is_xac_ok_payment = true;
                if (!order.xac_paymentlines || order.xac_paymentlines==undefined){
                    order.xac_paymentlines = [];
                }
                order.xac_paymentlines.push(paid_line);
                var unpaid = self.get_xac_ok_unpaid_payment();
                if (unpaid){
                    self.click_xac_sent(unpaid.unpaid_amount, unpaid.pline);
                }else{
                    self.uiUnLock();
                    self.$('.js_set_xac').addClass('highlight');
                    self.$('.js_set_xac').addClass('disabled');
                    self.validate_order();
                }
            }else{
                paid_line.xac_paid_ok = false;
                order.is_xac_ok_payment = false;
                order.xac_paymentlines = [];
                var error_code = '';
                var error_msg = '';
                if (result.responseCode){
                    error_code = result.responseCode;
                    error_msg = result.responseDesc;
                }else if (result.Exception){
                    error_code = result.Exception.ErrorCode;
                    error_msg = result.Exception.ErrorMessage;
                }
                self.uiUnLock();
                self.gui.show_popup('againxac',{
                    'title': 'Xac Гүйлгээний Алдааны код ['+error_code+'] Дахин Xac-д илгээх бол дарна уу',
                    'body': error_msg,
                    confirm: function(){
                        self.click_xac_sent(sum_bank_amount, paid_line);
                    },
                });    
            }
        }).fail(function (result) { 
            console.log('faile',result);
            paid_line.xac_paid_ok = false;
            order.is_xac_ok_payment = false;
            order.xac_paymentlines = [];
            var error_code = '';
            var error_msg = '';
            if (result.status && result.responseJSON.error){
                error_code = result.status;
                error_msg = result.responseJSON.error;
            }
            self.uiUnLock();
            self.gui.show_popup('againxac',{
                'title': 'Xac Гүйлгээний Алдааны код ['+error_code+'] Дахин Xac-д илгээх бол дарна уу',
                'body': error_msg,
                confirm: function(){
                    self.click_xac_sent(sum_bank_amount, paid_line);
                },
            });
            
        });
    },
    validate_order: function(force_validation) {
        var self = this;
        console.log('ugandaaaaa-++++++++++++++');
        var xac_ok = this.get_xac_ok_payment();
        if (xac_ok){
            var unpaid = self.get_xac_ok_unpaid_payment();
            if (unpaid){
                self.click_xac_sent(unpaid.unpaid_amount, unpaid.pline);
            }else{
                this._super();
            }
        }else{
            this._super();
        }
    },
});

var GetdoSettlementXac = PosBaseWidget.extend({
    template: 'GetdoSettlementXac',
    init: function(parent, options){
        options = options || {};
        this._super(parent,options);
    },
    b64DecodeUnicode: function( str ) {
        return decodeURIComponent(escape(window.atob( str )));;
    },
    renderElement: function(){
        var self = this;
        var order = this.pos.get_order();
        this._super();
        this.$el.click(function(){
            var list = [
                {
                    'label': '1. ӨДӨР ӨНДӨРЛӨХ',
                    'item': 'udur',
                },
                {
                    'label': '2. Буцаалт хийх',
                    'item': 'butsaalt',
                },
            ];
            self.pos.gui.show_popup('selection',{
                title:   'Өдөр Өндөрлөх эсвэл Буцаалт',
                list:    list,
                confirm: function (item) {
                    if (item=='udur'){
                        // var db_ref_no = self.pos.pos_session.id+Math.floor((Math.random() * 100) + 1);
                        var data = order.get_xac_data("Settlement", false, "");
                        var settings = order.get_xac_settings(data);
                        console.log('xac udur', settings);
                        $.ajax(settings).done(function (response) { 
                            var result = response;
                            console.log('result',result);
                            if (result.status=='200'){
                                // var res_data = result.ecrResult;
                                // if (res_data.status=='1'){
                                var reciept_data = result.ecrResult.toString();
                                rpc.query({
                                    model: 'pos.session',
                                    method: 'update_xac_udur_undurluh',
                                    args: [self.pos.pos_session.id, reciept_data],
                                }).then(function(result_res){
                                            console.log('Save epos result',result_res);
                                },function(err,event){
                                    console.log(err,' Epos Settlement save Server down hiisen bna');
                                    event.preventDefault(); 
                                });
                                self.pos.gui.show_popup('alert', {
                                    title: 'Хас Өдөр Өндөрлөх амжилттай',
                                    body: reciept_data,
                                });
                            }else{
                                var error_code = '';
                                var error_msg = '';
                                if (result.ecrResult){
                                    error_msg = result.ecrResult;
                                }
                                if (result.status){
                                    error_code = result.status;
                                }
                                self.gui.show_popup('error',{
                                    'title': '!!!! Хас Өдөр Өндөрлөх Амжилтгүй ['+error_code+'] !!!!',
                                    'body':  error_msg,
                                }); 
                            }
                        }).fail(function (result) { 
                            console.log('reject',result);
                            var error_code = '';
                            var error_msg = '';
                            if (result.status && result.responseJSON.error){
                                error_code = result.status;
                                error_msg = result.responseJSON.error;
                            }
                            self.gui.show_popup('error',{
                                'title': '!!!! Хас Өдөр Өндөрлөх Амжилтгүй !!!!',
                                'body':  error_code+' '+error_msg,
                            });
                        });
                    }
                    else if (item=='butsaalt'){
                        console.log('----------');
                        self.pos.gui.show_popup('number', {
                            'title':  'Буцаах дүнгээ оруулна уу',
                            'cheap': true,
                            'value': 100,
                            'confirm': function(value) {
                                value = Number(value);
                                var send_amount = value;
                                var data = order.get_xac_data("Refund", send_amount);
                                var settings = order.get_xac_settings(data);
                                $.ajax(settings).done(function (response) { 
                                    var result = response;
                                    if (result.status=='200'){
                                        var reciept_data = result.ecrResult.toString();
                                        console.log('reciept_data',reciept_data);
                                        console.log('resultresult',result);
                                        self.pos.gui.show_popup('alert', {
                                            title: 'Хас Буцаалт амжилттай',
                                            body: reciept_data,
                                        });
                                    }else{
                                        var error_code = '';
                                        var error_msg = '';
                                        if (result.ecrResult){
                                            error_msg = result.ecrResult;
                                        }
                                        if (result.status){
                                            error_code = result.status;
                                        }
                                        self.gui.show_popup('error',{
                                            'title': '!!!! Хас Буцаалт Амжилтгүй ['+error_code+'] !!!!',
                                            'body':  error_msg,
                                        }); 
                                    }
                                }).fail(function (result) { 
                                    console.log('reject',result);
                                    var error_code = '';
                                    var error_msg = '';
                                    if (result.status && result.responseJSON.error){
                                        error_code = result.status;
                                        error_msg = result.responseJSON.error;
                                    }
                                    self.gui.show_popup('error',{
                                        'title': '!!!! Хас Буцаалт Амжилтгүй !!!!',
                                        'body':  error_code+' '+error_msg,
                                    });
                                });
                            },
                        });
                    }
                },
                cancel:  '',
            });

            
        });
    },
});
    chrome.Chrome.include({
        build_widgets: function () {
            // add blackbox id widget to left of proxy widget
            var proxy_status_index = _.findIndex(this.widgets, function (widget) {
                return widget.name === "username";
            });
            this.widgets.splice(proxy_status_index, 0, {
                'name': 'getdosettlement_xac',
                'widget': GetdoSettlementXac,
                'append': '.pos-rightheader',
            });
            this._super();
        },
    });
});