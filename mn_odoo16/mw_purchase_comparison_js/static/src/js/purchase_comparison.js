odoo.define('mw_purchase_comparison_js.PurchaseComparison', function (require) {
	'use strict';

	const Widget = require('web.Widget');
	const widgetRegistry = require('web.widget_registry');

	const PurchaseOrderComparison = Widget.extend({
		template: 'mw_purchase_comparison_js.PurchaseComparison',
	});

	widgetRegistry.add('purchase_comparison_widget', PurchaseOrderComparison);
	return PurchaseOrderComparison;
});