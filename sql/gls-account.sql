SELECT address.institution as institute, lab.name as group, ludf1.udfvalue as pricing, ludf2.udfvalue as external, ludf3.udfvalue as collaboration
FROM lab
LEFT OUTER JOIN entity_udf_view as ludf1 on (ludf1.attachtoid=lab.labid and ludf1.udfname='Pricing')
LEFT OUTER JOIN entity_udf_view as ludf2 on (ludf2.attachtoid=lab.labid and ludf2.udfname='External')
LEFT OUTER JOIN entity_udf_view as ludf3 on (ludf3.attachtoid=lab.labid and ludf3.udfname='Outside Collaboration')
LEFT OUTER JOIN address on (lab.billingaddressid=address.addressid)
WHERE
ludf1.udfvalue != 'Dormant Account'
ORDER BY name
