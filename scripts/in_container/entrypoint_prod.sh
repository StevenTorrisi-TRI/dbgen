#!/usr/bin/env bash

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

# Might be empty
DBGEN_COMMAND="${1}"

set -euo pipefail

# We want to avoid misleading messages and perform only forward lookup of the service IP address.
# Netcat when run without -n performs both forward and reverse lookup and fails if the reverse
# lookup name does not match the original name even if the host is reachable via IP. This happens
# randomly with docker-compose in Github Actions.
# Since we are not using reverse lookup elsewhere, we can perform forward lookup in python
# And use the IP in NC and add '-n' switch to disable any DNS use.
# Even if this message might be harmless, it might hide the real reason for the problem
# Which is the long time needed to start some services, seeing this message might be totally misleading
# when you try to analyse the problem, that's why it's best to avoid it,
function run_nc() {
    local host=${1}
    local port=${2}
    local ip
    ip=$(python -c "import socket; print(socket.gethostbyname('${host}'))")

    nc -zvvn "${host}" "${port}"
}

function wait_for_connection {
    # Waits for Connection to the backend specified via URL passed as first parameter
    # Detects backend type depending on the URL schema and assigns
    # default port numbers if not specified in the URL.
    # Then it loops until connection to the host/port specified can be established
    # It tries `CONNECTION_CHECK_MAX_COUNT` times and sleeps `CONNECTION_CHECK_SLEEP_TIME` between checks
    local connection_url
    connection_url="${1}"

    local detected_backend=""
    local detected_host=""
    local detected_port=""


    if [[ ${connection_url} != sqlite* ]]; then
        # Auto-detect DB parameters
        # Examples:
        #  postgres://YourUserName:password@YourHostname:5432/YourDatabaseName
        #  postgres://YourUserName:password@YourHostname:5432/YourDatabaseName
        #  postgres://YourUserName:@YourHostname:/YourDatabaseName
        #  postgres://YourUserName@YourHostname/YourDatabaseName
        [[ ${connection_url} =~ ([^:]*)://([^:@]*):?([^@]*)@?([^/:]*):?([0-9]*)/([^\?]*)\??(.*) ]] && \
            detected_backend=${BASH_REMATCH[1]} &&
            # Not used USER match
            # Not used PASSWORD match
            detected_host=${BASH_REMATCH[4]} &&
            detected_port=${BASH_REMATCH[5]} &&
            # Not used SCHEMA match
            # Not used PARAMS match

        echo BACKEND="${BACKEND:=${detected_backend}}"
        readonly BACKEND

        if [[ -z "${detected_port=}" ]]; then
            if [[ ${BACKEND} == "postgres"* ]]; then
                detected_port=5432
            elif [[ ${BACKEND} == "mysql"* ]]; then
                detected_port=3306
            elif [[ ${BACKEND} == "redis"* ]]; then
                detected_port=6379
            elif [[ ${BACKEND} == "amqp"* ]]; then
                detected_port=5672
            fi
        fi
        detected_host=${detected_host:="localhost"}


        # Allow the DB parameters to be overridden by environment variable
        echo DB_HOST="${DB_HOST:=${detected_host}}"
        readonly DB_HOST

        echo DB_PORT="${DB_PORT:=${detected_port}}"
        readonly DB_PORT
        local countdown
        countdown="${CONNECTION_CHECK_MAX_COUNT}"
        while true
        do
            set +e
            local last_check_result
            local res
            last_check_result=$(run_nc "${DB_HOST}" "${DB_PORT}" >/dev/null 2>&1)
            res=$?
            set -e
            if [[ ${res} == 0 ]]; then
                echo
                break
            else
                echo -n "."
                countdown=$((countdown-1))
            fi
            if [[ ${countdown} == 0 ]]; then
                echo
                echo "ERROR! Maximum number of retries (${CONNECTION_CHECK_MAX_COUNT}) reached."
                echo "       while checking ${BACKEND} connection."
                echo
                echo "Last check result:"
                echo
                echo "${last_check_result}"
                echo
                exit 1
            else
                sleep "${CONNECTION_CHECK_SLEEP_TIME}"
            fi
        done
    fi
}

function create_system_user_if_missing() {
    # This is needed in case of OpenShift-compatible container execution. In case of OpenShift random
    # User id is used when starting the image, however group 0 is kept as the user group. Our production
    # Image is OpenShift compatible, so all permissions on all folders are set so that 0 group can exercise
    # the same privileges as the default "airflow" user, this code checks if the user is already
    # present in /etc/passwd and will create the system user dynamically, including setting its
    # HOME directory to the /home/airflow so that (for example) the ${HOME}/.local folder where airflow is
    # Installed can be automatically added to PYTHONPATH
    if ! whoami &> /dev/null; then
      if [[ -w /etc/passwd ]]; then
        echo "${USER_NAME:-default}:x:$(id -u):0:${USER_NAME:-default} user:${DBGEN_HOME}:/sbin/nologin" \
            >> /etc/passwd
      fi
      export HOME="${DBGEN_HOME}"
    fi
}

function wait_for_dbgen_db() {
    # Verifies connection to the Airflow DB
    if [[ -n "${DBGEN__CORE__DB_CONN_STR_CMD=}" ]]; then
        wait_for_connection "$(eval "${DBGEN__CORE__DB_CONN_STR_CMD}")"
    else
        # if no DB configured - use sqlite db by default
        DBGEN__CORE__DB_CONN_STR="${DBGEN__CORE__DB_CONN_STR:="sqlite://${DBGEN_HOME}/dbgen.db"}"
        wait_for_connection "${DBGEN__CORE__DB_CONN_STR}"
    fi
}

function upgrade_db() {
    # Runs airflow db upgrade
    airflow db upgrade || airflow upgradedb || true
}

function wait_for_celery_backend() {
    # Verifies connection to Celery Broker
    if [[ -n "${DBGEN__CELERY__BROKER_URL_CMD=}" ]]; then
        wait_for_connection "$(eval "${DBGEN__CELERY__BROKER_URL_CMD}")"
    else
        DBGEN__CELERY__BROKER_URL=${DBGEN__CELERY__BROKER_URL:=}
        if [[ -n ${DBGEN__CELERY__BROKER_URL=} ]]; then
            wait_for_connection "${DBGEN__CELERY__BROKER_URL}"
        fi
    fi
}

function exec_to_bash_or_python_command_if_specified() {
    # If one of the commands: 'airflow', 'bash', 'python' is used, either run appropriate
    # command with exec or update the command line parameters
    if [[ ${DBGEN_COMMAND} == "bash" ]]; then
       shift
       exec "/bin/bash" "${@}"
    elif [[ ${DBGEN_COMMAND} == "python" ]]; then
       shift
       exec "python" "${@}"
    elif [[ ${DBGEN_COMMAND} == "pytest" ]]; then
       shift
       exec "pytest" "${@}"
    fi
}


CONNECTION_CHECK_MAX_COUNT=${CONNECTION_CHECK_MAX_COUNT:=20}
readonly CONNECTION_CHECK_MAX_COUNT

CONNECTION_CHECK_SLEEP_TIME=${CONNECTION_CHECK_SLEEP_TIME:=3}
readonly CONNECTION_CHECK_SLEEP_TIME

# wait_for_dbgen_db

# The `bash` and `python` commands should also verify the basic connections
# So they are run after the DB check
exec_to_bash_or_python_command_if_specified "${@}"

# Remove "airflow" if it is specified as airflow command
# This way both command types work the same way:
#
#     docker run IMAGE dbgen run
#     docker run IMAGE run
#
if [[ ${DBGEN_COMMAND} == "dbgen" ]]; then
   DBGEN_COMMAND="${2}"
   shift
fi

exec "dbgen" "${@}"
