#!/usr/bin/env bash
#
# AWS Cost Check Tool

# Common

usage() {
    echo "USAGE"
    echo "    ./create_report.sh <json file directory>"
    echo "    example:"
    echo "       ./create_report.sh ./results/SAK_20200325-163924"
    echo ""
}

crete_result_directory() {
    current_dir=$(pwd)
    RESULT_DIR=${current_dir}/report/$(basename ${1})
    mkdir -p ${RESULT_DIR}
}

# main

if [ $# != 1 ]; then
    usage
    exit 1
fi
crete_result_directory ${1}
BIN_DIR=$(dirname ${0})
INPUT_DIR=${1}

# create report

> ${RESULT_DIR}/cost_report.md


# create COST report
echo "create_report_cost started"
${BIN_DIR}/sub_create_report_cost.py ${INPUT_DIR} --output ec2ta --format json > ${RESULT_DIR}/cost_report_ec2ta.json
${BIN_DIR}/sub_create_report_cost.py ${INPUT_DIR} --output ebsta --format json > ${RESULT_DIR}/cost_report_ebsta.json
${BIN_DIR}/sub_create_report_cost.py ${INPUT_DIR} --output ec2all --format json > ${RESULT_DIR}/cost_report_ec2all.json
${BIN_DIR}/sub_create_report_cost.py ${INPUT_DIR} --output ebsall --format json > ${RESULT_DIR}/cost_report_ebsall.json
${BIN_DIR}/sub_create_report_cost.py ${INPUT_DIR} --output ec2ta --format tsv > ${RESULT_DIR}/cost_report_ec2ta.tsv
${BIN_DIR}/sub_create_report_cost.py ${INPUT_DIR} --output ebsta --format tsv > ${RESULT_DIR}/cost_report_ebsta.tsv
${BIN_DIR}/sub_create_report_cost.py ${INPUT_DIR} --output ec2all --format tsv > ${RESULT_DIR}/cost_report_ec2all.tsv
${BIN_DIR}/sub_create_report_cost.py ${INPUT_DIR} --output ebsall --format tsv > ${RESULT_DIR}/cost_report_ebsall.tsv
echo "create_report_cost created. Report: ${RESULT_DIR}/*.json, *.tsv"