SELECT 	prop.*,
		vt.name vote_type,
		memb.address member_address,
		dao.address dao_address,
		dao.name dao_name
FROM daohaus.proposal_votes prop
	INNER JOIN daohaus.member memb ON (prop.member_id = memb.id)
	INNER JOIN daohaus.dao dao ON (memb.dao_id = dao.id)
	INNER JOIN daohaus.vote_type vt ON (vt.id = prop.vote_type_id)

		