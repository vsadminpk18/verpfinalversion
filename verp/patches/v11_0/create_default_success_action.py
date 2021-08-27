from __future__ import unicode_literals
import frappe
from verp.setup.install import create_default_success_action

def execute():
	frappe.reload_doc("core", "doctype", "success_action")
	create_default_success_action()
