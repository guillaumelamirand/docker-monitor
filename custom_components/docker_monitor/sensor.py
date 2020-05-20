'''
Docker Monitor component

'''
from datetime import timedelta
import logging
import async_timeout

import homeassistant.util.dt as dt_util
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    EVENT_HOMEASSISTANT_STOP
)
from homeassistant.helpers.entity import ( 
    Entity, 
    generate_entity_id
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, 
    UpdateFailed
)

from custom_components.docker_monitor.const import (
    DOMAIN,
    DATA_DOCKER_API,
    DATA_CONFIG,
    CONF_CONTAINERS,
    CONTAINER_MONITORED_CONDITIONS,
    CONTAINER_MONITOR_CPU_PERCENTAGE,
    CONTAINER_MONITOR_IMAGE,
    CONTAINER_MONITOR_MEMORY_PERCENTAGE,
    CONTAINER_MONITOR_MEMORY_USAGE,
    CONTAINER_MONITOR_NETWORK_SPEED_DOWN,
    CONTAINER_MONITOR_NETWORK_TOTAL_DOWN,
    CONTAINER_MONITOR_NETWORK_SPEED_UP,
    CONTAINER_MONITOR_NETWORK_TOTAL_UP,
    CONTAINER_MONITOR_STATUS,
    CONTAINER_MONITOR_UPTIME,
    ROUND_PRECISION
)

VERSION = '0.0.4'
DEPENDENCIES = ['docker_monitor']

_LOGGER = logging.getLogger(__name__)

ATTR_CREATED = 'created'
ATTR_IMAGE = 'image'
ATTR_MEMORY_LIMIT = 'memory_limit'
ATTR_ONLINE_CPUS = 'online_cpus'
ATTR_STARTED_AT = 'started_at'
ATTR_VERSION_API = 'api_version'
ATTR_VERSION_ARCH = 'architecture'
ATTR_VERSION_OS = 'os'

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Docker Monitor Sensor."""

    docker_api = hass.data[DOMAIN][DATA_DOCKER_API]
    config = hass.data[DOMAIN][DATA_CONFIG]
    platform_name = config[CONF_NAME]    
    interval = config[CONF_SCAN_INTERVAL].total_seconds()
    sensors = []

    for container_name in config[CONF_CONTAINERS]:
        container = docker_api.get_container(container_name)
        if container:
            _LOGGER.debug("Initialize sensors for container '{}'".format(container_name))
            async def async_update_data():
                """Fetch data from Container API endpoint.
                """
                try:
                    async with async_timeout.timeout(10):
                        return await hass.async_add_executor_job(container.get_stats)
                except Exception as exception:
                    raise UpdateFailed(f"Error communicating with Docker API: {exception}")

            coordinator = DockerContainerDataUpdateCoordinator(
                hass,
                _LOGGER,
                container=container,
                update_interval=timedelta(seconds=interval),
            )

            # Fetch initial data so we have data when entities subscribe
            await coordinator.async_refresh()

            sensors += [DockerContainerSensor(hass, coordinator, platform_name, container_name, monitor_condition)
                         for monitor_condition in config[CONF_MONITORED_CONDITIONS] if monitor_condition in CONTAINER_MONITORED_CONDITIONS]

   
    async_add_entities(sensors)
    return True
  
class DockerContainerDataUpdateCoordinator(DataUpdateCoordinator):
    """Manages polling for state changes from the container."""

    def __init__(self,hass, logger, update_interval, container):
        """Initialize the data update coordinator."""
        DataUpdateCoordinator.__init__(
            self,
            hass,
            logger,
            name="container stats for '{}'".format(container.name),
            update_interval=update_interval,
            update_method=self.async_update_data
        )
        self._container = container
    
    async def async_update_data(self):
        """Fetch data from Container API endpoint.
        """
        try:
            async with async_timeout.timeout(10):
                return await self.hass.async_add_executor_job(self._container.get_stats)
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with Docker API: {exception}")

class DockerContainerSensor(Entity):
    """Representation of a Docker Sensor."""

    def __init__(self, hass, coordinator, platform_name, container_name, monitor_condition):
        """Initialize the sensor."""
        self._hass = hass
        self._coordinator = coordinator
        self._platform_name = platform_name
        self._container_name = container_name

        self._var_id = monitor_condition
        self._var_name = CONTAINER_MONITORED_CONDITIONS[monitor_condition][0]
        self._var_unit = CONTAINER_MONITORED_CONDITIONS[monitor_condition][1]
        self._var_icon = CONTAINER_MONITORED_CONDITIONS[monitor_condition][2]
        self._var_class = CONTAINER_MONITORED_CONDITIONS[monitor_condition][3]

        self._state = None
        _LOGGER.debug("Create sensor for container '{}' and monitor condition: {}".format(
            self._container_name, monitor_condition))

    async def async_added_to_hass(self):
        """When entity is added to hass."""

        self.async_on_remove(
            self._coordinator.async_add_listener(
                self.async_write_ha_state
            )
        )

    async def async_update(self):
        """Update the entity.

        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()   
    
    
    @property
    def state(self):
        """Return the state of the sensor."""
        # Fetch new data from coordinator
        stats = self._coordinator.data
        # Info
        if self._var_id == CONTAINER_MONITOR_STATUS:
            self._state = stats['info']['status']
        elif self._var_id == CONTAINER_MONITOR_UPTIME:
            up_time = stats.get('info', {}).get('started')
            if up_time is not None:
                self._state = dt_util.as_local(up_time).isoformat()
        elif self._var_id == CONTAINER_MONITOR_IMAGE:
            self._state = stats['info']['image'][0]  # get first from array
        # cpu
        elif self._var_id == CONTAINER_MONITOR_CPU_PERCENTAGE:
            self._state = stats.get('cpu', {}).get('total')
        # memory
        elif self._var_id == CONTAINER_MONITOR_MEMORY_USAGE:
            use = stats.get('memory', {}).get('usage')
            if use is not None:
                self._state = round(use / (1024 ** 2), ROUND_PRECISION)  # Bytes to MB
        elif self._var_id == CONTAINER_MONITOR_MEMORY_PERCENTAGE:
            self._state = stats.get('memory', {}).get('usage_percent')
        # network
        elif self._var_id == CONTAINER_MONITOR_NETWORK_SPEED_UP:
            up = stats.get('network', {}).get('speed_tx')
            if up is not None:
                self._state = round(up / (1024), ROUND_PRECISION)  # Bytes to kB
        elif self._var_id == CONTAINER_MONITOR_NETWORK_SPEED_DOWN:
            down = stats.get('network', {}).get('speed_rx')
            if down is not None:
                self._state = round(down / (1024), ROUND_PRECISION)
        elif self._var_id == CONTAINER_MONITOR_NETWORK_TOTAL_UP:
            up = stats.get('network', {}).get('total_tx') # Bytes to kB
            if up is not None:
                self._state = round(up / (1024 ** 2), ROUND_PRECISION)
        elif self._var_id == CONTAINER_MONITOR_NETWORK_TOTAL_DOWN:
            down = stats.get('network', {}).get('total_rx')
            if down is not None:
                self._state = round(down / (1024 ** 2), ROUND_PRECISION)    
        return self._state

    @property
    def state_attributes(self):
        """Return the state attributes."""
        # Fetch new data from coordinator
        stats = self._coordinator.data
        attributes = {}
        if self._var_id in (CONTAINER_MONITOR_STATUS):
            attributes[ATTR_IMAGE] = stats['info']['image'][0]
            attributes[ATTR_CREATED] = dt_util.as_local(
                stats['info']['created']).isoformat()
            attributes[ATTR_STARTED_AT] = dt_util.as_local(
                stats['info']['started']).isoformat()
        elif self._var_id in (CONTAINER_MONITOR_CPU_PERCENTAGE):
            online_cpus = stats.get('cpu', {}).get('online_cpus')
            if online_cpus is not None:
                attributes[ATTR_ONLINE_CPUS] = online_cpus
        elif self._var_id in (CONTAINER_MONITOR_MEMORY_USAGE, CONTAINER_MONITOR_MEMORY_PERCENTAGE):
            limit = stats.get('memory', {}).get('limit')
            if limit is not None:
                attributes[ATTR_MEMORY_LIMIT] = str(
                    round(limit / (1024 ** 2), ROUND_PRECISION)) + ' MB'
        return attributes

    @property
    def should_poll(self):
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self):
        """Return if entity is available."""
        return self._coordinator.last_update_success

    @property
    def name(self):
        """Return the name of the sensor, if any."""
        return "{} {} {}".format(self._platform_name, self._container_name, self._var_name)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        if self._var_id == CONTAINER_MONITOR_STATUS:
            if self._state == 'running':
                return 'mdi:checkbox-marked-circle-outline'
            else:
                return 'mdi:checkbox-blank-circle-outline'
        else:
            return self._var_icon            

    @property
    def device_class(self):
        """Return the class of this sensor."""
        return self._var_class

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        return self._var_unit

        