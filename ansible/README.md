User Access Services
----
User Access Services will allow users to start an ssh session to a User Access
Instance and remotely execute commands to Work Load Manager services if
configured to do so.

To start User Access Instances (UAIs), a label of 'uas:true' must be
assigned to one or more worker nodes. For detailed instructions on adding
worker nodes as UAI hosts, consult the Cray UAS administration documentation.

If a label of 'uas:true' does not exist for a node, User Access Instances will remain
in a status of "Pending".
