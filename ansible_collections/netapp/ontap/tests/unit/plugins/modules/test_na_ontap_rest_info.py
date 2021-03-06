# (c) 2020, NetApp, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' Unit Tests NetApp ONTAP REST APIs Ansible module: na_ontap_rest_info '''

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import json
import pytest

from ansible_collections.netapp.ontap.tests.unit.compat import unittest
from ansible_collections.netapp.ontap.tests.unit.compat.mock import patch, Mock
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
from requests import Response
import ansible_collections.netapp.ontap.plugins.module_utils.netapp as netapp_utils

from ansible_collections.netapp.ontap.plugins.modules.na_ontap_rest_info \
    import NetAppONTAPGatherInfo as ontap_rest_info_module

# REST API canned responses when mocking send_request
SRR = {
    # common responses
    'validate_ontap_version_pass': ({'version': 'ontap_version'}, None),
    'validate_ontap_version_fail': (None, 'API not found error'),
    'get_subset_info': ({'_links': {'self': {'href': 'dummy_href'}},
                         'num_records': 3,
                         'records': [{'name': 'dummy_vol1'},
                                     {'name': 'dummy_vol2'},
                                     {'name': 'dummy_vol3'}],
                         'version': 'ontap_version'}, None),
    'get_subset_info_with_next': ({'_links': {'self': {'href': 'dummy_href'},
                                              'next': {'href': '/api/next_record_api'}},
                                   'num_records': 3,
                                   'records': [{'name': 'dummy_vol1'},
                                               {'name': 'dummy_vol2'},
                                               {'name': 'dummy_vol3'}],
                                   'version': 'ontap_version'}, None),
    'get_next_record': ({'_links': {'self': {'href': 'dummy_href'}},
                         'num_records': 2,
                         'records': [{'name': 'dummy_vol1'},
                                     {'name': 'dummy_vol2'}],
                         'version': 'ontap_version'}, None),
}


def set_module_args(args):
    """prepare arguments so that they will be picked up during module creation"""
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    basic._ANSIBLE_ARGS = to_bytes(args)  # pylint: disable=protected-access


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):  # pylint: disable=unused-argument
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


class TestMyModule(unittest.TestCase):
    ''' A group of related Unit Tests '''

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def set_default_args(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'validate_certs': False
        })

    def set_args_run_Ontap_version_check(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'validate_certs': False,
            'max_records': 1024,
            'gather_subset': ['volume_info']
        })

    def set_args_run_Ontap_gather_facts_for_vserver_info(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'validate_certs': False,
            'max_records': 1024,
            'gather_subset': ['vserver_info']
        })

    def set_args_run_Ontap_gather_facts_for_volume_info(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'validate_certs': False,
            'max_records': 1024,
            'gather_subset': ['volume_info']
        })

    def set_args_run_Ontap_gather_facts_for_all_subsets(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'validate_certs': False,
            'max_records': 1024,
            'gather_subset': ['all']
        })

    def set_args_run_Ontap_gather_facts_for_all_subsets_with_fields_section_pass(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'validate_certs': False,
            'max_records': 1024,
            'fields': '*',
            'gather_subset': ['all']
        })

    def set_args_run_Ontap_gather_facts_for_all_subsets_with_fields_section_fail(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'validate_certs': False,
            'max_records': 1024,
            'fields': ['uuid', 'name', 'node'],
            'gather_subset': ['all']
        })

    def set_args_run_Ontap_gather_facts_for_aggregate_info_with_fields_section_pass(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'fields': ['uuid', 'name', 'node'],
            'validate_certs': False,
            'max_records': 1024,
            'gather_subset': ['aggregate_info']
        })

    def set_args_get_all_records_for_volume_info_to_check_next_api_call_functionality_pass(self):
        return dict({
            'hostname': 'hostname',
            'username': 'username',
            'password': 'password',
            'https': True,
            'validate_certs': False,
            'max_records': 3,
            'gather_subset': ['volume_info']
        })

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_version_check_for_9_6_pass(self, mock_request):
        set_module_args(self.set_args_run_Ontap_version_check())
        my_obj = ontap_rest_info_module()
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info'],
        ]

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_version_check_for_10_2_pass(self, mock_request):
        set_module_args(self.set_args_run_Ontap_version_check())
        my_obj = ontap_rest_info_module()
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info'],
        ]

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['changed']

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_version_check_for_9_2_fail(self, mock_request):
        ''' Test for Checking the ONTAP version '''
        set_module_args(self.set_args_run_Ontap_version_check())
        my_obj = ontap_rest_info_module()
        mock_request.side_effect = [
            SRR['validate_ontap_version_fail'],
        ]

        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        assert exc.value.args[0]['msg'] == SRR['validate_ontap_version_fail'][1]

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_gather_facts_for_vserver_info_pass(self, mock_request):
        set_module_args(self.set_args_run_Ontap_gather_facts_for_vserver_info())
        my_obj = ontap_rest_info_module()
        gather_subset = ['vserver_info']
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info'],
        ]

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_run_Ontap_gather_facts_for_vserver_info_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['ontap_info']) == set(gather_subset)

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_gather_facts_for_volume_info_pass(self, mock_request):
        set_module_args(self.set_args_run_Ontap_gather_facts_for_volume_info())
        my_obj = ontap_rest_info_module()
        gather_subset = ['volume_info']
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info'],
        ]

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_run_Ontap_gather_facts_for_volume_info_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['ontap_info']) == set(gather_subset)

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_gather_facts_for_all_subsets_pass(self, mock_request):
        set_module_args(self.set_args_run_Ontap_gather_facts_for_all_subsets())
        my_obj = ontap_rest_info_module()
        gather_subset = ['aggregate_info', 'vserver_info', 'volume_info']
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info'],
            SRR['get_subset_info'],
            SRR['get_subset_info'],
        ]

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_run_Ontap_gather_facts_for_all_subsets_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['ontap_info']) == set(gather_subset)

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_gather_facts_for_all_subsets_with_fields_section_pass(self, mock_request):
        set_module_args(self.set_args_run_Ontap_gather_facts_for_all_subsets_with_fields_section_pass())
        my_obj = ontap_rest_info_module()
        gather_subset = ['aggregate_info', 'vserver_info', 'volume_info']
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info'],
            SRR['get_subset_info'],
            SRR['get_subset_info'],
        ]

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_run_Ontap_gather_facts_for_all_subsets_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['ontap_info']) == set(gather_subset)

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_gather_facts_for_all_subsets_with_fields_section_fail(self, mock_request):
        set_module_args(self.set_args_run_Ontap_gather_facts_for_all_subsets_with_fields_section_fail())
        my_obj = ontap_rest_info_module()
        error_message = "Error: fields: %s, only one subset will be allowed." \
                        % self.set_args_run_Ontap_gather_facts_for_aggregate_info_with_fields_section_pass()['fields']
        gather_subset = ['aggregate_info', 'vserver_info', 'volume_info']
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info'],
            SRR['get_subset_info'],
            SRR['get_subset_info'],
        ]

        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.apply()
        print('Info: test_run_Ontap_gather_facts_for_all_subsets_pass: %s' % repr(exc.value.args))
        assert exc.value.args[0]['msg'] == error_message

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_run_Ontap_gather_facts_for_aggregate_info_pass_with_fields_section_pass(self, mock_request):
        set_module_args(self.set_args_run_Ontap_gather_facts_for_aggregate_info_with_fields_section_pass())
        my_obj = ontap_rest_info_module()
        gather_subset = ['aggregate_info']
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info'],
        ]

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_run_Ontap_gather_facts_for_volume_info_pass: %s' % repr(exc.value.args))
        assert set(exc.value.args[0]['ontap_info']) == set(gather_subset)

    @patch('ansible_collections.netapp.ontap.plugins.module_utils.netapp.OntapRestAPI.send_request')
    def test_get_all_records_for_volume_info_to_check_next_api_call_functionality_pass(self, mock_request):
        set_module_args(self.set_args_get_all_records_for_volume_info_to_check_next_api_call_functionality_pass())
        my_obj = ontap_rest_info_module()
        total_records = 5
        gather_subset = ['volume_info']
        mock_request.side_effect = [
            SRR['validate_ontap_version_pass'],
            SRR['get_subset_info_with_next'],
            SRR['get_next_record'],
        ]

        with pytest.raises(AnsibleExitJson) as exc:
            my_obj.apply()
        print('Info: test_get_all_records_for_volume_info_to_check_next_api_call_functionality_pass: %s' % repr(exc.value.args))
        assert exc.value.args[0]['ontap_info']['volume_info']['num_records'] == total_records
