// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Gross and Net Profit Report"] = {
	"filters": [

	]
}
frappe.require("assets/verp/js/financial_statements.js", function() {
	frappe.query_reports["Gross and Net Profit Report"] = $.extend({},
		verp.financial_statements);

	frappe.query_reports["Gross and Net Profit Report"]["filters"].push(
		{
			"fieldname": "project",
			"label": __("Project"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Project', txt);
			}
		},
		{
			"fieldname": "accumulated_values",
			"label": __("Accumulated Values"),
			"fieldtype": "Check"
		}
	);
});
