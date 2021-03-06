import json
import logging
from typing import Dict, List

from aiohttp import ClientSession
from yarl import URL

from .exceptions import ConfigurationError, AutoDeployAgentException

log = logging.getLogger(__name__)

async def _portainer_request(url: URL, method: str, **kwargs) -> str:
    async with ClientSession() as client:
        async with getattr(client, method.lower())(url, **kwargs) as resp:
            log.debug("request received with code %s", resp.status)
            if resp.status == 200:
                data = await resp.json()
                return data
            if resp.status == 404:
                log.error("could not find route in %s", url)
                raise ConfigurationError("Could not authenticate with Portainer app in {}:\n {}".format(url, await resp.text()))
            log.error("Unknown error")
            raise AutoDeployAgentException("Unknown error while accessing Portainer app in {}:\n {}".format(url, await resp.text()))


async def authenticate(base_url: URL, username: str, password: str) -> str:
    log.debug("authenticating with portainer %s", base_url)
    data = await _portainer_request(base_url.with_path("api/auth"), "POST", json={
        "Username": username,
        "Password": password
        })
    bearer_code = data["jwt"]
    log.debug("authenticated with portainer in %s", base_url)
    return bearer_code

async def get_swarm_id(base_url: URL, bearer_code: str) -> str:
    log.debug("getting swarm id %s", base_url)
    headers = {"Authorization": "Bearer {}".format(bearer_code)}
    url = base_url.with_path("api/endpoints/1/docker/swarm")
    data = await _portainer_request(url, "GET", headers=headers)
    log.debug("received swarm details: %s", data)
    swarm_id = data["ID"]            
    return swarm_id

async def get_stacks_list(base_url: URL, bearer_code: str) -> List[Dict]:
    log.debug("getting stacks list %s", base_url)
    headers = {"Authorization": "Bearer {}".format(bearer_code)}
    url = base_url.with_path("api/stacks")
    data = await _portainer_request(url, "GET", headers=headers)
    log.debug("received list of stacks: %s", data)
    return data

async def get_current_stack_id(base_url: URL, bearer_code: str, stack_name: str) -> str:
    log.debug("getting current stack id %s", base_url)
    stacks_list = await get_stacks_list(base_url, bearer_code)
    for stack in stacks_list:
        if stack_name == stack["Name"]:
            return stack["Id"]
    return None

async def post_new_stack(base_url: URL, bearer_code: str, swarm_id: str, stack_name: str, stack_cfg: Dict):    
    log.debug("creating new stack %s", base_url)
    headers = {"Authorization": "Bearer {}".format(bearer_code)}
    body_data = {
        "Name": stack_name,
        "SwarmID": swarm_id,
        "StackFileContent": json.dumps(stack_cfg, indent=2)
    }
    url = base_url.with_path("api/stacks").with_query({"type": 1, "method": "string", "endpointId": 1})
    data = await _portainer_request(url, "POST", headers=headers, json=body_data)
    log.debug("created new stack: %s", data)

async def get_current_stack_config(base_url: URL, bearer_code: str, stack_id: str) -> Dict:
    log.debug("getting current stack config %s", base_url)
    headers = {"Authorization": "Bearer {}".format(bearer_code)}
    url = URL(base_url).with_path("api/stacks/{}/file".format(stack_id))
    data = await _portainer_request(url, "GET", headers=headers)
    data = json.loads(data["StackFileContent"])
    log.debug("retrieved stack config: %s", data)
    return data

async def update_stack(base_url: URL, bearer_code: str, stack_id: str, stack_cfg: Dict):
    log.debug("updating stack %s", base_url)
    headers = {"Authorization": "Bearer {}".format(bearer_code)}
    body_data = {
        "StackFileContent": json.dumps(stack_cfg, indent=2),
        "Prune": False
    }
    url = URL(base_url).with_path("api/stacks/{}".format(stack_id)).with_query({"endpointId":1})
    data = await _portainer_request(url, "PUT", headers=headers, json=body_data)
    log.debug("updated stack: %s", data)
