# Cray Shasta cray_uas_user ansible role

This ansible role adds a user to Keycloak for UAS testing.

Admins should add or federated users to an Identity Provider 
using the Keycloak GUI. The user(s) added by this ansible
play may be removed by using the Keycloak GUI.

## Role variables

```yaml
uas_users:
  - { username: "uastest", password: "uastestpwd",
      uidNumber: "12345", gidNumber: "54321",
      firstName: "Uas", lastName: "User",
      homeDirectory: "/home/uastest",
      loginShell: "/bin/bash" }
```
