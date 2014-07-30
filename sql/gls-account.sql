SELECT lab.name as group, ludf1.udfvalue as pricing
FROM lab
LEFT OUTER JOIN entity_udf_view as ludf1 on (ludf1.attachtoid=lab.labid and ludf1.udfname='Pricing')
WHERE
ludf1.udfvalue != 'Dormant Account'
ORDER BY name
