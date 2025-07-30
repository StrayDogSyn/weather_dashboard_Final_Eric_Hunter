#!/usr/bin/env python3
"""
Test script to verify search entry widget functionality.
This script creates a minimal UI to test text input capture.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox

class SearchTestApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Search Entry Test")
        self.root.geometry("500x200")
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title = ctk.CTkLabel(main_frame, text="Search Entry Widget Test", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        # Search frame
        search_frame = ctk.CTkFrame(main_frame)
        search_frame.pack(fill="x", padx=10, pady=10)
        
        # Try CustomTkinter entry first
        try:
            self.search_entry = ctk.CTkEntry(
                search_frame,
                placeholder_text="Type something here...",
                width=300,
                height=35,
                font=("Segoe UI", 12),
                state="normal"
            )
            self.entry_type = "CustomTkinter"
            print("✅ CustomTkinter entry created")
        except Exception as e:
            print(f"❌ CustomTkinter failed: {e}")
            # Fallback to standard tkinter
            self.search_entry = tk.Entry(
                search_frame,
                width=40,
                font=("Segoe UI", 12),
                bg="white",
                fg="black"
            )
            self.entry_type = "Tkinter"
            print("✅ Tkinter fallback entry created")
        
        self.search_entry.pack(side="left", padx=10, pady=10)
        
        # Test button
        test_btn = ctk.CTkButton(
            search_frame,
            text="Test Input",
            command=self.test_input,
            width=100
        )
        test_btn.pack(side="left", padx=5)
        
        # Clear button
        clear_btn = ctk.CTkButton(
            search_frame,
            text="Clear",
            command=self.clear_input,
            width=80
        )
        clear_btn.pack(side="left", padx=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(main_frame, text=f"Using: {self.entry_type} Entry Widget")
        self.status_label.pack(pady=5)
        
        # Result label
        self.result_label = ctk.CTkLabel(main_frame, text="Enter text and click 'Test Input'")
        self.result_label.pack(pady=5)
        
        # Bind Enter key
        self.search_entry.bind("<Return>", lambda e: self.test_input())
        
        # Set focus
        self.root.after(100, lambda: self.search_entry.focus_set())
        
    def test_input(self):
        """Test getting input from the search entry."""
        try:
            text = self.search_entry.get()
            if text.strip():
                self.result_label.configure(text=f"✅ Captured: '{text}' (Length: {len(text)})")
                messagebox.showinfo("Success", f"Successfully captured: '{text}'")
            else:
                self.result_label.configure(text="⚠️ No text entered or empty string")
                messagebox.showwarning("Warning", "Please enter some text")
        except Exception as e:
            self.result_label.configure(text=f"❌ Error: {e}")
            messagebox.showerror("Error", f"Failed to get text: {e}")
    
    def clear_input(self):
        """Clear the search entry."""
        try:
            self.search_entry.delete(0, 'end')
            self.result_label.configure(text="🧹 Input cleared")
        except Exception as e:
            self.result_label.configure(text=f"❌ Clear failed: {e}")
    
    def run(self):
        """Run the test application."""
        print(f"🚀 Starting search entry test with {self.entry_type}")
        self.root.mainloop()

if __name__ == "__main__":
    app = SearchTestApp()
    app.run()