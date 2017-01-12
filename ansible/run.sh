#!/usr/bin/env bash

if [ "$DEBUG" == "true" ]
then
   source ./hacking/env-setup
else
   source ./hacking/env-setup -q
fi

PARAMS=""
EXTRA_VARS=""

if [ -z $ROLE ]
then
    echo "No role supplied, use command: export ROLE=XXXXX"
    exit 1
fi

if [ -z $ENVIRONMENT ]
then
    echo "No role supplied, use command: export ENVIRONMENT=XXXXX"
    exit 1
fi
echo "========================================================="
echo "========================================================="
echo ""
echo "Ansible: $(cat VERSION)"
echo ""
echo ""
echo "Start ansible for:"
echo "    Role: $ROLE"

if [ ! -z "$STATE" ]
then
   echo "    With state: $STATE"
   PARAMS="$PARAMS --extra-vars state=$STATE"
fi

if [ ! -z "$LIMITS" ]
then
   echo "    With limits: $LIMITS"
   PARAMS="$PARAMS --limit $LIMITS"
fi

if [ "$CHECK" == "true" ]
then
   echo "    Test run: $CHECK"
   PARAMS="$PARAMS --check"
fi

if [ "$DIFF" == "true" ]
then
   echo "    Diff: $DIFF"
   PARAMS="$PARAMS --diff"
fi

if [ "$DEBUG" == "true" ]
then
   echo "    Debug: $DEBUG"
   PARAMS="$PARAMS -vvvv"
fi

if [ ! -z "$EXTRA_PARAMS" ]
then
   echo "    Extra params: $EXTRA_PARAMS"
   PARAMS="$PARAMS $EXTRA_PARAMS"
fi

echo "========================================================="
echo ""
echo "EXEC string:"
echo "ansible-playbook -i environments/${ENVIRONMENT} playbooks/$ROLE $PARAMS"
echo ""
echo ""
echo "========================================================="
echo ""

ansible-playbook -i environments/${ENVIRONMENT} playbooks/$ROLE $PARAMS
