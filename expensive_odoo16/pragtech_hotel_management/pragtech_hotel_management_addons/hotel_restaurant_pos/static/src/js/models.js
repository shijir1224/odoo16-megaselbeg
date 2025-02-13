odoo.define('hotel_restaurant_pos.models', function (require) {
	"use strict";
//
	const { PosGlobalState, Order } = require('point_of_sale.models');
	const Registries = require('point_of_sale.Registries');

	const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
		async _processData(loadedData) {
			await super._processData(loadedData);
			this.hotel_folio = loadedData['hotel.folio'];
			this.hotel_room_book_history = loadedData['hotel.room.booking.history'];
			this.sale_shop = loadedData['sale.shop'];
			this.hotel_rest_table = loadedData['hotel.restaurant.tables'];
			this.hotel_rest_kitchen = loadedData['hotel.restaurant.kitchen.order.tickets'];
			this.hotel_rest_reserve = loadedData['hotel.restaurant.reservation'];
			this.hotel_reserve = loadedData['hotel.reservation'];
			this.hotel_folio_line_ = loadedData['hotel_folio.line'];
			console.log(".......................................Models Loaded.......................................")
			console.log(this.hotel_folio)
			console.log(this.hotel_room_book_history)
			console.log(this.sale_shop)
			console.log(this.hotel_rest_table)
			console.log(this.hotel_rest_kitchen)
			console.log(this.hotel_rest_reserve)
			console.log(this.hotel_reserve)
			console.log(this.hotel_folio_line_)

		}

	}
	const NewPosOrder = (Order) => class NewPosOrder extends Order {
		constructor(obj, options) {
			super(...arguments);
			this.folio_line_id = this.folio_line_id || false;
			this.folio_ids = this.folio_ids || false;
			this.room_name = this.room_name || false;
			// this.env = this.get('env');
		}
		set_folio_line_id(folio) {
			this.folio_line_id = folio;
		}
		get_folio_line_id() {
			return this.folio_line_id;
		}

		set_folio_ids(folio_id) {
			this.folio_ids = folio_id;
		}
		get_folio_ids() {
			return this.folio_ids;
		}

		set_room_name(room) {
			this.room_name = room;
		}
		get_room_name() {
			return this.room_name;
		}

		init_from_JSON(json) {
			super.init_from_JSON(...arguments);
			this.folio_line_id = json.folio_line_id;
			this.folio_ids = json.folio_ids;
			this.room_name = json.room_name;
		}

		export_as_JSON() {
			let orderJson = super.export_as_JSON(...arguments);
			orderJson.folio_line_id = this.get_folio_line_id();
			orderJson.folio_ids = this.get_folio_ids();
			orderJson.room_name = this.get_room_name();
			return orderJson;
		}

		export_for_printing() {
			let Json = super.export_for_printing(...arguments);
			Json.folio_line_id = this.get_folio_line_id();
			Json.folio_ids = this.get_folio_ids();
			Json.room_name = this.get_room_name();
			return Json;
		}
	}

	Registries.Model.extend(PosGlobalState,NewPosGlobalState);
	Registries.Model.extend(Order, NewPosOrder);
	});
	

