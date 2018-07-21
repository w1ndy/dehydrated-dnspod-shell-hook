# DNSPOD hook for `dehydrated`

This a hook for [dehydrated](https://github.com/lukas2511/dehydrated) (a [Let's Encrypt](https://letsencrypt.org/) ACME client) that allows you to use [DNSPod](https://www.dnspod.cn/) DNS records to respond to `dns-01` challenges. Requires your DNSPod account API token being in the environment.

## Installation

```
$ git clone https://github.com/lukas2511/dehydrated
$ cd dehydrated
$ mkdir hooks
$ git clone https://github.com/w1ndy/dehydrated-dnspod-shell-hook.git hooks/dnspod-shell
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
$ ./dehydrated -c -d example.com -t dns-01 -k 'hooks/dnspod-shell/hook.sh'
```

