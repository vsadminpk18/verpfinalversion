frappe.provide("verp.accounts.bank_reconciliation");

verp.accounts.bank_reconciliation.DataTableManager = class DataTableManager {
	constructor(opts) {
		Object.assign(this, opts);
		this.dialog_manager = new verp.accounts.bank_reconciliation.DialogManager(
			this.company,
			this.bank_account
		);
		this.make_dt();
	}

	make_dt() {
		var me = this;
		frappe.call({
			method:
				"verp.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.get_bank_transactions",
			args: {
				bank_account: this.bank_account,
			},
			callback: function (response) {
				me.format_data(response.message);
				me.get_dt_columns();
				me.get_datatable();
				me.set_listeners();
			},
		});
	}

	get_dt_columns() {
		this.columns = [
			{
				name: "Date",
				editable: false,
				width: 100,
			},

			{
				name: "Party Type",
				editable: false,
				width: 95,
			},
			{
				name: "Party",
				editable: false,
				width: 100,
			},
			{
				name: "Description",
				editable: false,
				width: 350,
			},
			{
				name: "Deposit",
				editable: false,
				width: 100,
				format: (value) =>
					"<span style='color:green;'>" +
					format_currency(value, this.currency) +
					"</span>",
			},
			{
				name: "Withdrawal",
				editable: false,
				width: 100,
				format: (value) =>
					"<span style='color:red;'>" +
					format_currency(value, this.currency) +
					"</span>",
			},
			{
				name: "Unallocated Amount",
				editable: false,
				width: 100,
				format: (value) =>
					"<span style='color:blue;'>" +
					format_currency(value, this.currency) +
					"</span>",
			},
			{
				name: "Reference Number",
				editable: false,
				width: 140,
			},
			{
				name: "Actions",
				editable: false,
				sortable: false,
				focusable: false,
				dropdown: false,
				width: 80,
			},
		];
	}

	format_data(transactions) {
		this.transactions = [];
		if (transactions[0]) {
			this.currency = transactions[0]["currency"];
		}
		this.transaction_dt_map = {};
		let length;
		transactions.forEach((row) => {
			length = this.transactions.push(this.format_row(row));
			this.transaction_dt_map[row["name"]] = length - 1;
		});
	}

	format_row(row) {
		return [
			row["date"],
			row["party_type"],
			row["party"],
			row["description"],
			row["deposit"],
			row["withdrawal"],
			row["unallocated_amount"],
			row["reference_number"],
			`
			<Button class="btn btn-primary btn-xs center"  data-name = ${row["name"]} >
				Actions
			</a>
			`,
		];
	}

	get_datatable() {
		const datatable_options = {
			columns: this.columns,
			data: this.transactions,
			dynamicRowHeight: true,
			checkboxColumn: false,
			inlineFilters: true,
		};
		this.datatable = new frappe.DataTable(
			this.$reconciliation_tool_dt.get(0),
			datatable_options
		);
		$(`.${this.datatable.style.scopeClass} .dt-scrollable`).css(
			"max-height",
			"calc(100vh - 400px)"
		);

		if (this.transactions.length > 0) {
			this.$reconciliation_tool_dt.show();
			this.$no_bank_transactions.hide();
		} else {
			this.$reconciliation_tool_dt.hide();
			this.$no_bank_transactions.show();
		}
	}

	set_listeners() {
		var me = this;
		$(`.${this.datatable.style.scopeClass} .dt-scrollable`).on(
			"click",
			`.btn`,
			function () {
				me.dialog_manager.show_dialog(
					$(this).attr("data-name"),
					(bank_transaction) => me.update_dt_cards(bank_transaction)
				);
				return true;
			}
		);
	}

	update_dt_cards(bank_transaction) {
		const transaction_index = this.transaction_dt_map[
			bank_transaction.name
		];
		if (bank_transaction.unallocated_amount > 0) {
			this.transactions[transaction_index] = this.format_row(
				bank_transaction
			);
		} else {
			this.transactions.splice(transaction_index, 1);
		}
		this.datatable.refresh(this.transactions, this.columns);

		if (this.transactions.length == 0) {
			this.$reconciliation_tool_dt.hide();
			this.$no_bank_transactions.show();
		}

		// this.make_dt();
		this.get_cleared_balance().then(() => {
			this.cards_manager.$cards[1].set_value(
				format_currency(this.cleared_balance),
				this.currency
			);
			this.cards_manager.$cards[2].set_value(
				format_currency(
					this.bank_statement_closing_balance - this.cleared_balance
				),
				this.currency
			);
			this.cards_manager.$cards[2].set_value_color(
				this.bank_statement_closing_balance - this.cleared_balance == 0
					? "text-success"
					: "text-danger"
			);
		});
	}

	get_cleared_balance() {
		if (this.bank_account && this.bank_statement_to_date) {
			return frappe.call({
				method:
					"verp.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool.get_account_balance",
				args: {
					bank_account: this.bank_account,
					till_date: this.bank_statement_to_date,
				},
				callback: (response) =>
					(this.cleared_balance = response.message),
			});
		}
	}
};