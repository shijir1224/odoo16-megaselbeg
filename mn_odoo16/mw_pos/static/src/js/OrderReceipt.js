odoo.define('mw_pos.OrderReceipt', function (require) {
	'use strict';

	const OrderReceipt = require('point_of_sale.OrderReceipt');
	const Registries = require('point_of_sale.Registries');

	const EBarimtOrderReceipt = OrderReceipt => class extends OrderReceipt {
		get receiptEnv() {
			let receipt_render_env = super.receiptEnv;
			let order = this.env.pos.get_order();
			receipt_render_env.receipt.bill_type = order.bill_type;
			//            console.log("-this.env.pos.pos_session", this.env.pos.pos_session)
			//            receipt_render_env.receipt.day_order_no = this.env.pos.pos_session.last_order_no;
			return receipt_render_env;
		}
	}

	Registries.Component.extend(OrderReceipt, EBarimtOrderReceipt);

	return OrderReceipt;
});