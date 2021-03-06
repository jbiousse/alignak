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

from .alignak_test import AlignakTest
from collections import namedtuple
from alignak.util import average_percentile


class TestUtils(AlignakTest):
    def setUp(self):
        super(TestUtils, self).setUp()

    def test_average_percentile(self):
        # No values
        my_values = []
        lat_avg, lat_min, lat_max = average_percentile(my_values)
        assert lat_avg is None
        assert lat_min is None
        assert lat_max is None

        my_values = [10, 8, 9, 7, 3, 11, 7, 13, 9, 10]
        lat_avg, lat_min, lat_max = average_percentile(my_values)
        print(("result: %.2f, %.2f, %.2f" % (lat_min, lat_avg, lat_max)))
        assert 8.7 == lat_avg, 'Average'
        assert 4.8 == lat_min, 'Minimum'
        assert 12.1 == lat_max, 'Maximum'
