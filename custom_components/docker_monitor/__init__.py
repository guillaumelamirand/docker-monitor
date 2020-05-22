'''
Docker Monitor component
'''
import logging
import threading
import time
from datetime import timedelta
from dateutil import parser

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    EVENT_HOMEASSISTANT_STOP
)
from homeassistant.core import Config, HomeAssistant
from homeassistant.helpers.discovery import load_platform
from homeassistant.util import slugify as util_slugify

from custom_components.docker_monitor.const import (
    DOMAIN,
    PLATFORMS,
    DATA_DOCKER_API,
    DATA_CONFIG,
    STARTUP_MESSAGE,
    DEFAULT_NAME,
    DEFAULT_URL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_MONITORED_CONDITIONS,
    CONF_CONTAINERS
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_NAME, default=DEFAULT_NAME):
            cv.string,
        vol.Optional(CONF_URL, default=DEFAULT_URL):
            cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL):
            cv.time_period,
        vol.Optional(CONF_MONITORED_CONDITIONS, default=DEFAULT_MONITORED_CONDITIONS):
            vol.All(cv.ensure_list, [vol.In(DEFAULT_MONITORED_CONDITIONS)]),
        vol.Optional(CONF_CONTAINERS):
            cv.ensure_list,
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: Config):
    """Setup plateform."""
    
    _LOGGER.info(STARTUP_MESSAGE)        
    _LOGGER.debug("Configuration: {}".format(config[DOMAIN]))

    host = config[DOMAIN].get(CONF_URL)

    try:
        docker_api = DockerAPI(hass, host)
        await hass.async_add_executor_job(docker_api.load_containers)
    except (ImportError, ConnectionError) as e:
        _LOGGER.error("Error setting up Docker API ({})".format(e))
        return False
    else:
        hass.data[DOMAIN] = {}
        hass.data[DOMAIN][DATA_DOCKER_API] = docker_api
        hass.data[DOMAIN][DATA_CONFIG] = {
            CONF_NAME: config[DOMAIN][CONF_NAME],
            CONF_CONTAINERS: config[DOMAIN].get(CONF_CONTAINERS, [container.name for container in docker_api.get_containers()]),
            CONF_MONITORED_CONDITIONS: config[DOMAIN].get(CONF_MONITORED_CONDITIONS),
            CONF_SCAN_INTERVAL: config[DOMAIN].get(CONF_SCAN_INTERVAL)
        }

        for component in PLATFORMS:
            load_platform(hass, component, DOMAIN, {}, config)

        return True


"""
Docker API abstraction
"""
class DockerAPI:
    def __init__(self, hass, base_url):
        self._hass = hass
        self._base_url = base_url
        self._containers = {}
        try:
            import docker
        except ImportError as e:
            _LOGGER.error("Missing Docker library ({})".format(e))
            raise ImportError()

        try:
            self._client = docker.DockerClient(base_url=self._base_url)
        except Exception as e:
            _LOGGER.error("Can not connect to Docker ({})".format(e))
            raise ConnectionError()

    def load_containers(self):
        for container in self._client.containers.list(all=True) or []:
            _LOGGER.debug("Found container: {}".format(container.name))
            self._containers[container.name] = DockerContainerAPI(self._hass, self._client, container.name)

    def get_info(self):
        info = {}
        try:
            raw = self._client.version()
            info = {
                'version': raw.get('Version', None),
                'api_version': raw.get('ApiVersion', None),
                'os': raw.get('Os', None),
                'arch': raw.get('Arch', None),
                'kernel_version': raw.get('KernelVersion', None),
            }
        except Exception as e:
            _LOGGER.error("Cannot get Docker version ({})".format(e))

        return info

    def get_containers(self):
        return list(self._containers.values())

    def get_container(self, name):
        container = None
        if name in self._containers:
            container = self._containers[name]
        return container


class DockerContainerAPI:
    def __init__(self, hass, client, name):
        self._hass = hass
        self._name = name
        self._client = client
        self._container = self._client.containers.get(self._name)
        self._previous_network = None

    @property
    def name(self):
        return self._name

    def get_stats(self):
        
        _LOGGER.debug("Get stats for container {}".format(self._name))
        
        stats = {}
        self._reload_container()
        raw = self._container.stats(stream=False)

        stats['info'] = self._get_info()

        if stats['info']['status'] in ('running', 'paused'):
            _LOGGER.debug("Container {} is running".format(self._name))
            stats['read'] = parser.parse(raw['read'])
            stats['cpu'] = self._get_cpu_stats(raw)
            stats['memory'] = self._get_memory_stats(raw)
            stats['network'] = self._get_network_stats(raw, stats['read'])
        else:
            _LOGGER.debug("Container {} is not running".format(self._name))
            stats['cpu'] = {}
            stats['memory'] = {}
            stats['network'] = {}
            
        _LOGGER.debug("Stats for container {} ({}): {}".format(self._name, self._container.id, stats))
        return stats

    def _reload_container(self):
        try:
            self._container.reload()
        except Exception as e:
            self._container = self._client.containers.get(self._name)
            self._container.reload()
            self._previous_network = None

    def _get_info(self):
        _LOGGER.debug("Loading info for container {}".format(self._name))
        info = {
            'id': self._container.id,
            'image': self._container.image.tags,
            'status': self._container.attrs['State']['Status'],
            'created': parser.parse(self._container.attrs['Created']),
            'started_at': parser.parse(self._container.attrs['State']['StartedAt']),
            'finished_at': parser.parse(self._container.attrs['State']['FinishedAt']),
            'exit_code': self._container.attrs['State']['ExitCode'],
        }
        return info    

    def _get_cpu_stats(self, raw):
        _LOGGER.debug("Loading cpu stats for container {}".format(self._name))
        cpu_stats = {}
        try:
            # Compatibility wih older Docker API
            if 'online_cpus' in raw['cpu_stats']:
                cpu_count = raw['cpu_stats']['online_cpus']
            else:
                cpu_count = len(
                    raw['cpu_stats']['cpu_usage']['percpu_usage'] or [])

            cpu_percent = 0.0
            cpu_delta = float(raw["cpu_stats"]["cpu_usage"]["total_usage"]) - float(raw["precpu_stats"]["cpu_usage"]["total_usage"])
            system_delta = float(raw["cpu_stats"]["system_cpu_usage"]) - float(raw["precpu_stats"]["system_cpu_usage"])
            if system_delta > 0.0:
                cpu_percent = cpu_delta / system_delta * 100.0 * cpu_count
            cpu_stats['total'] = round(cpu_percent, 2)
            cpu_stats['online_cpus'] = cpu_count

        except KeyError as e:
            # raw do not have CPU information
            _LOGGER.debug("Cannot grab CPU usage for container {} ({})".format(
                self._container.id, e))
            _LOGGER.debug(raw) 
        return cpu_stats
    
    def _get_memory_stats(self, raw):
        _LOGGER.debug("Loading memory stats for container {}".format(self._name))
        memory_stats = {}
        try:
            memory_stats['usage'] = raw['memory_stats']['usage']
            memory_stats['limit'] = raw['memory_stats']['limit']
            memory_stats['max_usage'] = raw['memory_stats']['max_usage']
        except (KeyError, TypeError) as e:
            # raw_stats do not have MEM information
            _LOGGER.debug("Cannot grab MEM usage for container {} ({})".format(
                self._container.id, e))
            _LOGGER.debug(raw)
        else:
            memory_stats['usage_percent'] = round(
                float(memory_stats['usage']) / float(memory_stats['limit']) * 100.0, 2)
        return memory_stats

    def _get_network_stats(self, raw, read_at):
        _LOGGER.debug("Loading network stats for container {}".format(self._name))
        network_stats = {}
        network_stats['total_tx'] = 0
        network_stats['total_rx'] = 0
        network_stats['speed_tx'] = 0
        network_stats['speed_rx'] = 0
        try:
            for if_name, data in raw["networks"].items():
                network_stats['total_tx'] += data["tx_bytes"]
                network_stats['total_rx'] += data["rx_bytes"]

            network_new = {
                'read': read_at,
                'total_tx': network_stats['total_tx'],
                'total_rx': network_stats['total_rx'],
            }
        except KeyError as e:
            # raw_stats do not have NETWORK information
            _LOGGER.debug("Cannot grab NET usage for container {} ({})".format(
                self._container.id, e))
            _LOGGER.debug(raw)
        else:
            if self._previous_network:
                tx = network_new['total_tx'] - self._previous_network['total_tx']
                rx = network_new['total_rx'] - self._previous_network['total_rx']
                tim = (network_new['read'] - self._previous_network['read']).total_seconds()

                if tim > 0:
                    network_stats['speed_tx'] = round(float(tx) / tim, 2)
                    network_stats['speed_rx'] = round(float(rx) / tim, 2)

            self._previous_network = network_new
        return network_stats
