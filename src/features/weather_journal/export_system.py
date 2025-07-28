#!/usr/bin/env python3
"""
Weather Journal Export System - Professional export functionality

This module provides comprehensive export capabilities including:
- PDF export with professional formatting and embedded images
- HTML export with styled content and responsive design
- CSV export for data analysis
- Export filtering and date range selection
- Glassmorphic progress indicators
"""

import os
import csv
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import customtkinter as ctk

# PDF generation
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Markdown processing
try:
    import markdown
    from markdown.extensions import codehilite, tables, toc
    MARKDOWN_AVAILABLE = True
except ImportError:
    MARKDOWN_AVAILABLE = False

from ...utils.logger import LoggerMixin
from ...ui.components.glass import (
    GlassFrame, GlassButton, GlassLabel, GlassEntry,
    ComponentSize, create_glass_card
)
from .database import JournalDatabase
from .models import JournalEntry


class ExportSystem(LoggerMixin):
    """
    Core export system for journal entries.
    
    Handles PDF, HTML, and CSV export with professional formatting.
    """
    
    def __init__(self, database: JournalDatabase):
        self.database = database
        self.logger.info("Export System initialized")
    
    def export_to_pdf(self, entries: List[JournalEntry], output_path: str, 
                     include_photos: bool = True, template: str = "professional") -> bool:
        """
        Export entries to PDF format.
        
        Args:
            entries: List of journal entries to export
            output_path: Path for the output PDF file
            include_photos: Whether to include photo attachments
            template: Export template style
            
        Returns:
            True if export successful, False otherwise
        """
        if not REPORTLAB_AVAILABLE:
            self.logger.error("ReportLab not available for PDF export")
            return False
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Get styles
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                textColor=colors.HexColor('#2c3e50'),
                alignment=1  # Center alignment
            )
            
            entry_title_style = ParagraphStyle(
                'EntryTitle',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.HexColor('#34495e')
            )
            
            metadata_style = ParagraphStyle(
                'Metadata',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.HexColor('#7f8c8d'),
                spaceAfter=6
            )
            
            content_style = ParagraphStyle(
                'Content',
                parent=styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                leading=14
            )
            
            # Document title
            story.append(Paragraph("Weather Journal Export", title_style))
            story.append(Spacer(1, 12))
            
            # Export metadata
            export_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
            story.append(Paragraph(f"Exported on {export_date}", metadata_style))
            story.append(Paragraph(f"Total entries: {len(entries)}", metadata_style))
            story.append(Spacer(1, 24))
            
            # Process each entry
            for i, entry in enumerate(entries):
                if i > 0:
                    story.append(Spacer(1, 24))
                
                # Entry title
                story.append(Paragraph(entry.title, entry_title_style))
                
                # Entry metadata
                date_str = datetime.fromisoformat(entry.created_at.replace('Z', '+00:00')).strftime("%B %d, %Y")
                metadata_text = f"Date: {date_str} | Mood: {entry.mood.replace('_', ' ').title()} | Weather: {entry.weather_condition}"
                if entry.location:
                    metadata_text += f" | Location: {entry.location}"
                
                story.append(Paragraph(metadata_text, metadata_style))
                story.append(Spacer(1, 6))
                
                # Entry content
                content_text = self._process_content_for_pdf(entry.content)
                story.append(Paragraph(content_text, content_style))
                
                # Photos (if enabled and available)
                if include_photos and hasattr(entry, 'photos'):
                    photos = self.database.get_entry_photos(entry.id)
                    for photo in photos:
                        if os.path.exists(photo['file_path']):
                            try:
                                img = Image(photo['file_path'], width=4*inch, height=3*inch)
                                story.append(Spacer(1, 6))
                                story.append(img)
                                if photo.get('description'):
                                    story.append(Paragraph(f"<i>{photo['description']}</i>", metadata_style))
                            except Exception as e:
                                self.logger.warning(f"Could not include photo {photo['file_path']}: {e}")
                
                # Add separator line
                if i < len(entries) - 1:
                    story.append(Spacer(1, 12))
                    story.append(Paragraph("<hr/>", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            self.logger.info(f"PDF export completed: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"PDF export failed: {e}")
            return False
    
    def export_to_html(self, entries: List[JournalEntry], output_path: str,
                      include_photos: bool = True, template: str = "modern") -> bool:
        """
        Export entries to HTML format.
        
        Args:
            entries: List of journal entries to export
            output_path: Path for the output HTML file
            include_photos: Whether to include photo attachments
            template: Export template style
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Generate HTML content
            html_content = self._generate_html_content(entries, include_photos, template)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"HTML export completed: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"HTML export failed: {e}")
            return False
    
    def export_to_csv(self, entries: List[JournalEntry], output_path: str,
                     include_metadata: bool = True) -> bool:
        """
        Export entries to CSV format.
        
        Args:
            entries: List of journal entries to export
            output_path: Path for the output CSV file
            include_metadata: Whether to include metadata columns
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                # Define columns
                fieldnames = ['date', 'title', 'content', 'mood', 'weather_condition']
                
                if include_metadata:
                    fieldnames.extend(['location', 'temperature', 'humidity', 'tags', 'word_count'])
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                # Write entries
                for entry in entries:
                    row = {
                        'date': entry.created_at[:10],
                        'title': entry.title,
                        'content': entry.content.replace('\n', ' ').replace('\r', ''),
                        'mood': entry.mood,
                        'weather_condition': entry.weather_condition
                    }
                    
                    if include_metadata:
                        row.update({
                            'location': entry.location or '',
                            'temperature': getattr(entry, 'temperature', ''),
                            'humidity': getattr(entry, 'humidity', ''),
                            'tags': getattr(entry, 'tags', ''),
                            'word_count': len(entry.content.split())
                        })
                    
                    writer.writerow(row)
            
            self.logger.info(f"CSV export completed: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"CSV export failed: {e}")
            return False
    
    def _process_content_for_pdf(self, content: str) -> str:
        """
        Process content for PDF formatting.
        
        Args:
            content: Raw content text
            
        Returns:
            Processed content suitable for PDF
        """
        # Basic markdown to HTML-like processing for ReportLab
        processed = content
        
        # Convert markdown headers
        processed = processed.replace('# ', '<b>')
        processed = processed.replace('## ', '<b>')
        processed = processed.replace('### ', '<b>')
        
        # Convert bold and italic
        processed = processed.replace('**', '<b>').replace('**', '</b>')
        processed = processed.replace('*', '<i>').replace('*', '</i>')
        
        # Handle line breaks
        processed = processed.replace('\n', '<br/>')
        
        return processed
    
    def _generate_html_content(self, entries: List[JournalEntry], 
                              include_photos: bool, template: str) -> str:
        """
        Generate complete HTML content for export.
        
        Args:
            entries: List of journal entries
            include_photos: Whether to include photos
            template: Template style
            
        Returns:
            Complete HTML content
        """
        # HTML template
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather Journal Export</title>
    <style>
        {styles}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Weather Journal Export</h1>
            <p class="export-info">Exported on {export_date} | {entry_count} entries</p>
        </header>
        
        <main>
            {entries_html}
        </main>
        
        <footer>
            <p>Generated by Weather Journal Export System</p>
        </footer>
    </div>
</body>
</html>
        """
        
        # CSS styles
        styles = self._get_html_styles(template)
        
        # Generate entries HTML
        entries_html = ""
        for entry in entries:
            entries_html += self._generate_entry_html(entry, include_photos)
        
        # Format export date
        export_date = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        
        # Fill template
        html_content = html_template.format(
            styles=styles,
            export_date=export_date,
            entry_count=len(entries),
            entries_html=entries_html
        )
        
        return html_content
    
    def _get_html_styles(self, template: str) -> str:
        """
        Get CSS styles for HTML export.
        
        Args:
            template: Template name
            
        Returns:
            CSS styles string
        """
        if template == "modern":
            return """
                * {
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }
                
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }
                
                .container {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: rgba(255, 255, 255, 0.95);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    margin-top: 20px;
                    margin-bottom: 20px;
                }
                
                header {
                    text-align: center;
                    margin-bottom: 40px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #e0e0e0;
                }
                
                h1 {
                    color: #2c3e50;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }
                
                .export-info {
                    color: #7f8c8d;
                    font-size: 1.1em;
                }
                
                .entry {
                    margin-bottom: 40px;
                    padding: 25px;
                    background: rgba(255, 255, 255, 0.8);
                    border-radius: 15px;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                    border-left: 4px solid #3498db;
                }
                
                .entry-title {
                    color: #2c3e50;
                    font-size: 1.8em;
                    margin-bottom: 10px;
                }
                
                .entry-metadata {
                    color: #7f8c8d;
                    font-size: 0.9em;
                    margin-bottom: 15px;
                    padding: 8px 12px;
                    background: rgba(52, 73, 94, 0.1);
                    border-radius: 8px;
                }
                
                .entry-content {
                    font-size: 1.1em;
                    line-height: 1.7;
                    color: #34495e;
                }
                
                .entry-photos {
                    margin-top: 20px;
                }
                
                .photo {
                    margin: 10px 0;
                    text-align: center;
                }
                
                .photo img {
                    max-width: 100%;
                    height: auto;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                }
                
                .photo-description {
                    font-style: italic;
                    color: #7f8c8d;
                    margin-top: 5px;
                }
                
                footer {
                    text-align: center;
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #e0e0e0;
                    color: #7f8c8d;
                }
                
                @media (max-width: 768px) {
                    .container {
                        margin: 10px;
                        padding: 15px;
                    }
                    
                    h1 {
                        font-size: 2em;
                    }
                    
                    .entry {
                        padding: 20px;
                    }
                }
            """
        else:
            # Professional template
            return """
                body {
                    font-family: 'Times New Roman', serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #fff;
                }
                
                header {
                    text-align: center;
                    margin-bottom: 40px;
                    border-bottom: 2px solid #333;
                    padding-bottom: 20px;
                }
                
                h1 {
                    color: #333;
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }
                
                .export-info {
                    color: #666;
                    font-size: 1.1em;
                }
                
                .entry {
                    margin-bottom: 40px;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                
                .entry-title {
                    color: #333;
                    font-size: 1.5em;
                    margin-bottom: 10px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 5px;
                }
                
                .entry-metadata {
                    color: #666;
                    font-size: 0.9em;
                    margin-bottom: 15px;
                    font-style: italic;
                }
                
                .entry-content {
                    font-size: 1em;
                    line-height: 1.6;
                }
                
                .photo img {
                    max-width: 100%;
                    height: auto;
                    margin: 10px 0;
                }
                
                footer {
                    text-align: center;
                    margin-top: 40px;
                    border-top: 1px solid #ddd;
                    padding-top: 20px;
                    color: #666;
                }
            """
    
    def _generate_entry_html(self, entry: JournalEntry, include_photos: bool) -> str:
        """
        Generate HTML for a single entry.
        
        Args:
            entry: Journal entry
            include_photos: Whether to include photos
            
        Returns:
            HTML string for the entry
        """
        # Format date
        date_str = datetime.fromisoformat(entry.created_at.replace('Z', '+00:00')).strftime("%B %d, %Y")
        
        # Process content (convert markdown if available)
        content_html = entry.content
        if MARKDOWN_AVAILABLE:
            try:
                content_html = markdown.markdown(
                    entry.content,
                    extensions=['codehilite', 'tables', 'toc']
                )
            except Exception:
                # Fallback to plain text with line breaks
                content_html = entry.content.replace('\n', '<br>')
        else:
            content_html = entry.content.replace('\n', '<br>')
        
        # Build metadata
        metadata_parts = [
            f"Date: {date_str}",
            f"Mood: {entry.mood.replace('_', ' ').title()}",
            f"Weather: {entry.weather_condition}"
        ]
        
        if entry.location:
            metadata_parts.append(f"Location: {entry.location}")
        
        metadata_html = " | ".join(metadata_parts)
        
        # Photos HTML
        photos_html = ""
        if include_photos:
            photos = self.database.get_entry_photos(entry.id)
            if photos:
                photos_html = '<div class="entry-photos">'
                for photo in photos:
                    if os.path.exists(photo['file_path']):
                        # Convert image to base64 for embedding
                        try:
                            with open(photo['file_path'], 'rb') as img_file:
                                img_data = base64.b64encode(img_file.read()).decode()
                                img_ext = os.path.splitext(photo['file_path'])[1][1:].lower()
                                
                                photos_html += f'''
                                <div class="photo">
                                    <img src="data:image/{img_ext};base64,{img_data}" alt="Journal Photo">
                                    {f'<div class="photo-description">{photo.get("description", "")}</div>' if photo.get('description') else ''}
                                </div>
                                '''
                        except Exception as e:
                            self.logger.warning(f"Could not embed photo {photo['file_path']}: {e}")
                photos_html += '</div>'
        
        # Combine entry HTML
        entry_html = f"""
        <article class="entry">
            <h2 class="entry-title">{entry.title}</h2>
            <div class="entry-metadata">{metadata_html}</div>
            <div class="entry-content">{content_html}</div>
            {photos_html}
        </article>
        """
        
        return entry_html


class ExportDialog(GlassFrame, LoggerMixin):
    """
    Glassmorphic export dialog with options and progress tracking.
    
    Provides user interface for configuring and executing exports.
    """
    
    def __init__(self, parent, database: JournalDatabase, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.database = database
        self.export_system = ExportSystem(database)
        self.progress_callback: Optional[Callable] = None
        
        self._setup_ui()
        self.logger.info("Export Dialog initialized")
    
    def _setup_ui(self):
        """Setup the export dialog interface."""
        # Title
        title_label = GlassLabel(
            self,
            text="📤 Export Journal",
            font=("Segoe UI", 16, "bold")
        )
        title_label.pack(pady=10)
        
        # Export format selection
        format_frame = create_glass_card(self)
        format_frame.pack(fill="x", padx=20, pady=10)
        
        format_label = GlassLabel(
            format_frame,
            text="Export Format:",
            font=("Segoe UI", 12, "bold")
        )
        format_label.pack(anchor="w", padx=10, pady=5)
        
        self.format_var = tk.StringVar(value="pdf")
        
        format_options = [
            ("📄 PDF - Professional document", "pdf"),
            ("🌐 HTML - Web page with styling", "html"),
            ("📊 CSV - Data for analysis", "csv")
        ]
        
        for text, value in format_options:
            radio = ctk.CTkRadioButton(
                format_frame,
                text=text,
                variable=self.format_var,
                value=value,
                font=("Segoe UI", 11)
            )
            radio.pack(anchor="w", padx=20, pady=2)
        
        # Date range selection
        date_frame = create_glass_card(self)
        date_frame.pack(fill="x", padx=20, pady=10)
        
        date_label = GlassLabel(
            date_frame,
            text="Date Range:",
            font=("Segoe UI", 12, "bold")
        )
        date_label.pack(anchor="w", padx=10, pady=5)
        
        date_controls = GlassFrame(date_frame)
        date_controls.pack(fill="x", padx=10, pady=5)
        
        # From date
        from_label = GlassLabel(date_controls, text="From:")
        from_label.pack(side="left", padx=5)
        
        self.from_date = ctk.CTkEntry(
            date_controls,
            placeholder_text="YYYY-MM-DD",
            width=120
        )
        self.from_date.pack(side="left", padx=5)
        
        # To date
        to_label = GlassLabel(date_controls, text="To:")
        to_label.pack(side="left", padx=5)
        
        self.to_date = ctk.CTkEntry(
            date_controls,
            placeholder_text="YYYY-MM-DD",
            width=120
        )
        self.to_date.pack(side="left", padx=5)
        
        # Quick date buttons
        quick_dates = GlassFrame(date_frame)
        quick_dates.pack(fill="x", padx=10, pady=5)
        
        quick_buttons = [
            ("Last 7 days", lambda: self._set_date_range(7)),
            ("Last 30 days", lambda: self._set_date_range(30)),
            ("Last 90 days", lambda: self._set_date_range(90)),
            ("All time", lambda: self._set_date_range(None))
        ]
        
        for text, command in quick_buttons:
            btn = GlassButton(
                quick_dates,
                text=text,
                command=command,
                size=ComponentSize.SMALL,
                width=80
            )
            btn.pack(side="left", padx=2)
        
        # Export options
        options_frame = create_glass_card(self)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        options_label = GlassLabel(
            options_frame,
            text="Export Options:",
            font=("Segoe UI", 12, "bold")
        )
        options_label.pack(anchor="w", padx=10, pady=5)
        
        self.include_photos = tk.BooleanVar(value=True)
        self.include_metadata = tk.BooleanVar(value=True)
        
        photos_check = ctk.CTkCheckBox(
            options_frame,
            text="Include photo attachments",
            variable=self.include_photos
        )
        photos_check.pack(anchor="w", padx=20, pady=2)
        
        metadata_check = ctk.CTkCheckBox(
            options_frame,
            text="Include metadata (location, weather details)",
            variable=self.include_metadata
        )
        metadata_check.pack(anchor="w", padx=20, pady=2)
        
        # Template selection (for PDF/HTML)
        template_frame = create_glass_card(self)
        template_frame.pack(fill="x", padx=20, pady=10)
        
        template_label = GlassLabel(
            template_frame,
            text="Template Style:",
            font=("Segoe UI", 12, "bold")
        )
        template_label.pack(anchor="w", padx=10, pady=5)
        
        self.template_var = tk.StringVar(value="professional")
        
        template_options = [
            ("Professional - Clean and formal", "professional"),
            ("Modern - Glassmorphic styling", "modern")
        ]
        
        for text, value in template_options:
            radio = ctk.CTkRadioButton(
                template_frame,
                text=text,
                variable=self.template_var,
                value=value
            )
            radio.pack(anchor="w", padx=20, pady=2)
        
        # Progress bar
        self.progress_frame = GlassFrame(self)
        self.progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_label = GlassLabel(
            self.progress_frame,
            text="Ready to export",
            font=("Segoe UI", 10)
        )
        self.progress_label.pack(pady=5)
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        # Action buttons
        button_frame = GlassFrame(self)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        export_btn = GlassButton(
            button_frame,
            text="📤 Export",
            command=self._start_export,
            size=ComponentSize.LARGE,
            width=120
        )
        export_btn.pack(side="right", padx=5)
        
        cancel_btn = GlassButton(
            button_frame,
            text="❌ Cancel",
            command=self._cancel_export,
            size=ComponentSize.LARGE,
            width=120
        )
        cancel_btn.pack(side="right", padx=5)
        
        # Set default date range
        self._set_date_range(30)
    
    def _set_date_range(self, days: Optional[int]):
        """Set date range for export."""
        if days is None:
            # All time
            self.from_date.delete(0, tk.END)
            self.to_date.delete(0, tk.END)
        else:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            self.from_date.delete(0, tk.END)
            self.from_date.insert(0, start_date.strftime("%Y-%m-%d"))
            
            self.to_date.delete(0, tk.END)
            self.to_date.insert(0, end_date.strftime("%Y-%m-%d"))
    
    def _start_export(self):
        """Start the export process."""
        try:
            # Get export parameters
            export_format = self.format_var.get()
            from_date = self.from_date.get().strip()
            to_date = self.to_date.get().strip()
            include_photos = self.include_photos.get()
            include_metadata = self.include_metadata.get()
            template = self.template_var.get()
            
            # Get file path
            file_types = {
                'pdf': [("PDF files", "*.pdf")],
                'html': [("HTML files", "*.html")],
                'csv': [("CSV files", "*.csv")]
            }
            
            default_name = f"journal_export_{datetime.now().strftime('%Y%m%d')}.{export_format}"
            
            output_path = filedialog.asksaveasfilename(
                title="Save Export As",
                defaultextension=f".{export_format}",
                filetypes=file_types[export_format],
                initialname=default_name
            )
            
            if not output_path:
                return
            
            # Get entries to export
            entries = self._get_entries_for_export(from_date, to_date)
            
            if not entries:
                messagebox.showwarning("No Data", "No entries found for the selected date range.")
                return
            
            # Update progress
            self._update_progress(0, f"Preparing to export {len(entries)} entries...")
            
            # Perform export
            self.after(100, lambda: self._perform_export(
                export_format, entries, output_path, include_photos, include_metadata, template
            ))
            
        except Exception as e:
            self.logger.error(f"Export preparation failed: {e}")
            messagebox.showerror("Export Error", f"Failed to prepare export: {e}")
    
    def _perform_export(self, export_format: str, entries: List[JournalEntry],
                       output_path: str, include_photos: bool, include_metadata: bool,
                       template: str):
        """Perform the actual export operation."""
        try:
            self._update_progress(25, "Starting export...")
            
            success = False
            
            if export_format == "pdf":
                self._update_progress(50, "Generating PDF...")
                success = self.export_system.export_to_pdf(
                    entries, output_path, include_photos, template
                )
            elif export_format == "html":
                self._update_progress(50, "Generating HTML...")
                success = self.export_system.export_to_html(
                    entries, output_path, include_photos, template
                )
            elif export_format == "csv":
                self._update_progress(50, "Generating CSV...")
                success = self.export_system.export_to_csv(
                    entries, output_path, include_metadata
                )
            
            if success:
                self._update_progress(100, "Export completed successfully!")
                messagebox.showinfo(
                    "Export Complete",
                    f"Journal exported successfully to:\n{output_path}"
                )
            else:
                self._update_progress(0, "Export failed")
                messagebox.showerror(
                    "Export Failed",
                    "The export operation failed. Please check the logs for details."
                )
            
        except Exception as e:
            self.logger.error(f"Export operation failed: {e}")
            self._update_progress(0, "Export failed")
            messagebox.showerror("Export Error", f"Export failed: {e}")
    
    def _get_entries_for_export(self, from_date: str, to_date: str) -> List[JournalEntry]:
        """Get entries for the specified date range."""
        all_entries = self.database.get_all_entries()
        
        if not from_date and not to_date:
            return all_entries
        
        filtered_entries = []
        
        for entry in all_entries:
            entry_date = entry.created_at[:10]
            
            if from_date and entry_date < from_date:
                continue
            
            if to_date and entry_date > to_date:
                continue
            
            filtered_entries.append(entry)
        
        return filtered_entries
    
    def _update_progress(self, value: float, message: str):
        """Update progress bar and message."""
        self.progress_bar.set(value / 100)
        self.progress_label.configure(text=message)
        self.update_idletasks()
        
        if self.progress_callback:
            self.progress_callback(value, message)
    
    def _cancel_export(self):
        """Cancel the export operation."""
        self.destroy()
    
    def set_progress_callback(self, callback: Callable[[float, str], None]):
        """Set callback for progress updates."""
        self.progress_callback = callback