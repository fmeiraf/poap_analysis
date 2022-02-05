import enum
from numpy import block
import requests
import json
import time
import web3
from web3._utils.abi import get_constructor_abi, merge_args_and_kwargs
from web3._utils.events import get_event_data
from web3._utils.filters import construct_event_filter_params
from web3._utils.contracts import encode_abi


def extract_token_nested_fields(target_obj: dict):
    """
    Extract nested objects from the token graphql query
    """
    new_dict = {}
    for key in target_obj.keys():
        if key in ["event", "owner"]:
            for nested_key in target_obj[key].keys():
                new_dict[f"{key}_{nested_key}"] = target_obj[key][nested_key]
        else:
            new_dict[f"token_{key}"] = target_obj[key]

    return new_dict


def extract_all_tokens_from_subgraph(
    query: str, subgraph_api_url: str, page_size: int, verbose: bool = False
):

    """
    Extract all token data from subgraph.
    """
    last_token_id = 0
    wait_time_seconds = 5
    pages_ran = 0
    extracted_data = []

    print("Starting subgraph extraction..")
    while True:
        if verbose:
            print(f"Starting page: {pages_ran}")

        req = requests.post(
            subgraph_api_url,
            json={
                "query": query,
                "variables": {"last_token": last_token_id, "page_size": page_size},
            },
        )

        if req.status_code != 200:
            print(
                f"There was a problem with the request for last_token:{last_token_id}.\n Trying again in {wait_time_seconds}  seconds.. "
            )
            time.sleep(wait_time_seconds)
            continue

        j = json.loads(req.text)

        if not j["data"]["tokens"]:
            print("Subgraph extraction is DONE. \n")
            return extracted_data

        for token_data in j["data"]["tokens"]:
            cleaned_token_data = extract_token_nested_fields(token_data)
            extracted_data.append(cleaned_token_data)
            last_token_id = int(cleaned_token_data["token_id"])

        pages_ran += 1


def extract_snapshot_space_data(
    query: str, subgraph_api_url: str, page_size: int, verbose: bool = False
):

    """
    Extract all token data from subgraph.
    """
    last_pagination_number = 0
    wait_time_seconds = 5
    pages_ran = 0
    extracted_data = []

    print("Starting graph extraction..")
    while True:
        if verbose:
            print(f"Starting page: {pages_ran}")

        req = requests.post(
            subgraph_api_url,
            json={
                "query": query,
                "variables": {
                    "page_size": page_size,
                    "skip_size": last_pagination_number,
                },
            },
        )

        if req.status_code != 200:
            print(
                f"There was a problem with the request for last_token:{last_pagination_number}.\n Trying again in {wait_time_seconds}  seconds.. "
            )
            time.sleep(wait_time_seconds)
            continue

        j = json.loads(req.text)

        if not j["data"]["spaces"]:
            print("Subgraph extraction is DONE. \n")
            return extracted_data

        for space_data in j["data"]["spaces"]:
            if space_data["members"]:
                for member_address in space_data["members"]:
                    extracted_data.append(
                        {
                            "space_id": space_data["id"],
                            "space_name": space_data["name"],
                            "space_about": space_data["about"],
                            "space_network": space_data["network"],
                            "space_symbol": space_data["symbol"],
                            "member_address": member_address,
                        }
                    )
            else:
                extracted_data.append(
                    {
                        "space_id": space_data["id"],
                        "space_name": space_data["name"],
                        "space_about": space_data["about"],
                        "space_network": space_data["network"],
                        "space_symbol": space_data["symbol"],
                        "member_address": "no_members",
                    }
                )

        last_pagination_number += page_size
        pages_ran += 1


# Credits to Mikko Ohtamaa on : https://ethereum.stackexchange.com/questions/51637/get-all-the-past-events-of-the-contract
# Thanks for the awesome code dude! :)
def fetch_events(
    latest_block_number,
    event,
    argument_filters=None,
    from_block=None,
    to_block="latest",
    address=None,
    topics=None,
):
    """Get events using eth_getLogs API.

    This is a stateless method, as opposite to createFilter and works with
    stateless nodes like QuikNode and Infura.

    :param event: Event instance from your contract.events
    :param argument_filters:
    :param from_block: Start block. Use 0 for all history/
    :param to_block: Fetch events until this contract
    :param address:
    :param topics:
    :return:
    """

    if from_block is None:
        raise TypeError("Missing mandatory keyword argument to getLogs: from_Block")

    abi = event._get_event_abi()
    abi_codec = event.web3.codec

    # Set up any indexed event filters if needed
    argument_filters = dict()
    _filters = dict(**argument_filters)

    # data_filter_set, event_filter_params = construct_event_filter_params(
    #     abi,
    #     abi_codec,
    #     contract_address=event.address,
    #     argument_filters=_filters,
    #     fromBlock=from_block,
    #     toBlock=to_block,
    #     address=address,
    #     topics=topics,
    # )

    # # Call node over JSON-RPC API
    # logs = event.web3.eth.getLogs(event_filter_params)

    logs = find_optimal_params_for_getLogs(
        abi=abi,
        abi_codec=abi_codec,
        topics=topics,
        event=event,
        filters=_filters,
        address=address,
        latest_block_number=latest_block_number,
    )

    # Convert raw binary event data to easily manipulable Python objects
    for entry in logs:
        data = get_event_data(abi_codec, abi, entry)
        yield data


def find_optimal_params_for_getLogs(
    abi, abi_codec, topics, event, filters, address, latest_block_number
):
    split_in = 2
    while True:
        print(f"Trying to fetch logs using n={split_in}")
        all_logs = []
        increment = round(latest_block_number / split_in)
        block_num_splits = [increment * n for n in range(1, split_in + 1)]

        # is_one_number_list = True if len(block_num_splits) == 1 else False

        for index, block_num in enumerate(block_num_splits):
            from_block = 0 if index == 0 else block_num_splits[index - 1] + 1
            to_block = block_num

            data_filter_set, event_filter_params = construct_event_filter_params(
                abi,
                abi_codec,
                contract_address=event.address,
                argument_filters=filters,
                fromBlock=from_block,
                toBlock=to_block,
                address=address,
                topics=topics,
            )

            try:
                logs = event.web3.eth.getLogs(event_filter_params)
                all_logs.extend(logs)
            except ValueError:
                split_in += 1
                break

            if index == len(block_num_splits) - 1:
                return all_logs


def fetch_log_history(contract: web3.contract):
    """Fetch all trading pairs on Uniswap"""
    events = list(fetch_events(contract.events.EventMinterAdded, from_block=0))
    print("Got all event history.", len(events), "events")

    event_data = [ev["args"] for ev in events]

    return event_data


def fetch_transfer_logs(web3_provider: web3.Web3, contract: web3.contract):
    """Fetch all tranfer logs from ERC 20 contract"""
    latest_block = web3_provider.eth.get_block("latest")
    events = list(
        fetch_events(latest_block["number"], contract.events.Transfer, from_block=0)
    )
    print("Got all event history.", len(events), "events")

    event_data = [ev["args"] for ev in events]

    return event_data
