"""
This file will contain the model and score for different token types
"""

from enum import Enum


class TokenType(Enum):
    CONTENT = "content"
    HEADING = "heading"
    TITLE = "title"


TOKEN_TYPE_WEIGHTS = {
    TokenType.CONTENT: 1,
    TokenType.HEADING: 4,
    TokenType.TITLE: 8,
}
