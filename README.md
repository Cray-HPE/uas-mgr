# uan-mgr
The uan-mgr is a webservice to manage the life cycle of UAN Pods
on the Shasta System.

uan-mgr provides the following services:

* Allow users to request a UAN Pod (access instructions are returned
to the user)
* Allow users to see status and information about their UAN Pod(s)
* Allow users to delete their UAN Pod(s)
* Allow sysadmins to see status and information on all UAN Pods
* Allow sysadmins to delete UAN Pod(s)

# Implementation
The uan-mgr is a webservice that runs in a container deployed by
Kubernetes on Shasta Service Nodes.

