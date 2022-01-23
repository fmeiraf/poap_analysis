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
        poap_contract_address: str,
    ):

        self.eth_rpc_url = eth_rpc_url
        self.xdai_rpc_url = xdai_rpc_url
        self.poap_contract_addrress = poap_contract_address

    def set_endpoints(self):
        """
        Set the RPC endpoints for queries
        """
        self.w3e = Web3(Web3.HTTPProvider(self.eth_rpc_url))
        self.w3x = Web3(Web3.HTTPProvider(self.xdai_rpc_url))
        return self.w3e.isConnected() and self.w3x.isConnected()

    def set_contracts(self):
        """
        Initialize both contracts (ethereum and xDai)
        """
        abi_path = os.path.join(os.getcwd(), "data_gather/poap_abi.json")
        if not os.path.exists(abi_path):
            raise OSError(
                "You should have a the abi json file with this path > data_gather/poap_abi.json"
            )

        with open(abi_path, "r") as file:
            abi = file.read()
        self.poap_abi = abi

        # POAP contract happens to have the same address in both chains..
        self.poap_contract_eth = self.w3e.eth.contract(
            address=self.poap_contract_addrress, abi=abi
        )
        self.poap_contract_xdai = self.w3x.eth.contract(
            address=self.poap_contract_addrress, abi=abi
        )

        assert (
            type(self.poap_contract_eth.functions.name().call()) == str
        ), "Problem initializing POAP eth contract."
        assert (
            type(self.poap_contract_xdai.functions.name().call()) == str
        ), "Problem initializing POAP xdai contract."

    def get_token_data(self, page_size: int = 100):
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


def main():

    # getting RPC links and API keys
    eth_yaml_path = os.path.join(os.getcwd(), "eth_rpc.yaml")
    if not os.path.exists(eth_yaml_path):
        raise OSError(
            "You should have a yaml file on your root directory called eth_rpc.yaml! Check the README for more info"
        )

    with open(eth_yaml_path) as file:
        provider_params = yaml.load(file, Loader=yaml.FullLoader)
    eth_provider_url = provider_params["key"]

    xdai_rpc_link = "https://rpc.gnosischain.com/"
    poap_address = "0x22C1f6050E56d2876009903609a2cC3fEf83B415"

    # initializing the class and the set methods
    scrapper = PoapScrapper(
        eth_rpc_url=eth_provider_url,
        xdai_rpc_url=xdai_rpc_link,
        poap_contract_address=poap_address,
    )

    if not scrapper.set_endpoints():
        raise ValueError("There was some proble with RPC endpoint initialization.")

    scrapper.set_contracts()

    # calling getter methods

    scrapper.get_token_data()


if __name__ == "__main__":
    main()
