# quick_patch.py
"""
Quick patch to fix immediate issues in Weather Dashboard
Run this file once to fix the database schema, then update your main files.
"""

import sqlite3
from pathlib import Path
import logging

def fix_journal_database():
    """Fix the journal database schema."""
    print("Fixing journal database schema...")
    
    db_path = Path("data") / "weather_journal.db"
    db_path.parent.mkdir(exist_ok=True)
    
    with sqlite3.connect(str(db_path)) as conn:
        # Get current schema
        cursor = conn.execute("PRAGMA table_info(journal_entries)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        if existing_columns:
            # Table exists - add missing columns
            columns_to_add = [
                ("date", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("entry_date", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("location", "TEXT DEFAULT 'Unknown'"),
                ("weather_condition", "TEXT"),
                ("temperature", "REAL"),
                ("humidity", "INTEGER"),
                ("wind_speed", "REAL"),
                ("mood", "TEXT"),
                ("mood_score", "INTEGER"),
                ("notes", "TEXT"),
                ("tags", "TEXT"),
                ("photos", "TEXT"),
                ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("updated_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            ]
            
            for col_name, col_def in columns_to_add:
                if col_name not in existing_columns:
                    try:
                        conn.execute(f"ALTER TABLE journal_entries ADD COLUMN {col_name} {col_def}")
                        print(f"  Added column: {col_name}")
                    except sqlite3.OperationalError:
                        pass
        else:
            # Create new table
            print("  Creating new journal_entries table...")
            conn.execute("""
                CREATE TABLE journal_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    location TEXT DEFAULT 'Unknown',
                    weather_condition TEXT,
                    temperature REAL,
                    humidity INTEGER,
                    wind_speed REAL,
                    mood TEXT,
                    mood_score INTEGER,
                    notes TEXT,
                    tags TEXT,
                    photos TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indices
            conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON journal_entries(date DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_entry_date ON journal_entries(entry_date DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mood ON journal_entries(mood)")
        
        conn.commit()
    
    print("✅ Database schema fixed!")

def create_main_py_patch():
    """Create a patched main.py file."""
    patch_content = '''import sys
import logging
import time
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Disable CustomTkinter DPI awareness to prevent errors
import customtkinter as ctk
ctk.deactivate_automatic_dpi_awareness()

from ui.professional_weather_dashboard import ProfessionalWeatherDashboard
from services.config_service import ConfigService
from dotenv import load_dotenv

# Create logger for main module
logger = logging.getLogger(__name__)

def main():
    """Main application entry with window state management."""
    try:
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s [%(asctime)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        
        logger.info("📝 Logging initialized - Level: INFO")
        logger.info("Starting Weather Dashboard...")
        
        # Load environment variables
        load_dotenv()
        
        # Initialize configuration service
        config_service = ConfigService()
        
        # Create application with professional dashboard
        app = ProfessionalWeatherDashboard()
        
        # Override the destroy method to prevent errors
        original_destroy = app.destroy
        def safe_destroy():
            try:
                app._is_closing = True
                original_destroy()
            except Exception as e:
                logger.debug(f"Destroy error (ignored): {e}")
        app.destroy = safe_destroy
        
        # Force window to center and update with error handling
        try:
            app.update()
            app.update_idletasks()
        except Exception as e:
            logger.warning(f"Window update warning (non-critical): {e}")
        
        logger.info("Weather Dashboard initialized successfully")
        
        # Small delay to ensure proper initialization
        time.sleep(0.1)
        
        # Start main loop
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        logger.info("Application shutdown complete")

if __name__ == "__main__":
    main()
'''
    
    with open("main_patched.py", "w") as f:
        f.write(patch_content)
    
    print("✅ Created main_patched.py - rename to main.py after backing up original")

def create_dashboard_cleanup_patch():
    """Create cleanup patch for dashboard."""
    patch_content = '''# Add this to your MainDashboard or ProfessionalWeatherDashboard class

def __init__(self):
    super().__init__()
    
    # Add these at the beginning
    self._is_closing = False
    self._after_ids = []
    self._cleanup_done = False
    
    # ... rest of your init code ...

def after(self, ms, func=None, *args):
    """Safe after method that tracks callbacks."""
    if self._is_closing:
        return None
    
    try:
        if func is None:
            return super().after(ms)
        
        # Wrap the function to handle errors
        def safe_func():
            if not self._is_closing:
                try:
                    return func(*args) if args else func()
                except Exception as e:
                    if "invalid command name" not in str(e):
                        self.logger.debug(f"After callback error: {e}")
        
        after_id = super().after(ms, safe_func)
        self._after_ids.append(after_id)
        return after_id
    except:
        return None

def cleanup(self):
    """Safe cleanup method."""
    if self._cleanup_done:
        return
    
    self._is_closing = True
    self._cleanup_done = True
    
    try:
        self.logger.info("Starting application cleanup...")
        
        # Cancel all after callbacks
        for after_id in self._after_ids:
            try:
                self.after_cancel(after_id)
            except:
                pass
        
        # Cleanup other resources
        if hasattr(self, 'weather_service'):
            self.weather_service.cleanup()
        
        self.logger.info("Application cleanup completed")
    except Exception as e:
        self.logger.error(f"Cleanup error: {e}")

def destroy(self):
    """Safe destroy method."""
    self.cleanup()
    try:
        super().destroy()
    except:
        pass
'''
    
    with open("dashboard_cleanup_patch.txt", "w") as f:
        f.write(patch_content)
    
    print("✅ Created dashboard_cleanup_patch.txt - add this code to your dashboard class")

if __name__ == "__main__":
    print("Weather Dashboard Quick Patch")
    print("=" * 40)
    
    # Fix database
    try:
        fix_journal_database()
    except Exception as e:
        print(f"❌ Database fix failed: {e}")
    
    # Create patches
    try:
        create_main_py_patch()
        create_dashboard_cleanup_patch()
    except Exception as e:
        print(f"❌ Patch creation failed: {e}")
    
    print("\n" + "=" * 40)
    print("Next steps:")
    print("1. Backup your original main.py")
    print("2. Rename main_patched.py to main.py")
    print("3. Add the cleanup code from dashboard_cleanup_patch.txt to your dashboard class")
    print("4. Run the application again")