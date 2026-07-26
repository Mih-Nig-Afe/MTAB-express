WELCOME = (
    "👋 Welcome to Mela Express!\n\n"
    "I can help you track your parcels and manage your deliveries.\n"
    "To get started, please share your phone number so we can link your account."
)

LINKED = "✅ Phone number linked successfully! You can now use /my_parcels to view your shipments."

TRACK_USAGE = "Usage: /track MEX-HW-000482"

PARCEL_NOT_FOUND = "❌ No parcel found with code {code}."

STATUS_FORMAT = (
    "📦 *Tracking Code:* {code}\n"
    "📍 *Route:* {origin} ➔ {destination}\n"
    "🏷 *Status:* {status}\n"
    "💰 *Payment:* {payment_status}"
)

PAYMENT_PROMPT = "Your parcel requires payment before delivery."

PAYMENT_CONFIRMED = "✅ Payment initiated. Complete your payment using the link below."

RECEIPT_CONFIRMED = "✅ Thank you! Your delivery has been marked as received."

MY_PARCELS_HEADER = "📋 *Your Parcels:*\n"

MY_PARCELS_EMPTY = "You don't have any active parcels."

MY_PARCELS_ITEM = "📦 `{code}` - {status}"

ERROR_GENERIC = "⚠️ An error occurred while processing your request. Please try again later."
