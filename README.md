# WIP!!

## What is this about?

This is a bounty task from DiamondDAO to do a Data Landscape on POAPs.

## How to use the data gathering script:

1. Make sure you have a file with name `eth_rpc.yaml` in the main directory, with the following format:

   - ethereum : "your ethereum RPC url"
   - polygon : "your polygon RPC url"

2. Make sure you have a file with name `db_credentials.yaml` in the main directory, with the following format (this is just for DiamondDAO members):

   - dbname : "DBNAME"
   - host : "host URL"
   - port : "1234"
   - username : "joeDiamond"
   - password: "123change"

3. From the main directory:

   - Run the following: `python data_gather/data_gather.py`
   - This will generate all the datasets you need on `analysis/datasets`

4. Enjoy ;)
