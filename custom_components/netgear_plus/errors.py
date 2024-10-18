"""Errors for the Netgear Plus integration."""

from homeassistant.exceptions import HomeAssistantError


class CannotLoginError(HomeAssistantError):
    """Unable to login to the router."""
