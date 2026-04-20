# Neon Chess — Mobile Chess Game

Game cờ vua mobile tập trung retention + monetization (Flutter).

## Tính năng

- **Chess engine đầy đủ luật**: nhập thành, bắt tốt qua đường, phong tốt, chiếu/chiếu hết, stalemate, luật 50 nước
- **AI 4 cấp độ**: Easy (random + basic eval), Medium (minimax d=2), Hard (d=3), Master (d=4) với alpha-beta pruning, move ordering, PST
- **Boss AI có phong cách riêng**: aggressive/defensive/balanced/tactical — hệ số eval khác nhau
- **4 Game Modes**:
  - **Quick Play** — vs AI
  - **Local 2-player** — chia màn hình
  - **Daily Challenge** — 3 puzzle/ngày, giữ streak để lên bậc daily cycle 7 ngày
  - **Puzzle** — mate-in-1/2, reward theo rating
  - **Boss Battle** — 6 boss, unlock bằng level + coin
- **Retention**:
  - Daily login cycle 7 ngày (50→80→120→180→250→400→700 coin)
  - XP + level system (100 + 75×lv XP mỗi cấp)
  - Streak counter với progress bar
- **Monetization**:
  - Coin economy
  - Rewarded ad → +25 coin hoặc hint miễn phí
  - Interstitial ad sau mỗi 2 trận
  - IAP: remove ads, 3 coin packs
  - Skin shop: 4 bàn cờ + 3 bộ quân
- **UI dark neon**: gradient, glow effect, Orbitron font, animation mượt
- **Audio + vibration**: move/capture/win/lose/coin + haptic feedback

## Yêu cầu

- Flutter SDK **3.24.0+** (https://docs.flutter.dev/get-started/install)
- Android SDK 34 + build-tools
- JDK 17

## Build APK — các bước

```bash
cd C:\ThiemAICamp\chess_game

# 1) Generate missing Flutter boilerplate (gradle wrapper, ios folder, launch icons)
#    Chỉ cần chạy lần đầu
flutter create --platforms=android .

# 2) Install dependencies
flutter pub get

# 3) (Tùy chọn) Thêm sound assets
#    File MP3 vào assets/sounds/: move, capture, win, lose, coin
#    Thiếu file vẫn chạy được — AudioService bắt lỗi silently

# 4) Build APK
flutter build apk --release
```

APK: `build/app/outputs/flutter-apk/app-release.apk`

## Chạy dev

```bash
flutter run
```

## Cấu trúc source

```
lib/
├── main.dart                       # Entry, init services
├── theme/app_theme.dart            # Dark neon palette + Orbitron font
├── models/
│   ├── piece.dart, position.dart, move.dart
│   ├── board.dart                  # Initial setup + clone
│   ├── game_state.dart             # Combines board + mode + AI config
│   ├── puzzle.dart, boss.dart
├── engine/
│   ├── chess_rules.dart            # Move gen, legal moves, check detection
│   └── ai_engine.dart              # Minimax + alpha-beta + style-aware eval
├── services/
│   ├── storage_service.dart        # SharedPreferences wrapper + keys
│   ├── audio_service.dart          # audioplayers + vibration
│   ├── ads_service.dart            # google_mobile_ads (banner/intersti/rewarded)
│   ├── daily_rewards_service.dart  # 7-day cycle logic
│   ├── puzzle_repository.dart      # 8 built-in puzzles + deterministic daily
│   ├── boss_repository.dart        # 6 bosses
│   └── fen_service.dart            # FEN parse + UCI utils
├── providers/player_provider.dart  # coins/xp/level/streak/skins
├── screens/
│   ├── splash_screen.dart          # 1.2s neon logo
│   ├── main_menu_screen.dart       # Hub + daily login dialog
│   ├── daily_login_dialog.dart     # 7-day reward grid
│   ├── game_screen.dart            # Board + AI + undo + hint + end dialog
│   ├── daily_challenge_screen.dart
│   ├── puzzle_screen.dart
│   ├── battle_screen.dart          # 6 boss cards + unlock flow
│   └── shop_screen.dart            # Skins + coin packs + remove ads
└── widgets/
    ├── chess_board_widget.dart     # 8x8 grid + legal highlight + last move
    ├── neon_button.dart            # Glowing button with gradient
    ├── coin_badge.dart, xp_bar.dart
```

## Ad Unit IDs

`lib/services/ads_service.dart` + `AndroidManifest.xml` đang dùng **Google test ad IDs**. Trước khi release:

1. Tạo AdMob app → lấy `App ID` → thay trong `AndroidManifest.xml`
2. Tạo ad units (banner/interstitial/rewarded) → thay 3 const ở đầu `ads_service.dart`

## Tùy chỉnh / mở rộng

- **Stockfish Hard+**: thêm package `stockfish: ^1.5.0`, gọi UCI trong `AiEngine.chooseMove` khi `level == master`
- **Thêm puzzle**: thêm entry vào `PuzzleRepository.puzzles` (FEN + UCI solution)
- **Thêm boss**: append vào `BossRepository.bosses` với `BossStyle` tương ứng
- **Backend leaderboard** (nếu muốn): wrap `PlayerProvider.addXp` → POST lên server

## Cảnh báo kỹ thuật

- AI Master (depth 4) có thể chạy 200-800ms trên máy trung bình — đã chấp nhận UX "AI đang suy nghĩ". Để không chặn UI hoàn toàn, cân nhắc chuyển sang `Isolate` khi scale độ sâu.
- `shared_preferences` đủ cho MVP offline. Khi cần sync: migrate sang `drift` hoặc `isar`.

## License

MIT — free to use / modify / monetize.
