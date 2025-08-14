# Copyright (c) 2025, MooFlow and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, date_diff, getdate
from dateutil.relativedelta import relativedelta


class CowProfile(Document):
	def before_save(self):
		self.update_calculated_fields()
		self.validate_birth_date()
		self.validate_barn_capacity()
		self.set_cow_id()

	
	def on_update(self):
		self.update_barn_occupancy()
	
	def set_cow_id(self):
		if not self.cow_id:
			self.cow_id = self.name
	
	def update_calculated_fields(self):
		self.calculate_age_months()
	
	# def calculate_age_months(self):
	# 	if self.birth_date:
	# 		birth_date = getdate(self.birth_date)
	# 		today_date = getdate(today())
	# 		delta = relativedelta(today_date, birth_date)
	# 		self.age_months = delta.years * 12 + delta.months
	
	# def calculate_current_weight(self):
	# 	weight_readings = [r for r in self.readings if r.reading_type == "Body Weight" and r.numeric_value]
	# 	if weight_readings:
	# 		latest_reading = max(weight_readings, key=lambda x: x.reading_date)
	# 		self.current_weight = latest_reading.numeric_value
	
	
	def validate_birth_date(self):
		if self.birth_date and getdate(self.birth_date) > getdate(today()):
			frappe.throw("Birth date cannot be in the future")
	
	def validate_barn_capacity(self):
		if self.current_barn:
			barn = frappe.get_doc("Barn", self.current_barn)
			current_count = frappe.db.count("Cow Profile", {
				"current_barn": self.current_barn,
				"status": "Active",
				"name": ["!=", self.name]
			})
			if current_count >= barn.capacity:
				frappe.throw(f"Barn {self.current_barn} has reached its capacity of {barn.capacity}")
	
	def update_barn_occupancy(self):
		if self.current_barn:
			barn = frappe.get_doc("Barn", self.current_barn)
			barn.update_current_occupancy()