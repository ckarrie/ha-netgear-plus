"""Errors for the Netgear Plus integration."""

from homeassistant.exceptions import HomeAssistantError


class CannotLoginError(HomeAssistantError):
    """Unable to login to the router."""


class MaxSessionsError(HomeAssistantError):
    """Maximum number of sessions reached on the switch."""
