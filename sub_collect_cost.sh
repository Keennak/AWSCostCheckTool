#!/usr/bin/env bash
#
# HD Security Accessment Collector
#
# IAM collector
#
# -----------------------------------------------------------
SDA_REGION=${TARGET_REGION}

# The script creates directories and logs with this tag
SDA_TAG=COST

mkdir ${RESULT_DIR}/${SDA_TAG}
cd ${RESULT_DIR}/${SDA_TAG}

# cost 01
# Trusted Advisorの結果を取得する。Trusted AdvisorはGlobalサービスなので、us-east-1で実施する。
SDA_REGION="us-east-1"
caws "COST01" "support" "describe-trusted-advisor-checks" "--language en"

# cost 02
# costの結果を取得する。
aws support describe-trusted-advisor-checks \
    --region us-east-1 \
    --language en \
    --query 'checks[].[category,id,name]' \
    --output text |grep -e "^cost_optimizing" \
    |while read category id name ; do

        name=$(echo $name |sed -e 's/ /_/g')
        caws "COST02_${name}" "support" "describe-trusted-advisor-check-result" "--check-id  ${id}" 
    done

# 以下のchecksに関してタグを取得する。
    # Low_Utilization_Amazon_EC2_Instance
    # Underutilized_Amazon_EBS_Volumes
    # Unassociated_Elastic_IP_Addresses
    # Idle_Load_Balancers
    # Amazon_RDS_Idle_DB_Instances

# cost 03
#　Low_Utilization_Amazon_EC2_Instance
cat *Low_Utilization_Amazon_EC2_Instance* \
    |jq -r '.result.flaggedResources[].region' \
    |sort -u \
    |while read region; do
        SDA_REGION=${region}
        caws "COST03" "ec2" "describe-instances" ""
    done

# cost 04
#　Underutilized_Amazon_EBS_Volumes
cat *Underutilized_Amazon_EBS_Volumes* \
    |jq -r '.result.flaggedResources[].region' \
    |sort -u \
    |while read region; do
        SDA_REGION=${region}
        caws "COST04" "ec2" "describe-volumes" ""
    done

# cost 05
# Unassociated_Elastic_IP_Addresses
cat *Unassociated_Elastic_IP_Addresses* \
    |jq -r '.result.flaggedResources[].region' \
    |sort -u \
    |while read region; do
        SDA_REGION=${region}
        caws "COST05" "ec2" "describe-addresses" ""
    done

# cost 06
# Idle_Load_Balancers
cat *Idle_Load_Balancers* \
    |jq -r '.result.flaggedResources[].region' \
    |sort -u \
    |while read region; do
        SDA_REGION=${region}
        caws "COST06" "elbv2" "describe-load-balancers" ""
        aws elbv2 describe-load-balancers --query LoadBalancers[].LoadBalancerArn --output text |while read arn ; do
            name=$(basename ${arn})
            caws "COST06_${name}" "elbv2" "describe-tags" "--resource-arns ${arn}"
        done
    done

# cost 07
# Amazon_RDS_Idle_DB_Instances
cat *Amazon_RDS_Idle_DB_Instances* \
    |jq -r '.result.flaggedResources[].region' \
    |sort -u \
    |while read region; do
        SDA_REGION=${region}
        caws "COST07" "rds" "describe-db-instances" ""
    done

# END
echo "FINISHED ${SDA_TAG}"
cd -