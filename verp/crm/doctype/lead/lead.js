// Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("verp");
cur_frm.email_field = "email_id";

verp.LeadController = class LeadController extends frappe.ui.form.Controller {
	setup () {
		this.frm.make_methods = {
			'Customer': this.make_customer,
			'Quotation': this.make_quotation,
			'Opportunity': this.make_opportunity
		};

		this.frm.toggle_reqd("lead_name", !this.frm.doc.organization_lead);
	}

	onload () {
		this.frm.set_query("customer", function (doc, cdt, cdn) {
			return { query: "verp.controllers.queries.customer_query" }
		});

		this.frm.set_query("lead_owner", function (doc, cdt, cdn) {
			return { query: "frappe.core.doctype.user.user.user_query" }
		});

		this.frm.set_query("contact_by", function (doc, cdt, cdn) {
			return { query: "frappe.core.doctype.user.user.user_query" }
		});
	}

	refresh () {
		let doc = this.frm.doc;
		verp.toggle_naming_series();
		frappe.dynamic_link = { doc: doc, fieldname: 'name', doctype: 'Lead' }

		if (!this.frm.is_new() && doc.__onload && !doc.__onload.is_customer) {
			this.frm.add_custom_button(__("Customer"), this.make_customer, __("Create"));
			this.frm.add_custom_button(__("Opportunity"), this.make_opportunity, __("Create"));
			this.frm.add_custom_button(__("Quotation"), this.make_quotation, __("Create"));
		}

		if (!this.frm.is_new()) {
			frappe.contacts.render_address_and_contact(this.frm);
		} else {
			frappe.contacts.clear_address_and_contact(this.frm);
		}
	}

	make_customer () {
		frappe.model.open_mapped_doc({
			method: "verp.crm.doctype.lead.lead.make_customer",
			frm: cur_frm
		})
	}

	make_opportunity () {
		frappe.model.open_mapped_doc({
			method: "verp.crm.doctype.lead.lead.make_opportunity",
			frm: cur_frm
		})
	}

	make_quotation () {
		frappe.model.open_mapped_doc({
			method: "verp.crm.doctype.lead.lead.make_quotation",
			frm: cur_frm
		})
	}

	organization_lead () {
		this.frm.toggle_reqd("lead_name", !this.frm.doc.organization_lead);
		this.frm.toggle_reqd("company_name", this.frm.doc.organization_lead);
	}

	company_name () {
		if (this.frm.doc.organization_lead && !this.frm.doc.lead_name) {
			this.frm.set_value("lead_name", this.frm.doc.company_name);
		}
	}

	contact_date () {
		if (this.frm.doc.contact_date) {
			let d = moment(this.frm.doc.contact_date);
			d.add(1, "day");
			this.frm.set_value("ends_on", d.format(frappe.defaultDatetimeFormat));
		}
	}
};

extend_cscript(cur_frm.cscript, new verp.LeadController({ frm: cur_frm }));

