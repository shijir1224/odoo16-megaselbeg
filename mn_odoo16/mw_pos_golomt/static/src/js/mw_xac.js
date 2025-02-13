odoo.define('mw_pos_golomt.mw_golomt', function (require) {
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
models.load_fields('pos.payment.method',['golomt_ok']);

var AgaingolomtPopupWidget = PopupWidget.extend({
    template: 'AgaingolomtPopupWidget',
});
gui.define_popup({name:'againgolomt', widget: AgaingolomtPopupWidget});

models.Paymentline = models.Paymentline.extend({    
    initialize: function() {
        _super_paymentline.initialize.apply(this,arguments);
        this.golomt_status = false;
        this.golomt_textresponse = false;
        this.golomt_pan = false;
        this.golomt_authorizationcode = false;
        this.golomt_terminalid = false;
        this.golomt_merchantid = false;
        this.golomt_amount = false;
        this.golomt_referencenumber = false;
    },
    export_as_JSON: function() {
        var json = _super_paymentline.export_as_JSON.apply(this,arguments);
        json.golomt_status = this.golomt_status;
        json.golomt_textresponse = this.golomt_textresponse;
        json.golomt_pan = this.golomt_pan;
        json.golomt_authorizationcode = this.golomt_authorizationcode;
        json.golomt_terminalid = this.golomt_terminalid;
        json.golomt_merchantid = this.golomt_merchantid;
        json.golomt_amount = this.golomt_amount;
        json.golomt_referencenumber = this.golomt_referencenumber;
        return json;
    },
});

// END golomt POS 
PaymentScreenWidget.include({
    // START golomt POS 
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
    get_golomt_ok_unpaid_payment: function(){
        var order = this.pos.get_order();
        var plines = order.get_paymentlines();
        var sum_bank_amount = 0;
        for (var i = 0; i < plines.length; i++) {
            if (!plines[i].golomt_paid_ok && plines[i].payment_method.golomt_ok) {
                return {'unpaid_amount':plines[i].amount, 'pline':plines[i]}
            }
        }
        return false;
    },
    get_golomt_ok_payment: function(){
        var order = this.pos.get_order();
        var plines = order.get_paymentlines();
        for (var i = 0; i < plines.length; i++) {
            if (plines[i].payment_method.golomt_ok && this.pos.config.golomt_ok) {
                return true;
            }
        }
        return false;
    },
    b64DecodeUnicode: function( str ) {
        return decodeURIComponent(escape(window.atob( str )));;
    },
    click_golomt_sent: function(sum_bank_amount, paid_line){
        var self = this;
        var order = this.pos.get_order();
        // if (!order.golomt_db_ref_no || isNaN(order.golomt_db_ref_no)){
        //     order.golomt_db_ref_no = self.get_db_ref_no(paid_line);
        // }
        var send_amount = sum_bank_amount;
        // .toFixed(2).toString();
        var data = order.get_golomt_data("Sale", send_amount, order.name);
        // var main_data = Base64.btoa(data_dict2);
        // var data = main_data;
        this.uiLock();
        var settings = order.get_golomt_settings(data);
        console.log('golomt settings',settings);
        $.ajax(settings).done(function (response) { 
            var result = response;
            console.log('golomt -res ',result);
            if (result.status=='200'){

                var res_data = result.ecrResult;
                paid_line.golomt_status = result.status;
                paid_line.golomt_textresponse = res_data.RespCode + ' '+ res_data.HostRespCode;
                paid_line.golomt_pan = res_data.AID;
                paid_line.golomt_authorizationcode = res_data.ECRRefNo;
                paid_line.golomt_terminalid = res_data.TerminalID;
                paid_line.golomt_merchantid = res_data.MerchantID;
                paid_line.golomt_amount = res_data.TransAmount;
                paid_line.golomt_referencenumber = res_data.TraceNumber;
                
                
                paid_line.golomt_paid_ok = true;
                order.is_golomt_ok_payment = true;
                if (!order.golomt_paymentlines || order.golomt_paymentlines==undefined){
                    order.golomt_paymentlines = [];
                }
                order.golomt_paymentlines.push(paid_line);
                var unpaid = self.get_golomt_ok_unpaid_payment();
                if (unpaid){
                    self.click_golomt_sent(unpaid.unpaid_amount, unpaid.pline);
                }else{
                    self.uiUnLock();
                    self.$('.js_set_golomt').addClass('highlight');
                    self.$('.js_set_golomt').addClass('disabled');
                    self.validate_order();
                }
            }else{
                paid_line.golomt_paid_ok = false;
                order.is_golomt_ok_payment = false;
                order.golomt_paymentlines = [];
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
                self.gui.show_popup('againgolomt',{
                    'title': 'golomt Гүйлгээний Алдааны код ['+error_code+'] Дахин golomt-д илгээх бол дарна уу',
                    'body': error_msg,
                    confirm: function(){
                        self.click_golomt_sent(sum_bank_amount, paid_line);
                    },
                });    
            }
        }).fail(function (result) { 
            console.log('faile',result);
            paid_line.golomt_paid_ok = false;
            order.is_golomt_ok_payment = false;
            order.golomt_paymentlines = [];
            var error_code = '';
            var error_msg = '';
            if (result.status && result.responseJSON.error){
                error_code = result.status;
                error_msg = result.responseJSON.error;
            }
            self.uiUnLock();
            self.gui.show_popup('againgolomt',{
                'title': 'golomt Гүйлгээний Алдааны код ['+error_code+'] Дахин golomt-д илгээх бол дарна уу',
                'body': error_msg,
                confirm: function(){
                    self.click_golomt_sent(sum_bank_amount, paid_line);
                },
            });
            
        });
    },
    validate_order: function(force_validation) {
        var self = this;
        console.log('ugandaaaaa-++++++++++++++');
        var golomt_ok = this.get_golomt_ok_payment();
        if (golomt_ok){
            var unpaid = self.get_golomt_ok_unpaid_payment();
            if (unpaid){
                self.click_golomt_sent(unpaid.unpaid_amount, unpaid.pline);
            }else{
                this._super();
            }
        }else{
            this._super();
        }
    },
});

var GetdoSettlementgolomt = PosBaseWidget.extend({
    template: 'GetdoSettlementgolomt',
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
                        var data = order.get_golomt_data("Settlement", false, "");
                        var settings = order.get_golomt_settings(data);
                        console.log('golomt udur', settings);
                        $.ajax(settings).done(function (response) { 
                            var result = response;
                            console.log('result',result);
                            if (result.status=='200'){
                                // var res_data = result.ecrResult;
                                // if (res_data.status=='1'){
                                var reciept_data = result.ecrResult.toString();
                                rpc.query({
                                    model: 'pos.session',
                                    method: 'update_golomt_udur_undurluh',
                                    args: [self.pos.pos_session.id, reciept_data],
                                }).then(function(result_res){
                                            console.log('Save epos result',result_res);
                                },function(err,event){
                                    console.log(err,' Epos Settlement save Server down hiisen bna');
                                    event.preventDefault(); 
                                });
                                self.pos.gui.show_popup('alert', {
                                    title: 'Голомт Өдөр Өндөрлөх амжилттай',
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
                                    'title': '!!!! Голомт Өдөр Өндөрлөх Амжилтгүй ['+error_code+'] !!!!',
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
                                'title': '!!!! Голомт Өдөр Өндөрлөх Амжилтгүй !!!!',
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
                                var data = order.get_golomt_data("Refund", send_amount);
                                var settings = order.get_golomt_settings(data);
                                $.ajax(settings).done(function (response) { 
                                    var result = response;
                                    if (result.status=='200'){
                                        var reciept_data = result.ecrResult.toString();
                                        console.log('reciept_data',reciept_data);
                                        console.log('resultresult',result);
                                        self.pos.gui.show_popup('alert', {
                                            title: 'Голомт Буцаалт амжилттай',
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
                                            'title': '!!!! Голомт Буцаалт Амжилтгүй ['+error_code+'] !!!!',
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
                                        'title': '!!!! Голомт Буцаалт Амжилтгүй !!!!',
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
                'name': 'getdosettlement_golomt',
                'widget': GetdoSettlementgolomt,
                'append': '.pos-rightheader',
            });
            this._super();
        },
    });
});