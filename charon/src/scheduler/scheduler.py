#!/usr/bin/env python3
"""
Scheduler Module for Charon Firewall

This module provides time-based scheduling for firewall rules.
"""

import logging
import threading
import time
import datetime
import json
import os
from typing import Dict, List, Optional, Callable, Any

logger = logging.getLogger('charon.scheduler')

class Task:
    """Represents a scheduled task."""
    
    def __init__(self, name: str, callback: Callable, args: List = None, kwargs: Dict = None,
                 start_time: Optional[datetime.datetime] = None,
                 end_time: Optional[datetime.datetime] = None,
                 days: Optional[List[int]] = None,
                 interval: Optional[int] = None,
                 enabled: bool = True):
        """Initialize a scheduled task.
        
        Args:
            name: Name of the task
            callback: Function to call when the task is executed
            args: Positional arguments for the callback
            kwargs: Keyword arguments for the callback
            start_time: When the task should start (None for immediately)
            end_time: When the task should end (None for never)
            days: Days of the week to run (0-6, where 0 is Monday)
            interval: Interval in seconds between executions
            enabled: Whether the task is enabled
        """
        self.name = name
        self.callback = callback
        self.args = args or []
        self.kwargs = kwargs or {}
        self.start_time = start_time
        self.end_time = end_time
        self.days = days  # None means every day
        self.interval = interval  # None means run once
        self.enabled = enabled
        self.last_run = None
    
    def should_run(self) -> bool:
        """Check if the task should run now.
        
        Returns:
            bool: True if the task should run, False otherwise
        """
        if not self.enabled:
            return False
            
        now = datetime.datetime.now()
        
        # Check if we're in the valid time range
        if self.start_time and now < self.start_time:
            return False
        if self.end_time and now > self.end_time:
            return False
            
        # Check if it's the right day of the week
        if self.days is not None:
            if now.weekday() not in self.days:
                return False
                
        # For interval tasks, check if enough time has passed
        if self.interval is not None and self.last_run is not None:
            elapsed = (now - self.last_run).total_seconds()
            if elapsed < self.interval:
                return False
                
        return True
        
    def run(self) -> Any:
        """Execute the task.
        
        Returns:
            The result of the callback function
        """
        try:
            self.last_run = datetime.datetime.now()
            result = self.callback(*self.args, **self.kwargs)
            logger.info(f"Task '{self.name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing task '{self.name}': {e}")
            return None

class Scheduler:
    """Manages scheduled tasks."""
    
    def __init__(self, config_file: str = "/etc/charon/scheduler.json"):
        """Initialize the scheduler.
        
        Args:
            config_file: Path to the scheduler configuration file
        """
        self.config_file = config_file
        self.tasks: Dict[str, Task] = {}
        self.running = False
        self.thread = None
    
    def add_task(self, task: Task) -> bool:
        """Add a task to the scheduler.
        
        Args:
            task: The task to add
            
        Returns:
            bool: True if successful, False otherwise
        """
        if task.name in self.tasks:
            logger.warning(f"Task '{task.name}' already exists, replacing")
            
        self.tasks[task.name] = task
        logger.info(f"Added task '{task.name}'")
        return True
    
    def remove_task(self, name: str) -> bool:
        """Remove a task from the scheduler.
        
        Args:
            name: Name of the task to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if name not in self.tasks:
            logger.warning(f"Task '{name}' not found")
            return False
            
        del self.tasks[name]
        logger.info(f"Removed task '{name}'")
        return True
    
    def get_task(self, name: str) -> Optional[Task]:
        """Get a task by name.
        
        Args:
            name: Name of the task to get
            
        Returns:
            Task: The task or None if not found
        """
        return self.tasks.get(name)
    
    def list_tasks(self) -> List[Dict[str, Any]]:
        """Get a list of all tasks.
        
        Returns:
            List of task information dictionaries
        """
        result = []
        for name, task in self.tasks.items():
            task_info = {
                "name": name,
                "enabled": task.enabled,
                "start_time": task.start_time.isoformat() if task.start_time else None,
                "end_time": task.end_time.isoformat() if task.end_time else None,
                "days": task.days,
                "interval": task.interval,
                "last_run": task.last_run.isoformat() if task.last_run else None
            }
            result.append(task_info)
        return result
    
    def _run_loop(self) -> None:
        """Main scheduler loop."""
        while self.running:
            for name, task in list(self.tasks.items()):
                if task.should_run():
                    task.run()
                    
                    # If this is a one-time task, remove it after execution
                    if task.interval is None:
                        self.remove_task(name)
            
            # Sleep for a bit to avoid high CPU usage
            time.sleep(1)
    
    def start(self) -> bool:
        """Start the scheduler.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if self.running:
            logger.warning("Scheduler is already running")
            return False
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        
        logger.info("Scheduler started")
        return True
    
    def stop(self) -> bool:
        """Stop the scheduler.
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.running:
            logger.warning("Scheduler is not running")
            return False
            
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            
        logger.info("Scheduler stopped")
        return True
    
    def save_config(self) -> bool:
        """Save the scheduler configuration to a file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Convert tasks to serializable format
            tasks_config = {}
            for name, task in self.tasks.items():
                # Skip tasks that can't be serialized (custom callbacks)
                if not hasattr(task.callback, '__module__'):
                    continue
                    
                tasks_config[name] = {
                    "module": task.callback.__module__,
                    "function": task.callback.__name__,
                    "args": task.args,
                    "kwargs": task.kwargs,
                    "start_time": task.start_time.isoformat() if task.start_time else None,
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "days": task.days,
                    "interval": task.interval,
                    "enabled": task.enabled
                }
            
            with open(self.config_file, 'w') as f:
                json.dump(tasks_config, f, indent=2)
                
            logger.info(f"Scheduler configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save scheduler configuration: {e}")
            return False
    
    def load_config(self) -> bool:
        """Load the scheduler configuration from a file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.config_file):
                logger.warning(f"Configuration file {self.config_file} not found")
                return False
                
            with open(self.config_file, 'r') as f:
                tasks_config = json.load(f)
                
            for name, config in tasks_config.items():
                try:
                    module_name = config["module"]
                    function_name = config["function"]
                    
                    # Dynamically import the module and get the function
                    import importlib
                    module = importlib.import_module(module_name)
                    callback = getattr(module, function_name)
                    
                    # Parse datetime objects
                    start_time = None
                    if config["start_time"]:
                        start_time = datetime.datetime.fromisoformat(config["start_time"])
                        
                    end_time = None
                    if config["end_time"]:
                        end_time = datetime.datetime.fromisoformat(config["end_time"])
                    
                    # Create and add the task
                    task = Task(
                        name=name,
                        callback=callback,
                        args=config["args"],
                        kwargs=config["kwargs"],
                        start_time=start_time,
                        end_time=end_time,
                        days=config["days"],
                        interval=config["interval"],
                        enabled=config["enabled"]
                    )
                    
                    self.add_task(task)
                except Exception as e:
                    logger.error(f"Failed to load task '{name}': {e}")
            
            logger.info(f"Scheduler configuration loaded from {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to load scheduler configuration: {e}")
            return False 