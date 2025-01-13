# Hand Detection Demo

This project demonstrates hand movement and gesture detection using Python Mediapipe and includes a Unity-based game demo.

---

## Instructions

### Step 1: Launch the Hand Tracker
1. Navigate to the `Hand Tracker` directory.
2. Run `handTracker.exe`.
3. Wait for the script to initialize the camera and hand tracking logic.

**Note:** If no errors occur, skip to [Step 3](#step-3-run-the-demo). If you encounter errors, follow [Step 2](#step-2-manual-setup).

---

### Step 2: Manual Setup (in case of errors)
If the executable fails, manually set up the environment and run the Python script:

1. Open a terminal in the project directory.
2. Create a virtual environment:
   ```bash
   python -m venv myenv
   ```
3. Activate the virtual environment:
   - On Windows:
     ```bash
     myenv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source myenv/bin/activate
     ```
4. Install all dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run the project:
   ```bash
   python main.py
   ```
6. Wait for the script to initialize the camera and hand tracking logic. This may take some time on slower computers.

---

### Step 3: Run the Demo
1. Run `Game/HandDetection.exe`.
2. Enjoy the hand movement and gesture detection demo!

---
