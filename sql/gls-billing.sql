-- --------------------------------------------------------------------------------
-- BILLING QUERY - latest version 29-May-2014
-- against genologics database v3.0.2.8 http://genologics.com/
-- --------------------------------------------------------------------------------
-- changelog:
-- 29/05/15: remove control samples
-- 28/05/14: simplify billing query containing only essential fields
-- 05/03/14: remove sub-query and process join, simplify query by using WITH 
--           change billing month to return billing process daterun instead of 
--           sequencing process daterun
-- 26/02/14: add new sample UDF Billing Information 
-- 31/01/14: add two new UDFs % lost reads and yield
-- 21/01/14: add avg library length as it can be different over samples in pool
--           add fields Library Type; Index Type & Average Library Length
-- 02/07/13: first versions
-- --------------------------------------------------------------------------------

WITH billing as (
	SELECT artifact.luid as artifactluid, process.daterun as daterun
	FROM processiotracker, process,	processtype, artifact
	WHERE processiotracker.processid=process.processid 
	AND process.typeid=processtype.typeid 
	AND processtype.displayname='Billing' 
	AND processiotracker.inputartifactid=artifact.artifactid 
	AND process.daterun >= '2014-04-01' AND process.daterun <= '2015-03-31'
)
-- SELECT -------------------------------------------------------------------------
SELECT distinct
researcher.firstname || ' ' || researcher.lastname as researcher, 
lab.name as lab, 
address.institution as institute,
sudf1.udfvalue as slxid, 
itype.name || '_' || case when itype.name = 'Miseq' then split_part(pudf4.udfvalue, '-', 2) else case when pudf2.udfvalue is null then 'SE' else 'PE' end || pudf1.udfvalue end as runtype,
audf1.udfvalue as billable, 
to_char(billing.daterun, 'YYYY-MM') as billingmonth, 
sudf2.udfvalue as billingcode,
case when pudf3.udfvalue is null then container.name else pudf3.udfvalue end as flowcellid, 
'Lane' || containerplacement.wellyposition + 1 as lane, 
audf2.udfvalue as yield
-- FROM ---------------------------------------------------------------------------
FROM billing, 
process 
LEFT OUTER JOIN process_udf_view as pudf1 on (pudf1.processid=process.processid AND pudf1.udfname like 'Read 1 Cycle%') 
LEFT OUTER JOIN process_udf_view as pudf2 on (pudf2.processid=process.processid AND pudf2.udfname like 'Read 2 Cycle%')
LEFT OUTER JOIN process_udf_view as pudf3 on (pudf3.processid=process.processid AND pudf3.udfname = 'Flow Cell ID')
LEFT OUTER JOIN process_udf_view as pudf4 on (pudf4.processid=process.processid AND pudf4.udfname = 'Reagent Cartridge ID'), 
processtype, 
installation, 
instrument, 
itype, 
processiotracker, 
artifact 
LEFT OUTER JOIN artifact_udf_view as audf1 on (audf1.artifactid=artifact.artifactid AND audf1.udfname = 'Billable')
LEFT OUTER JOIN artifact_udf_view as audf2 on (audf2.artifactid=artifact.artifactid AND audf2.udfname = 'Yield (Mreads)'), 
containerplacement, 
container, 
artifact_sample_map, 
sample 
LEFT OUTER JOIN sample_udf_view as sudf1 on (sudf1.sampleid=sample.sampleid AND sudf1.udfname = 'SLX Identifier')
LEFT OUTER JOIN sample_udf_view as sudf2 on (sudf2.sampleid=sample.sampleid AND sudf2.udfname = 'Billing Information'),
project, 
researcher, 
lab 
LEFT OUTER JOIN address on (lab.billingaddressid=address.addressid)
-- WHERE --------------------------------------------------------------------------
WHERE process.typeid = processtype.typeid
AND processtype.displayname like '%Run%'
AND process.installationid=installation.id
AND installation.instrumentid=instrument.instrumentid
AND instrument.typeid=itype.typeid
AND process.processid=processiotracker.processid 
AND processiotracker.inputartifactid=artifact.artifactid
AND containerplacement.processartifactid=artifact.artifactid
AND containerplacement.containerid=container.containerid
AND artifact_sample_map.artifactid=artifact.artifactid
AND artifact_sample_map.processid=sample.processid
AND sample.projectid=project.projectid
AND project.researcherid=researcher.researcherid
AND researcher.labid=lab.labid
AND artifact.luid=billing.artifactluid
AND sample.name NOT LIKE 'Genomics Control%'
AND project.name != 'Controls'
-- ORDER BY -----------------------------------------------------------------------
ORDER BY billable, flowcellid, lane
