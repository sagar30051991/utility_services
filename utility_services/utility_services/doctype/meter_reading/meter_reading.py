# Copyright (c) 2025, sagar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MeterReading(Document):

	def before_insert(self):
		self.calculate_total_unit_consumed()


	def calculate_total_unit_consumed(self):

		# previous_reading_from_latest_reading = frappe.db.get_all(
		# 	'Meter Reading',
		# 	filters = {"meter_number":self.meter_number},
		# 	fields = ["meter_number","previous_reading_unit"],
		# 	order_by = "creation desc",
		# 	limit = 1
		# )

		# if (previous_reading_from_latest_reading and previous_reading_from_latest_reading[0]["previous_reading_unit"] != 0):
		# 	previous_reading = previous_reading_from_latest_reading[0]["previous_reading_unit"]
		# else:
		# 	previous_reading = frappe.db.get_value("Meter",self.meter_number,"previous_reading")

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
	
