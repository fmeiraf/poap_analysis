SELECT 	prop.*,
		sp.name space_name,
		sp.about space_about,
		sp.location space_location
FROM snapshot.proposals prop
	INNER JOIN snapshot.spaces sp ON (prop.space_id = sp.id)