import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime, timedelta
import os
import json
import threading
import re

from blogger_api import BloggerAPIHandler
from rewriter import ArticleRewriterEngine
from utils import Logger, ConfigManager, HTMLFormatter
import config

class ArticleRewriterUI(tk.Tk):
    def __init__(self):
        """Initialize the application UI."""
        super().__init__()

        # Initialize variables
        self._init_variables()
        
        # Initialize components
        self._init_window()
        self._init_styles()
        self._init_ui()
        
        # Initialize managers after UI
        self.logger = Logger(max_history=config.MAX_LOG_HISTORY)
        self.config_manager = ConfigManager(config.SETTINGS_FILE, self.logger)
        self.blogger_api = BloggerAPIHandler(self.logger.log)
        self.rewriter = ArticleRewriterEngine(logger_callback=self.logger.log)
        self.html_formatter = HTMLFormatter()
        
        # Load settings
        self.load_settings()
        
        # Initial log message
        self.logger.log("Application started", level="INFO")

    def _init_variables(self):
        """Initialize Tkinter variables and other attributes."""
        self.api_key_var = tk.StringVar()
        self.blog_var = tk.StringVar()
        self.blog_id_var = tk.StringVar()
        self.schedule_var = tk.StringVar(value="5")
        self.sitemap_url_var = tk.StringVar()
        self.auth_status_var = tk.StringVar(value="Not authenticated")
        self.creds_path_var = tk.StringVar()
        
        # Initialize other variables
        self.article_urls = {}
        self.rewritten_articles = {}
        self.article_schedules = {}
        self.hover_window = None
        
        # Schedule variables
        self.schedule_date_var = tk.StringVar()
        self.schedule_time_var = tk.StringVar()

    def _init_window(self):
        """Initialize the main window properties."""
        self.title(config.APP_NAME)
        self.geometry(config.APP_WINDOW_SIZE)
        self.configure(bg='#f0f0f0')

    def _init_styles(self):
        """Initialize custom styles for widgets."""
        style = ttk.Style()
        
        # Configure main theme
        style.configure(".",
            font=("Segoe UI", 10),
            background="#f0f0f0"
        )
        
        # Tab style
        style.configure("Custom.TNotebook",
            background="#2c3e50",
            padding=[5, 5],
            tabmargins=[0, 5, 0, 0]
        )
        style.configure("Custom.TNotebook.Tab",
            background="#34495e",
            foreground="white",
            padding=[15, 5],
            font=("Segoe UI", 10)
        )
        style.map("Custom.TNotebook.Tab",
            background=[("selected", "#2980b9")],
            foreground=[("selected", "white")]
        )
        
        # Frame style
        style.configure("Card.TFrame",
            background="white",
            relief="flat",
            borderwidth=1
        )
        
        # Label style
        style.configure("Header.TLabel",
            font=("Segoe UI", 12, "bold"),
            foreground="#2c3e50",
            background="white"
        )
        
        # Button style
        style.configure("Primary.TButton",
            font=("Segoe UI", 10),
            background="#2980b9",
            foreground="white"
        )
        style.map("Primary.TButton",
            background=[("active", "#3498db")],
            foreground=[("active", "white")]
        )

    def _init_ui(self):
        """Initialize the main UI components."""
        # Create main container with padding
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill="both", expand=True)

        # Create horizontal paned window
        paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        paned.pack(fill="both", expand=True)

        # Left side - Tabs
        self.left_tabs = ttk.Notebook(paned, style="Custom.TNotebook")
        
        # Create tab frames
        settings_tab = self._create_settings_tab()
        blogger_tab = self._create_blogger_tab()
        sitemap_tab = self._create_sitemap_tab()
        
        # Add tabs
        self.left_tabs.add(settings_tab, text="Settings")
        self.left_tabs.add(blogger_tab, text="Blogger")
        self.left_tabs.add(sitemap_tab, text="Sitemap")
        
        # Right side - Content
        right_pane = ttk.Frame(paned)
        
        # Add panes to PanedWindow
        paned.add(self.left_tabs, weight=1)
        paned.add(right_pane, weight=3)

        # Create content panels in right pane
        self._create_articles_panel(right_pane)
        self._create_preview_panel(right_pane)
        self._create_bottom_panel(right_pane)
        self._create_log_panel()

    def _create_settings_tab(self):
        """Create the settings tab."""
        tab = ttk.Frame(self.left_tabs, style="Card.TFrame", padding="10")
        
        # API Key Frame
        api_frame = ttk.LabelFrame(tab, text="Google API Key", padding="10")
        api_frame.pack(fill="x", pady=(0, 10))
        
        api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, show="*")
        api_key_entry.pack(fill="x", pady=5)
        
        btn_frame = ttk.Frame(api_frame)
        btn_frame.pack(fill="x")
        
        def toggle_api_key():
            if api_key_entry['show'] == '*':
                api_key_entry['show'] = ''
            else:
                api_key_entry['show'] = '*'
        
        ttk.Button(btn_frame, text="Show/Hide", 
                   style="Primary.TButton", 
                   command=toggle_api_key).pack(side="left", padx=5)
        
        return tab

    def _create_blogger_tab(self):
        """Create the Blogger settings tab."""
        tab = ttk.Frame(self.left_tabs, style="Card.TFrame", padding="10")
        
        # Blog Selection
        ttk.Label(tab, text="Select Blog:", style="Header.TLabel").pack(fill="x", pady=5)
        self.blog_dropdown = ttk.Combobox(tab, textvariable=self.blog_var, state="readonly")
        self.blog_dropdown.pack(fill="x", pady=5)
        
        # Credentials
        ttk.Label(tab, text="Credentials:", style="Header.TLabel").pack(fill="x", pady=5)
        creds_frame = ttk.Frame(tab)
        creds_frame.pack(fill="x", pady=5)
        
        ttk.Entry(creds_frame, textvariable=self.creds_path_var, 
                 state="readonly").pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(creds_frame, text="Browse", 
                  style="Primary.TButton",
                  command=self.browse_credentials).pack(side="right")
        
        # Authentication Status
        status_frame = ttk.Frame(tab)
        status_frame.pack(fill="x", pady=10)
        ttk.Label(status_frame, text="Status: ").pack(side="left")
        ttk.Label(status_frame, textvariable=self.auth_status_var).pack(side="left")
        
        # Buttons
        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x", pady=5)
        self.authenticate_button = ttk.Button(btn_frame, text="Authenticate",
                                            style="Primary.TButton",
                                            command=self.authenticate_blogger)
        self.authenticate_button.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Refresh Blogs",
                  style="Primary.TButton",
                  command=self.refresh_blogs).pack(side="left")
        
        # Post Schedule
        schedule_frame = ttk.LabelFrame(tab, text="Post Schedule", padding="10")
        schedule_frame.pack(fill="x", pady=10)
        ttk.Label(schedule_frame, text="Minutes between posts:").pack(side="left")
        ttk.Entry(schedule_frame, textvariable=self.schedule_var, 
                 width=5).pack(side="left", padx=5)
        
        return tab

    def _create_sitemap_tab(self):
        """Create the sitemap URL tab."""
        tab = ttk.Frame(self.left_tabs, style="Card.TFrame", padding="10")
        
        ttk.Label(tab, text="Enter Sitemap URL:", 
                 style="Header.TLabel").pack(fill="x", pady=5)
        
        ttk.Entry(tab, textvariable=self.sitemap_url_var).pack(fill="x", pady=5)
        
        ttk.Button(tab, text="Fetch Articles",
                  style="Primary.TButton",
                  command=self.fetch_sitemap).pack(fill="x", pady=10)
        
        return tab

    def _create_articles_panel(self, parent):
        """Create the articles panel with treeview."""
        articles_frame = ttk.LabelFrame(parent, text="Articles", padding="10")
        articles_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        
        # Create Treeview with modern style
        style = ttk.Style()
        style.configure("Custom.Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            rowheight=25
        )
        style.configure("Custom.Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            padding=5
        )
        
        # Create Treeview
        self.articles_tree = ttk.Treeview(
            articles_frame,
            columns=("Title", "Schedule"),
            selectmode="extended",
            style="Custom.Treeview"
        )
        
        # Configure columns
        self.articles_tree.heading("#0", text="ID")
        self.articles_tree.heading("Title", text="Title")
        self.articles_tree.heading("Schedule", text="Schedule")
        
        self.articles_tree.column("#0", width=50)
        self.articles_tree.column("Title", width=300)
        self.articles_tree.column("Schedule", width=150)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(articles_frame, orient="vertical",
                                  command=self.articles_tree.yview)
        y_scrollbar.pack(side="right", fill="y")
        
        x_scrollbar = ttk.Scrollbar(articles_frame, orient="horizontal",
                                  command=self.articles_tree.xview)
        x_scrollbar.pack(side="bottom", fill="x")
        
        self.articles_tree.configure(yscrollcommand=y_scrollbar.set,
                                   xscrollcommand=x_scrollbar.set)
        self.articles_tree.pack(side="left", fill="both", expand=True)
        
        # Action buttons
        action_frame = ttk.Frame(articles_frame)
        action_frame.pack(fill="x", pady=5)
        
        ttk.Button(action_frame, text="Schedule Articles",
                  style="Primary.TButton",
                  command=self.show_schedule_dialog).pack(side="left", padx=5)
        
        ttk.Button(action_frame, text="Rewrite Articles",
                  style="Primary.TButton",
                  command=self.rewrite_articles).pack(side="left", padx=5)
        
        ttk.Button(action_frame, text="Post to Blogger",
                  style="Primary.TButton",
                  command=self.batch_post_to_blogger).pack(side="left", padx=5)

    def _create_preview_panel(self, parent):
        """Create the article preview panel."""
        preview_frame = ttk.LabelFrame(parent, text="Article Preview", padding="10")
        preview_frame.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        
        # Configure text widget style
        self.preview_text = tk.Text(
            preview_frame,
            wrap="word",
            font=("Segoe UI", 10),
            bg="white",
            relief="flat",
            padx=10,
            pady=10
        )
        self.preview_text.pack(fill="both", expand=True)

    def _create_bottom_panel(self, parent):
        """Create the bottom panel with progress bar."""
        bottom_frame = ttk.Frame(parent)
        bottom_frame.pack(side="bottom", fill="x", pady=10)
        
        # Progress Bar
        self.progress_frame = ttk.Frame(bottom_frame)
        self.progress_frame.pack(side="bottom", fill="x", padx=10, pady=5)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            style="Custom.Horizontal.TProgressbar"
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.progress_label = ttk.Label(self.progress_frame, text="")
        self.progress_label.pack(side="right")

    def _create_log_panel(self):
        """Create the log panel."""
        log_frame = ttk.LabelFrame(self, text="Application Logs", padding="10")
        log_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        # Log Control Frame
        log_control_frame = ttk.Frame(log_frame)
        log_control_frame.pack(fill="x", pady=(0, 5))
        
        # Log Level Filter
        ttk.Label(log_control_frame, text="Log Level:").pack(side="left", padx=(0, 5))
        self.log_level_var = tk.StringVar(value="ALL")
        log_level_dropdown = ttk.Combobox(
            log_control_frame,
            textvariable=self.log_level_var,
            values=config.LOG_LEVELS,
            state="readonly",
            width=10
        )
        log_level_dropdown.pack(side="left", padx=(0, 10))
        log_level_dropdown.bind('<<ComboboxSelected>>', self.filter_logs)
        
        # Log Actions
        ttk.Button(log_control_frame, text="Clear Logs",
                  style="Primary.TButton",
                  command=self.clear_log).pack(side="right", padx=5)
        ttk.Button(log_control_frame, text="Save Logs",
                  style="Primary.TButton",
                  command=self.save_log).pack(side="right", padx=5)
        
        # Log Text Widget
        log_scroll_frame = ttk.Frame(log_frame)
        log_scroll_frame.pack(fill="both", expand=True)
        
        log_scroll = ttk.Scrollbar(log_scroll_frame)
        log_scroll.pack(side="right", fill="y")
        
        self.log_text = tk.Text(
            log_scroll_frame,
            height=8,
            wrap="word",
            font=("Consolas", 9),
            bg="white",
            relief="flat",
            yscrollcommand=log_scroll.set,
            state='disabled'
        )
        self.log_text.pack(side="left", fill="both", expand=True)
        log_scroll.config(command=self.log_text.yview)
        
        # Configure tags for different log levels
        self.log_text.tag_config('INFO', foreground='#2980b9')
        self.log_text.tag_config('WARNING', foreground='#f39c12')
        self.log_text.tag_config('ERROR', foreground='#c0392b')
        self.log_text.tag_config('SUCCESS', foreground='#27ae60')
        self.log_text.tag_config('DEBUG', foreground='#7f8c8d')

    def _bind_events(self):
        """Bind various events to handlers."""
        self.articles_tree.bind('<<TreeviewSelect>>', self.on_article_selected)
        self.articles_tree.bind('<Motion>', self.check_schedule_hover)
        self.articles_tree.bind('<Leave>', self.hide_schedule_popup)
