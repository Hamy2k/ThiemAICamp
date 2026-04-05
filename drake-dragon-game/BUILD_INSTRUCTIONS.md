# Drake Dragon: Mosquito Hunt - Build Instructions

## Prerequisites

1. **Godot 4.2+** - Download from https://godotengine.org/download
2. **Android Build Template** (for APK export):
   - Android Studio or Android SDK command-line tools
   - JDK 17+
   - Android SDK (API 34)

## Quick Start (Desktop Testing)

1. Open Godot 4.2+
2. Click "Import" > navigate to `drake-dragon-game/` > select `project.godot`
3. Press F5 or click "Play" button
4. Controls:
   - **Mouse click + drag** on left joystick area to move
   - **Click ZAP button** (or press Space) to swing racket
   - Walk into mosquitoes' range to attract them
   - Kill them before they bite you 100 times!

## Project Structure

```
drake-dragon-game/
├── project.godot              # Godot project config
├── scenes/
│   └── main.tscn              # Main scene (loads scene_builder.gd)
├── scripts/
│   ├── game_manager.gd        # Global state (autoload singleton)
│   ├── scene_builder.gd       # Procedurally builds entire game scene
│   ├── player.gd              # Player movement + racket swing
│   ├── mosquito.gd            # Mosquito AI (idle/chase/attack/die)
│   ├── mosquito_spawner.gd    # Wave spawning with difficulty scaling
│   ├── camera_controller.gd   # Third-person follow camera
│   ├── room_builder.gd        # Procedural room + furniture
│   ├── virtual_joystick.gd    # Mobile touch joystick
│   ├── game_ui.gd             # HUD + Game Over screen
│   ├── powerup.gd             # Shield / Strong Racket pickups
│   └── powerup_spawner.gd     # Random powerup spawning
├── export/
│   └── export_presets.cfg      # Android export config
└── BUILD_INSTRUCTIONS.md
```

## Android APK Export

### Step 1: Setup Android SDK in Godot

1. Open Godot > Editor > Editor Settings
2. Search "Android"
3. Set paths:
   - **Android SDK Path**: e.g., `C:\Users\YOU\AppData\Local\Android\Sdk`
   - **Debug Keystore**: auto-generated, or set your own
   - **Java SDK Path**: e.g., `C:\Program Files\Java\jdk-17`

### Step 2: Install Export Template

1. Editor > Manage Export Templates
2. Click "Download and Install" for your Godot version
3. Wait for download to complete

### Step 3: Export APK

1. Project > Export
2. Select "Android" preset (already configured in export_presets.cfg)
3. Click "Export Project"
4. Choose output path: `export/drake-dragon.apk`
5. Click "Save"

### Step 4: Install on Device

```bash
# Via ADB
adb install export/drake-dragon.apk

# Or transfer APK to phone and install manually
```

## Game Features

### Mosquito Types
| Type | Speed | HP | Special |
|------|-------|----|---------|
| Normal | 3.0 | 1 | Standard mosquito |
| Fast | 5.5 | 1 | Green, wider detection |
| Tanky | 2.0 | 3 | Red, 1.5x bigger, takes 3 hits |
| Stealth | 3.5 | 1 | Nearly invisible until close |

### Scoring
- Base kill: 10 points
- Combo bonus: +5 per combo level
- Strong Racket: 1.5x multiplier

### Difficulty Scaling
- Mosquito speed increases over time
- More mosquitoes spawn as game progresses
- Special types appear after 1-2 minutes
- Max 15 mosquitoes at once

### Power-Ups
- **Shield** (blue): Blocks all bites for 8 seconds
- **Strong Racket** (gold): 1.5x score + damage for 10 seconds

## Customizing Assets

All visuals are procedurally generated with primitive meshes.
To replace with real art:

1. **Character model**: Replace body/head meshes in `scene_builder.gd:_build_player()`
2. **Mosquito model**: Replace mesh in `mosquito_spawner.gd:_create_mosquito_scene()`
3. **Room**: Edit `room_builder.gd` furniture positions/colors
4. **UI textures**: Replace procedural joystick in `virtual_joystick.gd`
5. **Audio**: Add .ogg/.wav files to `audio/` and load in scripts

### Adding Sound Effects

In `player.gd`, add after zap effect:
```gdscript
var zap_sound = AudioStreamPlayer.new()
zap_sound.stream = load("res://audio/zap.ogg")
add_child(zap_sound)
zap_sound.play()
```

## Performance Notes

- Targets 30 FPS on mid-range Android devices
- Mobile renderer enabled (no desktop-only features)
- Max 15 mosquitoes + particles = light GPU load
- No textures to load = fast startup
- Procedural generation = tiny APK size (~5-10 MB)
