[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]](hacs)
![Project Maintenance][maintenance-shield]

# Docker Monitor

The Docker monitor allows you to monitor statistics and turn on/off containers. The monitor can connected to a daemon through the url parameter. When home assistant is used within a Docker container, the daemon can be mounted as follows `-v /var/run/docker.sock:/var/run/docker.sock`. The monitor is based on [Glances](https://github.com/nicolargo/glances) and [ha-dockermon](https://github.com/philhawthorne/ha-dockermon) and combines (in my opinion the best of both integrated in HA :)).

Configuration information can be found in the [documentation](https://github.com/guillaumelamirand/docker-monitor).

**This component will set up the following platforms.**

Platform | Description
-- | --
`sensor` | Sensor by container for each monitor condition
`switch` | Switch by container to start/stop them