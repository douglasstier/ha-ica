"""Polls all ICA shopping lists."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import IcaApi, IcaApiError, IcaAuthError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)


class IcaCoordinator(DataUpdateCoordinator[dict[str, dict]]):
    """Data is {list_id: list_json}."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, api: IcaApi) -> None:
        super().__init__(hass, _LOGGER, config_entry=entry, name=DOMAIN, update_interval=SCAN_INTERVAL)
        self.api = api

    async def _async_update_data(self) -> dict[str, dict]:
        try:
            lists = await self.api.get_lists()
        except IcaAuthError as err:
            raise ConfigEntryAuthFailed("ICA session expired") from err
        except IcaApiError as err:
            raise UpdateFailed(str(err)) from err
        return {lst["id"]: lst for lst in lists}
