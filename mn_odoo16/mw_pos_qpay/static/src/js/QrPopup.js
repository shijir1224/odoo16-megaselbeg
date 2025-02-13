odoo.define('mw_pos_qpay.QPayQrPopup', function (require) {
	'use strict';
	const {
		useState
	} = owl;
	const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
	const {
		useListener
	} = require('web.custom_hooks');
	const Registries = require('point_of_sale.Registries');
	var rpc = require('web.rpc');
	var _super_popup = AbstractAwaitablePopup.prototype;
	var core = require('web.core');
	var _t = core._t;

	class QPayQrPopup extends AbstractAwaitablePopup {
		constructor() {
			super(...arguments);
			useListener('accept-input', this.confirm);
			useListener('close-this-popup', this.cancel);
			let startingBuffer = '';
			let lines = this.env.pos.get_order().paymentlines.models;
			var is_pay = arguments[1].is_pay;
			var qpay_amt = arguments[1].due_amount;
			this.pos_order = arguments[1].pos_order;
			this.qpay_amt = qpay_amt;
			this.payment_method_line = arguments[1].payment_method_line;
			if (is_pay === true) {
				rpc.query({
					model: 'qpay.exchange',
					method: 'create_invoice',
					args: [this.env.pos.get_order().name, this.env.pos.get_order().pos.config['id'], qpay_amt],
				}).then(function (result) {
					if (result) {
						$("#invoice_id").attr('value', result['invoice_id']);
						$(".class_qr_data").attr('src', "data:image/png;base64," + result['qr_data']);
					}
				});
			}
		}

		async checkInv() {
			var invoice_id = $("#invoice_id")[0].value;
			var self = this;
			if (invoice_id) {
				rpc.query({
					model: 'qpay.exchange',
					method: 'check_invoice',
					args: [invoice_id],
				}).then(function (result) {
					if (result['status'] == '2') {
						$(".class_inv_response_paid").text(result['msg']);
						$(".class_inv_response_unpaid").text('');
						self.confirm();
					} else {
						$(".class_inv_response_unpaid").text(result['msg']);
						$(".class_inv_response_paid").text('');
					}
				});
			}
		}

		conPopup() {
			if (confirm(_t("If you close this window, you won't be able to check whether this QR code has been paid or not. If you submit again, the QR code will be renewed!!!"))) {
				this.cancel();
			}
		}
	}

	QPayQrPopup.template = 'QPayQrPopup';
	QPayQrPopup.defaultProps = {
		confirmText: 'Ok',
		cancelText: _t('Cancel'),
		title: 'Confirm ?',
		body: '',
		cheap: false,
		startingValue: null,
		isPassword: false,
	};

	Registries.Component.add(QPayQrPopup);

	return QPayQrPopup;
});