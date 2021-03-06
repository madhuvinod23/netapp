#!/usr/bin/python

# (c) 2020, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


""" NetApp ONTAP Info using REST APIs """


from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'certified'}

DOCUMENTATION = '''
module: na_ontap_rest_info
author: NetApp Ansible Team (@carchi8py) <ng-ansibleteam@netapp.com>
extends_documentation_fragment:
    - netapp.ontap.netapp.na_ontap
short_description: NetApp ONTAP information gatherer using REST APIs
description:
    - This module allows you to gather various information about ONTAP configuration using REST APIs

options:
    state:
        type: str
        description:
            - Returns "info"
        default: "info"
        choices: ['info']
    gather_subset:
        type: list
        description:
            - When supplied, this argument will restrict the information collected
                to a given subset.  Possible values for this argument include
                "aggregate_info",
                "vserver_info",
                "volume_info",
                Can specify a list of values to include a larger subset.
            - REST APIs are supported with ONTAP 9.6 onwards.
        default: "all"
    max_records:
        type: int
        description:
            - Maximum number of records returned in a single call.
        default: 1024
    fields:
        type: list
        description:
            - Request specific fields from subset.
               '*' to return all the fields, one or more subsets are allowed.
               '<list of fields>'  to return specified fields, only one subset will be allowed.
            - If the option is not present, return all the fields.
        version_added: '20.6.0'
'''

EXAMPLES = '''
- name: run ONTAP gather facts for vserver info
  na_ontap_info_rest:
      hostname: "1.2.3.4"
      username: "testuser"
      password: "test-password"
      https: true
      validate_certs: false
      use_rest: Always
      gather_subset:
      - vserver_info
- name: run ONTAP gather facts for aggregate info and volume info
  na_ontap_info_rest:
      hostname: "1.2.3.4"
      username: "testuser"
      password: "test-password"
      https: true
      validate_certs: false
      use_rest: Always
      gather_subset:
      - aggregate_info
      - volume_info
- name: run ONTAP gather facts for all subsets
  na_ontap_info_rest:
      hostname: "1.2.3.4"
      username: "testuser"
      password: "test-password"
      https: true
      validate_certs: false
      use_rest: Always
      gather_subset:
      - all
- name: run ONTAP gather facts for aggregate info and volume info with fields section
  na_ontap_info_rest:
      hostname: "1.2.3.4"
      username: "testuser"
      password: "test-password"
      https: true
      fields:
      - '*'
      validate_certs: false
      use_rest: Always
      gather_subset:
      - aggregate_info
      - volume_info
- name: run ONTAP gather facts for aggregate info with specified fields
  na_ontap_info_rest:
      hostname: "1.2.3.4"
      username: "testuser"
      password: "test-password"
      https: true
      fields:
      - 'uuid'
      - 'name'
      - 'node'
      validate_certs: false
      use_rest: Always
      gather_subset:
      - aggregate_info
'''

from ansible.module_utils.basic import AnsibleModule
import ansible_collections.netapp.ontap.plugins.module_utils.netapp as netapp_utils
from ansible_collections.netapp.ontap.plugins.module_utils.netapp_module import NetAppModule
from ansible_collections.netapp.ontap.plugins.module_utils.netapp import OntapRestAPI


class NetAppONTAPGatherInfo(object):
    '''Class with gather info methods'''

    def __init__(self):
        """
        Parse arguments, setup state variables,
        check paramenters and ensure request module is installed
        """
        self.argument_spec = netapp_utils.na_ontap_host_argument_spec()
        self.argument_spec.update(dict(
            state=dict(type='str', choices=['info'], default='info', required=False),
            gather_subset=dict(default=['all'], type='list', required=False),
            max_records=dict(type='int', default=1024, required=False),
            fields=dict(type='list', required=False)
        ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            supports_check_mode=True
        )

        # set up variables
        self.na_helper = NetAppModule()
        self.parameters = self.na_helper.set_parameters(self.module.params)
        self.fields = list()

        self.restApi = OntapRestAPI(self.module)

    def validate_ontap_version(self):
        """
            Method to validate the ONTAP version
        """

        api = 'cluster'
        data = {'fields': ['version']}

        ontap_version, error = self.restApi.get(api, data)

        if error:
            self.module.fail_json(msg=error)

        return ontap_version

    def get_subset_info(self, gather_subset_info):
        """
            Gather ONTAP information for the given subset using REST APIs
            Input for REST APIs call : (api, data)
            return gathered_ontap_info
        """

        api = gather_subset_info['api_call']
        data = {'max_records': self.parameters['max_records'], 'fields': self.fields}

        gathered_ontap_info, error = self.restApi.get(api, data)

        if error:
            # Fail the module if error occurs from REST APIs call
            if int(error.get('code', 0)) == 6:
                self.module.fail_json(msg="%s user is not authorized to make %s api call" % (self.parameters.get('username'), api))
            else:
                self.module.fail_json(msg=error)
        else:
            return gathered_ontap_info

        return None

    def get_next_records(self, api):
        """
            Gather next set of ONTAP information for the specified api
            Input for REST APIs call : (api, data)
            return gather_subset_info
        """

        data = {}
        gather_subset_info, error = self.restApi.get(api, data)

        if error:
            self.module.fail_json(msg=error)

        return gather_subset_info

    def apply(self):
        """
        Perform pre-checks, call functions and exit
        """

        result_message = dict()

        # Validating ONTAP version
        self.validate_ontap_version()

        # Defining gather_subset and appropriate api_call
        get_ontap_subset_info = {
            'aggregate_info': {
                'api_call': 'storage/aggregates',
            },
            'vserver_info': {
                'api_call': 'svm/svms',
            },
            'volume_info': {
                'api_call': 'storage/volumes',
            }
        }

        if 'all' in self.parameters['gather_subset']:
            # If all in subset list, get the information of all subsets
            self.parameters['gather_subset'] = get_ontap_subset_info.keys()

        length_of_subsets = len(self.parameters['gather_subset'])

        if self.parameters.get('fields') is not None:
            # If multiple fields specified to return, convert list to string
            self.fields = ','.join(self.parameters.get('fields'))

            if self.fields != '*' and length_of_subsets > 1:
                # Restrict gather subsets to one subset if fields section is list_of_fields
                self.module.fail_json(msg="Error: fields: %s, only one subset will be allowed." % self.parameters.get('fields'))

        for subset in self.parameters['gather_subset']:
            try:
                # Verify whether the supported subset passed
                specified_subset = get_ontap_subset_info[subset]
            except KeyError:
                self.module.fail_json(msg="Specified subset %s is not found, supported subsets are %s" %
                                      (subset, list(get_ontap_subset_info.keys())))

            result_message[subset] = self.get_subset_info(specified_subset)

            while result_message[subset]['_links'].get('next'):
                # Get all the set of records if next link found in subset_info for the specified subset
                next_api = result_message[subset]['_links']['next']['href']
                gathered_subset_info = self.get_next_records(next_api.replace('/api', ''))

                # Update the subset info for the specified subset
                result_message[subset]['_links'] = gathered_subset_info['_links']
                result_message[subset]['records'].extend(gathered_subset_info['records'])

            # Getting total number of records
            result_message[subset]['num_records'] = len(result_message[subset]['records'])

        self.module.exit_json(changed='False', state=self.parameters['state'], ontap_info=result_message)


def main():
    """
    Main function
    """
    obj = NetAppONTAPGatherInfo()
    obj.apply()


if __name__ == '__main__':
    main()
