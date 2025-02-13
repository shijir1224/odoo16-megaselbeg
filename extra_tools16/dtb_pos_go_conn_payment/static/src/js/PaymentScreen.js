odoo.define('dtb_pos_go_conn_payment.PaymentScreen', function(require) {
    "use strict";

    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const { onMounted } = owl;

    const PosGoConnPaymentScreen = PaymentScreen => class extends PaymentScreen {
        setup() {
        super.setup();
            onMounted(() => {
                const pendingPaymentLine = this.currentOrder.paymentlines.find(
                    paymentLine => paymentLine.payment_method.use_payment_terminal === 'dtb_go_conn' &&
                        (!paymentLine.is_done() && paymentLine.get_payment_status() !== 'pending')
                );
                if (pendingPaymentLine) {
                    // console.log("====Go conn payment line: ", pendingPaymentLine);
                    const paymentTerminal = pendingPaymentLine.payment_method.payment_terminal;
                    paymentTerminal.set_most_recent_service_id(pendingPaymentLine.terminalServiceId);
                    pendingPaymentLine.set_payment_status('retry');
                    pendingPaymentLine.can_be_reversed = false;
                }
            });
        }
    };

    Registries.Component.extend(PaymentScreen, PosGoConnPaymentScreen);

    return PaymentScreen;
});
