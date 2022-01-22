import pandas as pd
from web3 import Web3
import yaml
import os


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

        abi_path = os.path.join(os.getcwd(), "data_gather/poap_abi.json")
        if not os.path.exists(abi_path):
            raise OSError(
                "You should have a the abi json file with this path > data_gather/poap_abi.json"
            )

        with open(abi_path, "r") as file:
            abi = file.read()
        self.poap_abi = abi

        self.w3e = Web3(Web3.HTTPProvider(self.eth_rpc_url))
        self.w3x = Web3(Web3.HTTPProvider(self.xdai_rpc_url))

    def check_rpc_connection(self):
        return self.w3e.isConnected() and self.w3x.isConnected()


if __name__ == "__main__":
    ##initialization
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

    scrapper = PoapScrapper(
        eth_rpc_url=eth_provider_url,
        xdai_rpc_url=xdai_rpc_link,
        poap_contract_address=poap_address,
    )

    print(scrapper.check_rpc_connection())
