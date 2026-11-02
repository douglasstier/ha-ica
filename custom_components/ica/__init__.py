"""ICA Shopping Lists: each ICA list becomes a native to-do list."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import IcaApi
from .const import CONF_SESSION_ID
from .coordinator import IcaCoordinator

PLATFORMS = [Platform.TODO]

type IcaConfigEntry = ConfigEntry[IcaCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: IcaConfigEntry) -> bool:
    api = IcaApi(async_get_clientsession(hass), entry.data[CONF_SESSION_ID])
    coordinator = IcaCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: IcaConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
