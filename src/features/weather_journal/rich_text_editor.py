#!/usr/bin/env python3
"""
Weather Journal Rich Text Editor - Enhanced Markdown editor with live preview

This module provides an advanced rich text editor with:
- Markdown syntax support
- Live preview functionality
- Syntax highlighting
- Auto-completion
- Glassmorphic styling
"""

import re
import tkinter as tk
from tkinter import font, messagebox
import customtkinter as ctk
from typing import Dict, List, Optional, Callable
from datetime import datetime
import markdown
from markdown.extensions import codehilite, tables, toc

from ...utils.logger import LoggerMixin
from ...ui.components.glass import (
    GlassFrame, GlassButton, GlassLabel, 
    ComponentSize, create_glass_card
)


class MarkdownEditor(GlassFrame, LoggerMixin):
    """
    Enhanced rich text editor with Markdown support and live preview.
    
    Features:
    - Syntax highlighting for Markdown
    - Live preview with HTML rendering
    - Auto-completion for common patterns
    - Toolbar with formatting buttons
    - Word count and statistics
    """
    
    def __init__(self, parent, on_content_change: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.on_content_change = on_content_change
        self.markdown_processor = markdown.Markdown(
            extensions=['codehilite', 'tables', 'toc', 'fenced_code']
        )
        
        # Editor state
        self.current_content = ""
        self.preview_mode = False
        self.auto_save_enabled = True
        
        # Syntax highlighting patterns
        self.syntax_patterns = {
            'header': (r'^#{1,6}\s.*$', '#4a9eff'),
            'bold': (r'\*\*.*?\*\*|__.*?__', '#ffaa4a'),
            'italic': (r'\*.*?\*|_.*?_', '#4aff9e'),
            'code_inline': (r'`.*?`', '#ff4a9e'),
            'code_block': (r'^```[\s\S]*?```', '#ff4a9e'),
            'link': (r'\[.*?\]\(.*?\)', '#4affff'),
            'list': (r'^\s*[-*+]\s', '#ffff4a'),
            'quote': (r'^>.*$', '#9e4aff'),
            'strikethrough': (r'~~.*?~~', '#888888')
        }
        
        self._setup_ui()
        self._setup_bindings()
        
        self.logger.info("Markdown Editor initialized")
    
    def _setup_ui(self):
        """Setup the editor UI components."""
        # Toolbar
        self.toolbar = self._create_toolbar()
        self.toolbar.pack(fill="x", padx=5, pady=5)
        
        # Main editor area
        self.editor_frame = GlassFrame(self)
        self.editor_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create paned window for split view
        self.paned_window = tk.PanedWindow(
            self.editor_frame,
            orient=tk.HORIZONTAL,
            bg="#2b2b2b",
            sashwidth=5,
            sashrelief="flat",
            sashpad=2
        )
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Editor pane
        self.editor_pane = self._create_editor_pane()
        self.paned_window.add(self.editor_pane, minsize=300)
        
        # Preview pane (initially hidden)
        self.preview_pane = self._create_preview_pane()
        
        # Status bar
        self.status_bar = self._create_status_bar()
        self.status_bar.pack(fill="x", padx=5, pady=5)
    
    def _create_toolbar(self) -> GlassFrame:
        """Create the formatting toolbar."""
        toolbar = GlassFrame(self)
        
        # Formatting buttons
        buttons = [
            ("B", "Bold", self._insert_bold, "bold"),
            ("I", "Italic", self._insert_italic, "italic"),
            ("U", "Underline", self._insert_underline, "underline"),
            ("S", "Strikethrough", self._insert_strikethrough, "strikethrough"),
            ("`", "Code", self._insert_code, "code"),
            ("🔗", "Link", self._insert_link, "link"),
            ("📷", "Image", self._insert_image, "image"),
            ("#", "Header", self._insert_header, "header"),
            ("•", "List", self._insert_list, "list"),
            (">>", "Quote", self._insert_quote, "quote"),
            ("📊", "Table", self._insert_table, "table"),
            ("---", "Separator", self._insert_separator, "separator")
        ]
        
        for i, (text, tooltip, command, style) in enumerate(buttons):
            btn = GlassButton(
                toolbar,
                text=text,
                command=command,
                size=ComponentSize.SMALL,
                width=35,
                height=30
            )
            btn.pack(side="left", padx=2, pady=2)
            
            # Add tooltip (simplified)
            self._add_tooltip(btn, tooltip)
        
        # Separator
        separator = tk.Frame(toolbar, width=2, bg="#4d4d4d")
        separator.pack(side="left", fill="y", padx=10, pady=5)
        
        # View toggle buttons
        self.view_buttons = {
            'edit': GlassButton(
                toolbar,
                text="✏️ Edit",
                command=self._show_edit_view,
                size=ComponentSize.SMALL
            ),
            'preview': GlassButton(
                toolbar,
                text="👁️ Preview",
                command=self._show_preview_view,
                size=ComponentSize.SMALL
            ),
            'split': GlassButton(
                toolbar,
                text="⚌ Split",
                command=self._show_split_view,
                size=ComponentSize.SMALL
            )
        }
        
        for btn in self.view_buttons.values():
            btn.pack(side="left", padx=2, pady=2)
        
        # Set initial active view
        self.view_buttons['edit'].configure(fg_color="#4a9eff")
        
        return toolbar
    
    def _create_editor_pane(self) -> GlassFrame:
        """Create the text editor pane."""
        pane = GlassFrame(self.paned_window)
        
        # Line numbers frame
        self.line_numbers_frame = tk.Frame(
            pane,
            width=50,
            bg="#1e1e1e",
            relief="flat"
        )
        self.line_numbers_frame.pack(side="left", fill="y")
        
        # Line numbers text widget
        self.line_numbers = tk.Text(
            self.line_numbers_frame,
            width=4,
            padx=5,
            pady=5,
            bg="#1e1e1e",
            fg="#666666",
            font=("Consolas", 11),
            state="disabled",
            wrap="none",
            relief="flat",
            borderwidth=0,
            cursor="arrow"
        )
        self.line_numbers.pack(fill="both", expand=True)
        
        # Main text editor
        self.text_editor = tk.Text(
            pane,
            bg="#2b2b2b",
            fg="#ffffff",
            font=("Consolas", 12),
            wrap="word",
            relief="flat",
            borderwidth=0,
            padx=10,
            pady=10,
            insertbackground="#ffffff",
            selectbackground="#4a9eff",
            selectforeground="#ffffff",
            undo=True,
            maxundo=50
        )
        self.text_editor.pack(side="right", fill="both", expand=True)
        
        # Configure syntax highlighting tags
        self._configure_syntax_tags()
        
        return pane
    
    def _create_preview_pane(self) -> GlassFrame:
        """Create the HTML preview pane."""
        pane = GlassFrame(self.paned_window)
        
        # Preview header
        header = GlassLabel(
            pane,
            text="📖 Live Preview",
            font=("Segoe UI", 12, "bold")
        )
        header.pack(fill="x", padx=10, pady=5)
        
        # HTML preview area (using Text widget with HTML-like formatting)
        self.preview_text = tk.Text(
            pane,
            bg="#f8f9fa",
            fg="#212529",
            font=("Segoe UI", 11),
            wrap="word",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=15,
            state="disabled",
            cursor="arrow"
        )
        self.preview_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure preview text tags for formatting
        self._configure_preview_tags()
        
        return pane
    
    def _create_status_bar(self) -> GlassFrame:
        """Create the status bar."""
        status_bar = GlassFrame(self)
        
        # Word count
        self.word_count_label = GlassLabel(
            status_bar,
            text="Words: 0 | Characters: 0",
            font=("Segoe UI", 9)
        )
        self.word_count_label.pack(side="left", padx=10, pady=2)
        
        # Cursor position
        self.cursor_pos_label = GlassLabel(
            status_bar,
            text="Line: 1, Column: 1",
            font=("Segoe UI", 9)
        )
        self.cursor_pos_label.pack(side="right", padx=10, pady=2)
        
        return status_bar
    
    def _setup_bindings(self):
        """Setup event bindings."""
        # Text change events
        self.text_editor.bind('<KeyRelease>', self._on_text_change)
        self.text_editor.bind('<Button-1>', self._on_cursor_move)
        self.text_editor.bind('<KeyPress>', self._on_key_press)
        
        # Keyboard shortcuts
        self.text_editor.bind('<Control-b>', lambda e: self._insert_bold())
        self.text_editor.bind('<Control-i>', lambda e: self._insert_italic())
        self.text_editor.bind('<Control-k>', lambda e: self._insert_link())
        self.text_editor.bind('<Control-l>', lambda e: self._insert_list())
        self.text_editor.bind('<Control-q>', lambda e: self._insert_quote())
        
        # Sync scrolling between editor and line numbers
        self.text_editor.bind('<MouseWheel>', self._sync_scroll)
        self.text_editor.bind('<Button-4>', self._sync_scroll)
        self.text_editor.bind('<Button-5>', self._sync_scroll)
    
    def _configure_syntax_tags(self):
        """Configure text tags for syntax highlighting."""
        for tag_name, (pattern, color) in self.syntax_patterns.items():
            self.text_editor.tag_configure(
                tag_name,
                foreground=color,
                font=("Consolas", 12, "bold" if tag_name == "header" else "normal")
            )
    
    def _configure_preview_tags(self):
        """Configure text tags for preview formatting."""
        # Header tags
        for i in range(1, 7):
            size = 18 - i * 2
            self.preview_text.tag_configure(
                f"h{i}",
                font=("Segoe UI", size, "bold"),
                spacing1=10,
                spacing3=5
            )
        
        # Other formatting tags
        self.preview_text.tag_configure("bold", font=("Segoe UI", 11, "bold"))
        self.preview_text.tag_configure("italic", font=("Segoe UI", 11, "italic"))
        self.preview_text.tag_configure("code", font=("Consolas", 10), background="#f1f3f4")
        self.preview_text.tag_configure("quote", lmargin1=20, lmargin2=20, background="#f8f9fa")
    
    def _on_text_change(self, event=None):
        """Handle text change events."""
        self._update_line_numbers()
        self._update_syntax_highlighting()
        self._update_word_count()
        self._update_cursor_position()
        
        if self.preview_mode or hasattr(self, 'split_view_active'):
            self._update_preview()
        
        # Trigger content change callback
        if self.on_content_change:
            content = self.get_content()
            if content != self.current_content:
                self.current_content = content
                self.on_content_change(content)
    
    def _on_cursor_move(self, event=None):
        """Handle cursor movement."""
        self._update_cursor_position()
    
    def _on_key_press(self, event):
        """Handle key press events for auto-completion."""
        # Auto-completion for common Markdown patterns
        if event.keysym == "Return":
            self._handle_auto_completion()
    
    def _handle_auto_completion(self):
        """Handle auto-completion for lists and other patterns."""
        current_line = self.text_editor.get("insert linestart", "insert")
        
        # Auto-continue lists
        list_match = re.match(r'^(\s*)([-*+]|\d+\.)\s', current_line)
        if list_match:
            indent, marker = list_match.groups()
            if marker.isdigit():
                # Numbered list
                next_num = int(marker[:-1]) + 1
                new_marker = f"{next_num}."
            else:
                # Bullet list
                new_marker = marker
            
            self.text_editor.insert("insert", f"\n{indent}{new_marker} ")
            return "break"
        
        # Auto-continue quotes
        if current_line.strip().startswith('>'):
            indent = len(current_line) - len(current_line.lstrip())
            self.text_editor.insert("insert", f"\n{' ' * indent}> ")
            return "break"
    
    def _update_line_numbers(self):
        """Update line numbers display."""
        self.line_numbers.config(state="normal")
        self.line_numbers.delete(1.0, "end")
        
        line_count = int(self.text_editor.index("end-1c").split('.')[0])
        line_numbers_text = "\n".join(str(i) for i in range(1, line_count + 1))
        
        self.line_numbers.insert(1.0, line_numbers_text)
        self.line_numbers.config(state="disabled")
    
    def _update_syntax_highlighting(self):
        """Update syntax highlighting."""
        content = self.text_editor.get(1.0, "end-1c")
        
        # Clear existing tags
        for tag_name in self.syntax_patterns.keys():
            self.text_editor.tag_remove(tag_name, 1.0, "end")
        
        # Apply syntax highlighting
        for tag_name, (pattern, color) in self.syntax_patterns.items():
            for match in re.finditer(pattern, content, re.MULTILINE):
                start_idx = f"1.0+{match.start()}c"
                end_idx = f"1.0+{match.end()}c"
                self.text_editor.tag_add(tag_name, start_idx, end_idx)
    
    def _update_word_count(self):
        """Update word and character count."""
        content = self.text_editor.get(1.0, "end-1c")
        words = len(content.split())
        chars = len(content)
        
        self.word_count_label.configure(text=f"Words: {words} | Characters: {chars}")
    
    def _update_cursor_position(self):
        """Update cursor position display."""
        cursor_pos = self.text_editor.index("insert")
        line, column = cursor_pos.split('.')
        self.cursor_pos_label.configure(text=f"Line: {line}, Column: {int(column) + 1}")
    
    def _update_preview(self):
        """Update the HTML preview."""
        content = self.text_editor.get(1.0, "end-1c")
        
        try:
            # Convert Markdown to HTML (simplified preview)
            self.preview_text.config(state="normal")
            self.preview_text.delete(1.0, "end")
            
            # Simple Markdown parsing for preview
            lines = content.split('\n')
            for line in lines:
                self._render_preview_line(line)
            
            self.preview_text.config(state="disabled")
            
        except Exception as e:
            self.logger.error(f"Error updating preview: {e}")
    
    def _render_preview_line(self, line: str):
        """Render a single line in the preview."""
        # Headers
        header_match = re.match(r'^(#{1,6})\s(.*)$', line)
        if header_match:
            level = len(header_match.group(1))
            text = header_match.group(2)
            self.preview_text.insert("end", f"{text}\n", f"h{level}")
            return
        
        # Bold and italic (simplified)
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)  # Remove bold markers for preview
        line = re.sub(r'\*(.*?)\*', r'\1', line)      # Remove italic markers for preview
        
        # Code (simplified)
        line = re.sub(r'`(.*?)`', r'\1', line)       # Remove code markers for preview
        
        # Lists
        if re.match(r'^\s*[-*+]\s', line):
            text = re.sub(r'^\s*[-*+]\s', '• ', line)
            self.preview_text.insert("end", f"{text}\n")
            return
        
        # Quotes
        if line.strip().startswith('>'):
            text = line.replace('>', '').strip()
            self.preview_text.insert("end", f"{text}\n", "quote")
            return
        
        # Regular text
        self.preview_text.insert("end", f"{line}\n")
    
    def _sync_scroll(self, event):
        """Sync scrolling between editor and line numbers."""
        self.line_numbers.yview_moveto(self.text_editor.yview()[0])
    
    # Formatting methods
    def _insert_bold(self):
        """Insert bold formatting."""
        self._wrap_selection("**", "**")
    
    def _insert_italic(self):
        """Insert italic formatting."""
        self._wrap_selection("*", "*")
    
    def _insert_underline(self):
        """Insert underline formatting."""
        self._wrap_selection("<u>", "</u>")
    
    def _insert_strikethrough(self):
        """Insert strikethrough formatting."""
        self._wrap_selection("~~", "~~")
    
    def _insert_code(self):
        """Insert code formatting."""
        self._wrap_selection("`", "`")
    
    def _insert_link(self):
        """Insert link formatting."""
        try:
            selection = self.text_editor.get("sel.first", "sel.last")
            link_text = selection or "link text"
        except tk.TclError:
            link_text = "link text"
        
        link_format = f"[{link_text}](url)"
        self.text_editor.insert("insert", link_format)
    
    def _insert_image(self):
        """Insert image formatting."""
        image_format = "![alt text](image_url)"
        self.text_editor.insert("insert", image_format)
    
    def _insert_header(self):
        """Insert header formatting."""
        self.text_editor.insert("insert linestart", "# ")
    
    def _insert_list(self):
        """Insert list formatting."""
        self.text_editor.insert("insert linestart", "- ")
    
    def _insert_quote(self):
        """Insert quote formatting."""
        self.text_editor.insert("insert linestart", "> ")
    
    def _insert_table(self):
        """Insert table formatting."""
        table_format = """| Header 1 | Header 2 | Header 3 |
|----------|----------|----------|
| Cell 1   | Cell 2   | Cell 3   |
| Cell 4   | Cell 5   | Cell 6   |"""
        self.text_editor.insert("insert", table_format)
    
    def _insert_separator(self):
        """Insert horizontal separator."""
        self.text_editor.insert("insert", "\n---\n")
    
    def _wrap_selection(self, prefix: str, suffix: str):
        """Wrap selected text with prefix and suffix."""
        try:
            selection = self.text_editor.get("sel.first", "sel.last")
            self.text_editor.delete("sel.first", "sel.last")
            self.text_editor.insert("insert", f"{prefix}{selection}{suffix}")
        except tk.TclError:
            # No selection, just insert the formatting
            self.text_editor.insert("insert", f"{prefix}{suffix}")
            # Move cursor between the markers
            current_pos = self.text_editor.index("insert")
            line, col = current_pos.split('.')
            new_pos = f"{line}.{int(col) - len(suffix)}"
            self.text_editor.mark_set("insert", new_pos)
    
    # View mode methods
    def _show_edit_view(self):
        """Show only the editor view."""
        if hasattr(self, 'split_view_active'):
            delattr(self, 'split_view_active')
        
        self.paned_window.forget(self.preview_pane)
        self.preview_mode = False
        
        # Update button states
        self._update_view_buttons('edit')
    
    def _show_preview_view(self):
        """Show only the preview view."""
        if hasattr(self, 'split_view_active'):
            delattr(self, 'split_view_active')
        
        self.paned_window.forget(self.editor_pane)
        self.paned_window.add(self.preview_pane)
        self.preview_mode = True
        self._update_preview()
        
        # Update button states
        self._update_view_buttons('preview')
    
    def _show_split_view(self):
        """Show both editor and preview in split view."""
        self.split_view_active = True
        self.preview_mode = False
        
        # Ensure both panes are added
        self.paned_window.forget(self.editor_pane)
        self.paned_window.forget(self.preview_pane)
        self.paned_window.add(self.editor_pane, minsize=300)
        self.paned_window.add(self.preview_pane, minsize=300)
        
        self._update_preview()
        
        # Update button states
        self._update_view_buttons('split')
    
    def _update_view_buttons(self, active_view: str):
        """Update view button states."""
        for view, button in self.view_buttons.items():
            if view == active_view:
                button.configure(fg_color="#4a9eff")
            else:
                button.configure(fg_color="transparent")
    
    def _add_tooltip(self, widget, text: str):
        """Add a simple tooltip to a widget."""
        def on_enter(event):
            # Simple tooltip implementation
            pass
        
        def on_leave(event):
            pass
        
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)
    
    # Public methods
    def get_content(self) -> str:
        """Get the current editor content."""
        return self.text_editor.get(1.0, "end-1c")
    
    def set_content(self, content: str):
        """Set the editor content."""
        self.text_editor.delete(1.0, "end")
        self.text_editor.insert(1.0, content)
        self._on_text_change()
    
    def get_markdown_content(self) -> str:
        """Get content as Markdown."""
        return self.get_content()
    
    def get_html_content(self) -> str:
        """Get content as HTML."""
        markdown_content = self.get_content()
        try:
            return self.markdown_processor.convert(markdown_content)
        except Exception as e:
            self.logger.error(f"Error converting to HTML: {e}")
            return f"<p>Error converting content: {e}</p>"
    
    def clear_content(self):
        """Clear all content."""
        self.text_editor.delete(1.0, "end")
        self._on_text_change()
    
    def focus_editor(self):
        """Focus the text editor."""
        self.text_editor.focus_set()
    
    def insert_text(self, text: str):
        """Insert text at current cursor position."""
        self.text_editor.insert("insert", text)
        self._on_text_change()