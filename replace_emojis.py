#!/usr/bin/env python3
"""
Script to replace all emojis with text equivalents throughout the codebase.

This script will:
1. Scan all files in the repository
2. Replace specific emojis with their text equivalents
3. Create backups before making changes
4. Provide detailed reporting of changes made

Emoji mappings:
📊 -> [SUMMARY]
✅ -> [DONE]
🔄 -> [PARTIAL]
❌ -> [TODO]
💥 -> [ERROR]
🎯 -> [PROGRESS]
📋 -> [DETAILS]
"""



import argparse
import re
import shutil
import sys
from pathlib import Path

# Emoji to text mappings
EMOJI_MAPPINGS = {
    # Original core mappings
    "📊": "[SUMMARY]",
    "✅": "[DONE]",
    "🔄": "[PARTIAL]",
    "❌": "[TODO]",
    "💥": "[ERROR]",
    "🎯": "[PROGRESS]",
    "📋": "[DETAILS]",
    "🚀": "[LAUNCH]",
    "🎉": "[SUCCESS]",
    "🔧": "[TOOL]",
    "🛠️": "[TOOL]",
    "📱": "[MOBILE]",
    "💡": "[TIP]",
    "⚠️": "[WARNING]",
    "🎊": "[CELEBRATION]",
    # Additional emojis found in codebase
    "🌐": "[NETWORK]",
    "🌟": "[FEATURE]",
    "🌡": "[TEMPERATURE]",
    "🌱": "[PLANT]",
    "🌽": "[CROP]",
    "🌾": "[GRAIN]",
    "🌿": "[LEAF]",
    "🍅": "[TOMATO]",
    "🍇": "[GRAPE]",
    "🍎": "[APPLE]",
    "🍑": "[CHERRY]",
    "🎙": "[MICROPHONE]",
    "🎤": "[VOICE]",
    "🎧": "[AUDIO]",
    "🎨": "[DESIGN]",
    "🎭": "[INTERFACE]",
    "🎮": "[INTERACTIVE]",
    "🎵": "[SOUND]",
    "🏁": "[FINISH]",
    "🏆": "[ACHIEVEMENT]",
    "🏗️": "[ARCHITECTURE]",
    "🏠": "[HOME]",
    "🏥": "[HEALTH]",
    "🏷️": "[TAG]",
    "🐍": "[PYTHON]",
    "🐛": "[BUG]",
    "👁️": "[VISION]",
    "👆": "[POINTER]",
    "👐": "[HANDS]",
    "💊": "[TREATMENT]",
    "💔": "[BROKEN]",
    "💚": "[HEALTHY]",
    "💬": "[CHAT]",
    "💻": "[COMPUTER]",
    "💾": "[SAVE]",
    "📁": "[FOLDER]",
    "📂": "[DIRECTORY]",
    "📄": "[DOCUMENT]",
    "📅": "[DATE]",
    "📈": "[CHART]",
    "📍": "[LOCATION]",
    "📎": "[ATTACH]",
    "📏": "[MEASURE]",
    "📐": "[GEOMETRY]",
    "📓": "[NOTEBOOK]",
    "📖": "[MANUAL]",
    "📚": "[LIBRARY]",
    "📜": "[SCROLL]",
    "📝": "[WRITE]",
    "📤": "[UPLOAD]",
    "📥": "[DOWNLOAD]",
    "📦": "[PACKAGE]",
    "📷": "[CAMERA]",
    "📸": "[PHOTO]",
    "🔊": "[SPEAKER]",
    "🔋": "[BATTERY]",
    "🔍": "[SEARCH]",
    "🔒": "[SECURE]",
    "🔔": "[NOTIFICATION]",
    "🔗": "[LINK]",
    "🔤": "[TEXT]",
    "🔥": "[HOT]",
    "🔬": "[MICROSCOPE]",
    "🔮": "[PREDICTION]",
    "🔴": "[RED]",
    "🕒": "[TIME]",
    "🖥️": "[DESKTOP]",
    "🖼️": "[IMAGE]",
    "🗑️": "[DELETE]",
    "🙈": "[HIDE]",
    "🚨": "[ALERT]",
    "🚫": "[STOP]",
    "🚰": "[WATER]",
    "🛑": "[HALT]",
    "🛡️": "[SHIELD]",
    "🟠": "[ORANGE]",
    "🟡": "[YELLOW]",
    "🟢": "[GREEN]",
    "🤏": "[SMALL]",
    "🤔": "[THINKING]",
    "🤖": "[AI]",
    "🤗": "[HUG]",
    "🤝": "[HANDSHAKE]",
    "🥇": "[FIRST]",
    "🥈": "[SECOND]",
    "🥉": "[THIRD]",
    "🥔": "[POTATO]",
    "🦠": "[VIRUS]",
    "🧑": "[PERSON]",
    "🧠": "[BRAIN]",
    "🧩": "[PUZZLE]",
    "🧪": "[TEST]",
    "🧬": "[DNA]",
    "🧭": "[COMPASS]",
    "🧹": "[CLEAN]",
    "🪝": "[HOOK]",
    "🪴": "[POT]",
    "✨": "[DESIGN]",
    "⚡": "[ACTIONS]",
    "⚙️": "[SETTINGS]",
    "❓": "[UNKNOWN]",
    "⏰": "[TIME]",
}

# File extensions to process
SUPPORTED_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".ini",
    ".rst",
    ".sh",
    ".bat",
    ".ps1",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
}

# Directories to skip
SKIP_DIRECTORIES = {
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    "env",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
    ".tox",
    ".coverage",
    "htmlcov",
    ".mypy_cache",
    ".ruff_cache",
    ".kiro",
    ".github",
    ".qoder",
    ".streamlit",
}

# Files to skip (emoji-related scripts and reports)
SKIP_FILES = {
    "replace_emojis.py",
    "cleanup_backups.py",
    "generate_emoji_report.py",
    "emoji_replacement_stats.json",
    "emoji_replacement_report.md",
}


class EmojiReplacer:
    def __init__(self, root_path: str, backup: bool = True, dry_run: bool = False) -> None:
        self.root_path = Path(root_path)
        self.backup = backup
        self.dry_run = dry_run
        self.changes_made: list[dict] = []
        self.files_processed = 0
        self.files_changed = 0

    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed based on extension/location."""
        # Skip if in excluded directory
        for part in file_path.parts:
            if part in SKIP_DIRECTORIES:
                return False

        # Skip emoji-related scripts and reports
        if file_path.name in SKIP_FILES:
            return False

        # Check extension
        return file_path.suffix.lower() in SUPPORTED_EXTENSIONS

    def contains_emojis(self, content: str) -> bool:
        """Check if content contains any of our target emojis."""
        return any(emoji in content for emoji in EMOJI_MAPPINGS)

    def replace_emojis_in_content(self, content: str) -> tuple[str, list[str]]:
        """Replace emojis in content and return modified content/changes."""
        modified_content = content
        changes = []

        for emoji, replacement in EMOJI_MAPPINGS.items():
            if emoji in modified_content:
                count = modified_content.count(emoji)
                modified_content = modified_content.replace(emoji, replacement)
                change_text = f"  {emoji} -> {replacement} ({count} occur)"
                changes.append(change_text)

        return modified_content, changes

    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of the file."""
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")
        shutil.copy2(file_path, backup_path)
        return backup_path

    def process_file(self, file_path: Path) -> bool:
        """Process a single file, replacing emojis if found."""
        try:
            # Read file content
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                original_content = f.read()

            self.files_processed += 1

            # Check if file contains emojis
            if not self.contains_emojis(original_content):
                return False

            # Replace emojis
            result = self.replace_emojis_in_content(original_content)
            modified_content, changes = result

            if not changes:
                return False

            # Record changes
            relative_path = file_path.relative_to(self.root_path)
            change_info = {"file": str(relative_path), "changes": changes}
            self.changes_made.append(change_info)

            if not self.dry_run:
                # Create backup if requested
                if self.backup:
                    backup_path = self.backup_file(file_path)
                    print(f"  Backup created: {backup_path}")

                # Write modified content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(modified_content)

            self.files_changed += 1
            return True

        except (OSError, UnicodeDecodeError, PermissionError) as e:
            print(f"Error processing {file_path}: {e}")
            return False

    def process_directory(self) -> None:
        """Process all files in the directory recursively."""
        dry_run_prefix = "DRY RUN: " if self.dry_run else ""
        print(f"{dry_run_prefix}Processing files in: {self.root_path}")
        print(f"Backup enabled: {self.backup}")
        print("-" * 50)

        for file_path in self.root_path.rglob("*"):
            if file_path.is_file() and self.should_process_file(file_path):
                if self.process_file(file_path):
                    relative_path = file_path.relative_to(self.root_path)
                    action = "Would modify" if self.dry_run else "Modified"
                    print(f"{action}: {relative_path}")

                    # Show changes made
                    for change_info in self.changes_made:
                        if change_info["file"] == str(relative_path):
                            for change in change_info["changes"]:
                                print(change)
                            break

    def generate_report(self) -> None:
        """Generate a summary report of all changes made."""
        print("\n" + "=" * 60)
        print("EMOJI REPLACEMENT REPORT")
        print("=" * 60)
        print(f"Files processed: {self.files_processed}")
        print(f"Files changed: {self.files_changed}")
        print(f"Total files with changes: {len(self.changes_made)}")

        if self.dry_run:
            print("\n*** THIS WAS A DRY RUN - NO FILES WERE ACTUALLY MODIFIED ***")

        print("\nDETAILED CHANGES:")
        print("-" * 40)

        for change_info in self.changes_made:
            print(f"\nFile: {change_info['file']}")
            for change in change_info["changes"]:
                print(change)

        # Summary by emoji type
        emoji_counts = {}
        for change_info in self.changes_made:
            for change in change_info["changes"]:
                for emoji, replacement in EMOJI_MAPPINGS.items():
                    if f"{emoji} -> {replacement}" in change:
                        if emoji not in emoji_counts:
                            emoji_counts[emoji] = 0
                        # Extract count from change string
                        pattern = r"\((\d+) occur\)"
                        count_match = re.search(pattern, change)
                        if count_match:
                            emoji_counts[emoji] += int(count_match.group(1))

        if emoji_counts:
            print("\nEMOJI REPLACEMENT SUMMARY:")
            print("-" * 30)
            for emoji, count in sorted(emoji_counts.items()):
                replacement = EMOJI_MAPPINGS[emoji]
                print(f"{emoji} -> {replacement}: {count} total replacements")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Replace emojis with text equivalents in codebase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python replace_emojis.py                    # Replace emojis with backup
  python replace_emojis.py --no-backup       # Replace emojis without backup
  python replace_emojis.py --dry-run         # Show what would be changed
  python replace_emojis.py --path /custom    # Process custom directory
        """,
    )

    parser.add_argument("--path", default=".", help="Root path to process (default: current directory)")

    parser.add_argument("--no-backup", action="store_true", help="Do not create backup files")

    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without making changes")

    args = parser.parse_args()

    # Validate path
    root_path = Path(args.path).resolve()
    if not root_path.exists():
        print(f"Error: Path '{root_path}' does not exist")
        sys.exit(1)

    if not root_path.is_dir():
        print(f"Error: Path '{root_path}' is not a directory")
        sys.exit(1)

    # Create replacer and process
    replacer = EmojiReplacer(root_path=str(root_path), backup=not args.no_backup, dry_run=args.dry_run)

    try:
        replacer.process_directory()
        replacer.generate_report()

        if not args.dry_run and replacer.files_changed > 0:
            print(f"\n✅ [DONE] Successfully processed {replacer.files_changed} files!")
            if not args.no_backup:
                print("💡 [TIP] Backup files created with .backup extension")
                print("💡 [TIP] You can remove backups with: find . -name '*.backup' -delete")
        elif args.dry_run:
            print(f"\n🔍 [PREVIEW] Dry run complete. Would modify {replacer.files_changed} files.")
            print("💡 [TIP] Run without --dry-run to make actual changes")
        else:
            print("\n✅ [DONE] No emoji replacements needed!")

    except KeyboardInterrupt:
        print("\n\n❌ [TODO] Operation cancelled by user")
        sys.exit(1)
    except (OSError, UnicodeDecodeError) as e:
        print(f"\n💥 [ERROR] Error during processing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
