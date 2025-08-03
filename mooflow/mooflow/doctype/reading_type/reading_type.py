# Copyright (c) 2025, MooFlow and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ReadingType(Document):
	def before_save(self):
		"""Ensure stage ranges are properly saved"""
		if self.use_stage_specific_ranges:
			self.validate_stage_ranges()
	
	def validate_stage_ranges(self):
		"""Validate and ensure stage ranges are properly configured"""
		if not self.stage_ranges:
			# If no stage ranges but flag is enabled, create default ones
			self.create_default_stage_ranges()
	
	def create_default_stage_ranges(self):
		"""Create default stage ranges if none exist"""
		# Get available lifecycle stages
		lifecycle_stages = frappe.get_list("Lifecycle Stage", fields=["name", "stage_name"])
		
		if not lifecycle_stages:
			return  # No stages to create ranges for
		
		# Clear existing ranges
		self.stage_ranges = []
		
		# Add default ranges based on reading type
		for stage in lifecycle_stages:
			stage_row = self.append("stage_ranges", {})
			stage_row.lifecycle_stage = stage.name
			
			# Set defaults based on reading type and stage
			if "Temperature" in self.reading_name:
				if "Calf" in stage.stage_name:
					stage_row.stage_normal_min = 38.0
					stage_row.stage_normal_max = 39.5
					stage_row.stage_critical_min = 36.0
					stage_row.stage_critical_max = 41.0
					stage_row.stage_target_value = 38.8
				else:
					stage_row.stage_normal_min = 37.5
					stage_row.stage_normal_max = 39.0
					stage_row.stage_critical_min = 35.0
					stage_row.stage_critical_max = 41.5
					stage_row.stage_target_value = 38.2
			else:
				# Generic defaults
				stage_row.stage_normal_min = self.normal_range_min or 0
				stage_row.stage_normal_max = self.normal_range_max or 100
				stage_row.stage_critical_min = self.critical_low_threshold or 0
				stage_row.stage_critical_max = self.critical_high_threshold or 200
				stage_row.stage_target_value = (stage_row.stage_normal_min + stage_row.stage_normal_max) / 2
			frappe.db.commit()
	
	def validate(self):
		"""Validate and ensure stage ranges work correctly"""
		if self.use_stage_specific_ranges:
			self.ensure_stage_ranges_exist()
