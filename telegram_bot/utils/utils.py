from ..models.form_flow import Text

def str_to_Text(data) -> Text:
    """Convert a dictionary of translations to a Text object.
    
    Args:
        data: Dictionary with language codes as keys and translated strings as values
            e.g. {"he": "טקסט", "en": "text"}
            
    Returns:
        Text object containing the translations
    """
    return Text(data["he"], data["en"])