from requests import Session, Response
from typing import Self
from Logger import set_up_logger
from . import utils
from .api_errors import AuthenticationError, DeviceNotFoundError, InvalidEnvironmentError, GroupNotFoundError

logger = set_up_logger(name="here-ota-client")

# sign in
here_ota_url = "https://connect.ota.here.com/"
here_ota_code_endpoint = "https://account.here.com/api/account/sign-in-with-password"

here_ota_search_device_by_device_name = "https://connect.ota.here.com/api/v1/devices?nameContains="
here_ota_search_device_by_uuid = "https://connect.ota.here.com/api/v1/devices/"
here_ota_assignments = "https://connect.ota.here.com/api/v1/assignments/"

# campaigns
here_ota_campaigns = "https://connect.ota.here.com/api/v2/campaigns/"

# settings
here_ota_envs_endpoint = "https://connect.ota.here.com/user/organizations"
here_ota_default_namespace = "https://connect.ota.here.com/user/organizations/default"

# here ota software versions get
here_ota_software_versions = "https://connect.ota.here.com/api/v1/user_repo/targets.json"
here_ota_software_updates = "https://connect.ota.here.com/api/v2/updates?nameContains=&limit=10&offset=0&sortBy=createdAt"
here_ota_create_group_endpoint = "https://connect.ota.here.com/api/v1/device_groups"


# DELETE device_name FROM GROUP
# https://connect.ota.here.com/api/v1/device_groups/{group_id}/devices/{device_id} DELETE

# Add device to group
# https://connect.ota.here.com/api/v1/device_groups/{group_id}/devices/{device_id} POST

# default namespace
# https://connect.ota.here.com/user/profile
# https://connect.ota.here.com/user/organizations/default
# https://connect.ota.here.com/user/organizations


def build_env_url(name_space):
    return f"https://connect.ota.here.com/organizations/{name_space}/index"


def build_get_here_ota_campaign_data_url(name: str, limit: int = 1000):
    return f"https://connect.ota.here.com/api/v2/updates?nameContains={name}&limit={limit}&offset=0&sortBy=createdAt"


def build_here_ota_authorize_url(client_id, state) -> str:
    return f"https://account.here.com/authorize?response_type=code&client_id={client_id}&scope=openid profile email&redirect_uri=https://connect.ota.here.com/callback&state={state}&prompt="


def build_here_ota_add_device_to_group_endpoint(group_uuid: str, device_uuid: str) -> str:
    return f"https://connect.ota.here.com/api/v1/device_groups/{group_uuid}/devices/{device_uuid}"


def build_get_here_ota_groups_url(limit: int = 10, offset: int = 0) -> str:
    """
    collects id, groupName, namespace, createdAt, groupType, and expression
    :param limit: the amount of groups to be returned as an integer default 10
    :param offset: offset arg for pagination as an int default 0
    :return: url string
    """
    return f"https://connect.ota.here.com/api/v1/device_groups?limit={limit}&offset={offset}"


def build_here_ota_events_url(uuid: str) -> str:
    """
    uses the uuid to build url for the event endpoint
    :param uuid: uuid as a string
    :return: url as a string
    """
    return f"https://connect.ota.here.com/api/v1/devices/{uuid}/events?eventTypes=EcuDownloadStarted,EcuDownloadCompleted,EcuInstallationStarted,EcuInstallationCompleted"


def build_here_ota_device_history_url(uuid: str, limit: int = 10) -> str:
    """
    uses the uuid and limit to create url for installation history
    :param uuid: uuid as a string
    :param limit: integer of the amount of results to return
    :return: string
    """
    return f"https://connect.ota.here.com/api/v1/devices/{uuid}/installation_history?limit={limit}&offset=0"


def build_here_ota_device_network_endpoint(uuid: str) -> str:
    """

    :param uuid:
    :return:
    """
    return f"https://connect.ota.here.com/api/v1/devices/{uuid}/system_info/network"


def build_here_ota_last_device_update_data(uuid: str):
    """TODO"""
    return f"https://connect.ota.here.com/api/v1/admin/devices/{uuid}?includeReplaced=true"


class HereOtaClient(Session):
    """An api client built from the requests.Session object to get, update, and delete data on here ota"""
    __username = None
    __password = None
    __websocket = None
    __authentication_data = None
    __env = None
    __envs = None

    def __init__(self: Self, username: str, password: str) -> Self:
        """
        calls requests Session object init method, and API client init to add a logger
        :return: self
        """
        super().__init__()
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        }
        self.headers.update(headers)
        self.__csrf = None
        self.token = None
        self.__authentication_data = None
        self.__env = None

        # current envs for User
        self.envs = None
        self.__username = username
        self.__password = password
        self.authenticate()

    @property
    def current_env(self):
        return self.__env

    @property
    def list_envs(self):
        return self.__envs


    def authenticate(self) -> None:
        """
        Collect the X-CSRF-Token from here OTA then use it to authenticate with
        username and password. set a token for the current session
        :return: void
        """

        # get request to here ota to get the csrf token
        r1 = self.get(
            here_ota_url,
            headers={"X-CSRF-Token": "fetch"},
        )

        # request gets redirected three times. using the response.history we can see the contents
        # of each redirect to search and store the csrf token, client id, and x correlation id
        csrf_token = utils.get_here_ota_token1(r1.content.decode())
        client_id = utils.get_here_ota_client_id(r1.history[2].headers['Location'])
        x_correlation_id = r1.history[-1].headers['x-correlation-id']

        # make a post request with the csrf, client id, x correlation id in the headers
        # and a json payload containing the users credentials
        r2 = self.post(
            here_ota_code_endpoint,
            headers={
                "x-client": client_id,
                "x-correlation-id": x_correlation_id,
                "x-csrf-token": csrf_token,
                "x-oidc": "true",
                "x-realm": "here",
                "x-sdk": "true",
                "x-uri": "null"
            },
            json= \
                {
                    "realm": "here",
                    "email": self.__username,
                    "password": self.__password,
                    "rememberMe": True,
                    "isConversionSignIn": False,
                }
        )

        # collect the access token, and state from the post request
        # collect the access token, and state from the post request
        self.__authentication_data = r2.json()
        self.token = self.__authentication_data.get('accessToken', False)
        self.userId = self.__authentication_data.get("userId", False)
        if not self.token:
            raise AuthenticationError(f"Unable to authenticate: {self.__username} validate user credentials")
        self.__csrf_token = csrf_token
        state = self.cookies.get("state")

        # authorize the client and state
        authenticated = self.get(
            build_here_ota_authorize_url(client_id, state),
        )

        # set token
        logger.debug(authenticated.content.decode())
        self.__csrf_token = utils.get_here_ota_token2(authenticated.content.decode())
        self.headers["Csrf-Token"] = self.__csrf_token

        # validate result codes for previous requests
        if authenticated.status_code == 200:
            logger.info("Authenticated")
            data = r2.json()
            logger.debug(data['firstname'] + ", " + data['lastname'] + ", " + data["email"])
        else:
            logger.debug(str(authenticated.content.decode()))
            raise AuthenticationError(f"Unable to authenticate: {self.__username}")

        # save the websocket url to use to listen for ECU events such as ECUinstalltionstared, ECUDownloadStarted etc.
        self.__websocket = utils.get_here_ota_websocket_addr(authenticated.content.decode())

        # set available envs
        envs_data = self.get(here_ota_envs_endpoint).json()
        self.__envs = {i["name"]: i["namespace"] for i in envs_data}
        # set current / default env
        self.__env = self.get(here_ota_default_namespace).json()["name"]
        logger.info(f"Current env {self.__env}")
        return

    def change_env(self: Self, env: str) -> None:
        """
        changes the current session environment to the specified env
        :param env: environment to change to
        :return: void
        """

        if env not in self.__envs:  # if the env argument is not in our envs list raise an error
            raise InvalidEnvironmentError(f"{env} id not a valid env choose from: {self.__envs}")
        # perform a get to the
        name_space = self.__envs.get(env)
        env_url = build_env_url(name_space)
        r = self.get(env_url)

        # set token
        new_env_data = r.content.decode()
        self.__csrf = utils.get_here_ota_token2(new_env_data)
        self.headers["Csrf-Token"] = self.__csrf
        self.__websocket = utils.get_here_ota_websocket_addr(new_env_data)
        self.__env = env

        if r.status_code != 200:  # if we are not able to change to env successfully raise an error
            logger.debug(r.content.decode())
            raise EnvironmentError(f"Unsuccessful Response code changing to {env}")

    def get_device_info(self: Self, device_name: str, env: bool = False) -> dict:
        """
        returns details on a device from the search device by device_name endpoint
        :param device_name: device_name as a string
        :param env: if provided env will be changed before request is made
        :return: dictionary containing the device data
        """
        if env: self.change_env(env)

        # get request to devices endpoint with specified device_name
        r1 = self.get(
            here_ota_search_device_by_device_name + device_name + "&limit=24&offset=0"
        )
        return r1.json()

    def get_device_uuid(self: Self, device_name: str) -> str:
        """
        hits the device query endpoint to retrieve the device uuid
        :param device_name: device_name number as a string
        :param env: if provided will change to this env before request
        :return: string uuid for vehicle
        """
        response = self.get_device_info(device_name)['values']
        if not response:
            raise DeviceNotFoundError(f"No uuid found, device_name might not exist in environment: {self.__env}")
        else:
            return response[0]['uuid']

    def find_and_switch_to_env_for_device_name(self: Self, device_name: str) -> bool:
        """
        This method is used to locate the env for a provided device_name. returns the env of the device_name and a bool
        True of False if the device_name is found
        :param device_name: string representation of device_name
        :return: tuple or string
        """
        results = []
        for env in self.__envs:
            response = self.get_device_info(device_name, env=env)['values']
            if response:
                results.append(env)
        if len(results) > 1:
            raise EnvironmentError(f"device: {device_name} exists in multiple envs {results}")
        elif len(results) == 1:
            env = results[0]
            self.change_env(env)
            return env
        raise DeviceNotFoundError(f"device_name not found in any of: {self.__envs} by device_name")

    def get_device_history(self: Self, device_name: str, limit: int = 10) -> dict:
        """
        returns the device history for a specified device_name
        :param device_name: device_name number as a string
        :param env: if provided will change to this env before request
        :param limit: amount of campaign to return default 10
        :return: campaign data in the form of a DataFrame or an empty list if there is no data
        """
        # collect uuid

        uuid = self.get_device_uuid(device_name)

        # hit device history endpoint for uuid and amount of campaign/limit
        r1 = self.get(
            build_here_ota_device_history_url(uuid, limit)
        )
        logger.debug(f"{r1.status_code}")

        history = r1.json()
        return history

    def get_device_assignments(self: Self, device_name: str) -> list:
        """
        retrieves the current assignments or pending assignments for the specified device_name
        an empty list is returned if no pending assignments exist
        :param device_name: the device_name as a string
        :param env: if provided will change to this env before request
        :return: empty list or pandas DataFrame
        """

        # get uuid
        uuid = self.get_device_uuid(device_name)
        # hit assignments endpoint with uuid
        r1 = self.get(here_ota_assignments + uuid)
        # collect response data
        assignments = r1.json()
        return assignments

    def create_static_group(self: Self, name: str) -> dict:
        """
        This method creates a static group by name
        in the current env
        :param name: string of the name for the new group
        :return: dictionary result
        """
        r = self.post(
            here_ota_create_group_endpoint,
            json= \
                {
                    "expression": None,  # null
                    "groupType": "static",
                    "name": name
                },
        )
        logger.debug(r.content.decode())
        return r.json()

    def get_groups(self: Self, limit: int = 1000, offset=0) -> dict:
        """
        this method gets the device first 1000 groups in the current env
        :param limit: integer of how many records to return default 1000
        :return: python dictionary of results
        """
        r = self.get(build_get_here_ota_groups_url(limit=limit, offset=offset))
        if r.status_code != 200:
            raise AuthenticationError("Unable to ping endpoint")
        return r.json()

    def find_group_id_by_name(self: Self, name: str, limit: int = 1000, offset=0) -> str:
        data = self.get_groups(limit=limit, offset=offset)['values']
        for group_data in data:
            group_name = group_data["groupName"].strip()
            if name == group_name:
                logger.info(group_name)
                found = input("Select this group? (Y/N): ").lower()
                if found == "y":
                    return group_data["id"]
        raise GroupNotFoundError(f"No group containing {name} found in first {limit} groups")

    def find_here_ota_campaign_id_by_name(self: Self, name: str) -> str or None:
        r = self.get(build_get_here_ota_campaign_data_url(name))
        logger.debug(f"Response code: {r.status_code}")
        data = r.json()
        for update in data['values']:
            if name == update["name"]:
                logger.info(f'Name: {update["name"]}')
                logger.info(f'Created at: {update["createdAt"]}')
                logger.info(f'Updated at: {update["updatedAt"]}')
                logger.info(f"Description: {update['description']}")
                update_id = update["uuid"]
                correct = input("correct ? (Y/N/Q): ").lower()
                if correct == "y":
                    return update_id
                elif correct == "q":
                    return None
        raise ValueError(f"No update found with name: {name}")

    def add_device_to_group_by_uuid(self: Self, group_uuid: str, device_uuid: str) -> Response:
        r = self.post(build_here_ota_add_device_to_group_endpoint(group_uuid, device_uuid))
        return r

    def add_device_to_group(self, group: str, device_name: str) -> Response:
        group_id = self.find_group_by_name(group)
        device_id = self.get_device_uuid(device_name)
        r = self.add_device_to_group_by_uuid(group_id, device_id)
        return r

    def launch_campaign_on_group_by_name(self: Self, name: str, group_name: str, campaign_name: str) -> Response:
        group_uuid = self.find_group_by_name(group_name)
        update_id = self.find_here_ota_campaign_id_by_name(campaign_name)
        assert update_id is not None
        header = {
            "Host": "connect.ota.here.com",
            "Origin": "https://connect.ota.here.com"
        }
        self.headers.update(header)
        r = self.post(
            here_ota_campaigns[:-1], # pos needs to be done on endpoint without slash
            json= \
                {
                    "name": name,
                    "update": update_id,
                    "groups": [group_uuid],
                    "approvalNeeded": False
                }
        )
        launch_id = r.json()
        r = self.post(f"{here_ota_campaigns}{launch_id}/launch")
        logger.debug(r.content.decode())
        return r

    def get_campaign_info(self: Self, correlation_id: str):
        r1 = self.get(
            here_ota_campaigns + correlation_id
        )
        return r1

    def find_group_by_name(self: Self, name: str, limit: int = 1000, offset=0) -> str:
        data = self.get_groups(limit=limit, offset=offset)['values']
        for group_data in data:
            group_name = group_data["groupName"].strip()
            if name in group_name:
                logger.info(group_name)
                found = input("Select this group? (Y/N): ").lower()
                if found == "y":
                    return group_data["id"]
        raise GroupNotFoundError(f"No group containing {name} found in first {limit} groups")


    def get_device_names_in_group(self, group_name):
        group_id = self.find_group_by_name(group_name)
        data = self.get_devices_in_group_by_id(group_id)["values"]
        device_names = [device["deviceName"] for device in data]
        return device_names

    def get_devices_in_group_by_id(self, group_id, limit=100):
        r = self.get(f"https://connect.ota.here.com/api/v1/devices?nameContains=&limit={limit}&offset=0&groupId={group_id}")
        return r.json()

    def get_device_events(self: Self, device_name: str) -> dict:
        """TODO"""
        uuid = self.get_device_uuid(device_name)
        # r1 = self.get(
        #     build_here_ota_device_history_url(uuid)
        # )
        return self.get(build_here_ota_events_url(uuid)).json()

    def get_device_info_by_uuid(self: Self, uuid: str):
        return self.get(here_ota_search_device_by_uuid + uuid)

    def get_device_network(self: Self, device_name: str) -> dict:
        uuid = self.get_device_uuid(device_name)
        r = self.get(build_here_ota_device_network_endpoint(uuid))
        return r.json()
