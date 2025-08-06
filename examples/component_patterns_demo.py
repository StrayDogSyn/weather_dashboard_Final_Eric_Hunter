"""Component Patterns Demo

Demonstrates the new consolidated component system with practical examples.
"""

import customtkinter as ctk
from src.ui.components import (
    ComponentFactory, get_factory,
    create_frame, create_button, create_label, create_entry
)
from src.ui.components.glassmorphic import GlassmorphicFrame, GlassButton
from src.ui.components.common import LoadingSpinner, ErrorDisplay
from src.ui.styles.style_constants import (
    ColorPalette, SpacingSystem, FontSystem, ThemeVariants
)


class ComponentPatternsDemo(ctk.CTk):
    """Demo application showcasing consolidated component patterns."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Component Patterns Demo")
        self.geometry("800x600")
        
        # Initialize component factory
        self.factory = get_factory()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the demo UI."""
        
        # Main container using factory
        main_frame = self.factory.create_frame(
            self, 
            variant=ThemeVariants.FRAME_MAIN
        )
        main_frame.pack(fill="both", expand=True, padx=SpacingSystem.PADDING_LARGE)
        
        # Title using convenience function
        title_label = create_label(
            main_frame,
            "Component Patterns Demo",
            variant=ThemeVariants.TEXT_TITLE
        )
        title_label.pack(pady=SpacingSystem.PADDING_MEDIUM)
        
        # Create demo sections
        self.create_standard_components_section(main_frame)
        self.create_glassmorphic_section(main_frame)
        self.create_interactive_section(main_frame)
    
    def create_standard_components_section(self, parent):
        """Create section demonstrating standard components."""
        
        # Section frame
        section_frame = self.factory.create_frame(
            parent,
            variant=ThemeVariants.FRAME_DEFAULT
        )
        section_frame.pack(
            fill="x", 
            pady=SpacingSystem.PADDING_SMALL,
            padx=SpacingSystem.PADDING_MEDIUM
        )
        
        # Section title
        section_title = create_label(
            section_frame,
            "Standard Components",
            variant=ThemeVariants.TEXT_SUBTITLE
        )
        section_title.pack(pady=SpacingSystem.PADDING_SMALL)
        
        # Button variants
        button_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=SpacingSystem.PADDING_SMALL)
        
        # Primary button
        primary_btn = create_button(
            button_frame,
            "Primary Button",
            variant=ThemeVariants.BUTTON_PRIMARY
        )
        primary_btn.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        # Secondary button
        secondary_btn = create_button(
            button_frame,
            "Secondary Button",
            variant=ThemeVariants.BUTTON_SECONDARY
        )
        secondary_btn.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        # Danger button
        danger_btn = create_button(
            button_frame,
            "Danger Button",
            variant=ThemeVariants.BUTTON_DANGER
        )
        danger_btn.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        # Entry field
        entry_field = create_entry(
            section_frame,
            placeholder="Enter some text..."
        )
        entry_field.pack(
            fill="x", 
            pady=SpacingSystem.PADDING_SMALL,
            padx=SpacingSystem.PADDING_MEDIUM
        )
    
    def create_glassmorphic_section(self, parent):
        """Create section demonstrating glassmorphic components."""
        
        # Glassmorphic container
        glass_frame = GlassmorphicFrame(parent)
        glass_frame.pack(
            fill="x",
            pady=SpacingSystem.PADDING_MEDIUM,
            padx=SpacingSystem.PADDING_MEDIUM
        )
        
        # Section title
        glass_title = create_label(
            glass_frame,
            "Glassmorphic Components",
            variant=ThemeVariants.TEXT_SUBTITLE
        )
        glass_title.pack(pady=SpacingSystem.PADDING_SMALL)
        
        # Glass buttons
        glass_button_frame = ctk.CTkFrame(glass_frame, fg_color="transparent")
        glass_button_frame.pack(fill="x", pady=SpacingSystem.PADDING_SMALL)
        
        glass_btn1 = GlassButton(glass_button_frame, text="Glass Button 1")
        glass_btn1.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        glass_btn2 = GlassButton(glass_button_frame, text="Glass Button 2")
        glass_btn2.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        # Description
        description = create_label(
            glass_frame,
            "These components use the consolidated glassmorphic styling system.",
            variant=ThemeVariants.TEXT_CAPTION
        )
        description.pack(pady=SpacingSystem.PADDING_TINY)
    
    def create_interactive_section(self, parent):
        """Create section with interactive components."""
        
        # Interactive frame
        interactive_frame = self.factory.create_frame(
            parent,
            variant=ThemeVariants.FRAME_HIGHLIGHT
        )
        interactive_frame.pack(
            fill="x",
            pady=SpacingSystem.PADDING_MEDIUM,
            padx=SpacingSystem.PADDING_MEDIUM
        )
        
        # Section title
        interactive_title = create_label(
            interactive_frame,
            "Interactive Components",
            variant=ThemeVariants.TEXT_SUBTITLE
        )
        interactive_title.pack(pady=SpacingSystem.PADDING_SMALL)
        
        # Control buttons
        control_frame = ctk.CTkFrame(interactive_frame, fg_color="transparent")
        control_frame.pack(fill="x", pady=SpacingSystem.PADDING_SMALL)
        
        # Loading spinner demo
        self.loading_spinner = LoadingSpinner(
            control_frame,
            text="Loading..."
        )
        self.loading_spinner.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        # Error display demo
        self.error_display = ErrorDisplay(
            control_frame,
            message="This is an error message"
        )
        self.error_display.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        # Control buttons
        start_loading_btn = create_button(
            control_frame,
            "Start Loading",
            variant=ThemeVariants.BUTTON_SUCCESS,
            command=self.start_loading
        )
        start_loading_btn.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        stop_loading_btn = create_button(
            control_frame,
            "Stop Loading",
            variant=ThemeVariants.BUTTON_WARNING,
            command=self.stop_loading
        )
        stop_loading_btn.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        show_error_btn = create_button(
            control_frame,
            "Show Error",
            variant=ThemeVariants.BUTTON_DANGER,
            command=self.show_error
        )
        show_error_btn.pack(side="left", padx=SpacingSystem.PADDING_SMALL)
        
        # Style information
        info_text = (
            "This demo showcases the consolidated component system:\n"
            f"• Colors from {ColorPalette.__name__}\n"
            f"• Spacing from {SpacingSystem.__name__}\n"
            f"• Fonts from {FontSystem.__name__}\n"
            "• Components from ComponentFactory"
        )
        
        info_label = create_label(
            interactive_frame,
            info_text,
            variant=ThemeVariants.TEXT_CAPTION
        )
        info_label.pack(pady=SpacingSystem.PADDING_MEDIUM)
    
    def start_loading(self):
        """Start the loading spinner."""
        self.loading_spinner.start()
    
    def stop_loading(self):
        """Stop the loading spinner."""
        self.loading_spinner.stop()
    
    def show_error(self):
        """Show the error display."""
        self.error_display.show_error(
            "Demo error message",
            error_type="warning"
        )


def demonstrate_factory_patterns():
    """Demonstrate different ways to use the component factory."""
    
    print("=== Component Factory Patterns Demo ===")
    
    # Method 1: Direct factory usage
    factory = ComponentFactory()
    print(f"Factory created with {len(factory.get_registered_components())} registered components")
    
    # Method 2: Global factory instance
    global_factory = get_factory()
    print(f"Global factory has {len(global_factory.get_registered_components())} components")
    
    # Method 3: Convenience functions
    print("\nAvailable convenience functions:")
    print("- create_frame()")
    print("- create_button()")
    print("- create_label()")
    print("- create_entry()")
    
    # Method 4: Component registration
    class CustomComponent(ctk.CTkFrame):
        def __init__(self, parent, **kwargs):
            super().__init__(parent, **kwargs)
            self.configure(fg_color=ColorPalette.PRIMARY_GREEN)
    
    factory.register_component("custom", CustomComponent)
    print(f"\nRegistered custom component. Total: {len(factory.get_registered_components())}")
    
    print("\n=== Style Constants Demo ===")
    print(f"Primary color: {ColorPalette.PRIMARY_GREEN}")
    print(f"Medium padding: {SpacingSystem.PADDING_MEDIUM}px")
    print(f"Default font: {FontSystem.get_font()}")
    print(f"Button height: {ComponentSizes.BUTTON_HEIGHT_MEDIUM}px")


if __name__ == "__main__":
    # Run the pattern demonstrations
    demonstrate_factory_patterns()
    
    # Launch the GUI demo
    print("\nLaunching GUI demo...")
    app = ComponentPatternsDemo()
    app.mainloop()