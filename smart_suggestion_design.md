# MooFlow: Smart Suggestion Design

## Core Concept: 3-Step Automation

```
1. FILTER → Get list of cows based on criteria # {} cows -> {} filtered
2. EVALUATE → Apply rules to filtered cows  # apply rules -> get violations
3. SUGGEST → Auto-create actions for failed cows # suggest action for violations 
```

### **Smart Check Rule** (One Master DocType)

```python
{
    "doctype": "Smart Check Rule",
    "module": "MooFlow",
    "fields": [
        # Basic Info
        {"fieldname": "rule_name", "fieldtype": "Data", "label": "Rule Name", "reqd": 1},
        {"fieldname": "is_active", "fieldtype": "Check", "label": "Active", "default": 1},
        
        # When to Run
        {"fieldname": "schedule_time", "fieldtype": "Time", "label": "Run Time", "reqd": 1},
        {"fieldname": "schedule_frequency", "fieldtype": "Select", "label": "Frequency", 
         "options": "Daily\nWeekly\nMonthly", "default": "Daily"},
        
        # Step 1: FILTER - Who to check
        {"fieldname": "filter_expression", "fieldtype": "Code", "label": "Filter Expression", 
         "reqd": 1,
         "description": "Python expression to filter cows"},
        
        # Step 2: EVALUATE - What to check
        {"fieldname": "check_expression", "fieldtype": "Code", "label": "Check Expression", 
         "reqd": 1,
         "description": "Python expression returning True/False for each cow"},
        
        # Step 3: SUGGEST - What to do
        {"fieldname": "suggestion_logic", "fieldtype": "Code", "label": "Suggestion Logic", 
         "reqd": 1,
         "description": "Python code to determine suggested action"},
        
        # Results tracking
        {"fieldname": "last_run", "fieldtype": "Datetime", "label": "Last Run", "read_only": 1},
        {"fieldname": "last_failed_count", "fieldtype": "Int", "label": "Last Failed Count", "read_only": 1},
    ]
}
```


### **Filter Functions** (Available in expressions)
```python
# Available functions for filter_expression:

def in_barns(*barn_names):
    """Check if cow is in specified barns"""
    return f"current_barn in {list(barn_names)}"

def in_stages(*stage_names):
    """Check if cow is in specified lifecycle stages"""
    return f"current_stage in {list(stage_names)}"

def breed_type_is(*breed_names):
    """Check if cow breed is in specified types"""
    return f"breed_type in {list(breed_names)}"

def age_between(min_months, max_months):
    """Check if cow age is within range"""
    return f"{min_months} <= age_months <= {max_months}"

def days_in_milk_between(min_days, max_days):
    """Check if days in milk is within range"""
    return f"{min_days} <= days_in_milk <= {max_days}"

# Example filter expressions:
"in_barns('Milking Barn A', 'Milking Barn B') and in_stages('Lactating Cow')"
"breed_type_is('Holstein', 'Jersey') and age_between(24, 120)"
"current_barn == 'Hospital Barn' or health_status != 'Healthy'"
```

### **Check Functions** (Available in expressions)
```python
# Available functions for check_expression:

def last_readings(reading_type, count=5):
    """Get last N readings of specified type for current cow"""
    pass

def reading_count_above(reading_type, threshold, count=5):
    """Count how many of last N readings are above threshold"""
    # Returns: number of readings above threshold
    pass

def reading_count_below(reading_type, threshold, count=5):
    """Count how many of last N readings are below threshold"""
    pass

def reading_average(reading_type, count=5):
    """Get average of last N readings"""
    pass

def days_since_last_reading(reading_type):
    """Days since last reading of this type"""
    pass

def has_reading_within_days(reading_type, days):
    """Check if cow has reading within specified days"""
    pass

def reading_trend(reading_type, count=5):
    """Get trend: 'increasing', 'decreasing', 'stable'"""
    pass

# Example check expressions:
"reading_count_above('Daily Milk Yield', 20, 5) >= 3"  # 3 out of 5 readings > 20L
"reading_average('Daily Milk Yield', 7) > 25"  # 7-day average > 25L  
"days_since_last_reading('Body Weight') <= 7"  # Weighed within 7 days
```

### **Suggestion Functions** (Available in expressions)
```python
# Available functions for suggestion_logic:

def suggest_action(action_type, priority="Medium", notes=""):
    """Suggest specific action type"""
    pass

def smart_suggest():
    """Auto-determine best action based on what failed"""
    # Analyzes the failed check and suggests appropriate action
    pass

def suggest_based_on_reading(reading_type):
    """Suggest action based on specific reading type that failed"""
    mapping = {
        'Daily Milk Yield': 'Production Assessment',
        'Body Weight': 'Weight Check',
        'Body Temperature': 'Health Examination',
        'Appetite': 'Nutrition Assessment'
    }
    return mapping.get(reading_type, 'General Check')

# Example suggestion logic:
"suggest_action('Production Assessment', 'High', 'Low milk production detected')"
"smart_suggest()"  # System determines best action
```

## Real-World Examples

### **Example 1: Daily Milk Production Check**
```python
Rule Name: "Daily Production Monitor"
Schedule: Daily at 23:00

Filter Expression:
"in_stages('Lactating Cow') and in_barns('Milking Barn A', 'Milking Barn B')"

Check Expression:
"reading_count_above('Daily Milk Yield', 20, 5) >= 3"
# 3 out of last 5 readings must be above 20 liters

Suggestion Logic:
"suggest_action('Production Assessment', 'High', f'Only {reading_count_above(\"Daily Milk Yield\", 20, 5)} out of 5 recent readings above 20L')"
```

### **Example 2: Health Monitoring**
```python
Rule Name: "Weekly Health Check"
Schedule: Weekly

Filter Expression:
"status == 'Active' and age_months >= 6"

Check Expression:
"has_reading_within_days('General Health Status', 7)"
# Must have health reading within 7 days

Suggestion Logic:
"suggest_action('Health Examination', 'Critical', f'No health check for {days_since_last_reading(\"General Health Status\")} days')"
```

### **Example 3: Weight Monitoring**
```python
Rule Name: "Monthly Weight Check"
Schedule: Monthly

Filter Expression:
"in_stages('Growing Heifer', 'Breeding Heifer')"

Check Expression:
"days_since_last_reading('Body Weight') <= 30 and reading_trend('Body Weight', 3) != 'decreasing'"
# Must have weight reading within 30 days AND not losing weight

Suggestion Logic:
"smart_suggest()"  # System decides: Weight Check or Nutrition Assessment
```

### **Example 4: Feed Efficiency**
```python
Rule Name: "Feed Efficiency Monitor"
Schedule: Daily at 22:30

Filter Expression:
"in_stages('Lactating Cow') and days_in_milk_between(30, 300)"

Check Expression:
"reading_average('Daily Milk Yield', 7) / reading_average('Feed Consumption', 7) > 1.3"
# Feed conversion ratio should be > 1.3

Suggestion Logic:
"suggest_action('Nutrition Assessment', 'Medium', 'Poor feed conversion ratio')"
```