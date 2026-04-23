from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple

KEYWORDS = {
    "include",
    "int",
    "bool",
    "void",
    "return",
    "for",
    "while",
    "if",
    "else",
}

BOOL_CONSTANTS = {"true", "false"}

OPERATORS = [
    "++",
    "--",
    "==",
    "!=",
    "<=",
    ">=",
    "&&",
    "||",
    "+",
    "-",
    "*",
    "/",
    "%",
    "=",
    "<",
    ">",
    "!",
    "#",
]

DELIMITERS = {
    ";",
    ",",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
    ".",
}

TOKEN_TYPE_TO_TABLE = {
    "KEYWORD": "Ключевые слова",
    "IDENTIFIER": "Идентификаторы",
    "CONSTANT_INT": "Целочисленные константы",
    "CONSTANT_FLOAT": "Вещественные константы",
    "CONSTANT_STRING": "Строковые константы",
    "CONSTANT_BOOL": "Булевы константы",
    "OPERATOR": "Операторы",
    "DELIMITER": "Разделители",
}

TABLE_ORDER = [
    "Ключевые слова",
    "Идентификаторы",
    "Целочисленные константы",
    "Вещественные константы",
    "Строковые константы",
    "Булевы константы",
    "Операторы",
    "Разделители",
]


@dataclass
class Token:
    token_type: str
    value: str
    line: int
    column: int


@dataclass
class LexicalError:
    line: int
    column: int
    message: str


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.length = len(source)
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens: List[Token] = []
        self.errors: List[LexicalError] = []

    def current_char(self) -> str | None:
        if self.position >= self.length:
            return None
        return self.source[self.position]

    def peek(self, offset: int = 1) -> str | None:
        index = self.position + offset
        if index >= self.length:
            return None
        return self.source[index]

    def advance(self, count: int = 1) -> None:
        for _ in range(count):
            if self.position >= self.length:
                return
            char = self.source[self.position]
            self.position += 1
            if char == "\n":
                self.line += 1
                self.column = 1
            else:
                self.column += 1

    def add_token(self, token_type: str, value: str, line: int, column: int) -> None:
        self.tokens.append(Token(token_type, value, line, column))

    def add_error(self, message: str, line: int, column: int) -> None:
        self.errors.append(LexicalError(line, column, message))

    def tokenize(self) -> Tuple[List[Token], List[LexicalError]]:
        while self.position < self.length:
            char = self.current_char()
            if char is None:
                break

            if char in " \t\r\n":
                self.advance()
                continue

            if char == '"':
                self.read_string()
                continue

            if char.isalpha() or char == "_":
                self.read_identifier_or_keyword()
                continue

            if char.isdigit():
                self.read_number_or_invalid_identifier()
                continue

            if self.read_operator_or_delimiter():
                continue

            self.add_error(
                f"Недопустимый символ '{char}'.",
                self.line,
                self.column,
            )
            self.advance()

        return self.tokens, self.errors

    def read_identifier_or_keyword(self) -> None:
        start_line = self.line
        start_column = self.column
        start_pos = self.position

        while True:
            char = self.current_char()
            if char is None or not (char.isalnum() or char == "_"):
                break
            self.advance()

        lexeme = self.source[start_pos:self.position]

        if lexeme in BOOL_CONSTANTS:
            self.add_token("CONSTANT_BOOL", lexeme, start_line, start_column)
        elif lexeme in KEYWORDS:
            self.add_token("KEYWORD", lexeme, start_line, start_column)
        else:
            self.add_token("IDENTIFIER", lexeme, start_line, start_column)

    def read_number_or_invalid_identifier(self) -> None:
        start_line = self.line
        start_column = self.column
        start_pos = self.position
        has_dot = False

        while True:
            char = self.current_char()
            if char is None:
                break

            if char.isdigit():
                self.advance()
                continue

            if char == ".":
                if has_dot:
                    self.advance()
                    while True:
                        extra = self.current_char()
                        if extra is None or extra in " \t\r\n" or extra in DELIMITERS or self.starts_with_any_operator():
                            break
                        self.advance()
                    bad = self.source[start_pos:self.position]
                    self.add_error(
                        f"Некорректно оформленное число '{bad}': число содержит более одной точки.",
                        start_line,
                        start_column,
                    )
                    return
                has_dot = True
                self.advance()
                continue

            if char.isalpha() or char == "_":
                while True:
                    extra = self.current_char()
                    if extra is None or not (extra.isalnum() or extra == "_" or extra == "."):
                        break
                    self.advance()
                bad = self.source[start_pos:self.position]
                self.add_error(
                    f"Идентификатор '{bad}' не может начинаться с цифры.",
                    start_line,
                    start_column,
                )
                return

            break

        lexeme = self.source[start_pos:self.position]
        token_type = "CONSTANT_FLOAT" if has_dot else "CONSTANT_INT"
        self.add_token(token_type, lexeme, start_line, start_column)

    def read_string(self) -> None:
        start_line = self.line
        start_column = self.column
        start_pos = self.position
        self.advance()  # opening quote

        escaped = False
        while True:
            char = self.current_char()
            if char is None:
                self.add_error(
                    "Незакрытый строковый литерал.",
                    start_line,
                    start_column,
                )
                return

            if char == "\n" and not escaped:
                self.add_error(
                    "Незакрытый строковый литерал.",
                    start_line,
                    start_column,
                )
                return

            if escaped:
                escaped = False
                self.advance()
                continue

            if char == "\\":
                escaped = True
                self.advance()
                continue

            if char == '"':
                self.advance()
                lexeme = self.source[start_pos:self.position]
                self.add_token("CONSTANT_STRING", lexeme, start_line, start_column)
                return

            self.advance()

    def starts_with_any_operator(self) -> bool:
        return any(self.source.startswith(op, self.position) for op in OPERATORS)

    def read_operator_or_delimiter(self) -> bool:
        start_line = self.line
        start_column = self.column

        for operator in sorted(OPERATORS, key=len, reverse=True):
            if self.source.startswith(operator, self.position):
                self.add_token("OPERATOR", operator, start_line, start_column)
                self.advance(len(operator))
                return True

        current = self.current_char()
        if current in DELIMITERS:
            self.add_token("DELIMITER", current, start_line, start_column)
            self.advance()
            return True

        return False


class LexemeTables:
    def __init__(self):
        self.tables: Dict[str, Dict[str, int]] = {name: {} for name in TABLE_ORDER}

    def add_token(self, token: Token) -> int | None:
        table_name = TOKEN_TYPE_TO_TABLE.get(token.token_type)
        if table_name is None:
            return None
        table = self.tables[table_name]
        if token.value not in table:
            table[token.value] = len(table) + 1
        return table[token.value]

    def build(self, tokens: List[Token]) -> None:
        for token in tokens:
            self.add_token(token)

    def get_id(self, token: Token) -> int | None:
        table_name = TOKEN_TYPE_TO_TABLE.get(token.token_type)
        if table_name is None:
            return None
        return self.tables[table_name].get(token.value)


def read_source(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise ValueError("Ошибка: не удалось прочитать файл в кодировке UTF-8.")


def render_lexeme_tables(lexeme_tables: LexemeTables) -> str:
    lines: List[str] = ["ТАБЛИЦЫ ЛЕКСЕМ"]
    for table_name in TABLE_ORDER:
        table = lexeme_tables.tables[table_name]
        lines.append("")
        lines.append(table_name)
        lines.append("id | Лексема")
        lines.append("---+------------------------------")
        if not table:
            lines.append("-  | (нет лексем)")
            continue
        for lexeme, lexeme_id in table.items():
            lines.append(f"{lexeme_id:<2} | {lexeme}")
    return "\n".join(lines)


def render_token_sequence(tokens: List[Token], lexeme_tables: LexemeTables) -> str:
    lines: List[str] = ["ПОСЛЕДОВАТЕЛЬНОСТЬ ТОКЕНОВ", "Лексема | Тип | id в таблице | Строка | Позиция", "--------+-----+--------------+--------+--------"]
    for token in tokens:
        token_id = lexeme_tables.get_id(token)
        lines.append(
            f"{token.value} | {token.token_type} | {token_id if token_id is not None else '-'} | {token.line} | {token.column}"
        )
    return "\n".join(lines)


def render_pair_sequence(tokens: List[Token]) -> str:
    pairs = ", ".join(f"({token.token_type}, {token.value!r})" for token in tokens)
    return f"[{pairs}]"


def analyze_file(path: Path) -> Tuple[List[Token], List[LexicalError], LexemeTables]:
    source = read_source(path)
    lexer = Lexer(source)
    tokens, errors = lexer.tokenize()
    lexeme_tables = LexemeTables()
    if not errors:
        lexeme_tables.build(tokens)
    return tokens, errors, lexeme_tables


def write_report_files(output_dir: Path, tokens: List[Token], lexeme_tables: LexemeTables) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "lexeme_tables.txt").write_text(render_lexeme_tables(lexeme_tables), encoding="utf-8")
    (output_dir / "token_sequence.txt").write_text(render_token_sequence(tokens, lexeme_tables), encoding="utf-8")
    (output_dir / "token_pairs.txt").write_text(render_pair_sequence(tokens), encoding="utf-8")


def main() -> None:
    if len(sys.argv) not in {2, 3}:
        print("Использование: python lexer.py <входной_файл> [каталог_для_отчёта]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) == 3 else None

    if not input_path.exists():
        print(f"Ошибка: файл {input_path} не найден.")
        sys.exit(1)

    try:
        tokens, errors, lexeme_tables = analyze_file(input_path)
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)

    print(f"Файл: {input_path}")

    if errors:
        print("Лексический анализ завершён с ошибками.")
        for error in errors:
            print(f"Ошибка: {error.message} Строка {error.line}, позиция {error.column}.")
        sys.exit(1)

    print(render_lexeme_tables(lexeme_tables))
    print()
    print(render_token_sequence(tokens, lexeme_tables))
    print()
    print(render_pair_sequence(tokens))
    print()
    print(f"Лексический анализ завершён успешно. Обнаружено {len(tokens)} токенов. Ошибок не найдено.")

    if output_dir is not None:
        write_report_files(output_dir, tokens, lexeme_tables)
        print(f"Файлы для отчёта сохранены в каталог: {output_dir}")


if __name__ == "__main__":
    main()
