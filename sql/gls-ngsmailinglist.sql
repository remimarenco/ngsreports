SELECT array_to_string( ARRAY (
	SELECT 
	researcher.email
	FROM 
	researcher
	LEFT OUTER JOIN entity_udf_view as rudf1 on (researcher.researcherid=rudf1.attachtoid AND rudf1.udfname='Email Distribution List')
	WHERE rudf1.udfvalue = 'True'
), '; ')
