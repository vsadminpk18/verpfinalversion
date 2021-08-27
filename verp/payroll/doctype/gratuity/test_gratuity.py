# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
import unittest
from verp.hr.doctype.employee.test_employee import make_employee
from verp.payroll.doctype.salary_slip.test_salary_slip import make_employee_salary_slip, make_earning_salary_component, \
	make_deduction_salary_component
from verp.payroll.doctype.gratuity.gratuity import get_last_salary_slip
from verp.regional.united_arab_emirates.setup import create_gratuity_rule
from verp.hr.doctype.expense_claim.test_expense_claim import get_payable_account
from frappe.utils import getdate, add_days, get_datetime, flt

test_dependencies = ["Salary Component", "Salary Slip", "Account"]
class TestGratuity(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		make_earning_salary_component(setup=True, test_tax=True, company_list=['_Test Company'])
		make_deduction_salary_component(setup=True, test_tax=True, company_list=['_Test Company'])

	def setUp(self):
		frappe.db.sql("DELETE FROM `tabGratuity`")
		frappe.db.sql("DELETE FROM `tabAdditional Salary` WHERE ref_doctype = 'Gratuity'")

	def test_check_gratuity_amount_based_on_current_slab_and_additional_salary_creation(self):
		employee, sal_slip = create_employee_and_get_last_salary_slip()

		rule = get_gratuity_rule("Rule Under Unlimited Contract on termination (UAE)")

		gratuity = create_gratuity(pay_via_salary_slip = 1, employee=employee, rule=rule.name)

		#work experience calculation
		date_of_joining, relieving_date = frappe.db.get_value('Employee', employee, ['date_of_joining', 'relieving_date'])
		employee_total_workings_days = (get_datetime(relieving_date) - get_datetime(date_of_joining)).days

		experience = employee_total_workings_days/rule.total_working_days_per_year
		gratuity.reload()
		from math import floor
		self.assertEqual(floor(experience), gratuity.current_work_experience)

		#amount Calculation
		component_amount = frappe.get_list("Salary Detail",
		filters={
			"docstatus": 1,
			'parent': sal_slip,
			"parentfield": "earnings",
			'salary_component': "Basic Salary"
		},
		fields=["amount"])

		''' 5 - 0 fraction is 1 '''

		gratuity_amount = component_amount[0].amount * experience
		gratuity.reload()

		self.assertEqual(flt(gratuity_amount, 2), flt(gratuity.amount, 2))

		#additional salary creation (Pay via salary slip)
		self.assertTrue(frappe.db.exists("Additional Salary", {"ref_docname": gratuity.name}))

	def test_check_gratuity_amount_based_on_all_previous_slabs(self):
		employee, sal_slip = create_employee_and_get_last_salary_slip()
		rule = get_gratuity_rule("Rule Under Limited Contract (UAE)")
		set_mode_of_payment_account()

		gratuity = create_gratuity(expense_account = 'Payment Account - _TC', mode_of_payment='Cash', employee=employee)

		#work experience calculation
		date_of_joining, relieving_date = frappe.db.get_value('Employee', employee, ['date_of_joining', 'relieving_date'])
		employee_total_workings_days = (get_datetime(relieving_date) - get_datetime(date_of_joining)).days

		experience = employee_total_workings_days/rule.total_working_days_per_year

		gratuity.reload()

		from math import floor

		self.assertEqual(floor(experience), gratuity.current_work_experience)

		#amount Calculation
		component_amount = frappe.get_list("Salary Detail",
		filters={
			"docstatus": 1,
			'parent': sal_slip,
			"parentfield": "earnings",
			'salary_component': "Basic Salary"
		},
		fields=["amount"])

		''' range  | Fraction
			0-1    |    0
			1-5    |   0.7
			5-0    |    1
		'''

		gratuity_amount = ((0 * 1) + (4 * 0.7) + (1 * 1)) *  component_amount[0].amount
		gratuity.reload()

		self.assertEqual(flt(gratuity_amount, 2), flt(gratuity.amount, 2))
		self.assertEqual(gratuity.status, "Unpaid")

		from verp.accounts.doctype.payment_entry.payment_entry import get_payment_entry
		pay_entry = get_payment_entry("Gratuity", gratuity.name)
		pay_entry.reference_no = "123467"
		pay_entry.reference_date = getdate()
		pay_entry.save()
		pay_entry.submit()
		gratuity.reload()

		self.assertEqual(gratuity.status, "Paid")
		self.assertEqual(flt(gratuity.paid_amount,2), flt(gratuity.amount, 2))

	def tearDown(self):
		frappe.db.sql("DELETE FROM `tabGratuity`")
		frappe.db.sql("DELETE FROM `tabAdditional Salary` WHERE ref_doctype = 'Gratuity'")

def get_gratuity_rule(name):
	rule = frappe.db.exists("Gratuity Rule", name)
	if not rule:
		create_gratuity_rule()
	rule = frappe.get_doc("Gratuity Rule", name)
	rule.applicable_earnings_component = []
	rule.append("applicable_earnings_component", {
		"salary_component": "Basic Salary"
	})
	rule.save()
	rule.reload()

	return rule

def create_gratuity(**args):
	if args:
		args = frappe._dict(args)
	gratuity = frappe.new_doc("Gratuity")
	gratuity.employee = args.employee
	gratuity.posting_date = getdate()
	gratuity.gratuity_rule = args.rule or "Rule Under Limited Contract (UAE)"
	gratuity.pay_via_salary_slip = args.pay_via_salary_slip or 0
	if gratuity.pay_via_salary_slip:
		gratuity.payroll_date = getdate()
		gratuity.salary_component = "Performance Bonus"
	else:
		gratuity.expense_account =  args.expense_account or 'Payment Account - _TC'
		gratuity.payable_account = args.payable_account or get_payable_account("_Test Company")
		gratuity.mode_of_payment = args.mode_of_payment or 'Cash'

	gratuity.save()
	gratuity.submit()

	return gratuity

def set_mode_of_payment_account():
	if not frappe.db.exists("Account", "Payment Account - _TC"):
		mode_of_payment = create_account()

	mode_of_payment = frappe.get_doc("Mode of Payment", "Cash")

	mode_of_payment.accounts = []
	mode_of_payment.append("accounts", {
		"company": "_Test Company",
		"default_account": "_Test Bank - _TC"
	})
	mode_of_payment.save()

def create_account():
	return frappe.get_doc({
			"doctype": "Account",
			"company": "_Test Company",
			"account_name": "Payment Account",
			"root_type": "Asset",
			"report_type": "Balance Sheet",
			"currency": "INR",
			"parent_account": "Bank Accounts - _TC",
			"account_type": "Bank",
		}).insert(ignore_permissions=True)

def create_employee_and_get_last_salary_slip():
	employee = make_employee("test_employee@salary.com", company='_Test Company')
	frappe.db.set_value("Employee", employee, "relieving_date", getdate())
	frappe.db.set_value("Employee", employee, "date_of_joining", add_days(getdate(), - (6*365)))
	if not frappe.db.exists("Salary Slip", {"employee":employee}):
		salary_slip = make_employee_salary_slip("test_employee@salary.com", "Monthly")
		salary_slip.submit()
		salary_slip = salary_slip.name
	else:
		salary_slip = get_last_salary_slip(employee)

	if not frappe.db.get_value("Employee", "test_employee@salary.com", "holiday_list"):
		from verp.payroll.doctype.salary_slip.test_salary_slip import make_holiday_list
		make_holiday_list()
		frappe.db.set_value("Company", '_Test Company', "default_holiday_list", "Salary Slip Test Holiday List")

	return employee, salary_slip
