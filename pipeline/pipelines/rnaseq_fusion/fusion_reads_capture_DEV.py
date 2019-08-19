#!/usr/bin/env python

################################################################################
# Copyright (C) 2014, 2015 GenAP, McGill University and Genome Quebec Innovation Centre
#
# This file is part of MUGQIC Pipelines.
#
# MUGQIC Pipelines is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MUGQIC Pipelines is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with MUGQIC Pipelines.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

# Python Standard Modules
import argparse
import collections
import logging
import os
import re
import sys

# Append mugqic_pipelines directory to Python library path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(sys.argv[0])))))

# MUGQIC Modules
from core.config import *
from core.job import *
from core.pipeline import *
from bfx.design import *
from bfx.readset import *

from bfx import bedtools
from bfx import cufflinks
from bfx import differential_expression
from bfx import gq_seq_utils
from bfx import htseq
from bfx import metrics
from bfx import picard
from bfx import samtools
from bfx import star
from bfx import bvatools
from bfx import rmarkdown
from pipelines import common

from bfx import defuse
from bfx import fusionmap
from bfx import tophat2
from bfx import integrate
from bfx import ericscript
from bfx import gunzip
from bfx import cff_conversion
from bfx import merge_and_reannotate_cff_fusion
from bfx import samtools_1_1

# READS CAPTURE BFX
from bfx import filter_caputred_reads_DEV as filter_caputred_reads
from bfx import fusion_reads_capture_results_sum_DEV as fusion_reads_capture_results_sum
from bfx import build_fusion_and_head_gene_ref_DEV as build_fusion_and_head_gene_ref
from bfx import bwa_fusion_reads_capture_DEV as bwa_fusion_reads_capture
from bfx import extract_captured_reads_and_realn

import utils

log = logging.getLogger(__name__)

class FusionReadsCapture(common.Illumina):
    """
    """

    def __init__(self):
        # Add pipeline specific arguments
        self.argparser.add_argument("-d", "--design", help="design file", type=file)

        self.argparser.add_argument("--cff", help="cff file", type=file)
        self.argparser.add_argument("--sampleinfo", help="sample info file", type=file)

        super(FusionReadsCapture, self).__init__()


## fusion reads capture pipeline
    def build_fusion_and_head_gene_ref(self):
        """
        Build fusion reference together with the head gene's all transcripts sequences
        """
        
        jobs = []
        cff_file = self.args.cff.name
        out_dir = os.path.join("fusion_reads_capture", "fusion_refs")

        build_job = build_fusion_and_head_gene_ref.build_fusion_and_head_gene_ref(cff_file, out_dir)
        job = concat_jobs([
            Job(command="mkdir -p " + out_dir),
            build_job    
        ], name="build_fusion_and_head_gene_ref")

        jobs.append(job)
        return jobs

    def fastq_conversion_and_reads_capture(self):
        """
        Coert cram2.0 file to fastq file with samtools1.1 and picard
        """
        jobs = []
        cff_file = self.args.cff.name
        cram_file = self.args.cff.name
        #out_dir = os.path.join("fusion_reads_capture", "cram_fastq")
        for readset in self.readsets:
            out_dir = os.path.join("fusion_reads_capture", "captured_bam", readset.sample.name)
            if not readset.fastq1:
                if readset.cram:
                    # convert cram to bam then to fastq, fastq and bam are saved on localhd
                    out_bam = os.path.join("$TMPDIR", os.path.basename(readset.cram)+".bam")
                    fastq1 = out_bam + ".1.fastq"
                    fastq2 = out_bam + ".2.fastq"
                    #cram2bam_job = samtools_1_1.view(readset.cram, out_bam, "convert_cram_to_fastq")
                    cram2bam_job = samtools_1_1.view(readset.cram, out_bam)
                    bam2fastq_job = picard.sam_to_fastq(out_bam, fastq1, fastq2)

                    # bwa aln fastqs to capture reference
                    out_bam = os.path.join(out_dir, "captured.bam")
                    ref = os.path.join("fusion_reads_capture", "fusion_refs", os.path.basename(cff_file)+".fa")
                    capture_job = bwa_fusion_reads_capture.bwa_fusion_reads_capture(fastq1, fastq2, ref, out_bam, read_group=None, ini_section='bwa_fusion_reads_capture')

                    job = concat_jobs([
                        Job(command="mkdir -p " + out_dir),
                        cram2bam_job,
                        bam2fastq_job,
                        capture_job
                    ], name="fastq_conversion_and_reads_capture")
                    #], name="fastq_conversion_and_reads_capture"+readset.sample.name)
                                        # manually set I/O for job
                                        job._input_files = [readset.cram]
                                        job._output_files = [out_bam]

                    jobs.append(job)

                else:
                    raise Exception("Error: CRAM file not available for readset \"" + readset.name + "\"!")
            else:
                fastq1 = readset.fastq1
                fastq2 = readset.fastq2

                # bwa aln fastqs to capture reference
                out_bam = os.path.join(out_dir, "captured.bam")
                ref = os.path.join("fusion_reads_capture", "fusion_refs", os.path.basename(cff_file)+".fa")
                capture_job = bwa_fusion_reads_capture.bwa_fusion_reads_capture(fastq1, fastq2, ref, out_bam, read_group=None, ini_section='bwa_fusion_reads_capture')

                job = concat_jobs([
                    Job(command="mkdir -p " + out_dir),
                    capture_job
                ], name="bwa_fusion_reads_capture."+readset.sample.name)
                
                jobs.append(job)

        return jobs
        
        
#    def bwa_fusion_reads_capture(self):
#        """
#        BWA mem aln reads to fusion references
#        """
#        
#        jobs = []
#        
#
#        for readset in self.readsets:
#            input_dir = os.path.join("fusions", "gunzip_fastq", readset.sample.name)
#            if readset.fastq1 and readset.fastq2:
#                fastq1 = os.path.join(input_dir, os.path.basename(os.path.splitext(readset.fastq1)[0]))
#                fastq2 = os.path.join(input_dir, os.path.basename(os.path.splitext(readset.fastq2)[0]))
#            elif readset.cram:            
#                fastq_dir = os.path.join("fusion_reads_capture", "cram_fastq")
#                cram_name = os.path.basename(readset.cram)
#                fastq1 = os.path.join(fastq_dir, cram_name + ".bam.1.fastq")
#                fastq2 = os.path.join(fastq_dir, cram_name + ".bam.2.fastq")
#
#            cff_file = self.args.cff.name
#            out_dir = os.path.join("fusion_reads_capture", "captured_bam", readset.sample.name)
#            out_bam = os.path.join(out_dir, "captured.bam")
#            ref = os.path.join("fusion_reads_capture", "fusion_refs", os.path.basename(cff_file)+".fa")
#            capture_job = bwa_fusion_reads_capture.bwa_fusion_reads_capture(fastq1, fastq2, ref, out_bam, read_group=None, ini_section='bwa_fusion_reads_capture')
#        
#            job = concat_jobs([
#                Job(command="mkdir -p " + out_dir),
#                capture_job,
#            ], name="bwa_fusion_reads_capture."+readset.sample.name)
#            jobs.append(job)
#        return jobs
    
    def extract_captured_reads_and_realn(self):
        """
        BWA mem realign captured reads to hg + transcript junction references
        """
        
        jobs = []
        for readset in self.readsets:

            captured_bam = os.path.join("fusion_reads_capture", "captured_bam", readset.sample.name, "captured.bam")
            out_dir = os.path.join("fusion_reads_capture", "realigned_bam", readset.sample.name)
            out_bam = os.path.join(out_dir, "realigned.bam")
            
            realign_job = extract_captured_reads_and_realn.extract_captured_reads_and_realn(captured_bam, out_bam, ini_section='extract_captured_reads_and_realn')
        
            job = concat_jobs([
                Job(command="mkdir -p " + out_dir),
                realign_job    
            ], name="extract_captured_reads_and_realn."+readset.sample.name)
            jobs.append(job)
        return jobs
    
    def filter_caputred_reads(self):
        """
        Compare capture alignment and realignment, print filtered fusion reads alignment and count summary
        """
        
        jobs = []
        for readset in self.readsets:
            sample_info_file = os.path.abspath(self.args.sampleinfo.name)

            out_dir = os.path.join("fusion_reads_capture", "filtered_result", readset.sample.name)
            captured_bam = os.path.join("fusion_reads_capture", "captured_bam", readset.sample.name, "captured.bam")
            realigned_bam = os.path.join("fusion_reads_capture", "realigned_bam", readset.sample.name, "realigned.bam")
            if readset.cram:
                filter_job = filter_caputred_reads.filter_caputred_reads(captured_bam, realigned_bam, os.path.basename(readset.cram), sample_info_file, out_dir, ini_section='filter_caputred_reads')
            elif readset.fastq1:
                filter_job = filter_caputred_reads.filter_caputred_reads(captured_bam, realigned_bam, readset.sample.name, sample_info_file, out_dir, ini_section='filter_caputred_reads')
            job = concat_jobs([
                Job(command="mkdir -p " + out_dir),
                filter_job    
            ], name="filter_caputred_reads."+readset.sample.name)
            jobs.append(job)
        return jobs
    def merge_and_summary(self):
        """
        Merge the results, extract summaries and get the statistics
        """
        
        jobs = []
        out_dir = os.path.join("fusion_reads_capture", "merged_summary_stats")
        sum_files = [os.path.join("fusion_reads_capture", "filtered_result", sample.name, "aln_and_summary") for sample in self.samples]
        sum_job = fusion_reads_capture_results_sum.merge_and_summary(sum_files, out_dir)
        job = concat_jobs([
            Job(command="mkdir -p " + out_dir),
            sum_job
        ], name="merge_and_summary")

        jobs.append(job)
        return jobs
        
    @property
    def steps(self):
        return [
            self.build_fusion_and_head_gene_ref,
            self.fastq_conversion_and_reads_capture,
            self.extract_captured_reads_and_realn,
            self.filter_caputred_reads,
            self.merge_and_summary
        ]

if __name__ == '__main__':
    FusionReadsCapture()
