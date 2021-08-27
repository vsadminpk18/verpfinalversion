// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/verp/js/financial_statements.js", function() {
	frappe.query_reports["Dimension-wise Accounts Balance Report"] = {
		"filters": [
			{
				"fieldname": "company",
				"label": __("Company"),
				"fieldtype": "Link",
				"options": "Company",
				"default": frappe.defaults.get_user_default("Company"),
				"reqd": 1
			},
			{
				"fieldname": "fiscal_year",
				"label": __("Fiscal Year"),
				"fieldtype": "Link",
				"options": "Fiscal Year",
				"default": frappe.defaults.get_user_default("fiscal_year"),
				"reqd": 1,
				"on_change": function(query_report) {
					var fiscal_year = query_report.get_values().fiscal_year;
					if (!fiscal_year) {
						return;
					}
					frappe.model.with_doc("Fiscal Year", fiscal_year, function(r) {
						var fy = frappe.model.get_doc("Fiscal Year", fiscal_year);
						frappe.query_report.set_filter_value({
							from_date: fy.year_start_date,
							to_date: fy.year_end_date
						});
					});
				}
			},
			{
				"fieldname": "from_date",
				"label": __("From Date"),
				"fieldtype": "Date",
				"default": frappe.defaults.get_user_default("year_start_date"),
			},
			{
				"fieldname": "to_date",
				"label": __("To Date"),
				"fieldtype": "Date",
				"default": frappe.defaults.get_user_default("year_end_date"),
			},
			{
				"fieldname": "finance_book",
				"label": __("Finance Book"),
				"fieldtype": "Link",
				"options": "Finance Book",
			},
			{
				"fieldname": "dimension",
				"label": __("Select Dimension"),
				"fieldtype": "Select",
				"options": get_accounting_dimension_options(),
				"reqd": 1,
			},
		],
		"formatter": verp.financial_statements.formatter,
		"tree": true,
		"name_field": "account",
		"parent_field": "parent_account",
		"initial_depth": 3
	}

});

function get_accounting_dimension_options() {
	let options =["", "Cost Center", "Project"];
	frappe.db.get_list('Accounting Dimension',
		{fields:['document_type']}).then((res) => {
			res.forEach((dimension) => {
				options.push(dimension.document_type);
			});
		});
	return options
}
