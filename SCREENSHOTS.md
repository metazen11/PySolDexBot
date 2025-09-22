# 📸 Easy Mac Screenshots for Claude

This solves the annoying Mac file path problem! No more hunting through Finder.

## 🚀 Quick Start

1. **Take a screenshot** (Cmd+Shift+4 or Cmd+Shift+3)
2. **Run the helper**:
   ```bash
   cd pythonProject
   python3 screenshot_helper.py
   ```
3. **Choose option 1** to copy latest screenshot
4. **Tell Claude**: "Look at screenshot_20240921_142305.png"

## 🎯 Three Easy Ways

### Method 1: Copy Latest Screenshot
```bash
python3 screenshot_helper.py
# Choose 1, optionally give it a custom name
```

### Method 2: Take New Screenshot
```bash
python3 screenshot_helper.py
# Choose 2, positions screen and takes screenshot automatically
```

### Method 3: Command Line (Fastest)
```bash
# Take screenshot first (Cmd+Shift+4)
python3 -c "
from screenshot_helper import MacScreenshotHelper
helper = MacScreenshotHelper()
path = helper.copy_latest_screenshot('dashboard')
print(f'Tell Claude: Look at {path}')
"
```

## 📁 File Locations

- **Screenshots saved to**: `pythonProject/screenshots/`
- **Easy names**: `screenshot_20240921_142305.png`
- **Custom names**: `dashboard.png`, `token_list.png`, etc.

## 💡 Pro Tips

- Screenshots auto-saved with timestamps
- Use custom names for important ones: `dashboard`, `error`, `token_analysis`
- Helper cleans old screenshots automatically
- All screenshots accessible to Claude via simple filename

## 🔧 Integration with Claude

Once you have a screenshot:

```
You: "Look at dashboard.png - the rug check button isn't working"
Claude: [Can read the screenshot and help debug]

You: "Look at screenshot_20240921_142305.png"
Claude: [Can analyze whatever you captured]
```

## 🎉 No More File Path Hell!

Instead of this nightmare:
```
/Users/mz/Library/Containers/com.apple.screencaptureui/Data/Library/Caches/...
```

You get this:
```
"Look at dashboard.png"
```

**Happy screenshotting! 📸**