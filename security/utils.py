from django.core.exceptions import ValidationError

def clean_spaces(value):
    return ' '.join(value.split())


def validate_and_clean_spaces(value, field_name="This field", min_length=None, max_length=None):
    cleaned = ' '.join(value.split())
    
    if not cleaned:
        raise ValidationError(f"{field_name} cannot be empty or only spaces.")
    
    if min_length and len(cleaned) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters long.")
    
    if max_length and len(cleaned) > max_length:
        raise ValidationError(f"{field_name} must be at most {max_length} characters long.")
    
    return cleaned
