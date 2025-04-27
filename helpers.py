# helpers.py

import time
import pyautogui
import datetime
import sys
import os

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3

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

def wait_for_image(img_path, timeout=30, confidence=0.9):
    deadline = time.time() + timeout
    last_print = time.time()

    while time.time() < deadline:
        try:
            loc = pyautogui.locateCenterOnScreen(img_path, confidence=confidence)
            if loc:
                return loc
        except Exception:
            pass

        if time.time() - last_print > 5:
            print(f"…still waiting for {img_path} to appear...")
            last_print = time.time()

        time.sleep(0.5)

    return None


def wait_for_any_image(images, timeout=30, confidence=0.9):
    deadline = time.time() + timeout
    last_print = time.time()

    while time.time() < deadline:
        for img_path in images:
            try:
                loc = pyautogui.locateOnScreen(img_path, confidence=confidence)
                if loc:
                    return img_path
            except Exception:
                pass
        if time.time() - last_print > 5:
            print("…still waiting for a known screen to appear...")
            last_print = time.time()
        time.sleep(0.5)

    raise TimeoutError(f"❌ Timeout waiting for any of: {images}")

def wait_and_click(image_path, timeout=30, confidence=0.9):
    img = wait_for_any_image([image_path], timeout, confidence)
    center = pyautogui.locateCenterOnScreen(img, confidence=confidence)
    if not center:
        raise Exception(f"❌ Could not locate center of {img}")
    pyautogui.click(center)

def wait_and_doubleclick(image_path, timeout=30, confidence=0.9):
    img = wait_for_any_image([image_path], timeout, confidence)
    center = pyautogui.locateCenterOnScreen(img, confidence=confidence)
    if not center:
        raise Exception(f"❌ Could not locate center of {img}")
    pyautogui.doubleClick(center)

def capture_screenshot(save_folder="Logs", prefix="error"):
    """Capture the screen and save it with a timestamp."""
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}_{timestamp}.png"
    filepath = os.path.join(save_folder, filename)

    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)

    print(f"📸 Saved screenshot: {filepath}")
    return filepath

def wait_until_image_disappears(image_path, timeout=60, confidence=0.9):
    """Wait until a specific image disappears from the screen."""
    deadline = time.time() + timeout
    last_print = time.time()

    while time.time() < deadline:
        try:
            still_there = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if not still_there:
                print(f"✅ Image disappeared: {os.path.basename(image_path)}")
                return True
        except Exception:
            return True  # assume disappeared if image lookup fails

        if time.time() - last_print > 5:
            print("…still waiting for loading to finish...")
            last_print = time.time()

        time.sleep(0.5)

    raise TimeoutError(f"❌ Image still visible after timeout: {os.path.basename(image_path)}")

def load_query_from_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

class Logger:
    def __init__(self, log_folder="Logs"):
        self.log_folder = log_folder
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logfile_path = os.path.join(log_folder, f"log_{timestamp}.txt")

        # Open file handle
        self.logfile = open(self.logfile_path, "a", encoding="utf-8")

        # Optionally redirect stdout completely
        # sys.stdout = self

    def write(self, message):
        print(message)  # Still show in console
        self.logfile.write(message + "\n")
        self.logfile.flush()

    def close(self):
        self.logfile.close()

# Usage example:
# logger = Logger()
# logger.write("Hello world")
