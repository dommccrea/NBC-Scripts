# actions.py
import os
import sys
import time
import pyautogui
import pyperclip
from helpers import wait_and_click, wait_and_doubleclick, wait_for_specific_screen, wait_for_any_image

def run_full_diagnostics_flow(session_data):
    """Complete flow: open Diagnostics, paste query, execute."""
    print("📎 Running full Diagnostics flow...")

    # Step 1: Open Diagnostics - Part 1
    diagnostics_path = f"{session_data['anchors']}\\st04.1.png"
    wait_and_doubleclick(diagnostics_path, timeout=30)
    print("✅ Diagnostics subfolder expanded.")

    # Step 1: Open Diagnostics - Part 2
    diagnostics2_path = f"{session_data['anchors']}\\st04.2.png"
    wait_and_doubleclick(diagnostics2_path, timeout=30)
    print("✅ Diagnostics subfolder expanded.")

    # Step 2: Input Query
    input_field_path = f"{session_data['anchors']}\\input_query.png"
    img_path = wait_for_any_image([input_field_path], timeout=30)
    location = pyautogui.locateOnScreen(img_path, confidence=0.9)
    if not location:
        raise Exception("❌ Input field image not found.")

    center_x = location.left + location.width // 2
    center_y = location.top + location.height - 5
    pyautogui.click(center_x, center_y)

    text_to_input = session_data.get("input_text", "")
    if not text_to_input:
        raise Exception("❌ No input text provided.")

    pyperclip.copy(text_to_input)
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'v')
    print(f"✅ Query pasted ({len(text_to_input)} characters).")

    # Step 3: Execute Query
    execute_path = f"{session_data['anchors']}\\execute_query.png"
    wait_and_click(execute_path, timeout=30)
    print("✅ Query executed.")

    # Step 4: Wait for Execution
    print("⏳ Waiting for query to execute (sleeping 0.5 seconds)...")
    time.sleep(0.5)

    # Step 5: Detect Loading Popup
    loading_img = f"{session_data['anchors']}\\loading_query.png"
    print("⏳ Waiting for loading to finish...")
    loading_loc = None

    for _ in range(60):
        loading_loc = pyautogui.locateOnScreen(loading_img, confidence=0.9)
        if loading_loc:
            print("✅ Found Loading Query popup.")
            break
        time.sleep(0.5)

    if not loading_loc:
        raise Exception("❌ Could not find Loading Query popup to wait for.")

    # Step 6: Remember Popup Position
    center_x = loading_loc.left + loading_loc.width // 2
    center_y = loading_loc.top + loading_loc.height // 2

    # Step 7: Wait Until Loading Disappears
    from helpers import wait_until_image_disappears
    wait_until_image_disappears(loading_img, timeout=120)
    print("✅ Loading popup disappeared.")

    # Step 8: Right-click Previous Location
    time.sleep(1)  # Slight safety buffer
    pyautogui.rightClick(center_x, center_y)
    print(f"✅ Right-clicked at previous loading popup location ({center_x}, {center_y}).")

    # Step 9: Select Spreadsheet Export Option
    spreadsheet_img = f"{session_data['anchors']}\\spreadsheet.png"
    wait_and_click(spreadsheet_img, timeout=10)
    print("✅ Clicked 'Spreadsheet' option.")

    # Step 10: Rename Export File
    text_filename = session_data.get("input_filename", "Export")
    today = time.strftime("%Y%m%d")
    export_filename = f"{text_filename}_{today}"

    pyperclip.copy(export_filename)
    time.sleep(1)
    pyautogui.hotkey('ctrl', 'v')
    print(f"✅ Renamed export file to: {export_filename}")

    # Step 11: Confirm Export
    export_img = f"{session_data['anchors']}\\export_to.png"
    wait_and_click(export_img, timeout=10)
    print("✅ Clicked 'Export to Spreadsheet'.")

    # Step 12: Set Output Folder (before saving)
    output_folder = session_data.get("output_folder", None)
    if output_folder:
        print(f"📁 Setting output folder to: {output_folder}")

        # Focus on the address bar
        time.sleep(0.5)
        pyautogui.hotkey('alt', 'd')  # Windows Explorer trick: Alt+D focuses the address bar
        time.sleep(0.5)

        # Paste the desired folder path
        pyperclip.copy(output_folder)
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.5)

        pyautogui.press('enter')
        time.sleep(1)  # wait for folder navigation

        print("✅ Output folder set.")
    else:
        print("⚠️ No output_folder provided in session_data. Saving in default folder.")


    # Step 13: Save Export
    save_img = f"{session_data['anchors']}\\save.png"
    wait_and_click(save_img, timeout=15)
    print("✅ Clicked Save.")

    # Step 14: Handle Overwrite Confirmation Popup
    overwrite_img = f"{session_data['anchors']}\\overwrite_yes.png"
    try:
        wait_and_click(overwrite_img, timeout=1)
        print("✅ Overwrite popup detected and confirmed.")
    except Exception:
        print("⚠️ No overwrite popup detected — assuming file was new.")

    # Step 15: Handle Overwrite Popup
    allow_img = f"{session_data['anchors']}\\allow.png"
    for attempt in range(2):
        try:
            wait_and_click(allow_img, timeout=10)
            print(f"✅ Clicked Allow pop-up ({attempt+1}/2).")
            time.sleep(1)
        except Exception:
            print(f"⚠️ Allow pop-up not found on attempt {attempt+1} — continuing.")

    # Step 16: Flow Complete
    print("✅ Query successfully exported!")
    print("✅ Automation sequence complete. Exiting now.")
    sys.exit(0)

def run_tcode(session_data):
    """From Easy Access, type and run the T-code."""
    print("📎 Running T-code entry flow...")
    okcode_path = f"{session_data['anchors']}\\okcode_field.png"
    
    wait_and_click(okcode_path, timeout=30)

    # 💤 Tiny delay after click to allow field focus
    time.sleep(0.5)

    pyautogui.typewrite(f"/n{session_data['tcode']}")
    pyautogui.press("enter")
    print(f"✅ T-code '{session_data['tcode']}' launched.")

      # Wait
    print("⏳ Waiting for query to execute (sleeping 5 seconds)...")
    time.sleep(5)

    # NEW: Wait for specific next screen(s)
    expected_screens = [
        f"{session_data['anchors']}\\st04.1.png",    # expected after ST04
        f"{session_data['anchors']}\\se16n_screen.png",  # expected after SE16N, if needed
        # add others as needed
    ]

    detected_screen = wait_for_specific_screen(expected_screens, timeout=30)
    print(f"✅ Detected next screen: {detected_screen}")

def input_query(session_data):
    """Click bottom center of the input field and paste large SQL query from clipboard."""
    print("📎 Running input_query action...")

    input_field_path = f"{session_data['anchors']}\\input_query.png"

    # Wait until input field is visible
    img_path = wait_for_any_image([input_field_path], timeout=30)
    location = pyautogui.locateOnScreen(img_path, confidence=0.9)
    if not location:
        raise Exception("❌ Input field image not found.")

    # Calculate bottom center of the field
    center_x = location.left + location.width // 2
    center_y = location.top + location.height - 5

    pyautogui.click(center_x, center_y)

    # Paste the text via clipboard
    text_to_input = session_data.get("input_text", "")
    if not text_to_input:
        raise Exception("❌ No input text provided for input_query.")

    pyperclip.copy(text_to_input)  # ⬅️ COPY SQL text into clipboard
    time.sleep(0.5)
    pyautogui.hotkey('ctrl', 'v')  # ⬅️ PASTE using Ctrl+V
    print(f"✅ Successfully pasted query ({len(text_to_input)} characters).") 
    print("📎 Running input_query action...")

    input_field_path = f"{session_data['anchors']}\\input_query.png"

    # Wait until input field is visible
    img_path = wait_for_any_image([input_field_path], timeout=30)
    location = pyautogui.locateOnScreen(img_path, confidence=0.9)
    if not location:
        raise Exception("❌ Input field image not found.")

    # Calculate bottom center of the found box
    center_x = location.left + location.width // 2
    center_y = location.top + location.height - 5   # 5px up from absolute bottom to avoid edge glitches

    pyautogui.click(center_x, center_y)

    # Paste the text
    text_to_input = session_data.get("input_text", "")
    if not text_to_input:
        raise Exception("❌ No input text provided for input_query.")

    pyautogui.typewrite(text_to_input)
    print(f"✅ Successfully input query: '{text_to_input}'")

def open_diagnostics(session_data):
    """From ST04, expand Diagnostics folder."""
    print("📎 Expanding Diagnostics subfolder...")
    wait_and_doubleclick(f"{session_data['anchors']}\\st04.1.png", timeout=30)
    print("✅ Diagnostics subfolder expanded.")

def open_diagnostics2(session_data):
    """From ST04, expand Diagnostics folder."""
    print("📎 Expanding Diagnostics subfolder...")
    wait_and_doubleclick(f"{session_data['anchors']}\\st04.2.png", timeout=30)
    print("✅ Diagnostics subfolder expanded.")

def execute_query(session_data):
    """Execute Query."""
    print("📎 Execute Query...")
    wait_and_click(f"{session_data['anchors']}\\execute_query.png", timeout=30)
    print("✅ Query Executed.")

def wait_for_specific_screen(target_images, timeout=30, confidence=0.9):
    """Wait until any of the specific target images appear."""
    deadline = time.time() + timeout
    last_print = time.time()

    while time.time() < deadline:
        for img_path in target_images:
            try:
                found = pyautogui.locateOnScreen(img_path, confidence=confidence)
                if found:
                    print(f"✅ Detected expected screen: {os.path.basename(img_path)}")
                    return os.path.basename(img_path)
            except Exception:
                pass  # ignore lookup errors, keep checking

        if time.time() - last_print > 5:
            print("…still waiting for expected new screen to appear...")
            last_print = time.time()

        time.sleep(0.5)

    raise TimeoutError(f"❌ New expected screen(s) did not appear after action.")
