#!/bin/sh


# ../../crf_learn -c 10.0 templates/template01 train.data model
model/crf_test  -m model/crf/model model/crf/test.data > model/crf/output1.txt

