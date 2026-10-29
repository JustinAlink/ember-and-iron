#!/usr/bin/env python3
"""Builds the FTB Quests book in config/ftbquests/quests from the chapter definitions below.

Edit the quests here, not in-game: the files this writes are overwritten on every run, and the
server re-syncs them from the repo on every start. Object IDs are derived from the chapter and
quest keys, so renaming a key resets that quest's progress, while editing text or rewards does not.

    python3 scripts/quests.py                  # regenerate
    python3 scripts/quests.py --check ids.json # also fail on unknown item or entity ids
"""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "config" / "ftbquests" / "quests"


# ---------- quest building blocks ----------

def item(id, count=1):
    return {"type": "item", "item": id, "count": count}

def kill(entity, count=1):
    return {"type": "kill", "entity": entity, "value": count}

def dim(dimension):
    return {"type": "dimension", "dimension": dimension}

def check():
    return {"type": "checkmark"}

def xp(amount):
    return {"type": "xp", "xp": amount}

def give(id, count=1):
    return {"type": "item", "item": id, "count": count}

def Q(key, title, tasks, deps=(), rewards=(), sub=None, desc=(), icon=None, shape=None, size=None, optional=False):
    return {"key": key, "title": title, "tasks": tasks if isinstance(tasks, list) else [tasks],
            "deps": list(deps), "rewards": list(rewards), "sub": sub, "desc": list(desc),
            "icon": icon, "shape": shape, "size": size, "optional": optional}


# ---------- the book ----------

CHAPTERS = [
    {"key": "welcome", "title": "&6Welcome to Ember & Iron", "icon": "minecraft:campfire",
     "sub": "Start here: the basics of this world", "quests": [
        Q("welcome", "Welcome, traveller", check(), shape="gear", size=1.5, icon="minecraft:campfire",
          sub="Click the checkmark to begin",
          desc=["Ember & Iron is a big world: machines, magic, new dimensions and a lot of monsters that get &cstronger the further you go&r.",
                "",
                "This book is a loose guide, not a cage. Every chapter on the left is a path you can follow in any order.",
                "",
                "Tip: hover an item and press &eR&r for recipes or &eU&r for uses (JEI)."],
          rewards=[give("minecraft:bread", 8), give("minecraft:torch", 16)]),
        Q("levels", "Every monster has a level", check(), deps=["welcome"], icon="minecraft:zombie_head",
          sub="Remnants: RPG Mobs",
          desc=["The number above a monster is its &clevel&r. Levels rise with distance from spawn, with depth, with the number of days the world has lived and with how strong your gear is.",
                "",
                "Some monsters spawn ranked: &aVeteran&r, &9Elite&r, &5Champion&r. Very rarely a named &6Remnant&r walks out of the dark with a boss bar.",
                "",
                "Higher levels hit harder and drop more. Start close to spawn and push outward as your gear improves."],
          rewards=[xp(50)]),
        Q("table", "Getting started", item("minecraft:crafting_table"), deps=["welcome"],
          rewards=[xp(25)]),
        Q("bed", "A place to rest", item("comforts:sleeping_bag_white"), deps=["table"],
          sub="Sleeping bags skip the night without moving your spawn point",
          rewards=[xp(25)]),
        Q("backpack", "Pack your bags", item("sophisticatedbackpacks:backpack"), deps=["table"],
          desc=["A backpack you can upgrade later: more slots, auto-pickup, magnets, even a crafting grid."],
          rewards=[give("minecraft:iron_ingot", 8)]),
        Q("ultimine", "Mine smarter", check(), deps=["table"], icon="minecraft:iron_pickaxe",
          sub="FTB Ultimine",
          desc=["Hold &e`&r (the key left of 1) while breaking a block to mine the whole vein or tree at once. It costs hunger, so bring food."],
          rewards=[xp(25)]),
        Q("waystone", "Never lose your way", item("waystones:waystone"), deps=["backpack"],
          desc=["Waystones link up into a teleport network. Villages often have one already; walk up and activate it.",
                "",
                "Your map (&eM&r) shows waypoints and lets you claim land, see the next quests."],
          rewards=[give("waystones:return_scroll", 2)]),
        Q("claim", "Claim your home", check(), deps=["waystone"], icon="minecraft:oak_door",
          sub="Open Parties and Claims",
          desc=["Protect your base from griefing and explosions: open the world map (&eM&r), right-click the chunks you want and choose Claim.",
                "",
                "Or stand in a chunk and run &e/openpac-claims claim&r. Make a party with &e/openpac-parties create&r to share claims with friends."],
          rewards=[xp(50)]),
        Q("voice", "Say hello", check(), deps=["welcome"], icon="minecraft:note_block",
          sub="Simple Voice Chat",
          desc=["Proximity voice chat is built in. Press &eV&r to set up your microphone. Players near you hear you; walls and distance fade you out."],
          rewards=[xp(25)]),
        Q("megatorch", "Keep the dark at bay", item("torchmaster:megatorch"), deps=["levels"],
          desc=["Leveled monsters spawning inside your base get old fast. A Megatorch stops hostile spawns in a large radius around it."],
          rewards=[xp(100)]),
        Q("death", "If you fall", check(), deps=["levels"], icon="minecraft:skeleton_skull",
          desc=["When you die, a &ecorpse&r stays behind holding all your items. Go back and open it to collect them. It will not despawn."],
          rewards=[xp(25)]),
    ]},

    {"key": "adventure", "title": "&cThe Adventurer's Path", "icon": "minecraft:iron_sword",
     "sub": "Skills, loot and combat", "quests": [
        Q("first_blood", "First blood", kill("minecraft:zombie", 5), deps=["welcome/levels"],
          rewards=[xp(50)]),
        Q("skills", "Skill trees", check(), deps=["first_blood"], icon="minecraft:experience_bottle",
          sub="Pufferfish's Skills",
          desc=["Fighting and mining earn skill points. Press &eK&r to open your skill trees and spend them on permanent bonuses."],
          rewards=[xp(100)]),
        Q("combat", "Fight with style", item("simplyswords:iron_longsword"), deps=["first_blood"],
          sub="Better Combat",
          desc=["Weapons swing in combos and their reach and arcs differ: longswords sweep, spears thrust, greataxes cleave. Try a few.",
                "",
                "There is also a dodge roll; find its key under Controls."],
          rewards=[xp(75)]),
        Q("hunter", "Monster hunter", [kill("minecraft:skeleton", 10), kill("minecraft:creeper", 5), kill("minecraft:spider", 10)],
          deps=["first_blood"], rewards=[give("minecraft:golden_apple", 2), xp(100)]),
        Q("armor", "Suit up", item("magistuarmory:norman_helmet"), deps=["combat"],
          sub="Epic Knights",
          desc=["Medieval armour sets with real stats. Knights, crusaders, samurai and more."],
          rewards=[xp(75)]),
        Q("affix", "Loot with a story", item("apotheosis:salvaging_table"), deps=["hunter"],
          sub="Apotheosis",
          desc=["Gear can now drop with a rarity and random &daffixes&r. Monsters with higher levels drop better loot.",
                "",
                "Break gear you do not want at the Salvaging Table for materials."],
          rewards=[xp(150)]),
        Q("reforge", "Reforge", item("apotheosis:reforging_table"), deps=["affix"],
          desc=["Reroll an item's affixes with materials and gem dust."],
          rewards=[xp(150)]),
        Q("gems", "Gemcutter", item("apotheosis:gem_cutting_table"), deps=["affix"],
          desc=["Gems socket into gear for extra stats. Cut duplicates together to raise their tier."],
          rewards=[xp(150)]),
        Q("enchant", "A deeper library", item("apothic_enchanting:hellshelf"), deps=["affix"],
          desc=["Enchanting is overhauled: shelves change Eterna, Quanta and Arcana, which decide how strong and how wild your enchantments get. Look at a shelf for its stats."],
          rewards=[xp(150)]),
        Q("artifact", "Curios", item("artifacts:flame_pendant"), deps=["hunter"], optional=True,
          sub="Artifacts and Relics",
          desc=["Artifacts hide in dungeon chests and inside mimics. Relics level up as you use them. Both go into the curio slots of your inventory.",
                "",
                "Any artifact counts as progress; this one is just a goal."],
          rewards=[xp(150)]),
        Q("spells", "Spellsword", item("irons_spellbooks:inscription_table"), deps=["skills"],
          sub="Iron's Spells 'n Spellbooks",
          desc=["Ink scrolls into a spell book at the Inscription Table, then cast with the spell wheel. See the Arcane chapter for more."],
          rewards=[xp(100)]),
    ]},

    {"key": "horizons", "title": "&bBeyond the Horizon", "icon": "minecraft:ender_eye",
     "sub": "Other dimensions worth the trip", "quests": [
        Q("nether", "The Nether", dim("minecraft:the_nether"), deps=["welcome/waystone"],
          desc=["The Nether is rebuilt with new biomes and much bigger fortresses. Monsters here start at a higher level."],
          rewards=[xp(100)]),
        Q("twilight", "The Twilight Forest", dim("twilightforest:twilight_forest"), deps=["welcome/waystone"],
          desc=["Dig a 2x2 pool of water, ring it with flowers or grass, and throw a &bdiamond&r into it.",
                "",
                "A world of eternal dusk with a chain of bosses. Some areas stay locked until you beat the one before."],
          rewards=[xp(150)]),
        Q("aether", "The Aether", dim("aether:the_aether"), deps=["welcome/waystone"],
          desc=["Build a portal frame out of &eglowstone&r and pour a water bucket into it.",
                "",
                "Floating islands, three dungeons and a long way down. Bring a parachute."],
          rewards=[xp(150)]),
        Q("undergarden", "The Undergarden", dim("undergarden:undergarden"), deps=["welcome/waystone"],
          icon="undergarden:catalyst",
          desc=["Build a frame of &estone bricks&r and use a &eCatalyst&r on it. Dark, dangerous and full of strange ores."],
          rewards=[xp(150)]),
        Q("bumblezone", "The Bumblezone", dim("the_bumblezone:the_bumblezone"), deps=["welcome/waystone"],
          desc=["Throw an &eender pearl&r at a bee nest or beehive. A dimension made of honeycomb. Do not anger the bees."],
          rewards=[xp(150)]),
        Q("end", "The End", dim("minecraft:the_end"), deps=["nether"],
          rewards=[xp(250)]),
        Q("otherside", "The Otherside", dim("deeperdarker:otherside"), deps=["end"],
          desc=["Deep in an ancient city stands a portal. It only opens with the &3Heart of the Deep&r, which the Warden drops.",
                "",
                "The most dangerous place in this pack."],
          rewards=[xp(400)]),
        Q("compass", "Find anything", [item("naturescompass:naturescompass"), item("explorerscompass:explorerscompass")],
          deps=["welcome/waystone"], desc=["One compass points to any biome, the other to any structure."],
          rewards=[xp(75)]),
        Q("glider", "Ride the wind", item("hangglider:hang_glider"), deps=["compass"], optional=True,
          desc=["Jump off something high and glide. Cheaper than an elytra and good enough for a long time."],
          rewards=[xp(50)]),
    ]},

    {"key": "bosses", "title": "&4Bosses & Legends", "icon": "minecraft:wither_skeleton_skull",
     "sub": "The big fights, roughly in order", "quests": [
        Q("wroughtnaut", "Ferrous Wroughtnaut", kill("mowziesmobs:ferrous_wroughtnaut"), deps=["adventure/hunter"],
          desc=["Sleeps in a cave in the overworld. Hit it in the back when it gets stuck after a swing."],
          rewards=[xp(300), give("minecraft:diamond", 3)]),
        Q("naga", "The Naga", kill("twilightforest:naga"), deps=["horizons/twilight"],
          rewards=[xp(300)]),
        Q("lich", "The Twilight Lich", kill("twilightforest:lich"), deps=["naga"],
          rewards=[xp(400)]),
        Q("minoshroom", "The Minoshroom", kill("twilightforest:minoshroom"), deps=["lich"],
          rewards=[xp(400)]),
        Q("hydra", "The Hydra", kill("twilightforest:hydra"), deps=["minoshroom"],
          rewards=[xp(600)]),
        Q("slider", "The Slider", kill("aether:slider"), deps=["horizons/aether"],
          rewards=[xp(300)]),
        Q("valkyrie", "The Valkyrie Queen", kill("aether:valkyrie_queen"), deps=["slider"],
          rewards=[xp(400)]),
        Q("sun_spirit", "The Sun Spirit", kill("aether:sun_spirit"), deps=["valkyrie"],
          rewards=[xp(600)]),
        Q("frostmaw", "Frostmaw", kill("mowziesmobs:frostmaw"), deps=["wroughtnaut"],
          rewards=[xp(400)]),
        Q("umvuthi", "Umvuthi", kill("mowziesmobs:umvuthi"), deps=["wroughtnaut"],
          rewards=[xp(400)]),
        Q("dead_king", "The Dead King", kill("irons_spellbooks:dead_king"), deps=["wroughtnaut"],
          desc=["Waits in a catacomb. Drops a spellbook worth the trouble."],
          rewards=[xp(500)]),
        Q("cornelia", "Captain Cornelia", kill("aquamirae:captain_cornelia"), deps=["wroughtnaut"],
          desc=["Haunts the frozen seas on a ghost ship."],
          rewards=[xp(500)]),
        Q("monstrosity", "Netherite Monstrosity", kill("cataclysm:netherite_monstrosity"), deps=["horizons/nether"],
          rewards=[xp(600)]),
        Q("ignis", "Ignis", kill("cataclysm:ignis"), deps=["monstrosity"],
          rewards=[xp(800)]),
        Q("obsidilith", "The Obsidilith", kill("bosses_of_mass_destruction:obsidilith"), deps=["horizons/end"],
          rewards=[xp(600)]),
        Q("dragon", "The Ender Dragon", kill("minecraft:ender_dragon"), deps=["horizons/end"],
          rewards=[xp(1000)]),
        Q("ender_guardian", "The Ender Guardian", kill("cataclysm:ender_guardian"), deps=["dragon"],
          rewards=[xp(800)]),
        Q("wither", "The Wither", kill("minecraft:wither"), deps=["monstrosity"],
          rewards=[xp(1000)]),
        Q("harbinger", "The Harbinger", kill("cataclysm:the_harbinger"), deps=["wither"],
          rewards=[xp(1000)]),
        Q("leviathan", "The Leviathan", kill("cataclysm:the_leviathan"), deps=["ignis"],
          rewards=[xp(1200)]),
        Q("warden", "The Warden", kill("minecraft:warden"), deps=["dragon"], optional=True,
          desc=["Not required for anything except the Otherside's key. Bring a plan and an exit."],
          rewards=[xp(800)]),
    ]},

    {"key": "create", "title": "&eCreate: Gears & Grit", "icon": "create:cogwheel",
     "sub": "Rotation, contraptions and trains", "quests": [
        Q("alloy", "Andesite alloy", item("create:andesite_alloy", 16), deps=["welcome/table"],
          desc=["Everything in Create starts here: iron nuggets or zinc plus andesite.",
                "",
                "Press &eW&r while hovering any Create item to Ponder it: an animated tutorial in-game."],
          rewards=[xp(50)]),
        Q("power", "Turn the wheel", item("create:water_wheel"), deps=["alloy"],
          rewards=[xp(50)]),
        Q("shafts", "Shafts and cogs", [item("create:shaft", 8), item("create:cogwheel", 8)], deps=["alloy"],
          rewards=[xp(50)]),
        Q("millstone", "Grind it down", item("create:millstone"), deps=["power", "shafts"],
          rewards=[xp(75)]),
        Q("press", "Mechanical press", item("create:mechanical_press"), deps=["power", "shafts"],
          rewards=[xp(75)]),
        Q("fan", "Bulk processing", item("create:encased_fan"), deps=["press"],
          desc=["A fan blowing through lava smelts, through fire smokes, through water washes. Items on a belt in front of it are processed in bulk."],
          rewards=[xp(75)]),
        Q("mixer", "Mechanical mixer", item("create:mechanical_mixer"), deps=["press"],
          rewards=[xp(75)]),
        Q("brass", "Brass", item("create:brass_ingot", 8), deps=["mixer"],
          rewards=[xp(100)]),
        Q("blaze", "Heat it up", item("create:blaze_burner"), deps=["mixer"],
          rewards=[xp(100)]),
        Q("precision", "Precision mechanism", item("create:precision_mechanism"), deps=["brass"],
          rewards=[xp(150)]),
        Q("deployer", "Deployer", item("create:deployer"), deps=["brass"],
          rewards=[xp(100)]),
        Q("arm", "Mechanical arm", item("create:mechanical_arm"), deps=["precision"],
          rewards=[xp(150)]),
        Q("trains", "All aboard", [item("create:track", 32), item("create:controls")], deps=["precision"],
          desc=["Trains carry you and your cargo across the world. Steam 'n' Rails adds more track styles and couplers."],
          rewards=[xp(250)]),
        Q("electric", "Rotation to power", [item("createaddition:electric_motor"), item("createaddition:alternator")],
          deps=["precision"], desc=["Crafts & Additions bridges Create's rotation with Forge Energy used by every other tech mod."],
          rewards=[xp(200)]),
        Q("enchanter", "Automated enchanting", item("create_enchantment_industry:blaze_enchanter"), deps=["blaze", "precision"],
          rewards=[xp(200)]),
        Q("jetpack", "Fly on brass", item("create_sa:brass_jetpack_chestplate"), deps=["arm"], optional=True,
          sub="Create Stuff & Additions", rewards=[xp(200)]),
    ]},

    {"key": "industry", "title": "&7The Industrial Age", "icon": "mekanism:steel_casing",
     "sub": "Mekanism, Immersive Engineering, Powah", "quests": [
        Q("osmium", "Osmium", item("mekanism:ingot_osmium", 8), deps=["welcome/table"],
          rewards=[xp(50)]),
        Q("infuser", "Metallurgic infuser", item("mekanism:metallurgic_infuser"), deps=["osmium"],
          rewards=[xp(100)]),
        Q("steel", "Steel", item("mekanism:ingot_steel", 8), deps=["infuser"],
          rewards=[xp(100)]),
        Q("circuit", "Basic control circuit", item("mekanism:basic_control_circuit", 4), deps=["infuser"],
          rewards=[xp(100)]),
        Q("enrich", "Ore doubling", item("mekanism:enrichment_chamber"), deps=["circuit", "steel"],
          desc=["The first step of Mekanism's ore processing chain: two ingots per ore, later up to five."],
          rewards=[xp(150)]),
        Q("generators", "Power", [item("mekanismgenerators:heat_generator"), item("mekanismgenerators:wind_generator")],
          deps=["steel"], rewards=[xp(150)]),
        Q("digital_miner", "Digital miner", item("mekanism:digital_miner"), deps=["enrich"],
          rewards=[xp(400)]),
        Q("ie_hammer", "Engineer's hammer", item("immersiveengineering:hammer"), deps=["welcome/table"],
          desc=["Immersive Engineering builds machines as multiblocks in the world. Use the hammer on a finished structure to form it. The Engineer's Manual shows every layout."],
          rewards=[xp(50)]),
        Q("coke", "Coke oven", item("immersiveengineering:cokebrick", 27), deps=["ie_hammer"],
          rewards=[xp(100)]),
        Q("ie_steel", "Steel the old way", item("immersiveengineering:ingot_steel", 8), deps=["coke"],
          rewards=[xp(150)]),
        Q("revolver", "Revolver", item("immersiveengineering:revolver"), deps=["ie_steel"], optional=True,
          rewards=[xp(200)]),
        Q("orb", "Energizing orb", item("powah:energizing_orb"), deps=["welcome/table"],
          sub="Powah", desc=["Powah turns energy into upgraded crystals and much bigger generators."],
          rewards=[xp(100)]),
        Q("reactor", "Reactor", item("powah:reactor_basic", 36), deps=["orb"],
          rewards=[xp(300)]),
        Q("pipes", "Move it", item("pipez:item_pipe", 16), deps=["welcome/table"],
          desc=["Simple, cheap pipes for items, fluids and energy."],
          rewards=[xp(50)]),
        Q("frame", "Industrial Foregoing", item("industrialforegoing:machine_frame_pity"), deps=["circuit"],
          desc=["Mob farms, tree farms, ore laser drills. Automation for when you are tired of doing it by hand."],
          rewards=[xp(150)]),
        Q("inferium", "Grow your resources", item("mysticalagriculture:inferium_essence", 32), deps=["welcome/table"],
          sub="Mystical Agriculture", desc=["Inferium ore drops essence; plant seeds made from it to farm resources."],
          rewards=[xp(75)]),
        Q("prosperity", "Prosperity", item("mysticalagriculture:prosperity_shard", 8), deps=["inferium"],
          rewards=[xp(100)]),
        Q("ultimate", "Ultimate circuit", item("mekanism:ultimate_control_circuit"), deps=["digital_miner"],
          rewards=[xp(500)]),
        Q("mekasuit", "MekaSuit", item("mekanism:mekasuit_helmet"), deps=["ultimate"],
          rewards=[xp(1000)]),
    ]},

    {"key": "ae2", "title": "&3Applied Energistics", "icon": "ae2:controller",
     "sub": "Digital storage and autocrafting", "quests": [
        Q("certus", "Certus quartz", item("ae2:certus_quartz_crystal", 16), deps=["industry/circuit"],
          desc=["Find it in meteorites (a compass from AE2 points to them) and grow more from budding quartz."],
          rewards=[xp(75)]),
        Q("charged", "Charged certus", item("ae2:charged_certus_quartz_crystal", 4), deps=["certus"],
          rewards=[xp(75)]),
        Q("inscriber", "Inscriber", item("ae2:inscriber"), deps=["charged"],
          desc=["Presses for the processors are found in meteorites."],
          rewards=[xp(150)]),
        Q("processors", "Processors", [item("ae2:logic_processor", 4), item("ae2:calculation_processor", 4), item("ae2:engineering_processor", 4)],
          deps=["inscriber"], rewards=[xp(200)]),
        Q("drive", "ME drive", [item("ae2:drive"), item("ae2:item_storage_cell_1k", 2)], deps=["processors"],
          rewards=[xp(150)]),
        Q("terminal", "Terminal", [item("ae2:terminal"), item("ae2:crafting_terminal")], deps=["processors"],
          rewards=[xp(150)]),
        Q("controller", "Controller", item("ae2:controller"), deps=["drive", "terminal"],
          rewards=[xp(250)]),
        Q("autocraft", "Autocrafting", [item("ae2:pattern_provider"), item("ae2:molecular_assembler")], deps=["controller"],
          rewards=[xp(400)]),
        Q("wireless", "Your storage, anywhere", item("ae2wtlib:wireless_universal_terminal"), deps=["controller"],
          rewards=[xp(300)]),
        Q("singularity", "Singularity", item("ae2:singularity"), deps=["autocraft"], optional=True,
          rewards=[xp(800)]),
    ]},

    {"key": "arcane", "title": "&dThe Arcane", "icon": "ars_nouveau:novice_spell_book",
     "sub": "Ars Nouveau, Iron's Spells, Occultism", "quests": [
        Q("novice", "Novice spell book", item("ars_nouveau:novice_spell_book"), deps=["welcome/table"],
          desc=["Ars Nouveau lets you design your own spells from glyphs. The book's &eWorn Notebook&r explains everything."],
          rewards=[xp(75)]),
        Q("scribe", "Scribe's table", item("ars_nouveau:scribes_table"), deps=["novice"],
          rewards=[xp(75)]),
        Q("source", "Source", [item("ars_nouveau:source_jar"), item("ars_nouveau:agronomic_sourcelink")], deps=["novice"],
          desc=["Sourcelinks turn nearby activity into Source, the power behind Ars rituals and machines."],
          rewards=[xp(100)]),
        Q("imbue", "Imbuement", item("ars_nouveau:imbuement_chamber"), deps=["source"],
          rewards=[xp(100)]),
        Q("apprentice", "Apprentice", item("ars_nouveau:apprentice_spell_book"), deps=["scribe", "imbue"],
          rewards=[xp(200)]),
        Q("archmage", "Archmage", item("ars_nouveau:archmage_spell_book"), deps=["apprentice"],
          rewards=[xp(500)]),
        Q("inscription", "Inscription table", item("irons_spellbooks:inscription_table"), deps=["welcome/table"],
          rewards=[xp(75)]),
        Q("essence", "Arcane essence", item("irons_spellbooks:arcane_essence", 16), deps=["inscription"],
          rewards=[xp(75)]),
        Q("iron_book", "Iron spell book", item("irons_spellbooks:iron_spell_book"), deps=["essence"],
          rewards=[xp(150)]),
        Q("forge", "Scroll forge", item("irons_spellbooks:scroll_forge"), deps=["essence"],
          desc=["Write your own scrolls from ink and the spells you have found."],
          rewards=[xp(150)]),
        Q("anvil", "Arcane anvil", item("irons_spellbooks:arcane_anvil"), deps=["forge"],
          rewards=[xp(150)]),
        Q("netherite_book", "Netherite spell book", item("irons_spellbooks:netherite_spell_book"), deps=["anvil"],
          rewards=[xp(600)]),
        Q("chalk", "Occultism", item("occultism:chalk_white"), deps=["welcome/table"],
          desc=["Draw pentacles in chalk and summon spirits to mine, craft and fight for you. Read the in-game guide before you start."],
          rewards=[xp(75)]),
        Q("bowl", "The ritual", item("occultism:golden_sacrificial_bowl"), deps=["chalk"],
          rewards=[xp(150)]),
    ]},

    {"key": "hearth", "title": "&aHearth & Home", "icon": "farmersdelight:cooking_pot",
     "sub": "Food, farms, seasons and building", "quests": [
        Q("seasons", "The turning year", item("sereneseasons:calendar"), deps=["welcome/welcome"],
          desc=["Seasons change every few in-game weeks. Most crops only grow in some seasons; JEI shows which. Greenhouse glass lets anything grow all year."],
          rewards=[xp(50)]),
        Q("board", "Cutting board", item("farmersdelight:cutting_board"), deps=["welcome/table"],
          rewards=[xp(50)]),
        Q("pot", "Cooking pot", item("farmersdelight:cooking_pot"), deps=["board"],
          desc=["Put it over a heat source (a campfire or stove) and cook real meals. Better food keeps you full longer."],
          rewards=[xp(75)]),
        Q("skillet", "Skillet", item("farmersdelight:skillet"), deps=["pot"],
          rewards=[xp(50)]),
        Q("rice", "Rice", item("farmersdelight:rice", 16), deps=["pot"],
          rewards=[xp(50)]),
        Q("feast", "Shepherd's pie", item("farmersdelight:shepherds_pie_block"), deps=["rice", "skillet"],
          rewards=[xp(150)]),
        Q("keg", "The keg", item("brewinandchewin:keg"), deps=["pot"],
          desc=["Brew ales, meads and cheeses."],
          rewards=[xp(75)]),
        Q("kitchen", "A proper kitchen", item("cookingforblockheads:cooking_table"), deps=["pot"],
          desc=["Craft any meal from the ingredients stored around your kitchen."],
          rewards=[xp(100)]),
        Q("furniture", "Make it home", [item("handcrafted:oak_couch"), item("mcwfurnitures:oak_chair")], deps=["welcome/table"],
          desc=["Handcrafted, Macaw's and Supplementaries add furniture, windows, roofs, bridges, lights and a lot more decoration."],
          rewards=[xp(50)]),
        Q("hammock", "Afternoon nap", item("comforts:hammock_white"), deps=["furniture"], optional=True,
          desc=["Hammocks skip the day, sleeping bags skip the night."],
          rewards=[xp(25)]),
    ]},

    {"key": "legends", "title": "&5Endgame", "icon": "minecraft:nether_star",
     "sub": "For the long haul", "quests": [
        Q("netherite", "Netherite", item("minecraft:netherite_ingot"), deps=["horizons/nether"],
          rewards=[xp(300)]),
        Q("elytra", "Wings", item("minecraft:elytra"), deps=["bosses/dragon"],
          rewards=[xp(500)]),
        Q("star", "Nether star", item("minecraft:nether_star"), deps=["bosses/wither"],
          rewards=[xp(500)]),
        Q("beacon", "A light in the sky", item("minecraft:beacon"), deps=["star"],
          rewards=[xp(500)]),
        Q("ignitium", "Ignitium", item("cataclysm:ignitium_ingot"), deps=["bosses/ignis"],
          rewards=[xp(800)]),
        Q("fiery", "Fiery ingot", item("twilightforest:fiery_ingot"), deps=["bosses/hydra"],
          rewards=[xp(600)]),
        Q("legend", "Ember & Iron", check(), deps=["beacon", "elytra", "ignitium", "fiery", "industry/mekasuit", "ae2/autocraft", "arcane/archmage"],
          shape="gear", size=2.0, icon="minecraft:dragon_egg",
          desc=["You beat the hardest fights, built the biggest machines and mastered the arcane. Not bad."],
          rewards=[xp(5000)]),
    ]},
]


# ---------- SNBT output ----------

def oid(*parts):
    """Stable 63-bit object id, hex like FTB's own (never 0 or 1, which FTB reserves)."""
    n = int(hashlib.sha1("/".join(parts).encode()).hexdigest()[:16], 16) & 0x7FFFFFFFFFFFFFFF
    return f"{max(n, 2):016X}"

KEY = re.compile(r"^[A-Za-z0-9_.+-]+$")

def snbt(v, ind=0):
    pad = "\t" * ind
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, Long):
        return f"{int(v)}L"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return f"{v}d"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, list):
        if not v:
            return "[ ]"
        if len(v) == 1 and isinstance(v[0], (str, dict)):
            # FTB writes one-element lists inline; matching it stops the server rewriting the files.
            return f"[{snbt(v[0], ind)}]"
        return "[\n" + "".join(f"{pad}\t{snbt(x, ind + 1)}\n" for x in v) + f"{pad}]"
    if isinstance(v, Inline):
        return "{ " + ", ".join(f"{k}: {snbt(v[k])}" for k in sorted(v)) + " }"
    if isinstance(v, dict):
        body = "".join(f"{pad}\t{k if KEY.match(k) else json.dumps(k)}: {snbt(v[k], ind + 1)}\n" for k in sorted(v))
        return "{\n" + body + f"{pad}}}"
    raise TypeError(type(v))

class Long(int):
    pass

class Inline(dict):
    """A compound FTB writes on one line (task item stacks)."""


def layout(quests):
    """Columns by dependency depth inside the chapter, rows spread around the centre line."""
    by_key = {q["key"]: q for q in quests}
    depth = {}
    def d(k):
        if k not in depth:
            local = [x for x in by_key[k]["deps"] if "/" not in x]
            depth[k] = 1 + max((d(x) for x in local), default=-1)
        return depth[k]
    cols = {}
    for q in quests:
        cols.setdefault(d(q["key"]), []).append(q)
    pos = {}
    for c, qs in cols.items():
        for i, q in enumerate(qs):
            pos[q["key"]] = (c * 2.0, (i - (len(qs) - 1) / 2) * 1.5)
    return pos


def build(check_ids=None):
    known = None
    if check_ids:
        data = json.loads(Path(check_ids).read_text())
        known = {"item": set(data["item"]), "entity": set(data["entity"])}
    problems = []
    keys = {f"{c['key']}/{q['key']}" for c in CHAPTERS for q in c["quests"]}
    lang = {"file.0000000000000001.title": "Ember & Iron"}

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "chapters").mkdir(parents=True)
    (OUT / "lang").mkdir()

    for order, ch in enumerate(CHAPTERS):
        cid = oid(ch["key"])
        lang[f"chapter.{cid}.title"] = ch["title"]
        if ch.get("sub"):
            lang[f"chapter.{cid}.chapter_subtitle"] = [ch["sub"]]
        pos = layout(ch["quests"])
        quests = []
        for q in ch["quests"]:
            full = f"{ch['key']}/{q['key']}"
            qid = oid(full)
            lang[f"quest.{qid}.title"] = q["title"]
            if q["sub"]:
                lang[f"quest.{qid}.quest_subtitle"] = q["sub"]
            if q["desc"]:
                lang[f"quest.{qid}.quest_desc"] = q["desc"]
            deps = []
            for dep in q["deps"]:
                ref = dep if "/" in dep else f"{ch['key']}/{dep}"
                if ref not in keys:
                    problems.append(f"{full}: unknown dependency {ref}")
                deps.append(oid(ref))
            tasks = []
            for i, t in enumerate(q["tasks"]):
                tid = oid(full, "task", str(i))
                if t["type"] == "item":
                    tasks.append({"id": tid, "type": "item", "item": Inline(count=1, id=t["item"]),
                                  **({"count": Long(t["count"])} if t["count"] > 1 else {})})
                    if known and t["item"] not in known["item"]:
                        problems.append(f"{full}: unknown item {t['item']}")
                elif t["type"] == "kill":
                    tasks.append({"id": tid, "type": "kill", "entity": t["entity"], "value": Long(t["value"])})
                    if known and t["entity"] not in known["entity"]:
                        problems.append(f"{full}: unknown entity {t['entity']}")
                elif t["type"] == "dimension":
                    tasks.append({"id": tid, "type": "dimension", "dimension": t["dimension"]})
                else:
                    tasks.append({"id": tid, "type": t["type"]})
            rewards = []
            for i, r in enumerate(q["rewards"]):
                rid = oid(full, "reward", str(i))
                if r["type"] == "xp":
                    rewards.append({"id": rid, "type": "xp", "xp": r["xp"]})
                else:
                    rewards.append({"id": rid, "type": "item", "item": {"count": 1, "id": r["item"]},
                                    **({"count": r["count"]} if r["count"] > 1 else {})})
                    if known and r["item"] not in known["item"]:
                        problems.append(f"{full}: unknown reward item {r['item']}")
            x, y = pos[q["key"]]
            entry = {"id": qid, "tasks": tasks, "x": x, "y": y}
            if deps:
                entry["dependencies"] = deps
            if rewards:
                entry["rewards"] = rewards
            if q["icon"]:
                entry["icon"] = {"id": q["icon"]}
                if known and q["icon"] not in known["item"]:
                    problems.append(f"{full}: unknown icon {q['icon']}")
            if q["shape"]:
                entry["shape"] = q["shape"]
            if q["size"]:
                entry["size"] = q["size"]
            if q["optional"]:
                entry["optional"] = True
            quests.append(entry)
        chapter = {"default_hide_dependency_lines": False, "default_quest_shape": "", "filename": ch["key"],
                   "group": "", "icon": {"id": ch["icon"]}, "id": cid, "images": [], "order_index": order,
                   "quest_links": [], "quests": quests}
        if known and ch["icon"] not in known["item"]:
            problems.append(f"{ch['key']}: unknown chapter icon {ch['icon']}")
        (OUT / "chapters" / f"{ch['key']}.snbt").write_text(snbt(chapter) + "\n")

    data = {"default_autoclaim_rewards": "disabled", "default_consume_items": False,
            "default_quest_disable_jei": False, "default_quest_shape": "circle", "default_reward_team": False,
            "detection_delay": 20, "disable_gui": False, "drop_book_on_death": False, "drop_loot_crates": False,
            "emergency_items_cooldown": 300, "fallback_locale": "", "grid_scale": 0.5,
            "hide_excluded_quests": False, "icon": {"id": "minecraft:campfire"}, "lock_message": "",
            "loot_crate_no_drop": {"boss": 0, "monster": 600, "passive": 4000}, "pause_game": False,
            "presets": {"goal": {"shape": "hexagon", "size": 2.0}, "info": {"shape": "gear", "size": 1.0},
                        "normal": {"shape": "square", "size": 1.0}},
            "progression_mode": "flexible", "show_lock_icons": True, "verify_on_load": False, "version": 13}
    (OUT / "data.snbt").write_text(snbt(data) + "\n")
    (OUT / "chapter_groups.snbt").write_text("{\n\tchapter_groups: [ ]\n}\n")
    (OUT / "lang" / "en_us.snbt").write_text(snbt(lang) + "\n")

    total = sum(len(c["quests"]) for c in CHAPTERS)
    print(f"Wrote {len(CHAPTERS)} chapters, {total} quests to {OUT}")
    for p in problems:
        print("PROBLEM:", p)
    return not problems


if __name__ == "__main__":
    ids = sys.argv[sys.argv.index("--check") + 1] if "--check" in sys.argv else None
    sys.exit(0 if build(ids) else 1)
