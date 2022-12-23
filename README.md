# here_ota_client



Here Ota Python client is a work in progress client built on top of the request Session obejct to interact with the here ota api

### Capabilities
- Launch Campaigns on Groups
- Collect Device information
- Collect Device Install History information
- Collect Device Assignment/Device Pending Install Information
- Create Static Groups
- Add and Remove Devices to a Group
- Change to Different environments in the users allowed spaces

### Work In Progress
- websocket logic to use standard library socket module to listen to websocket campaign related events
- uploading new campaigns
- Launching campaigns on single devices


### HereOtaClient instance

Create an instance of the HereOtaClient object with the username and password.

```
In [1]: from here_ota_client import HereOtaClient


In [2]: hotac = HereOtaClient(<username>, <password>)

In [3]: hotac.get_device_names_in_group("test")
2022-12-22 10:12:40,364 - here-ota-client - INFO - test
Select this group? (Y/N): y

Out[3]: ["device_name_one", "device_name_two"]
```