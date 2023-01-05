from homeassistant.exceptions import HomeAssistantError


class CannotLoginException(HomeAssistantError):
    """Unable to login to the router."""
