from tabnanny import verbose
from web3 import Web3
from web3.middleware import geth_poa_middleware
import pandas as pd
import requests
import yaml
import os
import json
import utils
import psycopg2


class PoapScrapper:
    def __init__(
        self,
        eth_rpc_url: str,
        xdai_rpc_url: str,
        polygon_rpc_url: str,
        poap_contract_address: str,
        db_credentials: object,
    ):

        self.eth_rpc_url = eth_rpc_url
        self.xdai_rpc_url = xdai_rpc_url
        self.polygon_rpc_url = polygon_rpc_url
        self.poap_contract_addrress = poap_contract_address
        self.db_credentials = db_credentials

    def parse(self):
        print(" ### Starting POAP data gathering..(might take some time)  ### \n")

        # calling setters

        if not self.set_endpoints():
            raise ValueError("There was a problem setting the endpoints")

        # calling getters and storing in memory

        self.get_poap_token_data()
        self.get_poap_event_data()
        self.get_bufficorns_minters()
        self.get_all_erc20s_holder_balance()
        self.get_chainverse_db_data()
        self.get_snapshot_dao_members_data()

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

    # decided to comment out GTC and ENS once these have too many token balances
    # it's better to query the address I am intersted in later during analysis
    def get_all_erc20s_holder_balance(self):

        tokens_to_scrappe = [
            (self.w3p, "0x9CA6a77C8B38159fd2dA9Bd25bc3E259C33F5E39"),  # polygon:Spork
            (
                self.w3e,
                "0xD56daC73A4d6766464b38ec6D91eB45Ce7457c44",  # ethereum:PANvala
            ),
            (
                self.w3x,
                "0xc4fbE68522ba81a28879763C3eE33e08b13c499E",  # xdai:common stack
            ),
            # (
            #     self.w3e,
            #     "0xDe30da39c46104798bB5aA3fe8B9e0e1F348163F",  # ethereum:gitcoin
            # ),
            # (self.w3e, "0xC18360217D8F7Ab5e7c516566761Ea12Ce7F9D72"),  # ethereum:ens
        ]

        for token in tokens_to_scrappe:
            (
                token_holder_data,
                token_symbol,
                transactions_history,
            ) = self.scrappe_erc20token_holders_balance(
                web3_provider=token[0],
                contract_address=token[1],
                abi_path="data_gather/abi/erc20_abi.json",
            )

            self.export_to_json_file(
                content_to_export=token_holder_data,
                filename_without_extension=f"{token_symbol}_token_holder",
            )

            self.export_to_json_file(
                content_to_export=transactions_history,
                filename_without_extension=f"{token_symbol}_transaction_history",
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

    def get_chainverse_db_data(self):
        queries_root_dir = os.path.join(
            os.getcwd(), "data_gather/chainverse_db_queries"
        )
        query_files = os.listdir(queries_root_dir)

        # Creating the parameters dict
        query_repo = {}
        for filename in query_files:
            key = filename.split(".")[0]
            content = os.path.join(queries_root_dir, filename)
            query_repo[key] = content

        # getting the data as a pandas Dataframe and converting to json
        for query_name in query_repo.keys():
            print(f"Querying Chainverse database for {query_name} \n")
            self.get_data_from_chainverse_db(
                self.db_credentials, query_repo[query_name], f"{query_name}"
            )
            print("..done.")

    def get_snapshot_dao_members_data(self, page_size: int = 100):

        snapshot_graphql_api_url = "https://hub.snapshot.org/graphql"

        query = """
            query get_daos($skip_size: Int, $page_size: Int) {
                spaces (first: $page_size, 
                        skip: $skip_size,
                        orderBy:"id",
                        orderDirection: asc)
                   
                {
                    id
                    name
                    about
                    network
                    symbol
                    admins
                    members
                }
            }
        """
        print("Getting snapshot DAO/space data from their graphql API.")
        snap_spaces_data = utils.extract_snapshot_space_data(
            query=query,
            subgraph_api_url=snapshot_graphql_api_url,
            page_size=page_size,
            verbose=True,
        )

        self.export_to_json_file(
            content_to_export=snap_spaces_data,
            filename_without_extension=f"snapshot_spaces_members",
        )

    def set_endpoints(self):
        """
        Set the RPC endpoints for queries
        """
        self.w3e = Web3(Web3.HTTPProvider(self.eth_rpc_url))
        self.w3x = Web3(Web3.HTTPProvider(self.xdai_rpc_url))

        self.w3p = Web3(Web3.HTTPProvider(self.polygon_rpc_url))
        self.w3p.middleware_onion.inject(
            geth_poa_middleware, layer=0
        )  # adding this due to errors when running getLogs
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

        print(f"\nGetting all the {token_symbol} holders balances.")

        transfer_logs = utils.fetch_transfer_logs(web3_provider, contract)
        zerox = "0x0000000000000000000000000000000000000000"

        checked_addresses = set()
        transaction_history = []
        for transfer in transfer_logs:

            if transfer["from"] != zerox:
                checked_addresses.add(transfer["from"])

            if transfer["to"] != zerox:
                checked_addresses.add(transfer["to"])

            transaction_history.append({**transfer})

        all_balances = []
        for holder_address in checked_addresses:
            balance = contract.functions.balanceOf(holder_address).call()
            all_balances.append({"holder_address": holder_address, "balance": balance})

        print(f"Done with {token_symbol} holders. \n ")

        return all_balances, token_symbol, transaction_history

    def get_data_from_chainverse_db(
        self,
        db_credentials: object,
        sql_query_path: str,
        filename: str,
        dir_to_export_to="analysis/datasets/",
    ):
        conn_string = f"""
        dbname={db_credentials["dbname"]}
        host={db_credentials["host"]}
        port={db_credentials["port"]}
        user={db_credentials["username"]}
        password={db_credentials["password"]}
        """
        conn = psycopg2.connect(conn_string)

        with open(sql_query_path, "r") as sql_content:
            query = sql_content.read()

        df = pd.read_sql_query(query, conn)
        print(df.head())
        final_path = os.path.join(os.getcwd(), dir_to_export_to, f"{filename}.json")
        df.to_json(final_path, orient="records")

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

    db_credentials_path = os.path.join(os.getcwd(), "db_credentials.yaml")
    if not os.path.exists(db_credentials_path):
        raise OSError(
            "You should have a yaml file on your root directory called db_credentials.yaml! Check the README for more info"
        )

    with open(db_credentials_path) as file:
        db_credentials = yaml.load(file, Loader=yaml.FullLoader)

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
        db_credentials=db_credentials,
    )

    scrapper.parse()


if __name__ == "__main__":
    main()
