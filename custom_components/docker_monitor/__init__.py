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
    CONF_EVENTS,
    CONF_CONTAINERS,
    ROUND_PRECISION
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
        vol.Optional(CONF_EVENTS, default=False):
            cv.boolean,
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
        version = {}
        try:
            raw_stats = self._client.version()
            version = {
                'version': raw_stats.get('Version', None),
                'api_version': raw_stats.get('ApiVersion', None),
                'os': raw_stats.get('Os', None),
                'arch': raw_stats.get('Arch', None),
                'kernel': raw_stats.get('KernelVersion', None),
            }
        except Exception as e:
            _LOGGER.error("Cannot get Docker version ({})".format(e))

        return version

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
        self._container = client.containers.get(self._name)
        self._previous_cpu = None
        self._previous_network = None

    @property
    def name(self):
        return self._name

    def get_stats(self):

        _LOGGER.debug("Get stats for container {} ({})".format(self._name, self._container.id))
        raw = self._container.stats(stream=False)
        stats = {}
        _LOGGER.debug("Loading info for container {}".format(self._name))
        stats['info'] = self._get_info()

        if stats['info']['status'] in ('running', 'paused'):
            _LOGGER.debug("Container {} is running".format(self._name))
            stats['read'] = parser.parse(raw['read'])

            _LOGGER.debug("Loading cpu stats for container {}".format(self._name))
            cpu_stats = {}
            try:
                cpu_new = {}
                cpu_new['total'] = raw['cpu_stats']['cpu_usage']['total_usage']
                cpu_new['system'] = raw['cpu_stats']['system_cpu_usage']

                # Compatibility wih older Docker API
                if 'online_cpus' in raw['cpu_stats']:
                    cpu_stats['online_cpus'] = raw['cpu_stats']['online_cpus']
                else:
                    cpu_stats['online_cpus'] = len(
                        raw['cpu_stats']['cpu_usage']['percpu_usage'] or [])
            except KeyError as e:
                # raw do not have CPU information
                _LOGGER.debug("Cannot grab CPU usage for container {} ({})".format(
                    self._container.id, e))
                _LOGGER.debug(raw)
            else:
                if self._previous_cpu:
                    cpu_delta = float(cpu_new['total'] - self._previous_cpu['total'])
                    system_delta = float(
                        cpu_new['system'] - self._previous_cpu['system'])

                    cpu_stats['total'] = round(0.0, ROUND_PRECISION)
                    if cpu_delta > 0.0 and system_delta > 0.0:
                        cpu_stats['total'] = round(
                            (cpu_delta / system_delta) * float(cpu_stats['online_cpus']) * 100.0, ROUND_PRECISION)

                self._previous_cpu = cpu_new

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
                    float(memory_stats['usage']) / float(memory_stats['limit']) * 100.0, ROUND_PRECISION)

            _LOGGER.debug("Loading network stats for container {}".format(self._name))
            network_stats = {}
            try:
                network_new = {}
                network_stats['total_tx'] = 0
                network_stats['total_rx'] = 0
                for if_name, data in raw["networks"].items():
                    network_stats['total_tx'] += data["tx_bytes"]
                    network_stats['total_rx'] += data["rx_bytes"]

                network_new = {
                    'read': stats['read'],
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
                        network_stats['speed_tx'] = round(float(tx) / tim, ROUND_PRECISION)
                        network_stats['speed_rx'] = round(float(rx) / tim, ROUND_PRECISION)

                self._previous_network = network_new

            stats['cpu'] = cpu_stats
            stats['memory'] = memory_stats
            stats['network'] = network_stats
        else:
            _LOGGER.debug("Container {} is not running".format(self._name))
            stats['cpu'] = {}
            stats['memory'] = {}
            stats['network'] = {}
            
        _LOGGER.debug("Stats for container {} ({}): {}".format(self._name, self._container.id, stats))
        return stats

    def _get_info(self):
        self._container.reload()
        info = {
            'id': self._container.id,
            'image': self._container.image.tags,
            'status': self._container.attrs['State']['Status'],
            'created': parser.parse(self._container.attrs['Created']),
            'started': parser.parse(self._container.attrs['State']['StartedAt']),
        }
        return info       