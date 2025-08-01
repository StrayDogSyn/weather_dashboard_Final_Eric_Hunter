import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Dict, List, Optional

from PIL import Image, ImageTk

from models.journal_entry import JournalEntry
from utils.photo_manager import PhotoManager


class PhotoGalleryComponent(ttk.Frame):
    """Photo gallery with glassmorphic overlay panels for journal entries."""

    def __init__(
        self,
        parent: tk.Widget,
        photo_manager: PhotoManager,
        on_photo_selected: Optional[Callable[[str], None]] = None,
        on_photos_changed: Optional[Callable[[], None]] = None,
    ):
        """Initialize the photo gallery component.

        Args:
            parent: Parent widget
            photo_manager: Photo manager instance
            on_photo_selected: Callback when a photo is selected
            on_photos_changed: Callback when photos are added/removed
        """
        super().__init__(parent)
        self.photo_manager = photo_manager
        self.on_photo_selected = on_photo_selected
        self.on_photos_changed = on_photos_changed

        # Gallery state
        self.current_entry: Optional[JournalEntry] = None
        self.photo_thumbnails: Dict[str, ImageTk.PhotoImage] = {}
        self.selected_photo: Optional[str] = None
        self.thumbnail_size = (150, 150)

        # Create the gallery interface
        self._create_gallery_interface()

    def _create_gallery_interface(self):
        """Create the photo gallery interface."""
        # Main gallery frame with glassmorphic styling
        self.gallery_frame = ttk.LabelFrame(self, text="Photo Gallery", padding=10)
        self.gallery_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Toolbar frame
        toolbar_frame = ttk.Frame(self.gallery_frame)
        toolbar_frame.pack(fill="x", pady=(0, 10))

        # Add photos button
        self.add_button = ttk.Button(toolbar_frame, text="Add Photos", command=self._add_photos)
        self.add_button.pack(side="left")

        # Remove photo button
        self.remove_button = ttk.Button(
            toolbar_frame,
            text="Remove Selected",
            command=self._remove_selected_photo,
            state="disabled",
        )
        self.remove_button.pack(side="left", padx=(5, 0))

        # View full size button
        self.view_button = ttk.Button(
            toolbar_frame, text="View Full Size", command=self._view_full_size, state="disabled"
        )
        self.view_button.pack(side="left", padx=(5, 0))

        # Photo count label
        self.count_label = ttk.Label(toolbar_frame, text="No photos")
        self.count_label.pack(side="right")

        # Gallery canvas with scrollbar
        canvas_frame = ttk.Frame(self.gallery_frame)
        canvas_frame.pack(fill="both", expand=True)

        self.gallery_canvas = tk.Canvas(canvas_frame, bg="white")
        v_scrollbar = ttk.Scrollbar(
            canvas_frame, orient="vertical", command=self.gallery_canvas.yview
        )
        h_scrollbar = ttk.Scrollbar(
            canvas_frame, orient="horizontal", command=self.gallery_canvas.xview
        )

        self.gallery_canvas.configure(
            yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set
        )

        # Pack scrollbars and canvas
        v_scrollbar.pack(side="right", fill="y")
        h_scrollbar.pack(side="bottom", fill="x")
        self.gallery_canvas.pack(side="left", fill="both", expand=True)

        # Scrollable frame for photos
        self.photos_frame = ttk.Frame(self.gallery_canvas)
        self.canvas_window = self.gallery_canvas.create_window(
            (0, 0), window=self.photos_frame, anchor="nw"
        )

        # Bind events
        self.photos_frame.bind("<Configure>", self._on_frame_configure)
        self.gallery_canvas.bind("<Configure>", self._on_canvas_configure)
        self.gallery_canvas.bind("<MouseWheel>", self._on_mousewheel)

        # Photo info panel (glassmorphic overlay)
        self.info_panel = None
        self._create_info_panel()

    def _create_info_panel(self):
        """Create the photo info overlay panel."""
        # This would be positioned as an overlay in a real glassmorphic implementation
        info_frame = ttk.LabelFrame(self.gallery_frame, text="Photo Info", padding=5)
        info_frame.pack(fill="x", pady=(10, 0))

        self.info_text = tk.Text(info_frame, height=3, wrap="word", state="disabled")
        info_scrollbar = ttk.Scrollbar(info_frame, orient="vertical", command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=info_scrollbar.set)

        self.info_text.pack(side="left", fill="both", expand=True)
        info_scrollbar.pack(side="right", fill="y")

    def _on_frame_configure(self, event=None):
        """Handle frame configuration changes."""
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        """Handle canvas configuration changes."""
        canvas_width = self.gallery_canvas.winfo_width()
        self.gallery_canvas.itemconfig(self.canvas_window, width=canvas_width)

    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling."""
        self.gallery_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _add_photos(self):
        """Add photos to the current entry."""
        if not self.current_entry:
            messagebox.showwarning("No Entry", "Please select a journal entry first.")
            return

        # Open file dialog
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.gif *.bmp"),
            ("JPEG files", "*.jpg *.jpeg"),
            ("PNG files", "*.png"),
            ("All files", "*.*"),
        ]

        filenames = filedialog.askopenfilenames(title="Select Photos", filetypes=filetypes)

        if filenames:
            self._process_new_photos(filenames)

    def _process_new_photos(self, filenames: List[str]):
        """Process and add new photos."""
        try:
            added_photos = []

            for filename in filenames:
                try:
                    # Add photo using photo manager
                    photo_path = self.photo_manager.add_photo(filename, self.current_entry.id)
                    if photo_path:
                        added_photos.append(photo_path)
                        # Add to entry
                        self.current_entry.add_photo(photo_path)
                except Exception as e:
                    messagebox.showerror("Photo Error", f"Failed to add {filename}: {str(e)}")

            if added_photos:
                # Refresh gallery
                self._refresh_gallery()

                # Notify of changes
                if self.on_photos_changed:
                    self.on_photos_changed()

                messagebox.showinfo(
                    "Photos Added", f"Successfully added {len(added_photos)} photo(s)."
                )

        except Exception as e:
            messagebox.showerror("Error", f"Failed to process photos: {str(e)}")

    def _remove_selected_photo(self):
        """Remove the selected photo."""
        if not self.selected_photo or not self.current_entry:
            return

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Deletion", "Are you sure you want to remove this photo from the entry?"
        )

        if result:
            try:
                # Remove from entry
                self.current_entry.remove_photo(self.selected_photo)

                # Remove from photo manager
                self.photo_manager.remove_photo(self.selected_photo, self.current_entry.id)

                # Clear selection
                self.selected_photo = None

                # Refresh gallery
                self._refresh_gallery()

                # Update buttons
                self._update_button_states()

                # Notify of changes
                if self.on_photos_changed:
                    self.on_photos_changed()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to remove photo: {str(e)}")

    def _view_full_size(self):
        """View the selected photo in full size."""
        if not self.selected_photo:
            return

        try:
            # Create full-size viewer window
            viewer = tk.Toplevel(self.parent)
            viewer.title(f"Photo Viewer - {Path(self.selected_photo).name}")
            viewer.geometry("800x600")
            viewer.transient(self.parent)

            # Load and display full-size image
            image = Image.open(self.selected_photo)

            # Resize to fit window while maintaining aspect ratio
            window_size = (780, 550)
            image.thumbnail(window_size, Image.Resampling.LANCZOS)

            photo = ImageTk.PhotoImage(image)

            # Create label to display image
            image_label = ttk.Label(viewer, image=photo)
            image_label.pack(expand=True)

            # Keep a reference to prevent garbage collection
            image_label.image = photo

            # Add photo info
            info_frame = ttk.Frame(viewer)
            info_frame.pack(fill="x", padx=10, pady=5)

            # Get photo metadata
            photo_info = self.photo_manager.get_photo_info(self.selected_photo)
            if photo_info:
                info_text = f"Size: {photo_info.get('width', 'Unknown')}x{photo_info.get('height', 'Unknown')} | "
                info_text += f"File Size: {photo_info.get('file_size_mb', 'Unknown')} MB | "
                info_text += f"Format: {photo_info.get('format', 'Unknown')}"

                ttk.Label(info_frame, text=info_text).pack()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to open photo: {str(e)}")

    def _create_photo_thumbnail(self, photo_path: str) -> Optional[ImageTk.PhotoImage]:
        """Create a thumbnail for a photo."""
        try:
            # Check if thumbnail already exists
            if photo_path in self.photo_thumbnails:
                return self.photo_thumbnails[photo_path]

            # Load and resize image
            image = Image.open(photo_path)
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image)

            # Cache the thumbnail
            self.photo_thumbnails[photo_path] = photo

            return photo

        except Exception as e:
            print(f"Failed to create thumbnail for {photo_path}: {e}")
            return None

    def _on_photo_clicked(self, photo_path: str):
        """Handle photo thumbnail click."""
        # Update selection
        self.selected_photo = photo_path

        # Update button states
        self._update_button_states()

        # Update info panel
        self._update_info_panel()

        # Call callback
        if self.on_photo_selected:
            self.on_photo_selected(photo_path)

        # Refresh gallery to show selection
        self._refresh_gallery()

    def _update_button_states(self):
        """Update button states based on selection."""
        has_selection = self.selected_photo is not None
        has_entry = self.current_entry is not None

        self.add_button.config(state="normal" if has_entry else "disabled")
        self.remove_button.config(state="normal" if has_selection else "disabled")
        self.view_button.config(state="normal" if has_selection else "disabled")

    def _update_info_panel(self):
        """Update the photo info panel."""
        self.info_text.config(state="normal")
        self.info_text.delete(1.0, tk.END)

        if self.selected_photo:
            try:
                # Get photo info
                photo_info = self.photo_manager.get_photo_info(self.selected_photo)

                if photo_info:
                    info_lines = [
                        f"File: {Path(self.selected_photo).name}",
                        f"Size: {photo_info.get('width', 'Unknown')}x{photo_info.get('height', 'Unknown')}",
                        f"File Size: {photo_info.get('file_size_mb', 'Unknown')} MB",
                        f"Format: {photo_info.get('format', 'Unknown')}",
                        f"Added: {photo_info.get('date_added', 'Unknown')}",
                    ]

                    self.info_text.insert(tk.END, "\n".join(info_lines))
                else:
                    self.info_text.insert(tk.END, "Photo information not available.")

            except Exception as e:
                self.info_text.insert(tk.END, f"Error loading photo info: {str(e)}")
        else:
            self.info_text.insert(tk.END, "No photo selected.")

        self.info_text.config(state="disabled")

    def _refresh_gallery(self):
        """Refresh the photo gallery display."""
        # Clear existing thumbnails
        for widget in self.photos_frame.winfo_children():
            widget.destroy()

        if not self.current_entry or not self.current_entry.photos:
            self.count_label.config(text="No photos")
            self.selected_photo = None
            self._update_button_states()
            self._update_info_panel()
            return

        # Update count
        photo_count = len(self.current_entry.photos)
        self.count_label.config(text=f"{photo_count} photo{'s' if photo_count != 1 else ''}")

        # Create thumbnail grid
        photos_per_row = 4
        row = 0
        col = 0

        for photo_path in self.current_entry.photos:
            if not os.path.exists(photo_path):
                continue

            # Create thumbnail frame
            thumb_frame = ttk.Frame(self.photos_frame, relief="solid", borderwidth=2)
            thumb_frame.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

            # Highlight if selected
            if photo_path == self.selected_photo:
                thumb_frame.config(relief="solid", borderwidth=3)

            # Create thumbnail
            thumbnail = self._create_photo_thumbnail(photo_path)

            if thumbnail:
                # Photo button
                photo_btn = tk.Button(
                    thumb_frame,
                    image=thumbnail,
                    command=lambda p=photo_path: self._on_photo_clicked(p),
                    relief="flat",
                    borderwidth=0,
                )
                photo_btn.pack()

                # Keep reference to prevent garbage collection
                photo_btn.image = thumbnail
            else:
                # Placeholder for failed thumbnails
                placeholder = tk.Label(
                    thumb_frame, text="Failed to\nload image", width=15, height=8, bg="lightgray"
                )
                placeholder.pack()

            # Photo name label
            name_label = ttk.Label(
                thumb_frame, text=Path(photo_path).name, font=("TkDefaultFont", 8)
            )
            name_label.pack()

            # Update grid position
            col += 1
            if col >= photos_per_row:
                col = 0
                row += 1

        # Configure grid weights
        for i in range(photos_per_row):
            self.photos_frame.columnconfigure(i, weight=1)

        # Update scroll region
        self.photos_frame.update_idletasks()
        self.gallery_canvas.configure(scrollregion=self.gallery_canvas.bbox("all"))

    def set_entry(self, entry: Optional[JournalEntry]):
        """Set the current journal entry to display photos for."""
        self.current_entry = entry
        self.selected_photo = None

        # Clear cached thumbnails for memory efficiency
        self.photo_thumbnails.clear()

        # Refresh display
        self._refresh_gallery()
        self._update_button_states()
        self._update_info_panel()

    def get_selected_photo(self) -> Optional[str]:
        """Get the currently selected photo path."""
        return self.selected_photo

    def refresh(self):
        """Refresh the gallery display."""
        self._refresh_gallery()
