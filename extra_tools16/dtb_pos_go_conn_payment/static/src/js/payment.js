odoo.define('dtb_pos_go_conn_payment.payment', function (require) {
"use strict";

var core = require('web.core');
var rpc = require('web.rpc');
var PaymentInterface = require('point_of_sale.PaymentInterface');
const { Gui } = require('point_of_sale.Gui');

var _t = core._t;
var time_out_id;

var PaymentGoConn = PaymentInterface.extend({
    send_payment_request: function (cid) {
        console.log("==send_payment_request=", cid);
        this._super.apply(this, arguments);
        return this._go_conn_txn_create(cid);
    },
    send_payment_cancel: function (order, cid) {
        this._super.apply(this, arguments);
        console.log("==send_payment_cancel=", order);
        return this._go_conn_txn_cancel(order);
    },
    close: function () {
        this._super.apply(this, arguments);
    },

    set_most_recent_service_id(id) {
        this.most_recent_service_id = id;
    },
    pending_go_conn_line() {
      return this.pos.get_order().paymentlines.find(
        paymentLine => paymentLine.payment_method.use_payment_terminal === 'dtb_go_conn' && (!paymentLine.is_done()));
    },

    // ========================== CUSTOM methods ===========********************************************

    _go_conn_txn_create: function (cid) {
        var self = this;
        var order = this.pos.get_order();

        if (order.selected_paymentline.amount < 0) {
            this._show_error(_t('Cannot process transactions with negative amount.'));
            return Promise.resolve();
        }

        var line = order.paymentlines.find(paymentLine => paymentLine.cid === cid);
        line.set_payment_status('waitingCard');
        self.uiLock();
        // DATA prepare ===========================================================
        var headers = {
            "content-type": "application/json",
            // "msp_program_name": "Odoo ERP",
            "Access-Control-Allow-Origin": "*",
        }
        var db_ref_no = self.pos.pos_session.start_at.substring(0, 10).replaceAll('-','') + self.pos.pos_session.id;
        var body = {
            "service_name": "doSaleTransaction",
            "service_params": {
                "db_ref_no": db_ref_no,
                "amount": line.amount.toFixed(2),
            }
        };
        $.ajax({
            "url": "http://localhost:27028",
            "method": "POST",
            // "crossDomain": true,
            "headers": headers,
            "data": JSON.stringify(body),
            "success": function(result) {
                console.log("===result", result);
                if (result.status === true) {
                    if (result.response.response_code === "000"){
                        // To paid
                        if(line){
                            line.set_payment_status('done');
                            // Save data
                            var ret = result.response;
                            line.is_go_conn = true;
                            line.go_conn_amount = ret['amount'];
                            line.go_conn_db_ref_no = ret['db_ref_no'];
                            line.go_conn_textresponse = JSON.stringify(ret);
                            line.go_conn_resp_code = ret['response_code'];
                            line.go_conn_aid = ret['aid'];
                            line.go_conn_pan = ret['pan'];
                            line.go_conn_model = ret['model'];
                            line.go_conn_rrn = ret['rrn'];
                            line.go_conn_trace_no = ret['trace_no'];
                            line.go_conn_terminal_id = ret['terminal_id'];
                            // console.log("======paid==line", line);
                            self.uiUnLock();
                        }
                    } else {
                        // Cancelled by manual
                        var response_code = result.response.response_code;
                        var response_msg = result.response.response_msg;
                        self.uiUnLock();
                        self._show_error(_.str.sprintf(_t('Код: %s, %s'), response_code, response_msg));
                    }
                    
                } 
                else if (result.status_code === 'ng'){
                    var response_code = result.msg.code;
                    var response_msg = result.msg.body;
                    self.uiUnLock();
                    self._show_error(_.str.sprintf(_t('Код: %s, %s'), response_code, response_msg));
                }
                else {
                    var response = result.response
                    line.go_conn_textresponse = JSON.stringify(result.response);
                    var response_code = response.Exception.ErrorCode;
                    var response_msg = response.Exception.ErrorMessage;
                    self.uiUnLock();
                    self._show_error(_.str.sprintf(_t('Код: %s, %s'), response_code, response_msg));
                }
            },
            "error": function(xhr, status, error) {
                console.log("=error===", error);
                line.set_payment_status('retry');
                line.transaction_id = false;
                self.uiUnLock();
                self._show_error(_.str.sprintf(_t('Код: %s, %s'), status, error));
            },
        });
        // ======================================================================================
    },
    _go_conn_txn_cancel: function (order) {
        var self = this;
        var line = self.pending_go_conn_line()
        line.set_payment_status('retry');
        line.transaction_id = false;
    },
    uiLock: function(){
        var start_num = 30*1;
        var self = this;
        $('body').off('keypress', this.keyboard_handler);
        $('<div></div>').attr('id', 'uiLockId').css({
            'position': 'absolute',
            'top': 0,
            'left': 0,
            'z-index': 1000,
            'opacity': 0.6,
            'width':'100%',
            'height':'100%',
            'color':'white',
            'background-color':'black'
        }).html('').appendTo('body');
        
        $('<div></div>').attr('id', 'countdown_div').css({
            'position':'absolute',
            'top':'35%',
            'left':'30%',
            'width':'570px',
            'border':'3px solid #33b5e5',
            'padding':'10px',
            'overflow': 'hidden',
            'text-overflow': 'ellipsis',
            'color': 'white',
            'font-family': 'tahoma',
            'font-weight': 'bold',
            'font-size': '25px',
            'z-index': 5000,
            'opacity': 0.8,
            'background-color':'black'
        }).html('Карт унштал түр хүлээнэ үү!').appendTo('body');
    },
    uiUnLock: function(){
        $('div#uiLockId').remove();
        $('div#countdown_div').remove();
        $('body').keypress(this.keyboard_handler);
    },

    // *************************************************************************************************
    
    _show_error: function (msg, title) {
        if (!title) {
            title =  _t('Go conn Error');
        }
        Gui.showPopup('ErrorPopup',{
            'title': title,
            'body': msg,
        });
    },
});

return PaymentGoConn;
});
