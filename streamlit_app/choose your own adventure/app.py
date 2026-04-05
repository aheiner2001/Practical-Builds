
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ── Page Config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Realms of Legend",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── Global Styling ─────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;600;700&family=Crimson+Text:ital,wght@0,400;0,600;1,400&display=swap');

  /* Base theme */
  .stApp {
    background-color: #0a0a1a;
    color: #e8e0d0;
  }

  /* Headings */
  h1, h2, h3 {
    font-family: 'Cinzel', serif !important;
    color: #FFD700 !important;
    text-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
  }

  h4, h5, h6 {
    font-family: 'Cinzel', serif !important;
    color: #c0a060 !important;
  }

  /* Body text */
  p, li, label, .stMarkdown {
    font-family: 'Crimson Text', serif !important;
    font-size: 1.05rem;
    color: #e8e0d0;
  }

  /* Cards / Containers */
  .stContainer, [data-testid="stVerticalBlock"] {
    background: transparent;
  }

  /* Buttons */
  .stButton > button {
    font-family: 'Cinzel', serif !important;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    border: 1px solid #4a3a1a;
    background: #1a1a2e;
    color: #e8d5a0;
    transition: all 0.2s ease;
  }

  .stButton > button:hover {
    border-color: #FFD700;
    color: #FFD700;
    box-shadow: 0 0 12px rgba(255, 215, 0, 0.2);
    transform: translateY(-1px);
  }

  .stButton > button[kind="primary"] {
    background: #2a1a00;
    border-color: #FFD700;
    color: #FFD700;
  }

  .stButton > button[kind="primary"]:hover {
    background: #3a2a00;
    box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
  }

  /* Text inputs */
  .stTextInput > div > div > input,
  .stTextArea > div > div > textarea {
    background: #0f0f23 !important;
    color: #e8e0d0 !important;
    border: 1px solid #3a3a5a !important;
    font-family: 'Crimson Text', serif !important;
    font-size: 1rem !important;
  }

  /* Selectbox */
  .stSelectbox > div > div {
    background: #0f0f23 !important;
    color: #e8e0d0 !important;
    border-color: #3a3a5a !important;
  }

  /* Progress bars */
  .stProgress > div > div > div {
    background: linear-gradient(90deg, #8B0000, #cc2200);
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #0a0a14 !important;
    border-right: 1px solid #2a2a3a;
  }

  [data-testid="stSidebar"] h3 {
    font-size: 1rem !important;
  }

  /* Tabs */
  .stTabs [data-baseweb="tab"] {
    font-family: 'Cinzel', serif !important;
    color: #888 !important;
    font-size: 0.85rem;
  }

  .stTabs [aria-selected="true"] {
    color: #FFD700 !important;
    border-bottom-color: #FFD700 !important;
  }

  /* Divider */
  hr {
    border-color: #2a2a3a;
  }

  /* Expander */
  .streamlit-expanderHeader {
    font-family: 'Cinzel', serif !important;
    color: #c0a060 !important;
  }

  /* Metrics */
  [data-testid="stMetricValue"] {
    color: #FFD700 !important;
    font-family: 'Cinzel', serif !important;
  }

  /* Info/Success/Error boxes */
  .stAlert {
    background: #0f0f23 !important;
    border-left: 4px solid #444;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0a0a14; }
  ::-webkit-scrollbar-thumb { background: #3a3a5a; border-radius: 3px; }
  ::-webkit-scrollbar-thumb:hover { background: #FFD700; }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "home"
if "game_mode" not in st.session_state:
    st.session_state["game_mode"] = "story"

# ── Router ────────────────────────────────────────────────────────────
page = st.session_state.get("page", "home")

if page == "home":
    from pages.home import render_home
    render_home()

elif page == "campaign_create":
    from pages.campaign_create import render_campaign_create
    render_campaign_create()

elif page == "character_select":
    from pages.character_select import render_character_select
    render_character_select()

elif page == "lobby":
    from pages.lobby import render_lobby
    render_lobby()

elif page == "game":
    from pages.game_page import render_game
    render_game()

else:
    st.error(f"Unknown page: {page}")
    if st.button("Go Home"):
        st.session_state["page"] = "home"
        st.rerun()
import random
from dataclasses import dataclass, field

# ── Enemy System ─────────────────────────────────────────────────────
# 18 enemies across 5 tiers. Lower tiers spawn far more often.
# Spawn weights: Common > Uncommon > Rare > Elite > Legendary

@dataclass
class EnemyClass:
    name: str
    tier: int               # 1=Common, 2=Uncommon, 3=Rare, 4=Elite, 5=Legendary
    emoji: str
    description: str
    hp: int
    max_hp: int
    armor_class: int        # AC: how hard to hit
    attack_bonus: int       # bonus added to attack rolls
    damage_dice: str        # e.g. "1d6", "2d8+3"
    xp_reward: int
    loot_table: list[str]   # possible drops
    abilities: list[str] = field(default_factory=list)
    weakness: str = ""
    resistance: str = ""
    lore: str = ""

    def copy_instance(self) -> dict:
        """Return a mutable instance dict (for combat tracking)."""
        return {
            "name": self.name,
            "tier": self.tier,
            "emoji": self.emoji,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "armor_class": self.armor_class,
            "attack_bonus": self.attack_bonus,
            "damage_dice": self.damage_dice,
            "xp_reward": self.xp_reward,
            "loot_table": self.loot_table,
            "abilities": self.abilities,
            "weakness": self.weakness,
            "resistance": self.resistance,
            "is_alive": True,
        }

ENEMIES: dict[str, EnemyClass] = {

    # ── TIER 1: COMMON ──────────────────────────────────────────────

    "Goblin": EnemyClass(
        name="Goblin", tier=1, emoji="👺",
        description="Sneaky little troublemakers armed with rusty blades.",
        hp=7, max_hp=7, armor_class=11, attack_bonus=2, damage_dice="1d6",
        xp_reward=50, loot_table=["Rusty Dagger","Gold Coin","Goblin Ear"],
        abilities=["Nimble Escape"],
        weakness="Fire", lore="Goblins swarm in packs, relying on numbers and cowardice."
    ),

    "Kobold": EnemyClass(
        name="Kobold", tier=1, emoji="🦎",
        description="Draconic little scavengers who fight dirty in groups.",
        hp=5, max_hp=5, armor_class=12, attack_bonus=2, damage_dice="1d4",
        xp_reward=40, loot_table=["Shiny Pebble","Crude Spear","Kobold Scale"],
        abilities=["Pack Tactics"],
        weakness="Radiant", lore="Kobolds worship dragons and mimic their tactics — poorly."
    ),

    "Skeleton": EnemyClass(
        name="Skeleton", tier=1, emoji="💀",
        description="Animated bones held together by dark magic.",
        hp=13, max_hp=13, armor_class=13, attack_bonus=2, damage_dice="1d6+2",
        xp_reward=50, loot_table=["Bone Fragment","Ancient Coin","Rusty Sword"],
        abilities=["Undead Fortitude"],
        weakness="Bludgeoning", resistance="Piercing",
        lore="Once warriors, now mindless soldiers serving a long-dead necromancer."
    ),

    "Giant Rat": EnemyClass(
        name="Giant Rat", tier=1, emoji="🐀",
        description="Diseased rodents the size of a dog. Carriers of plague.",
        hp=9, max_hp=9, armor_class=10, attack_bonus=1, damage_dice="1d4",
        xp_reward=25, loot_table=["Rat Pelt","Diseased Fang"],
        abilities=["Disease Bite: on hit, DC 11 CON save or become poisoned"],
        weakness="Fire", lore="Mutated by dark magic in the depths of the dungeon."
    ),

    # ── TIER 2: UNCOMMON ────────────────────────────────────────────

    "Orc Warrior": EnemyClass(
        name="Orc Warrior", tier=2, emoji="👹",
        description="Fierce tribal warrior with brutal strength and thick skin.",
        hp=25, max_hp=25, armor_class=13, attack_bonus=4, damage_dice="1d8+3",
        xp_reward=100, loot_table=["Orc Blade","Chainmail Scraps","Orc Talisman","Gold Pouch"],
        abilities=["Aggressive: bonus action to move toward enemy"],
        weakness="Radiant", lore="Orcs live for battle and consider dying in combat an honor."
    ),

    "Hobgoblin": EnemyClass(
        name="Hobgoblin", tier=2, emoji="🪖",
        description="Militaristic, disciplined goblinoid who fights in formation.",
        hp=18, max_hp=18, armor_class=15, attack_bonus=3, damage_dice="1d8+1",
        xp_reward=100, loot_table=["Military Sword","Shield Fragment","Commander's Badge"],
        abilities=["Martial Advantage: +2d6 damage when ally is adjacent to target"],
        resistance="Fear",
        lore="Hobgoblins are the soldiers of goblinoid armies, trained and dangerous."
    ),

    "Zombie": EnemyClass(
        name="Zombie", tier=2, emoji="🧟",
        description="Slow but relentless undead. Hard to put down for good.",
        hp=22, max_hp=22, armor_class=8, attack_bonus=3, damage_dice="1d6+1",
        xp_reward=50, loot_table=["Tattered Cloth","Rotten Flesh","Cursed Trinket"],
        abilities=["Undead Fortitude: on death, DC 5+damage CON save to stay at 1 HP"],
        weakness="Radiant", lore="Zombies hunger endlessly and never know fear."
    ),

    "Dark Elf Scout": EnemyClass(
        name="Dark Elf Scout", tier=2, emoji="🌑",
        description="Stealthy underground elf who attacks from the shadows.",
        hp=16, max_hp=16, armor_class=14, attack_bonus=4, damage_dice="1d6+2",
        xp_reward=150, loot_table=["Poison Vial","Drow Rapier","Shadow Cloak","Dark Elf Token"],
        abilities=["Darkness: cast darkness once per combat", "Sneak Attack"],
        weakness="Sunlight",
        lore="Dark elves patrol the Underdark, hostile to all surface dwellers."
    ),

    # ── TIER 3: RARE ────────────────────────────────────────────────

    "Ogre": EnemyClass(
        name="Ogre", tier=3, emoji="👾",
        description="Massive brute with earth-shaking power and thick hide.",
        hp=59, max_hp=59, armor_class=11, attack_bonus=6, damage_dice="2d8+4",
        xp_reward=450, loot_table=["Ogre Club","Giant Boots","Crude Armor","Treasure Sack"],
        abilities=["Great Slam: knockback on crit"],
        weakness="Fire",
        lore="Ogres are solitary hunters who eat anything smaller than themselves."
    ),

    "Wyvern": EnemyClass(
        name="Wyvern", tier=3, emoji="🐲",
        description="Two-legged dragon cousin with a venomous stinger.",
        hp=40, max_hp=40, armor_class=13, attack_bonus=7, damage_dice="2d6+4",
        xp_reward=700, loot_table=["Wyvern Stinger","Dragon Scale (small)","Venom Sac"],
        abilities=["Poison Stinger: DC 15 CON save or 3d6 poison damage", "Flyby"],
        weakness="Cold", resistance="Fire",
        lore="Though not true dragons, wyverns are among the most feared beasts of the skies."
    ),

    "Vampire Spawn": EnemyClass(
        name="Vampire Spawn", tier=3, emoji="🧛",
        description="Undead bloodsucker with supernatural speed and charm.",
        hp=32, max_hp=32, armor_class=13, attack_bonus=5, damage_dice="1d8+3",
        xp_reward=400, loot_table=["Blood Vial","Silver Ring","Vampire Fang","Dark Cloak"],
        abilities=["Blood Drain: restore HP equal to damage dealt", "Charm: DC 13 WIS save"],
        weakness="Radiant", resistance="Necrotic",
        lore="Created by a vampire lord's bite, these spawn hunger eternally for blood."
    ),

    "Golem (Stone)": EnemyClass(
        name="Golem (Stone)", tier=3, emoji="🗿",
        description="Magically animated stone construct. Nearly impervious to weapons.",
        hp=55, max_hp=55, armor_class=17, attack_bonus=7, damage_dice="3d8+5",
        xp_reward=600, loot_table=["Golem Core","Enchanted Stone","Mana Crystal"],
        abilities=["Immutable Form: immune to spell alteration", "Slam"],
        weakness="Bludgeoning", resistance="Piercing,Slashing",
        lore="Built by ancient wizards as guardians, golems follow their last command forever."
    ),

    # ── TIER 4: ELITE ───────────────────────────────────────────────

    "Lich": EnemyClass(
        name="Lich", tier=4, emoji="☠️",
        description="Undead archmage of terrifying power. Commands the dead.",
        hp=75, max_hp=75, armor_class=17, attack_bonus=8, damage_dice="4d6+5",
        xp_reward=2500, loot_table=["Lich Phylactery Fragment","Tome of Dark Magic","Ancient Staff","Death Crystal"],
        abilities=["Paralyzing Touch", "Frightening Presence", "Spellcasting: Fireball/Chain Lightning"],
        weakness="Radiant", resistance="Cold,Lightning,Necrotic",
        lore="A wizard who sought immortality through dark ritual — and found it, at horrible cost."
    ),

    "Frost Giant": EnemyClass(
        name="Frost Giant", tier=4, emoji="🧊",
        description="Ancient giant of the frozen north. Commands ice and storm.",
        hp=90, max_hp=90, armor_class=15, attack_bonus=9, damage_dice="3d8+7",
        xp_reward=1800, loot_table=["Giant's Greatsword","Frost Core","Giant Rune Stone","Frozen Crown"],
        abilities=["Hurl Rock: ranged 60ft attack", "Blizzard Breath: cone of cold"],
        weakness="Fire", resistance="Cold",
        lore="Frost Giants dwell in mountaintop fortresses, raiding villages during winter."
    ),

    "Beholder": EnemyClass(
        name="Beholder", tier=4, emoji="👁️",
        description="Floating orb of eyes with multiple devastating eye rays.",
        hp=65, max_hp=65, armor_class=18, attack_bonus=7, damage_dice="2d8+4",
        xp_reward=2000, loot_table=["Beholder Eye","Central Eye","Antimagic Lens","Aberrant Bile"],
        abilities=["Eye Rays: random debuff each turn", "Antimagic Cone: suppress spells", "Death Ray"],
        resistance="All physical",
        lore="Beholders are paranoid, alien creatures that see all other life as inferior."
    ),

    # ── TIER 5: LEGENDARY ───────────────────────────────────────────

    "Ancient Dragon": EnemyClass(
        name="Ancient Dragon", tier=5, emoji="🐉",
        description="Wyrm of unfathomable age. A natural disaster given form.",
        hp=200, max_hp=200, armor_class=22, attack_bonus=14, damage_dice="4d10+8",
        xp_reward=15000, loot_table=["Dragon Heart","Dragon Scale (ancient)","Hoard Gem","Dragon Skull","Ancient Treasure"],
        abilities=["Fire Breath: 8d6 fire damage cone", "Wing Attack", "Legendary Resistance (3/day)",
                   "Frightful Presence: DC 19 WIS save or frightened"],
        weakness="None", resistance="Fire",
        lore="Ancient dragons are among the most powerful creatures in existence."
    ),

    "Demon Lord": EnemyClass(
        name="Demon Lord", tier=5, emoji="👿",
        description="Prince of the Abyss. Reality warps around its presence.",
        hp=160, max_hp=160, armor_class=20, attack_bonus=12, damage_dice="4d8+9",
        xp_reward=12000, loot_table=["Demon Core","Abyssal Rune","Chaotic Shard","Lord's Sigil"],
        abilities=["Abyssal Burst: 6d8 necrotic", "Summon Demons (1/day)", "Legendary Resistance (3/day)",
                   "Hellfire Aura: 2d6 fire damage to adjacent creatures"],
        weakness="Radiant", resistance="Fire,Cold,Lightning,Poison",
        lore="Demon Lords command vast armies of the Abyss and seek to corrupt all light."
    ),

    "Elder Lich King": EnemyClass(
        name="Elder Lich King", tier=5, emoji="💀👑",
        description="Master of all undead. Has died and returned so many times death fears HIM.",
        hp=180, max_hp=180, armor_class=21, attack_bonus=13, damage_dice="5d6+8",
        xp_reward=14000, loot_table=["Crown of the Lich King","Phylactery of Eternity","Necronomicon","Death Shard"],
        abilities=["Necromantic Burst", "Raise Army (resurrect fallen enemies)", "Soul Drain",
                   "Legendary Resistance (3/day)", "Undying: at 0 HP, roll DC 15 or return at 30 HP"],
        weakness="Radiant", resistance="Cold,Lightning,Necrotic,Poison",
        lore="The original necromancer. He has transcended death itself and now rules the undead realm."
    ),
}

# ── Spawn weight table (higher = more common) ────────────────────────
TIER_WEIGHTS = {1: 45, 2: 30, 3: 15, 4: 7, 5: 3}

def get_enemies_by_tier(tier: int) -> list[EnemyClass]:
    return [e for e in ENEMIES.values() if e.tier == tier]

def spawn_random_enemy() -> dict:
    """Pick a random enemy using tier-weighted probability."""
    tier = random.choices(list(TIER_WEIGHTS.keys()), weights=list(TIER_WEIGHTS.values()))[0]
    pool = get_enemies_by_tier(tier)
    if not pool:
        pool = get_enemies_by_tier(1)
    enemy_class = random.choice(pool)
    return enemy_class.copy_instance()

def spawn_encounter(party_level: int = 1, party_size: int = 2) -> list[dict]:
    """
    Generate a list of enemies for an encounter.
    Scales with party level and size.
    Higher party level slightly increases elite/rare chance.
    """
    # Base enemy count: 1 to party_size+1
    base_count = random.randint(1, max(2, party_size))

    # Boost rare/elite weights slightly for higher level parties
    weights = dict(TIER_WEIGHTS)
    boost = min(party_level - 1, 4)
    if boost > 0:
        weights[3] = min(weights[3] + boost * 2, 30)
        weights[4] = min(weights[4] + boost, 15)
        weights[1] = max(weights[1] - boost * 2, 15)

    enemies = []
    for _ in range(base_count):
        tier = random.choices(list(weights.keys()), weights=list(weights.values()))[0]
        pool = get_enemies_by_tier(tier)
        if pool:
            enemies.append(random.choice(pool).copy_instance())

    return enemies

def describe_encounter(enemies: list[dict]) -> str:
    """Human-readable encounter description."""
    counts = {}
    for e in enemies:
        counts[e["name"]] = counts.get(e["name"], 0) + 1
    parts = []
    for name, count in counts.items():
        emoji = ENEMIES[name].emoji if name in ENEMIES else ""
        if count == 1:
            parts.append(f"{emoji} {name}")
        else:
            parts.append(f"{emoji} {count}x {name}")
    return " and ".join(parts) if parts else "Unknown enemies"
from dataclasses import dataclass, field

# ── Character Classes ────────────────────────────────────────────────
# 16 classes across 4 archetypes: Martial, Arcane, Divine, Roguish

@dataclass
class CharacterClass:
    name: str
    archetype: str          # Martial | Arcane | Divine | Roguish
    description: str
    emoji: str
    hit_die: int            # d6, d8, d10, d12
    primary_stat: str
    secondary_stat: str
    base_stats: dict        # STR DEX INT CON CHA WIS
    base_hp: int
    base_mp: int
    spells: list[str] = field(default_factory=list)
    abilities: list[str] = field(default_factory=list)
    weapon_proficiencies: list[str] = field(default_factory=list)
    armor_proficiencies: list[str] = field(default_factory=list)
    lore: str = ""

CLASSES: dict[str, CharacterClass] = {

    # ── MARTIAL ─────────────────────────────────────────────────────

    "Fighter": CharacterClass(
        name="Fighter", archetype="Martial", emoji="⚔️",
        description="Master of weapons and armor. Tough, reliable, and deadly in close combat.",
        hit_die=10, primary_stat="strength", secondary_stat="constitution",
        base_stats={"strength":16,"dexterity":12,"intelligence":8,"constitution":15,"charisma":10,"wisdom":10},
        base_hp=30, base_mp=0,
        abilities=["Second Wind", "Action Surge", "Shield Block", "Weapon Mastery"],
        weapon_proficiencies=["Sword","Axe","Mace","Bow","Crossbow"],
        armor_proficiencies=["Light","Medium","Heavy","Shield"],
        lore="Trained in the art of war, fighters excel at sustained combat."
    ),

    "Paladin": CharacterClass(
        name="Paladin", archetype="Martial", emoji="🛡️",
        description="Holy warrior combining martial might with divine magic.",
        hit_die=10, primary_stat="strength", secondary_stat="charisma",
        base_stats={"strength":15,"dexterity":10,"intelligence":10,"constitution":14,"charisma":14,"wisdom":12},
        base_hp=28, base_mp=15,
        spells=["Divine Smite", "Lay on Hands", "Bless", "Protection from Evil"],
        abilities=["Divine Smite", "Aura of Protection", "Sacred Weapon"],
        weapon_proficiencies=["Sword","Mace","Warhammer"],
        armor_proficiencies=["Light","Medium","Heavy","Shield"],
        lore="Sworn to a sacred oath, paladins channel holy power through martial prowess."
    ),

    "Barbarian": CharacterClass(
        name="Barbarian", archetype="Martial", emoji="🪓",
        description="Primal warrior who channels rage into unstoppable fury.",
        hit_die=12, primary_stat="strength", secondary_stat="constitution",
        base_stats={"strength":18,"dexterity":13,"intelligence":7,"constitution":17,"charisma":8,"wisdom":9},
        base_hp=36, base_mp=0,
        abilities=["Rage", "Reckless Attack", "Brutal Critical", "Danger Sense", "Frenzy"],
        weapon_proficiencies=["Greataxe","Maul","Handaxe","Javelin"],
        armor_proficiencies=["Light","Medium"],
        lore="From the wild frontiers, barbarians fight with primal instinct and raw power."
    ),

    "Ranger": CharacterClass(
        name="Ranger", archetype="Martial", emoji="🏹",
        description="Hunter and tracker, deadly with a bow and at home in the wilds.",
        hit_die=10, primary_stat="dexterity", secondary_stat="wisdom",
        base_stats={"strength":12,"dexterity":16,"intelligence":11,"constitution":13,"charisma":10,"wisdom":14},
        base_hp=26, base_mp=10,
        spells=["Hunter's Mark", "Cure Wounds", "Fog Cloud"],
        abilities=["Favored Enemy", "Natural Explorer", "Colossus Slayer", "Multiattack"],
        weapon_proficiencies=["Longbow","Shortbow","Shortsword","Dagger"],
        armor_proficiencies=["Light","Medium"],
        lore="Wardens of the wilderness, rangers hunt monsters that threaten civilization."
    ),

    # ── ARCANE ──────────────────────────────────────────────────────

    "Wizard": CharacterClass(
        name="Wizard", archetype="Arcane", emoji="🧙",
        description="Scholar of arcane magic. Fragile but commands devastating spells.",
        hit_die=6, primary_stat="intelligence", secondary_stat="wisdom",
        base_stats={"strength":8,"dexterity":13,"intelligence":18,"constitution":10,"charisma":11,"wisdom":14},
        base_hp=16, base_mp=40,
        spells=["Fireball","Magic Missile","Lightning Bolt","Arcane Shield","Polymorph","Counterspell","Fly"],
        abilities=["Arcane Recovery", "Spell Mastery", "Ritual Casting"],
        weapon_proficiencies=["Dagger","Staff","Crossbow"],
        armor_proficiencies=[],
        lore="Years of study have given wizards unmatched mastery over the arcane arts."
    ),

    "Sorcerer": CharacterClass(
        name="Sorcerer", archetype="Arcane", emoji="✨",
        description="Born with innate magical power. Raw, instinctive, and unpredictable.",
        hit_die=6, primary_stat="charisma", secondary_stat="constitution",
        base_stats={"strength":9,"dexterity":14,"intelligence":13,"constitution":12,"charisma":18,"wisdom":11},
        base_hp=18, base_mp=35,
        spells=["Chaos Bolt","Burning Hands","Thunderwave","Charm Person","Metamagic Surge"],
        abilities=["Sorcery Points", "Metamagic", "Font of Magic"],
        weapon_proficiencies=["Dagger","Staff","Dart"],
        armor_proficiencies=[],
        lore="Magic flows through a sorcerer's blood, sometimes wild and barely contained."
    ),

    "Warlock": CharacterClass(
        name="Warlock", archetype="Arcane", emoji="👁️",
        description="Pact-bound spellcaster drawing power from an otherworldly patron.",
        hit_die=8, primary_stat="charisma", secondary_stat="constitution",
        base_stats={"strength":10,"dexterity":13,"intelligence":14,"constitution":13,"charisma":17,"wisdom":12},
        base_hp=20, base_mp=20,
        spells=["Eldritch Blast","Hex","Hunger of Hadar","Summon Shadow","Dark One's Blessing"],
        abilities=["Pact Boon", "Eldritch Invocations", "Mystic Arcanum"],
        weapon_proficiencies=["Dagger","Staff","Light Crossbow"],
        armor_proficiencies=["Light"],
        lore="A warlock's power comes at a price — bound to a patron of immense power."
    ),

    "Artificer": CharacterClass(
        name="Artificer", archetype="Arcane", emoji="⚙️",
        description="Magical inventor who infuses items with arcane power.",
        hit_die=8, primary_stat="intelligence", secondary_stat="constitution",
        base_stats={"strength":11,"dexterity":14,"intelligence":17,"constitution":14,"charisma":10,"wisdom":12},
        base_hp=22, base_mp=20,
        spells=["Magic Weapon","Arcane Turret","Thundercannon","Healing Infusion"],
        abilities=["Infuse Item", "Flash of Genius", "Tool Expertise", "Magical Tinkering"],
        weapon_proficiencies=["Crossbow","Handcrossbow","Dagger"],
        armor_proficiencies=["Light","Medium","Shield"],
        lore="Masters of magical invention, artificers see magic as a system to be understood."
    ),

    # ── DIVINE ──────────────────────────────────────────────────────

    "Cleric": CharacterClass(
        name="Cleric", archetype="Divine", emoji="✝️",
        description="Priest of the gods. Healer and divine spellcaster with surprising toughness.",
        hit_die=8, primary_stat="wisdom", secondary_stat="constitution",
        base_stats={"strength":12,"dexterity":10,"intelligence":12,"constitution":14,"charisma":13,"wisdom":17},
        base_hp=24, base_mp=30,
        spells=["Cure Wounds","Healing Word","Sacred Flame","Spiritual Weapon","Turn Undead","Revivify"],
        abilities=["Divine Intervention", "Channel Divinity", "Blessed Strikes"],
        weapon_proficiencies=["Mace","Warhammer","Crossbow"],
        armor_proficiencies=["Light","Medium","Heavy","Shield"],
        lore="Clerics are conduits for divine power, chosen champions of their deities."
    ),

    "Druid": CharacterClass(
        name="Druid", archetype="Divine", emoji="🌿",
        description="Guardian of nature who shapeshifts and wields primal magic.",
        hit_die=8, primary_stat="wisdom", secondary_stat="constitution",
        base_stats={"strength":11,"dexterity":13,"intelligence":13,"constitution":13,"charisma":11,"wisdom":17},
        base_hp=22, base_mp=28,
        spells=["Entangle","Moonbeam","Call Lightning","Wild Shape","Barkskin","Thorn Whip"],
        abilities=["Wild Shape", "Timeless Body", "Beast Spells"],
        weapon_proficiencies=["Club","Quarterstaff","Scimitar","Sickle"],
        armor_proficiencies=["Light","Medium","Shield (non-metal)"],
        lore="Druids draw power from the natural world, shapeshifting into beasts when needed."
    ),

    # ── ROGUISH ─────────────────────────────────────────────────────

    "Rogue": CharacterClass(
        name="Rogue", archetype="Roguish", emoji="🗡️",
        description="Master of stealth and precision. Strikes from the shadows for devastating damage.",
        hit_die=8, primary_stat="dexterity", secondary_stat="intelligence",
        base_stats={"strength":11,"dexterity":18,"intelligence":14,"constitution":12,"charisma":13,"wisdom":12},
        base_hp=20, base_mp=0,
        abilities=["Sneak Attack", "Cunning Action", "Evasion", "Uncanny Dodge", "Assassinate"],
        weapon_proficiencies=["Dagger","Shortsword","Shortbow","Hand Crossbow"],
        armor_proficiencies=["Light"],
        lore="Rogues use wit and agility to outwit opponents, striking where it hurts most."
    ),

    "Bard": CharacterClass(
        name="Bard", archetype="Roguish", emoji="🎵",
        description="Magical performer whose music inspires allies and confounds enemies.",
        hit_die=8, primary_stat="charisma", secondary_stat="dexterity",
        base_stats={"strength":10,"dexterity":15,"intelligence":13,"constitution":12,"charisma":18,"wisdom":12},
        base_hp=20, base_mp=25,
        spells=["Vicious Mockery","Healing Word","Hypnotic Pattern","Bardic Inspiration","Shatter"],
        abilities=["Bardic Inspiration", "Song of Rest", "Countercharm", "Jack of All Trades"],
        weapon_proficiencies=["Dagger","Rapier","Longsword","Hand Crossbow"],
        armor_proficiencies=["Light"],
        lore="Bards weave magic through music, story, and art, inspiring those around them."
    ),

    "Monk": CharacterClass(
        name="Monk", archetype="Roguish", emoji="👊",
        description="Martial artist who channels ki energy for supernatural combat abilities.",
        hit_die=8, primary_stat="dexterity", secondary_stat="wisdom",
        base_stats={"strength":13,"dexterity":17,"intelligence":11,"constitution":13,"charisma":10,"wisdom":15},
        base_hp=22, base_mp=20,
        abilities=["Flurry of Blows", "Patient Defense", "Step of the Wind", "Stunning Strike", "Ki Strike"],
        weapon_proficiencies=["Unarmed","Shortsword","Staff"],
        armor_proficiencies=[],
        lore="Monks harness the power of ki — the life force flowing through all things."
    ),

    "Assassin": CharacterClass(
        name="Assassin", archetype="Roguish", emoji="🩸",
        description="Elite killer trained to eliminate targets before they can react.",
        hit_die=8, primary_stat="dexterity", secondary_stat="intelligence",
        base_stats={"strength":12,"dexterity":18,"intelligence":15,"constitution":12,"charisma":11,"wisdom":13},
        base_hp=18, base_mp=0,
        abilities=["Assassinate", "Infiltration Expertise", "Imposter", "Death Strike", "Poison Use"],
        weapon_proficiencies=["Dagger","Shortbow","Blowgun","Crossbow"],
        armor_proficiencies=["Light"],
        lore="Assassins are trained killers who use disguise and poison to eliminate targets."
    ),

    "Blood Mage": CharacterClass(
        name="Blood Mage", archetype="Arcane", emoji="🩸✨",
        description="Dark spellcaster who sacrifices life force to fuel devastating blood magic.",
        hit_die=6, primary_stat="intelligence", secondary_stat="constitution",
        base_stats={"strength":9,"dexterity":13,"intelligence":17,"constitution":15,"charisma":12,"wisdom":10},
        base_hp=20, base_mp=35,
        spells=["Hemorrhage","Blood Bolt","Sanguine Shield","Exsanguinate","Life Drain","Blood Golem"],
        abilities=["Blood Sacrifice", "Crimson Pact", "Life Tap", "Vital Surge"],
        weapon_proficiencies=["Dagger","Staff"],
        armor_proficiencies=[],
        lore="Blood mages tap into the primal power of life itself, at great personal cost."
    ),

    "Necromancer": CharacterClass(
        name="Necromancer", archetype="Arcane", emoji="💀",
        description="Master of death magic who raises the fallen as undead servants.",
        hit_die=6, primary_stat="intelligence", secondary_stat="wisdom",
        base_stats={"strength":8,"dexterity":12,"intelligence":18,"constitution":11,"charisma":10,"wisdom":15},
        base_hp=16, base_mp=38,
        spells=["Animate Dead","Bone Spear","Death Coil","Undying Servant","Wail of the Banshee","Life Drain"],
        abilities=["Undead Thrall", "Grim Harvest", "Inured to Undeath", "Command Undead"],
        weapon_proficiencies=["Dagger","Staff"],
        armor_proficiencies=[],
        lore="Necromancers study the boundary between life and death, bending it to their will."
    ),
}

RACES = {
    "Human":   {"bonus": {"strength":1,"dexterity":1,"intelligence":1,"constitution":1,"charisma":1,"wisdom":1}, "trait": "Versatile: +1 to all stats", "emoji":"🧑"},
    "Elf":     {"bonus": {"dexterity":2,"intelligence":1,"wisdom":1}, "trait": "Keen Senses: advantage on perception checks", "emoji":"🧝"},
    "Dwarf":   {"bonus": {"constitution":2,"strength":1}, "trait": "Stonecunning: resist poison, +2 CON", "emoji":"🧔"},
    "Halfling":{"bonus": {"dexterity":2,"charisma":1}, "trait": "Lucky: reroll 1s on d20", "emoji":"🧒"},
    "Orc":     {"bonus": {"strength":2,"constitution":2,"intelligence":-1}, "trait": "Relentless: survive to 1 HP once per combat", "emoji":"👹"},
    "Tiefling":{"bonus": {"charisma":2,"intelligence":1}, "trait": "Hellish Resistance: fire damage resistance", "emoji":"😈"},
    "Dragonborn":{"bonus":{"strength":2,"charisma":1}, "trait": "Draconic Ancestry: breath weapon attack", "emoji":"🐉"},
    "Gnome":   {"bonus": {"intelligence":2,"dexterity":1}, "trait": "Gnome Cunning: advantage on INT/WIS/CHA saves", "emoji":"🧙‍♂️"},
    "Dark Elf":{"bonus": {"dexterity":2,"charisma":1,"strength":-1}, "trait": "Superior Darkvision: see in magical darkness", "emoji":"🌑"},
    "Half-Giant":{"bonus":{"strength":3,"constitution":2,"dexterity":-2,"intelligence":-1}, "trait": "Giant Strength: advantage on STR checks", "emoji":"🦣"},
}

def get_class_names() -> list[str]:
    return sorted(CLASSES.keys())

def get_race_names() -> list[str]:
    return sorted(RACES.keys())

def build_character(name: str, class_name: str, race_name: str) -> dict:
    """Build a full character dict from class + race selections."""
    cls = CLASSES[class_name]
    race = RACES[race_name]
    stats = dict(cls.base_stats)

    # Apply racial bonuses
    for stat, bonus in race["bonus"].items():
        stats[stat] = max(1, stats[stat] + bonus)

    return {
        "name": name,
        "class_name": class_name,
        "race": race_name,
        "emoji": cls.emoji,
        "hp": cls.base_hp,
        "max_hp": cls.base_hp,
        "mp": cls.base_mp,
        "max_mp": cls.base_mp,
        "strength": stats["strength"],
        "dexterity": stats["dexterity"],
        "intelligence": stats["intelligence"],
        "constitution": stats["constitution"],
        "charisma": stats["charisma"],
        "wisdom": stats["wisdom"],
        "xp": 0,
        "level": 1,
        "gold": 10,
        "inventory": [],
        "abilities": cls.abilities,
        "spells": cls.spells,
        "is_alive": True,
        "racial_trait": race["trait"],
    }

def xp_to_next_level(level: int) -> int:
    thresholds = [0, 300, 900, 2700, 6500, 14000, 23000, 34000, 48000, 64000]
    if level < len(thresholds):
        return thresholds[level]
    return 999999

def apply_level_up(character: dict) -> dict:
    """Level up a character, increasing stats and HP/MP."""
    character["level"] += 1
    lvl = character["level"]
    cls = CLASSES.get(character["class_name"])
    if cls:
        hp_gain = max(1, cls.hit_die // 2 + 1)
        character["max_hp"] += hp_gain
        character["hp"] = min(character["hp"] + hp_gain, character["max_hp"])
        if cls.base_mp > 0:
            character["max_mp"] += 5
    # Every 2 levels, +1 to primary stat
    if lvl % 2 == 0 and cls:
        primary = cls.primary_stat
        character[primary] = min(20, character[primary] + 1)
    return character
