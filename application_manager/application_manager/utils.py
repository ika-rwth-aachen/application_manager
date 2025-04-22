#!/usr/bin/env python3

def multiple_replace(text: str, replacement_dict: dict) -> str:
    """Replaces multiple strings in a text
    Args:
        text (str): Text where the replacements should be made
        replacement_dict (dict): Dictionary with the replacements
    Returns:
        str: Text with the replacements made
    """
    for old, new in replacement_dict.items():
        text = text.replace(old, new)
    return text
