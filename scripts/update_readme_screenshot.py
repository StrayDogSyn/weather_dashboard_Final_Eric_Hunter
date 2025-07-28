#!/usr/bin/env python3
"""
Automatic README Screenshot Updater

This script automatically updates the README.md file with the most recent screenshot
from the assets/images directory based on file modification time.

Usage:
    python update_readme_screenshot.py

Features:
- Finds the most recently modified image file
- Updates the README.md UI Preview section
- Preserves existing README structure
- Supports common image formats (png, jpg, jpeg, gif)
"""

import os
import glob
from pathlib import Path
from datetime import datetime

def find_most_recent_screenshot(images_dir="assets/images"):
    """
    Find the most recently modified image file in the images directory.
    
    Args:
        images_dir (str): Path to the images directory
        
    Returns:
        str: Relative path to the most recent image file
    """
    # Get the script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # Construct absolute path to images directory
    if not os.path.isabs(images_dir):
        images_path = project_root / images_dir
    else:
        images_path = Path(images_dir)
    
    # Supported image extensions
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif']
    
    image_files = []
    for ext in extensions:
        pattern = str(images_path / ext)
        image_files.extend(glob.glob(pattern))
    
    if not image_files:
        raise FileNotFoundError(f"No image files found in {images_path}")
    
    # Find the most recently modified file
    most_recent = max(image_files, key=os.path.getmtime)
    
    # Convert to relative path for README
    relative_path = os.path.relpath(most_recent, project_root).replace('\\', '/')
    
    return relative_path

def update_readme_screenshot(readme_path="README.md", images_dir="assets/images"):
    """
    Update the README.md file with the most recent screenshot.
    
    Args:
        readme_path (str): Path to the README.md file
        images_dir (str): Path to the images directory
    """
    try:
        # Get the script directory and project root
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        
        # Construct absolute path to README
        if not os.path.isabs(readme_path):
            readme_full_path = project_root / readme_path
        else:
            readme_full_path = Path(readme_path)
        
        # Find the most recent screenshot
        latest_image = find_most_recent_screenshot(images_dir)
        
        # Read the current README content
        with open(readme_full_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Find and replace the UI Preview image line
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            if line.strip().startswith('> ![UI Preview](') and ('assets/images/' in line or '../assets/images/' in line):
                # Update with the latest image
                updated_line = f"> ![UI Preview]({latest_image})"
                updated_lines.append(updated_line)
                print(f"Updated screenshot reference: {latest_image}")
            else:
                updated_lines.append(line)
        
        # Write the updated content back
        updated_content = '\n'.join(updated_lines)
        
        with open(readme_full_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
        
        print(f"README.md updated successfully with {latest_image}")
        
        # Show file modification info
        mod_time = os.path.getmtime(os.path.join(images_dir, os.path.basename(latest_image)))
        mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Image last modified: {mod_date}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def list_available_screenshots(images_dir="assets/images"):
    """
    List all available screenshots with their modification times.
    
    Args:
        images_dir (str): Path to the images directory
    """
    extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif']
    
    image_files = []
    for ext in extensions:
        pattern = os.path.join(images_dir, ext)
        image_files.extend(glob.glob(pattern))
    
    if not image_files:
        print(f"No image files found in {images_dir}")
        return
    
    print("\nAvailable Screenshots:")
    print("=" * 50)
    
    # Sort by modification time (newest first)
    image_files.sort(key=os.path.getmtime, reverse=True)
    
    for i, img_path in enumerate(image_files, 1):
        filename = os.path.basename(img_path)
        mod_time = os.path.getmtime(img_path)
        mod_date = datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
        size_kb = os.path.getsize(img_path) // 1024
        
        marker = "LATEST" if i == 1 else "      "
        print(f"{marker} {i}. {filename}")
        print(f"     Modified: {mod_date}")
        print(f"     Size: {size_kb} KB")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        # List available screenshots
        list_available_screenshots("assets/images")
    else:
        # Update README with most recent screenshot
        print("Updating README.md with most recent screenshot...")
        list_available_screenshots("assets/images")
        update_readme_screenshot()
        print("\nDone! Your README.md now shows the latest screenshot.")