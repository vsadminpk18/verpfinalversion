// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.require("assets/verp/js/salary_slip_deductions_report_filters.js", function() {
	frappe.query_reports["Provident Fund Deductions"] = verp.salary_slip_deductions_report_filters;
});