odoo.define("mw_pos_qpay.models", function (require) {

	var models = require("point_of_sale.models");
	const Registries = require("point_of_sale.Registries");

	var PaymentQpay = require("mw_pos_qpay.payment");
	models.register_payment_method("qpay", PaymentQpay);
});