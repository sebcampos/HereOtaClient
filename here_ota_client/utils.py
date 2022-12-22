import re
import json


def is_device_event(message) -> bool or tuple:
    """
    Pareses a websocket message searching for the DeviceEventMessage
    if it is not included in the message returns False
    :param message: string websocket response
    :return: campaign correlation id and event occurred value
    """
    # load message into python dict and check for DeviceEventMessage
    data = json.loads(message)
    data_type = data.get("type", False)
    if data_type is False or data_type != "DeviceEventMessage":
        return False
    # collect and return the correlation Id and the ECU event message
    campaign_correlation_id = data['event']['payload']['correlationId']
    event_occurred = data['event']['eventType']['id']
    return campaign_correlation_id, event_occurred


def get_here_ota_token1(string):
    return re.search(r'csrf:[\s]*[\'"](.*)?[\'"],', string).groups()[0]


def get_here_ota_token2(string):
    return re.search(r'id="csrf-token-val" value="(.*)"', string).groups()[0]


def get_here_ota_client_id(string):
    return re.search(r"client-id=(.*?)&", string).groups()[0]


def get_here_ota_websocket_addr(string):
    return re.search('id="ws-url" value="(.*)?"', string).groups()[0]


def set_token_and_websocket(api_client, data):
    # TODO this logic is duplicated at least twice find a way to turn it into a method
    pass

def collect_event_occurred_and_correlation_id(message):
    event = re.search(r"{.id.:[\"'](.*?)[\"'],", message).groups()[0]
    correlation = re.search(r"correlationId.*:[\"''](.*)[\"'],", message).groups()[0]
    return event, correlation

