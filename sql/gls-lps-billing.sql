-- --------------------------------------------------------------------------------
-- LPS BILLING QUERY
-- against genologics database v3.3.1.9 http://genologics.com/
-- --------------------------------------------------------------------------------

-- SELECT -------------------------------------------------------------------------
SELECT distinct
researcher.firstname || ' ' || researcher.lastname as researcher,
lab.name as lab,
address.institution as institute,
sudf1.udfvalue as slxid,
audf1.udfvalue as lpsbillable,
to_char(process.daterun, 'YYYY-MM') as billingmonth,
sudf2.udfvalue as billingcode,
project.name as projectname,
sampleprocess.luid as sampleid,
sample.name as samplename
-- FROM ---------------------------------------------------------------------------
FROM process,
processtype,
processiotracker,
outputmapping,
artifact
LEFT OUTER JOIN artifact_udf_view as audf1 on (audf1.artifactid=artifact.artifactid AND audf1.udfname = 'LPS - Billable'),
artifact_sample_map,
sample
LEFT OUTER JOIN sample_udf_view as sudf1 on (sudf1.sampleid=sample.sampleid AND sudf1.udfname = 'SLX Identifier')
LEFT OUTER JOIN sample_udf_view as sudf2 on (sudf2.sampleid=sample.sampleid AND sudf2.udfname = 'Billing Information'),
process as sampleprocess,
project,
researcher,
lab
LEFT OUTER JOIN address on (lab.billingaddressid=address.addressid)
-- WHERE --------------------------------------------------------------------------
WHERE process.typeid = processtype.typeid
AND processtype.displayname='LPS Complete'
AND process.workstatus='COMPLETE'
AND process.daterun >= '2014-04-01' AND process.daterun <= '2015-03-31'
AND process.processid=processiotracker.processid
AND outputmapping.trackerid=processiotracker.trackerid
AND outputmapping.outputartifactid=artifact.artifactid
AND artifact_sample_map.artifactid=artifact.artifactid
AND artifact_sample_map.processid=sample.processid
AND sample.processid=sampleprocess.processid
AND sample.projectid=project.projectid
AND project.researcherid=researcher.researcherid
AND researcher.labid=lab.labid
AND sample.name NOT LIKE 'Genomics Control%'
AND project.name != 'Controls'
-- ORDER BY -----------------------------------------------------------------------
ORDER BY slxid, billingmonth
