// Config audit
function ConfigAuditCtrl($rootScope, $location, $scope, config, ConfigAudit)
{
    $scope.config = config;

    // Filter
    $scope.filter = {
        action:   validString($location.search().action),
        user:     validString($location.search().user),
        contains: validString($location.search().contains)
    };

    $scope.applyFilters = function() {
        $location.search({
            page:        1,
            action:   $scope.filter.action,
            user:     $scope.filter.user,
            contains: $scope.filter.contains
        });
    }

    // On page change, reload
    $scope.pageChanged = function(newPage) {
        $location.search('page', newPage);
    };

    // Set timer to trigger autorefresh
    $scope.autoRefresh = setInterval(function() {
        loading($rootScope);
        var filter = $location.search();
        filter.page = $scope.config.page;
        ConfigAudit.query(filter, function(updatedConfigAudit) {
            $scope.config = updatedConfigAudit;
            stopLoading($rootScope);
        },
        genericFailureMethod(null, $rootScope, $location));
    }, REFRESH_INTERVAL);
    $scope.$on('$destroy', function() {
        clearInterval($scope.autoRefresh);
    });

    $scope.showFilterDialog = function() {
        document.getElementById('filterDialog').style.display = 'block';
    }
}

ConfigAuditCtrl.resolve = {
    config: function ($rootScope, $location, $route, $q, ConfigAudit) {
        loading($rootScope);

        var deferred = $q.defer();

        ConfigAudit.query($location.search(),
              genericSuccessMethod(deferred, $rootScope),
              genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    }
}

/// Config server
function ConfigServerCtrl($location, $scope, server)
{
    $scope.server = server;
}

ConfigServerCtrl.resolve = {
    server: function ($rootScope, $location, $route, $q, ConfigServer) {
        loading($rootScope);

        var deferred = $q.defer();

        ConfigServer.all(
              genericSuccessMethod(deferred, $rootScope),
              genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    }
}

/// Config links
function ConfigLinksCtrl($location, $scope, links) {
    $scope.links = links;

    // On page change, reload
    $scope.pageChanged = function(newPage) {
        $location.search('page', newPage);
    };
}

ConfigLinksCtrl.resolve = {
    links: function($rootScope, $location, $route, $q, ConfigLinks) {
        loading($rootScope);

        var deferred = $q.defer();

        ConfigLinks.query($location.search(),
              genericSuccessMethod(deferred, $rootScope),
              genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    },
}

/// Config storages
function ConfigStoragesCtrl($location, $scope, storages, ops) {
    $scope.storages = storages;
    $scope.ops = ops;

    // On page change, reload
    $scope.pageChanged = function(newPage) {
        $location.search('page', newPage);
    };
}

ConfigStoragesCtrl.resolve = {
    storages: function($rootScope, $location, $route, $q, ConfigStorages) {
        loading($rootScope);

        var deferred = $q.defer();

        ConfigStorages.query($location.search(),
              genericSuccessMethod(deferred, $rootScope),
              genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    },

    ops: function($rootScope, $location, $route, $q, ConfigOps) {
        loading($rootScope);

        var deferred = $q.defer();

        ConfigOps.query($location.search(),
              genericSuccessMethod(deferred, $rootScope),
              genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    },
}

/// Gfal2 configuration
function Gfal2Ctrl($location, $scope, gfal2) {
    $scope.gfal2 = gfal2;
}

Gfal2Ctrl.resolve = {
    gfal2: function($rootScope, $location, $q, ConfigGfal2) {
        loading($rootScope);

        var deferred = $q.defer();

        ConfigGfal2.query($location.search(),
              genericSuccessMethod(deferred, $rootScope),
              genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    }
}

/// Activities
function ActivitiesCtrl($location, $scope, activities) {
    $scope.activities = activities;
    $scope.filter = $location.search();
}

ActivitiesCtrl.resolve = {
    activities: function ($rootScope, $location, $q, ConfigActivities) {
        loading($rootScope);

        var deferred = $q.defer();

        ConfigActivities.query($location.search(),
            genericSuccessMethod(deferred, $rootScope),
            genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    }
}

/// Active per vo activities
function _plotDataFromCount(activeCount, key)
{
    var points = [];
    for (var activity in activeCount) {
        if (activity[0] != '$') {
            var value = undefinedAsZero(activeCount[activity]['count'][key]);
            points.push(value);
        }
    }
    if (points)
        return points;
    else
        return null;
}

function VoActivePerActivitiesCtrl($location, $scope, $route, activeCount) {
    $scope.vo = $route.current.params.vo;
    $scope.activeCount = activeCount;

    var colors = [
        '#366DD8', '#D836BE', '#D8A136', '#36D850', '#5036D8', '#D8366D', '#BED836', '#36D8A1', '#A136D8', '#D85036'
    ];

    var labels = []
    for (state in activeCount) {
        if (state[0] != '$') {
            labels.push(state);
        }
    }

    new Chart(document.getElementById("submittedPlot"), {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: _plotDataFromCount(activeCount, 'SUBMITTED'),
                backgroundColor: colors
            }],
        },
        options: {
            title: {
                display: true,
                text: "Submitted per activity"
            }
        }
    });

    new Chart(document.getElementById("activePlot"), {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: _plotDataFromCount(activeCount, 'ACTIVE'),
                backgroundColor: colors
            }],
        },
        options: {
            title: {
                display: true,
                text: "Actives per activity"
            }
        }
    });
}

VoActivePerActivitiesCtrl.resolve = {
    activeCount: function($rootScope, $location, $route, $q, ActivePerActivity) {
        loading($rootScope);

        var deferred = $q.defer();

        var filter = $location.$$search;
        filter.vo = $route.current.params.vo;

        ActivePerActivity.query(filter,
            genericSuccessMethod(deferred, $rootScope),
            genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    }
}
