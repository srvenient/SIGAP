import re

CHAR_TO_NUM = {
    'O': '0', 'Q': '0', 'D': '0', 'I': '1',
    'L': '1', 'T': '1', 'Z': '2', 'S': '5',
    'G': '6', 'B': '8', 'A': '4'
}
NUM_TO_CHAR = {
    '0': 'O', '1': 'I', '2': 'Z', '5': 'S',
    '8': 'B', '6': 'G', '4': 'A'
}


def sanitize_text(text: str) -> str:
    return re.sub(r'[^A-Z0-9]', '', text.upper())


def format_colombian_plate(text: str) -> str:
    if len(text) < 6:
        return text

    # Si hay 7 caracteres y el del medio (índice 3) es ruido del escudo entre letras y números:
    if len(text) == 7 and text[4:6].isdigit():
        text = text[:3] + text[4:]

    # Si sigue teniendo más de 6 caracteres, buscar la subcadena de 6 con mayor puntaje
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

    # Las primeras 3 posiciones siempre son letras (Carros y Motos)
    letters = [NUM_TO_CHAR.get(c, c) for c in text[:3]]

    # Las posiciones 4 y 5 (índices 3 y 4) siempre son números (Carros y Motos)
    mid_numbers = [CHAR_TO_NUM.get(c, c) for c in text[3:5]]

    # La posición 6 (índice 5) puede ser número (Carro) o letra (Moto), se conserva según lectura
    last_char = text[5]

    formatted = "".join(letters) + "".join(mid_numbers) + last_char
    return f"{formatted[:3]}-{formatted[3:]}"