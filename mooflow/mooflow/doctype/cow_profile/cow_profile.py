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
	
	def validate(self):
		"""Validate and populate child table with readings"""
		if not self.flags.get('ignore_child_table_population'):
			self.force_populate_readings_child_table()
	
	def onload(self):
		"""Load standalone readings into child table for display"""
		self.load_standalone_readings()
		self.populate_child_table_readings()
	
	def on_update(self):
		self.update_barn_occupancy()
	
	def set_cow_id(self):
		if not self.cow_id:
			self.cow_id = self.name
	
	def update_calculated_fields(self):
		self.calculate_age_months()
		self.calculate_current_weight()
		self.calculate_total_milk_produced()
	
	def calculate_age_months(self):
		if self.birth_date:
			birth_date = getdate(self.birth_date)
			today_date = getdate(today())
			delta = relativedelta(today_date, birth_date)
			self.age_months = delta.years * 12 + delta.months
	
	def calculate_current_weight(self):
		weight_readings = [r for r in self.readings if r.reading_type == "Body Weight" and r.numeric_value]
		if weight_readings:
			latest_reading = max(weight_readings, key=lambda x: x.reading_date)
			self.current_weight = latest_reading.numeric_value
	
	def calculate_total_milk_produced(self):
		milk_readings = [r for r in self.readings if r.reading_type == "Daily Milk Yield" and r.numeric_value]
		self.total_milk_produced = sum(r.numeric_value for r in milk_readings)
	
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
	
	def load_standalone_readings(self):
		"""Load standalone Cow Reading Items into the readings child table for display"""
		
		# Get standalone readings for this cow
		standalone_readings = frappe.get_list(
			"Cow Reading Item",
			filters={"cow": self.name},
			fields=[
				"name", "reading_date", "reading_type", "numeric_value", 
				"text_value", "boolean_value", "select_value", "unit",
				"alert_triggered", "alert_severity", "validation_status", 
				"quality_score", "notes"
			],
			order_by="reading_date desc",
			limit=50  # Show latest 50 readings in child table
		)
		
		# Clear existing child table
		self.readings = []
		
		# Populate child table with standalone readings data
		for reading in standalone_readings:
			child_row = self.append("readings", {})
			
			# Copy key fields to child table
			child_row.reading_date = reading.reading_date
			child_row.reading_type = reading.reading_type
			child_row.numeric_value = reading.numeric_value
			child_row.text_value = reading.text_value
			child_row.boolean_value = reading.boolean_value
			child_row.select_value = reading.select_value
			child_row.unit = reading.unit
			child_row.alert_triggered = reading.alert_triggered
			child_row.alert_severity = reading.alert_severity
			child_row.validation_status = reading.validation_status
			child_row.quality_score = reading.quality_score
			child_row.notes = reading.notes
			
			# Store reference to standalone reading
			child_row.name = reading.name
	
	def populate_child_table_readings(self):
		"""Force populate child table with standalone readings for immediate UI display"""
		try:
			# Get recent standalone readings
			standalone_readings = frappe.db.sql("""
				SELECT name, reading_date, reading_type, numeric_value, unit,
				       alert_triggered, alert_severity, validation_status, 
				       quality_score, notes, method
				FROM `tabCow Reading Item`
				WHERE cow = %s
				ORDER BY reading_date DESC, creation DESC
				LIMIT 15
			""", (self.name,), as_dict=True)
			
			if not standalone_readings:
				return
			
			# Clear existing child table data
			self.readings = []
			
			# Populate with fresh data
			for reading in standalone_readings:
				row = self.append("readings", {})
				row.reading_date = reading.reading_date
				row.reading_type = reading.reading_type
				row.numeric_value = reading.numeric_value
				row.unit = reading.unit or ""
				row.notes = reading.notes or ""
				row.method = reading.method or "Manual"
				row.is_valid = 1
				row.alert_triggered = reading.alert_triggered or 0
				row.alert_severity = reading.alert_severity or ""
				row.validation_status = reading.validation_status or "Valid"
				row.quality_score = reading.quality_score or 0.0
				row.cow = self.name  # Ensure parent reference
			
		except Exception as e:
			frappe.log_error(f"Error populating child table for {self.name}: {str(e)}", "Child Table Population")
	
	def force_populate_readings_child_table(self):
		"""Force populate child table - called from validate to ensure it always runs"""
		try:
			# Only populate if we don't already have readings in child table
			# or if we have fewer readings than standalone
			standalone_count = frappe.db.count("Cow Reading Item", {"cow": self.name})
			current_child_count = len(self.readings) if self.readings else 0
			
			if standalone_count > current_child_count:
				# Get the latest readings
				latest_readings = frappe.db.sql("""
					SELECT name, reading_date, reading_type, numeric_value, unit,
					       alert_triggered, alert_severity, validation_status, 
					       quality_score, notes, method, text_value, boolean_value, select_value
					FROM `tabCow Reading Item`
					WHERE cow = %s
					ORDER BY reading_date DESC, creation DESC
					LIMIT 20
				""", (self.name,), as_dict=True)
				
				# Clear and repopulate
				self.readings = []
				
				for reading in latest_readings:
					child_row = self.append("readings", {})
					child_row.reading_date = reading.reading_date
					child_row.reading_type = reading.reading_type
					child_row.numeric_value = reading.numeric_value
					child_row.text_value = reading.text_value
					child_row.boolean_value = reading.boolean_value  
					child_row.select_value = reading.select_value
					child_row.unit = reading.unit or ""
					child_row.notes = reading.notes or ""
					child_row.method = reading.method or "Manual"
					child_row.is_valid = 1
					child_row.alert_triggered = reading.alert_triggered or 0
					child_row.alert_severity = reading.alert_severity or ""
					child_row.validation_status = reading.validation_status or "Valid"
					child_row.quality_score = reading.quality_score or 0.0
					child_row.cow = self.name
					
					# Store reference to original standalone reading
					child_row.name = reading.name
				
				frappe.msgprint(f"Loaded {len(self.readings)} readings into child table", alert=True)
				
		except Exception as e:
			frappe.log_error(f"Error in force_populate_readings_child_table for {self.name}: {str(e)}", "Force Child Table Population")
			# Don't fail the entire save operation
			pass