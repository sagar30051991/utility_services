# Copyright (c) 2025, sagar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MeterReading(Document):

	def validate(self):
		self.calculate_total_unit_consumed()

	def on_submit(self):
		self.creating_item_price()

		self.create_sales_invoice()

	def calculate_total_unit_consumed(self):

		previous_reading = None

		previous_entries = frappe.db.get_all("Meter Reading",filters={"meter_number":self.meter_number,"name":["!=",self.name]},fields=["current_reading"],order_by="creation desc",limit=1)

		if previous_entries:
			previous_reading = previous_entries[0]["current_reading"]
			self.previous_reading_unit = previous_reading
		else:
			previous_reading = frappe.db.get_value("Meter",self.meter_number,"previous_reading")
			self.previous_reading_unit = previous_reading
		
		try:
			prev_reading = float(previous_reading)
			cur_reading = float(self.current_reading)
		except (ValueError,TypeError):
			frappe.throw("Kindly enter a valid number.")
		
		total = cur_reading - prev_reading
		if total < 0:
			frappe.throw("Current reading cannot be less than previous reading.")

		self.total_unit_consumed = total



	def creating_item_price(self):

		total_unit = self.total_unit_consumed

		customer_name = frappe.db.sql(
			"""
			SELECT
			  cm.name,cm.default_price_list,cm.custom_rate_plan,cm.custom_is_fixed_rate 
			FROM
				`tabUtility Services` as us
			LEFT JOIN
				`tabCustomer` as cm
			ON
				us.parent = cm.name
			WHERE 
				us.meter = '%s'

			"""%(self.meter_number),as_dict=1
		)	

		rate_config = frappe.get_doc("Rate Configuration",customer_name[0]['custom_rate_plan'])

		rate = None

		if rate_config.is_fixed and customer_name[0]['custom_is_fixed_rate'] == 1:
			rate = rate_config.fixed_rate
		else:
			for configs in rate_config.reading_rate_configuration:
				if float(configs.from_value) <= total_unit <= float(configs.to_value):
					rate = self.total_unit_consumed * configs.rate

		meter_details = frappe.get_value("Meter",self.meter_number,["utility_service"],as_dict=1)

		new_action = {
			'doctype':'Item Price',
			'docstatus':1,
			'packing_unit':self.total_unit_consumed,
			'valid_from' : frappe.utils.now_datetime(),
			'date_of_action':frappe.utils.now(),
			'item_code' : meter_details["utility_service"],
			'customer' : customer_name[0]['name'],
			'price_list' : customer_name[0]["default_price_list"],
			'selling' : 1,
			'price_list_rate' : rate
		}

		frappe.get_doc(new_action).insert(ignore_permissions=True)

		# frappe.log_error(title={"Customer"},message=frappe.as_json(rate_config))	
		# frappe.log_error(title={"Meter details"},message=frappe.as_json(meter_details))	
	
	def create_sales_invoice(self):

		
		customer_name = frappe.db.sql(
			"""
			SELECT
				cm.name,cm.custom_is_fixed_rate,cm.custom_rate_plan
			FROM
				`tabUtility Services` as us
			LEFT JOIN 
				`tabCustomer` as cm
			ON
				us.parent = cm.name
			WHERE
				us.meter = '%s'
			"""%(self.meter_number),as_dict=1
		)

		item_price_details = frappe.db.get_all("Item Price",filters={"customer":customer_name[0]['name']},fields=["*"],order_by="creation desc",limit=1)

		rate_config = frappe.get_doc("Rate Configuration")

		rate = None
		qty = None
		if customer_name[0]['custom_is_fixed_rate'] == 1:
			rate = item_price_details[0]["price_list_rate"]
			qty = 1
		else:
			qty = self.total_unit_consumed
			rate_config = frappe.get_doc("Rate Configuration",customer_name[0]['custom_rate_plan'])
			for configs in rate_config.reading_rate_configuration:
				if configs.from_value <= item_price_details[0]["packing_unit"] <= configs.to_value:
						rate = configs.rate


		sales_invoice_data = {
			'doctype':'Sales Invoice',
			'customer':item_price_details[0]["customer"],
			'posting_date': frappe.utils.nowdate(),
			'posting_time' : frappe.utils.nowtime(),
			'grand_total' : item_price_details[0]["price_list_rate"],
			'rounded_total' : item_price_details[0]["price_list_rate"],
			'total' : item_price_details[0]["price_list_rate"],
			'items' : [{
				'item_code' : item_price_details[0]["item_code"],
				'qty' : qty,
				'rate': rate
			}]  
		}

		frappe.get_doc(sales_invoice_data).insert(ignore_permissions=True)