User Access Services
----
User Access Services will allow users to start an ssh session to a User Access
Service instance and remotely execute commands to Work Load Manager services if
configured to do so.

To start User Access Services (UAS), a label of 'uas:true' must be assigned to
one or more worker nodes. For detailed instructions on adding worker nodes and labels,
consult the kubernetes-installer documentation. For each worker node intended to
be eligible to run UAS, define a labels.yml file using the directory structure
and contents shown below.

```
host_vars/
└── ssn-01.craydev.com
    └── labels.yml
```

labels.yml:
```
---
kubernetes_tnl_labels:
  - {key: uas, value: true}
```

If a label of 'uas:true' does not exist for a node, User Access Services will remain
in a status of "Pending".
