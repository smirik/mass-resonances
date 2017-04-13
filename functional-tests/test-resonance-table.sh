#!/bin/bash
CURRENT_FILE_PATH=`pwd`/`dirname $0`
python -m resonances rtable JUPITER SATURN > matrix-JS.new
diff matrix-JS.new $CURRENT_FILE_PATH"/"matrix-JS.res
if [[ $? = 0 ]]
then
    rm matrix-JS.new
else
    exit 1
fi
