odoo.define('mw_pos_qpay.PaymentScreen', function (require) {
	'use strict';

	const PaymentScreen = require('point_of_sale.PaymentScreen');
	const Registries = require('point_of_sale.Registries');
	const {
		useState
	} = owl;

	const QPayPaymentScreen = PaymentScreen => class extends PaymentScreen {
		async scanQR() {
			let value = 0.0
			const {
				confirmed,
				payload
			} = await this.showPopup('QPayQrPopup', {
				title: this.env._t('Scan QR'),
				startingValue: value,
			});
		}
	}

	Registries.Component.extend(PaymentScreen, QPayPaymentScreen);

	return PaymentScreen;
});