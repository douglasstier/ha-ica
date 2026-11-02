"""Constants for the ICA Shopping Lists integration."""
from datetime import timedelta

DOMAIN = "ica"
CONF_SESSION_ID = "session_id"
SCAN_INTERVAL = timedelta(minutes=3)

USER_INFO_URL = "https://www.ica.se/api/user/information"
API_BASE = "https://apim-pub.gw.ica.se/sverige/digx/shopping-list/v1/api"
