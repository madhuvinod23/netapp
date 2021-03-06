# Copyright (c) 2018 NetApp
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

''' unit tests for module_utils netapp_module.py '''
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest

from ansible_collections.netapp.ontap.tests.unit.compat import unittest
from ansible_collections.netapp.ontap.plugins.module_utils.netapp_module import NetAppModule as na_helper


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


class MockModule(object):
    ''' rough mock for an Ansible module class '''
    def __init__(self, required_param=None, not_required_param=None, unqualified_param=None):
        self.argument_spec = dict(
            required_param=dict(required=True),
            not_required_param=dict(required=False),
            unqualified_param=dict(),
            feature_flags=dict(type='dict')
        )
        self.params = dict(
            required_param=required_param,
            not_required_param=not_required_param,
            unqualified_param=unqualified_param,
            feature_flags=dict(type='dict')
        )

    def fail_json(self, *args, **kwargs):  # pylint: disable=unused-argument
        """function to simulate fail_json: package return data into an exception"""
        kwargs['failed'] = True
        raise AnsibleFailJson(kwargs)


class TestMyModule(unittest.TestCase):
    ''' a group of related Unit Tests '''

    def test_get_cd_action_create(self):
        ''' validate cd_action for create '''
        current = None
        desired = {'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_cd_action(current, desired)
        assert result == 'create'

    def test_get_cd_action_delete(self):
        ''' validate cd_action for delete '''
        current = {'state': 'absent'}
        desired = {'state': 'absent'}
        my_obj = na_helper()
        result = my_obj.get_cd_action(current, desired)
        assert result == 'delete'

    def test_get_cd_action(self):
        ''' validate cd_action for returning None '''
        current = None
        desired = {'state': 'absent'}
        my_obj = na_helper()
        result = my_obj.get_cd_action(current, desired)
        assert result is None

    def test_get_modified_attributes_for_no_data(self):
        ''' validate modified attributes when current is None '''
        current = None
        desired = {'name': 'test'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired)
        assert result == {}

    def test_get_modified_attributes(self):
        ''' validate modified attributes '''
        current = {'name': ['test', 'abcd', 'xyz', 'pqr'], 'state': 'present'}
        desired = {'name': ['abcd', 'abc', 'xyz', 'pqr'], 'state': 'absent'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired)
        assert result == desired

    def test_get_modified_attributes_for_intersecting_mixed_list(self):
        ''' validate modified attributes for list diff '''
        current = {'name': [2, 'four', 'six', 8]}
        desired = {'name': ['a', 8, 'ab', 'four', 'abcd']}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'name': ['a', 'ab', 'abcd']}

    def test_get_modified_attributes_for_intersecting_list(self):
        ''' validate modified attributes for list diff '''
        current = {'name': ['two', 'four', 'six', 'eight']}
        desired = {'name': ['a', 'six', 'ab', 'four', 'abc']}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'name': ['a', 'ab', 'abc']}

    def test_get_modified_attributes_for_nonintersecting_list(self):
        ''' validate modified attributes for list diff '''
        current = {'name': ['two', 'four', 'six', 'eight']}
        desired = {'name': ['a', 'ab', 'abd']}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'name': ['a', 'ab', 'abd']}

    def test_get_modified_attributes_for_list_of_dicts_no_data(self):
        ''' validate modified attributes for list diff '''
        current = None
        desired = {'address_blocks': [{'start': '10.20.10.40', 'size': 5}]}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {}

    def test_get_modified_attributes_for_intersecting_list_of_dicts(self):
        ''' validate modified attributes for list diff '''
        current = {'address_blocks': [{'start': '10.10.10.23', 'size': 5}, {'start': '10.10.10.30', 'size': 5}]}
        desired = {'address_blocks': [{'start': '10.10.10.23', 'size': 5}, {'start': '10.10.10.30', 'size': 5}, {'start': '10.20.10.40', 'size': 5}]}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'address_blocks': [{'start': '10.20.10.40', 'size': 5}]}

    def test_get_modified_attributes_for_nonintersecting_list_of_dicts(self):
        ''' validate modified attributes for list diff '''
        current = {'address_blocks': [{'start': '10.10.10.23', 'size': 5}, {'start': '10.10.10.30', 'size': 5}]}
        desired = {'address_blocks': [{'start': '10.20.10.23', 'size': 5}, {'start': '10.20.10.30', 'size': 5}, {'start': '10.20.10.40', 'size': 5}]}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'address_blocks': [{'start': '10.20.10.23', 'size': 5}, {'start': '10.20.10.30', 'size': 5}, {'start': '10.20.10.40', 'size': 5}]}

    def test_get_modified_attributes_for_list_diff(self):
        ''' validate modified attributes for list diff '''
        current = {'name': ['test', 'abcd'], 'state': 'present'}
        desired = {'name': ['abcd', 'abc'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'name': ['abc']}

    def test_get_modified_attributes_for_no_change(self):
        ''' validate modified attributes for same data in current and desired '''
        current = {'name': 'test'}
        desired = {'name': 'test'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired)
        assert result == {}

    def test_get_modified_attributes_for_an_empty_desired_list(self):
        ''' validate modified attributes for an empty desired list '''
        current = {'snapmirror_label': ['daily', 'weekly', 'monthly'], 'state': 'present'}
        desired = {'snapmirror_label': [], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired)
        assert result == {'snapmirror_label': []}

    def test_get_modified_attributes_for_an_empty_desired_list_diff(self):
        ''' validate modified attributes for an empty desired list with diff'''
        current = {'snapmirror_label': ['daily', 'weekly', 'monthly'], 'state': 'present'}
        desired = {'snapmirror_label': [], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'snapmirror_label': []}

    def test_get_modified_attributes_for_an_empty_current_list(self):
        ''' validate modified attributes for an empty current list '''
        current = {'snapmirror_label': [], 'state': 'present'}
        desired = {'snapmirror_label': ['daily', 'weekly', 'monthly'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired)
        assert result == {'snapmirror_label': ['daily', 'weekly', 'monthly']}

    def test_get_modified_attributes_for_an_empty_current_list_diff(self):
        ''' validate modified attributes for an empty current list with diff'''
        current = {'snapmirror_label': [], 'state': 'present'}
        desired = {'snapmirror_label': ['daily', 'weekly', 'monthly'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'snapmirror_label': ['daily', 'weekly', 'monthly']}

    def test_get_modified_attributes_for_empty_lists(self):
        ''' validate modified attributes for empty lists '''
        current = {'snapmirror_label': [], 'state': 'present'}
        desired = {'snapmirror_label': [], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired)
        assert result == {}

    def test_get_modified_attributes_for_empty_lists_diff(self):
        ''' validate modified attributes for empty lists with diff '''
        current = {'snapmirror_label': [], 'state': 'present'}
        desired = {'snapmirror_label': [], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {}

    def test_get_modified_attributes_equal_lists_with_duplicates(self):
        ''' validate modified attributes for equal lists with duplicates '''
        current = {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily'], 'state': 'present'}
        desired = {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, False)
        assert result == {}

    def test_get_modified_attributes_equal_lists_with_duplicates_diff(self):
        ''' validate modified attributes for equal lists with duplicates with diff '''
        current = {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily'], 'state': 'present'}
        desired = {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {}

    def test_get_modified_attributes_for_current_list_with_duplicates(self):
        ''' validate modified attributes for current list with duplicates '''
        current = {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily'], 'state': 'present'}
        desired = {'schedule': ['daily', 'daily', 'weekly', 'monthly'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, False)
        assert result == {'schedule': ['daily', 'daily', 'weekly', 'monthly']}

    def test_get_modified_attributes_for_current_list_with_duplicates_diff(self):
        ''' validate modified attributes for current list with duplicates with diff '''
        current = {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily'], 'state': 'present'}
        desired = {'schedule': ['daily', 'daily', 'weekly', 'monthly'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'schedule': []}

    def test_get_modified_attributes_for_desired_list_with_duplicates(self):
        ''' validate modified attributes for desired list with duplicates '''
        current = {'schedule': ['daily', 'weekly', 'monthly'], 'state': 'present'}
        desired = {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, False)
        assert result == {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily']}

    def test_get_modified_attributes_for_desired_list_with_duplicates_diff(self):
        ''' validate modified attributes for desired list with duplicates with diff '''
        current = {'schedule': ['daily', 'weekly', 'monthly'], 'state': 'present'}
        desired = {'schedule': ['hourly', 'daily', 'daily', 'weekly', 'monthly', 'daily'], 'state': 'present'}
        my_obj = na_helper()
        result = my_obj.get_modified_attributes(current, desired, True)
        assert result == {'schedule': ['hourly', 'daily', 'daily']}

    def test_is_rename_action_for_empty_input(self):
        ''' validate rename action for input None '''
        source = None
        target = None
        my_obj = na_helper()
        result = my_obj.is_rename_action(source, target)
        assert result == source

    def test_is_rename_action_for_no_source(self):
        ''' validate rename action when source is None '''
        source = None
        target = 'test2'
        my_obj = na_helper()
        result = my_obj.is_rename_action(source, target)
        assert result is False

    def test_is_rename_action_for_no_target(self):
        ''' validate rename action when target is None '''
        source = 'test2'
        target = None
        my_obj = na_helper()
        result = my_obj.is_rename_action(source, target)
        assert result is True

    def test_is_rename_action(self):
        ''' validate rename action '''
        source = 'test'
        target = 'test2'
        my_obj = na_helper()
        result = my_obj.is_rename_action(source, target)
        assert result is False

    def test_required_is_not_set_to_none(self):
        ''' if a key is present, without a value, Ansible sets it to None '''
        my_obj = na_helper()
        my_module = MockModule()
        print(my_module.argument_spec)
        with pytest.raises(AnsibleFailJson) as exc:
            my_obj.check_and_set_parameters(my_module)
        msg = 'required_param requires a value, got: None'
        assert exc.value.args[0]['msg'] == msg

        # force a value different than None
        my_module.params['required_param'] = 1
        my_params = my_obj.check_and_set_parameters(my_module)
        assert set(my_params.keys()) == set(['required_param', 'feature_flags'])
