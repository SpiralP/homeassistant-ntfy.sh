import logging
import requests
from typing import Any
import voluptuous as vol
from homeassistant.const import (
    CONF_URL,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_ICON
)

CONF_TOPIC = 'topic'

import homeassistant.helpers.config_validation as cv
from homeassistant.components.notify import (
    ATTR_TITLE_DEFAULT,
    ATTR_TITLE,
    ATTR_DATA,
    PLATFORM_SCHEMA,
    BaseNotificationService,
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_URL): cv.url,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_TOPIC): cv.string,
    vol.Optional(CONF_ICON): cv.url
})
_LOGGER = logging.getLogger(__name__)

def get_service(hass, config, discovery_info=None):
    url = config[CONF_URL]
    username = config[CONF_USERNAME]
    password = config[CONF_PASSWORD]
    topic = config[CONF_TOPIC]
    icon = config.get(CONF_ICON)

    _LOGGER.info('Service created')

    return HassAgentNotificationService(hass, url, username, password, topic, icon)


class HassAgentNotificationService(BaseNotificationService):
    def __init__(self, hass, url, username, password, topic, icon):
        self._url = url
        self._username = username
        self._password = password
        self._topic = topic
        self._icon = icon
        self._hass = hass

    def send_request(self, url, username, password, data):
        return requests.post(url, json=data, timeout=10, auth=(username, password))

    async def async_send_message(self, message: str, **kwargs: Any):
        title = kwargs.get(ATTR_TITLE, ATTR_TITLE_DEFAULT)
        data = kwargs.get(ATTR_DATA, None)
        if data is None:
            data = dict()

        # Prefer topic in automation
        topic = data.get('topic') or self._topic or "homeassistant"
        # Prefer icon in automation
        icon = data.get('icon') or self._icon or ""

        payload = {
            'topic': topic,
            'message': message,
            'title': title,
            'tags': data.get('tags', []),
            'priority': data.get('priority', 3),
            'attach': data.get('attach', "") or data.get('image', ""),
            'filename': data.get('filename', ""),
            'click': data.get('click', "") or data.get('click_url', ""),
            'actions': data.get('actions', []),
            'icon': icon,
        }

        _LOGGER.debug('Sending message to ntfy.sh: %s', payload)

        try:
            response = await self.hass.async_add_executor_job(self.send_request, self._url, self._username, self._password, payload)
            response.raise_for_status()
        except Exception as ex:
            _LOGGER.error('Error while sending ntfy.sh message: %s', ex)
