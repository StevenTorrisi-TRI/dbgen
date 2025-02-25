#   Copyright 2021 Modelyst LLC
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from sqlalchemy.dialects.postgresql import BYTEA, JSON, JSONB, UUID
from sqlalchemy.types import (
    ARRAY,
    VARCHAR,
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum,
    Integer,
    Interval,
    LargeBinary,
    String,
    Text,
)
from sqlmodel.sql.sqltypes import GUID, AutoString
