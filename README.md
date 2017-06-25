# DNSPOD hook for `dehydrated`

This a hook for [dehydrated](https://github.com/lukas2511/dehydrated) (a [Let's Encrypt](https://letsencrypt.org/) ACME client) that allows you to use [DNSPod](https://www.dnspod.cn/) DNS records to respond to `dns-01` challenges. Requires Python and your DNSPod account API token being in the environment.

## Installation

```
$ git clone https://github.com/lukas2511/dehydrated
$ cd dehydrated
$ mkdir hooks
$ git clone https://github.com/ftao/letsencrypt-dnspod-hook hooks/dnspod
$ pip install -r hooks/dnspod/requirements.txt
```
If using Python 2, replace the last step with the one below and check the [urllib3 documentation](http://urllib3.readthedocs.org/en/latest/security.html#installing-urllib3-with-sni-support-and-certificates) for other possible caveats.

```
$ pip install -r hooks/dnspod/requirements-python-2.txt
```


## Configuration

Your account's DNSPod LOGIN Token are expected to be in the environment, so make sure to:

```
$ export DNSPOD_LOGIN_TOKEN='YOUR-DNSPOD-LOGIN-TOKEN'
```


Alternatively, these statements can be placed in `dehydrated/config.sh`, which is automatically sourced by `dehydrated` on startup:

```
echo "export DNSPOD_LOGIN_TOKEN='YOUR-DNSPOD-LOGIN-TOKEN'" >> config.sh
```



## Usage

```
$ ./dehydrated -c -d example.com -t dns-01 -k 'hooks/dnspod/hook.py'
#
# !! WARNING !! No main config file found, using default config!
#
Processing example.com
 + Signing domains...
 + Creating new directory /home/user/dehydrated/certs/example.com ...
 + Generating private key...
 + Generating signing request...
 + Requesting challenge for example.com...
 + DNSPod hook executing: deploy_challenge
 + DNS not propagated, waiting 30s...
 + DNS not propagated, waiting 30s...
 + Responding to challenge for example.com...
 + DNSPod hook executing: clean_challenge
 + Challenge is valid!
 + Requesting certificate...
 + Checking certificate...
 + Done!
 + Creating fullchain.pem...
 + DNSPod hook executing: deploy_cert
 + ssl_certificate: /home/user/dehydrated/certs/example.com/fullchain.pem
 + ssl_certificate_key: /home/user/dehydrated/certs/example.com/privkey.pem
 + Done!
```

