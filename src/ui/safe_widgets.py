import weakref
from typing import Optional
import tkinter as tk
import customtkinter as ctk

class SafeWidget:
    """Mixin for safe widget lifecycle management."""

    _active_widgets = weakref.WeakSet()
    _after_ids = {}

    def __init__(self):
        SafeWidget._active_widgets.add(self)
        self._after_ids[id(self)] = set()

    def safe_after(self, ms: int, func: callable, *args) -> Optional[str]:
        """Safely schedule a callback with automatic cleanup."""
        try:
            if not hasattr(self, 'winfo_exists') or not self.winfo_exists():
                return None
            after_id = self.after(ms, func, *args)
            self._after_ids[id(self)].add(after_id)
            return after_id
        except (tk.TclError, AttributeError, Exception):
            return None
    
    def safe_after_idle(self, func: callable, *args) -> Optional[str]:
        """Safely schedule an idle callback with automatic cleanup."""
        try:
            if not hasattr(self, 'winfo_exists') or not self.winfo_exists():
                return None
            after_id = self.after_idle(func, *args)
            self._after_ids[id(self)].add(after_id)
            return after_id
        except (tk.TclError, AttributeError, Exception):
            return None

    def safe_after_cancel(self, after_id: str) -> None:
        """Safely cancel an after callback."""
        try:
            if after_id and hasattr(self, 'winfo_exists') and self.winfo_exists():
                self.after_cancel(after_id)
            self._after_ids[id(self)].discard(after_id)
        except (tk.TclError, ValueError, AttributeError, Exception):
            pass

    def cleanup_after_callbacks(self) -> None:
        """Cancel all pending after callbacks for this widget."""
        widget_id = id(self)
        if widget_id in self._after_ids:
            for after_id in list(self._after_ids[widget_id]):
                self.safe_after_cancel(after_id)
            self._after_ids[widget_id].clear()

    def destroy(self) -> None:
        """Safely destroy widget with cleanup."""
        try:
            self.cleanup_after_callbacks()
            
            # Check if widget still exists before attempting destruction
            if hasattr(self, 'winfo_exists'):
                try:
                    exists = self.winfo_exists()
                except (tk.TclError, AttributeError):
                    exists = False
                    
                if exists:
                    # Try to destroy using the specific widget class destroy method
                    for cls in self.__class__.__mro__:
                        if hasattr(cls, 'destroy') and cls != SafeWidget:
                            try:
                                cls.destroy(self)
                                break
                            except (tk.TclError, AttributeError):
                                continue
        except (tk.TclError, AttributeError, Exception):
            pass
        finally:
            SafeWidget._active_widgets.discard(self)
            # Clean up after_ids for this widget
            widget_id = id(self)
            if widget_id in self._after_ids:
                del self._after_ids[widget_id]

    @classmethod
    def cleanup_all_widgets(cls) -> None:
        """Clean up all active widgets and their callbacks."""
        for widget in list(cls._active_widgets):
            try:
                if hasattr(widget, "cleanup_after_callbacks"):
                    widget.cleanup_after_callbacks()
            except BaseException:
                pass
        cls._after_ids.clear()

class SafeCTkFrame(SafeWidget, ctk.CTkFrame):
    """Safe CTkFrame with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkFrame.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTk(SafeWidget, ctk.CTk):
    """Safe main window with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTk.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTkLabel(SafeWidget, ctk.CTkLabel):
    """Safe CTkLabel with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkLabel.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTkButton(SafeWidget, ctk.CTkButton):
    """Safe CTkButton with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkButton.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTkEntry(SafeWidget, ctk.CTkEntry):
    """Safe CTkEntry with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkEntry.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTkProgressBar(SafeWidget, ctk.CTkProgressBar):
    """Safe CTkProgressBar with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkProgressBar.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTkTabview(SafeWidget, ctk.CTkTabview):
    """Safe CTkTabview with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkTabview.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTkScrollableFrame(SafeWidget, ctk.CTkScrollableFrame):
    """Safe CTkScrollableFrame with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkScrollableFrame.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTkTextbox(SafeWidget, ctk.CTkTextbox):
    """Safe CTkTextbox with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkTextbox.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)

class SafeCTkComboBox(SafeWidget, ctk.CTkComboBox):
    """Safe CTkComboBox with lifecycle management."""

    def __init__(self, *args, **kwargs):
        ctk.CTkComboBox.__init__(self, *args, **kwargs)
        SafeWidget.__init__(self)
