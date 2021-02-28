#!/bin/bash
set -e
set -o pipefail

ACME_DNS_PREFIX=_acme-challenge
DNS_SERVER=114.114.114.114

stderr() {
  >&2 echo "$@"
}

succeeded() {
  local code=$(echo $1 | grep -Po "(?<=\"code\":\").*?(?=\")" || true)
  if [[ ! "$code" == "1" ]]; then
    stderr " ! DNSPod Error: $(echo $1 | grep -Po "(?<=\"message\":\").*?(?=\")")"
    return 1
  fi
  return 0
}

check_login_token() {
  if [[ -z "$DNSPOD_LOGIN_TOKEN" ]]; then
    stderr " ! No DNSPOD_LOGIN_TOKEN specified"
    exit 1
  fi

  local resp
  resp="$(curl -s -X POST https://dnsapi.cn/Domain.List -d "login_token=$DNSPOD_LOGIN_TOKEN&format=json")"
  if ! succeeded "$resp"; then
    stderr " ! Cannot fetch registered domains"
  fi

  DOMAINS=$(echo $resp | grep -Po "(?<=\"name\":\").*?(?=\")")
}

parse_tld() {
  local domain="$1"
  for d in $DOMAINS; do
    if [[ "$domain" =~ "$d" ]]; then
      echo $d
      return 0
    fi
  done
  return 1
}

parse_subdomain() {
  local domain="$1"
  local tld
  tld="$(parse_tld "$domain")"
  if [[ $? -ne 0 ]]; then return 1; fi
  echo $domain | grep -Po "^.*(?=\.$tld)"
}

execute_dnspod_action() {
  local action="$1"
  local domain="$2"
  local params="$3"

  local tld
  local subdomain

  tld="$(parse_tld "$domain")"
  if [[ $? -ne 0 ]]; then
    stderr " ! DNSPod: Domain $domain not found"
    return 1
  fi

  subdomain="$(parse_subdomain "$domain")"
  if [[ $? -ne 0 ]]; then
    stderr " ! DNSPod: Cannot parse subdomain from domain $domain"
    return 1
  fi

  stderr " + DNSPod: Executing $action on $subdomain for $tld..."
  local resp
  resp="$(curl -s -X POST "https://dnsapi.cn/$action" -d "login_token=$DNSPOD_LOGIN_TOKEN&domain=$tld&sub_domain=$subdomain&format=json&lang=en$params")"
  if ! succeeded "$resp"; then return 1; fi

  echo $resp
}

deploy_challenge() {
  local domain="$ACME_DNS_PREFIX.$1"
  local token="$3"
  local result
  local rid

  stderr " + DNSPod: Deploying challenge token $token..."
  result="$(execute_dnspod_action "Record.Create" $domain "&record_type=TXT&record_line=默认&value=$token")"
  if [[ $? -ne 0 ]]; then return 1; fi
  rid="$(echo $result | grep -Po "(?<=\"id\":\").*?(?=\")")"
  stderr " + DNSPod: TXT record created, ID $rid"

  set +e
  while : ; do
    stderr " + DNSPod: Waiting 10 sec..."
    sleep 10
    local records
    stderr " + DNSPod: Resolving TXT records for domain $domain with DNS $DNS_SERVER ..."
    records=$(dig @$DNS_SERVER TXT +short $domain)
    if [[ $? -ne 0 ]]; then
      stderr " ! DNSPod: Failed to resolve TXT records for domain $domain"
    else
      for rec in $records; do
        stderr " + DNSPod: Processing record $rec..."
        if [[ "$rec" =~ "$token" ]]; then
          stderr " + DNSPod: Done deploying challenge"
          set -e
          return 0
        fi
      done
    fi
  done
}

clean_challenge() {
  local domain="$ACME_DNS_PREFIX.$1"
  local token="$3"
  stderr " + DNSPod: Cleaning challenge token..."

  local result
  result="$(execute_dnspod_action Record.List $domain "&record_type=TXT")"
  if [[ $? -ne 0 ]]; then
    stderr " + DNSPod: No challenge token found."
    return 0;
  fi

  local ids
  ids="$(echo $result | grep -Po "(?<=\"id\":\").*?(?=\")" | tail -n +2)"
  for id in $ids; do
    echo " + DNSPod: Removing record $id..."
    execute_dnspod_action Record.Remove $domain "&record_id=$id" >/dev/null
  done
}

main() {
  check_login_token
  HANDLER="$1"; shift
  if [[ "$HANDLER" =~ ^(deploy_challenge|clean_challenge)$ ]]; then
    "$HANDLER" $@
  fi
}

main $@
