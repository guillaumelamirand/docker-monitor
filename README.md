# Custom components for Home Assistant

[![maintainer](https://img.shields.io/badge/maintainer-Sander%20Huisman%20-blue.svg?style=for-the-badge)](https://github.com/Sanderhuisman)

## About

This repository contains custom components I developed for my own [Home-Assistant](https://www.home-assistant.io) setup. Feel free to use the components and report bugs if you find them. If you want to contribute, please report a bug or pull request and I will reply as soon as possible. Please star & watch my project such I can see how many people like my components and for you to stay in the loop as updates come along.

### Docker Monitor

The Docker monitor allows you to monitor statistics and turn on/off containers. The monitor can connected to a daemon through the url parameter. When home assistant is used within a Docker container, the daemon can be mounted as follows `-v /var/run/docker.sock:/var/run/docker.sock`. The monitor is based on [Glances](https://github.com/nicolargo/glances) and [ha-dockermon](https://github.com/philhawthorne/ha-dockermon) and combines (in my opinion the best of both integrated in HA :)).

**Important note: as the loading path of platforms have been changed in issue [#20807](https://github.com/home-assistant/home-assistant/pull/20807), the current version requires HA versions 0.88 and above. For older versions, use version [0.0.1](https://github.com/Sanderhuisman/home-assistant-custom-components/releases/tag/0.0.1).**

#### Events

The monitor can listen for events on the Docker event bus and can fire an event on the Home Assistant Bus. The monitor will use the following event:

* `{name}_container_event` with name the same set in the configuration.

The event will contain the following data:

* `Container`: Container name
* `Image`: Container image
* `Status`: Container satus
* `Id`: Container ID (long)

#### Installation with HACS
[HACS](https://github.com/custom-components/hacs) is a custom integration that allows you to search for, discover, install, and manage custom additions to Home Assistant.

1. In the HACS store select the **Settings** tab.
2. Enter `guillaumelamirand/docker-monitor` in the **Add Custom Repository** box and select **Integration** from the **Category** list.
3. On the **Integrations** tab search for "Docker Monitor" and follow the links to install.

#### Configuration

To use the `docker_monitor` in your installation, add the following to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
docker_monitor:
  containers:
    - homeassistant_homeassistant_1
    - homeassistant_mariadb_1
    - homeassistant_mosquitto_1
  monitored_conditions:
    - utilization_version
    - container_status
    - container_memory_usage
    - container_memory_percentage_usage
    - container_cpu_percentage_usage
```

##### Configuration variables

| Parameter            | Type                     | Description                                                           |
| -------------------- | ------------------------ | --------------------------------------------------------------------- |
| name                 | string       (Optional)  | Client name of Docker daemon. Defaults to `Docker`.                   |
| url                  | string       (Optional)  | Host URL of Docker daemon. Defaults to `unix://var/run/docker.sock`.  |
| scan_interval        | time_period  (Optional)  | Update interval. Defaults to 10 seconds.                              |
| events               | boolean      (Optional)  | Listen for events from Docker. Defaults to false.                     |
| containers           | list         (Optional)  | Array of containers to monitor. Defaults to all containers.           |
| monitored_conditions | list         (Optional)  | Array of conditions to be monitored. Defaults to all conditions       |

| Condition                         | Description                     | Unit  |
| --------------------------------- | ------------------------------- | ----- |
| utilization_version               | Docker version                  | -     |
| container_status                  | Container status                | -     |
| container_uptime                  | Container start time            | -     |
| container_image                   | Container image                 | -     |
| container_cpu_percentage_usage    | CPU usage                       | %     |
| container_memory_usage            | Memory usage                    | MB    |
| container_memory_percentage_usage | Memory usage                    | %     |
| container_network_speed_up        | Network total speed upstream    | kB/s  |
| container_network_speed_down      | Network total speed downstream  | kB/s  |
| container_network_total_up        | Network total upstream          | MB    |
| container_network_total_down      | Network total downstream        | MB    |

## Credits

* [Sanderhuisman](https://https://github.com/Sanderhuisman/home-assistant-custom-components)
* [brianhanifin](https://https://github.com/brianhanifin/docker-monitor)
* [frenck](https://github.com/frenck/home-assistant-config)
* [robmarkcole](https://github.com/robmarkcole/Hue-sensors-HASS)
