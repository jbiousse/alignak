#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015-2018: Alignak team, see AUTHORS.txt file for contributors
#
# This file is part of Alignak.
#
# Alignak is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Alignak is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Alignak.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import sys
import time
import signal
import json

import subprocess
from time import sleep
import requests
import shutil
import psutil

import pytest
from alignak_test import AlignakTest

from alignak.http.generic_interface import GenericInterface
from alignak.http.receiver_interface import ReceiverInterface
from alignak.http.arbiter_interface import ArbiterInterface
from alignak.http.scheduler_interface import SchedulerInterface
from alignak.http.broker_interface import BrokerInterface


class TestLaunchArbiter(AlignakTest):
    def setUp(self):
        super(TestLaunchArbiter, self).setUp()

        # copy the default shipped configuration files in /tmp/etc and change the root folder
        # used by the daemons for pid and log files in the alignak.ini file
        if os.path.exists('/tmp/etc/alignak'):
            shutil.rmtree('/tmp/etc/alignak')

        if os.path.exists('/tmp/var'):
            shutil.rmtree('/tmp/var')

        if os.path.exists('/tmp/alignak.log'):
            os.remove('/tmp/alignak.log')

        if os.path.exists('/tmp/monitoring-logs.log'):
            os.remove('/tmp/monitoring-logs.log')

        print("Preparing configuration...")
        shutil.copytree('../etc', '/tmp/etc/alignak')
        files = ['/tmp/etc/alignak/alignak.ini']
        replacements = {
            '_dist=/usr/local/': '_dist=/tmp',
            'user=alignak': ';user=alignak',
            'group=alignak': ';group=alignak'
        }
        self._files_update(files, replacements)

        # # Clean the former existing pid and log files
        # print("Cleaning pid and log files...")
        # for daemon in ['arbiter-master', 'scheduler-master', 'broker-master',
        #                'poller-master', 'reactionner-master', 'receiver-master']:
        #     if os.path.exists('/tmp/var/run/%s.pid' % daemon):
        #         os.remove('/tmp/var/run/%s.pid' % daemon)
        #     if os.path.exists('/tmp/var/log/%s.log' % daemon):
        #         os.remove('/tmp/var/log/%s.log' % daemon)
        self.req = requests.Session()

    def tearDown(self):
        print("Test terminated!")

    def _ping_daemons(self, daemon_names=None):
        # -----
        print("Pinging the daemons: %s" % daemon_names)
        satellite_map = {
            'arbiter': '7770', 'scheduler': '7768', 'broker': '7772',
            'poller': '7771', 'reactionner': '7769', 'receiver': '7773'
        }
        for name, port in satellite_map.items():
            if daemon_names and name not in daemon_names:
                continue
            print("- pinging %s: http://localhost:%s/ping" % (name, port))
            raw_data = self.req.get("http://localhost:%s/ping" % (port))
            data = raw_data.json()
            assert data == 'pong', "Daemon %s  did not ping back!" % name
        # -----

    def _stop_daemons(self, daemon_names=None):
        # -----
        print("Stopping the daemons: %s" % daemon_names)
        satellite_map = {
            'arbiter': '7770', 'scheduler': '7768', 'broker': '7772',
            'poller': '7771', 'reactionner': '7769', 'receiver': '7773'
        }
        for name, port in satellite_map.items():
            if daemon_names and name not in daemon_names:
                continue
            print("- stopping %s: http://localhost:%s/stop_request" % (name, port))
            raw_data = self.req.get("http://localhost:%s/stop_request?stop_now=1" % (port))
            data = raw_data.json()
            print("- response = %s" % data)
        # -----

    def test_arbiter_no_daemons(self):
        """ Run the Alignak Arbiter - all the expected daemons are missing

        :return:
        """
        # All the default configuration files are in /tmp/etc

        # Update monitoring configuration file name
        files = ['/tmp/etc/alignak/alignak.ini']
        replacements = {
            ';CFG=%(etcdir)s/alignak.cfg': 'CFG=%(etcdir)s/alignak.cfg',
            # ';log_cherrypy=1': 'log_cherrypy=1'

            'polling_interval=5': 'polling_interval=1',
            'daemons_check_period=5': '',
            'daemons_stop_timeout=10': 'daemons_stop_timeout=5',
            ';daemons_start_timeout=0': 'daemons_start_timeout=0',
            ';daemons_dispatch_timeout=0': 'daemons_dispatch_timeout=0',

            'user=alignak': ';user=alignak',
            'group=alignak': ';group=alignak',
            #
            # ';alignak_launched=1': 'alignak_launched=1',
            # ';is_daemon=1': 'is_daemon=0'
        }
        self._files_update(files, replacements)

        args = ["../alignak/bin/alignak_arbiter.py", "-e", "/tmp/etc/alignak/alignak.ini"]
        arbiter = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("%s launched (pid=%d)" % ('arbiter', arbiter.pid))

        # Sleep some few seconds because of the time needed to start the processes,
        # poll them and declare as faulty !
        sleep(30)

        # The arbiter will have stopped!

        ret = arbiter.poll()
        print("*** Arbiter exited with: %s" % ret)
        assert ret == 4
        ok = True
        for line in iter(arbiter.stdout.readline, b''):
            if 'WARNING:' in line:
                ok = False
                # Only WARNING because of missing daemons...
                if 'that we must be related with cannot be connected' in line:
                    ok = True
                if 'Add failed attempt for' in line:
                    ok = True
                if 'as dead, too much failed attempts' in line:
                    ok = True
                # if 'Exception: Server not available:' in line:
                #     ok = True
                if 'as dead :(' in line:
                    ok = True
                if 'is not alive for' in line:
                    ok = True
                if 'ignoring repeated file: ' in line:
                    ok = True
                if 'directory did not exist' in line:
                    ok = True
                if 'Cannot call the additional groups setting with ' in line:
                    ok = True
                if '- satellites connection #1 is not correct; ' in line:
                    ok = True
                if '- satellites connection #2 is not correct; ' in line:
                    ok = True
                if '- satellites connection #3 is not correct; ' in line:
                    ok = True
                if ok:
                    print("... " + line.rstrip())
                else:
                    print(">>> " + line.rstrip())

                assert ok
            if 'ERROR:' in line:
                # Only ERROR because of configuration sending failures...
                if 'The connection is not initialized for reactionner-master' in line:
                    ok = True
                assert ok
            # if 'CRITICAL:' in line:
            #     ok = False
        assert ok
        ok = True
        for line in iter(arbiter.stderr.readline, b''):
            print("*** " + line.rstrip())
            if 'All the daemons connections could not be established ' \
               'despite 3 tries! Sorry, I bail out!' not in line:
                ok = False
        if not ok and sys.version_info > (2, 7):
            assert False, "stderr output!"

    def test_arbiter_daemons(self):
        """ Run the Alignak Arbiter - all the expected daemons are started by the arbiter

        :return:
        """
        # All the default configuration files are in /tmp/etc

        # Update monitoring configuration file name
        files = ['/tmp/etc/alignak/alignak.ini']
        replacements = {
            ';CFG=%(etcdir)s/alignak.cfg': 'CFG=%(etcdir)s/alignak.cfg',
            # ';log_cherrypy=1': 'log_cherrypy=1',

            'polling_interval=5': 'polling_interval=1',
            'daemons_check_period=5': 'daemons_check_period=2',
            'daemons_stop_timeout=10': 'daemons_stop_timeout=5',
            ';daemons_start_timeout=0': 'daemons_start_timeout=0',
            ';daemons_dispatch_timeout=0': 'daemons_dispatch_timeout=0',

            'user=alignak': ';user=alignak',
            'group=alignak': ';group=alignak',
            #
            ';alignak_launched=1': 'alignak_launched=1',
            ';is_daemon=1': 'is_daemon=0'
        }
        self._files_update(files, replacements)

        args = ["../alignak/bin/alignak_arbiter.py", "-e", "/tmp/etc/alignak/alignak.ini"]
        arbiter = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("%s launched (pid=%d)" % ('arbiter', arbiter.pid))

        # Sleep some few seconds because of the time needed to start the processes,
        # poll them and declare as faulty !
        sleep(10)

        # The arbiter will NOT have stopped! It is still running
        ret = arbiter.poll()
        assert ret is None
        print("Started...")

        # self._ping_daemons()
        # sleep(2)
        #
        # self._ping_daemons()
        # sleep(2)
        #
        # self._ping_daemons()
        # sleep(2)

        print("Killing one daemon process...")
        # self._stop_daemons(['receiver'])
        for daemon in ['receiver']:
            for proc in psutil.process_iter():
                if daemon not in proc.name():
                    continue
                if getattr(self, 'my_pid', None) and proc.pid == self.my_pid:
                    continue
                print("- killing %s" % (proc.name()))

                try:
                    daemon_process = psutil.Process(proc.pid)
                except psutil.NoSuchProcess:
                    print("not existing!")
                    continue

                os.kill(proc.pid, signal.SIGKILL)
                time.sleep(2)
                # daemon_process.terminate()
                try:
                    daemon_process.wait(10)
                except psutil.TimeoutExpired:
                    print("***** timeout 10 seconds, force-killing the daemon...")
                    daemon_process.kill()

        # self._ping_daemons()
        # sleep(2)

        # Sleep some few seconds to let the arbiter manage the daemon failure
        sleep(30)

        # This function will only send a SIGTERM to the arbiter daemon
        # self._stop_daemons(['arbiter'])
        self._stop_alignak_daemons(arbiter_only=True)