# Test Plan for User Access Service (UAS)

The following is the test plan for the User Access Service (UAS).  The tests are grouped in three categories:
- Unit tests
- Integration tests
- Sanity tests

## Unit Tests

Unit tests are standalone tests run automatically every time UAS is built and are intended to verify the internal logic of UAS.  Where the functionality under test requires access to an external service or sub-system that can be mocked, the expected behavior of the service or sub-system is mocked to permit testing of logic based on expected external behaviors.  Where functionality relies on external functionality that cannot be mocked, that functionality cannot be tested directly so the unit tests test around the external functionality as much as possible.  This results in incomplete coverage by unit tests.  Currently the minimum required test coverate for UAS is 75% of the combined unit test and functional code.
|Summary|Description|Automated|Notes|
|-------|-----------|---------|-----|
|Create an Auth Object|Auth Objectes are created when a user operation is attempted, for example creating or listing UAIs in legacy mode|yes|test_uas_auth.py:test_UasAuth|
|Get passwd entry from Auth Object|Auth objectes compose `/etc/passwd` style strings for use in creating legacy mode UAIs|yes|test_uas_auth.py:test_createPasswd|
|Detect Missing Attributes|An Auth object learns user Attributes from Keycloak, but receives proposed attributes in a JWT for legacy mode. Test the function that identifies missing attributes in the JWT attributes for error reporting|yes|test_uas_auth.py:test_missingAttributes|
|Validate User Info|An Auth object validates arttributes proposed in a JWT against Keycloak attributes.  Test this function.|yes|test_uas_auth.py:test_validUserinfo|
|Get user info with bad token|Test that trying to retrieve user information from an Auth object using an invalid token fails with an internal server error|yes|test_uas_auth.py:test_user_info|
|Test Auth timeout exception logging|Verify that timeout exception handling while using Keycloak to create an Auth object produces the appropriate logging|yes|test_uas_auth.py:test_timeout|
|Test Auth connection error logging|Verify that conection errors seen while using Keycloak to create Auth object produce appropriate logging|yes|test_uas_auth.py:test_connection_error|
|Test Auth request handling|Verify that the various possible results for Keycloak requests are handled  correctly|yes|test_uas_auth.py:tests_requests|
|500 responses in Auth|Test that 500 responses seen in Auth objects raise the correct werkzeug exception from UAS|yes|test_uas_auth.py:test_500|
|404 responses in Auth|Test that 404 responses seen in Auth objects raise the correct werkzeug exception from UAS|yes|test_uas_auth.py:test_404|
|Bad JSON in Auth|Test invalid JSON responses seen in Auth objects raise the correct werkzeug exception from UAS|yes|test_uas_auth.py:test_invalid_json_returned|
|Get Basic UAS Configs|Test retrieving UAS basic configurations from various config objects|yes|test_uas_cfg.py:test_get_config|
|Get UAI image registrations|Test retrieving all UAI Image registrations from the UAS configuration|yes|test_uas_cfg.py:test_get_images|
|Get Default Image Registration|Test retrieving the default image registration from the UAS|yes|test_uas_cfg.py:test_get_default_image|
|Validate non-existent image|Test that attempting to validate the image name of an image that has not been configured fails as expected|yes|test_uas_cfg.py:test_validate_image_no_defaults|
|Validate non-existent image|Test trying to validate an image name of an image that is not in the configuration|yes|test_uas_cfg.py:test_validate_image_false NOTE: there appear to be two unit tests that do this same test in slightly different ways|
|Get external IP|Test retrieving the configured IP Address for non-load-balancer UAIs with public IPs (this is an obsolete configuration of UAIs but the code still exists)|yes|test_uas_cfg.py:test_get_external_ip|
|Volume Mount Generation|Test the Config object's volume mount generation logic|yes|test_uas_cfg.py:test_gen_volume_mounts|
|Get Volumes|Test retrieving the list of configured volumes from the UAS configuration|yes|test_uas_cfg.py:test_get_volumes|
|Generate Port List Entry|Test the Config object port list entry generation logic|yes|test_uas_cfg.py:test_gen_port_entry|
|Generate Port List|Test the Config object port list generation logic|yes|test_uas_cfg.py:test_uas_cfg_gen_port_list|
|Generate Port List for Service|Test the Config object port list generation logic for service UAIs|yes|test_uas_cfg.py:test_uas_cfg_svc_gen_port_list|
|Create Readiness Probe|Test the Configuration object's readiness probe creation logic|yes|test_uas_cfg.py:test_create_readiness_probe|
|Get Valid Optional Ports|Test the Config object's logic for getting the list of valid optional ports for legacy mode UAI creation from the basic configuration|yes|test_uas_cfg.py:test_get_valid_optional_ports|
|Get Service Type|Test getting the basic UAI Service Type from the Config object (no Bifurcated CAN specific tests)|yes|test_uas_cfg.py:test_get_service_type|
|Get Service Type with Bi-CAN Variations No Required Bi-CAN|Test getting UAI Service Types from the Config object with all of the various supported Bifurcated CAN configurations and some selected unsupported configurations / results with the `require_bican` configuration setting set not specified (default false) to verify correct behavior in both supported and unsupported conditions|yes|test_uas_cfg.py:test_get_service_type_bican_no_require|
|Get Service Type with Bi-CAN Variations Required Bi-CAN False|Test getting UAI Service Types from the Config object with all of the various supported Bifurcated CAN configurations and some selected unsupported configurations / results with the `require_bican` configuration setting set to false to verify correct behavior in both supported and unsupported conditions|yes|test_uas_cfg.py:test_get_service_type_bican_require_false|
|Get Service Type with Bi-CAN Variations With Required Bi-CAN|Test getting UAI Service Types from the Config object with all of the various supported Bifurcated CAN configurations and some selected unsupported configurations / results with the `require_bican` configuration setting set to true to verify correct behavior in both supported and unsupported conditions|yes|test_uas_cfg.py:test_get_service_type_bican_require_true|
|Valid Host Path Mount Type|Test the host-path mount type validator logic in the Config object for volumes|yes|test_uas_cfg.py:test_is_valid_host_path_mount_type|
|Validate SSH Key|Test the SSH key validator logic in the Config object|yes|test_uas_cfg.py:test_validate_ssh_key|
|Valid Volume Name|Test the volume name validator logic in the Config object|yes|test_uas_cfg.py:test_is_valid_volume_name|
|Volume Descriptor Errors|Test construction and content of the volume descriptor error exception classes defined by the UAS configuration logic|yes|test_uas_cfg.py:test_vol_desc_errors|
|Get UAI Namespace|Test getting the basic UAS configuration indicating the default UAI namespace|yes|test_uas_cfg.py:test_get_uai_namespace|
|Data Model Expandale Get|Test logic in the UAS Data Model that is used to allow un-resolved references between configuration objects to be handled gracefully when expanding the contents of a configuration object|yes|test_uas_cfg.py:test_data_model_expandable_get|
|Delete UAI By Name|Test the UAS API entrypooint that deletes UAIs by name.  This test just verifies that the error condition created by trying to delete an empty list of UAIs reaches the code that will error out expecting a non-empty list.  Other unit tests test the underlying behavior for other cases.|yes|test_uas_controller.py:test_delete_uai_by_name|
|Get UAS Images|Test the UAS API entrypoint that retrieves the list of UAI images.  This test just verifies that the API reaches the code to get an empty list of images.  Other unit tests verify behavior for other cases.|yes|test_uas_controller.py:test_get_uas_images|
|Get UAI Image Registrations (admin)|Test the UAS Admin API for getting a list of UAI image Registrations and verify that it returns a list of images.|yes|test_uas_controller.py:test_get_uas_images_admin|
|Create UAI Image Registration (admin)|Test the UAS Admin API for creating a new UAI image registration|yes|test_uas_controller.py:test_create_uas_image_admin|
|Get UAS Image Registration (admin)|Test the UAS Admin API for getting information about a single UAI Image Registration|yes|test_uas_controller.py:test_get_uas_image_admin|
|Update UAI Image Registration (admin)|Test the UAS Admin API for updating a UAI Image registration|yes|test_uas_controller.py:test_update_uas_image_admin|
|Delete UAI Image Registration (admin)|Test the UAS Admin API for deleting a UAI Image registration|yes|test_uas_controller.py:test_delete_uas_image_admin|
|Get UAS Volume List (admin)|Test the UAS Admin API for listing UAS Volume Configuration|yes|test_uas_controller.py:test_get_uas_volumes_admin|
|Create UAS Volume (admin)|Test the UAS Admin API for creating a UAS volume specification|yes|test_uas_controller.py:test_create_uas_volume_admin|
|Get UAS Volume (admin)|Test the UAS Admin API for rettrieving a specific UAS volume specification|yes|test_uas_controller.py:test_get_uas_volume_admin|
|Update UAS Volume|Test the UAS Admin API for updating a UAS volume specification|yes|test_uas_controller.py:test_update_uas_volume_admin|
|Delete UAS Volume|Test the UAS Admin API for deleting a UAS volume specification|yes|test_uas_controller.py:test_delete_uas_volume_admin|
|Get UAS Resource List|Test the UAS Admin API for listing UAS Resource specifications|yes|test_uas_controller.py:test_get_uas_resources_admin|
|Get UAS Resource|Test the UAS Admin API for retrieving a specific UAS Resource specification|yes|test_uas_controller.py:test_get_uas_resource_admin NOTE: this includes creating a test resource which implicitly tests the Create UAS Resource API|
|Update UAS Resource|Test the UAS Admin API for updating a UAS Resource specification|yes|test_uas_controller.py:test_update_uas_resource_admin|
|Delete UAS Resource|Test the UAS Admin API for deleting UAS Reource specifications|yes|test_uas_controller.py:test_delete_uas_resource_admin|
|Get UAI Class (admin)|Test the UAS Admin API for retrieving a UAI Class from the UAS config|yes|test_uas_controller.py:test_get_uas_class_admin|
|Update UAI Class (admin)|Test the UAS Admin API for updating a UAI class in the UAS config|yes|test_uas_controller.py:test_update_uas_class_admin NOTE: this also creates test UAI Classes to test with through the API so tests that functionality implicitly|
|Delete UAI Class|Test the UAS Admin API for deleting a UAI class from the UAS config|yes|test_uas_controller.py:test_delete_uas_class_admin|
|Delete UAS Local Config|Test the UAS Admin API for deleting the entire local UAS configuration|yes|test_uas_controller.py:test_delete_local_config_admin|
|Test UAS MGR Init|This test seems to do nothing, probably obsolete|yes|test_uas_mgr.py:test_uas_mgr_init NOTE: this test should probably be removed|
|Construct a UAI Class|Test the UAS Internal operation of constructing a new UAI Class|yes|test_uas_mgr.py:test_construct_uai_class|
|Generate UAI Labels|Test the UAS Internal operation of generating Kubernetes labels for a UAI|yes|test_uas_mgr.py:test_gen_labels|
|UAI Instance|Test the UAS Internal operation of creating a UAI instance object used to deploy a UAI|yes|test_uas_mgr.py:test_uai_instance|
|Get UAI Environment|Test the UAS Internal operation of getting the passed in environment from a UAI image|yes|test_uas_mgr.py:test_get_env|
|Create Job Object|Test the UAS Internal operation of creating a Kubernetes Job structure for deploying a UAI|yes|test_uas_mgr.py:test_create_job_object|
|Create Service Object|Test the UAS Internal operation of creating a Kubernetes Service structure for deploying a UAI|yes|test_uas_mgr.py:test_create_service_object|
|Generate Connetion String|Test the UAS Internal operation of generating an SSH connection string with a '-p <port>' option for a UAI|yes|test_uas_mgr.py:test_gen_connection_string|
|Generate Connection String No Port|Test the UAS Internal operation of generating an SSH conection string with no '-p <port>' option for a UAI|yes|test_uas_mgr.py:test_gen_connection_string_no_port|
|Image Lifecycle|Test the UAS Internal operations involved in a UAI Image registration lifecycle (create, get, update, list, delete)|yes|test_uas_mgr.py:test_image_lifecycle|
|Host Path Volume Lifecycle|Test the UAS Internal operations involved in a 'host-path' type volume lifecycle (create, get, update, list, delete)|yes|test_uas_mgr.py:test_host_path_lifecycle|
|Config Map Volume Lifecycle|Test the UAS Internal operations involved in a 'configmap' type volume lifecycle (create, get, update, list, delete)|yes|test_uas_mgr.py:test_config_map_lifecycle|
|Secret Volume Lifecycle|Test the UAS Internal operations involved in a 'secret' type volume lifecycle (create, get, update, list, delete)|yes|test_uas_mgr.py:test_secret_lifecycle|
|Get Pod Age|Test the UAS Internal operation of getting the age of a UAI pod|yes|test_uas_mgr.py:test_get_pod_age|
|Version Controller Root Get|Test getting the 'root' API version from the internal version controller ('v1')|yes|test_uas_versions_controller.py:test_root_get|



## Integration Tests

Integration tests are tests run on new releases of the code and on existing releases of the code deployed on new platforms or platform versions.  They verify that the expected external behaviors mocked in the unit tests are actually seen on the platform, and that any code that could not be tested stand-alone due to mocking limitations has been shown to work in a real-world environment.  We do not currently have integration test coverage metrics, and the UAS integration tests are performed manually.  As automation is added for integration tests this test plan will be updated to reflect those improvements.

NOTE: the planned automated sanity tests are pretty comprehensive, but currently they are not automated.  Since the sanity testing plan is to automate those, and those will provide a good integration workout, once those are automated, this table of tests will, most likely move to the Sanity Tests section and be replaced with a single test that invokes those and checks the result.

|Summary|Description|Automated|Notes|
|-------|-----------|---------|-----|
|Wait for UAS update|Wait for / verify that uas-update job is completed|no|This is a gating test for all other integration tests. It ensures that the UAS manager is running and that the up-to-date factory configuration has been merged with the UAS configuration.|
|Verify required basic UAI image|Make sure that the basic (HPE supplied) UAS image to be used with the tests is in place|no|If the required image is not present, then update-uas failed in some way and we can't proceed with the testing|
|Verify required basic UAI class is configured|Make sure that the basic (HPE supplied) UAI calss for sanity testing is in place|no|If the required class is not present, then update-uas failed in some way and we can't proceed with the testing|
|Create a non-public End-User UAI|Use the administrative UAI creationg API endpoint to create a UAI using the basic sanity testing UAI class and image with a test user and test user keys|no|This demonstrates that end-user UAIs can be created|
|Log into and validate non-public UAI|Use SSH to log into the end-user UAI created above and run ps(1) to show it works|no|This demostrates that the basic UAI image works for creating UAIs|
|List UAIs|Use the admin UAI management API to list UAIs by owner and by class and verify that the UAI is found|no|This demonstrates that UAI listing works and that the by owner and by class selection filtering works|
|Delete the end-user UAI|Delete the previously created UAI by owner and list uais to see that it goes away|no|This demonstrates UAI deletion works, the by owner and by class selection filtering has already been tested above|
|Verify that end-user UAI K8s elements are removed|Use the K8s API to look for the service, job and pods of the previously deleted UAI and make sure they are gone|no|This ensures that UAI resources do not leak when UAIs are delete|

## Sanity Tests

Sanity tests are tests that are run upon installation or whenever the behavior of the UAS is in question.  They provide an indication of whether the UAS is functioning correctly and diagnosis of common installation problems that can arise for the UAS.  The UAS sanity tests are currently manual.  As automation is added, this test plan will be updated to reflect those improvements, probably removing the tests listed below in favor of automation of the integration tests above.

NOTE: these manual sanity tests are described in the [UAS / UAI Documentation](https://github.com/Cray-HPE/docs-csm/blob/release/1.2/operations/UAS_user_and_admin_topics/UAS_and_UAI_Health_Checks.md)

|Summary|Description|Automated|Notes|
|-------|-----------|---------|-----|
|Create end-user UAI (legacy mode)|Use the `cray uas create` command to create a UAI in legacy mode|no|This demonstrates that a UAI can be created|
|List UAIs (legacy mode)|Use the `cray uas list` command to list UAIs|no|This demonstrates that the created UAI is actually created and gives the user a way to know when it is running (or see any problems it is having getting to a running state)|
|SSH to UAI|Log into the UAI using SSH and run ps(1)|no|This demonstrates that the UAI is running and accepting logins|
|Delete the UAI|Use the `cray uas delete` command to delete the UAI created above|no|This demonstrates that a UAI can be deleted|
|List UAIs|Use the `cray uas list` command to list UAIs again|no|This demonstrates that a deleted UAI is actually gone|
