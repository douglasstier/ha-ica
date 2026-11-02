# ICA Shopping Lists for Home Assistant

Custom integration that turns every shopping list in your [ICA](https://www.ica.se/inkopslista/) account into a native
Home Assistant **to-do list** (`todo.ica_<list name>`).

- Add, check off, rename and delete items from the HA To-do dashboard, Assist or automations, and they show up in the ICA app.
- Changes made in the ICA app show up in HA within 3 minutes. New lists appear automatically.
- When the ICA login expires, HA raises a repair, *"ICA session expired"*, where you paste a new cookie.

> Unofficial. Uses the same (undocumented) API as the shopping list on ica.se, so it can break if ICA changes it.

## Installation

**HACS:** add this repository as a custom repository (category *Integration*) and install *ICA Shopping Lists*.

**Manual:** copy `custom_components/ica` into your HA `config/custom_components/` folder.

Restart Home Assistant, then go to *Settings → Devices & services → Add integration → ICA Shopping Lists*.

## Logging in

The integration authenticates with the `thSessionId` cookie from ica.se:

1. Log in on **www.ica.se** in a desktop browser.
2. Open developer tools (**F12**) → **Application** (Firefox: **Storage**) → **Cookies** → `https://www.ica.se`.
3. Copy the value of **`thSessionId`** and paste it into the integration.

Logging out on ica.se invalidates the cookie. Just log in again and paste the new one when the repair appears.

## Sync with Google Keep or another list

Want the ICA list in sync with Google Keep, Todoist or another to-do list? Use
[Todo Sync](https://github.com/douglasstier/ha-todo-sync). It syncs open items both ways between any two Home Assistant
to-do lists, without copying old checked-off history or creating duplicates.

## How it works

| Step | Endpoint |
|---|---|
| Cookie → bearer token (lives a few minutes, `loginState` 2 = logged in) | `GET https://www.ica.se/api/user/information` |
| All lists with rows | `GET https://apim-pub.gw.ica.se/sverige/digx/shopping-list/v1/api/list/all` |
| Add item | `POST …/api/list/{list_id}/row` `{"text": "..."}` |
| Check off / rename | `PUT …/api/row/{row_id}` (full row, `isStriked`) |
| Delete item | `DELETE …/api/row/{row_id}` |

## Credits

Thanks to [mellamomax/ica_shopping](https://github.com/mellamomax/ica_shopping), which showed how the ICA shopping list
API is authenticated. This integration is a separate implementation (native to-do entities, the new
`apim-pub.gw.ica.se` API host).

## License

MIT, see [LICENSE](LICENSE).
