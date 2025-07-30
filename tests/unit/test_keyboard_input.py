#!/usr/bin/env python3
"""
Minimal test for search entry keyboard input functionality.
This will help isolate any keyboard input issues.
"""

import customtkinter as ctk
import tkinter as tk
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KeyboardInputTest:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Keyboard Input Test")
        self.root.geometry("600x400")
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(
            self.main_frame,
            text="Search Entry Keyboard Input Test",
            font=("Arial", 20, "bold")
        )
        title.pack(pady=20)
        
        # Instructions
        instructions = ctk.CTkLabel(
            self.main_frame,
            text="Click in the search box below and try typing. Check console for logs.",
            font=("Arial", 12)
        )
        instructions.pack(pady=10)
        
        # Create search entry
        self.create_search_entry()
        
        # Status display
        self.status_label = ctk.CTkLabel(
            self.main_frame,
            text="Status: Ready for input",
            font=("Arial", 12)
        )
        self.status_label.pack(pady=20)
        
        # Current text display
        self.text_display = ctk.CTkLabel(
            self.main_frame,
            text="Current text: ''",
            font=("Arial", 12, "bold")
        )
        self.text_display.pack(pady=10)
        
        # Update display every 100ms
        self.update_display()
        
    def create_search_entry(self):
        """Create the search entry widget with comprehensive monitoring."""
        logger.info("Creating search entry widget...")
        
        # Container for search entry
        search_container = ctk.CTkFrame(self.main_frame)
        search_container.pack(pady=20)
        
        try:
            # Create CustomTkinter entry
            self.search_entry = ctk.CTkEntry(
                search_container,
                placeholder_text="Type here to test keyboard input...",
                width=400,
                height=40,
                font=("Arial", 14),
                state="normal"
            )
            self.search_entry.pack(padx=20, pady=20)
            
            # Bind all input events
            self.search_entry.bind("<KeyPress>", self.on_key_press)
            self.search_entry.bind("<KeyRelease>", self.on_key_release)
            self.search_entry.bind("<Button-1>", self.on_click)
            self.search_entry.bind("<FocusIn>", self.on_focus_in)
            self.search_entry.bind("<FocusOut>", self.on_focus_out)
            self.search_entry.bind("<Return>", self.on_enter)
            
            # Force focus
            self.search_entry.focus_set()
            
            logger.info("✅ Search entry created successfully")
            
            # Test widget immediately
            self.test_widget()
            
        except Exception as e:
            logger.error(f"❌ Failed to create search entry: {e}")
            
            # Fallback to tkinter
            self.search_entry = tk.Entry(
                search_container,
                width=50,
                font=("Arial", 14)
            )
            self.search_entry.pack(padx=20, pady=20)
            
            # Bind events for tkinter entry
            self.search_entry.bind("<KeyPress>", self.on_key_press)
            self.search_entry.bind("<KeyRelease>", self.on_key_release)
            self.search_entry.bind("<Button-1>", self.on_click)
            self.search_entry.bind("<FocusIn>", self.on_focus_in)
            self.search_entry.bind("<FocusOut>", self.on_focus_out)
            self.search_entry.bind("<Return>", self.on_enter)
            
            self.search_entry.focus_set()
            logger.info("✅ Tkinter fallback entry created")
    
    def test_widget(self):
        """Test widget functionality."""
        try:
            # Test insert/get
            self.search_entry.insert(0, "TEST")
            value = self.search_entry.get()
            self.search_entry.delete(0, 'end')
            
            if value == "TEST":
                logger.info("✅ Widget insert/get test PASSED")
            else:
                logger.error(f"❌ Widget insert/get test FAILED: got '{value}'")
                
            # Check state
            try:
                state = self.search_entry.cget("state")
                logger.info(f"Widget state: {state}")
            except:
                logger.info("Widget state check not supported (tkinter)")
                
        except Exception as e:
            logger.error(f"❌ Widget test failed: {e}")
    
    def on_key_press(self, event):
        """Handle key press events."""
        logger.info(f"🔧 KEY PRESS: {event.keysym} (char: '{event.char}')")
        self.status_label.configure(text=f"Status: Key pressed - {event.keysym}")
    
    def on_key_release(self, event):
        """Handle key release events."""
        current_text = self.search_entry.get()
        logger.info(f"🔧 KEY RELEASE: {event.keysym} - Current text: '{current_text}'")
        self.status_label.configure(text=f"Status: Key released - {event.keysym}")
    
    def on_click(self, event):
        """Handle click events."""
        logger.info("🔧 CLICK: Widget clicked")
        self.status_label.configure(text="Status: Widget clicked")
    
    def on_focus_in(self, event):
        """Handle focus in events."""
        logger.info("🔧 FOCUS IN: Widget gained focus")
        self.status_label.configure(text="Status: Widget focused")
    
    def on_focus_out(self, event):
        """Handle focus out events."""
        logger.info("🔧 FOCUS OUT: Widget lost focus")
        self.status_label.configure(text="Status: Widget lost focus")
    
    def on_enter(self, event):
        """Handle enter key."""
        text = self.search_entry.get()
        logger.info(f"🔧 ENTER: Enter pressed with text: '{text}'")
        self.status_label.configure(text=f"Status: Enter pressed - '{text}'")
    
    def update_display(self):
        """Update the text display."""
        try:
            current_text = self.search_entry.get()
            self.text_display.configure(text=f"Current text: '{current_text}'")
        except:
            pass
        
        # Schedule next update
        self.root.after(100, self.update_display)
    
    def run(self):
        """Run the test application."""
        logger.info("Starting keyboard input test...")
        logger.info("Instructions:")
        logger.info("1. Click in the search entry field")
        logger.info("2. Try typing some text")
        logger.info("3. Press Enter to test")
        logger.info("4. Check console logs for event detection")
        
        self.root.mainloop()

if __name__ == "__main__":
    test = KeyboardInputTest()
    test.run()