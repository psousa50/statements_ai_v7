#!/usr/bin/env python3
"""
Script to read categories from categories.csv and create them via the API.

This script:
1. Reads the CSV file with categories in "Category: Subcategory" format
2. Creates parent categories first
3. Creates subcategories with proper parent relationships
4. Calls the /api/v1/categories endpoint to create them
"""

import argparse

# Add the project root to the path so we can import the centralized config
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import requests

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Use environment variable or .env for API base URL
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class CategoryLoader:
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = API_BASE_URL
        self.base_url = base_url.rstrip("/")
        self.api_url = urljoin(self.base_url, "/api/v1/categories")
        self.session = requests.Session()
        self.created_categories: Dict[str, str] = {}  # name -> id mapping

    def parse_csv(self, csv_file_path: str) -> Tuple[Set[str], List[Tuple[str, str]]]:
        """
        Parse the CSV file and extract parent categories and subcategories.

        Returns:
            - Set of parent category names
            - List of (parent_name, subcategory_name) tuples
        """
        parent_categories: Set[str] = set()
        subcategories: List[Tuple[str, str]] = []

        with open(csv_file_path, "r", encoding="utf-8") as file:
            # Skip the comment line if it exists
            content = file.read().strip()
            lines = content.split("\n")

            for line in lines:
                line = line.strip()
                if not line or line.startswith("//"):
                    continue

                if ":" in line:
                    parent, subcategory = line.split(":", 1)
                    parent = parent.strip()
                    subcategory = subcategory.strip()

                    parent_categories.add(parent)
                    subcategories.append((parent, subcategory))
                else:
                    # Handle lines without ':' as parent categories
                    parent_categories.add(line)

        return parent_categories, subcategories

    def create_category(self, name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Create a category via the API.

        Returns:
            - Category ID if successful, None otherwise
        """
        payload = {"name": name}
        if parent_id:
            payload["parent_id"] = parent_id

        try:
            response = self.session.post(self.api_url, json=payload)
            response.raise_for_status()

            category_data = response.json()
            category_id = category_data.get("id")

            print(f"✅ Created {'subcategory' if parent_id else 'category'}: {name}")
            return category_id

        except requests.exceptions.RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json().get("detail", str(e))
                    print(f"❌ Failed to create {name}: {error_detail}")
                except ValueError:
                    print(f"❌ Failed to create {name}: HTTP {e.response.status_code}")
            else:
                print(f"❌ Failed to create {name}: {str(e)}")
            return None

    def load_categories(self, csv_file_path: str) -> bool:
        """
        Load all categories from the CSV file.

        Returns:
            - True if all categories were created successfully, False otherwise
        """
        print(f"📖 Reading categories from: {csv_file_path}")
        print(f"🌐 API endpoint: {self.api_url}")
        print()

        try:
            parent_categories, subcategories = self.parse_csv(csv_file_path)
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            return False

        print(f"📊 Found {len(parent_categories)} parent categories and {len(subcategories)} subcategories")
        print()

        # Step 1: Create all parent categories
        print("🏗️  Creating parent categories...")
        failed_parents = []

        for parent_name in sorted(parent_categories):
            category_id = self.create_category(parent_name)
            if category_id:
                self.created_categories[parent_name] = category_id
            else:
                failed_parents.append(parent_name)

        if failed_parents:
            print(f"\n⚠️  Failed to create {len(failed_parents)} parent categories:")
            for name in failed_parents:
                print(f"   - {name}")

        print()

        # Step 2: Create all subcategories
        print("🏗️  Creating subcategories...")
        failed_subcategories = []

        for parent_name, subcategory_name in subcategories:
            parent_id = self.created_categories.get(parent_name)
            if not parent_id:
                print(f"⚠️  Skipping {subcategory_name} (parent {parent_name} not found)")
                failed_subcategories.append((parent_name, subcategory_name))
                continue

            category_id = self.create_category(subcategory_name, parent_id)
            if category_id:
                self.created_categories[f"{parent_name}: {subcategory_name}"] = category_id
            else:
                failed_subcategories.append((parent_name, subcategory_name))

        if failed_subcategories:
            print(f"\n⚠️  Failed to create {len(failed_subcategories)} subcategories:")
            for parent_name, subcategory_name in failed_subcategories:
                print(f"   - {parent_name}: {subcategory_name}")

        print()

        # Summary
        total_expected = len(parent_categories) + len(subcategories)
        total_created = len([k for k in self.created_categories.keys() if not k.startswith("//") and k.strip()])

        print("📈 Summary:")
        print(f"   Expected: {total_expected} categories")
        print(f"   Created:  {total_created} categories")
        print(f"   Success rate: {(total_created / total_expected) * 100:.1f}%")

        return len(failed_parents) == 0 and len(failed_subcategories) == 0


def main():
    parser = argparse.ArgumentParser(description="Load categories from CSV into the Bank Statements API")
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="/Users/pedrosousa/Work/Personal/statements-ai/statements-ai-v7/data/categories.csv",
        help="Path to the CSV file containing categories (default: data/categories.csv)",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help=f"Base URL of the API (default: {API_BASE_URL})",
    )

    args = parser.parse_args()

    # Check if CSV file exists
    import os

    if not os.path.exists(args.csv_file):
        print(f"❌ CSV file not found: {args.csv_file}")
        sys.exit(1)

    # Test API connectivity
    loader = CategoryLoader(args.api_url)
    try:
        health_url = urljoin(loader.base_url, "/health")
        response = requests.get(health_url, timeout=5)
        response.raise_for_status()
        print(f"✅ API is reachable at {loader.base_url}")
    except Exception as e:
        print(f"❌ Cannot reach API at {loader.base_url}: {e}")
        print("   Make sure the API server is running (python run.py in bank-statements-api/)")
        sys.exit(1)

    print()

    # Load categories
    success = loader.load_categories(args.csv_file)

    if success:
        print("\n🎉 All categories loaded successfully!")
        sys.exit(0)
    else:
        print("\n⚠️  Some categories failed to load. Check the output above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
