# cray-uas-mgr Helm chart

In most cases the resources here should be left at their defaults. Should you need to add additional resources to your helm chart, you have the ability to do so. If you find that you're making changes that might be able to other Cray services, you're encouraged to submit a pull request to [the base service chart](https://stash.us.cray.com/projects/CLOUD/repos/cray-charts/browse/stable/cray-service).

# To Do:

Before this can be put in the Loftsman manifest the following need to be done:

To Do:
- need to populate port into the config map - related to the bullet below.
- need to test with ansible localization - not sure a great way to do this, but it sounds like the Cloud team is weighing options so waiting is probably the best course here.
- figure out what to do with uas-id container - preferably it's gone before we transition to Helm
- uncomment the CA volume, right now since the ca config map isn't available in loftsman we cannot test if this is enabled. It's also possible, but not proven, that we won't need this at all when keycloak moves to Istio.

