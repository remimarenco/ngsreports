-- --------------------------------------------------------------------------------
-- BILLING QUERY - latest version 31-Jan-2014
-- against genologics database v2.5.2.367 http://genologics.com/
-- 31/01/14: add two new UDFs % lost reads and yield
-- 21/01/14: add avg library length as it can be different over samples in pool
--           add fields Library Type; Index Type & Average Library Length
-- 02/07/13: first versions
-- --------------------------------------------------------------------------------

SELECT distinct
researcher.firstname || ' ' || researcher.lastname as researcher, 
lab.name as lab, 
address.institution as institute,
sudf1.udfvalue as slxid, 
itype.name || '_' || case when itype.name = 'Miseq' then split_part(pudf6.udfvalue, '-', 2) else case when pudf2.udfvalue is null then 'SE' else 'PE' end || pudf1.udfvalue end as runtype,
audf1.udfvalue as billable, 
to_char(process.daterun, 'YYYY-MM') as billingmonth, 
pudf4.udfvalue as flowcellid, 
'Lane' || containerplacement.wellyposition + 1 as lane, 
bpudf1.udfvalue as flowcellbillingcomments,
audf2.udfvalue as billingcomments,
pudf5.udfvalue as runfolder, 
instrument.name as instrument,
to_char(sample.datereceived, 'YYYY-MM-DD') as submissiondate,
to_char(to_date(pudf3.udfvalue, 'YYYY-MM-DD'), 'YYYY-MM-DD') as completiondate, 
sudf2.udfvalue as library_type,
sudf3.udfvalue as index_type,
to_char(avg(to_number(sudf4.udfvalue, '99999')), '9999.99') as avg_library_length,
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

FROM process 
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
LEFT OUTER JOIN sample_udf_view as sudf4 on (sudf4.sampleid=sample.sampleid AND sudf4.udfname = 'Average Library Length'),
project, 
researcher, 
lab LEFT OUTER JOIN entity_udf_view as ludf1 on (lab.labid=ludf1.attachtoid AND ludf1.udfname='External')
LEFT OUTER JOIN address on (lab.billingaddressid=address.addressid), 
-- billing process
process as bprocess LEFT OUTER JOIN process_udf_view as bpudf1 on (bpudf1.processid=bprocess.processid AND bpudf1.udfname = 'Flowcell Billing Comments') ,
processtype as bprocesstype,
processiotracker as bprocessiotracker,
artifact as bartifact

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
--AND ludf1.udfvalue='True'
AND artifact.luid IN ( 
	SELECT sub_artifact.luid
	FROM processiotracker as sub_processiotracker, process as sub_process, processtype as sub_processtype, artifact as sub_artifact
	WHERE sub_processiotracker.processid=sub_process.processid 
	AND sub_process.typeid=sub_processtype.typeid 
	AND sub_processtype.displayname='Billing' 
	AND sub_processiotracker.inputartifactid=sub_artifact.artifactid 
	AND sub_process.daterun >= '2013-04-01' AND sub_process.daterun <= '2014-02-07'
) 
-- billing process
AND artifact.luid=bartifact.luid
AND bprocess.typeid = bprocesstype.typeid
AND bprocessiotracker.processid=bprocess.processid
AND bprocessiotracker.inputartifactid=bartifact.artifactid
AND bprocesstype.displayname='Billing'
GROUP BY researcher, lab, institute, slxid, runtype, billable, billingmonth, flowcellid, lane, flowcellbillingcomments, billingcomments, runfolder, instrument, submissiondate, completiondate, 
 library_type, index_type, yield_pf_r1, avg_q_score_r1, percent_bases_q30_r1, yield, percent_lost_reads, cluster_density_r1, percent_pf_r1, 
 intensity_cycle_1_r1, percent_intensity_cycle_20_r1, percent_phasing_r1, percent_prephasing_r1, percent_aligned_r1, percent_error_rate_r1, external
