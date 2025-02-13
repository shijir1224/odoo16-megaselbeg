/** @odoo-module **/

import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
const data = require('web.data');
var rpc = require('web.rpc');

const { mount, Component, EventBus, useState, onWillRender,onWillUpdateProps, loadFile} = owl;

// Technic Odometer
class OdometerWidget extends Component {
	setup() {
		super.setup();
		this.state = useState({ value: 0 });
	}
	increment() {
		this.state.value++;
	}
}

OdometerWidget.template = "mw_technic_equipment.OdometerWidget";
// OdometerWidget.template = owl.xml`<div class="row" style="background-color: lightblue">
// 								<div class="col-sm-12 col-lg-3">Filter 2</div>
// 								<div class="col-sm-12 col-lg-9">
// 									<button t-on-click="increment">
// 										Click Me! [<t t-esc="state.value"/>]
// 									</button>
// 								</div>
// 							</div>`;
OdometerWidget.components = { OdometerWidget };

registry.category("fields").add("odometer_widget", OdometerWidget);

// Tire Position
class TirePositionWidget extends Component {
	setup() {
		super.setup();
		this.state = useState({ value: 0 });
	}
	increment() {
		this.state.value++;
	}
}
TirePositionWidget.template = "mw_technic_equipment.TirePositionWidget";
TirePositionWidget.components = { TirePositionWidget };

registry.category("view_widgets").add("tire_position_widget", TirePositionWidget);
