# 📸 Automatic README Screenshot Updates

This guide explains how to automatically update your README.md file with the most recent screenshot from your `assets/images` directory.

## 🎯 Quick Start

### Option 1: One-Time Update (Simplest)
```bash
cd scripts
python update_readme_screenshot.py
```

### Option 2: Windows Batch File
```bash
scripts\update_screenshot.bat
```

### Option 3: PowerShell Automation
```powershell
# One-time update
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode update

# File watcher (auto-updates when new screenshots are added)
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode watch

# Scheduled task (runs every 30 minutes)
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode schedule -Interval 30
```

## 📋 Available Tools

### 1. `update_readme_screenshot.py` - Core Python Script

**Features:**
- ✅ Finds the most recently modified image file
- ✅ Updates README.md UI Preview section automatically
- ✅ Preserves existing README structure
- ✅ Supports PNG, JPG, JPEG, GIF formats
- ✅ Shows file modification timestamps

**Usage:**
```bash
# Update README with latest screenshot
cd scripts
python update_readme_screenshot.py

# List all available screenshots
cd scripts
python update_readme_screenshot.py --list
```

**Example Output:**
```
📸 Available Screenshots:
==================================================
🔥 LATEST 1. TTKBootstrap.png
     Modified: 2025-07-27 17:59:01
     Size: 35 KB

   2. Phase3C.png
     Modified: 2025-07-27 17:36:02
     Size: 37 KB

✅ README.md updated successfully with assets/images/TTKBootstrap.png
```

### 2. `update_screenshot.bat` - Windows Batch File

**Features:**
- ✅ Simple double-click execution
- ✅ Error checking for Python installation
- ✅ User-friendly output with pause
- ✅ Automation guidance

**Usage:**
- Double-click the file in Windows Explorer (from the scripts folder)
- Or run from command prompt: `scripts\update_screenshot.bat`

### 3. `Setup-AutoScreenshotUpdate.ps1` - Advanced PowerShell Automation

**Features:**
- ✅ **File Watcher Mode**: Automatically updates when new screenshots are added
- ✅ **Scheduled Task Mode**: Creates Windows scheduled task for periodic updates
- ✅ **Manual Update Mode**: One-time update execution
- ✅ **Help Mode**: Shows usage instructions

**Modes:**

#### File Watcher Mode
```powershell
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode watch
```
- Monitors `assets/images` folder in real-time
- Automatically updates README when new PNG files are added
- Press Ctrl+C to stop watching
- Perfect for active development

#### Scheduled Task Mode
```powershell
# Run every hour
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode schedule -Interval 60

# Run every 15 minutes
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode schedule -Interval 15
```
- Creates a Windows scheduled task
- Runs automatically in the background
- Survives system restarts
- Manage via Task Scheduler or PowerShell

#### Manual Update Mode
```powershell
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode update
```
- Same as running the Python script directly
- PowerShell-native execution

## 🔧 Setup Instructions

### Prerequisites
- Python 3.6+ installed and in PATH
- PowerShell 5.0+ (for advanced automation)
- Windows 10/11 (for scheduled tasks)

### Initial Setup

1. **Ensure your screenshots are in the right place:**
   ```
   your-project/
   ├── assets/
   │   └── images/
   │       ├── screenshot1.png
   │       ├── screenshot2.png
   │       └── latest_screenshot.png  ← Most recent
   ├── README.md
   └── update_readme_screenshot.py
   ```

2. **Test the basic functionality:**
   ```bash
   python update_readme_screenshot.py --list
   ```

3. **Choose your automation level:**
   - **Manual**: Run script when needed
   - **Semi-automatic**: Use batch file for easy execution
   - **Automatic**: Set up file watcher or scheduled task

## 🚀 Automation Workflows

### Workflow 1: Development Mode (File Watcher)
**Best for:** Active development with frequent screenshot updates

```powershell
# Start file watcher in a dedicated terminal
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode watch
```

**Process:**
1. Take new screenshot → Save to `assets/images/`
2. File watcher detects new file
3. README.md automatically updates
4. Commit changes to git

### Workflow 2: Production Mode (Scheduled Task)
**Best for:** Periodic updates without manual intervention

```powershell
# Set up daily updates
.\scripts\Setup-AutoScreenshotUpdate.ps1 -Mode schedule -Interval 1440
```

**Process:**
1. Scheduled task runs daily
2. Checks for newer screenshots
3. Updates README if newer files found
4. Logs results to Windows Event Log

### Workflow 3: Manual Mode (On-Demand)
**Best for:** Controlled updates before releases

```bash
# Before committing/releasing
cd scripts
python update_readme_screenshot.py
cd ..
git add README.md
git commit -m "Update README with latest screenshot"
```

## 🔍 How It Works

### Detection Logic
1. **Scans** `assets/images/` for image files (*.png, *.jpg, *.jpeg, *.gif)
2. **Sorts** by file modification time (newest first)
3. **Identifies** the most recently modified file
4. **Updates** the README.md line that starts with `> ![UI Preview](assets/images/`
5. **Preserves** all other README content unchanged

### README Update Process
```markdown
# Before
> ![UI Preview](assets/images/old_screenshot.png)

# After
> ![UI Preview](assets/images/new_screenshot.png)
```

## 🛠️ Troubleshooting

### Common Issues

**"No image files found"**
- Check that images exist in `assets/images/`
- Verify file extensions are supported (.png, .jpg, .jpeg, .gif)
- Ensure you're running from the project root directory

**"Python is not installed"**
- Install Python from [python.org](https://python.org)
- Ensure Python is added to your system PATH
- Restart your terminal/command prompt

**"Access denied" (Scheduled Task)**
- Run PowerShell as Administrator
- Check Windows execution policy: `Get-ExecutionPolicy`
- If needed: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

**"File watcher not working"**
- Ensure the `assets/images` directory exists
- Check that you have read/write permissions
- Try running PowerShell as Administrator

### Debug Mode
```bash
# List all screenshots with details
cd scripts
python update_readme_screenshot.py --list

# Check PowerShell execution policy
Get-ExecutionPolicy

# View scheduled task status
Get-ScheduledTask -TaskName "WeatherDashboard-ScreenshotUpdate"
```

## 🎨 Customization

### Modify Image Directory
Edit the scripts to use a different directory:

```python
# In update_readme_screenshot.py
update_readme_screenshot(images_dir="path/to/your/images")
```

### Change File Extensions
Add support for additional formats:

```python
# In find_most_recent_screenshot function
extensions = ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.svg']
```

### Custom README Pattern
Modify the line detection pattern:

```python
# In update_readme_screenshot function
if line.strip().startswith('> ![Your Custom Pattern]('):
    # Update logic here
```

## 📝 Integration with Git

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:

```bash
#!/bin/sh
# Auto-update README screenshot before commit
cd scripts
python update_readme_screenshot.py
cd ..
git add README.md
```

### GitHub Actions
Add to `.github/workflows/update-screenshot.yml`:

```yaml
name: Update README Screenshot
on:
  push:
    paths:
      - 'assets/images/**'

jobs:
  update-readme:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Update README
        run: |
          cd scripts
          python update_readme_screenshot.py
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add README.md
          git commit -m "Auto-update README screenshot" || exit 0
          git push
```

## 🎯 Best Practices

1. **Naming Convention**: Use descriptive names for screenshots
   - ✅ `weather_dashboard_v2.1_main_ui.png`
   - ❌ `screenshot1.png`

2. **File Size**: Optimize images for web
   - Keep under 100KB when possible
   - Use PNG for UI screenshots
   - Consider WebP for better compression

3. **Backup**: Keep old screenshots for version history
   - Move to `assets/images/archive/` instead of deleting

4. **Testing**: Always test automation before relying on it
   ```bash
   # Test with a new dummy file
   touch assets/images/test_$(date +%s).png
   cd scripts
   python update_readme_screenshot.py
   ```

5. **Documentation**: Update this guide when modifying scripts

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify your Python installation
3. Test with manual mode first
4. Check file permissions and paths
5. Review PowerShell execution policies

**Happy automating! 🚀**