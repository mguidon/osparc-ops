import logging
from contextlib import contextmanager
from typing import Dict, List

import docker

from .subtask import SubTask

log = logging.getLogger(__name__)


@contextmanager
def docker_client(registries: List[Dict]) -> docker.client:
    log.debug("creating docker client..")
    client = docker.from_env()
    log.debug("docker client ping returns: %s", client.ping())
    for registry in registries:
        log.debug("logging in %s..", registry["url"])
        client.login(registry=registry["url"],
                     username=registry["username"],
                     password=registry["password"])
        log.debug("login done")

    try:
        yield client
    finally:
        pass


class DockerRegistriesWatcher(SubTask):
    def __init__(self, app_config: Dict, stack_cfg: Dict):
        super().__init__(name="dockerhub repo watcher")
        # get all the private registries
        self.private_registries = app_config["main"]["docker_private_registries"]
        # get all the images to check for
        self.watched_repos = []
        if "services" in stack_cfg:
            for service_name in stack_cfg["services"].keys():
                if "image" in stack_cfg["services"][service_name]:
                    image_url = stack_cfg["services"][service_name]["image"]
                    self.watched_repos.append({
                        "image": image_url
                        })

    async def init(self):
        log.debug("initialising docker watcher..")
        with docker_client(self.private_registries) as client:
            for repo in self.watched_repos:
                try:
                    registry_data = client.images.get_registry_data(repo["image"])
                    log.debug("accessed to image %s: %s", repo["image"], registry_data.attrs)
                    repo["registry_data_attrs"] = registry_data.attrs
                except docker.errors.APIError:
                    # in case a new service that is not yet in the registry was added
                    log.warning("could not find image %s, maybe a new image was added to the stack??", repo["image"])
                    repo["registry_data_attrs"] = ""
        log.debug("docker watcher initialised")

    async def check_for_changes(self):
        with docker_client(self.private_registries) as client:
            for repo in self.watched_repos:
                try:
                    registry_data = client.images.get_registry_data(repo["image"])
                    if repo["registry_data_attrs"] != registry_data.attrs:
                        log.info("docker image %s signature changed!", repo["image"])
                        return True
                except docker.errors.APIError:
                    if repo["registry_data_attrs"]:
                        # in that case something is wrong...either docker or config
                        log.exception("Error while retrieving image %s in registry", repo["image"])
                        # raise
                    else:
                        # in that case the registry does not contain yet the new service
                        log.warning("the image %s is still not available in the registry", repo["image"])
                
        return False

    async def cleanup(self):
        pass


__all__ = (
    'DockerRegistriesWatcher'
)
