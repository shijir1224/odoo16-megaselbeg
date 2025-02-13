odoo.define("mw_pos_golomt.models", function (require) {

	const { register_payment_method, Payment } = require('point_of_sale.models');
	const Registries = require("point_of_sale.Registries");
	const Paymentgolomt = require('mw_pos_golomt.payment');

	register_payment_method('golomt', Paymentgolomt);

	const PosgolomtPayment = (Payment) => class PosgolomtPayment extends Payment {
        constructor(obj, options) {
            super(...arguments);
			this.golomt_status = false;
			this.golomt_textresponse = false;
			this.golomt_pan = false;
			this.golomt_authorizationcode = false;
			this.golomt_terminalid = false;
			this.golomt_merchantid = false;
			this.golomt_amount = false;
			this.golomt_referencenumber = false;
        }
        //@override
        export_as_JSON() {
            const json = super.export_as_JSON(...arguments);
            json.golomt_status = this.golomt_status;
			json.golomt_textresponse = this.golomt_textresponse;
			json.golomt_pan = this.golomt_pan;
			json.golomt_authorizationcode = this.golomt_authorizationcode;
			json.golomt_terminalid = this.golomt_terminalid;
			json.golomt_merchantid = this.golomt_merchantid;
			json.golomt_amount = this.golomt_amount;
			json.golomt_referencenumber = this.golomt_referencenumber;
			return json;
        }
        //@override
        // init_from_JSON(json) {
        //     super.init_from_JSON(...arguments);
        // }
    }
    Registries.Model.extend(Payment, PosgolomtPayment);
});