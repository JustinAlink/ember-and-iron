# Ember & Iron

A big kitchen-sink modpack for Minecraft 1.21.1 (NeoForge) with RPG at its core: every monster has
a level, loot rolls with affixes, and a quest book walks you through machines, magic, new dimensions
and a long list of bosses. About 200 mods, built for playing together on a server.

## Playing

1. Install [Prism Launcher](https://prismlauncher.org/) and sign in with your Microsoft account.
2. Download **Ember-and-Iron-Prism.zip** from the
   [Prism instance release](https://github.com/JustinAlink/ember-and-iron/releases/tag/prism-instance).
3. In Prism: *Add Instance* > *Import* > pick the zip.
4. Press *Launch*. The first start downloads every mod (a few minutes); after that it only fetches
   what changed.
5. Multiplayer > Add Server: `node.junipergray.nl:25565`.

The instance updates itself before every launch, so you stay in sync with the server without doing
anything. It is set to 6 GB of RAM; lower it under *Edit* > *Settings* > *Java* if your machine has
less than 12 GB, raise it if you have plenty.

Controllers work out of the box (Controlify). Voice chat is built in: press `V` to set it up.

## What is in it

- **RPG:** Remnants: RPG Mobs (monster levels, ranks and named bosses), Apotheosis (affix loot,
  gems, reforging, a reworked enchanting table), Pufferfish's Skills with skill trees, Better Combat
  and Combat Roll, Iron's Spells 'n Spellbooks, Artifacts, Relics, Simply Swords, Epic Knights,
  Immersive Armors.
- **Tech:** Create with Steam 'n' Rails, Crafts & Additions, Enchantment Industry, New Age, Big
  Cannons and more; Mekanism, Applied Energistics 2, Immersive Engineering, Powah, Industrial
  Foregoing, Mystical Agriculture.
- **Magic:** Ars Nouveau, Iron's Spells, Occultism.
- **Dimensions:** the Twilight Forest, the Aether, the Undergarden, the Bumblezone, Deeper and
  Darker's Otherside, plus a rebuilt Nether and End (Incendium, Nullscape).
- **Bosses and monsters:** L_Ender's Cataclysm, Mowzie's Mobs, Bosses of Mass Destruction, Born in
  Chaos, Aquamirae, Mutant Monsters, Friends & Foes.
- **World:** Terralith and Tectonic terrain, all of YUNG's structures, Dungeons and Taverns, Towns
  and Towers, When Dungeons Arise, Repurposed Structures, Explorify, Lootr (every player gets their
  own chest loot).
- **Home:** Farmer's Delight and friends, Serene Seasons, Supplementaries, Quark, Handcrafted,
  Macaw's furniture and building sets, Comforts.
- **Quality of life:** FTB Quests (128 quests in 10 chapters), JEI, Jade, Xaero's maps, Waystones,
  Sophisticated Backpacks and Storage, FTB Ultimine, Corpse, Open Parties and Claims, Simple Voice
  Chat.
- **Performance:** Sodium, ModernFix, FerriteCore, ImmediatelyFast, Entity Culling, More Culling,
  Dynamic FPS.

The full list is the `mods/` folder.

## How it works

The pack is a [packwiz](https://packwiz.infra.link/) project. `pack.toml` and the `mods/*.pw.toml`
files pin every mod to an exact file and hash; nothing is downloaded from a mod's "latest" at play
time. The Pelican server and every Prism instance run
[packwiz-installer](https://github.com/packwiz/packwiz-installer) against `main` on start, so
**a push to main is a release**: players get it on their next launch, the server on its next
restart. CI boots a real dedicated server from every commit, so main should never be broken.

The installer jars are pinned by version and hash in `scripts/tools.env`.

## Changing the pack

Needs [packwiz](https://github.com/packwiz/packwiz) (`go install github.com/packwiz/packwiz@latest`).

```bash
packwiz mr add <modrinth-slug>   # add a mod (Modrinth first)
packwiz cf add <curseforge-slug> # only for mods that are not on Modrinth
packwiz update --all             # update everything
packwiz remove <name>
```

Check the new mod's `side` in its `.pw.toml`: a client-only mod marked `both` crashes the server
(Controlify did).

**Quests** are generated: edit `scripts/quests.py`, then run `python3 scripts/quests.py`. Do not
edit them in-game; the server overwrites its copy from the repo on every start.

**Test before pushing.** `scripts/boot-test.sh` installs and boots a dedicated server from any
pack URL, the same check CI runs:

```bash
packwiz serve --port 8099 &
BOOT_TEST_JAVA_OPTS="-Xmx6G" scripts/boot-test.sh /path/to/scratch/server http://localhost:8099/pack.toml
```

It needs Java 21 (`docker run ... eclipse-temurin:21-jdk` works if your system Java is newer).

## Server

Runs on Pelican (`panel.junipergray.nl`) with the NeoForge egg. Its startup command syncs the pack
before launching:

```
java -jar packwiz-installer-bootstrap.jar --bootstrap-no-update --bootstrap-main-jar packwiz-installer.jar -g -s server https://raw.githubusercontent.com/JustinAlink/ember-and-iron/main/pack.toml && java ... @libraries/net/neoforged/neoforge/<version>/unix_args.txt nogui
```

Server-only settings (`server.properties`, the whitelist, voice chat's port) live on the server, not
in this repo, so syncing never overwrites them. Voice chat uses its own UDP port, the server's
second allocation.
