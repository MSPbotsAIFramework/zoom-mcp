from .._json import error_envelope

NO_TOKEN = error_envelope(
    "not_configured",
    "No Zoom credentials. Send the X-Zoom-Account-Id, X-Zoom-Client-Id, and "
    "X-Zoom-Client-Secret headers.",
    False,
)
