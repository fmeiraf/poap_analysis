import pandas as pd


def get_cleaned_poap_data():

    ###__getting all info about POAP events__###
    poap_events = pd.read_json("datasets/event_data.json")

    # renaming event columns for merging with poap dataset
    new_event_columns_names = {}
    for col in poap_events.columns:
        if "event" in col:
            new_name = col
        else:
            new_name = f"event_{col}"
        new_event_columns_names[col] = new_name
    poap_events = poap_events.rename(columns=new_event_columns_names)

    ###__getting all info about POAP token__###
    poap_xdai = pd.read_json("datasets/xdai_token_data.json")
    poap_xdai["chain"] = "xdai"

    poap_eth = pd.read_json("datasets/ethereum_token_data.json")
    poap_eth["chain"] = "ethereum"

    poap = pd.concat([poap_eth, poap_xdai])

    poap_original_length = len(poap)

    ###__merging POAP events and tokens__###

    poap = poap.merge(poap_events, on="event_id", how="left")
    poap_new_length = len(poap)

    if poap_original_length != poap_new_length:
        raise ValueError(
            "There was a problem with merging, new dataframe has different amount of lines"
        )

    return poap


def get_daohaus_cleaned_data():

    dao_members_dh = pd.read_json("datasets/dao_member_daohaus.json")

    dao_proposal_votes_dh = pd.read_json("datasets/dao_proposal_votes_daohaus.json")

    dao_proposal_dh = pd.read_json("datasets/dao_proposals_daohaus.json")

    return dao_members_dh, dao_proposal_dh, dao_proposal_votes_dh


# ## __ Work around to load bignumbers from json when using pandas __ ##
# import pandas.io.json

# # monkeypatch using standard python json module
# import json
# pd.io.json._json.loads = lambda s, *a, **kw: json.loads(s)
# # monkeypatch using faster simplejson module
# import simplejson
# pd.io.json._json.loads = lambda s, *a, **kw: simplejson.loads(s)
# # normalising (unnesting) at the same time (for nested jsons)
# pd.io.json._json.loads = lambda s, *a, **kw: pandas.io.json.json_normalize(simplejson.loads(s))