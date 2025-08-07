# Copyright (c) 2025, sagar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MeterReading(Document):

	def before_insert(self):
		self.calculate_total_unit_consumed()

	def validate(self):
		self.creating_item_price()

	def calculate_total_unit_consumed(self):

		previous_reading = self.previous_reading_unit

		
		if previous_reading is None:
			frappe.throw("Previous reading not found.")
		
		try:
			prev_reading = float(previous_reading)
			current_reading = float(self.current_reading)
		except (ValueError,TypeError):
			frappe.throw("Meter reading must be a valid integer.")

		total = current_reading - prev_reading

		if total < 0:
			frappe.throw("Current reading cannot be less than previous reading.")

		self.total_unit_consumed = total
		self.previous_reading_unit = frappe.db.get_value("Meter",self.meter_number,"previous_reading")

		frappe.db.set_value("Meter",self.meter_number,"previous_reading",current_reading)

	
	# def creating_item_price(self):

	# 	total_unit = self.total_unit_consumed

	# 	rate_config = frappe.get_doc("Rate configuration")

	# 	rate = None

	# 	for configs in rate_config.reading_rate_configuration:
	# 		if configs.range:
	# 			min_value,max_value = [float(unit.strip()) for unit in configs.range.split("-")]
	# 			if min_value <= total_unit <= max_value:
	# 				rate = self.total_unit_consumed * configs.rate

	# 	doc_customer = frappe.get_doc("Customer",filters={"custom_utility_services"})

	# 	parent = frappe.db.sql(
	# 		"""
	# 		SELECT
	# 		  * 
	# 		FROM
	# 			`tabUtility Services` 
	# 		"""
	# 	)		
	
