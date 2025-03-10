import tkinter as tk
from tkinter import ttk, messagebox
from ui import ArticleRewriterUI
import config

def main():
    """Main entry point for the Article Rewriter application."""
    try:
        # Create and run the application
        app = ArticleRewriterUI()
        
        # Set window icon if available
        try:
            app.iconbitmap('icon.ico')
        except:
            pass  # Icon not critical, continue without it
        
        # Configure ttk style if needed
        style = ttk.Style()
        if config.UI_THEME != "default":
            try:
                style.theme_use(config.UI_THEME)
            except:
                pass  # Theme not critical, continue with default
        
        # Start the application
        app.mainloop()
        
    except Exception as e:
        # Show error in a messagebox since GUI might not be available
        messagebox.showerror(
            "Application Error",
            f"An error occurred while starting the application:\n\n{str(e)}"
        )
        raise  # Re-raise the exception for debugging

if __name__ == "__main__":
    main()
