#!/bin/bash
filenames=rand_ppkt_list.txt
for file in $(cat $filenames)
do
    cp /home/leonardo/Desktop/programs/bih/code/OntoGPT/multilingualGPT/malco/inputdir/phenopacket-store/*/$file ./phenopacket-store/
done;
