# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
#import frappe
import verp
from frappe.model.document import Document

class IncomeTaxSlab(Document):
	def validate(self):
		if self.company:
			self.currency = verp.get_company_currency(self.company)
