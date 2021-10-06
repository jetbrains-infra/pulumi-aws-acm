from typing import Dict, List

import pulumi
from pulumi_aws import acm as aws_acm
from pulumi_aws import route53


class Certificate(pulumi.ComponentResource):
    certificate_validation: aws_acm.CertificateValidation
    name: str
    issue: str
    stack: str
    zones: Dict[str, List[str]]
    SANs: List[str]
    tags: Dict[str, str]
    domain_name: str

    def __init__(self,
                 name: str,
                 issue: str,
                 stack: str,
                 zones: Dict[str, List[str]],
                 opts: pulumi.ResourceOptions = None):
        """
        Constructs a Certificate

        :param name: Will be used for objects naming, like ACM Certificate object and technical names
        :param issue: Issue tracker issue ID
        :param stack: Stack name, for example dev, staging or prod
        :param zones: Map of zone_id: to domains names, for example {'12345ABCDE': ['example.com', 'www.example.com']}
            zone_id will use to create DNS validation records for certs for exact domain names
        :param opts: Standard pulumi ResourceOptions
        """
        super().__init__('AWSCertificate', name, None, opts)
        self.name = f'acm-{name}-{stack}'
        self.issue = issue
        self.stack = stack
        self.zones = zones
        self.SANs = []
        self.tags = {'acm': self.name,
                     'stack': self.stack,
                     'issue': self.issue}

        for _, names in self.zones.items():
            self.SANs += names
        # Pop first element from SANs due to ACM pop it during deploy and next apply catch redeploy of the certificate
        # due to state have n SANs, but in ACM n-1
        self.domain_name = self.SANs.pop(0)

        cert = aws_acm.Certificate(f'{self.name}-cert',
                                   domain_name=self.domain_name,
                                   subject_alternative_names=self.SANs,
                                   tags=self.tags,
                                   validation_method="DNS",
                                   opts=pulumi.ResourceOptions(parent=self))
        fqdns = cert.domain_validation_options.apply(self._create_records)
        self.certificate_validation = aws_acm.CertificateValidation(self.name,
                                                                    certificate_arn=cert.arn,
                                                                    validation_record_fqdns=fqdns,
                                                                    opts=pulumi.ResourceOptions(parent=self))

    def _create_records(self, domain_validation_options):
        validation_record_fqdns = []
        i = 0
        for dvo in domain_validation_options:
            cert_validation = route53.Record(f'{self.name}-record-{i}',
                                             name=dvo.resource_record_name,
                                             records=[dvo.resource_record_value],
                                             ttl=300,
                                             type=dvo.resource_record_type,
                                             zone_id=self._get_zone_id_by_domain(dvo.domain_name),
                                             opts=pulumi.ResourceOptions(parent=self, delete_before_replace=True))
            i += 1
            validation_record_fqdns.append(cert_validation.fqdn)
        return validation_record_fqdns

    def _get_zone_id_by_domain(self, domain):
        for zone_id, names in self.zones.items():
            if domain in names:
                return zone_id
        raise Exception(
            f'Unable to get zone id by domain_name, domain_name: "{domain}"')
