# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from fractions import gcd
from typing import Any


# Numeric functions
# ------------------
def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def roundfloat(x: Any) -> float:
    output = round(float(x), 3)
    return abs(output) if output == 0 else output


def safe_div(x: float, y: float) -> float:
    try:
        return x / y
    except ZeroDivisionError:
        return 0.0
