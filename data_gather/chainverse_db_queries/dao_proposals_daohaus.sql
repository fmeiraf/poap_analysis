SELECT 	prop.*
FROM daohaus.proposal prop
WHERE 	prop.trade != true
		AND prop.whitelist != true
		AND prop."newMember" != true
		