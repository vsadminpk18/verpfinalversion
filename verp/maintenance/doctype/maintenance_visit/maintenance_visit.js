// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.provide("verp.maintenance");
var serial_nos = [];
frappe.ui.form.on('Maintenance Visit', {
	refresh: function (frm) {
		//filters for serial_no based on item_code
		frm.set_query('serial_no', 'purposes', function (frm, cdt, cdn) {
			let item = locals[cdt][cdn];
			if (serial_nos) {
				return {
					filters: {
						'item_code': item.item_code,
						'name': ["in", serial_nos]
					}
				};
			} else {
				return {
					filters: {
						'item_code': item.item_code
					}
				};
			}
		});
	},
	setup: function (frm) {
		frm.set_query('contact_person', verp.queries.contact_query);
		frm.set_query('customer_address', verp.queries.address_query);
		frm.set_query('customer', verp.queries.customer);
	},
	onload: function (frm, cdt, cdn) {
		let item = locals[cdt][cdn];
		if (frm.maintenance_type == 'Scheduled') {
			let schedule_id = item.purposes[0].prevdoc_detail_docname;
			frappe.call({
				method: "verp.maintenance.doctype.maintenance_schedule.maintenance_schedule.update_serial_nos",
				args: {
					s_id: schedule_id
				},
				callback: function (r) {
					serial_nos = r.message;
				}
			});
		}

		if (!frm.doc.status) {
			frm.set_value({ status: 'Draft' });
		}
		if (frm.doc.__islocal) {
			frm.set_value({ mntc_date: frappe.datetime.get_today() });
		}
	},
	customer: function (frm) {
		verp.utils.get_party_details(frm);
	},
	customer_address: function (frm) {
		verp.utils.get_address_display(frm, 'customer_address', 'address_display');
	},
	contact_person: function (frm) {
		verp.utils.get_contact_details(frm);
	}

})

// TODO commonify this code
verp.maintenance.MaintenanceVisit = class MaintenanceVisit extends frappe.ui.form.Controller {
	refresh() {
		frappe.dynamic_link = {doc: this.frm.doc, fieldname: 'customer', doctype: 'Customer'}

		var me = this;

		if (this.frm.doc.docstatus === 0) {
			this.frm.add_custom_button(__('Maintenance Schedule'),
				function () {
					verp.utils.map_current_doc({
						method: "verp.maintenance.doctype.maintenance_schedule.maintenance_schedule.make_maintenance_visit",
						source_doctype: "Maintenance Schedule",
						target: me.frm,
						setters: {
							customer: me.frm.doc.customer || undefined,
						},
						get_query_filters: {
							docstatus: 1,
							company: me.frm.doc.company
						}
					})
				}, __("Get Items From"));
			this.frm.add_custom_button(__('Warranty Claim'),
				function () {
					verp.utils.map_current_doc({
						method: "verp.support.doctype.warranty_claim.warranty_claim.make_maintenance_visit",
						source_doctype: "Warranty Claim",
						target: me.frm,
						date_field: "complaint_date",
						setters: {
							customer: me.frm.doc.customer || undefined,
						},
						get_query_filters: {
							status: ["in", "Open, Work in Progress"],
							company: me.frm.doc.company
						}
					})
				}, __("Get Items From"));
			this.frm.add_custom_button(__('Sales Order'),
				function () {
					verp.utils.map_current_doc({
						method: "verp.selling.doctype.sales_order.sales_order.make_maintenance_visit",
						source_doctype: "Sales Order",
						target: me.frm,
						setters: {
							customer: me.frm.doc.customer || undefined,
						},
						get_query_filters: {
							docstatus: 1,
							company: me.frm.doc.company,
							order_type: me.frm.doc.order_type,
						}
					})
				}, __("Get Items From"));
		}
	}
};

extend_cscript(cur_frm.cscript, new verp.maintenance.MaintenanceVisit({frm: cur_frm}));
