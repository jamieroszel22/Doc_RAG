#!/usr/bin/env python3
"""
DocRAG Migration Script
This script helps migrate from the old IBM Redbooks structure to the new DocRAG structure
"""

import os
import sys
import shutil
import json
from pathlib import Path

def migrate_data():
    """Migrate data from old structure to new DocRAG structure"""
    # Use relative paths for portability
    script_dir = Path(__file__).parent.absolute()
    base_dir = script_dir
    old_dir = base_dir / "processed_redbooks"
    new_dir = base_dir / "processed_docs"

    # Check if old directory exists
    if not old_dir.exists():
        print("No old directory found, nothing to migrate.")
        return False

    # Create new directory
    if not new_dir.exists():
        new_dir.mkdir(parents=True, exist_ok=True)

    # Copy all folders from old to new
    subfolders = ["docs", "chunks", "ollama", "openwebui", "embeddings_cache"]
    for folder in subfolders:
        old_folder = old_dir / folder
        new_folder = new_dir / folder

        if old_folder.exists():
            print(f"Migrating {folder}...")

            # Create new folder if it doesn't exist
            if not new_folder.exists():
                new_folder.mkdir(parents=True, exist_ok=True)

            # Copy all files from old to new
            for item in old_folder.glob("**/*"):
                # Get relative path from old_folder
                rel_path = item.relative_to(old_folder)
                # Construct new path
                new_path = new_folder / rel_path

                # Create parent directories if they don't exist
                if not new_path.parent.exists() and item.is_file():
                    new_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file or directory
                if item.is_file():
                    shutil.copy2(item, new_path)
                    print(f"  Copied {rel_path}")

    # Rename the OpenWebUI collection file if it exists
    old_collection = new_dir / "openwebui" / "ibm_knowledge_collection.json"
    new_collection = new_dir / "openwebui" / "knowledge_collection.json"

    if old_collection.exists() and not new_collection.exists():
        print("Updating OpenWebUI collection name...")
        # Read the old collection
        with open(old_collection, "r", encoding="utf-8") as f:
            collection = json.load(f)

        # Update the collection name if it contains IBM or Redbooks
        if "name" in collection and ("IBM" in collection["name"] or "Redbooks" in collection["name"]):
            collection["name"] = "Document Knowledge Base"

        # Write to the new file
        with open(new_collection, "w", encoding="utf-8") as f:
            json.dump(collection, f, ensure_ascii=False, indent=2)

        print(f"  Created {new_collection}")

    print("\nMigration completed successfully.")
    print(f"Old data remains in: {old_dir}")
    print(f"New data available in: {new_dir}")
    print("\nYou can safely delete the old directory if everything works correctly.")
    return True

if __name__ == "__main__":
    print("DocRAG Migration Utility")
    print("-----------------------")
    print("This script will migrate data from the old IBM Redbooks structure to the new DocRAG structure.")

    choice = input("Do you want to proceed with migration? (y/N): ")
    if choice.lower() in ["y", "yes"]:
        if migrate_data():
            print("\nMigration completed. You can now use DocRAG with your existing data.")
        else:
            print("\nMigration not needed or failed.")
    else:
        print("Migration cancelled.")
