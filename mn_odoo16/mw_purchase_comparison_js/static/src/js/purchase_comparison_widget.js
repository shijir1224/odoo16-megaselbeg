/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

const { Component } = owl;
const rpc = require('web.rpc');

class PurchaseComparisonWidget extends Component {
	setup() {
		this.action = useService("action");
		this.rpc = useService("rpc");
		this.initData()
	}

	async saveButton() {
		var com_id = false;
		var is_refresh = false
		for (var partner of this.partners) {
			let input_key = 'input[id="{0}"]';
			var key_desc = input_key.replace("{0}", partner.description_id);
			var desc_data = $(key_desc).val();
			var key_discount = input_key.replace("{0}", partner.discount_id);
			var discount_data = $(key_discount).val();
			var key_quality = input_key.replace("{0}", partner.quality_id);
			var quality_data = $(key_quality).val();
			var key_price = input_key.replace("{0}", partner.price_id);
			var price_data = $(key_price).val();
			var key_other = input_key.replace("{0}", partner.other_id);
			var other_data = $(key_other).val();
			var key_honog = input_key.replace("{0}", partner.honog_id);
			var honog_data = $(key_honog).val();
			var key_teever_tatvar = input_key.replace("{0}", partner.teever_tatvar_id);
			var teever_tatvar_data = $(key_teever_tatvar).val();
			var key_insurance_other_expense = input_key.replace("{0}", partner.insurance_other_expense_id);
			var insurance_other_expense_data = $(key_insurance_other_expense).val();

			var partner_product_id = 0
			var product_list_data = []
			for (var product of this.products) {
				var key_price_unit = input_key.replace("{0}", product.product_id + partner.partner_id * 5);
				var price_unit = $(key_price_unit).val();
				var key_discount = input_key.replace("{0}", product.product_id + partner.partner_id * 12);
				var discount = $(key_discount).val();
				var key_vote = input_key.replace("{0}", product.product_id + partner.partner_id * 22);
				var is_vote = $(key_vote).prop('checked');
				var vals = {
					product_id: product.product_id,
					price_unit: price_unit,
					discount: discount,
					is_vote: is_vote,
				}
				product_list_data.push(vals)
			}

			var partner_vote_id = 0;
			var vote_list_data = [];
			for (var vote of this.voteUsers) {
				partner_vote_id = partner.partner_id * 12 + vote.vote_id
				var key_vote_user = input_key.replace("{0}", partner_vote_id);
				var is_user_vote = $(key_vote_user).prop('checked');
				var vals = {
					vote_id: vote.vote_id,
					is_user_vote: is_user_vote,
				}
				vote_list_data.push(vals)
			}

			// if ((quality_data > 60 || quality_data <= 0) || (price_data > 20 || price_data <= 0) || (other_data > 20 || other_data <= 0)) {
			// 	alert("Чанар 1-60, Үнэ 1-20, Бусад үзүүлэлт 1-20 хүртэлх оноо өгөх боломжтой!" + "\n\n" + partner.partner_name + " харилцагч дээрх бүртгэлийг засна уу!");
			// }
			// else {
			await rpc.query({
				model: "purchase.order.comparison",
				method: 'save_comparison_data',
				args: [partner.comparison_id, desc_data, discount_data, quality_data, price_data, other_data, honog_data, teever_tatvar_data, insurance_other_expense_data, product_list_data, vote_list_data, partner],
			})
			com_id = partner.comparison_id;
			is_refresh = true
			// }

		}
		if (is_refresh === true) {
			this.action.doAction({
				type: 'ir.actions.act_window',
				res_model: 'purchase.order.comparison',
				res_id: parseInt(com_id),
				views: [[false, 'form']],
				target: 'current'
			});
		}
	}

	initData() {
		const dataInfo = {
			data: this.props.record.data,
			partner_datas: [],
			product_datas: [],
			vote_datas: [],
			product_price_list: [],
			product_vote_list: [],
			user_vote_list: [],
		};

		this.flow_line_id = dataInfo.data.flow_line_id[0];
		this.start_flow_line_id = dataInfo.data.vote_start_flow_line[0];

		const productData = dataInfo.data.line_ids.records
		for (var product of productData) {
			dataInfo.product_datas.push({ product_name: product.data.product_id[1], product_id: product.data.product_id[0], product_qty: product.data.product_qty });
		}
		this.products = dataInfo.product_datas;

		var voteData = dataInfo.data.vote_flow_line_ids.records;
		for (var user of voteData) {
			dataInfo.vote_datas.push({ vote_user: user.data.display_name, vote_id: user.data.id });
		}
		this.voteUsers = dataInfo.vote_datas;

		const partnerData = dataInfo.data.partner_ids.records;
		const comparisonData = dataInfo.data.purchase_comparison_js_line.records;
		const comparisonProductData = dataInfo.data.purchase_comparison_js_line_line.records;
		const comparisonVoteData = dataInfo.data.purchase_comparison_js_vote_line.records;

		for (var partner of partnerData) {
			var description = '';
			var description_id = 'description_' + partner.data.id.toString();
			var discount = 0;
			var discount_id = 'discount_' + partner.data.id.toString();
			var quality_point = 0;
			var quality_id = 'quality_' + partner.data.id.toString();
			var price_point = 0;
			var price_id = 'price_' + partner.data.id.toString();
			var other_point = 0;
			var other_id = 'other_' + partner.data.id.toString();
			var total_point = 0;
			var total_id = 'total_' + partner.data.id.toString();
			var niiluuleh_hugatsaa = 0;
			var honog_id = 'honog_' + partner.data.id.toString();
			var teever_tatvar = 0;
			var teever_tatvar_id = 'teever_tatvar_' + partner.data.id.toString();
			var insurance_other_expense = 0;
			var insurance_other_expense_id = 'insurance_other_expense_' + partner.data.id.toString();
			var total_expense = 0;
			var total_expense_id = 'total_expense_' + partner.data.id.toString();
			var total_price = 0;
			var total_price_id = 'total_price_' + partner.data.id.toString();
			var voted_total_price = 0;
			var currency_amount_id = 'currency_amount_' + partner.data.id.toString();
			var currency_amount = 0;
			var discount_currency_amount_id = 'discount_currency_amount_' + partner.data.id.toString();
			var discount_currency_amount = 0;
			var voted_discount_currency_amount_id = 'voted_discount_currency_amount_' + partner.data.id.toString();
			var voted_discount_currency_amount = 0;
			var voted_currency_amount_id = 'voted_currency_amount_' + partner.data.id.toString();
			var voted_currency_amount = 0;
			var voted_total_price_id = 'voted_total_price_' + partner.data.id.toString();
			var discount_total_price = 0;
			var discount_total_price_id = 'discount_total_price_' + partner.data.id.toString();
			var discount_voted_total_price = 0;
			var discount_voted_total_price_id = 'discount_voted_total_price_' + partner.data.id.toString();

			for (var compare of comparisonData) {
				if (compare.data.partner_id && compare.data.partner_id[0] === partner.data.id) {
					description = compare.data.description;
					discount = compare.data.discount;
					quality_point = compare.data.quality_point;
					price_point = compare.data.price_point;
					other_point = compare.data.other_point;
					total_point = compare.data.total_point;
					niiluuleh_hugatsaa = compare.data.niiluuleh_hugatsaa;
					teever_tatvar = compare.data.teever_tatvar;
					insurance_other_expense = compare.data.insurance_other_expense;
					total_expense = compare.data.total_expense;
					voted_total_price = compare.data.voted_total_price;
					currency_amount = compare.data.currency_amount;
					discount_currency_amount = compare.data.discount_currency_amount;
					voted_discount_currency_amount = compare.data.voted_discount_currency_amount;
					voted_currency_amount = compare.data.voted_currency_amount;
					total_price = compare.data.total_price;
					discount_total_price = compare.data.discount_total_price;
					discount_voted_total_price = compare.data.discount_voted_total_price;
				}
			}
			var vals = {
				partner_name: partner.data.display_name,
				partner_id: partner.data.id,
				comparison_id: dataInfo.data.id,
				description_id: description_id,
				description_value: description,
				discount_id: discount_id,
				discount_value: discount,
				quality_id: quality_id,
				quality_value: quality_point,
				price_id: price_id,
				price_value: price_point,
				other_id: other_id,
				other_value: other_point,
				total_point_id: total_id,
				total_point_value: total_point,
				honog_id: honog_id,
				niiluuleh_hugatsaa_value: niiluuleh_hugatsaa,
				teever_tatvar_id: teever_tatvar_id,
				teever_tatvar_value: teever_tatvar,
				insurance_other_expense_id: insurance_other_expense_id,
				insurance_other_expense_value: insurance_other_expense,
				total_expense_id: total_expense_id,
				total_expense_value: total_expense,
				total_price_id: total_price_id,
				total_price_value: total_price,
				currency_amount_id: currency_amount_id,
				currency_amount_value: currency_amount,
				discount_currency_amount_id: discount_currency_amount_id,
				discount_currency_amount_value: discount_currency_amount,
				voted_discount_currency_amount_id: voted_discount_currency_amount_id,
				voted_discount_currency_amount_value: voted_discount_currency_amount,
				voted_currency_amount_id: voted_currency_amount_id,
				voted_currency_amount_value: voted_currency_amount,
				voted_total_price_id: voted_total_price_id,
				voted_total_price_value: voted_total_price,
				discount_total_price_id: discount_total_price_id,
				discount_total_price_value: discount_total_price,
				discount_voted_total_price_id: discount_voted_total_price_id,
				discount_voted_total_price_value: discount_voted_total_price
			};
			dataInfo.partner_datas.push(vals);

			for (var product of dataInfo.product_datas) {
				var product_id = 0;
				var partner_id = 0;
				var id = 0;
				var price_unit_value = 0;
				var discount_value = 0;
				var price_total_value = 0;
				var product_vote = false;
				for (var pp of comparisonProductData) {
					if ((pp.data.partner_id && pp.data.partner_id[0] === partner.data.id) && (pp.data.product_id && pp.data.product_id[0] == product.product_id)) {
						price_unit_value = pp.data.price_unit;
						discount_value = pp.data.discount;
						price_total_value = pp.data.total_price;
						product_id = product.product_id;
						partner_id = partner.data.id;
						dataInfo.product_price_list[product_id + partner_id * 5] = price_unit_value;
						dataInfo.product_price_list[product_id + partner_id * 12] = discount_value;
						dataInfo.product_price_list[product_id + partner_id * 32] = price_total_value;
						product_vote = pp.data.is_vote;
						dataInfo.product_vote_list[product_id + partner_id * 22] = product_vote;
					}
				}
			}

			for (var vote of dataInfo.vote_datas) {
				var vote_id = 0;
				var partner_id = 0;
				var id = 0;
				var user_vote_value = false;
				for (var pp of comparisonVoteData) {
					if ((pp.data.partner_id && pp.data.partner_id[0] === partner.data.id) && (pp.data.vote_flow_line_id && pp.data.vote_flow_line_id[0] == vote.vote_id)) {
						user_vote_value = pp.data.is_user_vote;
						vote_id = vote.vote_id;
						partner_id = partner.data.id;
						id = vote_id + partner_id * 12;
						dataInfo.user_vote_list[id] = user_vote_value;
					}
				}
			}
		}
		this.product_price_list = dataInfo.product_price_list
		this.product_vote_list = dataInfo.product_vote_list
		this.user_vote_list = dataInfo.user_vote_list
		this.partners = dataInfo.partner_datas;
	}

	onCheckboxChange(event) {
		const isChecked = event.target.checked;
		$(document).ready(function () {
			$('input[type="checkbox"]').on('change', function () {
				var checkedValue = $(this).prop('checked');
				$(this).closest('tr').find('input[type="checkbox"]').each(function () {
					$(this).prop('checked', false);
				});
				$(this).prop("checked", checkedValue);
			});
		});

		this.env.bus.trigger("comparison_widget_checkbox_event", {
			isChecked: isChecked,
		});
	}

	doPartnerInfo(event) {
		event.preventDefault();
		var partnerId = event.currentTarget.getAttribute('data-partner-id');

		this.action.doAction({
			type: 'ir.actions.act_window',
			res_model: 'res.partner',
			res_id: parseInt(partnerId),
			views: [[false, 'form']],
			target: 'current'
		});
	}

	doProductInfo(event) {
		event.preventDefault();
		var partnerId = event.currentTarget.getAttribute('td-product-id');

		this.action.doAction({
			type: 'ir.actions.act_window',
			res_model: 'product.product',
			res_id: parseInt(partnerId),
			views: [[false, 'form']],
			target: 'current'
		});
	}
}

PurchaseComparisonWidget.template = 'mw_purchase_comparison_js.PurchaseComparison';
registry.category("view_widgets").add("purchase_comparison_widget", PurchaseComparisonWidget);