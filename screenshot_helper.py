#!/usr/bin/env python3
"""
Mac Screenshot Helper - Easy way to share screenshots with Claude
Solves the annoying Mac file path problem!
"""

import os
import shutil
import subprocess
import time
from datetime import datetime

class MacScreenshotHelper:
    def __init__(self):
        # Create a simple screenshots folder in the project
        self.screenshots_dir = '/Users/mz/Dropbox/_CODING/solscannerNewTokens/pythonProject/screenshots'
        os.makedirs(self.screenshots_dir, exist_ok=True)

        # Easy access paths
        self.desktop = os.path.expanduser('~/Desktop')

    def find_latest_screenshot(self):
        """Find the most recent screenshot on Desktop"""
        screenshot_patterns = ['Screenshot*.png', 'Screen Shot*.png']
        latest_file = None
        latest_time = 0

        for pattern in screenshot_patterns:
            import glob
            files = glob.glob(os.path.join(self.desktop, pattern))
            for file in files:
                file_time = os.path.getmtime(file)
                if file_time > latest_time:
                    latest_time = file_time
                    latest_file = file

        return latest_file

    def copy_latest_screenshot(self, custom_name=None):
        """Copy the latest screenshot to our project folder with an easy name"""
        latest = self.find_latest_screenshot()

        if not latest:
            print("❌ No screenshots found on Desktop")
            print("💡 Take a screenshot first: Cmd+Shift+4 or Cmd+Shift+3")
            return None

        # Create a simple filename
        if custom_name:
            filename = f"{custom_name}.png"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"

        destination = os.path.join(self.screenshots_dir, filename)

        try:
            shutil.copy2(latest, destination)
            print(f"✅ Screenshot copied!")
            print(f"📁 Saved as: {filename}")
            print(f"🔗 Full path: {destination}")
            print(f"💬 Tell Claude: 'Look at {filename}'")
            return destination
        except Exception as e:
            print(f"❌ Error copying screenshot: {e}")
            return None

    def take_screenshot_and_copy(self, custom_name=None):
        """Take a screenshot and automatically copy it"""
        print("📸 Taking screenshot in 3 seconds...")
        print("🎯 Position your screen now!")
        time.sleep(3)

        # Take screenshot with macOS screencapture
        temp_path = os.path.join(self.desktop, "temp_screenshot.png")

        try:
            # Use screencapture command
            result = subprocess.run(
                ['screencapture', '-i', temp_path],
                capture_output=True,
                text=True
            )

            if result.returncode == 0 and os.path.exists(temp_path):
                # Copy to our folder
                if custom_name:
                    filename = f"{custom_name}.png"
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"screenshot_{timestamp}.png"

                destination = os.path.join(self.screenshots_dir, filename)
                shutil.move(temp_path, destination)

                print(f"✅ Screenshot captured and saved!")
                print(f"📁 Saved as: {filename}")
                print(f"🔗 Full path: {destination}")
                print(f"💬 Tell Claude: 'Look at {filename}'")
                return destination
            else:
                print("❌ Screenshot cancelled or failed")
                return None

        except Exception as e:
            print(f"❌ Error taking screenshot: {e}")
            return None

    def list_screenshots(self):
        """List all screenshots in our folder"""
        screenshots = [f for f in os.listdir(self.screenshots_dir) if f.endswith('.png')]

        if not screenshots:
            print("📁 No screenshots found")
            return []

        print(f"📁 Found {len(screenshots)} screenshots:")
        for i, screenshot in enumerate(sorted(screenshots), 1):
            path = os.path.join(self.screenshots_dir, screenshot)
            size = os.path.getsize(path) / 1024  # KB
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
            print(f"  {i}. {screenshot} ({size:.1f}KB, {mtime.strftime('%m/%d %H:%M')})")

        return screenshots

    def clean_old_screenshots(self, keep_last=10):
        """Clean old screenshots, keep only the last N"""
        screenshots = [f for f in os.listdir(self.screenshots_dir) if f.endswith('.png')]

        if len(screenshots) <= keep_last:
            print(f"📁 Only {len(screenshots)} screenshots, nothing to clean")
            return

        # Sort by modification time
        screenshots_with_time = []
        for screenshot in screenshots:
            path = os.path.join(self.screenshots_dir, screenshot)
            mtime = os.path.getmtime(path)
            screenshots_with_time.append((mtime, screenshot, path))

        screenshots_with_time.sort(reverse=True)  # Newest first

        # Keep the newest, delete the rest
        to_delete = screenshots_with_time[keep_last:]

        for _, filename, path in to_delete:
            os.remove(path)
            print(f"🗑️  Deleted old screenshot: {filename}")

        print(f"✅ Cleaned up {len(to_delete)} old screenshots, kept {keep_last} newest")

def main():
    helper = MacScreenshotHelper()

    print("🖼️  Mac Screenshot Helper for Claude")
    print("="*50)
    print("1. Copy latest screenshot from Desktop")
    print("2. Take new screenshot and copy")
    print("3. List existing screenshots")
    print("4. Clean old screenshots")
    print("5. Exit")

    while True:
        try:
            choice = input("\n🎯 Choose option (1-5): ").strip()

            if choice == '1':
                name = input("📝 Custom name (optional): ").strip()
                helper.copy_latest_screenshot(name if name else None)

            elif choice == '2':
                name = input("📝 Custom name (optional): ").strip()
                helper.take_screenshot_and_copy(name if name else None)

            elif choice == '3':
                helper.list_screenshots()

            elif choice == '4':
                keep = input("🔢 Keep how many recent screenshots? (default: 10): ").strip()
                keep = int(keep) if keep.isdigit() else 10
                helper.clean_old_screenshots(keep)

            elif choice == '5':
                print("👋 Goodbye!")
                break

            else:
                print("❌ Invalid choice, try again")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()