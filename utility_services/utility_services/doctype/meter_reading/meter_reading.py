# Copyright (c) 2025, sagar and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class MeterReading(Document):

	def before_insert(self):
		self.calculate_total_unit_consumed()


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
	
