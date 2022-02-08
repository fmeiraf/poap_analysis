SELECT 	prop.*,
		dao.name dao_name,
		dao.address dao_address
FROM daohaus.proposal prop
	INNER JOIN daohaus.dao dao ON ( prop.dao_id = dao.id)
WHERE 	prop.trade != true
		AND prop.whitelist != true
		AND prop."newMember" != true
		