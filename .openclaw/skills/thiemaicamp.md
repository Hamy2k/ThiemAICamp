# ThiemAICamp - Telegram Bot Skill

## Description
Ket noi Telegram bot voi ThiemAICamp AI Software Office pipeline.
Nhan lenh tu Telegram, parse yeu cau, chay pipeline, tra ket qua ve Telegram.

## Trigger
- Khi nhan tin nhan tu Telegram bot co chua `/build`, `/status`, `/approve`, `/reject`, `/run`, `/templates`, `/memory`
- Khi nhan tin nhan bat ky (free-form task description)

## Setup

### 1. Tao Telegram Bot
```
1. Mo Telegram, tim @BotFather
2. Gui /newbot
3. Dat ten: ThiemAICamp Bot
4. Dat username: thiemaicamp_bot
5. Nhan BOT_TOKEN
6. Set env: export TELEGRAM_BOT_TOKEN=your_token
```

### 2. Cai dependencies
```bash
pip install python-telegram-bot
```

### 3. Chay bot
```bash
python -m src.telegram_bot
```

## Commands

| Command | Mo ta | Vi du |
|---------|-------|-------|
| `/build <name> <desc>` | Tao project moi qua pipeline | `/build MyAPI REST API cho users` |
| `/run <task>` | Chay 1 task don le | `/run Viet function login voi JWT` |
| `/status` | Xem trang thai he thong | `/status` |
| `/approve <id>` | Approve request dang cho | `/approve approval_0001` |
| `/reject <id> <reason>` | Reject request | `/reject approval_0001 Chua test du` |
| `/templates` | Xem danh sach templates | `/templates` |
| `/scaffold <type> <name>` | Tao project tu template | `/scaffold saas MySaaS` |
| `/memory <query>` | Tim trong memory store | `/memory database pattern` |
| `/score` | Xem diem va metrics | `/score` |
| Free text | Gui task cho AI pipeline | `Tao REST API cho todo app` |

## Flow

```
Telegram Message
    │
    ▼
Parse Command/Text
    │
    ├─ /build ──────► Pipeline.run_project()
    │                     │
    │                     ├─ Planning (memory search)
    │                     ├─ Approval (neu can)
    │                     ├─ Development (4 agents)
    │                     ├─ Review + QA
    │                     └─ Tra ket qua ◄──── Telegram Reply
    │
    ├─ /run ──────���─► Pipeline.run_single_task()
    │                     └─ Tra code ◄──── Telegram Reply
    │
    ├─ /status ─────► Pipeline.get_system_status()
    │                     └─ Tra status ◄── Telegram Reply
    │
    ├─ /approve ────► ApprovalSystem.approve()
    ├─ /reject ─────► ApprovalSystem.reject()
    ├─ /templates ──► TemplateManager.list_templates()
    ├─ /scaffold ───► TemplateManager.scaffold()
    ├─ /memory ─────► MemoryStore.search_all()
    │
    └─ Free text ──► Pipeline.run_single_task() (auto-detect role)
```

## Response Format

### Build Result
```
✅ Pipeline COMPLETED: MyAPI

📊 Summary:
- Tasks: 3
- Files written: 5
- Review score: 8.5/10

📁 Files:
- src/api/users.py
- src/api/auth.py
- src/models/user.py

⏱ Duration: 45.2s
```

### Error
```
❌ Pipeline FAILED: MyAPI
Error: Agent api failed: timeout

💡 Thu lai voi: /build MyAPI REST API
```

### Status
```
📊 ThiemAICamp Status

🤖 Team:
  API: ✅ available
  UI: ✅ available
  Auth: ✅ available
  DB: ✅ available

📋 Pending Approvals: 0
📈 Total Runs: 15
🎯 Score: 2,450
🧠 Memory: 23 patterns, 8 bugs, 5 ADRs
```

## Code

File: `src/telegram_bot.py`
