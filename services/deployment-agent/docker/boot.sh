#!/bin/sh
#

# BOOTING application ---------------------------------------------
echo "Booting in ${SC_BOOT_MODE} mode ..."
echo "  User    :`id $(whoami)`"
echo "  Workdir :`pwd`"

if [[ ${SC_BUILD_TARGET} == "development" ]]
then
  echo "  Environment :"
  printenv  | sed 's/=/: /' | sed 's/^/    /' | sort
  #--------------------

  APP_CONFIG=host-dev.yaml

  cd services/deployment-agent
  $SC_PIP install --user -r requirements/dev.txt
  cd /devel

  #--------------------
  echo "  Python :"
  python --version | sed 's/^/    /'
  which python | sed 's/^/    /'
  echo "  PIP :"
  $SC_PIP list | sed 's/^/    /'

elif [[ ${SC_BUILD_TARGET} == "production" ]]
then
  APP_CONFIG=config-prod.yaml
  LOG_LEVEL=info
fi


# RUNNING application ----------------------------------------
if [[ ${SC_BOOT_MODE} == "debug" ]]
then
  LOG_LEVEL=debug
else
  LOG_LEVEL=info
fi

simcore-service-deployment-agent --config $APP_CONFIG --loglevel=$LOG_LEVEL