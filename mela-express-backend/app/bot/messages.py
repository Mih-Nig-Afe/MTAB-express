"""
All bot message template strings.
English only for now — structured for future i18n (Amharic, Afaan Oromo, Somali).
"""
# TODO: populate message templates (Task 18.1)

WELCOME = (
    "Welcome to Mela Express. Share your phone number to link your account "
    "and start receiving parcel updates here."
)
LINKED = (
    "You're linked. You'll get a message here every time one of your parcels changes status. "
    "Use /track <code> anytime to check a specific parcel."
)
TRACK_USAGE = "Usage: /track MEX-HW-000482"
PARCEL_NOT_FOUND = "No parcel found with code {code}."
