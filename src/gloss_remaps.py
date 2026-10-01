#!/usr/bin/env python3
"""
SignBridge — ASL Gloss Remapping Table

The ASLLVD dataset uses specific gloss notation and doesn't include
all common English words in citation form. This table maps English words
to their ASLLVD equivalents or synonyms.

Words not found here fall through to fingerspelling.
"""

# English word → ASLLVD gloss (if different from the English word)
# Only include mappings where the ASLLVD gloss is DIFFERENT from the English word
GLOSS_REMAPS = {
    # Pronouns — now have synthetic deictic signs in pose library
    # (I, ME, MY, YOU, YOUR, HE, SHE, IT, WE, US, OUR, THEY, THEM, THEIR, THIS, etc.)
    # These match directly, no remap needed
    
    # Pronoun variants
    "HIM": "HE",
    "HERS": "HER",
    "HIS": "HE",
    "MINE": "MY",
    "OURS": "OUR",
    "THEIRS": "THEIR",
    "YOURS": "YOUR",
    "MYSELF": "MY",
    "YOURSELF": "YOUR",
    "HIMSELF": "HE",
    "HERSELF": "SHE",
    "ITSELF": "IT",
    
    # Common words with different ASL glosses
    "GOOD": "FINE",
    "LOVE": "CARE",
    "NEED": "MUST",
    "THANK": "THANKFUL",
    "THANKS": "THANKFUL",
    "THANK-YOU": "THANKFUL",
    "HEAR": "LISTEN",
    "HELP": "SUPPORT",
    "HUNGRY": "WANT-FOOD",
    "JOB": "WORK",
    "BOOK": "READ",
    "DOG": "ANIMAL",
    "HAND": "ARM",
    "NICE": "FINE",
    "OPEN": "DOOR",
    "OUTSIDE": "OUT",
    "PRETTY": "BEAUTIFUL",
    "REAL": "TRUE",
    "ROOM": "HOUSE",
    "SHARE": "GIVE",
    "SPEAK": "TALK",
    "SURE": "KNOW",
    "SWEET": "SUGAR",
    "TODAY": "NOW",
    "TOGETHER": "WITH",
    "TONIGHT": "NIGHT",
    "TOO": "ALSO",
    "TRUST": "BELIEVE",
    "VISIT": "COME",
    "WAY": "PATH",
    "WEAR": "CLOTHES",
    "WELL": "FINE",
    "WENT": "GO",
    "WILL": "FUTURE",
    "WISH": "WANT",
    "WITHOUT": "NONE",
    "YET": "STILL",
    "NO": "#NO",
    "YES": "#YES",
    "OK": "#OK",
    "OKAY": "#OK",
    "WHAT": "#WHAT",
    "WOW": "#WOW",
    "HA": "#HA-HA",
    "HAHA": "#HA-HA",
}

# Words that should always be fingerspelled (names, proper nouns)
ALWAYS_FINGERSPELL = {
    "KELLEN", "PERRI", "SCARLET", "ARCHIE", "POPPY",
    "ARIZONA", "SCOTTSDALE", "PHOENIX",
    "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY",
}

# Words that don't have signs and should be skipped (filler/zero-morpheme in ASL)
SKIP_WORDS = {
    "THE", "A", "AN", "OF", "UM", "UH", "LIKE", "YOU_KNOW",
    "JUST", "REALLY", "VERY", "QUITE", "KIND_OF",
    "SORT_OF", "I_MEAN", "ACTUALLY", "BASICALLY", "LITERALLY",
    # ASL zero-morphemes — these don't have signs, just omit
    "IS", "ARE", "AM", "BE", "BEEN", "BEING",
    "TO",  # ASL doesn't use "to" — direction is implied by the verb
    "OF",  # possessive is shown by word order
}


def remap_gloss(english_word, available_glosses):
    """
    Try to find the best ASLLVD gloss for an English word.
    
    Returns: (gloss, source) where source is 'direct', 'remap', 'synonym', or None
    """
    word = english_word.upper().strip()
    
    if word in SKIP_WORDS or not word:
        return None, "skip"
    
    if word in ALWAYS_FINGERSPELL:
        return "FINGERSPELL", "fingerspell"
    
    # Try direct lookup (this now catches I, ME, MY, YOU, HE, SHE, etc.)
    if word in available_glosses:
        return word, "direct"
    
    # Try with :i suffix (individual variant)
    if f"{word}:i" in available_glosses:
        return f"{word}:i", "remap"
    
    # Try remap table
    remapped = GLOSS_REMAPS.get(word)
    if remapped and remapped in available_glosses:
        return remapped, "remap"
    
    # Try remap with :i suffix
    remapped = GLOSS_REMAPS.get(word)
    if remapped and f"{remapped}:i" in available_glosses:
        return f"{remapped}:i", "remap"
    
    # Last resort: fingerspell
    return "FINGERSPELL", "fingerspell"