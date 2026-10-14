import re

CHAR_TO_NUM = {
    'O': '0',
    'Q': '0',
    'D': '0',
    'I': '1',
    'L': '1',
    'T': '1',
    'Z': '2',
    'S': '5',
    'G': '6',
    'B': '8',
    'A': '4'
}
NUM_TO_CHAR = {
    '0': 'O',
    '1': 'I',
    '2': 'Z',
    '5': 'S',
    '8': 'B',
    '6': 'G',
    '4': 'A'
}


def sanitize_text(text: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', text.upper())


def format_colombian_plate(text: str) -> str:
    # If the text is already less than 5 characters, return it as is
    if len(text) < 5:
        return text

    # If there are 7 characters and the middle one (index 3) is noise from the shield between letters and numbers:
    if len(text) == 7 and text[4:6].isdigit():
        text = text[:3] + text[4:]

    # If still longer than 6 characters, find the best 6-character substring that resembles a Colombian plate
    if len(text) > 6:
        best_candidate = text[:6]
        best_score = -1
        for i in range(len(text) - 5):
            cand = text[i:i + 6]
            score = (
                    sum(1 for c in cand[:3] if c.isalpha()) +
                    sum(1 for c in cand[3:5] if c.isdigit())
            )
            if score > best_score:
                best_score = score
                best_candidate = cand
        text = best_candidate

    # Now we have a candidate of 6 characters, we can apply the character-to-number and number-to-character corrections
    letters = list(text[:3])
    for i in range(len(letters)):
        if letters[i] in NUM_TO_CHAR:
            letters[i] = NUM_TO_CHAR[letters[i]]

    # Apply character-to-number corrections to the rest of the characters
    rest = list(text[3:6])
    for i in range(min(2, len(rest))):
        if rest[i] in CHAR_TO_NUM:
            rest[i] = CHAR_TO_NUM[rest[i]]

    text = ''.join(letters) + ''.join(rest)

    if len(text) >= 5:
        text = f"{text[:3]}-{text[3:]}"

    return text
