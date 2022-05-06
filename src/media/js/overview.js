
function pairState(pair)
{
	var klasses;

	// No active with submitted is bad, and so it is
	// less than three active and more than three submitted
	if ((!pair.active && pair.submitted) || (pair.active < 2 && pair.submitted >= 2))
		klasses = 'bad-state';
	// Very high rate of failures, that's pretty bad
	else if ((!pair.finished && pair.failed) || (pair.finished / pair.failed <= 0.8))
		klasses = 'bad-state';
	// Less than three actives is so-so
	else if (pair.active < 2)
		klasses = 'underused';
	// More than three active, that's good enough
	else if (pair.active >= 2)
		klasses = 'good-state';
	// High rate of success, that's good
	else if ((pair.finished && !pair.failed) || (pair.finished / pair.failed >= 0.9))
		klasses = 'good-state';
	// Meh
	else
		klasses = '';

	// If any active, always give that
	if (pair.active)
		klasses += ' active';

	return klasses;
}

function mergeAttrs(a, b)
{
	for (var attr in b) {
		if (typeof(b[attr]) == 'string')
			a[attr] = b[attr];
		else
			a[attr] = '';
	}
	return a;
}

function getLimitDescription(limit)
{
    if (!limit)
        return '';

    var descr = 'Limited at ';
    if (limit.bandwidth)
        descr += limit.bandwidth + 'MiB/s';
    if (limit.bandwidth && limit.active)
        descr += ' and ';
    if (limit.active)
        descr += limit.active + ' actives';
    return descr;
}

function OverviewCtrl($rootScope, $location, $scope, $http,  overview, Overview)
{
	$scope.overview = overview;
    $scope.monit_url = SITE_MONIT;
    $scope.alias = SITE_ALIAS;
	// On page change, reload
	$scope.pageChanged = function(newPage) {
		$location.search('page', newPage);
	};

	// Method to choose a style for a pair
	$scope.pairState = pairState;

	// Render a human-readable representation of the limits
	$scope.getLimitDescription = getLimitDescription;

	// Filter
	$scope.filterBy = function(filter) {
		$location.search($.extend({}, $location.$$search, filter));
	}
	// Link info modal pop up
	$scope.Openlink = function(source_se,dest_se) {
		siteurl = window.location.href.slice(0, -2);

		$http.get(siteurl+"linkinfo?source_se="+source_se+"&dest_se="+dest_se).
			then(function(data){
			linkinfodata = angular.fromJson(data).data;
			$scope.Link_all_to_dest = linkinfodata[0].Link_all_to_dest[0] ?? 'N/A';
			$scope.Link_source_to_all = linkinfodata[0].Link_source_to_all[0] ?? 'N/A';
			$scope.link_all_to_all = linkinfodata[0].link_all_to_all[0];
			$scope.active_transfers_dest = linkinfodata[0].active_transfers_dest[0][0] ?? 'N/A';
			$scope.active_transfers_source = linkinfodata[0].active_transfers_source[0][0] ?? 'N/A';
			$scope.optimizer_evolution = linkinfodata[0].optimizer_evolution[0];
			$scope.outbound_max_active_all = linkinfodata[0].outbound_max_active_all[0] ?? 'N/A';
			$scope.outbound_max_active_source = linkinfodata[0].outbound_max_active_source[0] ?? 'N/A';
			// Preventing background scrolling
			$('body').css('overflow','hidden');
			$('body').css('position','fixed');

		})
		};

	// Set timer to trigger autorefresh
	$scope.autoRefresh = setInterval(function() {
		var filter = $location.$$search;
		filter.page = $scope.overview.page;
		loading($rootScope);
        Overview.query(filter, function(updatedOverview) {
            for(var i = 0; i < updatedOverview.overview.items.length; i++) {
                updatedOverview.overview.items[i].show = $scope.overview.overview.items[i].show;
            }
            $scope.overview = updatedOverview;
            stopLoading($rootScope);
        });
	}, REFRESH_INTERVAL);
	$scope.$on('$destroy', function() {
		clearInterval($scope.autoRefresh);
	});
}


OverviewCtrl.resolve = {
	overview: function($rootScope, $location, $q, Overview) {
		loading($rootScope);

		var deferred = $q.defer();

		var page = $location.$$search.page;
		if (!page || page < 1)
			page = 1;

		Overview.query($location.$$search,
  			  genericSuccessMethod(deferred, $rootScope),
			  genericFailureMethod(deferred, $rootScope, $location));

		return deferred.promise;
	}
}