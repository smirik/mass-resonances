#!/bin/bash
CURRENT_FILE_PATH=`pwd`/`dirname $0`
PHASE_DIR=$CURRENT_FILE_PATH"/../.phases_dir"
ETALON_PHASE_DIR=$CURRENT_FILE_PATH"/phases"

function testPhases() {
    checkFile=$1
    etalonFile=$2
    diff $checkFile $etalonFile
    if [[ $? -ne 0 ]]; then
        echo "Difference between $checkFile and $etalonFile"
        exit 1
    fi
}

rm -r $PHASE_DIR 2>/dev/null
python -m resonances load-resonances --file=$CURRENT_FILE_PATH"/"matrix-JS.res -a 0.01 --start=401 --stop=402 JUPITER SATURN
python -m resonances load-resonances --file=$CURRENT_FILE_PATH"/"matrix-JS.res -a 0.01 --start=463 --stop=464 JUPITER SATURN
python -m resonances load-resonances --file=$CURRENT_FILE_PATH"/"matrix-JS.res -a 0.01 --start=490 --stop=491 JUPITER SATURN

python -m resonances --loglevel=INFO find --aei-paths=$CURRENT_FILE_PATH --start=401 --stop=402 JUPITER SATURN
testPhases $PHASE_DIR"/phase:1.rphs" $ETALON_PHASE_DIR"/401JS/phases_+5+2-3.rphs"

python -m resonances --loglevel=INFO find --aei-paths=$CURRENT_FILE_PATH --start=463 --stop=464 JUPITER SATURN
testPhases $PHASE_DIR"/phase:2.rphs" $ETALON_PHASE_DIR"/463JS/phases_+2+3-1.rphs"
testPhases $PHASE_DIR"/phase:3.rphs" $ETALON_PHASE_DIR"/463JS/phases_+4-2-1.rphs"
testPhases $PHASE_DIR"/phase:4.rphs" $ETALON_PHASE_DIR"/463JS/phases_+6-7-1.rphs"
testPhases $PHASE_DIR"/phase:5.rphs" $ETALON_PHASE_DIR"/463JS/phases_+6+1-2.rphs"
testPhases $PHASE_DIR"/phase:5.rphs" $ETALON_PHASE_DIR"/463JS/phases_+6+1-2.rphs"
testPhases $PHASE_DIR"/phase:6.rphs" $ETALON_PHASE_DIR"/463JS/phases_+8-4-2.rphs"

python -m resonances --loglevel=INFO find --aei-paths=$CURRENT_FILE_PATH --start=490 --stop=491 JUPITER SATURN
testPhases $PHASE_DIR"/phase:7.rphs" $ETALON_PHASE_DIR"/490JS/phases_+3+3-2.rphs"
testPhases $PHASE_DIR"/phase:8.rphs" $ETALON_PHASE_DIR"/490JS/phases_+5-2-2.rphs"
testPhases $PHASE_DIR"/phase:9.rphs" $ETALON_PHASE_DIR"/490JS/phases_+7-7-2.rphs"
testPhases $PHASE_DIR"/phase:10.rphs" $ETALON_PHASE_DIR"/490JS/phases_+8+1-4.rphs"
