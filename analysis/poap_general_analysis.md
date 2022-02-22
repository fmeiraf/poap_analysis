# POAP Data Landscape

This analysis is part of a bounty task for [Diamond DAO](https://www.diamonddao.xyz/) and the main goal here is to understand better the POAP ecosystem and what types of signal we could get from it.

For more detailed information on the calculations and data manipulation for this summary check the following files:

- General POAP data [here](./poap_general_analysis.ipynb).
- POAP users data [here](./poap_user_analysis.ipynb).

# Some limitations of the data

Even though there is a [good API](https://api.poap.xyz/documentation/json) directly from the POAP team and a couple of subgraphs ([here](https://api.thegraph.com/subgraphs/name/poap-xyz/poap) and [here](https://api.thegraph.com/subgraphs/name/poap-xyz/poap-xdai)) the main limitation was the fact that event issuers are not identified. There is a _host_id_ field in the API but it seems it's not been used. Also, there aren't ways to identify issuer addresses or any relavant info (even a username that would be fixed in time). This fact prevented most of the analysis associating events with DAOs in a more meaningful way to happen.

# One data cleaning detail

Among the top minters a good amount of possible bots were identified where these wallets were minting 20+ events a day for a whole year. Even when the events were presencial and in different countries. After checking the data I decided to actually stick to a maximum of 5 events a day per wallet as the majority of the wallets are located in this range, plus this sounds as a more human approach to events than the possible bots.

For more details check: POAP users data [here](./poap_user_analysis.ipynb).

# Most interesting findings

- [##1](##-2021:-the-POAP-explosion): 85% of ALL the events created in the POAP platform were creted during 2021.

- [##2](##-2021:-the-POAP-explosion): ETH price seems to be fair predictor variable for the number of tokens minted.

- [##3](##-2021:-the-POAP-explosion): Even though the number of mints skyrocketed during 2021, the median number of attendees has been flat for the last 5 years , which means that the ecosystem is growing through spreading users across multiple events rather than concentrating them.

- [##4](##-2021:-the-POAP-explosion) +90% of the top minters had their first mint in 2021.

- [##5](###Most-popular-events-and-the-NFT-boom) Among the top minters, NFT related events are the most popular ones, followed by Ethereum infrastructure.

- [##6](###Most-popular-events-and-the-NFT-boom) NFT related events seem to be a very powerful tool for onboarding people to web3 and get them to participate in different types of events.

- [##7](###Most-popular-events-and-the-NFT-boom) NFT related events have on average 38% more mints than the non-NFT ones.

## 2021: the POAP explosion

2021 is a total game-changer for the POAP platform: **85% of ALL the events created in the POAP platform were created during 2021**.

![Most popular events](./images/poap_general/events_created.png)

The scenario for the number of tokens minted is very similar:

![Most popular events](./images/poap_general/tokens_minted.png)

Although we cannot be 100% sure the exact reason why, ETH price seems like a very good predictor for this big 2021 push:

![Most popular events](./images/poap_general/mints_vs_price.png)
_Number of mints is in log due to the big bumps._

Although the number of events and mints are going through the roof, the median number of mints (hence attendees) per event has been flat in the last years. This indicates that the space is growing by a bigger variety of events rather than through big massive events.

![Most popular events](./images/poap_general/median_attendees.png)

Following all the data discussed above, the most engaged users in number of mints (for the whole POAP existance) started minting in 2021 (we are so early)!

![Most popular events](./images/poap_general/minters_start.png)
_is_top_x% represents the wallets with the highest numbers of mints considering ALL years_

## Most popular events and the NFT boom

If we focus on the top 10% to 50% of the minters in the whole POAP ecosystem, we start seeing an interesting trend: NFT events are always in the top 10's:

![Most popular events](./images/poap_general/popular_events_top_minters.png)

Among the most popular events:

- Beanie x Farokh Ceasefire
- NFTFY Official Launch Party - POAP
- Metamask 10 Million Users Party
- VeeFriends x Christie's 10/01

ALL NFT related events. This leads us to some questions on **how relevant are NFT related events** among the top minters. Let's see:

![Most popular events](./images/poap_general/nft_perc_mints.png)
_This analysis is somewhat fragile though, once to identify NFT events I am using the mention of the word NFT in either the name, description or URL, so I could be probably underestimating in a good amount here_

This is very interesting because it shows that, as we go deep into the ranks of the top minters, NFT events get more and more relevant. This let us get to the conclusion that: **NFT events might be working as a big onboarding mechanism** for the ecosystem. As people enter web3 and discover different things, they start participating in different types of events. This is so much the case that, if we take a look at the top 10 events for the top 10% minters we can see a lot of Ethereum infrastructure type of events (Eth Staking, Rocket Pool, Zapper):

![Most popular events](./images/poap_general/top_10_events.png)

The other interesting aspect about the NFT role as an onboarding tool is that it has not been an overwhelming force compared to the total amount of events (_again, I might be underestimating here due to difficulty on assigning an event as related to NFT_):

![Most popular events](./images/poap_general/n_events_nft.png)

This comes as one more argument that NFTs might have been a very an important attraction point to the POAP ecosystem. In fact if we compare the average number of mints (that could be considered as a proxy for attendees) for NFT and non-NFT related events **NFT events have on average 38% more mints than the non-NFT ones** (_statistically significant for t-test with p-value < 1%_).

## Other topics explored - but with no success

- DAO relationship: this is the part that becomes difficult once we don't have issuer identification. It's hard to associate events to DAOs only using names, descriptions and URLs. I personally tried all these approaches but none of them showed satisfactory results.
