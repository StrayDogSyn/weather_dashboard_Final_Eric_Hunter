from typing import Any, Callable, Dict
import customtkinter as ctk



class ThemePreviewCard(ctk.CTkFrame):
    """A preview card showing theme colors and allowing theme selection."""

    def __init__(
        self, parent, theme_data: Dict[str, Any], theme_key: str, on_select: Callable[[str], None]
    ):
        super().__init__(parent)

        self.theme_data = theme_data
        self.theme_key = theme_key
        self.on_select = on_select
        self.is_selected = False

        # Configure the main frame
        self.configure(
            fg_color=theme_data["card"],
            border_color=theme_data["primary"],
            border_width=2,
            corner_radius=10,
            width=200,
            height=120,
        )

        self._create_widgets()
        self._setup_bindings()

    def _create_widgets(self):
        """Create the preview widgets."""
        # Theme name label
        self.name_label = ctk.CTkLabel(
            self,
            text=self.theme_data["name"],
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=self.theme_data["text"],
        )
        self.name_label.pack(pady=(10, 5))

        # Color swatches frame
        self.swatches_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.swatches_frame.pack(pady=5)

        # Create color swatches
        colors = [
            self.theme_data["primary"],
            self.theme_data["secondary"],
            self.theme_data["accent"],
            self.theme_data["chart_color"],
        ]

        for i, color in enumerate(colors):
            swatch = ctk.CTkFrame(
                self.swatches_frame, fg_color=color, width=25, height=25, corner_radius=5
            )
            swatch.grid(row=0, column=i, padx=2)
            swatch.grid_propagate(False)

        # Preview text
        self.preview_text = ctk.CTkLabel(
            self, text="Sample Text", font=ctk.CTkFont(size=10), text_color=self.theme_data["text"]
        )
        self.preview_text.pack(pady=(5, 10))

        # Selection indicator (initially hidden)
        self.selection_indicator = ctk.CTkLabel(
            self,
            text="✓ ACTIVE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=self.theme_data["accent"],
        )

    def _setup_bindings(self):
        """Setup mouse event bindings."""
        # Bind click events to all widgets
        widgets_to_bind = [self, self.name_label, self.swatches_frame, self.preview_text]

        for widget in widgets_to_bind:
            widget.bind("<Button-1>", self._on_click)
            widget.bind("<Enter>", self._on_hover_enter)
            widget.bind("<Leave>", self._on_hover_leave)

    def _on_click(self, event):
        """Handle click event."""
        self.on_select(self.theme_key)

    def _on_hover_enter(self, event):
        """Handle mouse enter event."""
        if not self.is_selected:
            self.configure(border_color=self.theme_data["accent"])

    def _on_hover_leave(self, event):
        """Handle mouse leave event."""
        if not self.is_selected:
            self.configure(border_color=self.theme_data["primary"])

    def set_selected(self, selected: bool):
        """Set the selection state of this card."""
        self.is_selected = selected

        if selected:
            self.configure(border_color=self.theme_data["accent"], border_width=3)
            self.selection_indicator.pack(pady=(0, 5))
        else:
            self.configure(border_color=self.theme_data["primary"], border_width=2)
            self.selection_indicator.pack_forget()

    def update_colors(self, new_theme_data: Dict[str, Any]):
        """Update colors when theme changes."""
        self.theme_data = new_theme_data

        # Update frame colors
        self.configure(
            fg_color=new_theme_data["card"],
            border_color=(
                new_theme_data["primary"] if not self.is_selected else new_theme_data["accent"]
            ),
        )

        # Update text colors
        self.name_label.configure(text_color=new_theme_data["text"])
        self.preview_text.configure(text_color=new_theme_data["text"])
        self.selection_indicator.configure(text_color=new_theme_data["accent"])
