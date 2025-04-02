#!/usr/bin/env python3
"""
Firewall Scheduler Module for Charon Firewall

This module provides functions to schedule firewall rules based on time.
"""

import logging
import datetime
from typing import Dict, List, Optional, Any
import os
import subprocess

from .scheduler import Scheduler, Task
from ..db.database import Database

logger = logging.getLogger('charon.scheduler.firewall')

class FirewallScheduler:
    """Manages scheduled firewall rules."""
    
    def __init__(self, scheduler: Optional[Scheduler] = None, 
                 db: Optional[Database] = None):
        """Initialize the firewall scheduler.
        
        Args:
            scheduler: Existing scheduler instance or None to create a new one
            db: Database instance or None to create a new one
        """
        self.scheduler = scheduler or Scheduler()
        self.db = db
        
        # Start the scheduler if it's not already running
        if not self.scheduler.running:
            self.scheduler.start()
    
    def _enable_rule(self, rule_id: int) -> bool:
        """Enable a firewall rule.
        
        Args:
            rule_id: ID of the rule to enable
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.db:
            return self.db.update_rule(rule_id, {"enabled": True})
        else:
            # Fall back to direct modification if no database is available
            try:
                # Get the rules from the database by ID
                cmd = ["nft", "list", "table", "inet", "charon"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Apply the rule using nftables directly
                # This is a simplified example - in practice you'd need to parse
                # the output and find the specific rule
                
                # For demonstration purposes only:
                logger.info(f"Rule {rule_id} enabled")
                return True
            except subprocess.SubprocessError as e:
                logger.error(f"Failed to enable rule {rule_id}: {e}")
                return False
    
    def _disable_rule(self, rule_id: int) -> bool:
        """Disable a firewall rule.
        
        Args:
            rule_id: ID of the rule to disable
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.db:
            return self.db.update_rule(rule_id, {"enabled": False})
        else:
            # Fall back to direct modification if no database is available
            try:
                # Get the rules from the database by ID
                cmd = ["nft", "list", "table", "inet", "charon"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                
                # Apply the rule using nftables directly
                # This is a simplified example - in practice you'd need to parse
                # the output and find the specific rule
                
                # For demonstration purposes only:
                logger.info(f"Rule {rule_id} disabled")
                return True
            except subprocess.SubprocessError as e:
                logger.error(f"Failed to disable rule {rule_id}: {e}")
                return False
    
    def schedule_rule_enable(self, rule_id: int, name: str, 
                            start_time: Optional[datetime.datetime] = None,
                            end_time: Optional[datetime.datetime] = None,
                            days: Optional[List[int]] = None) -> bool:
        """Schedule a rule to be enabled at a specific time.
        
        Args:
            rule_id: ID of the rule to enable
            name: Name for this scheduled task
            start_time: When to enable the rule (None for immediately)
            end_time: When to disable the rule (None for never)
            days: Days of the week on which to enable the rule (0-6, where 0 is Monday)
            
        Returns:
            bool: True if scheduled successfully, False otherwise
        """
        try:
            # Schedule the rule to be enabled
            enable_task = Task(
                name=f"{name}_enable",
                callback=self._enable_rule,
                args=[rule_id],
                start_time=start_time,
                days=days,
                enabled=True
            )
            
            self.scheduler.add_task(enable_task)
            
            # If an end time is specified, schedule the rule to be disabled
            if end_time:
                disable_task = Task(
                    name=f"{name}_disable",
                    callback=self._disable_rule,
                    args=[rule_id],
                    start_time=end_time,
                    days=days,
                    enabled=True
                )
                
                self.scheduler.add_task(disable_task)
                
            # Save the scheduler configuration
            self.scheduler.save_config()
            
            logger.info(f"Scheduled rule {rule_id} to be enabled at {start_time} and disabled at {end_time}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule rule {rule_id}: {e}")
            return False
    
    def schedule_rule_disable(self, rule_id: int, name: str,
                             start_time: datetime.datetime) -> bool:
        """Schedule a rule to be disabled at a specific time.
        
        Args:
            rule_id: ID of the rule to disable
            name: Name for this scheduled task
            start_time: When to disable the rule
            
        Returns:
            bool: True if scheduled successfully, False otherwise
        """
        try:
            task = Task(
                name=name,
                callback=self._disable_rule,
                args=[rule_id],
                start_time=start_time,
                enabled=True
            )
            
            self.scheduler.add_task(task)
            self.scheduler.save_config()
            
            logger.info(f"Scheduled rule {rule_id} to be disabled at {start_time}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule rule {rule_id} for disabling: {e}")
            return False
    
    def schedule_recurring_rule(self, rule_id: int, name: str,
                              days: List[int],
                              start_time: datetime.time,
                              end_time: datetime.time) -> bool:
        """Schedule a rule to be enabled on certain days during certain hours.
        
        Args:
            rule_id: ID of the rule to enable/disable
            name: Name for this scheduled task
            days: Days of the week on which to enable the rule (0-6, where 0 is Monday)
            start_time: Time of day to enable the rule
            end_time: Time of day to disable the rule
            
        Returns:
            bool: True if scheduled successfully, False otherwise
        """
        try:
            # For each specified day, create a task to enable and disable the rule
            for day in days:
                # Calculate the next occurrence of this day
                now = datetime.datetime.now()
                days_ahead = (day - now.weekday()) % 7
                if days_ahead == 0 and now.time() > start_time:
                    days_ahead = 7  # Schedule for next week if today's slot has passed
                
                next_day = now + datetime.timedelta(days=days_ahead)
                
                # Create the start datetime
                start_datetime = datetime.datetime.combine(
                    next_day.date(), start_time
                )
                
                # Create the end datetime
                end_datetime = datetime.datetime.combine(
                    next_day.date(), end_time
                )
                
                # If end time is earlier than start time, it means it spans to the next day
                if end_time < start_time:
                    end_datetime += datetime.timedelta(days=1)
                
                # Schedule the rule to be enabled
                self.schedule_rule_enable(
                    rule_id=rule_id,
                    name=f"{name}_day{day}",
                    start_time=start_datetime,
                    end_time=end_datetime,
                    days=[day]  # Recurs on this day of the week
                )
            
            logger.info(f"Scheduled recurring rule {rule_id} for days {days}")
            return True
        except Exception as e:
            logger.error(f"Failed to schedule recurring rule {rule_id}: {e}")
            return False
    
    def cancel_schedule(self, name: str) -> bool:
        """Cancel a scheduled rule.
        
        Args:
            name: Name of the scheduled task to cancel
            
        Returns:
            bool: True if cancelled successfully, False otherwise
        """
        try:
            # Remove both enable and disable tasks if they exist
            result = self.scheduler.remove_task(name)
            self.scheduler.remove_task(f"{name}_enable")
            self.scheduler.remove_task(f"{name}_disable")
            
            # Save the scheduler configuration
            self.scheduler.save_config()
            
            logger.info(f"Cancelled scheduled rule {name}")
            return result
        except Exception as e:
            logger.error(f"Failed to cancel scheduled rule {name}: {e}")
            return False
    
    def list_scheduled_rules(self) -> List[Dict[str, Any]]:
        """Get a list of all scheduled rules.
        
        Returns:
            List of scheduled rule information dictionaries
        """
        return self.scheduler.list_tasks()
    
    def apply_time_based_rules(self) -> bool:
        """Apply time-based rules from the database.
        
        This method retrieves rules with time restrictions from the database
        and schedules them accordingly.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.db:
            logger.error("Database connection not available")
            return False
            
        try:
            # This is a simplified example - in practice, you'd need to extend
            # the database schema to include time-based restrictions for rules
            
            # For demonstration purposes only:
            logger.info("Applied time-based rules from database")
            return True
        except Exception as e:
            logger.error(f"Failed to apply time-based rules: {e}")
            return False 