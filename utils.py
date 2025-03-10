import json
import os
from datetime import datetime
import re
from typing import List, Dict, Optional, Callable

class Logger:
    def __init__(self, max_history: int = 500):
        """Initialize the logger.
        
        Args:
            max_history (int): Maximum number of log entries to keep in history
        """
        self.max_history = max_history
        self.history: List[tuple] = []
        self.callbacks: List[Callable] = []

    def log(self, message: str, level: str = "INFO") -> None:
        """Add a log entry.
        
        Args:
            message (str): The log message
            level (str): Log level (INFO, WARNING, ERROR, SUCCESS, DEBUG)
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = (f"[{timestamp}] [{level}] {message}", level)
        
        # Add to history
        self.history.append(entry)
        
        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]
        
        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(entry)
            except Exception as e:
                print(f"Error in log callback: {str(e)}")

    def clear(self) -> None:
        """Clear all log history."""
        self.history = []

    def get_logs(self, level: Optional[str] = None) -> List[str]:
        """Get filtered log entries.
        
        Args:
            level (str, optional): Filter logs by this level. If None, return all logs.
            
        Returns:
            List[str]: List of filtered log messages
        """
        if level and level != "ALL":
            return [msg for msg, lvl in self.history if lvl == level]
        return [msg for msg, _ in self.history]

    def save_to_file(self, filepath: str) -> None:
        """Save logs to a file.
        
        Args:
            filepath (str): Path to save the log file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for message, _ in self.history:
                    f.write(message + "\n")
        except Exception as e:
            self.log(f"Error saving logs to file: {str(e)}", level="ERROR")

    def add_callback(self, callback: Callable) -> None:
        """Add a callback function to be called for each new log entry.
        
        Args:
            callback (callable): Function to call with each new log entry
        """
        if callable(callback) and callback not in self.callbacks:
            self.callbacks.append(callback)

    def remove_callback(self, callback: Callable) -> None:
        """Remove a callback function.
        
        Args:
            callback (callable): Function to remove from callbacks
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)

class ConfigManager:
    def __init__(self, config_file: str, logger: Optional[Logger] = None):
        """Initialize the configuration manager.
        
        Args:
            config_file (str): Path to the configuration file
            logger (Logger, optional): Logger instance for logging
        """
        self.config_file = config_file
        self.logger = logger
        self.config: Dict = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                if self.logger:
                    self.logger.log("Configuration loaded successfully", level="INFO")
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error loading configuration: {str(e)}", level="ERROR")
            self.config = {}

    def save_config(self) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
            if self.logger:
                self.logger.log("Configuration saved successfully", level="INFO")
        except Exception as e:
            if self.logger:
                self.logger.log(f"Error saving configuration: {str(e)}", level="ERROR")

    def get(self, key: str, default=None):
        """Get a configuration value.
        
        Args:
            key (str): Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            The configuration value or default
        """
        return self.config.get(key, default)

    def set(self, key: str, value) -> None:
        """Set a configuration value.
        
        Args:
            key (str): Configuration key
            value: Value to set
        """
        self.config[key] = value

    def delete(self, key: str) -> None:
        """Delete a configuration value.
        
        Args:
            key (str): Configuration key to delete
        """
        if key in self.config:
            del self.config[key]

class HTMLFormatter:
    def __init__(self):
        """Initialize the HTML formatter."""
        self.heading_pattern = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)
        self.list_pattern = re.compile(r'^\s*[-*+]\s+(.+)$', re.MULTILINE)
        self.paragraph_pattern = re.compile(r'([^\n]+?)(?:\n\n|$)')

    def format_content(self, content: str) -> str:
        """Format content into structured HTML.
        
        Args:
            content (str): Raw content to format
            
        Returns:
            str: Formatted HTML content
        """
        try:
            # Clean up whitespace
            content = content.strip()
            content = re.sub(r'\n{3,}', '\n\n', content)
            
            # Convert headings
            content = self.heading_pattern.sub(lambda m: f'<h2>{m.group(1)}</h2>', content)
            
            # Convert lists
            content = self.list_pattern.sub(lambda m: f'<li>{m.group(1)}</li>', content)
            content = re.sub(r'(<li>.*?</li>\n*)+', r'<ul>\n\g<0></ul>', content, flags=re.DOTALL)
            
            # Convert paragraphs
            content = self.paragraph_pattern.sub(lambda m: f'<p>{m.group(1)}</p>\n<p></p>\n', content)
            
            # Clean up empty paragraphs
            content = re.sub(r'(<p></p>\s*){2,}', '<p></p>\n', content)
            
            return content.strip()
            
        except Exception as e:
            return f'<p>Error formatting content: {str(e)}</p>'

    def sanitize_html(self, html: str) -> str:
        """Sanitize HTML content.
        
        Args:
            html (str): HTML content to sanitize
            
        Returns:
            str: Sanitized HTML content
        """
        try:
            # Remove potentially harmful tags
            html = re.sub(r'<script.*?>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<style.*?>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r'<iframe.*?>.*?</iframe>', '', html, flags=re.DOTALL | re.IGNORECASE)
            
            # Clean up whitespace
            html = re.sub(r'\s+', ' ', html)
            
            # Ensure proper spacing between elements
            html = re.sub(r'</h[1-6]>\s*<h[1-6]>', lambda m: m.group(0) + '\n<p></p>\n', html)
            html = re.sub(r'</p>\s*<p>', '</p>\n<p></p>\n<p>', html)
            html = re.sub(r'</ul>\s*<', '</ul>\n<p></p>\n<', html)
            
            return html.strip()
            
        except Exception as e:
            return f'<p>Error sanitizing HTML: {str(e)}</p>'

    def extract_text(self, html: str) -> str:
        """Extract plain text from HTML content.
        
        Args:
            html (str): HTML content
            
        Returns:
            str: Plain text content
        """
        try:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', '', html)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            return f"Error extracting text: {str(e)}"
