odoo.define("mw_pos_golomt.payment", function (require) {
	"use strict";

	var core = require("web.core");
	var PaymentInterface = require("point_of_sale.PaymentInterface");
	const {
		Gui
	} = require("point_of_sale.Gui");
	var framework = require('web.framework');
	var _t = core._t;

	var Paymentgolomt = PaymentInterface.extend({
		init: function () {
			this._super.apply(this, arguments);
		},

		get_golomt_ok_payment: async function(cid){
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
			var db_ref_no = self.pos.pos_session.start_at.substring(0, 10).replaceAll('-','') + self.pos.pos_session.id;
			
			$.ajax({
				"url": "http://127.0.0.1:8088/ecrt1000/",
				"method": "POST",
				"timeout": 0,
				// "crossDomain": true,
				"headers": {
					"Content-Type": "application/x-www-form-urlencoded"
				},
				"data": {
					"ecrRefNo": db_ref_no,
					"operation": "Sale",
					"amount": line.amount.toFixed(2)
				},
				"success": function(result) {
					console.log("===result", result);
					console.log("===result.status", result.status);
					if (result.status === 200) {
						if (result.ecrResult.HostRespCode === '00') {
							// To paid
							if(line){
								line.set_payment_status('done');
								// Save data
								var res_data = result.ecrResult;
								line.golomt_status = result.status;
								line.golomt_textresponse = res_data.RespCode + ' '+ res_data.HostRespCode;
								line.golomt_pan = res_data.PAN;
								line.golomt_authorizationcode = res_data.ECRRefNo;
								line.golomt_terminalid = res_data.TerminalID;
								line.golomt_merchantid = res_data.MerchantName;
								line.golomt_amount = res_data.TransAmount;
								line.golomt_referencenumber = res_data.TraceNumber;
								
								console.log('result.ecrResult', result.ecrResult);
								line.golomt_paid_ok = true;
								order.is_golomt_ok_payment = true;
								if (!order.golomt_paymentlines || order.golomt_paymentlines==undefined){
									order.golomt_paymentlines = [];
								}
								order.golomt_paymentlines.push(line);
								var unpaid = self.get_golomt_ok_unpaid_payment();
								if (unpaid){
									self.click_golomt_sent(unpaid.unpaid_amount, unpaid.pline);
								}else{
									self.uiUnLock();
									// self.$('.js_set_golomt').addClass('highlight');
									// self.$('.js_set_golomt').addClass('disabled');
									// self.validate_order();
								}
								self.uiUnLock();
							}
						} else {
							var response_code = result.ecrResult.HostRespCode;
							var response_msg = result.ecrResult.RespCode;
							self.uiUnLock();
							self._show_error(_.str.sprintf(_t('Код: %s, %s'), response_code, response_msg));
						}
						
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
						// self.$('.js_set_golomt').addClass('highlight');
						// self.$('.js_set_golomt').addClass('disabled');
						// self.validate_order();
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
		send_payment_request: function (cid) {
			this._super.apply(this, arguments);
			console.log('aaa');
			// return this._qpay_payment_pay();

			// 
			var self = this;
			var golomt_ok = this.get_golomt_ok_payment(cid);
			console.log('ugandaaaaa-++++++++++++++', golomt_ok);
			if (golomt_ok){
				var unpaid = this.get_golomt_ok_unpaid_payment();
				if (unpaid){
					self.click_golomt_sent(unpaid.unpaid_amount, unpaid.pline);
				}else{
					this._super();
				}
			}else{
				this._super();
			}
		},

		send_payment_cancel: function () {
			this._super.apply(this, arguments);
			this._show_error(_t("Please press the red button on the payment qpay to cancel the transaction."));
			return Promise.reject();
		},

		// click_golomt_sent: function () {
		// 	return this;
		// },

		_qpay_payment_pay: function () {
			var order = this.pos.get_order();
			var pay_line = order.selected_paymentline;
			var currency = this.pos.currency;
			if (pay_line.amount <= 0) {
				// TODO check if it's possible or not
				this._show_error(_t("Cannot process transactions with zero or negative amount."));
				return Promise.resolve();
			}
			return this._qpay_payment_request(pay_line, pay_line.amount).then((result) => {
				console.log("+++++++++++++++++ golomt result +++++++++++++++++++")
				console.log(result)
				if (result.confirmed == false) {
					pay_line.set_payment_status("waitingCard");
					return false;
				} else {
					console.log("golomt Payment success.................")
					pay_line.card_type = 'qpay';
					return true;
				}
				pay_line.set_payment_status("force_done");
				return Promise.reject();
			});
		},

		_qpay_payment_request: function (line, amount) {
			return Gui.showPopup('QPayQrPopup', {
				title: _t('Scan QR'),
				startingValue: amount,
				due_amount: amount,
				is_pay: true,
				pos_order: this,
				payment_method_line: line,
			}).then((result) => {
				return result;
			}).catch(async (error) => {
				console.error("Error starting payment transaction");
				return false;
			});
			console.log()
		},

		_show_error: function (msg, title) {
			if (!title) {
				title =  _t('Go conn Error');
			}
			Gui.showPopup("ErrorPopup", {
				title: title || _t("Payment golomt Error"),
				body: msg,
			});
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
	});
	return Paymentgolomt;
});


// Success transaction golomt body
// {
//     "status": 200,
//     "error": "",
//     "operation": "Sale",
//     "ecrResult": {
//         "ATC": "261",
//         "CardHolderName": "BADMAARAG    /TSEVEGJAV   ",
//         "EntryMode": "C",
//         "TC": "D5 CD D4 11 1C 8E 67 E4 ",
//         "TransAmount": 10.0,
//         "AppName": "VISA DEBIT",
//         "AuthCode": "9EY4ZS",
//         "BatchNo": "00 00 02 ",
//         "PAN": "438054******2284",
//         "IssuerName": "VISA CARD",
//         "CardType": "02",
//         "ExpiryDate": "2704",
//         "MerchantName": "THE MAKER CAFE",
//         "RRN": "001010863108",
//         "HostRespCode": "00",
//         "RespCode": "[ 00 ] Гүйлгээ амжилттай",
//         "TerminalID": "44217791",
//         "TraceNumber": "000035",
//         "Date": "0321",
//         "Time": "140040",
//         "ECRRefNo": "0000000000000asd"
//     },
//     "errors": {},
//     "parameters": {
//         "amount": "10",
//         "ecrRefNo": "asd"
//     }
// }