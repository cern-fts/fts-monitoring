angular.module('ftsmon.resources', ['ngResource'])
.factory('Job', function($resource) {
	return $resource('jobs/:jobId', {}, {
		query: {method: 'GET',
			    isArray: false},
	})
})
.factory('Files', function($resource) {
	return $resource('jobs/:jobId/files', {}, {
		query: {method: 'GET',
			    isArray: false},
	})
})
//__________________________________________________________
.factory('Job_del', function($resource) {
        return $resource('jobs_del/:jobId', {}, {
                query: {method: 'GET',
                            isArray: false},
        })
})

.factory('Files_del', function($resource) {
        return $resource('jobs_del/:jobId/files', {}, {
                query: {method: 'GET',
                            isArray: false},
       })
})
//__________________________________________________________
.factory('Transfers', function($resource) {
	return $resource('transfers', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('Overview', function($resource) {
	return $resource('overview', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('OverviewActivities', function($resource) {
	return $resource('overview/activities', {}, {
		query: {method: 'GET', isArray: false},
	})
})

.factory('OverviewDeletion', function($resource) {
        return $resource('overview/deletion', {}, {
                query: {method: 'GET', isArray: false},
        })
})

.factory('Optimizer', function($resource) {
	return $resource('optimizer', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('OptimizerDetailed', function($resource) {
	return $resource('optimizer/detailed', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('OptimizerStreams', function($resource) {
	return $resource('optimizer/streams', {}, {
		query: {
            method: 'GET',
            isArray: false,
            transformResponse: function(data, headersGetter) {
                if (data === 'null') {
                    return {null: true};
                }
                return angular.fromJson(data);
            }
        }
	})
})
.factory('Errors', function($resource) {
	return $resource('errors', {}, {
        query: {method: 'GET', isArray: false}
	})
})
.factory('ErrorsForPair', function($resource) {
	return $resource('errors/list', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('ConfigAudit', function($resource) {
	return $resource('config/audit', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('Statistics', function($resource) {
	return $resource('stats/', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('Servers', function($resource) {
	return $resource('stats/servers', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('Database', function($resource) {
	return $resource('stats/database', {}, {
		query: {method: 'GET', isArray: true}
	})
})
.factory('TransferVolume', function($resource) {
    return $resource('stats/volume', {}, {
        query: {method: 'GET', isArray: false}
    })
})
.factory('StatsVO', function($resource) {
	return $resource('stats/vo', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('Unique', function($resource) {
	return $resource('unique/:field', {}, {
		query: {method: 'GET', isArray: true}
	})
})
.factory('ConfigServer', function($resource) {
	return $resource('config/server', {}, {
		all: {method: 'GET', isArray: false}
	})
})
.factory('ConfigStorages', function($resource) {
	return $resource('config/storages', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('ConfigOps', function($resource) {
	return $resource('config/ops', {}, {
		query: {method: 'GET', isArray: true}
	})
})
.factory('ConfigLinks', function($resource) {
	return $resource('config/links', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('ConfigGfal2', function($resource) {
	return $resource('config/gfal2', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('ConfigActivities', function($resource) {
	return $resource('config/activities', {}, {
		query: {method: 'GET', isArray: false}
	})
})
.factory('ActivePerActivity', function($resource) {
	return $resource('config/activities/:vo', {}, {
		query: {method: 'GET', isArray: false}
	})
})
;
