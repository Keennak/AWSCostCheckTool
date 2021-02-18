#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import re
from pathlib import Path
import sys

import pprint

# common

# ---------------------------------------------------------
# get_value_from_key_value_dict
# extract value from specified Key.
# usage get_value_from_key_value_dict(dictionary, key)
#
# example
#    get_value_from_key_value_dict(d, Name) -> MainDISK
#      from dictionary below
#      { Key : Name, Value: MainDISK },{ Key : SIZE, Value : 1GB }
def get_value_from_key_value_dict(d, val):
    for t in d:
        if ([v for k, v in t.items() if v == val]):
            return(t.get('Value'))
# ---------------------------------------------------------

# Input JSON directory
args = sys.argv
dir = args[1] + '/COST'
p = Path(dir)



# print header
print('# Security Deep Assessment (COST）')

# ---------------------------------------------
# 共通関数
# ---------------------------------------------

# get reion list from file name (not aws)
def get_regions():
    file_names = os.listdir(p)
    regions = set()
    for file_name in file_names:
        region = re.search('[^_]*.json', file_name)
        regions.add(file_name[region.start(): region.end()-5])
    regions = list(regions)
    return regions

# 結果ファイルからリソースオブジェクトを収集する
def get_resource_object(command, region):
    for f in list(p.glob('*'+command+'_'+region+'.json')):
        with open(f) as j:
            resource_object = json.load(j)
            return resource_object


def get_loadbalancer_ids(region):
    file_names = os.listdir(p)
    lb_ids = set()
    for file_name in file_names:
        lb_id = re.search(
            '_[a-f0-9]+_describe-load-balancer-attributes_'+region+'.json', file_name)
        if lb_id != None:
            lb_ids.add(file_name[6:22])
    lb_ids = list(lb_ids)
    return lb_ids


def get_check_headers():
    d = {}
    for f in list(p.glob('*describe-trusted-advisor-checks*')):
        with open(f) as j:
            d = json.load(j)
            for k in d['checks']:
                # check_headers[k.get('id')] = []
                # check_headers[k.get('id')].append(k.get('metadata'))
                check_headers[k.get('id')] = k.get('metadata')

def get_instance_tags(region):
    d ={}
    if ec2_instances[region] is not None:
        for k in ec2_instances[region].get('Reservations'):
            for k2 in k['Instances']:
                d[k2.get('InstanceId')] =[]
                d[k2.get('InstanceId')].append(k2.get('Tags')) 
    return d

def get_volume_tags(region):
    d ={}
    if ebs_volumes[region] is not None:
        for k in ebs_volumes[region].get('Volumes'):
            d[k.get('VolumeId')] =[]
            d[k.get('VolumeId')].append(k.get('Tags')) 
    return d

def get_eip_tags(region):
    d ={}
    if elastic_ips[region] is not None:
        for k in elastic_ips[region].get('Addresses'):
            d[k.get('PublicIp')] =[]
            d[k.get('PublicIp')].append(k.get('Tags')) 
    return d

def get_rds_tags(region):
    d ={}
    if rds_instances[region] is not None:
        for k in rds_instances[region].get('DBInstances'):
            d[k.get('DBInstanceIdentifier')] =[]
            d[k.get('DBInstanceIdentifier')].append(k.get('TagList')) 
    return d

def get_flagged_resources(command, tag_dict):
    # 引数で指定されたTrusted AdvisorのCOST結果ファイルから、検出されたリソースのメタデータを取得し、
    # tag_dictから得たTAG情報をJOINします。
    # JOINしたメタデータ配列（LIST型）を返却します。
    # (1) Get detected resource metadata by Trusted Advisor Cost check that specified with an argument.
    # (2) JOIN tag infomation and metadata. tag is described in tag_dict.
    # (3) retuen metadatas (list)  
    metadatas = []
    d = {}
    for f in list(p.glob('*'+command+"*")):
        with open(f) as j:
            d = json.load(j)
            check_id = d.get('result').get('checkId')
            
            # create header
            header = check_headers.get(check_id)
            header.append('Tags')
            metadatas.append(header)

            # create records
            for k in d.get('result')['flaggedResources']:
                region=k.get('region')
                metadata=k.get('metadata')
                try:
                    id=metadata[1]
                    metadata.extend(tag_dict[region].get(id))
                    metadatas.append(metadata)
                except TypeError:
                    metadata.append('None - This instance may be deleted.')
                    metadatas.append(metadata)

    return metadatas

def print_markdown(output_list, title):
    print('  ')
    print('## ' + title )
    for row in range(len(output_list)):
        for n in range(len(output_list[row])):
            print('| ', end='')
            print(output_list[row][n], end=' ')
        print('|')

        if row == 0:
            for n in range(len(output_list[row])):
                print('| ', end='')
                print( ' :--- ', end='')
            print('|')
    print('  ')
    print('  ')
    

# init resource objects
ec2_instances = {}
ec2_instance_tags = {}
instance_dict = {}

ebs_volumes = {}
ebs_volume_tags = {}

elastic_ips = {}
elastic_ip_tags = {}

rds_instances = {}
rds_instance_tags = {}

loadbalancers = {}
loadbalancer_tags = {}

check_headers = {}

# set resource objects for detected region
#
# get regions collected in the files
regions = get_regions()
#
for region in regions:
    # EC2 instance
    ec2_instances[region] = get_resource_object('describe-instances', region)
    ec2_instance_tags[region] = get_instance_tags(region)

    # EBS volumes
    ebs_volumes[region] = get_resource_object('describe-volumes', region)
    ebs_volume_tags[region] = get_volume_tags(region)

    # EIP
    elastic_ips[region] = get_resource_object('describe-addresses', region)
    elastic_ip_tags[region] = get_eip_tags(region)

    # RDS
    rds_instances[region] = get_resource_object('describe-db-instances', region)
    rds_instance_tags[region] = get_rds_tags(region)    

    # ELB
    loadbalancers[region] = {}
    loadbalancer_ids = get_loadbalancer_ids(region)
    for lb_id in loadbalancer_ids:
        loadbalancers[region][lb_id] = get_resource_object(
            lb_id+'_describe-load-balancer-attributes', region)

# ------------------------------
# create report
# ------------------------------
# (1) Create header
get_check_headers()

# (2) create Low_Utilization_Amazon_EC2_Instances report
ec2_flagged_instances = get_flagged_resources('Low_Utilization_Amazon_EC2_Instances', ec2_instance_tags)
print_markdown(ec2_flagged_instances, 'Low_Utilization_Amazon_EC2_Instances')

# (3) create Underutilized_Amazon_EBS_Volumes report
ebs_flagged_volumes = get_flagged_resources('Underutilized_Amazon_EBS_Volumes', ebs_volume_tags)
print_markdown(ebs_flagged_volumes, 'Underutilized_Amazon_EBS_Volumes')

# (4) create Unassociated_Elastic_IP_Addresses report
ec2_flagged_ips = get_flagged_resources('Unassociated_Elastic_IP_Addresses', elastic_ip_tags)
print_markdown(ec2_flagged_ips, 'Unassociated_Elastic_IP_Addresses')

# (5) create RDS_Idle_DB_Instances report
rds_flagged_instances = get_flagged_resources('RDS_Idle_DB_Instances', rds_instance_tags)
print_markdown(rds_flagged_instances, 'RDS_Idle_DB_Instances')

print('# CSV Files')

# (6) create Low_Utilization_Amazon_EC2_Instances report 2
# Extract Ultra Low Utilization EC2 Instance from ec2_flagged_instances dictionary
#
# Extraction condition
#   CPU utils are equal or less than 1.0% for all days. 
#   If there is a day with no data, that instance will not be extracted.
#
def get_ultralow_instances(t2):
    t1 = []
    # new header
    t1.append(['Region/AZ', 'Instance ID', 'Instance Name', 'Instance Type', 'Estimated Monthly Savings', 'Day 1 CPU', 'Day 1 NW', 'Day 2 CPU', 'Day 2 NW', 'Day 3 CPU', 'Day 3 NW', 'Day 4 CPU', 'Day 4 NW', 'Day 5 CPU', 'Day 5 NW', 'Day 6 CPU', 'Day 6 NW', 'Day 7 CPU', 'Day 7 NW', 'Day 8 CPU', 'Day 8 NW', 'Day 9 CPU', 'Day 9 NW', 'Day 10 CPU', 'Day 10 NW', 'Day 11 CPU', 'Day 11 NW', 'Day 12 CPU', 'Day 12 NW', 'Day 13 CPU', 'Day 13 NW', 'Day 14 CPU', 'Day 14 NW', '14-Day Average CPU Utilization', '14-Day Average Network I/O', 'Number of Days Low Utilization', 'Tags', 'Service', 'Very Low'])
    # content
    for row in t2[1:]:
        is_very_low = True
        t1.append([])
        for i in range(4):
            t1[-1].append(row[i])
        t1[-1].append(float(row[4][1:]))
        for i in range(5,19):
            cpu = ""
            nw = ""
            if row[i]!=None:
                cpu = float(row[i].split('%')[0])
                if cpu > 1.0:
                    is_very_low = False
                nw = float(row[i].split()[1][:-2])
            else:
                is_very_low = False
            t1[-1].append(cpu)
            t1[-1].append(nw)
        t1[-1].append(float(row[19][:-1]))
        t1[-1].append(float(row[20][:-2]))
        t1[-1].append(int(row[21][:-5]))
        t1[-1].append(row[22])
        service_tag = None
        for kv in row[-1]:
            if kv['Key'] == 'Service':
                service_tag = kv['Value']
        t1[-1].append(service_tag)
        t1[-1].append(is_very_low)

    return t1

# create dictionary
ec2_ultralow_instances = []
ec2_ultralow_instances = get_ultralow_instances(ec2_flagged_instances)
pprint.pprint(ec2_ultralow_instances)

### EBS

print('## EBS')
# print(ebs_flagged_volumes)

### EBS NEW

ebs_flagged_volumes_new = []
# header
ebs_flagged_volumes_new.append(ebs_flagged_volumes[0])
ebs_flagged_volumes_new[0].append("Service")
# data
for row in ebs_flagged_volumes[1:]:
    print(row)
    ebs_flagged_volumes_new.append([])
    for col in row:
        ebs_flagged_volumes_new[-1].append(col)
    ebs_flagged_volumes_new[-1][5] = float(ebs_flagged_volumes_new[-1][5][1:])
    service_tag = None
    for kv in row[-1]:
        if kv['Key'] == 'Service':
            service_tag = kv['Value']
    ebs_flagged_volumes_new[-1].append(service_tag)



pprint.pprint(ebs_flagged_volumes_new)

