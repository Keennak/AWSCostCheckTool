#!/usr/bin/env bash
#
# AWS Cost Check Tool
# Collecter
#
# usage
usage() {
    echo "USAGE"
    echo "    ./collect.sh <region name>  [<profile name>]"
    echo "    example:"
    echo "       ./collect.sh us-west-2 myProfile"
    echo ""
}

# check input
case $# in
  1 ) 
    aws sts get-caller-identity --region ${1} > /dev/null 2>&1
    if [ $? != 0 ]; then
      usage
      exit 1
    fi
    TARGET_REGION=${1}
    TARGET_PROFILE=""
  ;;
  2 )
    aws sts get-caller-identity --region ${1} --profile ${2} > /dev/null 2>&1
    if [ $? != 0 ]; then
      usage
      exit 1
    fi
    TARGET_REGION=${1}
    TARGET_PROFILE=${2}
  ;;
  * ) 
    usage
    exit 1
  ;;
esac

echo TARGET_PROFILE: ${TARGET_PROFILE}

# caws command
# usage:
#  caws <AWS Service Name> <CLI_COMMAND> "<PARAMETER>"
caws() {
  SDA_ID=${1}
  SDA_SERVICE=${2}
  SDA_COMMAND=${3}
  SDA_PARAM=${4}

  echo aws ${SDA_SERVICE} ${SDA_COMMAND} --region ${SDA_REGION} ${SDA_PARAM}
  aws ${SDA_SERVICE} ${SDA_COMMAND} --region ${SDA_REGION} ${SDA_PARAM} >>${SDA_ID}_${SDA_COMMAND}_${SDA_REGION}.json
}

set_profile(){
  if [ -n "${TARGET_PROFILE}" ]; then
    # check profile is user or role
    type=$(aws sts get-caller-identity --query Arn --output text --profile ${TARGET_PROFILE} |cut -d ":" -f 6| cut -d "/" -f 1)
    case ${type} in
      'assumed-role' )
        role_arn="$(aws configure get role_arn --profile ${TARGET_PROFILE})"
        tokens=$(aws sts assume-role --role-arn ${role_arn} --role-session-name "AssessmentKit" --query Credentials)
      ;;
      'user' )
        tokens=$(aws sts get-session-token --profile ${TARGET_PROFILE} --query Credentials)
        id=
      ;;
      * )
        echo ${id} 
        exit 1
      ;;
    esac

    export AWS_ACCESS_KEY_ID=`echo $tokens     |jq -r .AccessKeyId`
    export AWS_SECRET_ACCESS_KEY=`echo $tokens |jq -r .SecretAccessKey`
    export AWS_SESSION_TOKEN=`echo $tokens     |jq -r .SessionToken`
    
    echo "Collected by $(aws sts get-caller-identity --query Arn --output text)"

    else
      echo "Collect by current credentials"

  fi
}

# COMMON Environment variable
#
# Specify the region to be surveyed.
# Security services settings are surveyed in all region regardless of this setting.
SDA_REGION=${TARGET_REGION}

CURRENT_DIR=$(pwd)
COMMAND_DIR=$(dirname ${0})
RESULT_DIR=./result/SAK_$(date "+%Y%m%d-%H%M%S")
mkdir -p ${RESULT_DIR}

# Run collector for each service

# use role in profile
set_profile


. ${COMMAND_DIR}/sub_collect_cost.sh 2>&1 | tee ${RESULT_DIR}/COST.log      # Cost from TrustedAdvisor

# Archive the result files and delete the temporary files

echo "FINISHED result file : ${RESULT_DIR}"

# END
