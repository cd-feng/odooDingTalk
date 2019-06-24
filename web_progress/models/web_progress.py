# Part of web_progress. See LICENSE file for full copyright and licensing details.
from odoo import models, api, registry, fields, _, SUPERUSER_ID
from odoo.exceptions import UserError
from threading import RLock
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)
lock = RLock()
# track time between progress reports
last_report_time = {}


class WebProgress(models.TransientModel):
    _name = 'web.progress'
    _description = "Operation Progress"
    _transient_max_hours = 0.5
    # store recursion depth for every operation
    _recur_depths = {}
    # progress reports data
    _progress_data = {}
    # time between progress reports (in seconds)
    _progress_period_secs = 5

    msg = fields.Char("Message")
    code = fields.Char("Code", required=True, index=True)
    recur_depth = fields.Integer("Recursion depth", index=True, default=0)
    progress = fields.Integer("Progress")
    done = fields.Integer("Done")
    total = fields.Integer("Total")
    state = fields.Selection([('ongoing', "Ongoing"),
                              ('done', "Done"),
                              ('cancel', "Cancelled"),
                              ], "State")
    cancellable = fields.Boolean("Cancellable")

    #
    # Called by web client
    #

    @api.model
    def cancel_progress(self, code=None):
        """
        Register cancelled operation
        :param code: web progress code
        """
        vals = {
            'code': code,
            'state': 'cancel',
        }
        _logger.info('Cancelling progress {}'.format(code))
        self._create_progress([vals], notify=False)

    @api.model
    def get_progress(self, code=None, recur_depth=None):
        """
        Get progress for given code
        :param code: web progress code
        :param recur_depth: recursion depth
        """
        result = []
        domain = []
        if recur_depth is not None:
            domain.append(('recur_depth', '=', recur_depth))
        if code:
            domain.append(('code', '=', code))
        if domain:
            progress_id = self.search(domain, order='create_date DESC,recur_depth DESC', limit=1)
        else:
            progress_id = self.env[self._name]
        # check progress of parent operations
        if recur_depth is None and progress_id.recur_depth:
            for parent_depth in range(progress_id.recur_depth):
                result += self.get_progress(code, recur_depth=parent_depth)
        progress_vals = {
            'msg': progress_id.msg,
            'code': progress_id.code,
            'progress': progress_id.progress,
            'done': progress_id.done,
            'total': progress_id.total,
            'state': progress_id.state,
            'cancellable': progress_id.cancellable,
            'uid': progress_id.create_uid.id,
            'user': progress_id.create_uid.name,
        }
        # register this operation progress
        result.append(progress_vals)

        return result

    @api.model
    def get_all_progress(self):
        """
        Get progress information for all ongoing operations
        """
        query = """
        SELECT DISTINCT
        FIRST_VALUE(CASE WHEN state = 'ongoing' AND done != total THEN id END) 
            OVER (PARTITION BY code ORDER BY create_date DESC, recur_depth DESC) AS id
        FROM web_progress
        WHERE recur_depth = 0 {user_id}
        """.format(user_id=self.env.user.id != SUPERUSER_ID and "AND create_uid = {}".format(self.env.user.id) or '')
        # superuser has right to see (and cancel) progress of everybody
        # _logger.info(query)
        self.env.cr.execute(query)
        result = self.env.cr.fetchall()
        progress_ids = self.browse([r[0] for r in result if r[0]]).sorted('code')
        # compute real progress when there are recursive progress calls
        progress_real = {}
        for progress_id in progress_ids:
            progress = 0
            progress_total = 100
            deep_progress_list = progress_id.get_progress(progress_id.code)
            if len(deep_progress_list) <= 1:
                progress = progress_id.progress
            else:
                for el in deep_progress_list:
                    if el['progress'] and el['total']:
                        progress += el['progress'] * progress_total / 100
                    if el['total']:
                        progress_total /= el['total']
            progress_real[progress_id.code] = round(progress, 0)
        return [{'msg': progress_id.msg,
                 'code': progress_id.code,
                 'progress': progress_real[progress_id.code],
                 'done': progress_id.done,
                 'total': progress_id.total,
                 'state': progress_id.state,
                 'cancellable': progress_id.cancellable,
                 'uid': progress_id.create_uid.id,
                 } for progress_id in progress_ids]

    #
    # Protected members called by backend
    # Do not call them directly
    #

    @api.model
    def _report_progress(self, data, msg='', total=None, cancellable=True, log_level="info"):
        """
        Progress reporting generator
        :param data: collection / generator to iterate onto
        :param msg: msg to mass in progress report
        :param total: provide total directly to avoid calling len on data (which fails on generators)
        :param cancellable: indicates whether the operation is cancellable
        :param log_level: log level to use when logging progress
        :return: yields every element of iteration
        """
        # web progress_code typically comes from web client in call context
        code = self.env.context.get('progress_code')
        if total is None:
            total = len(data)
        if not code or total <= 1:
            # no progress reporting when no code and for singletons
            for elem in data:
                yield elem
            return
        with lock:
            recur_depth = self._get_recur_depth(code)
            if recur_depth:
                self._recur_depths[code] += 1
            else:
                self._recur_depths[code] = 1
        params = dict(code=code, total=total, msg=msg, recur_depth=recur_depth,
                      cancellable=cancellable, log_level=log_level)
        try:
            for done, rec in zip(range(total), data):
                params['done'] = done
                params['progress'] = round(100 * done / total, 2)
                params['state'] = done >= total and 'done' or 'ongoing'
                self._report_progress_do_percent(params)
                yield rec
        finally:
            # finally record progress as finished
            self._report_progress_done(params)
            with lock:
                self._recur_depths[code] -= 1
                if not self._recur_depths[code]:
                    del self._recur_depths[code]

    @api.model
    def _get_recur_depth(self, code):
        """
        Get current recursion depth
        :param code: web progress code
        :return: current recursion depth
        """
        with lock:
            recur_depth = self._recur_depths.get(code, 0)
        return recur_depth

    @api.model
    def _create_progress(self, vals_list, notify=True):
        """
        Create a web progress record
        Creation uses a fresh cursor, i.e. outside the current transaction scope
        :param vals: list of creation vals
        :return: None
        """
        if not vals_list:
            return
        code = vals_list[0].get('code')
        with api.Environment.manage():
            with registry(self.env.cr.dbname).cursor() as new_cr:
                # Create a new environment with new cursor database
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                # with_env replace original env for this method
                progress_obj = self.with_env(new_env)
                for vals in vals_list:
                    progress_obj.create(vals)  # isolated transaction to commit
                # notify bus
                if notify:
                    progress_notif = progress_obj.get_progress(code)
                    new_env['bus.bus'].sendone('web_progress', progress_notif)
                new_env.cr.commit()

    @api.model
    def _check_cancelled(self, params):
        """
        Check if operation was not cancelled by the user.
        The check is executed using a fresh cursor, i.e., it looks outside the current transaction scope
        :param code: web progress code
        :return: (recordset) res.users of the user that cancelled the operation
        """
        code = params.get('code')
        with api.Environment.manage():
            with registry(self.env.cr.dbname).cursor() as new_cr:
                # use new cursor to check for cancel
                query = """
                SELECT create_uid FROM web_progress
                WHERE code = %s AND state = 'cancel' AND recur_depth = 0 
                    AND (create_uid = %s OR create_uid = %s)
                """
                new_cr.execute(query, (code, self.env.user.id, SUPERUSER_ID))
                result = new_cr.fetchall()
                if result:
                    return self.create_uid.browse(result[0])
        return False

    def _get_parent_codes(self, params):
        """
        Get list of precise codes of all parents
        """
        code = params.get('code')
        return [code + '##' + str(d) for d in range(params.get('recur_depth'))]

    def _get_precise_code(self, params):
        """
        Get precise code, i.e. progress code + recurency depth level
        """
        return params.get('code') + '##' + str(params.get('recur_depth'))

    def _report_progress_do_percent(self, params):
        """
        Progress reporting function
        At the moment this only logs the progress.
        :param params: dict with parameters:
            done: how much items processed
            total: total of items to process
            msg: message for progress report
            recur_depth: recursion depth
            cancellable: indicates whether the operation is cancellable
        :return: None
        """
        # check the time from last progress report
        global last_report_time
        code = params.get('code')
        precise_code = self._get_precise_code(params)
        time_now = datetime.now()
        with lock:
            last_ts = last_report_time.get(code)
            if not last_ts:
                last_ts = (time_now - timedelta(seconds=self._progress_period_secs + 1))
            self._progress_data[precise_code] = dict(params)
        period_sec = (time_now - last_ts).total_seconds()
        # report progress every time period
        if period_sec >= self._progress_period_secs:
            if params.get('cancellable', True):
                user_id = self._check_cancelled(params)
                if user_id:
                    raise UserError(_("Operation has been cancelled by") + " " + user_id.name)
            self._report_progress_store(params)
            with lock:
                last_report_time[code] = time_now

    def _report_progress_done(self, params):
        """
        Report progress as done.
        :param code: progress operation code
        :param total: total units
        :param msg: logging message
        :param recur_depth: recursion depth
        :param cancellable: indicates whether the operation is cancellable
        :return:
        """
        precise_code = self._get_precise_code(params)
        params['progress'] = 100
        params['done'] = params['total']
        params['state'] = 'done'
        code = params.get('code')
        if params.get('iter_depth'):
            # done sub-level progress, lazy report
            ret = self._report_progress_do_percent(params)
        else:
            # done main-level progress, report immediatelly
            self._progress_data[precise_code] = dict(params)
            ret = self._report_progress_store(params)
            with lock:
                # remove last report time for this code
                if code in last_report_time:
                    del last_report_time[code]
        # remove data for this precise code code
        with lock:
            if precise_code in self._progress_data:
                del self._progress_data[precise_code]
        return ret

    def _report_progress_prepare_vals(self, params):
        vals = {k:v for k,v in params.items() if k in self._fields}
        return vals

    def _report_progress_store(self, params):
        """
        Progress storing function. Stores progress in log and in db.
        :param code: progress operation code
        :param percent: done percent
        :param done: done units
        :param total: total units
        :param msg: logging message
        :param recur_depth: recursion depth
        :param cancellable: indicates whether the operation is cancellable
        :param state: state of progress: ongoing or done
        """
        codes = self._get_parent_codes(params)
        codes.append(self._get_precise_code(params))
        vals_list = []
        for precise_code in codes:
            with lock:
                progress_data = self._progress_data.get(precise_code)
            log_message = "Progress {code} {level} {progress}% ({done}/{total}) {msg}".format(
                level=(">" * (progress_data.get('recur_depth') + 1)),
                **progress_data)
            log_level = progress_data.get('log_level')
            if hasattr(_logger, log_level):
                logger_cmd = getattr(_logger, log_level)
            else:
                logger_cmd = _logger.info
            logger_cmd(log_message)
            vals_list.append(self._report_progress_prepare_vals(progress_data))
        self._create_progress(vals_list)

