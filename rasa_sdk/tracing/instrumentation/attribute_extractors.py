import json

from typing import Any, Dict, Text, List
from rasa_sdk.executor import ActionExecutor, CollectingDispatcher
from rasa_sdk.forms import ValidationAction
from rasa_sdk.types import ActionCall, DomainDict
from rasa_sdk import Tracker


# This file contains all attribute extractors for tracing instrumentation.
# These are functions that are applied to the arguments of the wrapped function to be
# traced to extract the attributes that we want to forward to our tracing backend.
# Note that we always mirror the argument lists of the wrapped functions, as our
# wrapping mechanism always passes in the original arguments unchanged for further
# processing.


def extract_attrs_for_action_executor(
    self: ActionExecutor,
    action_call: ActionCall,
) -> Dict[Text, Any]:
    """Extract the attributes for `ActionExecutor.run`.

    :param self: The `ActionExecutor` on which `run` is called.
    :param action_call: The `ActionCall` argument.
    :return: A dictionary containing the attributes.
    """
    attributes = {"sender_id": action_call.get("sender_id", "None")}
    action_name = action_call.get("next_action")

    if action_name:
        attributes["action_name"] = action_name

    return attributes


def extract_attrs_for_validation_action(
    self: ValidationAction,
    dispatcher: CollectingDispatcher,
    tracker: Tracker,
    domain: DomainDict,
) -> Dict[Text, Any]:
    """Extract the attributes for `ValidationAction.run`.

    :param self: The `ValidationAction` on which `run` is called.
    :param dispatcher: The `CollectingDispatcher` argument.
    :param tracker: The `Tracker` argument.
    :param domain: The `DomainDict` argument.
    :return: A dictionary containing the attributes.
    """
    slots_to_validate = tracker.slots_to_validate().keys()

    return {
        "class_name": self.__class__.__name__,
        "sender_id": tracker.sender_id,
        "slots_to_validate": json.dumps(list(slots_to_validate)),
        "action_name": self.name(),
    }


def extract_attrs_for_action_executor_create_api_response(
    events: List[Dict[Text, Any]],
    messages: List[Dict[Text, Any]],
) -> Dict[Text, Any]:
    """Extract the attributes for `ActionExecutor.run`.

    :param events: A list of events.
    :param messsages: A list of bot responses.
    :return: A dictionary containing the attributes.
    """
    event_names = []
    slot_names = []

    event_seen = set()
    slot_seen = set()

    append_event_name = event_names.append
    append_slot_name = slot_names.append

    # Optimize repeated .get lookups and preserve order/uniqueness without dict overhead
    for event in events:
        event_val = event.get("event")
        if event_val not in event_seen:
            append_event_name(event_val)
            event_seen.add(event_val)
        if event_val == "slot":
            slot_val = event.get("name")
            if slot_val != "requested_slot" and slot_val not in slot_seen:
                append_slot_name(slot_val)
                slot_seen.add(slot_val)

    # Pre-allocate list by iterating once, avoid redundant .get
    utters = []
    append_utter = utters.append
    for message in messages:
        response = message.get("response")
        if response:
            append_utter(response)

    return {
        "events": json.dumps(event_names),
        "slots": json.dumps(slot_names),
        "utters": json.dumps(utters),
        "message_count": len(messages),
    }
