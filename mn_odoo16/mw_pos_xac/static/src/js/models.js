odoo.define("mw_pos_xac.models", function (require) {

	const { register_payment_method, Payment } = require('point_of_sale.models');
	const Registries = require("point_of_sale.Registries");
	const PaymentXac = require('mw_pos_xac.payment');

	register_payment_method('xac', PaymentXac);

	const PosXacPayment = (Payment) => class PosXacPayment extends Payment {
        constructor(obj, options) {
            super(...arguments);
			this.xac_status = false;
			this.xac_textresponse = false;
			this.xac_pan = false;
			this.xac_authorizationcode = false;
			this.xac_terminalid = false;
			this.xac_merchantid = false;
			this.xac_amount = false;
			this.xac_referencenumber = false;
        }
        //@override
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.xac_status = this.xac_status;
			json.xac_textresponse = this.xac_textresponse;
			json.xac_pan = this.xac_pan;
			json.xac_authorizationcode = this.xac_authorizationcode;
			json.xac_terminalid = this.xac_terminalid;
			json.xac_merchantid = this.xac_merchantid;
			json.xac_amount = this.xac_amount;
			json.xac_referencenumber = this.xac_referencenumber;
			return json;
        }
        //@override
        // init_from_JSON(json) {
        //     super.init_from_JSON(...arguments);
        // }
    }
    Registries.Model.extend(Payment, PosXacPayment);
});