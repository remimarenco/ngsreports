-- --------------------------------------------------------------------------------
-- QC QUERY - latest version 29-May-2014
-- against genologics database v3.0.2.8 http://genologics.com/
-- --------------------------------------------------------------------------------
-- changelog:
-- 30/04/14: add acceptance and publishing dates and number of days between the two
-- 29/05/14: create qc query from previous billing one
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
	SELECT artifact.luid as artifactluid, process.daterun as daterun, pudf1.udfvalue as fcbillingcomments
	FROM processiotracker, process
	LEFT OUTER JOIN process_udf_view as pudf1 on (pudf1.processid=process.processid AND pudf1.udfname = 'Flowcell Billing Comments'),
	processtype, artifact
	WHERE processiotracker.processid=process.processid 
	AND process.typeid=processtype.typeid 
	AND processtype.displayname='Billing' 
	AND processiotracker.inputartifactid=artifact.artifactid 
) ,
publishing as (
	SELECT artifact.luid as artifactluid, process.daterun as daterun
	FROM processiotracker, process, processtype, artifact
	WHERE processiotracker.processid=process.processid 
	AND process.typeid=processtype.typeid 
	AND processtype.displayname='Publishing' 
	AND processiotracker.inputartifactid=artifact.artifactid 
),
accept as (
 	SELECT sample.processid as sampleid, process.daterun as daterun
 	FROM processiotracker, process, processtype, artifact, artifact_sample_map, sample
 	WHERE processiotracker.processid=process.processid 
 	AND process.typeid=processtype.typeid 
 	AND (processtype.displayname='Accept SLX' or processtype.displayname='Aggregate QC (Library Validation)')
 	AND processiotracker.inputartifactid=artifact.artifactid 
 	AND artifact_sample_map.artifactid=artifact.artifactid
 	AND artifact_sample_map.processid=sample.processid
) 
-- SELECT -------------------------------------------------------------------------
SELECT distinct
researcher.firstname || ' ' || researcher.lastname as researcher, 
lab.name as lab, 
address.institution as institute,
sudf1.udfvalue as slxid, 
case when itype.name = 'Hiseq' then 
        case when pudf4.udfvalue like '______NXX' then 'HiSeq'
             when pudf4.udfvalue like '______CXX' then 'HiSeq2000' 
             when pudf4.udfvalue like '______DXX' then 'HiSeqRapid' 
             else 'HiSeqUnknown'
        end
     when itype.name = 'Miseq' then itype.name 
     else itype.name 
end || '_' || case when pudf2.udfvalue is null then 'SE' else 'PE' end || pudf1.udfvalue as runtype,
case when sudf7.udfvalue = 'Single Read' then 'SE'
     when sudf7.udfvalue = 'Paired End' then 'PE'
     else '??'
end || sudf8.udfvalue as requested_runtype,
audf1.udfvalue as billable, 
to_char(billing.daterun, 'YYYY-MM') as billingmonth, 
case when pudf4.udfvalue is null then container.name else pudf4.udfvalue end as flowcellid, 
'Lane' || containerplacement.wellyposition + 1 as lane, 
billing.fcbillingcomments as flowcellbillingcomments,
audf2.udfvalue as billingcomments,
pudf5.udfvalue as runfolder, 
instrument.name as instrument,
to_char(sample.datereceived, 'YYYY-MM-DD') as submissiondate,
to_char(accept.daterun, 'YYYY-MM-DD') as acceptancedate,
to_char(to_date(pudf3.udfvalue, 'YYYY-MM-DD'), 'YYYY-MM-DD') as sequencingdate, 
to_char(publishing.daterun, 'YYYY-MM-DD') as publishingdate,
to_char(billing.daterun, 'YYYY-MM-DD') as billingdate, 
publishing.daterun - accept.daterun as accept2publishdays,
sudf5.udfvalue as billing_code,
sudf2.udfvalue as library_type,
sudf3.udfvalue as index_type,
to_char(avg(to_number(sudf4.udfvalue, '99999')), '9999.99') as avg_library_length,
sudf6.udfvalue as priority_status,
audf3.udfvalue as yield_pf_r1,
audf4.udfvalue as avg_q_score_r1,
audf5.udfvalue as percent_bases_q30_r1,
audf15.udfvalue as yield,
audf14.udfvalue as percent_lost_reads,
audf6.udfvalue as cluster_density_r1,
audf7.udfvalue as percent_pf_r1,
audf8.udfvalue as intensity_cycle_1_r1,
audf9.udfvalue as percent_intensity_cycle_20_r1,
audf10.udfvalue as percent_phasing_r1,
audf11.udfvalue as percent_prephasing_r1,
audf12.udfvalue as percent_aligned_r1,
audf13.udfvalue as percent_error_rate_r1,
ludf1.udfvalue as external
-- FROM ---------------------------------------------------------------------------
FROM billing, 
publishing,
accept,
process 
LEFT OUTER JOIN process_udf_view as pudf1 on (pudf1.processid=process.processid AND pudf1.udfname like 'Read 1 Cycle%') 
LEFT OUTER JOIN process_udf_view as pudf2 on (pudf2.processid=process.processid AND pudf2.udfname like 'Read 2 Cycle%') 
LEFT OUTER JOIN process_udf_view as pudf3 on (pudf3.processid=process.processid AND pudf3.udfname = 'Finish Date')
LEFT OUTER JOIN process_udf_view as pudf4 on (pudf4.processid=process.processid AND pudf4.udfname = 'Flow Cell ID')
LEFT OUTER JOIN process_udf_view as pudf5 on (pudf5.processid=process.processid AND pudf5.udfname = 'Run ID')
LEFT OUTER JOIN process_udf_view as pudf6 on (pudf6.processid=process.processid AND pudf6.udfname = 'Reagent Cartridge ID'), 
processtype, 
installation, 
instrument, 
itype, 
processiotracker, 
artifact 
LEFT OUTER JOIN artifact_udf_view as audf1 on (audf1.artifactid=artifact.artifactid AND audf1.udfname = 'Billable')
LEFT OUTER JOIN artifact_udf_view as audf2 on (audf2.artifactid=artifact.artifactid AND audf2.udfname = 'Billing Comments')
LEFT OUTER JOIN artifact_udf_view as audf3 on (audf3.artifactid=artifact.artifactid AND audf3.udfname = 'Yield PF (Gb) R1')
LEFT OUTER JOIN artifact_udf_view as audf4 on (audf4.artifactid=artifact.artifactid AND audf4.udfname = 'Avg Q Score R1')
LEFT OUTER JOIN artifact_udf_view as audf5 on (audf5.artifactid=artifact.artifactid AND audf5.udfname = '% Bases >=Q30 R1')
LEFT OUTER JOIN artifact_udf_view as audf6 on (audf6.artifactid=artifact.artifactid AND audf6.udfname = 'Cluster Density (K/mm^2) R1')
LEFT OUTER JOIN artifact_udf_view as audf7 on (audf7.artifactid=artifact.artifactid AND audf7.udfname = '%PF R1')
LEFT OUTER JOIN artifact_udf_view as audf8 on (audf8.artifactid=artifact.artifactid AND audf8.udfname = 'Intensity Cycle 1 R1')
LEFT OUTER JOIN artifact_udf_view as audf9 on (audf9.artifactid=artifact.artifactid AND audf9.udfname = '% Intensity Cycle 20 R1')
LEFT OUTER JOIN artifact_udf_view as audf10 on (audf10.artifactid=artifact.artifactid AND audf10.udfname = '% Phasing R1')
LEFT OUTER JOIN artifact_udf_view as audf11 on (audf11.artifactid=artifact.artifactid AND audf11.udfname = '% Prephasing R1')
LEFT OUTER JOIN artifact_udf_view as audf12 on (audf12.artifactid=artifact.artifactid AND audf12.udfname = '% Aligned R1')
LEFT OUTER JOIN artifact_udf_view as audf13 on (audf13.artifactid=artifact.artifactid AND audf13.udfname = '% Error Rate R1')
LEFT OUTER JOIN artifact_udf_view as audf14 on (audf14.artifactid=artifact.artifactid AND audf14.udfname = '% Lost Reads')
LEFT OUTER JOIN artifact_udf_view as audf15 on (audf15.artifactid=artifact.artifactid AND audf15.udfname = 'Yield (Mreads)'), 
containerplacement, 
container, 
artifact_sample_map, 
sample 
LEFT OUTER JOIN sample_udf_view as sudf1 on (sudf1.sampleid=sample.sampleid AND sudf1.udfname = 'SLX Identifier')
LEFT OUTER JOIN sample_udf_view as sudf2 on (sudf2.sampleid=sample.sampleid AND sudf2.udfname = 'Library Type')
LEFT OUTER JOIN sample_udf_view as sudf3 on (sudf3.sampleid=sample.sampleid AND sudf3.udfname = 'Index Type')
LEFT OUTER JOIN sample_udf_view as sudf4 on (sudf4.sampleid=sample.sampleid AND sudf4.udfname = 'Average Library Length')
LEFT OUTER JOIN sample_udf_view as sudf5 on (sudf5.sampleid=sample.sampleid AND sudf5.udfname = 'Billing Information')
LEFT OUTER JOIN sample_udf_view as sudf6 on (sudf6.sampleid=sample.sampleid AND sudf6.udfname = 'Priority Status'),
project, 
researcher, 
lab 
LEFT OUTER JOIN entity_udf_view as ludf1 on (lab.labid=ludf1.attachtoid AND ludf1.udfname='External')
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
AND artifact.luid=publishing.artifactluid
AND sample.processid=accept.sampleid
AND sample.name NOT LIKE 'Genomics Control%'
AND project.name != 'Controls'
-- GROUP BY -----------------------------------------------------------------------
GROUP BY researcher, lab, institute, slxid, runtype, requested_runtype, billable, billingmonth, flowcellid, lane, flowcellbillingcomments, billingcomments, runfolder,
instrument, submissiondate, acceptancedate, sequencingdate, publishingdate, billingdate, accept2publishdays, billing_code, library_type, index_type, 
priority_status, yield_pf_r1, avg_q_score_r1, percent_bases_q30_r1, yield, percent_lost_reads, cluster_density_r1, percent_pf_r1, intensity_cycle_1_r1, 
percent_intensity_cycle_20_r1, percent_phasing_r1, percent_prephasing_r1, percent_aligned_r1, percent_error_rate_r1, external
-- ORDER BY -----------------------------------------------------------------------
ORDER BY billable, flowcellid, lane

