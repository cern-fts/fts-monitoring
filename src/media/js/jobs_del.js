
function searchJob_del(jobList, jobId)
{
    for (j in jobList) {
        if (jobList[j].job_id == jobId)
            return jobList[j];
    }
    return {show: false};
}

function JobListDelCtrl($rootScope, $location, $scope, jobs_del, Job_del)
{
    // Jobs
    $scope.jobs_del = jobs_del;

    // On page change, reload
    $scope.pageChanged = function(newPage) {
        $location.search('page', newPage);
    };

    // Set timer to trigger autorefresh
    $scope.autoRefresh = setInterval(function() {
        loading($rootScope);
        var filter = $location.$$search;
        filter.page = $scope.jobs_del.page;
        Job_del.query(filter, function(updatedJobs) {
            for (j in updatedJobs.items) {
                var job_del = updatedJobs.items[j];
                job_del.show = searchJob_del($scope.jobs_del.items, job_del.job_id).show;
            }
            $scope.jobs_del = updatedJobs;
            stopLoading($rootScope);
        },
        genericFailureMethod(null, $rootScope, $location));
    }, REFRESH_INTERVAL);
    $scope.$on('$destroy', function() {
        clearInterval($scope.autoRefresh);
    });

    // Set up filters
    $scope.filter = {
        vo:          validString($location.$$search.vo),
        source_se:   validString($location.$$search.source_se),
        time_window: withDefault($location.$$search.time_window, 1),
        state:       statesFromString($location.$$search.state),
    }

    $scope.showFilterDialog = function() {
    	document.getElementById('filterDialog').style.display = 'block';
    }

    $scope.cancelFilters = function() {
    	document.getElementById('filterDialog').style.display = 'none';
    }

    $scope.applyFilters = function() {
    	document.getElementById('filterDialog').style.display = 'none';
        $location.search({
            page:        1,
            time_window: $scope.filter.time_window,
            state:       joinStates($scope.filter.state),
        });
    }

    // Method to set class depending on the metadata value
    $scope.classFromMetadata = function(job_del) {
        var metadata = job_del.job_metadata;
        if (metadata) {
            metadata = eval('(' + metadata + ')');
            if (metadata && typeof(metadata) == 'object' && 'label' in metadata)
                return 'label-' + metadata.label;
        }
        return '';
    }
}


JobListDelCtrl.resolve = {
    jobs_del: function($rootScope, $location, $q, Job_del) {
        loading($rootScope);

        var deferred = $q.defer();

        var page = $location.$$search.page;
        if (!page || page < 1)
            page = 1;

        Job_del.query($location.$$search,
              genericSuccessMethod(deferred, $rootScope),
              genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    }
}

/** Job_del view
 */
function JobDelViewCtrl($rootScope, $location, $scope, job_del, files, Job_del, Files_del)
{
    var page = $location.$$search.page;
    if (!page)
        page = 1;

    $scope.itemPerPage = 50;

    $scope.job_del = job_del;
    $scope.files = files;
//__________________________________________________________________________________________
   // $scope.getRemainingTime = function(file) {
   //     if (file.file_state == 'ACTIVE') {
   //             if (file.throughput && file.filesize) {
   //                     var bytes_per_sec = file.throughput * (1024 * 1024);
   //                     var remaining_bytes = file.filesize - file.transferred;
   //                     var remaining_time = remaining_bytes / bytes_per_sec;
   //                     return (Math.round(remaining_time*100)/100).toString() + ' s';
   //            }
   //             else {
   //                     return '?';
   //             }
   //     }
   //     else {
   //             return '-';
   //     }
    //}
//____________________________________________________________________________________________
    // On page change
    $scope.pageChanged = function(newPage) {
        $location.search('page', newPage);
    }

    // Filtering
    $scope.filter = {
        state: statesFromString($location.$$search.state),
        reason: validString($location.$$search.reason),
        file: validString($location.$$search.file),
    }
    $scope.filterByState = function() {
        $location.search('state', joinStates($scope.filter.state));
    }

    $scope.resetReasonFilter = function() {
        $location.search({state: $location.$$search.state});
    }

    // Reloading
    $scope.autoRefresh = setInterval(function() {
        loading($rootScope);
        var filter   = $location.$$search;
        filter.jobId = $scope.job_del.job.job_id;
        Job_del.query(filter, function(updatedJob) {
            $scope.job_del = updatedJob;
        })
        // Do this in two steps so we can copy the show attribute
        Files_del.query(filter, function (updatedFiles) {
            for(var i = 0; i < updatedFiles.files.items.length; i++) {
                updatedFiles.files.items[i].show = $scope.files.files.items[i].show;
            }
            $scope.files = updatedFiles;
            stopLoading($rootScope);
        },
        genericFailureMethod(null, $rootScope, $location));
    }, REFRESH_INTERVAL);
    $scope.$on('$destroy', function() {
        clearInterval($scope.autoRefresh);
    });
}


JobDelViewCtrl.resolve = {
    job_del: function ($rootScope, $location, $route, $q, Job_del) {
        loading($rootScope);

        var deferred = $q.defer();

        var filter = {
            jobId: $route.current.params.jobId
        };
        if ($route.current.params.file)
            filter.file = $route.current.params.file;
        if ($route.current.params.reason)
            filter.reason = $route.current.params.reason;

        Job_del.query(filter,
                  genericSuccessMethod(deferred, $rootScope),
                  genericFailureMethod(deferred, $rootScope));

        return deferred.promise;
    },

    files: function ($rootScope, $location, $route, $q, Files_del) {
        loading($rootScope);

        var deferred = $q.defer();

                var filter = $location.$$search;
        filter.jobId = $route.current.params.jobId
        filter.jobId = $route.current.params.jobId
        Files_del.query(filter,
              function (data) {
                genericSuccessMethod(deferred, $rootScope)(data);
                // If file filter is set, by default show the details
                if ($location.$$search.file) {
                    data.files.items[0].show = true;
                }
              },
              genericFailureMethod(deferred, $rootScope, $location));

        return deferred.promise;
    }
}
