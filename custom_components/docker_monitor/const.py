"""Constants for docker-monitor."""
from datetime import timedelta

# Base component constants
NAME = "Docker Monitor"
DOMAIN = "docker_monitor"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
REQUIREMENTS = ['docker==3.7.0', 'python-dateutil==2.7.5']

ISSUE_URL = "https://github.com/guillaumelamirand/docker-monitor/issues"

# Icons
ICON = "mdi:docker"

# Platforms
SENSOR = "sensor"
SWITCH = "switch"
#PLATFORMS = [SENSOR, SWITCH]
PLATFORMS = [SENSOR]
DATA_DOCKER_API = 'docker_api'
DATA_CONFIG = 'config'

# Configuration and options
CONF_EVENTS = 'events'
CONF_CONTAINERS = 'containers'
ROUND_PRECISION = 2

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_URL = 'unix://var/run/docker.sock'
DEFAULT_SCAN_INTERVAL = timedelta(seconds=10)

DOCKER_MONITOR_VERSION = 'docker_version'

DOCKER_MONITORED_CONDITIONS = {
    DOCKER_MONITOR_VERSION: ['Version', None, 'mdi:information-outline', None],
}

CONTAINER_MONITOR_STATUS = 'container_status'
CONTAINER_MONITOR_UPTIME = 'container_uptime'
CONTAINER_MONITOR_IMAGE = 'container_image'
CONTAINER_MONITOR_CPU_PERCENTAGE = 'container_cpu_percentage_usage'
CONTAINER_MONITOR_MEMORY_USAGE = 'container_memory_usage'
CONTAINER_MONITOR_MEMORY_PERCENTAGE = 'container_memory_percentage_usage'
CONTAINER_MONITOR_NETWORK_SPEED_UP = 'container_network_speed_up'
CONTAINER_MONITOR_NETWORK_SPEED_DOWN = 'container_network_speed_down'
CONTAINER_MONITOR_NETWORK_TOTAL_UP = 'container_network_total_up'
CONTAINER_MONITOR_NETWORK_TOTAL_DOWN = 'container_network_total_down'
CONTAINER_MONITORED_CONDITIONS = {
    DOCKER_MONITOR_VERSION: ['Docker Version', None, 'mdi:information-outline', None],
    CONTAINER_MONITOR_STATUS: ['Status', None, 'mdi:checkbox-marked-circle-outline', None],
    CONTAINER_MONITOR_UPTIME: ['Up Time', '', 'mdi:clock', 'timestamp'],
    CONTAINER_MONITOR_IMAGE: ['Image', None, 'mdi:information-outline', None],
    CONTAINER_MONITOR_CPU_PERCENTAGE: ['CPU use', '%', 'mdi:chip', None],
    CONTAINER_MONITOR_MEMORY_USAGE: ['Memory use', 'MB', 'mdi:memory', None],
    CONTAINER_MONITOR_MEMORY_PERCENTAGE: ['Memory use (percent)', '%', 'mdi:memory', None],
    CONTAINER_MONITOR_NETWORK_SPEED_UP: ['Network speed Up', 'kB/s', 'mdi:upload', None],
    CONTAINER_MONITOR_NETWORK_SPEED_DOWN: ['Network speed Down', 'kB/s', 'mdi:download', None],
    CONTAINER_MONITOR_NETWORK_TOTAL_UP: ['Network total Up', 'MB', 'mdi:upload', None],
    CONTAINER_MONITOR_NETWORK_TOTAL_DOWN: ['Network total Down', 'MB', 'mdi:download', None],
}

DEFAULT_MONITORED_CONDITIONS = \
    list(DOCKER_MONITORED_CONDITIONS.keys()) + \
    list(CONTAINER_MONITORED_CONDITIONS.keys())

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""