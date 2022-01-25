from tabnanny import check
from black import token
import pandas as pd
from web3 import Web3
import requests
import yaml
import os
import json
import utils


class PoapScrapper:
    def __init__(
        self,
        eth_rpc_url: str,
        xdai_rpc_url: str,
        polygon_rpc_url: str,
        poap_contract_address: str,
        spork_token_address: str,
    ):

        self.eth_rpc_url = eth_rpc_url
        self.xdai_rpc_url = xdai_rpc_url
        self.polygon_rpc_url = polygon_rpc_url
        self.poap_contract_addrress = poap_contract_address
        self.spork_token_address = spork_token_address

    def parse(self):
        print(" ### Starting POAP data gathering..(might take some time)  ### \n")
        # calling setters

        ## Thought I would need to query contracts, but in didn't need ##
        ## will leave it here though until I get certain. ##

        # if not self.set_endpoints():
        #     raise ValueError("There was a problem setting the endpoints")

        # self.set_contracts()

        # calling getters and storing in memory

        self.get_token_data()
        self.get_event_data()
        self.get_spork_token_holders()

        # saving files as json on (root)/analysis/

        print("Saving files on (root)/analysis..")

        eth_file_destiny_path = os.path.join(
            os.getcwd(), "analysis/datasets/ethereum_token_data.json"
        )
        with open(eth_file_destiny_path, "w") as outfile:
            json.dump(self.eth_token_data, outfile)

        xdai_file_destiny_path = os.path.join(
            os.getcwd(), "analysis/datasets/xdai_token_data.json"
        )
        with open(xdai_file_destiny_path, "w") as outfile:
            json.dump(self.xdai_token_data, outfile)

        events_file_destiny_path = os.path.join(
            os.getcwd(), "analysis/datasets/event_data.json"
        )
        with open(events_file_destiny_path, "w") as outfile:
            json.dump(self.event_data, outfile)

        spork_holders_file_destiny_path = os.path.join(
            os.getcwd(), "analysis/datasets/spork_holders_balance.json"
        )
        with open(spork_holders_file_destiny_path, "w") as outfile:
            json.dump(self.spork_token_balances, outfile)

        print("Done. :)")

    def get_token_data(self, page_size: int = 900):
        """
        Get all the tokens from both chains using graphql

        @page_size = number of records per query
        """
        eth_subgraph = "https://api.thegraph.com/subgraphs/name/poap-xyz/poap"
        xdai_subgraph = "https://api.thegraph.com/subgraphs/name/poap-xyz/poap-xdai"

        query = """
            query get_token($last_token: Int, $page_size: Int) {
                tokens (first: $page_size, 
                        orderBy:id,
                        orderDirection: asc,
                        where: {id_gt: $last_token}) 
                {
                    id
                    owner{
                        id
                    }
                    event {
                        id
                        tokenCount
                        created
                        transferCount
                    }
                    created
                    transferCount
                }
            }
        """
        print("Getting ethereum mainnet subgraph data.")
        self.eth_token_data = utils.extract_all_tokens_from_subgraph(
            query=query,
            subgraph_api_url=eth_subgraph,
            page_size=page_size,
        )

        print("Getting xdai subgraph data.")
        self.xdai_token_data = utils.extract_all_tokens_from_subgraph(
            query=query,
            subgraph_api_url=xdai_subgraph,
            page_size=page_size,
            verbose=True,
        )

    def get_event_data(self):
        print("Getting event data..")
        poap_event_api_url = "https://api.poap.xyz/events"
        req = requests.get(poap_event_api_url)

        if req.status_code != 200:
            raise ValueError("There was a problem with your request to POAP API. ")

        j = json.loads(req.text)

        self.event_data = j

        print("Finished gathering event data. \n")

    def get_spork_token_holders(self):
        token_balances = {}

        transfer_logs = utils.fetch_erc20_transfer_logs(self.spork_token_contract)
        zerox = "0x0000000000000000000000000000000000000000"

        checked_addresses = []
        for transfer in transfer_logs:
            if transfer["from"] != zerox and transfer["from"] not in checked_addresses:
                balance = self.spork_token_contract.functions.balanceOf(
                    transfer["from"]
                ).call()
                token_balances[transfer["from"]] = balance
                checked_addresses.append(transfer["from"])
            if transfer["to"] != zerox and transfer["to"] not in checked_addresses:
                balance = self.spork_token_contract.functions.balanceOf(
                    transfer["to"]
                ).call()
                token_balances[transfer["to"]] = balance
                checked_addresses.append(transfer["to"])

        self.spork_token_balances = token_balances

        return token_balances

    # Thought I would need to query contracts, in the end
    # it was not necessary, but will leave it here.
    def set_endpoints(self):
        """
        Set the RPC endpoints for queries
        """
        self.w3e = Web3(Web3.HTTPProvider(self.eth_rpc_url))
        self.w3x = Web3(Web3.HTTPProvider(self.xdai_rpc_url))
        self.w3p = Web3(Web3.HTTPProvider(self.polygon_rpc_url))
        return (
            self.w3e.isConnected() and self.w3x.isConnected() and self.w3p.isConnected()
        )

    def create_contract_instance(
        self, web3_provider: Web3, contract_address: str, abi_path: str
    ):
        """
        Instantiate one contract
        """

        if not os.path.exists(abi_path):
            raise OSError(
                "You should have a the abi json file with this path > data_gather/poap_abi.json"
            )
        with open(abi_path, "r") as file:
            abi = file.read()

        contract_instance = web3_provider.eth.contract(
            address=contract_address, abi=abi
        )

        return contract_instance

    # Thought I would need to query contracts, in the end
    # it was not necessary, but will leave it here.
    def set_all_contracts(self):
        """
        Initialize both contracts (ethereum and xDai)
        """
        poap_abi_path = os.path.join(os.getcwd(), "data_gather/abi/poap_abi.json")
        erc20_abi_path = os.path.join(os.getcwd(), "data_gather/abi/erc20_abi.json")

        # POAP contract happens to have the same address in both chains..
        self.poap_contract_eth = self.create_contract_instance(
            web3_provider=self.w3e,
            contract_address=self.poap_contract_addrress,
            abi_path=poap_abi_path,
        )

        self.poap_contract_xdai = self.create_contract_instance(
            web3_provider=self.w3x,
            contract_address=self.poap_contract_addrress,
            abi_path=poap_abi_path,
        )

        self.spork_token_contract = self.create_contract_instance(
            web3_provider=self.w3p,
            contract_address=self.spork_token_address,
            abi_path=erc20_abi_path,
        )

        assert (
            type(self.poap_contract_eth.functions.name().call()) == str
        ), "Problem initializing POAP eth contract."
        assert (
            type(self.poap_contract_xdai.functions.name().call()) == str
        ), "Problem initializing POAP xdai contract."

    # Thought I would need to query contracts, in the end
    # it was not necessary, but will leave it here.
    def get_event_emitter_logs(self):
        print(utils.fetch_log_history(self.poap_contract_xdai))


def main():

    # getting RPC links and API keys
    eth_yaml_path = os.path.join(os.getcwd(), "eth_rpc.yaml")
    if not os.path.exists(eth_yaml_path):
        raise OSError(
            "You should have a yaml file on your root directory called eth_rpc.yaml! Check the README for more info"
        )

    with open(eth_yaml_path) as file:
        provider_params = yaml.load(file, Loader=yaml.FullLoader)

    eth_provider_url = provider_params["ethereum"]
    polygon_provider_url = provider_params["polygon"]

    xdai_rpc_link = "https://rpc.gnosischain.com/"
    poap_address = "0x22C1f6050E56d2876009903609a2cC3fEf83B415"
    spork_address = "0x9CA6a77C8B38159fd2dA9Bd25bc3E259C33F5E39"

    # initializing the class and calling parse
    scrapper = PoapScrapper(
        eth_rpc_url=eth_provider_url,
        xdai_rpc_url=xdai_rpc_link,
        polygon_rpc_url=polygon_provider_url,
        poap_contract_address=poap_address,
        spork_token_address=spork_address,
    )

    scrapper.set_endpoints()
    scrapper.set_all_contracts()
    print(scrapper.get_spork_token_holders())

    # scrapper.parse()


if __name__ == "__main__":
    main()
