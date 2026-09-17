#!/usr/bin/env python3
"""
Reversible Encoding / Transformation Lab
=========================================

Supports:
    UTF-8
    ISO-8859-1
    ISO-2022-JP
    Windows-1252

Generates 60+ distinct reversible variations from one input string.

Important:
    These transformations are intended for encoding/decoding experiments,
    MIME/character-set testing, and interoperability testing.

    They are NOT intended to bypass security, spam filters, moderation,
    authentication, or other controls.

The decoder understands every variation produced by this script.

Requirements:
    Python 3.9+

No external packages are required.
"""

from __future__ import annotations

import base64
import codecs
import quopri
import re
from typing import Callable, Dict, List, Tuple


# ============================================================
# CONFIGURATION
# ============================================================

VARIATION_COUNT = 60

CHARSETS = [
    "utf-8",
    "iso-8859-1",
    "iso-2022-jp",
    "windows-1252",
]


# ============================================================
# BASIC CHARACTER-SET FUNCTIONS
# ============================================================

def encode_charset(text: str, charset: str) -> bytes:
    """
    Encode Unicode text using a requested character set.

    strict=True means unsupported characters raise UnicodeEncodeError.
    """
    return text.encode(charset, errors="strict")


def decode_charset(data: bytes, charset: str) -> str:
    """
    Decode bytes using a requested character set.
    """
    return data.decode(charset, errors="strict")


def hex_bytes(data: bytes) -> str:
    """Convert bytes into continuous hexadecimal."""
    return data.hex().upper()


def unhex_bytes(value: str) -> bytes:
    """Convert hexadecimal back into bytes."""
    return bytes.fromhex(value)


def b64_bytes(data: bytes) -> str:
    """Standard Base64."""
    return base64.b64encode(data).decode("ascii")


def unb64(value: str) -> bytes:
    """Decode standard Base64."""
    return base64.b64decode(value.encode("ascii"), validate=True)


# ============================================================
# QUOTED-PRINTABLE
# ============================================================

def qp_encode_bytes(data: bytes) -> str:
    """
    RFC-style quoted-printable encoding.

    quopri works on bytes and therefore handles arbitrary byte sequences.
    """
    return quopri.encodestring(
        data,
        quotetabs=True
    ).decode("ascii")


def qp_decode(value: str) -> bytes:
    """Decode quoted-printable text back into bytes."""
    return quopri.decodestring(value.encode("ascii"))


def qp_byte(b: int) -> str:
    """Represent one byte as a quoted-printable =XX sequence."""
    return f"={b:02X}"


# ============================================================
# REVERSIBLE TEXT TRANSFORMATIONS
# ============================================================

def vowel_qp_transform(text: str, charset: str = "utf-8") -> str:
    """
    Replace vowels with their quoted-printable byte representation.

    Example for UTF-8:
        a -> =61
        e -> =65
        i -> =69
        o -> =6F
        u -> =75

    Uppercase vowels are handled as well.

    The remaining text is left readable.
    """

    result = []

    for char in text:
        if char in "aeiouAEIOU":
            encoded = char.encode(charset)

            # Normally ASCII vowels are one byte.
            result.append("".join(qp_byte(b) for b in encoded))
        else:
            result.append(char)

    return "".join(result)


def reverse_vowel_qp(value: str) -> str:
    """
    Reverse vowel quoted-printable sequences.

    We only convert =XX sequences corresponding to ASCII vowels.
    """

    vowel_bytes = {
        0x41,  # A
        0x45,  # E
        0x49,  # I
        0x4F,  # O
        0x55,  # U
        0x61,  # a
        0x65,  # e
        0x69,  # i
        0x6F,  # o
        0x75,  # u
    }

    pattern = re.compile(r"=([0-9A-Fa-f]{2})")

    def repl(match):
        b = int(match.group(1), 16)

        if b in vowel_bytes:
            return chr(b)

        return match.group(0)

    return pattern.sub(repl, value)


# ------------------------------------------------------------
# Consecutive-letter separator
# ------------------------------------------------------------

def separate_duplicates(text: str, separator: str) -> str:
    """
    Insert a reversible marker between consecutive identical characters.

    Example:
        letter -> let=3Fter

    The marker itself is configurable.
    """

    if not text:
        return text

    output = [text[0]]

    for current in text[1:]:
        previous = output[-1]

        if previous == current:
            output.append(separator)

        output.append(current)

    return "".join(output)


def remove_duplicate_separator(text: str, separator: str) -> str:
    """Reverse separate_duplicates()."""
    return text.replace(separator, "")


# ------------------------------------------------------------
# Space transformations
# ------------------------------------------------------------

def replace_spaces(text: str, replacement: str) -> str:
    """Replace ordinary spaces with a reversible replacement."""
    return text.replace(" ", replacement)


def restore_spaces(text: str, replacement: str) -> str:
    """Restore spaces."""
    return text.replace(replacement, " ")


# ------------------------------------------------------------
# Start/end modifications
# ------------------------------------------------------------

def add_wrappers(text: str, prefix: str, suffix: str) -> str:
    """Add a reversible wrapper."""
    return prefix + text + suffix


def remove_wrappers(
    text: str,
    prefix: str,
    suffix: str
) -> str:

    if not text.startswith(prefix):
        raise ValueError("Expected prefix was not found.")

    if not text.endswith(suffix):
        raise ValueError("Expected suffix was not found.")

    return text[len(prefix):-len(suffix)] if suffix else text[len(prefix):]


# ------------------------------------------------------------
# Hidden/control-character transformation
# ------------------------------------------------------------

HIDDEN_MARKERS = {
    "ZWSP": "\u200b",       # Zero Width Space
    "ZWNJ": "\u200c",       # Zero Width Non-Joiner
    "ZWJ": "\u200d",        # Zero Width Joiner
    "WORD_JOINER": "\u2060",
}


def insert_hidden(text: str, marker: str, every: int = 2) -> str:
    """
    Insert an invisible Unicode marker periodically.

    The decoder removes exactly the selected marker.
    """

    if not text:
        return text

    result = []

    for index, char in enumerate(text, start=1):
        result.append(char)

        if index % every == 0:
            result.append(marker)

    return "".join(result)


def remove_hidden(text: str, marker: str) -> str:
    """Remove the hidden marker."""
    return text.replace(marker, "")


# ============================================================
# MIME ENCODED-WORD STYLE TRANSFORM
# ============================================================

def mime_q_word(word: str, charset: str = "utf-8") -> str:
    """
    Produce a MIME encoded-word-like representation.

    Example:
        Hello
        becomes something similar to

        =?utf-8?Q?Hello?=

    This is generated for interoperability/testing purposes.
    """

    raw = word.encode(charset)

    encoded = []

    for b in raw:
        # RFC-style Q readable characters
        if (
            33 <= b <= 60
            or 62 <= b <= 126
        ) and b not in (61, 63, 95):
            encoded.append(chr(b))
        elif b == 32:
            encoded.append("_")
        else:
            encoded.append(f"={b:02X}")

    payload = "".join(encoded)

    return f"=?{charset}?Q?{payload}?="


def mime_split_words(text: str, charset: str = "utf-8") -> str:
    """
    Convert each whitespace-separated word to an encoded-word-like
    representation.
    """

    parts = text.split(" ")

    return " ".join(
        mime_q_word(part, charset)
        for part in parts
    )


def decode_mime_q_word(value: str) -> str:
    """
    Decode the MIME encoded-word-like representation produced above.
    """

    pattern = re.compile(
        r"=\?([^?]+)\?Q\?([^?]*)\?=",
        re.IGNORECASE
    )

    def repl(match):
        charset = match.group(1)
        payload = match.group(2)

        # MIME Q encoding uses "_" for space.
        payload = payload.replace("_", " ")

        data = bytearray()
        i = 0

        while i < len(payload):
            if (
                payload[i] == "="
                and i + 2 < len(payload)
                and re.match(
                    r"^[0-9A-Fa-f]{2}$",
                    payload[i + 1:i + 3]
                )
            ):
                data.append(
                    int(payload[i + 1:i + 3], 16)
                )
                i += 3
            else:
                data.extend(
                    payload[i].encode("ascii")
                )
                i += 1

        return data.decode(charset)

    return pattern.sub(repl, value)


# ============================================================
# VARIATION STORAGE
# ============================================================

class Variation:
    """
    Stores:
        ID
        Description
        Encoded output
        Decoder function
    """

    def __init__(
        self,
        number: int,
        name: str,
        encoded: str,
        decoder: Callable[[str], str],
    ):
        self.number = number
        self.name = name
        self.encoded = encoded
        self.decoder = decoder


# ============================================================
# VARIATION GENERATOR
# ============================================================

def generate_variations(text: str) -> List[Variation]:
    """
    Generate many distinct reversible transformations.

    Each generated string begins with:

        EV##:

    This makes it possible for decode_variation() to determine
    which decoder should be used.
    """

    variations: List[Variation] = []

    def add(
        number: int,
        name: str,
        payload: str,
        decoder: Callable[[str], str],
    ):
        variations.append(
            Variation(
                number,
                name,
                f"EV{number:02d}:{payload}",
                decoder,
            )
        )

    number = 1

    # ========================================================
    # 1-4: STANDARD CHARACTER-SET ENCODING
    # ========================================================

    for charset in CHARSETS:
        try:
            data = encode_charset(text, charset)
        except UnicodeEncodeError:
            # Some Unicode input cannot exist in ISO-8859-1,
            # Windows-1252, etc.
            continue

        payload = b64_bytes(data)

        charset_copy = charset

        add(
            number,
            f"Standard {charset}",
            payload,
            lambda value, c=charset_copy:
                decode_charset(
                    unb64(value),
                    c
                )
        )

        number += 1

    # ========================================================
    # 5-8: HEX BYTE REPRESENTATION
    # ========================================================

    for charset in CHARSETS:
        try:
            data = encode_charset(text, charset)
        except UnicodeEncodeError:
            continue

        payload = hex_bytes(data)

        charset_copy = charset

        add(
            number,
            f"Hex bytes ({charset})",
            payload,
            lambda value, c=charset_copy:
                decode_charset(
                    unhex_bytes(value),
                    c
                )
        )

        number += 1

    # ========================================================
    # 9: UTF-8 QUOTED-PRINTABLE
    # ========================================================

    data = text.encode("utf-8")
    payload = qp_encode_bytes(data)

    add(
        number,
        "UTF-8 quoted-printable",
        payload,
        lambda value:
            qp_decode(value).decode("utf-8")
    )

    number += 1

    # ========================================================
    # 10-13: VOWELS AS QP
    # ========================================================

    for charset in CHARSETS:
        try:
            transformed = vowel_qp_transform(text, charset)
        except UnicodeEncodeError:
            continue

        add(
            number,
            f"Vowels quoted-printable ({charset})",
            transformed,
            lambda value:
                reverse_vowel_qp(value)
        )

        number += 1

    # ========================================================
    # 14-18: SPACE REPLACEMENTS
    # ========================================================

    space_replacements = [
        "__",
        "____",
        "________",
        "<SP>",
        "=20",
    ]

    for replacement in space_replacements:
        transformed = replace_spaces(text, replacement)

        add(
            number,
            f"Spaces -> {repr(replacement)}",
            transformed,
            lambda value, r=replacement:
                restore_spaces(value, r)
        )

        number += 1

    # ========================================================
    # 19-23: START / END WRAPPERS
    # ========================================================

    wrappers = [
        ("[[", "]]"),
        ("<<<", ">>>"),
        ("___", "___"),
        ("BEGIN:", ":END"),
        ("@@@", "@@@"),
    ]

    for prefix, suffix in wrappers:
        transformed = add_wrappers(
            text,
            prefix,
            suffix
        )

        add(
            number,
            f"Wrapper {repr(prefix)} ... {repr(suffix)}",
            transformed,
            lambda value, p=prefix, s=suffix:
                remove_wrappers(value, p, s)
        )

        number += 1

    # ========================================================
    # 24-27: HIDDEN UNICODE MARKERS
    # ========================================================

    hidden_configs = [
        ("ZWSP", HIDDEN_MARKERS["ZWSP"], 1),
        ("ZWSP", HIDDEN_MARKERS["ZWSP"], 2),
        ("ZWNJ", HIDDEN_MARKERS["ZWNJ"], 2),
        ("WORD_JOINER", HIDDEN_MARKERS["WORD_JOINER"], 3),
    ]

    for name, marker, every in hidden_configs:
        transformed = insert_hidden(
            text,
            marker,
            every
        )

        add(
            number,
            f"Hidden {name}, interval={every}",
            transformed,
            lambda value, m=marker:
                remove_hidden(value, m)
        )

        number += 1

    # ========================================================
    # 28-32: DUPLICATE LETTER SEPARATORS
    # ========================================================

    duplicate_separators = [
        "~",
        "::",
        "[DUP]",
        "=5F",
        "____",
    ]

    for separator in duplicate_separators:
        transformed = separate_duplicates(
            text,
            separator
        )

        add(
            number,
            f"Duplicate separator {repr(separator)}",
            transformed,
            lambda value, s=separator:
                remove_duplicate_separator(value, s)
        )

        number += 1

    # ========================================================
    # 33-36: MIME-LIKE WORD SEPARATION
    # ========================================================

    for charset in [
        "utf-8",
        "iso-8859-1",
        "windows-1252",
        "iso-2022-jp",
    ]:
        try:
            transformed = mime_split_words(
                text,
                charset
            )
        except UnicodeEncodeError:
            continue

        charset_copy = charset

        add(
            number,
            f"MIME Q-word style ({charset})",
            transformed,
            lambda value:
                decode_mime_q_word(value)
        )

        number += 1

    # ========================================================
    # 37-41: BASE64 + VISIBLE WRAPPERS
    # ========================================================

    data = text.encode("utf-8")
    b64 = b64_bytes(data)

    b64_wrappers = [
        ("B64[", "]"),
        ("BASE64(", ")"),
        ("<B64>", "</B64>"),
        ("ENC{", "}"),
        ("[UTF8-B64]", "[/UTF8-B64]"),
    ]

    for prefix, suffix in b64_wrappers:

        transformed = prefix + b64 + suffix

        def decoder(
            value,
            p=prefix,
            s=suffix
        ):
            raw = remove_wrappers(
                value,
                p,
                s
            )

            return unb64(raw).decode("utf-8")

        add(
            number,
            f"UTF-8 Base64 wrapper {prefix}",
            transformed,
            decoder
        )

        number += 1

    # ========================================================
    # 42-46: HEX + WRAPPERS
    # ========================================================

    hex_value = hex_bytes(
        text.encode("utf-8")
    )

    hex_wrappers = [
        ("HEX[", "]"),
        ("0x", ""),
        ("HEX(", ")"),
        ("<HEX>", "</HEX>"),
        ("{HEX:", "}"),
    ]

    for prefix, suffix in hex_wrappers:

        transformed = prefix + hex_value + suffix

        def decoder(
            value,
            p=prefix,
            s=suffix
        ):
            raw = remove_wrappers(
                value,
                p,
                s
            )

            return unhex_bytes(raw).decode("utf-8")

        add(
            number,
            f"UTF-8 hex wrapper {prefix}",
            transformed,
            decoder
        )

        number += 1

    # ========================================================
    # 47-51: QP + WRAPPERS
    # ========================================================

    qp_value = qp_encode_bytes(
        text.encode("utf-8")
    )

    qp_wrappers = [
        ("QP[", "]"),
        ("QP(", ")"),
        ("<QP>", "</QP>"),
        ("{QP:", "}"),
        ("=?utf-8?Q?", "?="),
    ]

    for prefix, suffix in qp_wrappers:

        transformed = prefix + qp_value + suffix

        def decoder(
            value,
            p=prefix,
            s=suffix
        ):
            raw = remove_wrappers(
                value,
                p,
                s
            )

            return qp_decode(raw).decode("utf-8")

        add(
            number,
            f"UTF-8 QP wrapper {prefix}",
            transformed,
            decoder
        )

        number += 1

    # ========================================================
    # 52-56: COMBINED TRANSFORMATIONS
    # ========================================================

    # Combined 1:
    # spaces -> underscores + UTF-8 Base64
    transformed = replace_spaces(text, "____")
    transformed_b64 = b64_bytes(
        transformed.encode("utf-8")
    )

    add(
        number,
        "Spaces + Base64",
        transformed_b64,
        lambda value:
            unb64(value).decode("utf-8").replace(
                "____",
                " "
            )
    )

    number += 1

    # Combined 2:
    # vowels -> QP + wrapper
    transformed = vowel_qp_transform(text)

    add(
        number,
        "Vowel QP + wrapper",
        "[VQ]" + transformed + "[/VQ]",
        lambda value:
            reverse_vowel_qp(
                remove_wrappers(
                    value,
                    "[VQ]",
                    "[/VQ]"
                )
            )
    )

    number += 1

    # Combined 3:
    # hidden marker + spaces
    transformed = insert_hidden(
        replace_spaces(text, "___"),
        HIDDEN_MARKERS["ZWSP"],
        2
    )

    add(
        number,
        "Hidden marker + underscore spaces",
        transformed,
        lambda value:
            restore_spaces(
                remove_hidden(
                    value,
                    HIDDEN_MARKERS["ZWSP"]
                ),
                "___"
            )
    )

    number += 1

    # Combined 4:
    # MIME-like encoding + outer wrapper
    transformed = mime_split_words(
        text,
        "utf-8"
    )

    add(
        number,
        "MIME Q-word + wrapper",
        "<MIME>" + transformed + "</MIME>",
        lambda value:
            decode_mime_q_word(
                remove_wrappers(
                    value,
                    "<MIME>",
                    "</MIME>"
                )
            )
    )

    number += 1

    # Combined 5:
    # duplicate separators + wrapper
    transformed = separate_duplicates(
        text,
        "=5F"
    )

    add(
        number,
        "Duplicate separator + wrapper",
        "[DUP]" + transformed + "[/DUP]",
        lambda value:
            remove_duplicate_separator(
                remove_wrappers(
                    value,
                    "[DUP]",
                    "[/DUP]"
                ),
                "=5F"
            )
    )

    number += 1

    # ========================================================
    # 57-61: MORE COMBINATIONS
    # ========================================================

    # 57
    transformed = text
    transformed = replace_spaces(
        transformed,
        "__"
    )
    transformed = insert_hidden(
        transformed,
        HIDDEN_MARKERS["ZWSP"],
        3
    )

    add(
        number,
        "Underscore + hidden",
        transformed,
        lambda value:
            restore_spaces(
                remove_hidden(
                    value,
                    HIDDEN_MARKERS["ZWSP"]
                ),
                "__"
            )
    )

    number += 1

    # 58
    transformed = vowel_qp_transform(text)
    transformed = add_wrappers(
        transformed,
        "<<<",
        ">>>"
    )

    add(
        number,
        "Vowel QP + triple wrapper",
        transformed,
        lambda value:
            reverse_vowel_qp(
                remove_wrappers(
                    value,
                    "<<<",
                    ">>>"
                )
            )
    )

    number += 1

    # 59
    transformed = separate_duplicates(
        text,
        "~"
    )
    transformed = replace_spaces(
        transformed,
        "____"
    )

    add(
        number,
        "Duplicate separator + long spaces",
        transformed,
        lambda value:
            restore_spaces(
                remove_duplicate_separator(
                    value,
                    "~"
                ),
                "____"
            )
    )

    number += 1

    # 60
    transformed = qp_encode_bytes(
        text.encode("utf-8")
    )

    transformed = add_wrappers(
        transformed,
        "<UTF8-QP>",
        "</UTF8-QP>"
    )

    add(
        number,
        "UTF-8 QP + XML-style wrapper",
        transformed,
        lambda value:
            qp_decode(
                remove_wrappers(
                    value,
                    "<UTF8-QP>",
                    "</UTF8-QP>"
                )
            ).decode("utf-8")
    )

    return variations


# ============================================================
# GENERIC DECODER
# ============================================================

def decoder_from_variations(
    variations: List[Variation]
) -> Dict[int, Callable[[str], str]]:

    return {
        variation.number: variation.decoder
        for variation in variations
    }


def decode_variation(
    encoded: str,
    variations: List[Variation]
) -> str:
    """
    Decode any string generated by generate_variations().

    The EV## prefix identifies the transformation.
    """

    match = re.match(
        r"^EV(\d{2}):(.*)$",
        encoded,
        flags=re.DOTALL
    )

    if not match:
        raise ValueError(
            "Invalid variation. Expected EV##: prefix."
        )

    number = int(match.group(1))
    payload = match.group(2)

    decoders = decoder_from_variations(
        variations
    )

    if number not in decoders:
        raise ValueError(
            f"Unknown variation number: {number}"
        )

    return decoders[number](payload)


# ============================================================
# VALIDATION
# ============================================================

def validate_variations(
    original: str,
    variations: List[Variation]
) -> Tuple[int, int]:

    success = 0
    failed = 0

    for variation in variations:
        try:
            decoded = decode_variation(
                variation.encoded,
                variations
            )

            if decoded == original:
                success += 1
            else:
                failed += 1
                print(
                    f"[FAIL] EV{variation.number:02d} "
                    f"returned different text"
                )

        except Exception as exc:
            failed += 1
            print(
                f"[FAIL] EV{variation.number:02d}: {exc}"
            )

    return success, failed


# ============================================================
# PRINTING
# ============================================================

def print_variations(
    original: str,
    variations: List[Variation]
):
    """
    Print every generated variation and its decoded result.
    """

    print("=" * 80)
    print("ORIGINAL")
    print("=" * 80)
    print(repr(original))
    print()

    print("=" * 80)
    print(f"GENERATED VARIATIONS: {len(variations)}")
    print("=" * 80)

    for variation in variations:

        print()
        print(
            f"[EV{variation.number:02d}] "
            f"{variation.name}"
        )

        print(
            "ENCODED :",
            repr(variation.encoded)
        )

        try:
            decoded = decode_variation(
                variation.encoded,
                variations
            )

            print(
                "DECODED :",
                repr(decoded)
            )

            print(
                "MATCH   :",
                decoded == original
            )

        except Exception as exc:
            print(
                "DECODE ERROR:",
                exc
            )


# ============================================================
# DEMONSTRATION
# ============================================================

def main():

    # --------------------------------------------------------
    # Sample input
    # --------------------------------------------------------

    sample = "This is a test sentence."

    # You can replace the above with Unicode examples such as:
    #
    # sample = "Hello café — 日本語 € ™"
    #
    # UTF-8 will support these characters.
    #
    # ISO-8859-1 / Windows-1252 / ISO-2022-JP may not support
    # every possible Unicode character, so those particular
    # character-set variants are skipped when unsupported.
    # UTF-8 variants continue to work.

    variations = generate_variations(
        sample
    )

    # --------------------------------------------------------
    # Ensure at least 50 variations
    # --------------------------------------------------------

    if len(variations) < 50:
        raise RuntimeError(
            f"Only {len(variations)} variations generated. "
            f"At least 50 are required."
        )

    # --------------------------------------------------------
    # Print everything
    # --------------------------------------------------------

    print_variations(
        sample,
        variations
    )

    # --------------------------------------------------------
    # Final verification
    # --------------------------------------------------------

    success, failed = validate_variations(
        sample,
        variations
    )

    print()
    print("=" * 80)
    print("FINAL VALIDATION")
    print("=" * 80)
    print(
        f"Total variations : {len(variations)}"
    )
    print(
        f"Successful       : {success}"
    )
    print(
        f"Failed           : {failed}"
    )

    if failed == 0:
        print(
            "RESULT           : ALL VARIATIONS "
            "DECODED CORRECTLY"
        )
    else:
        print(
            "RESULT           : SOME VARIATIONS FAILED"
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()
