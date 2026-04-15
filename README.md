# cliping-script-for-obs

## :movie_camera: OBS Clipping Setup Guide

### 1. Install Required Programs

Download and install:

* OBS Studio 32.1.1 or newer
* Python 3.11.9

---

### 2. Set Up Python in OBS

1. Open OBS
2. Go to **Tools → Scripts**
3. Click **Python Settings**
4. Set your Python path (usually):

```
C:\Users\YOUR NAME\AppData\Local\Programs\Python\Python311
```

---

### 3. Add the Clipping Script

1. Download the script and save it somewhere easy to find
2. In OBS:

   * Go to **Tools → Scripts**
   * Click the **+ (bottom left)**
   * Select your script
3. On the right side:

   * Find **Base Clips Folder**
   * Choose where your clips will be saved

---

### 4. Set Up Display Capture

1. In the **Sources** box:

   * Click **+**
   * Add a new **Scene** (name it “Display Capture”)
2. Add a **Display Capture source**

   * Select your monitor

---

### 5. Enable Replay Buffer

1. Go to **Settings → Output**
2. Find **Replay Buffer**
3. Enable it
4. Set your clip length (example: 45 seconds)

---

### 6. Set a Clip Hotkey

1. Go to **Settings → Hotkeys**
2. Find **Save & Sort Clip**
3. Set a keybind (example: Alt + 1)

---

### 7. Start Clipping

1. Back in OBS:

   * Click **Start Replay Buffer**
2. Press your hotkey anytime to save a clip :video_game:

---

## :gear: Auto-Start OBS on Boot (Optional)

1. Right-click OBS → **Properties → Open File Location**

2. Right-click **obs64.exe → Create Shortcut**

3. Press **Win + R** and type:

```
shell:startup
```

4. Paste the shortcut into that folder

5. Right-click the shortcut → **Properties**

6. In **Target**, add this at the end:

```
--startreplaybuffer --minimize-to-tray --disable-updater
```

7. Click **Apply → OK**

---

:white_check_mark: Done! OBS will now auto-start and be ready to clip.
