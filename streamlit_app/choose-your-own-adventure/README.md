# ⚔️ Realms of Legend
A High Fantasy multiplayer RPG built with **Streamlit**, **Supabase**, and **Gemini AI**.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🧙 **16 Character Classes** | Fighter, Wizard, Necromancer, Blood Mage, Bard, and more |
| 🌍 **10 Races** | Human, Elf, Dwarf, Tiefling, Dragonborn, Dark Elf, Half-Giant... |
| 👾 **18 Enemies** | 5 tiers — Goblin to Ancient Dragon, weighted random spawning |
| 🤖 **Bot Companions** | Pure dice-roll AI bots, no API cost |
| 📜 **Gemini Story Gen** | DM writes a prompt → Gemini expands into a full campaign |
| 🎲 **Full D&D Combat** | HP, MP, spells, abilities, skill checks, crits, saves |
| 🗡️ **Free Actions** | Players do anything — skill checks resolve the outcome |
| 💰 **Loot + XP** | 5 rarity tiers, leveling system, gold drops |
| 🎨 **Pixel Builder** | Mix-and-match head/body/legs character sprite |
| 🌐 **Multiplayer** | 2–14 players join via 6-character campaign code |

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/realms-of-legend.git
cd realms-of-legend
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up Supabase
1. Go to [supabase.com](https://supabase.com) → New Project
2. Open **SQL Editor** and run the entire contents of `supabase_schema.sql`
3. Enable **Realtime** for tables: `campaigns`, `players`, `game_log`, `combat_encounters`
   - Go to Database → Replication → toggle these tables on

### 4. Get your API keys
- **Supabase:** Project Settings → API → copy `URL` and `anon/public` key
- **Gemini:** [Google AI Studio](https://aistudio.google.com/app/apikey) → Create API key

### 5. Configure secrets
```bash
mkdir -p .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your real keys
```

```toml
# .streamlit/secrets.toml
GEMINI_API_KEY = "AIza..."
SUPABASE_URL = "https://abc123.supabase.co"
SUPABASE_KEY = "eyJ..."
```

### 6. Run
```bash
streamlit run app.py
```

---

## 🗂️ Project Structure

```
realms-of-legend/
├── app.py                    # Entry point + routing + global CSS
├── db.py                     # All Supabase queries
├── ai.py                     # Gemini Flash integration
├── supabase_schema.sql       # Run this in Supabase SQL editor
├── requirements.txt
├── .gitignore
│
├── game/
│   ├── dice.py               # All dice rolling (d4–d100, skill checks)
│   ├── classes.py            # 16 character classes + 10 races
│   ├── enemies.py            # 18 enemy classes, weighted spawning
│   ├── combat.py             # Attack, spell, ability resolution
│   ├── loot.py               # Loot tables, rarity system, gold drops
│   └── bot.py                # Bot decision engine (no AI API)
│
├── pages/
│   ├── home.py               # Home: name entry + join/create
│   ├── campaign_create.py    # DM creates + Gemini generates story
│   ├── character_select.py   # Race/class picker + pixel builder
│   ├── lobby.py              # Waiting room with join code
│   └── game_page.py          # Main game: story + combat + log
│
└── components/
    └── character_builder.py  # Pixel sprite builder (canvas)
```

---

## 🎮 How to Play

### As DM (Campaign Creator)
1. Enter your name → **Create Campaign**
2. Write a story prompt → Gemini generates the full adventure
3. Set a win condition (e.g. "Defeat the Lich King")
4. Set bot count (0–10 bots)
5. Share the **6-letter code** with your party
6. In the lobby, click **Start Adventure** when everyone is ready
7. In-game, trigger encounters with the **Random Encounter** button

### As a Player
1. Enter your name → **Join Campaign** with the code
2. Pick your **race** and **class**, design your pixel character
3. In the game:
   - **Describe any action** in the text box → d20 skill check resolves it
   - Or pick from **AI-generated choices**
   - When combat starts, choose **Attack / Spell / Ability / Item**
   - Collect **loot**, earn **XP**, level up

### Bots
- Created automatically when the campaign starts
- They attack lowest-HP enemies, heal critical allies, use AoE spells on groups
- All done with prewritten dice logic — no API calls

---

## ⚔️ Enemy Tiers & Spawn Rates

| Tier | Examples | Spawn Rate |
|---|---|---|
| 1 — Common | Goblin, Kobold, Skeleton, Giant Rat | 45% |
| 2 — Uncommon | Orc Warrior, Hobgoblin, Zombie, Dark Elf Scout | 30% |
| 3 — Rare | Ogre, Wyvern, Vampire Spawn, Stone Golem | 15% |
| 4 — Elite | Lich, Frost Giant, Beholder | 7% |
| 5 — Legendary | Ancient Dragon, Demon Lord, Elder Lich King | 3% |

Higher party level slightly increases elite/rare spawn rates.

---

## 🧙 Character Classes

**Martial:** Fighter, Paladin, Barbarian, Ranger  
**Arcane:** Wizard, Sorcerer, Warlock, Artificer, Blood Mage, Necromancer  
**Divine:** Cleric, Druid  
**Roguish:** Rogue, Bard, Monk, Assassin  

---

## 🔑 Deploying to Streamlit Cloud

1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) → New App
3. Select your repo + `app.py`
4. Under **Advanced Settings → Secrets**, paste your secrets.toml content
5. Deploy!

---

## 🛣️ Roadmap / Future Features
- [ ] Scene images via Gemini Imagen API
- [ ] Real-time multiplayer via Supabase Realtime subscriptions
- [ ] Persistent characters across campaigns
- [ ] DM-controlled story progression panel
- [ ] Custom enemy creation
- [ ] Voice narration via TTS

---

## 📄 License
MIT — use it, fork it, adventure with it.
