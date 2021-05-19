# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.12.1] - 2021-05-19
- Update kubernetes client library initialization to 12.0.1 sequence

## [1.12.0] - 2021-05-07
- Remove factory settings for UAI images in favor of dynamic update

## [1.11.8] - 2021-02-17
- Switch to MIT License in preparation for releasing to GitHub

## [1.11.7] - 2021-02-14
- CASMUAS-210 Helm Chart fixes to reapair macvlan route generation

## [1.11.6] - 2021-02-11
- CASMUAS-210 Helm Chart changes to support multiple macvlan routes

## [1.11.5] - 2021-01-25
- CASMUAS-201 Fix uai_compute_network logic in UAI creation

## [1.11.4] - 2020-12-15
- CASMINST-254 Change the macvlan interface to vlan002. Update default UAI image

## [1.11.3] - 2020-11-23
- CASMUAS-196 Add uai_compute_network and sidecar configuration for UAS namespace

## [1.11.2] - 2020-11-10
- CASMUAS-183 Add Administrative UAI Managememt APIs to UAS

## [1.11.1] - 2020-10-26
- CASMUAS-182 Add support for configured UIA / Broker Classes in UAS

## [1.11.0] - 2020-10-26
- CASMUAS-181 Add support for configured Resource Limit / Request overrides in UAS

## [1.10.1] - 2020-10-01
- CASMUAS-176 refactor UAS manager / UAI manager functions to prep for SSH Broker work

## [1.10.0] - 2020-10-01
- Updates to chart(s) to support Helm v3/Loftsman v1

## [1.9.2] - 2020-09-23
- CASMUAS-175 use mount instead of unsquashfs to make UAI images from IMS builds

## [1.9.1] - 2020-09-18
- Fix UAI image generation ansible to work with the 1.3.1 Patch

## [1.9.0]
- Version Re-alignment after 1.3 release
- CASMUAS-164 add resource limits on UAIs to protect management services

## [1.7.2] - 2020-09-09
- CASMUAS-149: Handling of default images is not clean in UAS Admin Config commands

## [1.7.1] - 2020-07-13
- Change the repository where UAI images are kept from bis.local:5000 to registry.local so it can be picked up by Nexus

## [1.7.0] - 2020-06-25
- CASMUAS-126: Because of DST-5600 a version bump is required to get artifacts built

## [1.6.1] - 2020-06-11
- CASMUAS-121: Use nexus repo instead of PRS

## [1.6.0] - 2020-06-11
- CASMUAS-7: back-end implementation of Images and Volumes APIs
- CASMUAS-31: integrate UAS with etcd

## [1.5.0] - 2020-06-04
CASMUAS-9: Remove creation of uastest user
CASMUAS-46: Switch SSH to LoadBalancer IPs

## [1.4.0] - 2020-06-01
CASMUAS-113: Remove cray_uai_hosts tasks and role from playbook

## [1.3.2] - 2020-05-26
- CASMUAS-108: Remove ansible playbooks and roles that aren't used

## [1.3.1] - 2020-05-21
- CASMUAS-114: Update K8s API to support 1.18

## [1.3.0] - 2020-05-18
- CASMUAS-108: Remove taints and label ansible. Switch to not running on uas=False K8s nodes.
- CASMUAS-106: Fix pod affinity label

## [1.2.6] - 2020-05-05
### Changed
- CASMUAS-100: Fix pod restart label

## [1.2.5] - 2020-04-28
### Changed
- CASMUAS-90: Add a changelog and a tool to regenerate the changelog

## [1.2.4] - 2020-04-24
### Changed
- CASMUAS-93: Add support for online upgrades
- CASMUAS-91: Remove PE, UAN, and WLM specific tests

## [1.2.3] - 2020-04-23
### Changed
- CASMUAS-85: Add kubectl during UAI image build

## [1.2.2] - 2020-04-17
### Changed
- CASMUAS-89 fix version per review comment
- CASMUAS-89 Bump Helm Chart Version
- CASMUAS-89 make macvlan use configurable to support vshasta
- CASMUAS-82: Update build trigger to use 1.3 CME

## [1.2.1] - 2020-03-23
### Changed
- CASMCLOUD-963: Fix ct test for all NCNs
- CASMUAS-67: Enable the sles15sp1 UAI image builds
- PE-29504 Clean up macvlan reserved IPs on boot

## [1.2.0] - 2020-03-06
### Changed
- CASMUAS-59: Fix helm template format and images
- PE-29534: Update UAI CT tests to work with PBS
- CASMUAS-61: Add the cray_uai_img role

## [1.1.0] - 2020-02-12
### Changed
- CASMUAS-63: Add debugging for CASMUAS-63
- CASMUAS-58: Add gen-uai-img.sh utility

## [1.0.7] - 2020-02-06
### Changed
- CASMCLOUD-894: Add resources to values.yaml

## [1.0.6] - 2020-01-13
### Changed
- CASMUAS-49: Don't return 22 for an ssh connection string

## [1.0.5] - 2019-12-16
### Changed
- CASMPET-1491: Use Host from request headers to get userinfo

## [1.0.4] - 2019-12-13
### Changed
- CASMUAS-42: Fix portmap for optional ports

## [1.0.3] - 2019-11-21
### Changed
- CASMUAS-37: Fix reference in helm template

## [1.0.2] - 2019-11-21
### Changed
- STP-1027: Add blank lines which corrects header duplication
- STP-1027
- CASMUAS-14: Use bis.local instead of sms.local
- STP-1027: Add descriptive text for resources, reformat workflows.
- CASMUSER-2472, CASMUSER-2473, CASMUSER-2474: Create UAI CT tests
- CASMUSER-2506: Update UAI diagnostics CT test
- CASMUSER-1793: Fix UAS CT test with PBS
- CASMUSER-1050, CASMUSER-2475, CASMUSER-2481: Update UAI CT tests
- CASMUSER-2462: Fix configmap parsing
- CASMUSER-2485: Fix label to search for Keycloak
- CASMUSER-2484: Fix rbac role/rolebinding to use the user namespace
- CASMUSER-2453: Add cray-uas-mgr service account to cray-uas-mgr helm chart

## [1.0.1] - 2019-11-01
### Changed
- CASMUSER-2415: Validate uai_macvlan in networks.yml
- CASMUSER-2433: Update UAI diagnostics CT test
- CASMUSER-2413 and CASMUSER-2402: Update UAS CT tests
- CASMUSER-2414 Get mountain network from UAI subnet
- CASMUSER-2245: Hide Keycloak error info
- Add a Makefile to help automate development
- Change to the Dockerfile to maximize cache usage
- CASMUSER-2412: Bump version and chart version.

## [1.0.0] - 2019-10-24
### Changed
- CASMUSER-2412: Fix localization bug
- CASMUSER-2340 and CASMUSER-2410: Test PBS commands
- CASMUSER-1209: Localization fixes
- CASMUSER-2339: Test SLURM commands
- CASMUSER-1209: Update versions to 1.0.0

## [0.16.0] - 2019-10-18
### Changed
- CASMUSER-1209: Update copyright
- CASMUSER-1209: Address PR comments
- CASMUSER-2366: Update UAN smoke CT test
- CASMUSER-1209: customization play fix
- CASMUSER-1209: Fix localization play for helm
- CASMUSER-2337: Update UAN smoke CT test
- CASMUSER-1209: Fix image handling
- CASMUSER-1209: More fixes for Loftsman/Helm
- CASMUSER-1209: Helm chart support
- CASMUSER-1207: More progress on Helm
- CASMUSER-2338 and CASMUSER-2344: Update UAN CT tests
- CASMUSER-1304: Use port 22 when LoadBalancer is used for ssh
- CASMUSER-2347: upgrade Werkzeug python lib
- CASMUSER-1400: Fix port reporting between LoadBalancer and NodePort

## [0.15.0] - 2019-10-09
### Changed
- CASMUSER-1400: Reset defaults back to NodePort
- CASMUSER-1400: Return the correct ip if loadbalancer
- CASMUSER-1400: Fix unit test
- CASMUSER-1400: Initial work to move to LoadBalancer with BGP
- CASMUSER-2276: support sles15sp1 builds for ncns
- CASMUSER-2345: Test uas-mgr version
- CASMUSER-2336: Update UAN CT tests
- CASMUSER-2335: Delegate cray_uas_mgr tasks to bis

## [0.14.0] - 2019-10-04
### Changed
- CASMUSER-2323: Get SLURM/PBS version
- CASMUSER-2287: switch UAIs to a user namespace

## [0.13.11] - 2019-09-27
### Changed
- CASMUSER-2291:Update a WLM diagnostics script
- CASMUSER-2254: Create a WLM diagnostics script
- CASMUSER-2186: rename managers to bis

## [0.13.10] - 2019-09-21
### Changed
- Revert change made in CASMPET-605
- CASMUSER-2258: Create a UAI CT smoke test
- CASMUSER-2257: check keycloak pods
- Add ip no arp to mac0 interface.
- CASMUSER-2247: make the container useful for debug
- CASMUSER-2183: add copyright headers
- CASMUSER-2153: Remove all references to sms
- CASMUSER-2075: address PR comments

## [0.13.9] - 2019-09-05
### Changed
- CASMUSER-2088: Update uan-smoke.sh
- CASMUSER-1986: Add macvlan checks to UAI diagnostics
- CASMUSER-2075: Add uai-hosts play
- CASMUSER-2134: Specify container when adding users to keycloak
- CASMUSER-1982: Fix cray uas list failures
- CASMUSER-2086: use trusted base for UAS manager

## [0.13.8] - 2019-08-23
### Changed
- CASMUSER-2047: Move a test to a right dir
- CASMUSER-2071: Update uan-smoke.sh
- CASMUSER-2082: Update UAS smoke test
- CASMUSER-1324: Add UAN smoke test
- CASMUSER-2034: use new RPM version format

## [0.13.7] - 2019-08-13
### Changed
- CASMUSER-1979: Create UAI CT test for DST-3133, Mismatch version issue of Cray CLI on SMS and UAI
- CASMUSER-2013: Move macvlan setup/teardown scripts to /opt/cray/uas
- CASMUSER-2024 Move CT tests to user directory
- CASMUSER-1967: Remove UAN ansible plays
- CASMUSER-1923 Update to new DST standards
- CASMUSER-1908: Add play to update motd only
- CASMUSER-1911: Add debug to user creation in keycloak
- CASMUSER-1918: fix macvlan bridge creation

## [0.13.6] - 2019-07-18
### Changed
- CASMUSER-1889: Address PR comments and cleanup
- CASMUSER-1889: update version in swagger.yaml
- CASMUSER-1889: Move uan-config to UAS repo
- CASMUSER-1902: Fix UAN idempotency
- Add missing template action for macvlan teardown
- CASMUSER-1900: Create a new UAI test to verify that BMCs cannot be connected from a UAI
- CASMUSER-1889: Address PR comments and cleanup
- CASMUSER-1889: update version in swagger.yaml
- CASMUSER-1889: Move uan-config to UAS repo

## [0.13.5] - 2019-07-17
### Changed
- CASMUSER-1832: Add UAN role for ldap configuration
- CASMUSER-1886: Remove unused vars
- CASMUSER-1886: Address PR comments
- CASMUSER-1886: Add motd and fix uan-interface gateway
- CASMUSER-1886: Fix task name
- CASMUSER-1886: Set motd on uan and fix gateway
- CASMUSER-1815: Clean up /etc/hosts
- CASMUSER-1709: Add customer network gateway
- CASMUSER-1709: address PR comments
- CASMUSER-1665: Make vlan link configurable
- CASMUSER-1709: Configure UAN networks
- CASMUSER-1665: Scale out labeling of nodes and macvlan setup
- CASMUSER-1874: Use services namespace for Keycloak
- CASMUSER_1760: remove uas_ip/uas_port from output

## [0.13.4] - 2019-07-03
### Changed
- CASMUSER-1859: improve delete performance/status
- CASMUSER-1857: fix false positive in docker check
- Fix Remove portion of mount types
- Update conf_UAS_read_write.sh to make sure that TMPDIR is set.
- Update conf_UAS_read_write.sh one more time for David's comment.
- Update conf_UAS_read_write.sh for David and Jim's comments
- Update conf_UAS_read_write.sh for Matt's comments
- Move one of UAI tests, conf_UAS_read_write.sh, from Health Check to CT
- CASMUSER-1775: fix uas node label requirement
- Fix confusing "error" when waiting
- CASMUSER-1849: make type: unique in config map
- Fix example uai_age in swagger
- CASMUSER-1759: add uai_age field

## [0.13.3] - 2019-06-25
### Changed
- Check for Ready & Labeled nodes
- Add BUILD_NUMBER & git hash to Release
- CASMUSER-1365: add UAI Diagnostics
- STP-644: wording tweeks
- STP-644: minor tweek
- STP-644: Minor tag tweeks
- STP-644: Minor punctuation changes. Move ? to comments.
- work in progress
- swagger.yaml edited online with Bitbucket
- swagger.yaml edited online with Bitbucket
- swagger.yaml edited online with Bitbucket
- STP-628: Clean-up UAS Swagger File
- CASMUSER-1710: Only run keycloak related tasks on one host
- CASMUSER-1469: delete/list UAIs by host/user

## [0.13.2] - 2019-06-09
### Changed
- CASMUSER-1667: check for invalid volume names

## [0.13.1] - 2019-06-07
### Changed
- CASMUSER-1469 (partial) - show host for UAI

## [0.13.0] - 2019-06-10
### Changed
- CASMUSER-1207: Change port to 8088 and fix ansible
- CASMUSER-1207: Migrate cray-uas-mgr to istio

## [0.12.0] - 2019-05-31
### Changed
- CASMUSER-1625: Require a token to use the UAS API
- CASMUSER-1475: get UAIs functional in craystack
- CASMUSER-1479: Remove support for username
- CASMUSER-1615: Add role to add users to compute nodes
- CASMUSER-1612: Change uastest home directory
- CASMUSER-1593 Restart uas-mgr after config change
- CASMUSER-1531: Parameterize macvlan setup
- CASMUSER-1562: Make mac0 bridge persistent
- CASMUSER-1497: Add comment about uastest user
- CASMUSER-1497: Run the cray_uas_user role
- Update version to fix master
- Update helm version to reflect centos removal
- Fix typo
- CASMUSER-1497: Add cray_uas_user role

## [0.11.4] - 2019-05-20
### Changed
- CASMUSER-1542: Remove centos support for UAI
- CASMUSER-1544: Reorganize the crayctl Jenkinsfile
- CASMUSER-1506: Fix unit test
- CASMUSER-1506: Add port 8888 to allowed list of ports
- CASMUSER-1489: Only create mac0 link if it doesn't exist
- CASMUSER-1424: Correct rebase error
- CASMUSER-1424: Add additional port support to UAI NodePort service
- CASMUSER-1431: Add more unit tests
- CASMUSER-1207: minimal helm charts for UAS
- initial filling in of default configmap values
- add service generated Helm chart and tweaks
- CASMUSER-1434: Add checks to auth routines
- CASMUSER-1434: Query Keycloak userinfo if token is sent with API requests

## [0.11.3] - 2019-05-13
### Changed
- CASMUSER-1477: Add test tool deploy.sh to help cray-uas-mgr dev
- Add validation for ssh keys
- Fix swagger examples
- Add a basic API check
- CASMUSER-1220: Add more tests and logging to uas_auth.py
- CASMUSER-1220: Update version

## [0.11.1] - 2019-05-02
### Changed
- CASMUSER-1220: Add UasAuth class
- CASMUSER-1013: make tests use real images
- Update pip requirements
- CASMUSER-1391: Allow for multiple macvlan interfaces

## [0.11.0] - 2019-04-30
### Changed
- CASMUSER-1389: remove code that built our own UAI
- CASMUSER-1374: Make sles15 image the default
- CASMUSER-1335 Allow localization without gwn_ipv4
- CASMUSER-1335 Remove Slurm dependencies
- CASMUSER-1216: Fix uan_info to be uai_info
- CASMUSER-1216: Fix up some rebase errors.
- CASMUSER-1216: Implement macvlan for UAIs
- CASMUSER-1289: Initial Images & Volumes APIs
- CASMUSER-1216: Fix uan_info to be uai_info
- CASMUSER-1216: Fix up some rebase errors.
- CASMUSER-1216: Implement macvlan for UAIs

## [0.10.1] - 2019-04-25
### Changed
- CASMUSER-1296 - add logging
- Changes from CR comments
- Move to sms-functional
- CASMUSER-1356: check libfabric ver in smoke tests
- CASMUSER-1005: better error handling on delete
- CASMUSER-1363: Use .version in spec file and add version validation

## [0.10.0] - 2019-04-22
### Changed
- CASMUSER-1330-ct: Add simple smoke test for UAS
- fix versions to 0.10.0

## [0.9.0] - 2019-04-12
### Changed
- Rename usersshpubkey to publickey
- CASMUSER-458: s/uan/uai/gi
- CASMUSER-1266: failure when uas-id pod isn't ready
- put uas-mgr image on a diet
- CASMUSER-1233: Remove SLES12SP3 as a supported image type
- CASMUSER-1226: probes and wait for install
- CASMUSER-1041: Add summaries and fix tags
- CASMUSER-1066: return 400 on user not found
- CASMUSER-619: Resiliency work for uas-mgr
- Add missing tag "UAS"
- CASMUSER-1041: Consolidate to a single swagger.yaml
- CASMUSER-1041: Update API to openapi 3.0.2

## [0.8.0] - 2019-04-03
### Changed
- Fix CR comment and add 'type' to template
- Fixes from testing customization
- CASMUSER-1123: confirm on delete all UAIs
- CASMUSER-137: match UAI timezone to host
- CASMUSER-1065: Remove uas-mgr-auth installer files
- Remove Versions ref and dont rev API version
- Redo the UAS Config test module to improve coverage
- Fix typo in secret_name and reduce range
- Also make changes to the 2nd swagger file
- CASMUSER-764: code coverage improvements
- Add .vscode to .gitignore
- CASMUSER-982: Cleanup if create_uans should fail
- CASMUSER-1142: Configure slack notifications
- CASMUSER-1084: Update defaults for slurm port range
- CASMUSER-1103: Remove setting external IP on UAIs
- CASMUSER-1068: Address comments, add unittests
- CASMUSER-1068: Add global UAI list and delete function
- CASMUSER-1064: show terminating status
- Address CR comments with dead code removal
- Address code review comments
- Add missing file
- CASMUSER-1033: Prevent accidental deletion of uas_ports value.
- CASMUSER-690: add readiness check for UAIs
- Add specific yaml loader
- CASMUSER-1033: Fix so default image setup runs just once.
- Strip trailing newline from uid info
- CASMUSER-1033: Fix typos.
- CASMUSER-1033: Fix typos.
- CASMUSER-1033: Bump rpm version
- CASMUSER-1033: Expand localization coverage
- CASMUSER-55: Add uas=managed label and fix app=deployment_name
- Switch gitignore pycache to wildcard
- A few small README fixes
- add .gitignore with some reasonable files to ignore
- CASMUSER-977: Address PR comments.
- CASMUSER-977: Refactored cray-uas-mgr localization scheme

## [0.7.0] - 2019-03-07
### Changed
- CASMUSER-175: Fix swagger merge error.
- CASMUSER-175: Add /uas-images endpoint for listing available images

## [0.6.0] - 2019-03-06
### Changed
- CASMCMS-1958 Complex Ansible dependencies significantly slow down installers.
- CASMUSER-966: Add new images to cray-uas-mgr install.
- CASMUSER-937: Update api doc location
- CASMUSER-946: Update service defaults
- CASMUSER-908: Update copyright dates.
- CASMUSER-908: Remove GUI code
- CASMUSER-908: Remove GUI code

## [0.5.0] - 2019-02-15
### Changed
- CASMUSER-918: Update version is spec file.
- CASMUSER-918: Add MetalLB IP pool annotations.
- CASMUSER-895: Set default service types to NodePort and ClusterIP
- CASMUSER-895: Fix indents.
- CASMUSER-895: Make UAI service type configurable
- CASMUSER-895: Fix a problem caught by a unittest.
- CASMUSER-895: Address PR comments, add template and default vars.
- CASMUSER-910: Add serviceaccount for testing
- CASMUSER-895: Test updates
- CASMUSER-895: Make UAI service type configurable

## [0.4.0] - 2019-02-11
### Changed
- CASMUSER-845: Only included relevant files in docker image
- CASMUSER-874: Add uas_mgr_info endpoint to return cray-uas-mgr version.

## [0.2.0] - 2019-02-06
### Changed
- CASMUSER-859: Bump version number
- CASMUSER-859: Bump version number
- CASMUSER-859: Enable auto-select of default image when no image is specified in the CLI
- CASMUSER-775: Make UAI ports configurable
- CASMUSER-776: Fix copyright headers
- CASMUSER-772: Refactor env variables from UAN_* to UAS_* and provide UAS_NAME
- CASMUSER-136: Trigger testing stage in DST
- DST-965: Update rpm name to use crayctldeploy
- Remove chdir
- CASMUSER-679: Add cray-uas-mgr-auth service
- CASMUSER-683: Add ansible role for cray-uas-mgr

## [0.1.0] - 2018-12-03
### Changed
- CASMUSER-669: Fix swagger spec for craycli
- CASMUSER-516-swagger
- CASMUSER-536: Catch UAS manager misconfig where external IPs aren't configured
- CASMUSER-508: Add default image selection for curl endpoints
- CASMUSER-18: Improve status reporting of UAI
- CASMUSER-520: Add UAI affinity
- CASMUSER-224: Added pull-down menu to GUI for image selection.
- UAN-183: Catch missing error check on image variables.
- UAN-183: Make uas-mgr configurable.
- UAN-183: Make uas-mgr configurable.
- UAN-257: Update uan-mgr html access for kong integration.
- UAN-238: Change uas-mgr to use k8s service user
- UAN-238: Change uas-mgr to use k8s service user
- UAN-223: Adopt the naming convention for uas
- UAN-180: Handle the case when looking for containers that don't yet exist.
- UAS-180: Improve status messages.
- UAN-181: Catch missing ssh key on create uan request.
- UAN-164: Change uan-mgr to user k8s secret for cluster config.
- UAN-159: Keep uan deployment name to under 59 characters.
- UAN-148: Catch unknown user in get_user_account_info
- UAN-148: Add support for getting user uid/gid from uas-id service.
- UAN-147: Adding ssh key support.
- UAN-102: Address PR comments. Add image name to output.
- UAN-102: Fix some missed exception handling.
- UAN-102: Initial commit of UAS.
