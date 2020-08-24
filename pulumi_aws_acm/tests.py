import pulumi
import unittest
from typing import Optional, Tuple, List
from pulumi_aws_acm import Certificate


class MyMocks(pulumi.runtime.Mocks):
    def new_resource(self,
                     type_: str,
                     name: str,
                     inputs: dict,
                     provider: Optional[str],
                     id_: Optional[str]) -> Tuple[str, dict]:
        if type_ == 'aws:acm/certificate:Certificate':
            state = {
                'domain_validation_options': [
                    {
                        'resourceRecordName': '_test.zone.',
                        'resourceRecordValue': '_test.acm.zone.',
                        'resourceRecordType': 'A',
                        'domain_name': 'test.jetbrains.com',
                    },
                    {
                        'resourceRecordName': '_test1.zone.',
                        'resourceRecordValue': '_test1.acm.zone.',
                        'resourceRecordType': 'A',
                        'domain_name': 'test1.jetbrains.com',
                    }
                ],
            }
            return name + '_id', dict(inputs, **state)
        return name + '_id', inputs

    def call(self, token, args, provider):
        return {}


pulumi.runtime.set_mocks(MyMocks())

certificate = Certificate('test', issue='sre-123',
                          stack='staging',
                          zones={
                              'id-1': ['test.jetbrains.com', 'test1.jetbrains.com'],
                              'id-2': ['test.jetbrains.org', 'test1.jetbrains.org'],
                          })


class TestingWithMocks(unittest.TestCase):
    @pulumi.runtime.test
    def test_check_tags(self):
        def check_tags(args: List[Certificate]):
            c = args[0]
            self.assertEqual(c.tags.get('acm'), 'acm-test-staging')
            self.assertEqual(c.tags.get('stack'), 'staging')
            self.assertEqual(c.tags.get('issue'), 'sre-123')

        return pulumi.Output.all(certificate).apply(check_tags)

    def test_check_SANs(self):
        def check_SANs(args: List[Certificate]):
            c = args[0]
            self.assertEqual(c.domain_name, 'test.jetbrains.com')
            self.assertEqual(c.SANs, [
                'test1.jetbrains.com',
                'test.jetbrains.org',
                'test1.jetbrains.org'
            ])

        return pulumi.Output.all(certificate).apply(check_SANs)

    def test_check_get_zone_by_id(self):
        def check_get_zone_by_id(args: List[Certificate]):
            c = args[0]
            self.assertEqual(c._get_zone_id_by_domain('test.jetbrains.com'), 'id-1')
            self.assertEqual(c._get_zone_id_by_domain('test1.jetbrains.com'), 'id-1')
            self.assertEqual(c._get_zone_id_by_domain('test.jetbrains.org'), 'id-2')
            self.assertEqual(c._get_zone_id_by_domain('test1.jetbrains.org'), 'id-2')

            return pulumi.Output.all(certificate).apply(check_get_zone_by_id)
