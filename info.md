[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

![Project Maintenance][maintenance-shield]

[![hacs][hacs-shield]](hacs)
[![Community Forum][forum-shield]][forum]

# Docker Monitor

The Docker monitor allows you to monitor statistics about containers. The monitor can connected to a daemon through the url parameter. When home assistant is used within a Docker container, the daemon can be mounted as follows `-v /var/run/docker.sock:/var/run/docker.sock`.

## Configuration

To use the `docker_monitor` in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
docker_monitor:
  containers:
    - homeassistant_homeassistant_1
    - homeassistant_mariadb_1
    - homeassistant_mosquitto_1
  monitored_conditions:
    - docker_version
    - container_status
    - container_memory_usage
    - container_memory_percentage_usage
    - container_cpu_percentage_usage
```

## Variables

| Parameter            | Type                     | Description                                                           |
| -------------------- | ------------------------ | --------------------------------------------------------------------- |
| name                 | string       (Optional)  | Client name of Docker daemon. Defaults to `Docker`.                   |
| url                  | string       (Optional)  | Host URL of Docker daemon. Defaults to `unix://var/run/docker.sock`.  |
| scan_interval        | time_period  (Optional)  | Update interval. Defaults to 10 seconds.                              |
| containers           | list         (Optional)  | Array of containers to monitor. Defaults to all containers.           |
| monitored_conditions | list         (Optional)  | Array of conditions to be monitored. Defaults to all conditions       |

| Monitored conditions              | Description                     | Unit    |
| --------------------------------- | ------------------------------- | ------- |
| docker_version                    | Docker version                  | -       |
| container_status                  | Container status                | -       |
| container_uptime                  | Container up time               | minutes |
| container_cpu_percentage_usage    | CPU usage                       | %       |
| container_memory_usage            | Memory usage                    | MiB     |
| container_memory_percentage_usage | Memory usage                    | %       |
| container_network_speed_up        | Network total speed upstream    | kB/s    |
| container_network_speed_down      | Network total speed downstream  | kB/s    |
| container_network_total_up        | Network total upstream          | MB      |
| container_network_total_down      | Network total downstream        | MB      |
***

[docker-monitor]: https://github.com/guillaumelamirand/docker-monitor
[releases]: https://github.com/guillaumelamirand/docker-monitor/releases
[license-shield]: https://img.shields.io/github/license/guillaumelamirand/docker-monitor.svg?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/guillaumelamirand/docker-monitor.svg?style=for-the-badge
[commits]: https://github.com/guillaumelamirand/docker-monitor/commits/master
[hacs]: https://github.com/custom-components/hacs
[hacs-shield]: https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge
[forum-shield]: https://img.shields.io/badge/community-forum-brightgreen.svg?style=for-the-badge
[forum]: https://community.home-assistant.io/
[maintenance-shield]: https://img.shields.io/badge/maintainer-Guillaume%20Lamirand-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/guillaumelamirand/docker-monitor.svg?style=for-the-badge
