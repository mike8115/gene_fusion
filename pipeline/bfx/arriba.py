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
import os

# MUGQIC Modules
from core.config import *
from core.job import *
#['run_arriba', 'module_arriba'],
def run(fastqs1, fastqs2, output_dir):
    output_file = os.path.join(output_dir, "fusions.tsv")
    return Job(
        fastqs1,
        [output_file],
        [
            ['run_arriba', 'module_star'],
	        ['run_arriba', 'module_samtools']
        ],

        command="""\
/hpf/largeprojects/ccmbio/mapostolides/MODULES/arriba_v1.2.0/run_arriba.sh \\
      {genome_build} \\
      {gene_annot} \\
      {reference} \\
      {blacklist} \\
      {fastq1} \\
      {fastq2} \\
      {threads}""".format(
            genome_build=config.param('run_arriba', 'genome_build'),
            gene_annot=config.param('run_arriba', 'gene_annot'),
            reference=config.param('run_arriba', 'reference'),
            blacklist=config.param('run_arriba', 'blacklist'),
            threads=config.param('run_arriba', 'threads', type='posint'),
            options=config.param('run_arriba', 'options'),
            fastq1=",".join(fastq1 for fastq1 in fastqs1),
            fastq2=",".join(fastq2 for fastq2 in fastqs2),
        ),
    )
