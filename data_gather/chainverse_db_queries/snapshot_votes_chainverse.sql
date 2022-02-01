SELECT  sv.*,
        sp.name space_name,
		sp.about space_about,
		sp.location space_location
FROM snapshot.votes sv
    INNER JOIN snapshot.spaces sp ON (sv.space_id = sp.id)