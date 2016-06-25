#!/usr/bin/env python
# coding=utf-8

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from future import standard_library
standard_library.install_aliases()

import socket
import dns.exception
import dns.resolver
import logging
import os
import requests
import sys
import time

from tld import get_tld

# Enable verified HTTPS requests on older Pythons
# http://urllib3.readthedocs.org/en/latest/security.html
if sys.version_info[0] == 2:
    requests.packages.urllib3.contrib.pyopenssl.inject_into_urllib3()

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

ACME_DNS_PREFIX = '_acme-challenge'

try:
    DNSPOD_AUTH_PARAMS = {
        'login_token' : os.environ['DNSPOD_LOGIN_TOKEN'],
    }
except KeyError:
    logger.error(" + Unable to locate DNSPod credentials in environment!")
    sys.exit(1)

try:
    dns_servers = os.environ['DNSPOD_DNS_SERVERS']
    dns_servers = map(socket.gethostbyname, dns_servers.split())
except KeyError:
    dns_servers = False


def _has_dns_propagated(name, token):
    txt_records = []
    try:
        if dns_servers:
            custom_resolver = dns.resolver.Resolver()
            custom_resolver.nameservers = dns_servers
            dns_response = custom_resolver.query(name, 'TXT')
        else:
            dns_response = dns.resolver.query(name, 'TXT')
        for rdata in dns_response:
            for txt_record in rdata.strings:
                txt_records.append(txt_record)
    except dns.exception.DNSException as error:
        logger.exception("check TXT record failed")
        return False

    for txt_record in txt_records:
        if txt_record == token:
            return True

    return False

def _execute_dnspod_action(action, domain, params):
    res = get_tld('http://' + domain, as_object=True)
    sub_domain, tld = res.subdomain, res.tld
    if sub_domain:
        sub_domain = "%s.%s" % (ACME_DNS_PREFIX, sub_domain)
    else:
        sub_domain = ACME_DNS_PREFIX

    url = "https://dnsapi.cn/%s" % action
    payload = {
        'domain' : tld,
        'sub_domain' : sub_domain,
        'format' : 'json',
    }
    payload.update(params)
    payload.update(DNSPOD_AUTH_PARAMS)
    r = requests.post(url, data=payload)
    r.raise_for_status()
    return r

# https://www.dnspod.cn/docs/records.html#record-list
def _get_txt_record_id(domain, token):
    action = 'Record.List'
    payload = {
        'keyword' : token,
    }
    r = _execute_dnspod_action(action, domain, payload)
    try:
        for rec in r.json()['records']:
            if rec['type'] == 'TXT' and rec['value'] == token:
                return rec['id']
    except (IndexError, KeyError):
        logger.info(" + Unable to locate record named {0}".format(domain))
        return


# https://www.dnspod.cn/docs/records.html#record-create
def create_txt_record(args):
    domain, token = args[0], args[2]
    
    action = 'Record.Create'
    payload = {
        'record_type': 'TXT',
        'record_line': '默认',
        'value' :  token,
    }
    r = _execute_dnspod_action(action, domain, payload)

    record_id = r.json()['record']['id']
    logger.debug("+ TXT record created, ID: {0}".format(record_id))

    # give it 10 seconds to settle down and avoid nxdomain caching
    logger.info(" + Settling down for 10s...")
    time.sleep(10)

    name = "{0}.{1}".format(ACME_DNS_PREFIX, domain)
    while(_has_dns_propagated(name, token) == False):
        logger.info(" + DNS not propagated, waiting 30s...")
        time.sleep(30)


# https://www.dnspod.cn/docs/records.html#record-remove
def delete_txt_record(args):
    domain, token = args[0], args[2]
    if not domain:
        logger.info(" + http_request() error in letsencrypt.sh?")
        return

    record_id = _get_txt_record_id(domain, token)

    name = "{0}.{1}".format(ACME_DNS_PREFIX, domain)
    logger.debug(" + Deleting TXT record name: {0}".format(name))
    action = "Record.Remove"
    payload = {
        'record_id' : record_id
    }
    _execute_dnspod_action(action, domain, payload)


def deploy_cert(args):
    domain, privkey_pem, cert_pem, fullchain_pem, chain_pem, timestamp = args
    logger.info(' + ssl_certificate: {0}'.format(fullchain_pem))
    logger.info(' + ssl_certificate_key: {0}'.format(privkey_pem))
    return

def unchanged_cert(args):
    return

def main(argv):
    ops = {
        'deploy_challenge': create_txt_record,
        'clean_challenge' : delete_txt_record,
        'deploy_cert'     : deploy_cert,
        'unchanged_cert'  : unchanged_cert,
    }
    logger.info(" + DNSPod hook executing: {0}".format(argv[0]))
    ops[argv[0]](argv[1:])


if __name__ == '__main__':
    main(sys.argv[1:])
