#! /usr/bin/env python
""" The script to parse Terrafrom tfstate file and list the deployed asset information"""
from colorama import *
import json
import re
import argparse
import os
import sys


class tfstate:
    """Parse the tfstate file to return a dictionary"""

    def __init__(self, json_data):
        self.json_data = json_data

    def resource_type(self, dict):
        keys_list = list(dict.keys())
        temp_dict = {}
        for each_resource in keys_list:
            type = dict[each_resource]['type']
            resource_id = dict[each_resource]['primary']['id']
            temp_dict[resource_id] = {}
            if 'depends_on' in list(dict[each_resource].keys()):
                depend = dict[each_resource]['depends_on']
            attributes = dict[each_resource]['primary']['attributes']
            temp_dict[resource_id]['type'] = type
            temp_dict[resource_id]['attributes'] = attributes
        return temp_dict

    def get_aws_resources(self, json_data):
        no_of_modules = (self.json_data['modules'])
        final_dict2 = {}
        for i in no_of_modules:
            temp_dict = self.resource_type(i['resources'])
            final_dict2.update(temp_dict)
        return final_dict2


def get_args():
    """Parse the input arguments."""
    parser = argparse.ArgumentParser(description='List the\
                       AWS Resources by parsing the terraform \
                       tfstate file')
    parser.add_argument(
        '-v',
        '--verbose',
        help='Option for increasing verbosity',
        action="count", default=0)
    parser.add_argument(
        '-p',
        '--path',
        help='terraform tfstate file path')
    parser.add_argument(
        '-s',
        '--specific',
        help='specific lookup for a type of AWS resources; (comma separated for more than one resource types)'
    )
    parser.add_argument(
        '-i',
        '--resourceID',
        help='specific lookup based on resource IDs; (comma seperated for more than one resource IDs)'
    )
    args = parser.parse_args()
    path = args.path
    verbose = args.verbose
    specific = args.specific
    r_id = args.resourceID
    return verbose, path, specific, r_id


def print_resource_summary(final_dict2):
    """ Print resource summary """
    id_list = final_dict2.keys()
    type_list = [final_dict2[i]['type'] for i in id_list]
    type_dict = dict(zip(id_list, type_list))
    total_resource = len(type_list)
    c = [(i, type_list.count(i)) for i in set(type_list)]
    print Fore.GREEN + "\t\tFound %s amazon resources" % (str(total_resource))
    print Style.RESET_ALL
    for each_item in c:
        print pretty_print(each_item[0]), '->', each_item[1]
    return type_dict


def pretty_print(string):
    """ Pretty print the string """
    split1 = string.split('_')
    string2 = ' '.join(split1)
    return string2.title()


def print_instance_summary(final_dict):
    """ Print instance summary """
    id_list = final_dict.keys()
    print '\n'
    print Fore.GREEN + "\t\t\t\tAvailable Instances details"
    print Style.RESET_ALL
    for each in final_dict.keys():
        if re.match('aws_instance', final_dict[each]['type']):
            if 'tags.Name' in final_dict[each]['attributes']:
                print "\t\t\t" + Fore.GREEN + "%s - %s " % (pretty_print('aws_instance'), final_dict[each]['attributes']['tags.Name'])
                print Style.RESET_ALL
            print 'Instance Id       :', each
            print_level1_attributes(final_dict[each])
            print '\n'


def print_level1_attributes(dict):
    print 'Availabilty Zone  :', dict['attributes']['availability_zone']
    print 'Private IP        :', dict['attributes']['private_ip']
    print 'AMI Image         :', dict['attributes']['ami']


def print_level2_attributes(dict):
    """ Print level2 attributes """
    attributes = dict['attributes']
    for x in sorted(list(attributes.keys())):
        if attributes[x] == '' or re.search("#", x):
            del attributes[x]
    attributes_list = dict['attributes'].keys()
    for each_attri in attributes_list:
        print pretty_print(each_attri).ljust(40), " - " + dict['attributes'][each_attri].ljust(10)


def print_all(final_dict2):
    """ Print the verbose output """
    id_list = final_dict2.keys()
    type_list = [final_dict2[i]['type'] for i in id_list]
    type_list_unique = list(set(type_list))
    for each_type in type_list_unique:
        print "\t\t\t\t" + Fore.GREEN + "Available %s  details" % (pretty_print(each_type))
        print Style.RESET_ALL
        for each_resource in sorted(list(final_dict2.keys())):
            if final_dict2[each_resource]['type'] == each_type:
                if 'tags.Name' in final_dict2[each_resource]['attributes']:
                    print "\t\t\t" + Fore.GREEN + "%s - %s " % (pretty_print(each_type), final_dict2[each_resource]['attributes']['tags.Name'])
                    print Style.RESET_ALL
                elif 'name' in final_dict2[each_resource]['attributes']:
                    print "\t\t\t" + Fore.GREEN + "%s - %s " % (pretty_print(each_type), final_dict2[each_resource]['attributes']['name'])
                    print Style.RESET_ALL
                print_level2_attributes(final_dict2[each_resource])
                print '\n'


def print_specific(final_dict2, specific_list):
    """ Print speciic attributes """
    id_list = final_dict2.keys()
    type_list = [final_dict2[i]['type'] for i in id_list]
    type_list_unique = list(set(type_list))
    for each_type in type_list_unique:
        if each_type in specific_list:
            print "\t\t\t\t" + Fore.GREEN + "Available %s  details" % (pretty_print(each_type))
            print Style.RESET_ALL
            for each_resource in final_dict2.keys():
                if final_dict2[each_resource]['type'] == each_type:
                    if 'tags.Name' in final_dict2[each_resource]['attributes']:
                        print "\t\t\t" + Fore.GREEN + "%s - %s " % (pretty_print(each_type), final_dict2[each_resource]['attributes']['tags.Name'])
                        print Style.RESET_ALL
                    elif 'name' in final_dict2[each_resource]['attributes']:
                        print "\t\t\t" + Fore.GREEN + "%s - %s " % (pretty_print(each_type), final_dict2[each_resource]['attributes']['name'])
                        print Style.RESET_ALL
                    print_level2_attributes(final_dict2[each_resource])
                    print '\n'


def print_single(final_dict2, resource_id):
    dict = final_dict2[resource_id]
    print "\t\t\t\t" + Fore.GREEN + "Available %s  details Resource ID %s" % (pretty_print(dict['type']), resource_id)
    print Style.RESET_ALL
    print_level2_attributes(final_dict2[resource_id])


def transform_string(string):
    lower_string1 = string.lower()
    str_split = lower_string1.split()
    return '_'.join(str_split)


def main():
    verbose, path, specific, id = get_args()

    if path:
        file_path = path + '/terraform.tfstate'
    else:
        file_path = os.getcwd() + '/terraform.tfstate'

    try:
        file_handle = open(file_path, 'r')
    except IOError:
        print "No terraform tfstate file found"
        sys.exit()
    try:
        json_data = json.loads(file_handle.read())
        file_handle.close()
    except ValueError:
        print "Not a proper tfstate file"
        file_handle.close()
        sys.exit()

    state_file = tfstate(json_data)
    final_dict2 = state_file.get_aws_resources(json_data)

    specific_lookup = False
    resource_lookup = False

    if id:
        id_list = id.split(',')
        for each in id_list:
            print_single(final_dict2, each)
        resource_lookup = True

    if specific:
        specific_list = specific.split(',')
        specific_list1 = [transform_string(s) for s in specific_list]
        print_specific(final_dict2, specific_list1)
        specific_lookup = True

    if verbose < 2 and specific_lookup == False and resource_lookup == False:
        summary_dict = print_resource_summary(final_dict2)
        print_instance_summary(final_dict2)
    elif verbose > 1 and specific_lookup == False and resource_lookup == False:
        print_all(final_dict2)

if __name__ == "__main__":
    main()

