# Copyright notice:
#
# Copyright (C) CERN 2013-2015
#
# Copyright (C) Members of the EMI Collaboration, 2010-2013.
#   See www.eu-emi.eu for details on the copyright holders
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from django.db import models


ACTIVE_STATES        = ['SUBMITTED', 'READY', 'ACTIVE', 'STAGING']
FILE_TERMINAL_STATES = ['FINISHED', 'FAILED', 'CANCELED', 'NOT_USED']
ON_HOLD_STATES         = ['ON_HOLD', 'ON_HOLD_STAGING']
STATES = ACTIVE_STATES + FILE_TERMINAL_STATES + ON_HOLD_STATES

class JobBase(models.Model):
    job_id          = models.CharField(max_length = 36, primary_key = True)
    job_state       = models.CharField(max_length = 32)
    source_se       = models.CharField(max_length = 255)
    dest_se         = models.CharField(max_length = 255)
    job_type        = models.CharField(max_length = 1)
    cancel_job      = models.CharField(max_length = 1)
    cred_id         = models.CharField(max_length = 100)
    vo_name         = models.CharField(max_length = 50)
    reason          = models.CharField(max_length = 2048)
    submit_time     = models.DateTimeField()
    priority        = models.IntegerField()
    submit_host     = models.CharField(max_length = 255)
    max_time_in_queue = models.IntegerField()
    space_token     = models.CharField(max_length = 255)
    internal_job_params = models.CharField(max_length = 255)
    overwrite_flag  = models.CharField(max_length = 1)
    job_finished    = models.DateTimeField()
    source_space_token = models.CharField(max_length = 255)
    copy_pin_lifetime = models.IntegerField()
    checksum_method = models.CharField(max_length = 1)
    bring_online    = models.IntegerField()
    job_metadata    = models.CharField(max_length = 1024)
    retry           = models.IntegerField()
    retry_delay     = models.IntegerField()

    class Meta:
        abstract = True

    def isFinished(self):
        return self.job_state not in ['SUBMITTED', 'READY', 'ACTIVE', 'STAGING']

    def __str__(self):
        return self.job_id


class Job(JobBase):
    class Meta:
        db_table = 't_job'


class FileBase(models.Model):
    file_id      = models.BigIntegerField(primary_key = True)
    hashed_id    = models.IntegerField()
    vo_name      = models.CharField(max_length = 255)
    source_se    = models.CharField(max_length = 255)
    dest_se      = models.CharField(max_length = 255)
    file_state   = models.CharField(max_length = 32)
    transfer_host= models.CharField(max_length = 255)
    source_surl  = models.CharField(max_length = 1100)
    dest_surl    = models.CharField(max_length = 1100)
    staging_host = models.CharField(db_column = 'staging_host', max_length = 1024)
    reason       = models.CharField(max_length = 2048)
    current_failures  = models.IntegerField()
    filesize     = models.FloatField()
    checksum     = models.CharField(max_length = 100)
    finish_time  = models.DateTimeField()
    start_time   = models.DateTimeField()
    internal_file_params = models.CharField(max_length = 255)
    pid          = models.IntegerField()
    tx_duration  = models.FloatField()
    throughput   = models.FloatField()
    transferred  = models.FloatField()
    retry        = models.IntegerField()
    file_metadata     = models.CharField(max_length = 1024)
    user_filesize     = models.FloatField()
    staging_start     = models.DateTimeField()
    staging_finished  = models.DateTimeField()
    bringonline_token = models.CharField(max_length = 255)
    log_file        = models.CharField(max_length = 2048)
    log_debug       = models.IntegerField(db_column = 'log_file_debug')
    activity        = models.CharField(max_length = 255)
    selection_strategy = models.CharField(max_length = 255)

    def get_start_time(self):
        """
        Return staging_start, or start_time or None in that order
        """
        if self.staging_start:
            return self.staging_start
        elif self.start_time:
            return self.start_time
        else:
            return None

    def __str__(self):
        return str(self.file_id)

    class Meta:
        abstract = True


class File(FileBase):
    job = models.ForeignKey('Job', db_column = 'job_id', related_name = '+', null = True)
    class Meta:
        db_table = 't_file'


class DmFile(models.Model):
    file_id       = models.IntegerField(primary_key=True)
    job           = models.ForeignKey('Job', db_column = 'job_id', related_name = '+', null = True)
    file_state    = models.CharField(max_length=32)
    transfer_host = models.CharField(max_length=150, db_column='dmHost')
    source_surl   = models.CharField(max_length=900)
    dest_surl     = models.CharField(max_length=900)
    source_se     = models.CharField(max_length=150)
    dest_se       = models.CharField(max_length=150)
    reason        = models.CharField(max_length=2048)
    checksum      = models.CharField(max_length=100)
    finish_time   = models.DateTimeField()
    start_time    = models.DateTimeField()
    job_finished  = models.DateTimeField()
    tx_duration   = models.FloatField()
    retry         = models.IntegerField()
    user_filesize = models.FloatField()
    file_metadata = models.CharField(max_length=1024)
    activity      = models.CharField(max_length=255)
    dm_token      = models.CharField(max_length=255)
    retry_timestamp = models.DateTimeField()
    hashed_id       = models.IntegerField()
    vo_name         = models.CharField(max_length=100)

    # Compatibility fields, so it can be used as regular file
    filesize = 0
    transferred = 0
    throughput = 0

    def get_start_time(self):
        """
        Return staging_start, or start_time or None in that order
        """
        if self.start_time:
            return self.start_time
        else:
            return None

    def __str__(self):
        return str(self.file_id)

    class Meta:
        db_table = 't_dm'

class RetryError(models.Model):
    attempt  = models.IntegerField()
    datetime = models.DateTimeField()
    reason   = models.CharField(max_length = 2048)

    file_id = models.ForeignKey('File', db_column = 'file_id', related_name = '+', primary_key = True)

    class Meta:
        db_table = 't_file_retry_errors'

    def __eq__(self, b):
        return isinstance(b, self.__class__) and \
            self.file_id == b.file_id and \
            self.attempt == b.attempt


class  ConfigAudit(models.Model):
    # This field is definitely NOT the primary key, but since we are not modifying
    # this from Django, we can live with this workaround until Django supports fully
    # composite primary keys
    datetime = models.DateTimeField(primary_key = True)
    config   = models.CharField(max_length = 4000)
    action   = models.CharField(max_length = 100)

    class Meta:
        db_table = 't_config_audit'

    def simple_action(self):
        return self.action.split(' ')[0]

    def __eq__(self, b):
        return isinstance(b, self.__class__) and \
               self.datetime == b.datetime and \
               self.config == b.config and self.action == b.action


class LinkConfig(models.Model):
    source_se         = models.CharField(max_length = 255, primary_key = True)
    dest_se           = models.CharField(max_length = 255)
    symbolic_name     = models.CharField(max_length = 255, unique=True)
    min_active        = models.IntegerField()
    max_active        = models.IntegerField()
    optimizer_mode    = models.IntegerField()
    tcp_buffer_size   = models.IntegerField()
    nostreams         = models.IntegerField()

    def __eq__(self, b):
        return isinstance(b, self.__class__) and \
               self.source_se == b.source_se and \
               self.dest_se == b.dest_se

    class Meta:
        db_table = 't_link_config'


class Storage(models.Model):
    storage     = models.CharField(max_length=150, primary_key=True)
    site        = models.CharField(max_length=45)
    metadata    = models.TextField()
    ipv6        = models.BooleanField()
    udt         = models.BooleanField()
    debug_level = models.IntegerField()
    inbound_max_active      = models.IntegerField()
    inbound_max_throughput  = models.FloatField()
    outbound_max_active     = models.IntegerField()
    outbound_max_throughput = models.FloatField()

    class Meta:
        db_table = 't_se'


class ShareConfig(models.Model):
    source      = models.CharField(max_length = 255, primary_key = True)
    destination = models.CharField(max_length = 255)
    vo          = models.CharField(max_length = 100)
    active      = models.IntegerField()

    def __eq__(self, b):
        return isinstance(b, self.__class__) and \
               self.source == b.source and \
               self.destination == b.destination and \
               self.vo == b.vo

    class Meta:
        db_table = 't_share_config'


class Optimizer(models.Model):
    source_se  = models.CharField(max_length = 255, primary_key=True)
    dest_se    = models.CharField(max_length = 255)
    datetime   = models.DateTimeField()
    ema        = models.FloatField()
    active     = models.IntegerField()
    nostreams  = models.IntegerField()

    def __eq__(self, other):
        if type(self) != type(other):
            return False

        return self.source_se == other.source_se and \
               self.dest_se   == other.dest_se

    class Meta:
        db_table = 't_optimizer'


class OptimizerEvolution(models.Model):
    datetime     = models.DateTimeField(primary_key = True)
    source_se    = models.CharField(max_length = 255)
    dest_se      = models.CharField(max_length = 255)
    active       = models.IntegerField()
    ema          = models.FloatField()
    throughput   = models.FloatField()
    filesize_avg = models.FloatField()
    filesize_stddev = models.FloatField()
    success      = models.FloatField(db_column = 'success')
    actual_active = models.IntegerField()
    queue_size   = models.IntegerField()
    rationale    = models.TextField()
    diff         = models.IntegerField()

    class Meta:
        db_table = 't_optimizer_evolution'


class Host(models.Model):
    hostname = models.CharField(primary_key = True, max_length = 64)
    beat     = models.DateTimeField()
    service_name = models.CharField()
    drain    = models.IntegerField()

    class Meta:
        db_table = 't_hosts'


class ActivityShare(models.Model):
    vo             = models.CharField(primary_key=True)
    activity_share = models.TextField()
    active         = models.CharField()

    class Meta:
        db_table = 't_activity_share_config'


class OperationLimit(models.Model):
    vo             = models.CharField(db_column='vo_name')
    host           = models.CharField(primary_key=True)
    operation      = models.CharField()
    concurrent_ops = models.IntegerField()

    def __eq__(self, other):
        if type(other) != type(self):
            return False
        return self.vo == other.vo and \
            self.host == other.host and \
            self.operation == other.operation

    class Meta:
        db_table = 't_stage_req'
