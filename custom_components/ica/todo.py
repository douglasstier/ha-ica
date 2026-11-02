"""One to-do entity per ICA shopping list."""
from __future__ import annotations

from homeassistant.components.todo import (
    TodoItem,
    TodoItemStatus,
    TodoListEntity,
    TodoListEntityFeature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IcaConfigEntry
from .api import IcaApiError, IcaAuthError
from .const import DOMAIN
from .coordinator import IcaCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: IcaConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    known: set[str] = set()

    @callback
    def _add_new() -> None:
        new = [lid for lid in coordinator.data if lid not in known]
        known.update(new)
        if new:
            async_add_entities(IcaTodoList(coordinator, lid) for lid in new)

    _add_new()
    entry.async_on_unload(coordinator.async_add_listener(_add_new))


class IcaTodoList(CoordinatorEntity[IcaCoordinator], TodoListEntity):
    _attr_has_entity_name = True
    _attr_supported_features = (
        TodoListEntityFeature.CREATE_TODO_ITEM
        | TodoListEntityFeature.UPDATE_TODO_ITEM
        | TodoListEntityFeature.DELETE_TODO_ITEM
    )

    def __init__(self, coordinator: IcaCoordinator, list_id: str) -> None:
        super().__init__(coordinator)
        self._list_id = list_id
        self._attr_unique_id = list_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.unique_id or "ica")},
            name="ICA",
            manufacturer="ICA",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def _list(self) -> dict | None:
        return self.coordinator.data.get(self._list_id)

    @property
    def available(self) -> bool:
        return super().available and self._list is not None

    @property
    def name(self) -> str:
        return (self._list or {}).get("name") or "Shopping list"

    def _rows(self) -> dict[str, dict]:
        return {r["id"]: r for r in (self._list or {}).get("rows", [])}

    @property
    def todo_items(self) -> list[TodoItem] | None:
        if self._list is None:
            return None
        return [
            TodoItem(
                uid=r["id"],
                summary=r.get("text") or "",
                status=TodoItemStatus.COMPLETED if r.get("isStriked") else TodoItemStatus.NEEDS_ACTION,
            )
            for r in self._list.get("rows", [])
        ]

    async def _call(self, coro) -> None:
        try:
            await coro
        except IcaAuthError as err:
            self.coordinator.config_entry.async_start_reauth(self.hass)
            raise HomeAssistantError("ICA session expired, re-authenticate the integration") from err
        except IcaApiError as err:
            raise HomeAssistantError(f"ICA request failed: {err}") from err
        finally:
            await self.coordinator.async_refresh()

    async def async_create_todo_item(self, item: TodoItem) -> None:
        await self._call(self.coordinator.api.add_row(self._list_id, item.summary or ""))

    async def async_update_todo_item(self, item: TodoItem) -> None:
        row = self._rows().get(item.uid)
        if row is None:
            raise HomeAssistantError(f"Item {item.uid} not found in ICA list")
        await self._call(
            self.coordinator.api.update_row(
                row,
                text=item.summary if item.summary is not None else row.get("text"),
                isStriked=item.status == TodoItemStatus.COMPLETED,
            )
        )

    async def async_delete_todo_items(self, uids: list[str]) -> None:
        async def _delete_all() -> None:
            for uid in uids:
                await self.coordinator.api.delete_row(uid)

        await self._call(_delete_all())
