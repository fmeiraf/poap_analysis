SELECT 	prop.*,
		memb.address member_address
FROM daohaus.proposal_votes prop
	INNER JOIN daohaus.member memb ON (prop.member_id = memb.id)

		