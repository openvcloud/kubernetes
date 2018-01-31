## Getting started
- Port ays templates for deploying cloudspace and vm to 0-robot
- 0-robot template for deploying kubernetes master (using prefab)
- 0-robot template for deploying 0-robot using a docker in the kubernetes master vm
- 0-robot template for deploying kubernetes worker (via prefab)

## Cloud integration
- Implement cloud integration library that interacts with locally deployed 0-robot
- Implement templates (create persistent volume, attach volume to worker, move volume to other worker, delete persistent volume, ...)
- Authentication / authorization to itsyou.online for the kubernetes api.
see https://github.com/coreos/dex
