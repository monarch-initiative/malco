#!/bin/bash
filenames=rand_ppkt_list.txt
for file in $(cat $filenames)
do
    cp /Users/leonardo/data/phenopacket-store/*/$file ./phenopacket-store/
done;
