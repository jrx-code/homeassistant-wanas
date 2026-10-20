"""Diagnostics support for the Wanas integration."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .const import CONF_MAC, DOMAIN
from .coordinator import WanasCoordinator
from .model_v2 import GROUPED_REGISTERS_NO_COMPLEX

TO_REDACT = {CONF_HOST, CONF_MAC, "host"}


def _plain(value: Any) -> Any:
    """Make coordinator data JSON friendly (schedules hold dataclasses and times)."""
    if is_dataclass(value):
        return _plain(asdict(value))
    if isinstance(value, dict):
        return {str(k): _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_plain(v) for v in value]
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    return value


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: WanasCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    connection = coordinator.connection
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
        },
        "connection": {
            "connected": connection.connected,
            "port": connection.port,
            "slave": connection.slave,
            "last_error": connection.last_error,
            "reconnect_attempts": connection.reconnect_attempts,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval": str(coordinator.update_interval),
            "last_exception": repr(coordinator.last_exception)
            if coordinator.last_exception
            else None,
        },
        "read_plan": [
            {"start": start, "count": count, "registers": [r.name for r in regs]}
            for start, count, regs in GROUPED_REGISTERS_NO_COMPLEX
        ],
        "data": _plain(coordinator.data) if coordinator.data is not None else None,
    }
