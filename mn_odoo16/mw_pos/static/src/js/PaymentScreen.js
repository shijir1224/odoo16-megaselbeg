odoo.define('mw_pos.PaymentScreen', function (require) {
	'use strict';

	const PaymentScreen = require('point_of_sale.PaymentScreen');
	const Registries = require('point_of_sale.Registries');
	const {
		useState
	} = owl;

	const EBarimtPaymentScreen = PaymentScreen => class extends PaymentScreen {
		constructor() {
			super(...arguments);
			this.state = useState({
				bill_type: null,
				utga: null
			});
		}

		async _isOrderValid() {
			this.currentOrder.bill_type = this.state.bill_type;
			this.currentOrder.utga = document.getElementById("utga").value;
			if (this.currentOrder.bill_type === '5' && !this.currentOrder.get_client()) {
				const {
					confirmed
				} = await this.showPopup('ConfirmPopup', {
					'title': this.env._t('Please select the Customer'),
					'body': this.env._t('You need to select the customer before you can validate an order.'),
				});
				if (confirmed) {
					this.selectClient();
				}
				return false;
			} else {
				return super._isOrderValid();
			}
		}

		toggleIsToInvoice() {
			super.toggleIsToInvoice();
			if (this.currentOrder.is_to_invoice() && this.currentOrder.bill_type !== '5') {
				this.currentOrder.bill_type = '5';
			}

			if (!this.currentOrder.is_to_invoice() && this.currentOrder.bill_type === '5') {
				this.currentOrder.bill_type = '1';
			}
			this.state.bill_type = this.currentOrder.bill_type;
		}

		changeBillType(event) {
			this.currentOrder.bill_type = event.target.value;
			this.state.bill_type = this.currentOrder.bill_type;
			if (this.state.bill_type === '3') {
				$('.isCompany').show();
				$('.company-name').text('');
			} else {
				$('.isCompany').hide();
				this.currentOrder.customerReg = null;
				this.currentOrder.customerName = "";
			}
			if (this.state.bill_type === '5') {
				this.toggleIsToInvoice();
			}
		}
		async inputValueCheck() {
			var inputData = document.getElementById("register").value;
			if (inputData.length > 6) {
				var resp = inputData;
				let your_return_value = await this.rpc({
					model: 'pos.order',
					method: 'get_merchant_info',
					args: [resp],
				});
				var cast = Promise.resolve(your_return_value);
				cast.then(function (value) {
					if (value.found == false)
						alert(register.value + " регистрийн дугаартай байгууллага бүртгэлгүй байна!");
					else
						document.getElementById("company_name").innerHTML = value.name;
				});
				this.currentOrder.customerReg = inputData;
				this.currentOrder.customerName = your_return_value['name'];
			} else
				document.getElementById("company_name").innerHTML = "";
		}
	}

	Registries.Component.extend(PaymentScreen, EBarimtPaymentScreen);

	return PaymentScreen;
});