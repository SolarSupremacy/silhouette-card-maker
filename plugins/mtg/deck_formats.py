import json
import re

from enum import Enum
from typing import Callable, Tuple
from xml.etree import ElementTree as ET

from scryfall import remove_nonalphanumeric

card_data_tuple = Tuple[str, str, int, int]

def parse_deck_helper(deck_text: str, is_card_line: Callable[[str], bool], extract_card_data: Callable[[str], card_data_tuple], handle_card: Callable) -> None:
    error_lines = []

    index = 0
    for line in deck_text.strip().split('\n'):
        if is_card_line(line):
            index = index + 1

            name, set_code, collector_number, quantity = extract_card_data(line)

            parts = [f'Index: {index}', f'quantity: {quantity}']
            if set_code: parts.append(f'set code: {set_code}')
            if collector_number: parts.append(f'collector number: {collector_number}')
            if name: parts.append(f'name: {name}')
            print(', '.join(parts))
            try:
                handle_card(index, name, set_code, collector_number, quantity)
            except Exception as e:
                print(f'Error: {e}')
                error_lines.append((line, e))

        else:
            print(f'Skipping: "{line}"')

    if len(error_lines) > 0:
        print(f'Errors: {error_lines}')

# Isshin, Two Heavens as One
# Arid Mesa
# Battlefield Forge
# Blazemire Verge
# Blightstep Pathway
# Blood Crypt
def parse_simple_list(deck_text, handle_card: Callable) -> None:
    def is_simple_card_line(line) -> bool:
        return bool(line.strip())

    def extract_simple_card_data(line) -> card_data_tuple:
        return (line.strip(), "", "", 1)

    parse_deck_helper(deck_text, is_simple_card_line, extract_simple_card_data, handle_card)

# About
# Name Death & Taxes

# Companion
# 1 Yorion, Sky Nomad

# Deck
# 2 Arid Mesa
# 1 Lion Sash
# 1 Loran of the Third Path
# 2 Witch Enchanter

# Sideboard
# 1 Containment Priest
def parse_mtga(deck_text, handle_card: Callable) -> None:
    pattern = re.compile(r'(\d+)x?\s+(.+?)\s+\((\w+)\)\s+(\d+)', re.IGNORECASE)
    fallback_pattern = re.compile(r'(\d+)x?\s+(.+)')

    def is_mtga_card_line(line) -> bool:
        return bool(pattern.match(line) or fallback_pattern.match(line))

    def extract_mtga_card_data(line) -> card_data_tuple:
        match = pattern.match(line)
        if match:
            quantity = int(match.group(1))
            name = match.group(2).strip()
            set_code = match.group(3).strip()
            collector_number = match.group(4).strip()

            return (name, set_code, collector_number, quantity)
        else:
            # Handle simpler "1x Mountain" lines
            fallback_match = fallback_pattern.match(line)
            quantity = int(fallback_match.group(1))
            name = fallback_match.group(2).strip()

            return (name, "", "", quantity)

    parse_deck_helper(deck_text, is_mtga_card_line, extract_mtga_card_data, handle_card)

# 1 Abzan Battle Priest
# 1 Abzan Falconer
# 1 Aerial Surveyor
# 1 Ainok Bond-Kin
# 1 Angel of Condemnation
# 2 Witch Enchanter

# SIDEBOARD:
# 1 Containment Priest
# 3 Deafening Silence
# 2 Disruptor Flute
def parse_mtgo(deck_text, handle_card: Callable) -> None:
    def is_mtgo_card_line(line) -> bool:
        line = line.strip()
        return bool(line and line[0].isdigit())

    def extract_mtgo_card_data(line) -> card_data_tuple:
        parts = line.split(' ', 1)
        quantity = int(parts[0])
        name = parts[1].strip()
        return (name, "", "", quantity)

    parse_deck_helper(deck_text, is_mtgo_card_line, extract_mtgo_card_data, handle_card)

# 1x Agadeem's Awakening // Agadeem, the Undercrypt (znr) 90 [Resilience,Land]
# 1x Ancient Cornucopia (big) 16 [Maybeboard{noDeck}{noPrice},Mana Advantage]
# 1x Arachnogenesis (cmm) 647 [Maybeboard{noDeck}{noPrice},Mass Disruption]
# 1x Ashnod's Altar (ema) 218 *F* [Mana Advantage]
# 1x Assassin's Trophy (sld) 139 [Targeted Disruption]
# 2x Boseiju Reaches Skyward // Branch of Boseiju (neo) 177 [Ramp] ^Have,#37d67a^
def parse_archidekt(deck_text, handle_card: Callable) -> None:
    pattern = re.compile(r'^(\d+)x?\s+(.+?)\s+\((\w+)\)\s+([\w\-]+).*')
    def is_archidekt_card_line(line: str) -> bool:
        return bool(pattern.match(line))

    def extract_archidekt_card_data(line: str) -> card_data_tuple:
        match = pattern.match(line)
        quantity = int(match.group(1))
        name = match.group(2).strip()
        set_code = match.group(3).strip()
        collector_number = match.group(4).strip()

        return (name, set_code, collector_number, quantity)

    parse_deck_helper(deck_text, is_archidekt_card_line, extract_archidekt_card_data, handle_card)

# //Main
# 1 [2XM#310] Ash Barrens
# 1 Blinkmoth Nexus
# 1 Bloodstained Mire
# 1 Buried Ruin
# 2 Command Beacon

# //Sideboard
# 1 [2XM#315] Darksteel Citadel

# //Maybeboard
# 1 [MID#159] Smoldering Egg // Ashmouth Dragon
def parse_deckstats(deck_text, handle_card: Callable) -> None:
    pattern = re.compile(r'^(\d+)\s+(?:\[(\w+)?#(\w+)\]\s+)?(.+)$')
    def is_deckstats_card_line(line: str) -> bool:
        return bool(pattern.match(line))

    def extract_deckstats_card_data(line: str) -> card_data_tuple:
        match = pattern.match(line)
        quantity = int(match.group(1))
        set_code = match.group(2) or ""
        collector_number = match.group(3) or ""
        name = match.group(4).strip()

        return (name, set_code, collector_number, quantity)

    parse_deck_helper(deck_text, is_deckstats_card_line, extract_deckstats_card_data, handle_card)

# 1 Lulu, Loyal Hollyphant (CLB) 477 *E*
# 1 Abzan Battle Priest (IMA) 2
# 1 Abzan Falconer (ZNC) 9
# 1 Aerial Surveyor (NEC) 5
# 1 Ainok Bond-Kin (2X2) 5
# 1 Pegasus Guardian // Rescue the Foal (CLB) 36
# 4 Plains (MOM) 277
# 2 Witch Enchanter // Witch-Blessed Meadow (MH3) 239

# SIDEBOARD:
# 1 Containment Priest (M21) 13
# 1 Deafening Silence (MB2) 9
# 1 Disruptor Flute (MH3) 209
def parse_moxfield(deck_text, handle_card: Callable) -> None:
    pattern = re.compile(r'^(\d+)\s+(.+?)\s+\((\w+)\)\s+([\w\-]+)')
    def is_moxfield_card_line(line: str) -> bool:
        return bool(pattern.match(line))

    def extract_moxfield_card_data(line: str) -> card_data_tuple:
        match = pattern.match(line)
        quantity = int(match.group(1))
        name = match.group(2).strip()
        set_code = match.group(3).strip()
        collector_number = match.group(4).strip()

        return (name, set_code, collector_number, quantity)

    parse_deck_helper(deck_text, is_moxfield_card_line, extract_moxfield_card_data, handle_card)

# Scryfall deck builder JSON
def parse_scryfall_json(deck_text, handle_card: Callable) -> None:
    data = json.loads(deck_text)
    entries = data.get("entries", {})
    for entry in entries.values():
        for index, item in enumerate(entry, start=1):
            card_digest = item.get("card_digest", {})
            if card_digest is None:
                continue

            name = card_digest.get("name", "")
            set_code = card_digest.get("set", "")
            collector_number = card_digest.get("collector_number", "")
            quantity = item.get("count", 1)

            parts = [f'Index: {index}', f'quantity: {quantity}']
            if set_code: parts.append(f'set code: {set_code}')
            if collector_number: parts.append(f'collector number: {collector_number}')
            if name: parts.append(f'name: {name}')
            print(', '.join(parts))
            handle_card(index, name, set_code, collector_number, quantity)

# MPCFill XML
def extract_mpcfill_card_ids(deck_text: str) -> set[str]:
    """Extract all unique card IDs from MPCFill XML for prefetching."""
    data = ET.fromstring(deck_text)
    card_ids = set()

    fronts = data.find("fronts")
    if fronts:
        for front in fronts.findall("card"):
            card_ids.add(front.find("id").text)

    backs = data.find("backs")
    if backs:
        for back in backs.findall("card"):
            card_ids.add(back.find("id").text)

    return card_ids


def parse_mpcfill_xml(deck_text, handle_card: Callable) -> None:
    """
    Parse MPCFill XML and call handle_card once per slot.

    Each slot represents one physical card. handle_card signature:
        handle_card(slot, front_id, front_name, back_id, back_name)

    back_id and back_name will be None if the slot has no custom back.
    """
    data = ET.fromstring(deck_text)
    fronts = data.find("fronts")
    backs = data.find("backs")

    card_qty = int(data.find("details").find("quantity").text)

    # Create per-slot entries: {front_id, front_name, back_id, back_name}
    slots = [{"front_id": None, "front_name": None, "back_id": None, "back_name": None} for _ in range(card_qty)]

    if fronts is None:
        raise ValueError("No fronts found in decklist")

    # Assign fronts to ALL their slots
    for front in fronts.findall("card"):
        card_id = front.find("id").text
        name_parts = front.find("name").text.split(".")
        name = ".".join(name_parts[:-1]) if len(name_parts) > 1 else name_parts[0]
        slot_indices = [int(s) for s in front.find("slots").text.split(",")]
        for slot_idx in slot_indices:
            slots[slot_idx]["front_id"] = card_id
            slots[slot_idx]["front_name"] = name

    # Assign backs to ALL their slots
    if backs:
        for back in backs.findall("card"):
            card_id = back.find("id").text
            name_parts = back.find("name").text.split(".")
            name = ".".join(name_parts[:-1]) if len(name_parts) > 1 else name_parts[0]
            slot_indices = [int(s) for s in back.find("slots").text.split(",")]
            for slot_idx in slot_indices:
                slots[slot_idx]["back_id"] = card_id
                slots[slot_idx]["back_name"] = name

    # Call handle_card once per slot
    for slot_idx, slot in enumerate(slots):
        if slot["front_id"] is None:
            print(f"Warning: Slot {slot_idx} has no front image, skipping")
            continue

        print(f"Slot {slot_idx}: {slot['front_name']}" + (f" / {slot['back_name']}" if slot['back_id'] else ""))
        handle_card(slot_idx, slot["front_id"], slot["front_name"], slot["back_id"], slot["back_name"])

class DeckFormat(str, Enum):
    SIMPLE = "simple"
    MTGA = "mtga"
    MTGO = "mtgo"
    ARCHIDEKT = "archidekt"
    DECKSTATS = "deckstats"
    MOXFIELD = "moxfield"
    SCRYFALL_JSON = "scryfall_json"
    MPCFILL_XML = "mpcfill_xml"

def parse_deck(deck_text: str, format: DeckFormat, handle_card: Callable) -> None:
    if format == DeckFormat.SIMPLE:
        parse_simple_list(deck_text, handle_card)
    elif format == DeckFormat.MTGA:
        parse_mtga(deck_text, handle_card)
    elif format == DeckFormat.MTGO:
        parse_mtgo(deck_text, handle_card)
    elif format == DeckFormat.ARCHIDEKT:
        parse_archidekt(deck_text, handle_card)
    elif format == DeckFormat.DECKSTATS:
        parse_deckstats(deck_text, handle_card)
    elif format == DeckFormat.MOXFIELD:
        parse_moxfield(deck_text, handle_card)
    elif format == DeckFormat.SCRYFALL_JSON:
        parse_scryfall_json(deck_text, handle_card)
    elif format == DeckFormat.MPCFILL_XML:
        parse_mpcfill_xml(deck_text, handle_card)
    else:
        raise ValueError("Unrecognized deck format")