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
#
# This file incorporates work covered by the following copyright and
# permission notice:
#
#  Copyright (C) 2009-2014:
#     Jean Gabes, naparuba@gmail.com
#     Grégory Starck, g.starck@gmail.com
#     Sebastien Coavoux, s.coavoux@free.fr

#  This file is part of Shinken.
#
#  Shinken is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  Shinken is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with Shinken.  If not, see <http://www.gnu.org/licenses/>.

#
# This file is used to test reading and processing of config files
#

from .alignak_test import *


class TestMacroModulations(AlignakTest):

    def setUp(self):
        super(TestMacroModulations, self).setUp()
        self.setup_with_file('cfg/cfg_macros_modulation.cfg')
        assert self.conf_is_correct

    def test_macros_modulation(self):
        """ Test macros modulation """
        # Get the host
        host = self._scheduler.hosts.find_by_name("modulated_host")
        assert host is not None
        assert host.macromodulations is not None

        # Get its macros modulations
        mod = self._scheduler.macromodulations.find_by_name("MODULATION")
        assert mod is not None
        assert mod.get_name() == "MODULATION"
        assert mod.is_active(self._scheduler.timeperiods)
        assert mod.uuid in host.macromodulations

        mod2 = self._scheduler.macromodulations.find_by_name("MODULATION2")
        assert mod2 is not None
        assert mod2.get_name() == "MODULATION2"
        assert mod2.is_active(self._scheduler.timeperiods)
        assert mod2.uuid in host.macromodulations

        # Get the host service
        svc = self._scheduler.services.find_srv_by_name_and_hostname("modulated_host",
                                                                     "modulated_service")

        # Service is going CRITICAL/HARD ... this forces an host check!
        assert len(host.checks_in_progress) == 0
        self.scheduler_loop(1, [[svc, 2, 'BAD']])
        self.show_checks()
        assert len(host.checks_in_progress) == 1
        for c in host.checks_in_progress:
            print("Check: %s / %s" % (c, self._scheduler.checks[c]))
        for c in host.checks_in_progress:
            # The host has a custom macro defined as UNCHANGED
            # The host has 2 attached modulations impacting this macro value.
            # The first one with the value MODULATED and the second with NOT_THE_GOOD.
            # Both are currently active, but we want to get the first one
            assert 'plugins/nothing MODULATED' == self._scheduler.checks[c].command
