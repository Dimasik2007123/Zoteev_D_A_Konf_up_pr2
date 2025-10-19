# -*- coding: utf-8 -*-
"""
Created on Sun Oct 19 13:51:37 2025

@author: zdima
"""

import sys
import xml.etree.ElementTree as ET

def main():
    if len(sys.argv) != 2:
        print("Usage: python app.py config.xml")
        sys.exit(1)

    config_file = sys.argv[1]
    try:
        tree = ET.parse(config_file)
        root = tree.getroot()

        package_name = root.find('package_name').text.strip()
        repo_url = root.find('repo_url').text.strip()
        test_mode = root.find('test_mode').text.strip()
        package_version = root.find('package_version').text.strip()
        output_file = root.find('output_file').text.strip()
        ascii_mode = root.find('ascii_mode').text.strip()
        max_depth = int(root.find('max_depth').text.strip())

        # Вывод параметров
        print(f"package_name: {package_name}")
        print(f"repo_url: {repo_url}")
        print(f"test_mode: {test_mode}")
        print(f"package_version: {package_version}")
        print(f"output_file: {output_file}")
        print(f"ascii_mode: {ascii_mode}")
        print(f"max_depth: {max_depth}")

    except FileNotFoundError:
        print("Error: Config file not found.")
        sys.exit(1)
    except ET.ParseError:
        print("Error: Invalid XML format.")
        sys.exit(1)
    except (AttributeError, ValueError):
        print("Error: Missing or invalid parameter in config (e.g., missing element or non-integer max_depth).")
        sys.exit(1)

if __name__ == "__main__":
    main()