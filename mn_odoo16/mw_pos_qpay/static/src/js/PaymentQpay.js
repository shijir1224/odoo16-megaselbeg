odoo.define("mw_pos_qpay.payment", function (require) {
	"use strict";

	var core = require("web.core");
	var PaymentInterface = require("point_of_sale.PaymentInterface");
	const {
		Gui
	} = require("point_of_sale.Gui");
	var framework = require('web.framework');
	var _t = core._t;

	var PaymentQpay = PaymentInterface.extend({
		init: function () {
			this._super.apply(this, arguments);
		},

		send_payment_request: function () {
			this._super.apply(this, arguments);
			return this._qpay_payment_pay();
		},

		send_payment_cancel: function () {
			this._super.apply(this, arguments);
			this._show_error(_t("Please press the red button on the payment qpay to cancel the transaction."));
			return Promise.reject();
		},

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
				console.log("+++++++++++++++++ qpay result +++++++++++++++++++")
				console.log(result)
				if (result.confirmed == false) {
					pay_line.set_payment_status("waitingCard");
					return false;
				} else {
					console.log("Qpay Payment success.................")
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
		},

		_show_error: function (msg, title) {
			Gui.showPopup("ErrorPopup", {
				title: title || _t("Payment QPay Error"),
				body: msg,
			});
		},
	});
	return PaymentQpay;
});