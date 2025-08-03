# Copyright (c) 2025, MooFlow and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Barn(Document):
	def on_update(self):
		self.update_current_occupancy()
	
	def update_current_occupancy(self):
		count = frappe.db.count("Cow Profile", {"current_barn": self.name, "status": "Active"})
		frappe.db.set_value("Barn", self.name, "current_occupancy", count)