# HereOtaClient




```
In [1]: from here_ota_client import HereOtaClient


In [2]: hotac = HereOtaClient(<username>, <password>)

In [3]: hotac.get_device_names_in_group("test")
2022-12-22 10:12:40,364 - here-ota-client - INFO - test
Select this group? (Y/N): y

Out[3]: ["device_name_one", "device_name_one"]
```