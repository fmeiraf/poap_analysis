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
    ):

        self.eth_rpc_url = eth_rpc_url
        self.xdai_rpc_url = xdai_rpc_url
        self.polygon_rpc_url = polygon_rpc_url
        self.poap_contract_addrress = poap_contract_address

    def parse(self):
        print(" ### Starting POAP data gathering..(might take some time)  ### \n")

        # calling setters

        if not self.set_endpoints():
            raise ValueError("There was a problem setting the endpoints")

        # calling getters and storing in memory

        # self.get_poap_token_data()
        # self.get_poap_event_data()
        # self.get_bufficorns_minters()
        self.get_all_erc20s_holder_balance()

        # saving files as json on (root)/analysis/

        print("Saving files on (root)/analysis..")

        print("Done. :)")

    def get_poap_token_data(self, page_size: int = 900):
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
        print("Getting ethereum POAP mainnet subgraph data.")
        eth_token_data = utils.extract_all_tokens_from_subgraph(
            query=query,
            subgraph_api_url=eth_subgraph,
            page_size=page_size,
        )

        self.export_to_json_file(
            content_to_export=eth_token_data,
            filename_without_extension="poap_ethereum_token_data",
        )

        print("Getting POAP xdai subgraph data.")
        xdai_token_data = utils.extract_all_tokens_from_subgraph(
            query=query,
            subgraph_api_url=xdai_subgraph,
            page_size=page_size,
            verbose=True,
        )

        self.export_to_json_file(
            content_to_export=xdai_token_data,
            filename_without_extension="poap_xdai_token_data",
        )

    def get_poap_event_data(self):
        print("Getting event data..")
        poap_event_api_url = "https://api.poap.xyz/events"
        req = requests.get(poap_event_api_url)

        if req.status_code != 200:
            raise ValueError("There was a problem with your request to POAP API. ")

        j = json.loads(req.text)

        self.export_to_json_file(
            content_to_export=j,
            filename_without_extension="poap_event_data.json",
        )

        print("Finished gathering POAP event data. \n")

    def get_all_erc20s_holder_balance(self):

        tokens_to_scrappe = [
            (self.w3p, "0x9CA6a77C8B38159fd2dA9Bd25bc3E259C33F5E39"),  # polygon:Spork
            (
                self.w3e,
                "0xD56daC73A4d6766464b38ec6D91eB45Ce7457c44",  # ethereum:PANvala
            ),
            (
                self.w3e,
                "0xDe30da39c46104798bB5aA3fe8B9e0e1F348163F",  # ethereum:gitcoin
            ),
            (self.w3e, "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72"),  # ethereum:ens
            (
                self.w3x,
                "0xc4fbE68522ba81a28879763C3eE33e08b13c499E",  # xdai:common stack
            ),
        ]

        for token in tokens_to_scrappe[1:]:
            token_holder_data, token_symbol = self.scrappe_erc20token_holders_balance(
                web3_provider=token[0],
                contract_address=token[1],
                abi_path="data_gather/abi/erc20_abi.json",
            )

            self.export_to_json_file(
                content_to_export=token_holder_data,
                filename_without_extension=f"{token_symbol}_token_holder",
            )

    def get_bufficorns_minters(self):
        print("\nGetting all the BUFFINCORNS minters balances.")

        bufficorn_contract_address = "0x1e988ba4692e52Bc50b375bcC8585b95c48AaD77"
        contract = self.create_contract_instance(
            web3_provider=self.w3e,
            contract_address=bufficorn_contract_address,
            abi_path="/data_gather/abi/bufficorn_abi.json",
        )

        all_minters = []

        transfer_logs = utils.fetch_transfer_logs(contract)
        zerox = "0x0000000000000000000000000000000000000000"

        for transfer in transfer_logs:
            minter = {}
            if transfer["from"] == zerox:
                minter["bufficorn_minter_address"] = transfer["to"]
                minter["bufficorn_token_id"] = transfer["tokenId"]
                all_minters.append(minter)

        self.export_to_json_file(
            content_to_export=all_minters,
            filename_without_extension="bufficorn_minters_data",
        )

        print("Done with buffies. ")

        return all_minters

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

    def export_to_json_file(
        self,
        content_to_export: object,
        filename_without_extension: str,
        dir_to_export_to: str = "analysis/datasets/",
    ):

        final_path = os.path.join(
            os.getcwd(), dir_to_export_to, f"{filename_without_extension}.json"
        )
        if os.path.exists(final_path):
            print("This file already exists ;).")
        else:
            with open(final_path, "w") as outfile:
                json.dump(content_to_export, outfile)

    def scrappe_erc20token_holders_balance(
        self, web3_provider: Web3, contract_address: str, abi_path: str
    ):
        contract = self.create_contract_instance(
            web3_provider=web3_provider,
            contract_address=contract_address,
            abi_path=abi_path,
        )

        token_symbol = contract.functions.symbol().call()

        all_balances = []

        transfer_logs = utils.fetch_transfer_logs(contract)
        zerox = "0x0000000000000000000000000000000000000000"

        print(f"\nGetting all the {token_symbol} holders balances.")

        checked_addresses = []
        for transfer in transfer_logs:

            if transfer["from"] != zerox or transfer["from"] not in checked_addresses:
                token_balances = {}

                balance = contract.functions.balanceOf(transfer["from"]).call()

                token_balances["token_holder_address"] = transfer["from"]
                token_balances["token_holder_balance"] = balance
                all_balances.append(token_balances)
                checked_addresses.append(transfer["from"])

            if transfer["to"] != zerox or transfer["to"] not in checked_addresses:
                token_balances = {}

                balance = contract.functions.balanceOf(transfer["to"]).call()

                token_balances["token_holder_address"] = transfer["to"]
                token_balances["token_holder_balance"] = balance
                all_balances.append(token_balances)
                checked_addresses.append(transfer["to"])

        print(f"Done with {token_symbol} holders. \n ")

        return all_balances, token_symbol

    # Thought I would need to query contracts, in the end
    # it was not necessary, but will leave it here.
    # def get_event_emitter_logs(self):
    #     print(utils.fetch_log_history(self.poap_contract_xdai))


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

    # initializing the class and calling parse
    scrapper = PoapScrapper(
        eth_rpc_url=eth_provider_url,
        xdai_rpc_url=xdai_rpc_link,
        polygon_rpc_url=polygon_provider_url,
        poap_contract_address=poap_address,
    )

    scrapper.parse()


if __name__ == "__main__":
    main()
