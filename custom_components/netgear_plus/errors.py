"""Errors for the Netgear Plus integration."""

from homeassistant.exceptions import HomeAssistantError


class CannotLoginError(HomeAssistantError):
    """Unable to login to the router."""


class CannotResolveError(HomeAssistantError):
    """Unable to resolve the configured host name to an IP address."""
