SELECT 	memb.*,
		dao.name dao_name,
		dao.address dao_address,
		dao.inactive dao_inactive,
		dao.created_at dao_created_at,
		dao.chain dao_chain
FROM daohaus.member memb
  INNER JOIN daohaus.dao dao ON (memb.dao_id = dao.id)
ORDER BY memb.address