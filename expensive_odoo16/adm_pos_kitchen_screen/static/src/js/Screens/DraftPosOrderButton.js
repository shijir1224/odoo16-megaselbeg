odoo.define('wr_draft_pos_order.DraftPosOrderButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require("@web/core/utils/hooks");
    const Registries = require('point_of_sale.Registries');

    const { ConnectionLostError, ConnectionAbortedError } = require('@web/core/network/rpc_service')
    const { identifyError } = require('point_of_sale.utils');
    const { useState } = owl;

    class DraftPosOrderButton extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick() {
            /* const { confirmed } = await this.showPopup('ConfirmPopup', {
                title: this.env._t('Send To Kitchen?'),
                body: this.env._t('Are you sure you want to create a draft pos order?'),
            });
            if(confirmed){ */
            var orders = [{
                id: this.env.pos.get_order().export_as_JSON().uid,
                data: this.env.pos.get_order().export_as_JSON()
            }];
            var timeout = orders.length;
            var syncOrderResult = await this.env.services.rpc({
                model: 'pos.order',
                method: 'create_from_ui',
                args: [orders, {'draft': true}],
                kwargs: {context: this.env.session.user_context},
            }, {
                timeout: timeout,
                shadow: true
            });
            if (syncOrderResult.length > 0) {
                this.showNotification("Order " + syncOrderResult[0].pos_reference + " sent to Kitchen", 5000);
            }
        }
    }
    DraftPosOrderButton.template = 'DraftPosOrderButton';

    ProductScreen.addControlButton({
        component: DraftPosOrderButton,
        condition: function () {
            return this.env.pos.config.iface_allow_to_create_draft_order;
        },
    });

    Registries.Component.add(DraftPosOrderButton);

    return DraftPosOrderButton;
});
