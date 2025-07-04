
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

function OverviewCtrl($rootScope, $location, $scope, $http, $timeout, overview, Overview)
{
	$scope.overview = overview;
	$scope.monit_url = SITE_MONIT;
	$scope.alias = SITE_ALIAS;
	$scope.linkinfo = LINKINFO
	$scope.fts3_rest_endpnt = FTS3_REST_ENDPNT;
	$scope.overview_cache_autorefresh = OVERVIEW_PAGE_CACHE_AUTOREFRESH.toLowerCase() === "true";

	$scope.overview_cache_refresh = false;
	$scope.overview_cache_refresh_countdown = 0;
	let countdownTimer = null;

	/* Overview Cache Management */
	if ($scope.overview_cache_autorefresh && $scope.overview.overview_cache.cache_stale) {
		var seconds = $scope.overview.overview_cache.cache_update_duration;
		$scope.overview_cache_refresh = true;
		$scope.overview_cache_refresh_countdown = 5 * (Math.floor(seconds / 5) + 1);

		function countdown() {
			if ($scope.overview_cache_refresh_countdown > 0) {
				$scope.overview_cache_refresh_countdown--;
				countdownTimer = $timeout(countdown, 1000);
			} else {
				location.reload();
			}
		}

		countdown();
	}

	$scope.cancelOverviewAutoRefresh = function() {
		if (countdownTimer) {
			$timeout.cancel(countdownTimer);
		}
		$scope.overview_cache_refresh = false;
	}

	$scope.$on('$destroy', function() {
		if (countdownTimer) {
			$timeout.cancel(countdownTimer);
		}
	});

	/* End of Overview Cache Management */

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
	$scope.Openlink = function(source_se, dest_se) {
		let siteurl = "https://" + window.location.host + window.location.pathname;

		if (siteurl.endsWith("/")) {
			siteurl = siteurl.slice(0, -1);
		}

		let modal = document.getElementById("LinkInfoModal");
		modal.style.display = "block";

		$http.get(siteurl + "/linkinfo?source_se=" + source_se + "&dest_se=" + dest_se).
			then(function(data){
			linkinfodata = angular.fromJson(data).data;
			$scope.link_source_act_trans = linkinfodata[0].source["active_transfers"];
			$scope.link_source_outbound_limit = linkinfodata[0].source["outbound_limit"];
			$scope.link_source_conf_type = linkinfodata[0].source["config_type"];
			$scope.link_dest_act_trans = linkinfodata[0].destination["active_transfers"];
			$scope.link_dest_inbound_limit = linkinfodata[0].destination["inbound_limit"];
			$scope.link_dest_conf_type = linkinfodata[0].destination["config_type"];
			$scope.link_act_trans = linkinfodata[0].link["active_transfers"];
			$scope.link_min_lim = linkinfodata[0].link["limits"][0];
			$scope.link_max_lim = linkinfodata[0].link["limits"][1];
			$scope.link_conf_type = linkinfodata[0].link["config_type"];
			$scope.opt_act_trans = linkinfodata[0].optimizer["active_transfers"];
			$scope.opt_decision = linkinfodata[0].optimizer["decision"];
			$scope.opt_desc = linkinfodata[0].optimizer["description"];
			let user_dn_result = linkinfodata[0].user_dn_result;

			// Show source and dest 
			document.getElementById("source_pop").innerHTML = '<b>Source:</b><br>' + source_se;
			document.getElementById("dest_pop").innerHTML = '<b>Destination:</b><br>' + dest_se;

			// If the user has rights, display config links for Storage and Link
			if (user_dn_result === 1) {
				document.getElementById("config_link").innerHTML =
				'<HR width="70%"><center>  <button id="StorageConfig" type="button" class="btn btn-primary"> Storage Config </button> | <button id="LinkConfig"  type="button" class="btn btn-primary" > Link Config </button></center>';
			}

			document.getElementById("StorageConfig").onclick = function () {
				OpenStorageConfig()
			};
			document.getElementById("LinkConfig").onclick = function () {
				OpenLinkConfig()
			};

			function OpenStorageConfig() {
				window.open($scope.fts3_rest_endpnt + "/config/se")
			}

			function OpenLinkConfig() {
				window.open($scope.fts3_rest_endpnt + "/config/links")
			}

			// Prevent background scrolling when modal popup is open
			$('#LinkInfoModal').modal().on('shown', function(){
				$('html, body').css({
					overflow: 'hidden'
				});
			}).on('hidden', function(){
				$('html, body').css({
					overflow: 'auto'
				});
			})
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
