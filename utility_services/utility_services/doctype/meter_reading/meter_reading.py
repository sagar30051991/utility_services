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

		rate_config = frappe.get_doc("Rate configuration")

		rate = None

		for configs in rate_config.reading_rate_configuration:
			if configs.range:
				min_value,max_value = [float(unit.strip()) for unit in configs.range.split("-")]
				if min_value <= total_unit <= max_value:
					rate = self.total_unit_consumed * configs.rate

		meter_details = frappe.get_value("Meter",self.meter_number,["utility_service"],as_dict=1)

		customer_name = frappe.db.sql(
			"""
			SELECT
			  cm.name,cm.default_price_list 
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

		# frappe.log_error(title={"Customer"},message=frappe.as_json(customer_name))	
		# frappe.log_error(title={"Meter details"},message=frappe.as_json(meter_details))	
	
	def create_sales_invoice(self):

		
		customer_name = frappe.db.sql(
			"""
			SELECT
				cm.name
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

		rate_config = frappe.get_doc("Rate configuration")

		rate = None

		for configs in rate_config.reading_rate_configuration:
			if configs.range:
				min_range,max_range = [float(x.strip()) for x in configs.range.split("-")]
				if min_range <= item_price_details[0]["packing_unit"] <= max_range:
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
				'qty' : item_price_details[0]["packing_unit"],
				'rate': rate
			}]  
		}

		frappe.get_doc(sales_invoice_data).insert(ignore_permissions=True)