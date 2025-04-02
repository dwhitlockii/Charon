# Scheduler Documentation

## Overview

The Scheduler module in Charon provides time-based scheduling for firewall rules and other actions. It allows rules to be automatically enabled or disabled based on time, day of the week, or recurring schedules.

## Key Components

### Scheduler

The base scheduler provides a generic task scheduling system:

- **Task Management**: Add, remove, and list scheduled tasks
- **Time-based Execution**: Execute tasks at specific times or intervals
- **Recurring Schedules**: Tasks can run on specific days of the week
- **Persistence**: Save and load scheduler configuration from files

### Firewall Scheduler

Built on top of the base scheduler, the firewall scheduler specifically handles scheduling firewall rules:

- **Rule Scheduling**: Schedule rules to be enabled or disabled at specific times
- **Recurring Rules**: Define rules that are active only during certain hours on certain days
- **Integration**: Works with the database module to update rule status

## Basic Concepts

### Tasks

A task represents a scheduled action and includes:

- A name for identification
- A callback function to execute
- Arguments for the callback
- Timing parameters (start time, end time, days, interval)
- Enabled status

### Scheduling Rules

Rules can be scheduled in multiple ways:

- **One-time Schedule**: Enable or disable a rule at a specific date and time
- **Recurring Schedule**: Enable a rule on specific days of the week during specific hours
- **Temporary Rules**: Rules that are automatically disabled after a certain period

## Usage

### Basic Scheduler

```python
from charon.src.scheduler.scheduler import Scheduler, Task

# Create a scheduler
scheduler = Scheduler()

# Define a task
def my_task(arg1, arg2):
    print(f"Task executed with {arg1} and {arg2}")

# Schedule the task
task = Task(
    name="example_task",
    callback=my_task,
    args=["value1", "value2"],
    interval=60,  # Run every 60 seconds
    enabled=True
)

# Add the task to the scheduler
scheduler.add_task(task)

# Start the scheduler
scheduler.start()
```

### Firewall Scheduler

```python
from charon.src.scheduler.firewall_scheduler import FirewallScheduler
from charon.src.db.database import Database
import datetime

# Connect to the database
db = Database()
db.connect()

# Create a firewall scheduler
firewall_scheduler = FirewallScheduler(db=db)

# Schedule a rule to be enabled at a specific time
firewall_scheduler.schedule_rule_enable(
    rule_id=123,
    name="enable_ssh",
    start_time=datetime.datetime(2023, 12, 31, 8, 0),  # 8:00 AM on Dec 31
    end_time=datetime.datetime(2023, 12, 31, 17, 0)    # 5:00 PM on Dec 31
)

# Schedule a recurring rule (Monday-Friday, 9 AM to 5 PM)
firewall_scheduler.schedule_recurring_rule(
    rule_id=456,
    name="business_hours",
    days=[0, 1, 2, 3, 4],  # Monday-Friday
    start_time=datetime.time(9, 0),  # 9:00 AM
    end_time=datetime.time(17, 0)    # 5:00 PM
)

# Cancel a scheduled rule
firewall_scheduler.cancel_schedule("business_hours")

# List all scheduled rules
scheduled_rules = firewall_scheduler.list_scheduled_rules()
```

## Examples

### Parental Controls

```python
from charon.src.scheduler.firewall_scheduler import FirewallScheduler
import datetime

# Create a firewall scheduler
scheduler = FirewallScheduler()

# Schedule internet access for kids (Monday-Friday, 4 PM to 8 PM)
scheduler.schedule_recurring_rule(
    rule_id=789,  # Assuming this rule allows internet access for kids' devices
    name="kids_internet",
    days=[0, 1, 2, 3, 4],  # Monday-Friday
    start_time=datetime.time(16, 0),  # 4:00 PM
    end_time=datetime.time(20, 0)     # 8:00 PM
)

# Weekend schedule (Saturday-Sunday, 10 AM to 9 PM)
scheduler.schedule_recurring_rule(
    rule_id=789,
    name="kids_weekend",
    days=[5, 6],  # Saturday-Sunday
    start_time=datetime.time(10, 0),  # 10:00 AM
    end_time=datetime.time(21, 0)     # 9:00 PM
)
```

### Temporary Access

```python
from charon.src.scheduler.firewall_scheduler import FirewallScheduler
import datetime

# Create a firewall scheduler
scheduler = FirewallScheduler()

# Grant temporary access to a guest (for the next 2 hours)
now = datetime.datetime.now()
end_time = now + datetime.timedelta(hours=2)

scheduler.schedule_rule_enable(
    rule_id=567,  # Assuming this rule allows access for a guest
    name="guest_access",
    start_time=now,
    end_time=end_time
)
```

## Technical Details

### Thread Safety

The scheduler runs in a separate thread to avoid blocking the main application. All operations on the scheduler are thread-safe.

### Persistence

The scheduler configuration is saved to a JSON file, which allows scheduled tasks to persist across restarts of the application.

### Integration with Database

The firewall scheduler integrates with the database to:
- Update rule status (enabled/disabled)
- Apply time-based rules from the database
- Log scheduled operations 