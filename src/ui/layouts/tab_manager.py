"""Tab Manager Component

Manages tabbed interfaces with glassmorphic styling.
"""

from typing import Dict, List, Optional, Callable, Any
import customtkinter as ctk
from ..components.glassmorphic.base_frame import GlassmorphicFrame
from ..components.glassmorphic.glass_button import GlassButton


class TabManager(GlassmorphicFrame):
    """Tab manager with glassmorphic styling and smooth transitions."""

    def __init__(self, parent, tab_position: str = "top", **kwargs):
        """Initialize tab manager.
        
        Args:
            parent: Parent widget
            tab_position: Position of tabs ("top", "bottom", "left", "right")
            **kwargs: Additional frame arguments
        """
        super().__init__(parent, **kwargs)
        
        self.tab_position = tab_position
        self.tabs: Dict[str, Dict[str, Any]] = {}  # tab_id -> {"button": button, "content": widget, "title": str}
        self.active_tab: Optional[str] = None
        self.tab_buttons: List[GlassButton] = []
        self.on_tab_change: Optional[Callable] = None
        
        # Tab styling
        self.tab_colors = {
            "active": ("#00FF41", "#00DD33"),
            "inactive": ("#333333", "#444444"),
            "hover": ("#555555", "#666666"),
            "text_active": ("#000000", "#000000"),
            "text_inactive": ("#E0E0E0", "#FFFFFF")
        }
        
        # Layout configuration
        self.tab_height = 40
        self.tab_width = 120
        self.tab_spacing = 2
        
        # Animation settings
        self.transition_duration = 200  # milliseconds
        self.animation_steps = 10
        
        self._setup_layout()
    
    def _setup_layout(self):
        """Setup tab manager layout based on tab position."""
        if self.tab_position in ["top", "bottom"]:
            # Horizontal tab layout
            self.grid_columnconfigure(0, weight=1)
            
            if self.tab_position == "top":
                self.grid_rowconfigure(0, weight=0)  # Tab bar
                self.grid_rowconfigure(1, weight=1)  # Content area
                tab_row, content_row = 0, 1
            else:  # bottom
                self.grid_rowconfigure(0, weight=1)  # Content area
                self.grid_rowconfigure(1, weight=0)  # Tab bar
                tab_row, content_row = 1, 0
            
            # Create tab bar
            self.tab_bar = ctk.CTkFrame(
                self,
                height=self.tab_height,
                fg_color="transparent"
            )
            self.tab_bar.grid(row=tab_row, column=0, sticky="ew", padx=0, pady=0)
            
            # Create content area
            self.content_area = GlassmorphicFrame(
                self,
                corner_radius=8
            )
            self.content_area.grid(row=content_row, column=0, sticky="nsew", padx=5, pady=5)
            
        else:
            # Vertical tab layout (left/right)
            self.grid_rowconfigure(0, weight=1)
            
            if self.tab_position == "left":
                self.grid_columnconfigure(0, weight=0)  # Tab bar
                self.grid_columnconfigure(1, weight=1)  # Content area
                tab_col, content_col = 0, 1
            else:  # right
                self.grid_columnconfigure(0, weight=1)  # Content area
                self.grid_columnconfigure(1, weight=0)  # Tab bar
                tab_col, content_col = 1, 0
            
            # Create tab bar
            self.tab_bar = ctk.CTkFrame(
                self,
                width=self.tab_width,
                fg_color="transparent"
            )
            self.tab_bar.grid(row=0, column=tab_col, sticky="ns", padx=0, pady=0)
            
            # Create content area
            self.content_area = GlassmorphicFrame(
                self,
                corner_radius=8
            )
            self.content_area.grid(row=0, column=content_col, sticky="nsew", padx=5, pady=5)
        
        # Configure content area grid
        self.content_area.grid_columnconfigure(0, weight=1)
        self.content_area.grid_rowconfigure(0, weight=1)
    
    def add_tab(self, tab_id: str, title: str, content_widget: ctk.CTkBaseClass, 
                icon: str = "", closable: bool = False) -> bool:
        """Add a new tab.
        
        Args:
            tab_id: Unique identifier for the tab
            title: Tab title text
            content_widget: Widget to display in tab content
            icon: Optional icon for tab button
            closable: Whether tab can be closed
            
        Returns:
            True if tab was added successfully
        """
        if tab_id in self.tabs:
            print(f"Tab '{tab_id}' already exists")
            return False
        
        try:
            # Create tab button
            button_text = f"{icon} {title}" if icon else title
            tab_button = self._create_tab_button(button_text, tab_id, closable)
            
            # Store tab information
            self.tabs[tab_id] = {
                "button": tab_button,
                "content": content_widget,
                "title": title,
                "icon": icon,
                "closable": closable
            }
            
            self.tab_buttons.append(tab_button)
            
            # Update tab bar layout
            self._update_tab_bar_layout()
            
            # Set as active tab if it's the first one
            if len(self.tabs) == 1:
                self.set_active_tab(tab_id)
            
            return True
            
        except Exception as e:
            print(f"Error adding tab '{tab_id}': {e}")
            return False
    
    def _create_tab_button(self, text: str, tab_id: str, closable: bool) -> GlassButton:
        """Create a tab button.
        
        Args:
            text: Button text
            tab_id: Tab identifier
            closable: Whether tab is closable
            
        Returns:
            Created tab button
        """
        # Determine button size based on tab position
        if self.tab_position in ["top", "bottom"]:
            width = self.tab_width
            height = self.tab_height - 4
        else:
            width = self.tab_width - 4
            height = self.tab_height
        
        button = GlassButton(
            self.tab_bar,
            text=text,
            width=width,
            height=height,
            command=lambda: self.set_active_tab(tab_id),
            font=("Consolas", 10, "bold")
        )
        
        # Add close functionality if closable
        if closable:
            button.bind("<Button-3>", lambda e: self._show_close_menu(e, tab_id))  # Right click
        
        return button
    
    def _update_tab_bar_layout(self):
        """Update tab bar layout with current tabs."""
        try:
            # Clear existing layout
            for widget in self.tab_bar.winfo_children():
                widget.grid_forget()
            
            # Layout tabs based on position
            if self.tab_position in ["top", "bottom"]:
                # Horizontal layout
                for i, (tab_id, tab_info) in enumerate(self.tabs.items()):
                    button = tab_info["button"]
                    button.grid(
                        row=0, column=i,
                        padx=(0, self.tab_spacing) if i < len(self.tabs) - 1 else 0,
                        pady=2,
                        sticky="w"
                    )
            else:
                # Vertical layout
                for i, (tab_id, tab_info) in enumerate(self.tabs.items()):
                    button = tab_info["button"]
                    button.grid(
                        row=i, column=0,
                        pady=(0, self.tab_spacing) if i < len(self.tabs) - 1 else 0,
                        padx=2,
                        sticky="n"
                    )
                    
        except Exception as e:
            print(f"Error updating tab bar layout: {e}")
    
    def remove_tab(self, tab_id: str) -> bool:
        """Remove a tab.
        
        Args:
            tab_id: Tab identifier to remove
            
        Returns:
            True if tab was removed successfully
        """
        if tab_id not in self.tabs:
            return False
        
        try:
            tab_info = self.tabs[tab_id]
            
            # Remove button from tab bar
            tab_info["button"].destroy()
            if tab_info["button"] in self.tab_buttons:
                self.tab_buttons.remove(tab_info["button"])
            
            # Hide content if it's the active tab
            if self.active_tab == tab_id:
                tab_info["content"].grid_forget()
                self.active_tab = None
            
            # Remove from tabs dictionary
            del self.tabs[tab_id]
            
            # Update layout
            self._update_tab_bar_layout()
            
            # Activate another tab if available
            if self.tabs and not self.active_tab:
                first_tab_id = next(iter(self.tabs))
                self.set_active_tab(first_tab_id)
            
            return True
            
        except Exception as e:
            print(f"Error removing tab '{tab_id}': {e}")
            return False
    
    def set_active_tab(self, tab_id: str) -> bool:
        """Set the active tab.
        
        Args:
            tab_id: Tab identifier to activate
            
        Returns:
            True if tab was activated successfully
        """
        if tab_id not in self.tabs:
            return False
        
        try:
            # Hide current active tab content
            if self.active_tab and self.active_tab in self.tabs:
                current_content = self.tabs[self.active_tab]["content"]
                current_content.grid_forget()
                
                # Update current tab button appearance
                current_button = self.tabs[self.active_tab]["button"]
                self._update_button_appearance(current_button, False)
            
            # Show new active tab content
            new_content = self.tabs[tab_id]["content"]
            new_content.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            
            # Update new tab button appearance
            new_button = self.tabs[tab_id]["button"]
            self._update_button_appearance(new_button, True)
            
            # Update active tab
            old_tab = self.active_tab
            self.active_tab = tab_id
            
            # Call change callback
            if self.on_tab_change:
                self.on_tab_change(old_tab, tab_id)
            
            return True
            
        except Exception as e:
            print(f"Error setting active tab '{tab_id}': {e}")
            return False
    
    def _update_button_appearance(self, button: GlassButton, is_active: bool):
        """Update tab button appearance.
        
        Args:
            button: Tab button to update
            is_active: Whether button represents active tab
        """
        try:
            if is_active:
                button.configure(
                    fg_color=self.tab_colors["active"],
                    text_color=self.tab_colors["text_active"]
                )
            else:
                button.configure(
                    fg_color=self.tab_colors["inactive"],
                    text_color=self.tab_colors["text_inactive"]
                )
        except Exception as e:
            print(f"Error updating button appearance: {e}")
    
    def get_active_tab(self) -> Optional[str]:
        """Get the currently active tab ID.
        
        Returns:
            Active tab ID or None
        """
        return self.active_tab
    
    def get_tab_count(self) -> int:
        """Get the number of tabs.
        
        Returns:
            Number of tabs
        """
        return len(self.tabs)
    
    def get_tab_ids(self) -> List[str]:
        """Get list of all tab IDs.
        
        Returns:
            List of tab IDs
        """
        return list(self.tabs.keys())
    
    def update_tab_title(self, tab_id: str, new_title: str, new_icon: str = "") -> bool:
        """Update tab title and icon.
        
        Args:
            tab_id: Tab identifier
            new_title: New tab title
            new_icon: New tab icon
            
        Returns:
            True if update was successful
        """
        if tab_id not in self.tabs:
            return False
        
        try:
            tab_info = self.tabs[tab_id]
            tab_info["title"] = new_title
            
            if new_icon:
                tab_info["icon"] = new_icon
            
            # Update button text
            button_text = f"{tab_info['icon']} {new_title}" if tab_info["icon"] else new_title
            tab_info["button"].configure(text=button_text)
            
            return True
            
        except Exception as e:
            print(f"Error updating tab title for '{tab_id}': {e}")
            return False
    
    def set_tab_change_callback(self, callback: Callable[[Optional[str], str], None]):
        """Set callback for tab change events.
        
        Args:
            callback: Function to call when tab changes (old_tab_id, new_tab_id)
        """
        self.on_tab_change = callback
    
    def _show_close_menu(self, event, tab_id: str):
        """Show context menu for closable tabs.
        
        Args:
            event: Mouse event
            tab_id: Tab identifier
        """
        if not self.tabs[tab_id]["closable"]:
            return
        
        try:
            # Create context menu
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(
                label=f"Close '{self.tabs[tab_id]['title']}'",
                command=lambda: self.remove_tab(tab_id)
            )
            
            # Show menu at cursor position
            menu.tk_popup(event.x_root, event.y_root)
            
        except Exception as e:
            print(f"Error showing close menu: {e}")
    
    def clear_all_tabs(self):
        """Remove all tabs."""
        tab_ids = list(self.tabs.keys())
        for tab_id in tab_ids:
            self.remove_tab(tab_id)
    
    def set_tab_position(self, position: str):
        """Change tab position.
        
        Args:
            position: New tab position ("top", "bottom", "left", "right")
        """
        if position != self.tab_position and position in ["top", "bottom", "left", "right"]:
            # Store current tabs
            current_tabs = dict(self.tabs)
            current_active = self.active_tab
            
            # Clear current layout
            self.clear_all_tabs()
            
            # Update position
            self.tab_position = position
            
            # Recreate layout
            for child in self.winfo_children():
                child.destroy()
            
            self._setup_layout()
            
            # Restore tabs
            for tab_id, tab_info in current_tabs.items():
                self.add_tab(
                    tab_id,
                    tab_info["title"],
                    tab_info["content"],
                    tab_info["icon"],
                    tab_info["closable"]
                )
            
            # Restore active tab
            if current_active:
                self.set_active_tab(current_active)