#!/usr/bin/env python
import sys
import pygeneann
import sequtils
import pysam
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('cff_file', action='store', help='CFF file, can be .cff or cff.reann')
parser.add_argument('ensbed', action='store', help='Ensemble gene file')
parser.add_argument('ref_fa', action='store', help='Reference genome file')

args = parser.parse_args()

gene_ann = pygeneann.GeneAnnotation(args.ensbed)
	
ref = pysam.FastaFile(args.ref_fa)
seq_dict ={}
for line in open(args.cff_file, "r"):
	fusion = pygeneann.CffFusion(line)

        gene1 = fusion.reann_gene1
        gene2 = fusion.reann_gene2
        lib = fusion.library
        fusion_id = fusion.fusion_id
	
	#print fusion.tostring()

	#fusion.check_codon(gene_ann, ref_fa)
	head_seqs = pygeneann.build_transcript_and_fusion_seq(gene_ann, fusion.reann_gene1, ref, fusion.pos1, "head")
	tail_seqs = pygeneann.build_transcript_and_fusion_seq(gene_ann, fusion.reann_gene2, ref, fusion.pos2, "tail")
	if not head_seqs or not tail_seqs:
		continue
	# build head gene transcript ref
	trans_seqs = set([(t[0], t[1]) for t in head_seqs])
	ref_id = 0
	for trans_seq1, trans_seq2 in trans_seqs:
		#print "TR:", trans_seq1, trans_seq2
		bp_pos = len(trans_seq1)
		trans_seq = trans_seq1 + trans_seq2
		key = gene1 + "_" + gene2
		if not key in seq_dict or not trans_seq in seq_dict[key]:
			ref_id += 1
			seq_dict.setdefault(key, []).append(trans_seq)
			print ">" + gene1 + "_" + gene2 + "_TRANS_" + fusion_id + "_" + str(ref_id) + "_" + str(bp_pos)
			print trans_seq
		

	# build fusion ref
	fusion_seqs1 = set([t[2] for t in head_seqs])
	fusion_seqs2 = set([t[2] for t in tail_seqs])
	ref_id = 0
	for fusion_seq1 in fusion_seqs1:
		for fusion_seq2 in fusion_seqs2:
			ref_id += 1
			fusion_seq = fusion_seq1 + fusion_seq2
			#print "FU:", fusion_seq1, fusion_seq2
			bp_pos = len(fusion_seq1)
			print ">" + gene1 + "_" + gene2 + "_FUSION_" + fusion_id + "_" + str(ref_id) + "_" + str(bp_pos)
			print fusion_seq