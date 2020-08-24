# pulumi-aws-acm
Pulumi ComponentResource for create AWS ACM Certificate and validate it with DNS validation method

# How to install

```bash
pip install pulumi-aws-acm
# or 
pip install git+git://github.com/jetbrains-infra/pulumi-aws-acm@<tag or branch>
```

# How to use 
```python
import pulumi
from pulumi_aws_acm import Certificate
from pulumi_aws import Provider

cert_provider = Provider('cert-provider', region='us-east-1')

certificate = Certificate('test',
                          issue='sre-123',
                          stack='staging',
                          zones={
                              'zone_id-1': ['example.com', 'www.example.com'],
                              'zone_id-2': ['example.org', 'www.example.org'],
                          },
                          opts=pulumi.ResourceOptions(provider=cert_provider))

pulumi.export('certificate-arn', certificate.certificate_validation.certificate_arn)
```

ACM Certificate will be issued for first domain name from first zone, `example.com` as for code above and with SANs:`['www.example.com', 'example.org', 'www.example.org']`
