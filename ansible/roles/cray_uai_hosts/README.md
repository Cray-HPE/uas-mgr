cray_uai_hosts
===============

An ansible role for setting/unsetting which NCNs may be UAI hosts.

This role performs the following tasks on NCNs defined to be UAI hosts:

* Sets up the mac0 macvlan bridge interface
* Sets up the mac0 macvlan bridge routing
* Sets up Kubernetes network attachment definition for the macvlan
* Labels UAI hosts for UAI deployments
* Taints UAI hosts to prevent other services from being deployed to them

This role performs the following on NCNs no longer defined to be UAI hosts:

* Removes the mac0 macvlan bridge interface
* Removes the mac0 macvlan bridge routing
* Removes the label for UAI deployments
* Removes taints to prevent other services from being deployed to them

Role Variables
--------------

Macvlan configuration is derived from /etc/ansible/hosts/group_vars/all/networks.yml:

```yaml
 node_management:
    <<: *old_node_management
    meta: &node_management_meta
      description: Node management network.
      cluster_name: mgmt-plane-nmn.local
    blocks:
      ipv4:
        - label: river
          network: 10.2.0.0/16
          subnets:
            - label: uai_macvlan
# NOTE: uai_macvlan network supports 500 UAIs (500 users) across 10 UAI hosts
# NOTE: gateway is the IP of the first UAI host - support 10 UAI hosts 10.2.201.[245-254]
              network: 10.2.200.0/23
              gateway: 10.2.201.245
              dhcp:
                start: 10.2.200.1
                end: 10.2.201.244
# Note: Uncomment the mountain section to activate its default NMN.
#        - label: mountain
#          subnets:
# Note: Uncomment this uai_macvlan section for mountain uai access.
#            - label: uai_macvlan
#              network: 10.100.104.0/23
#              gateway: 10.252.127.254
```

Labels are set from /etc/ansible/hosts/group_vars/all/uai_hosts.yml:

```yaml
---
uai_tnl_labels:
  - { key: "uas", value: "True" }
```

Example Playbook
----------------

```yaml
---
- hosts: uai_hosts
  gather_facts: no
  roles:
    - cray_uai_hosts
```

License
-------

Copyright (c) 2019 Cray Inc.
