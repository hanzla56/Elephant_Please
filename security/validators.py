from django.utils import timezone

def validate_start_date_not_in_past(start_date):
    if start_date < timezone.now().date():
        raise ValidationError("Start date cannot be in the past.")
    return start_date


def validate_end_after_start(start_date, end_date):
    if end_date < start_date:
        raise ValidationError("End date must be after start date.")
    return end_date
