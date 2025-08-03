# Copyright (c) 2025, MooFlow and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now


class CowReadingItem(Document):
	def before_insert(self):
		"""Set default values before inserting"""
		if not self.reading_date:
			self.reading_date = now()
		if not self.recorded_by:
			self.recorded_by = frappe.session.user
		if not self.method:
			self.method = "Manual"
	
	def after_insert(self):
		"""Process intelligence after inserting reading"""
		self.process_intelligence()
	
	def on_update(self):
		"""Process intelligence when reading is updated"""
		# Only process if values changed AND we haven't already processed (avoid duplicates)
		if (self.has_value_changed(['numeric_value', 'text_value', 'boolean_value', 'select_value']) 
			and not getattr(self, '_intelligence_processed', False)):
			self.process_intelligence()
	
	def process_intelligence(self):
		"""Apply intelligence processing to this reading"""
		try:
			# Mark as processed to avoid duplicate processing
			self._intelligence_processed = True
			
			# Only process if we have a numeric value (most intelligence is for numeric readings)
			if self.numeric_value is not None:
				from mooflow.intelligence_engine import process_reading_with_intelligence
				process_reading_with_intelligence(self)
				
				# Show real-time alert messages to user (only once)
				self.show_alert_messages()
				
				# Save the updated intelligence fields
				self.db_update()
				
				# Trigger automation rules if alerts were generated
				if self.alert_triggered:
					from mooflow.intelligence_engine import trigger_automated_actions
					trigger_automated_actions(self)
			
		except Exception as e:
			frappe.log_error(f"Intelligence processing failed for reading {self.name}: {str(e)}", "MooFlow Intelligence")
			# Don't fail the save operation due to intelligence processing errors
			pass
	
	def show_alert_messages(self):
		"""Show real-time messages to the user when alerts are triggered"""
		
		if self.alert_triggered and self.alert_message:
			cow_name = frappe.db.get_value("Cow Profile", self.cow, "cow_name") or "Unknown Cow"
			
			# Show appropriate message based on severity
			if self.alert_severity == "Critical":
				frappe.msgprint(
					f"🚨 <strong>CRITICAL ALERT</strong><br><br>"
					f"<strong>Cow:</strong> {cow_name}<br>"
					f"<strong>Reading:</strong> {self.reading_type} = {self.numeric_value}<br>"
					f"<strong>Issue:</strong> {self.alert_message}<br><br>"
					f"<em>Immediate attention required!</em>",
					title="Critical Health Alert",
					indicator="red"
				)
			elif self.alert_severity == "High":
				frappe.msgprint(
					f"⚠️ <strong>HIGH PRIORITY ALERT</strong><br><br>"
					f"<strong>Cow:</strong> {cow_name}<br>"
					f"<strong>Reading:</strong> {self.reading_type} = {self.numeric_value}<br>"
					f"<strong>Issue:</strong> {self.alert_message}<br><br>"
					f"<em>Action recommended within 24 hours</em>",
					title="High Priority Alert",
					indicator="orange"
				)
			elif self.alert_severity in ["Medium", "Low"]:
				frappe.msgprint(
					f"ℹ️ <strong>ALERT NOTIFICATION</strong><br><br>"
					f"<strong>Cow:</strong> {cow_name}<br>"
					f"<strong>Reading:</strong> {self.reading_type} = {self.numeric_value}<br>"
					f"<strong>Note:</strong> {self.alert_message}",
					title=f"{self.alert_severity} Priority Alert",
					indicator="blue"
				)
		
		# Also show quality score information for very low scores
		if hasattr(self, 'quality_score') and self.quality_score is not None and self.quality_score < 0.5:
			cow_name = frappe.db.get_value("Cow Profile", self.cow, "cow_name") or "Unknown Cow"
			frappe.msgprint(
				f"📊 <strong>DATA QUALITY NOTICE</strong><br><br>"
				f"<strong>Cow:</strong> {cow_name}<br>"
				f"<strong>Reading:</strong> {self.reading_type} = {self.numeric_value}<br>"
				f"<strong>Quality Score:</strong> {self.quality_score:.2f}/1.0<br><br>"
				f"<em>This reading may need verification due to low quality score.</em>",
				title="Data Quality Alert",
				indicator="yellow"
			)