# sapautologin.py

import os
import sys
import time
import subprocess
import pyautogui
from config import SAPLOGON_EXE, ANCHORS_FOLDER, TCODE, SCREEN_ACTION_MAP
from helpers import wait_for_any_image, capture_screenshot, load_query_from_file, wait_for_image, Logger
import actions

print("✅ SAPAutoLogin script loaded.")

# 🆕 Define query folder (all your .txt queries here)
QUERY_FOLDER = r"C:\Projects\PythonAutomation\QueryScripts"
OUTPUT_FOLDER = r"C:\Users\dmccrea\OneDrive - ALDI-HOFER\A Python Scripts\AutomatedReportsOutput"

logger = Logger()
print("✅ SAPAutoLogin script started.")

def main():
    # 1) Launch SAP Logon
    logger.write("🚀 Starting SAP Logon…")
    subprocess.Popen(SAPLOGON_EXE)

    print("🕒 Waiting 5 seconds for SAP Logon to fully open...")
    time.sleep(5)

    # 2) Open E41
    print("⏳ Waiting for E41 entry...")

    entry = wait_for_image(
        img_path=os.path.join(ANCHORS_FOLDER, "e41_entry.png"),
        timeout=20,
        confidence=0.9
    )

    if entry:
        logger.write("🖱 Clicking system entry…")
        pyautogui.doubleClick(entry)
        print("✅ Double-clicked E41 entry.")
    else:
        logger.write("⚠️ E41 entry not found after 20 seconds. Continuing without it.")
        print("⚠️ Warning: Could not find E41 entry. Continuing...")

    # 🆕 Load all query files
    query_files = [f for f in os.listdir(QUERY_FOLDER) if f.endswith(".txt")]
    if not query_files:
        logger.write("❌ No .txt query files found in the query folder. Exiting.")
        print("❌ No .txt query files found.")
        return

    for query_file in query_files:
        query_path = os.path.join(QUERY_FOLDER, query_file)
        input_text = load_query_from_file(query_path)
        input_filename = os.path.splitext(query_file)[0]  # filename without extension

        logger.write(f"🚀 Starting automation for query: {query_file}")
        print(f"🚀 Starting automation for query: {query_file}")

        run_main_screen_loop(input_text, input_filename)

        logger.write(f"✅ Finished automation for query: {query_file}")
        print(f"✅ Finished automation for query: {query_file}")

def run_main_screen_loop(input_text, input_filename):
    # 3) Main screen-action loop
    logger.write("⏳ Starting main screen-action loop...")
    timeout_deadline = time.time() + 300  # total timeout for full run (5 min)

    while time.time() < timeout_deadline:
        try:
            matched_image = wait_for_any_image(
                images=[os.path.join(ANCHORS_FOLDER, img) for img in SCREEN_ACTION_MAP.keys()],
                timeout=30
            )
            screen_filename = os.path.basename(matched_image)

            if screen_filename in SCREEN_ACTION_MAP:
                action_name = SCREEN_ACTION_MAP[screen_filename]
                action_function = getattr(actions, action_name)
                logger.write(f"🎯 Matched screen: {screen_filename}. Running '{action_name}'...")
                action_function({
                    "anchors": ANCHORS_FOLDER,
                    "tcode": TCODE,
                    "input_text": input_text,
                    "input_filename": input_filename,
                    "output_folder": OUTPUT_FOLDER
                })
            else:
                logger.write(f"⚠️ No action defined for {screen_filename}. Skipping...")

        except TimeoutError:
            logger.write("⌛ No new screens detected within 30 seconds. Assuming process complete.")
            break

    logger.write("✅ Main automation loop finished.")

if __name__ == "__main__":
    print("✅ Starting main()...")
    try:
        main()
    except Exception as e:
        logger.write(f"❌ Automation failed: {str(e)}")
        capture_screenshot()
        raise
    finally:
        logger.close()
        print("✅ Script finished and logger closed.")
