# coding: utf-8
"""
Provide a report and downloadable CSV according to the German DATEV format.

- Query report showing only the columns that contain data, formatted nicely for
	dispay to the user.
- CSV download functionality `download_datev_csv` that provides a CSV file with
	all required columns. Used to import the data into the DATEV Software.
"""
from __future__ import unicode_literals

import json
import frappe
from six import string_types

from frappe import _
from verp.accounts.utils import get_fiscal_year
from verp.regional.germany.utils.datev.datev_csv import zip_and_download, get_datev_csv
from verp.regional.germany.utils.datev.datev_constants import Transactions, DebtorsCreditors, AccountNames

COLUMNS = [
	{
		"label": "Umsatz (ohne Soll/Haben-Kz)",
		"fieldname": "Umsatz (ohne Soll/Haben-Kz)",
		"fieldtype": "Currency",
		"width": 100
	},
	{
		"label": "Soll/Haben-Kennzeichen",
		"fieldname": "Soll/Haben-Kennzeichen",
		"fieldtype": "Data",
		"width": 100
	},
	{
		"label": "Konto",
		"fieldname": "Konto",
		"fieldtype": "Data",
		"width": 100
	},
	{
		"label": "Gegenkonto (ohne BU-Schlüssel)",
		"fieldname": "Gegenkonto (ohne BU-Schlüssel)",
		"fieldtype": "Data",
		"width": 100
	},
	{
		"label": "Belegdatum",
		"fieldname": "Belegdatum",
		"fieldtype": "Date",
		"width": 100
	},
	{
		"label": "Belegfeld 1",
		"fieldname": "Belegfeld 1",
		"fieldtype": "Data",
		"width": 150
	},
	{
		"label": "Buchungstext",
		"fieldname": "Buchungstext",
		"fieldtype": "Text",
		"width": 300
	},
	{
		"label": "Beleginfo - Art 1",
		"fieldname": "Beleginfo - Art 1",
		"fieldtype": "Link",
		"options": "DocType",
		"width": 100
	},
	{
		"label": "Beleginfo - Inhalt 1",
		"fieldname": "Beleginfo - Inhalt 1",
		"fieldtype": "Dynamic Link",
		"options": "Beleginfo - Art 1",
		"width": 150
	},
	{
		"label": "Beleginfo - Art 2",
		"fieldname": "Beleginfo - Art 2",
		"fieldtype": "Link",
		"options": "DocType",
		"width": 100
	},
	{
		"label": "Beleginfo - Inhalt 2",
		"fieldname": "Beleginfo - Inhalt 2",
		"fieldtype": "Dynamic Link",
		"options": "Beleginfo - Art 2",
		"width": 150
	},
	{
		"label": "Beleginfo - Art 3",
		"fieldname": "Beleginfo - Art 3",
		"fieldtype": "Link",
		"options": "DocType",
		"width": 100
	},
	{
		"label": "Beleginfo - Inhalt 3",
		"fieldname": "Beleginfo - Inhalt 3",
		"fieldtype": "Dynamic Link",
		"options": "Beleginfo - Art 3",
		"width": 150
	},
	{
		"label": "Beleginfo - Art 4",
		"fieldname": "Beleginfo - Art 4",
		"fieldtype": "Data",
		"width": 100
	},
	{
		"label": "Beleginfo - Inhalt 4",
		"fieldname": "Beleginfo - Inhalt 4",
		"fieldtype": "Data",
		"width": 150
	}
]


def execute(filters=None):
	"""Entry point for frappe."""
	data = []
	if filters and validate(filters):
		fn = 'temporary_against_account_number'
		filters[fn] = frappe.get_value('DATEV Settings', filters.get('company'), fn)
		data = get_transactions(filters, as_dict=0)

	return COLUMNS, data


def validate(filters):
	"""Make sure all mandatory filters and settings are present."""
	company = filters.get('company')
	if not company:
		frappe.throw(_('<b>Company</b> is a mandatory filter.'))

	from_date = filters.get('from_date')
	if not from_date:
		frappe.throw(_('<b>From Date</b> is a mandatory filter.'))

	to_date = filters.get('to_date')
	if not to_date:
		frappe.throw(_('<b>To Date</b> is a mandatory filter.'))

	validate_fiscal_year(from_date, to_date, company)

	if not frappe.db.exists('DATEV Settings', filters.get('company')):
		msg = 'Please create DATEV Settings for Company {}'.format(filters.get('company'))
		frappe.log_error(msg, title='DATEV Settings missing')
		return False

	return True


def validate_fiscal_year(from_date, to_date, company):
	from_fiscal_year = get_fiscal_year(date=from_date, company=company)
	to_fiscal_year = get_fiscal_year(date=to_date, company=company)
	if from_fiscal_year != to_fiscal_year:
		frappe.throw(_('Dates {} and {} are not in the same fiscal year.').format(from_date, to_date))


def get_transactions(filters, as_dict=1):
	"""
	Get a list of accounting entries.

	Select GL Entries joined with Account and Party Account in order to get the
	account numbers. Returns a list of accounting entries.

	Arguments:
	filters -- dict of filters to be passed to the sql query
	as_dict -- return as list of dicts [0,1]
	"""
	filter_by_voucher = 'AND gl.voucher_type = %(voucher_type)s' if filters.get('voucher_type') else ''
	gl_entries = frappe.db.sql("""
		SELECT

			/* either debit or credit amount; always positive */
			case gl.debit when 0 then gl.credit else gl.debit end as 'Umsatz (ohne Soll/Haben-Kz)',

			/* 'H' when credit, 'S' when debit */
			case gl.debit when 0 then 'H' else 'S' end as 'Soll/Haben-Kennzeichen',

			/* account number or, if empty, party account number */
			acc.account_number as 'Konto',

			/* against number or, if empty, party against number */
			%(temporary_against_account_number)s as 'Gegenkonto (ohne BU-Schlüssel)',

			gl.posting_date as 'Belegdatum',
			gl.voucher_no as 'Belegfeld 1',
			LEFT(gl.remarks, 60) as 'Buchungstext',
			gl.voucher_type as 'Beleginfo - Art 1',
			gl.voucher_no as 'Beleginfo - Inhalt 1',
			gl.against_voucher_type as 'Beleginfo - Art 2',
			gl.against_voucher as 'Beleginfo - Inhalt 2',
			gl.party_type as 'Beleginfo - Art 3',
			gl.party as 'Beleginfo - Inhalt 3',
			case gl.party_type when 'Customer' then 'Debitorennummer' when 'Supplier' then 'Kreditorennummer' else NULL end as 'Beleginfo - Art 4',
			par.debtor_creditor_number as 'Beleginfo - Inhalt 4'

		FROM `tabGL Entry` gl

			/* Kontonummer */
			left join `tabAccount` acc 
			on gl.account = acc.name

			left join `tabCustomer` cus
			on gl.party_type = 'Customer'
			and gl.party = cus.name

			left join `tabSupplier` sup
			on gl.party_type = 'Supplier'
			and gl.party = sup.name

			left join `tabParty Account` par
			on par.parent = gl.party
			and par.parenttype = gl.party_type
			and par.company = %(company)s

		WHERE gl.company = %(company)s 
		AND DATE(gl.posting_date) >= %(from_date)s
		AND DATE(gl.posting_date) <= %(to_date)s
		{}
		ORDER BY 'Belegdatum', gl.voucher_no""".format(filter_by_voucher), filters, as_dict=as_dict)

	return gl_entries


def get_customers(filters):
	"""
	Get a list of Customers.

	Arguments:
	filters -- dict of filters to be passed to the sql query
	"""
	return frappe.db.sql("""
		SELECT

			par.debtor_creditor_number as 'Konto',
			CASE cus.customer_type
				WHEN 'Company' THEN cus.customer_name
				ELSE null
				END as 'Name (Adressatentyp Unternehmen)',
			CASE cus.customer_type
				WHEN 'Individual' THEN TRIM(SUBSTR(cus.customer_name, LOCATE(' ', cus.customer_name)))
				ELSE null
				END as 'Name (Adressatentyp natürl. Person)',
			CASE cus.customer_type
				WHEN 'Individual' THEN SUBSTRING_INDEX(SUBSTRING_INDEX(cus.customer_name, ' ', 1), ' ', -1)
				ELSE null
				END as 'Vorname (Adressatentyp natürl. Person)',
			CASE cus.customer_type
				WHEN 'Individual' THEN '1'
				WHEN 'Company' THEN '2'
				ELSE '0'
				END as 'Adressatentyp',
			adr.address_line1 as 'Straße',
			adr.pincode as 'Postleitzahl',
			adr.city as 'Ort',
			UPPER(country.code) as 'Land',
			adr.address_line2 as 'Adresszusatz',
			adr.email_id as 'E-Mail',
			adr.phone as 'Telefon',
			adr.fax as 'Fax',
			cus.website as 'Internet',
			cus.tax_id as 'Steuernummer'

		FROM `tabCustomer` cus

			left join `tabParty Account` par
			on par.parent = cus.name
			and par.parenttype = 'Customer'
			and par.company = %(company)s

			left join `tabDynamic Link` dyn_adr
			on dyn_adr.link_name = cus.name
			and dyn_adr.link_doctype = 'Customer'
			and dyn_adr.parenttype = 'Address'

			left join `tabAddress` adr
			on adr.name = dyn_adr.parent
			and adr.is_primary_address = '1'

			left join `tabCountry` country
			on country.name = adr.country

		WHERE adr.is_primary_address = '1'
		""", filters, as_dict=1)


def get_suppliers(filters):
	"""
	Get a list of Suppliers.

	Arguments:
	filters -- dict of filters to be passed to the sql query
	"""
	return frappe.db.sql("""
		SELECT

			par.debtor_creditor_number as 'Konto',
			CASE sup.supplier_type
				WHEN 'Company' THEN sup.supplier_name
				ELSE null
				END as 'Name (Adressatentyp Unternehmen)',
			CASE sup.supplier_type
				WHEN 'Individual' THEN TRIM(SUBSTR(sup.supplier_name, LOCATE(' ', sup.supplier_name)))
				ELSE null
				END as 'Name (Adressatentyp natürl. Person)',
			CASE sup.supplier_type
				WHEN 'Individual' THEN SUBSTRING_INDEX(SUBSTRING_INDEX(sup.supplier_name, ' ', 1), ' ', -1)
				ELSE null
				END as 'Vorname (Adressatentyp natürl. Person)',
			CASE sup.supplier_type
				WHEN 'Individual' THEN '1'
				WHEN 'Company' THEN '2'
				ELSE '0'
				END as 'Adressatentyp',
			adr.address_line1 as 'Straße',
			adr.pincode as 'Postleitzahl',
			adr.city as 'Ort',
			UPPER(country.code) as 'Land',
			adr.address_line2 as 'Adresszusatz',
			adr.email_id as 'E-Mail',
			adr.phone as 'Telefon',
			adr.fax as 'Fax',
			sup.website as 'Internet',
			sup.tax_id as 'Steuernummer',
			case sup.on_hold when 1 then sup.release_date else null end as 'Zahlungssperre bis'

		FROM `tabSupplier` sup

			left join `tabParty Account` par
			on par.parent = sup.name
			and par.parenttype = 'Supplier'
			and par.company = %(company)s

			left join `tabDynamic Link` dyn_adr
			on dyn_adr.link_name = sup.name
			and dyn_adr.link_doctype = 'Supplier'
			and dyn_adr.parenttype = 'Address'

			left join `tabAddress` adr
			on adr.name = dyn_adr.parent
			and adr.is_primary_address = '1'

			left join `tabCountry` country
			on country.name = adr.country

		WHERE adr.is_primary_address = '1'
		""", filters, as_dict=1)


def get_account_names(filters):
	return frappe.db.sql("""
		SELECT

			account_number as 'Konto',
			LEFT(account_name, 40) as 'Kontenbeschriftung',
			'de-DE' as 'Sprach-ID'

		FROM `tabAccount`
		WHERE company = %(company)s
		AND is_group = 0
		AND account_number != ''
	""", filters, as_dict=1)


@frappe.whitelist()
def download_datev_csv(filters):
	"""
	Provide accounting entries for download in DATEV format.

	Validate the filters, get the data, produce the CSV file and provide it for
	download. Can be called like this:

	GET /api/method/verp.regional.report.datev.datev.download_datev_csv

	Arguments / Params:
	filters -- dict of filters to be passed to the sql query
	"""
	if isinstance(filters, string_types):
		filters = json.loads(filters)

	validate(filters)
	company = filters.get('company')

	fiscal_year = get_fiscal_year(date=filters.get('from_date'), company=company)
	filters['fiscal_year_start'] = fiscal_year[1]

	# set chart of accounts used
	coa = frappe.get_value('Company', company, 'chart_of_accounts')
	filters['skr'] = '04' if 'SKR04' in coa else ('03' if 'SKR03' in coa else '')

	datev_settings = frappe.get_doc('DATEV Settings', company)
	filters['account_number_length'] = datev_settings.account_number_length
	filters['temporary_against_account_number'] = datev_settings.temporary_against_account_number

	transactions = get_transactions(filters)
	account_names = get_account_names(filters)
	customers = get_customers(filters)
	suppliers = get_suppliers(filters)

	zip_name = '{} DATEV.zip'.format(frappe.utils.datetime.date.today())
	zip_and_download(zip_name, [
		{
			'file_name': 'EXTF_Buchungsstapel.csv',
			'csv_data': get_datev_csv(transactions, filters, csv_class=Transactions)
		},
		{
			'file_name': 'EXTF_Kontenbeschriftungen.csv',
			'csv_data': get_datev_csv(account_names, filters, csv_class=AccountNames)
		},
		{
			'file_name': 'EXTF_Kunden.csv',
			'csv_data': get_datev_csv(customers, filters, csv_class=DebtorsCreditors)
		},
		{
			'file_name': 'EXTF_Lieferanten.csv',
			'csv_data': get_datev_csv(suppliers, filters, csv_class=DebtorsCreditors)
		},
	])
