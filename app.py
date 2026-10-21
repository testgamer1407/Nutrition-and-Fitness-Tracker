import random
import streamlit as st

# Emberfall: a small, interactive, turn-based RPG built with Streamlit.
st.set_page_config(page_title="Emberfall RPG", page_icon="⚔️", layout="wide")

st.markdown("""
<style>
.stApp { background: radial-gradient(circle at 20% 0%, #25354b 0, #101722 42%, #0b1018 100%); color: #eef3f8; }
.block-container { max-width: 1180px; padding-top: 1.4rem; }
.hero { padding: 1.4rem 1.6rem; border: 1px solid #46566b; border-radius: 18px;
        background: linear-gradient(120deg, rgba(40,62,84,.95), rgba(22,31,45,.92)); margin-bottom: 1rem; }
.hero h1 { margin: 0; letter-spacing: .04em; }
.muted { color: #aab8c8; }
.panel { background: rgba(21,30,43,.88); border: 1px solid #354458; border-radius: 14px; padding: 1rem; }
.log { background: #0d141e; border-left: 3px solid #d6a85c; padding: .65rem .85rem; border-radius: 6px; margin: .35rem 0; }
.bigstat { font-size: 1.45rem; font-weight: 700; }
div.stButton > button { border-radius: 10px; border: 1px solid #52677e; min-height: 2.8rem; }
</style>
""", unsafe_allow_html=True)

AREAS = {
    "Whispering Woods": {
        "emoji": "🌲", "danger": 1, "description": "Old trees murmur secrets. Something watches between the trunks.",
        "enemies": [("Mossfang Wolf", 24, 6, 8, 12), ("Thorn Sprite", 18, 5, 7, 10), ("Lost Bandit", 28, 7, 10, 14)]
    },
    "Sunken Ruins": {
        "emoji": "🏛️", "danger": 2, "description": "Broken pillars rise from black water, guarding a forgotten treasury.",
        "enemies": [("Crypt Sentinel", 38, 8, 13, 20), ("Drowned Acolyte", 31, 9, 12, 18), ("Ruin Stalker", 34, 7, 15, 19)]
    },
    "Ashen Keep": {
        "emoji": "🏰", "danger": 3, "description": "A fortress of cinders. The air itself tastes of old magic.",
        "enemies": [("Ash Knight", 48, 11, 17, 28), ("Cinder Witch", 39, 13, 18, 30)]
    }
}
BOSS = ("The Hollow King", 100, 13, 38, 100)

def new_game(name, role, difficulty):
    bases = {
        "Vanguard": {"hp": 112, "attack": 13, "defense": 5, "gold": 18},
        "Ranger": {"hp": 92, "attack": 16, "defense": 3, "gold": 24},
        "Arcanist": {"hp": 82, "attack": 20, "defense": 2, "gold": 30},
    }
    p = bases[role].copy()
    scale = {"Story": .8, "Adventurer": 1.0, "Nightmare": 1.25}[difficulty]
    st.session_state.hero = {
        "name": name.strip() or "Wayfarer", "role": role, "max_hp": p["hp"], "hp": p["hp"],
        "attack": p["attack"], "defense": p["defense"], "gold": p["gold"], "potions": 3,
        "xp": 0, "level": 1, "xp_next": 40, "kills": 0, "relics": 0, "scale": scale,
        "difficulty": difficulty, "weapon_bonus": 0, "armor_bonus": 0, "special_ready": True,
    }
    st.session_state.area = "Whispering Woods"
    st.session_state.enemy = None
    st.session_state.log = ["Your journey begins at the edge of Emberfall. The old road leads into danger."]
    st.session_state.visited = set()
    st.session_state.boss_defeated = False
    st.session_state.game_over = False
    st.session_state.victory = False

def say(message):
    st.session_state.log.insert(0, message)
    st.session_state.log = st.session_state.log[:12]

def spawn_enemy(boss=False):
    if boss:
        template = BOSS
    else:
        pool = AREAS[st.session_state.area]["enemies"]
        template = random.choice(pool)
    name, hp, atk, xp, gold = template
    scale = st.session_state.hero["scale"] * (1 + (st.session_state.hero["level"] - 1) * .12)
    st.session_state.enemy = {
        "name": name, "max_hp": int(hp * scale), "hp": int(hp * scale),
        "attack": max(1, int(atk * scale)), "xp": int(xp * scale), "gold": int(gold * scale),
        "boss": boss, "guard": False
    }
    say(f"⚠️ {name} emerges from the gloom!")

def player_damage(multiplier=1.0):
    h = st.session_state.hero
    return max(1, int((h["attack"] + h["weapon_bonus"] + random.randint(-3, 4)) * multiplier))

def enemy_turn():
    h, e = st.session_state.hero, st.session_state.enemy
    if not e or e["hp"] <= 0 or st.session_state.game_over:
        return
    raw = e["attack"] + random.randint(-2, 3)
    damage = max(1, raw - h["defense"] - h["armor_bonus"])
    if e.get("guard"):
        damage = max(1, damage // 2)
        e["guard"] = False
    h["hp"] = max(0, h["hp"] - damage)
    say(f"💥 {e['name']} hits you for {damage} damage.")
    if h["hp"] <= 0:
        st.session_state.game_over = True
        say("☠️ You fall beneath Emberfall's shadow. Begin a new run to rise again.")

def win_battle():
    h, e = st.session_state.hero, st.session_state.enemy
    if not e or e["hp"] > 0:
        return
    h["xp"] += e["xp"]
    h["gold"] += e["gold"]
    h["kills"] += 1
    say(f"🏆 Victory! +{e['xp']} XP · +{e['gold']} gold.")
    if e["boss"]:
        st.session_state.boss_defeated = True
        st.session_state.victory = True
        say("👑 The Hollow King is defeated. Emberfall sees its first dawn in a century.")
    while h["xp"] >= h["xp_next"]:
        h["xp"] -= h["xp_next"]
        h["level"] += 1
        h["xp_next"] = int(h["xp_next"] * 1.45)
        h["max_hp"] += 12
        h["hp"] = h["max_hp"]
        h["attack"] += 2
        say(f"✨ LEVEL UP! You are now level {h['level']}. Your strength and vitality grow.")
    st.session_state.enemy = None

def action_attack():
    if st.session_state.enemy is None or st.session_state.game_over: return
    e = st.session_state.enemy
    dmg = player_damage()
    if random.random() < .12:
        dmg = int(dmg * 1.8)
        say("🎯 Critical strike!")
    e["hp"] = max(0, e["hp"] - dmg)
    say(f"⚔️ You strike {e['name']} for {dmg} damage.")
    if e["hp"] <= 0:
        win_battle()
    else:
        enemy_turn()

def action_special():
    if st.session_state.enemy is None or st.session_state.game_over: return
    h, e = st.session_state.hero, st.session_state.enemy
    if not h["special_ready"]: return
    multiplier = {"Vanguard": 1.8, "Ranger": 1.6, "Arcanist": 2.2}[h["role"]]
    dmg = player_damage(multiplier)
    e["hp"] = max(0, e["hp"] - dmg)
    h["special_ready"] = False
    say(f"🌟 {h['role']} skill deals {dmg} damage!")
    if e["hp"] <= 0: win_battle()
    else: enemy_turn()

def action_heal():
    h = st.session_state.hero
    if h["potions"] <= 0 or h["hp"] >= h["max_hp"] or st.session_state.game_over: return
    heal = min(35, h["max_hp"] - h["hp"])
    h["hp"] += heal
    h["potions"] -= 1
    say(f"🧪 You recover {heal} HP.")
    if st.session_state.enemy: enemy_turn()

def action_guard():
    if st.session_state.enemy is None or st.session_state.game_over: return
    st.session_state.enemy["guard"] = True
    say("🛡️ You brace for impact. The next enemy strike is weakened.")
    enemy_turn()

if "hero" not in st.session_state:
    st.session_state.started = False
    st.session_state.log = []

st.markdown('<div class="hero"><h1>⚔️ EMBERFALL</h1><p class="muted">A dark-fantasy, turn-based RPG · Explore. Grow stronger. End the curse.</p></div>', unsafe_allow_html=True)

if not st.session_state.get("started", False):
    st.markdown("### Your legend starts here")
    st.write("The Hollow King has returned, and the kingdoms are fading into ash. Choose your path.")
    with st.form("start_game"):
        name = st.text_input("Hero name", value="Wayfarer", max_chars=24)
        role = st.selectbox("Class", ["Vanguard", "Ranger", "Arcanist"])
        difficulty = st.select_slider("Difficulty", options=["Story", "Adventurer", "Nightmare"], value="Adventurer")
        submitted = st.form_submit_button("Begin Adventure", type="primary", use_container_width=True)
    st.markdown("""
    <div class="panel">
    <b>Vanguard</b> — durable frontline fighter · <b>Ranger</b> — balanced precision ·
    <b>Arcanist</b> — fragile, devastating magic.<br><br>
    <span class="muted">How to play: explore areas to trigger encounters, use tactical combat actions, earn XP and gold, and upgrade gear before challenging the final boss.</span>
    </div>""", unsafe_allow_html=True)
    if submitted:
        new_game(name, role, difficulty)
        st.session_state.started = True
        st.rerun()
    st.stop()

h = st.session_state.hero
e = st.session_state.enemy

with st.sidebar:
    st.markdown(f"## 🧙 {h['name']}")
    st.caption(f"{h['role']} · Level {h['level']} · {h['difficulty']}")
    st.progress(h["hp"] / h["max_hp"], text=f"HP {h['hp']} / {h['max_hp']}")
    st.progress(min(1.0, h["xp"] / h["xp_next"]), text=f"XP {h['xp']} / {h['xp_next']}")
    st.markdown("---")
    st.metric("⚔️ Attack", h["attack"] + h["weapon_bonus"])
    st.metric("🛡️ Defense", h["defense"] + h["armor_bonus"])
    st.metric("🪙 Gold", h["gold"])
    st.metric("🧪 Potions", h["potions"])
    st.markdown("---")
    if st.button("Restart run", use_container_width=True):
        st.session_state.started = False
        st.session_state.pop("hero", None)
        st.rerun()

if st.session_state.victory:
    st.success("🏆 THE CURSE IS BROKEN — YOU SAVED EMBERFALL!")
    st.balloons()
    st.write(f"{h['name']} reached level {h['level']}, defeated {h['kills']} enemies, and collected {h['gold']} gold.")
    st.markdown("### The kingdoms remember your name.")
    st.stop()
if st.session_state.game_over:
    st.error("Your adventure has ended.")
    if st.button("Start a new adventure"):
        st.session_state.started = False
        st.session_state.pop("hero", None)
        st.rerun()
    st.stop()

left, right = st.columns([1.25, 1], gap="large")
with left:
    area = AREAS[st.session_state.area]
    st.markdown(f"### {area['emoji']} {st.session_state.area}")
    st.write(area["description"])
    st.caption("Choose a location to travel. More dangerous regions reward more XP and gold.")
    area_names = list(AREAS.keys())
    cols = st.columns(len(area_names))
    for i, area_name in enumerate(area_names):
        with cols[i]:
            if st.button(area_name, disabled=(e is not None), use_container_width=True):
                st.session_state.area = area_name
                st.session_state.visited.add(area_name)
                say(f"You travel to {area_name}.")
                st.rerun()

    st.markdown("### 🌍 Adventure")
    if e is None:
        if st.button("🔎 Explore this area", type="primary", use_container_width=True):
            spawn_enemy()
            st.rerun()
        if st.session_state.area == "Ashen Keep" and h["level"] >= 3 and h["kills"] >= 4:
            if st.button("👑 Enter the throne room", use_container_width=True):
                spawn_enemy(boss=True)
                st.rerun()
        elif st.session_state.area == "Ashen Keep":
            st.info("The throne room seals itself. Reach level 3 and defeat 4 enemies to challenge the Hollow King.")
    else:
        st.markdown(f"#### ⚔️ Battle: {e['name']}")
        st.progress(e["hp"] / e["max_hp"], text=f"Enemy HP {e['hp']} / {e['max_hp']}")
        if e["boss"]:
            st.warning("BOSS ENCOUNTER — the fate of Emberfall hangs in the balance.")
        c1, c2 = st.columns(2)
        with c1:
            st.button("⚔️ Attack", on_click=action_attack, use_container_width=True)
            st.button("🌟 Class skill", on_click=action_special, disabled=not h["special_ready"], use_container_width=True)
        with c2:
            st.button("🧪 Use potion", on_click=action_heal, disabled=(h["potions"] <= 0 or h["hp"] == h["max_hp"]), use_container_width=True)
            st.button("🛡️ Guard", on_click=action_guard, use_container_width=True)
        if not h["special_ready"]:
            if st.button("Recharge class skill (cost: 1 turn)", use_container_width=True):
                h["special_ready"] = True
                say("✨ Your class skill is ready again.")
                enemy_turn()
                st.rerun()
        st.caption("Combat is turn-based. Every action except a finishing blow gives the enemy a chance to strike.")

with right:
    st.markdown("### 🎒 The Wayfarer's Market")
    st.write("Spend gold between battles to prepare for the road.")
    if e is not None:
        st.info("The merchant only trades when the area is safe.")
    shop_items = [
        ("Sharpen weapon", "Permanent +3 attack", 35, "weapon"),
        ("Reinforce armor", "Permanent +2 defense", 35, "armor"),
        ("Buy potion", "Restore up to 35 HP in battle", 15, "potion"),
        ("Rest at inn", "Restore all HP", 20, "rest"),
    ]
    for title, desc, cost, kind in shop_items:
        row = st.columns([2.2, 1, 1])
        with row[0]:
            st.markdown(f"**{title}**")
            st.caption(desc)
        with row[1]:
            st.write(f"🪙 {cost}")
        with row[2]:
            disabled = e is not None or h["gold"] < cost or (kind == "rest" and h["hp"] == h["max_hp"])
            if st.button("Buy", key=f"buy_{kind}", disabled=disabled, use_container_width=True):
                h["gold"] -= cost
                if kind == "weapon":
                    h["weapon_bonus"] += 3
                    say("⚒️ Your weapon has been sharpened. Attack increased by 3.")
                elif kind == "armor":
                    h["armor_bonus"] += 2
                    say("🛡️ Your armor has been reinforced. Defense increased by 2.")
                elif kind == "potion":
                    h["potions"] += 1
                    say("🧪 Potion added to your pack.")
                elif kind == "rest":
                    restored = h["max_hp"] - h["hp"]
                    h["hp"] = h["max_hp"]
                    say(f"🛏️ You rest at the inn and recover {restored} HP.")
                st.rerun()
    st.markdown("---")
    st.markdown("### 📜 Chronicle")
    if not st.session_state.log:
        st.caption("Your story will be written here.")
    for item in st.session_state.log[:8]:
        st.markdown(f'<div class="log">{item}</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 🏅 Run record")
    m1, m2 = st.columns(2)
    m1.metric("Enemies defeated", h["kills"])
    m2.metric("Areas visited", len(st.session_state.visited))
    st.caption("Tip: upgrade before entering the Ashen Keep. Level 3 and four victories unlock the throne room.")
