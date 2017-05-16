#!/bin/bash
CURRENT_FILE_PATH=`pwd`/`dirname $0`
PHASE_DIR=$CURRENT_FILE_PATH"/../.phases_dir"
ETALON_PHASE_DIR=$CURRENT_FILE_PATH"/phases"

rm -r $PHASE_DIR 2>/dev/null
python -m resonances load-resonances --file=$CURRENT_FILE_PATH"/"matrix-JS.res -a 0.01 --start=401 --stop=402 JUPITER SATURN
python -m resonances load-resonances --file=$CURRENT_FILE_PATH"/"matrix-JS.res -a 0.01 --start=463 --stop=464 JUPITER SATURN
python -m resonances load-resonances --file=$CURRENT_FILE_PATH"/"matrix-JS.res -a 0.01 --start=490 --stop=491 JUPITER SATURN

python -m resonances --loglevel=INFO find --aei-paths=$CURRENT_FILE_PATH --start=401 --stop=402 JUPITER SATURN
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:1.rphs" $ETALON_PHASE_DIR"/401JS/phases_+5+2-3.rphs"

python -m resonances --loglevel=INFO find --aei-paths=$CURRENT_FILE_PATH --start=463 --stop=464 JUPITER SATURN
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:2.rphs" $ETALON_PHASE_DIR"/463JS/phases_+2+3-1.rphs"
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:3.rphs" $ETALON_PHASE_DIR"/463JS/phases_+4-2-1.rphs"
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:4.rphs" $ETALON_PHASE_DIR"/463JS/phases_+6-7-1.rphs"
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:5.rphs" $ETALON_PHASE_DIR"/463JS/phases_+6+1-2.rphs"
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:5.rphs" $ETALON_PHASE_DIR"/463JS/phases_+6+1-2.rphs"
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:6.rphs" $ETALON_PHASE_DIR"/463JS/phases_+8-4-2.rphs"

python -m resonances --loglevel=INFO find --aei-paths=$CURRENT_FILE_PATH --start=490 --stop=491 JUPITER SATURN
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:7.rphs" $ETALON_PHASE_DIR"/490JS/phases_+3+3-2.rphs"
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:8.rphs" $ETALON_PHASE_DIR"/490JS/phases_+5-2-2.rphs"
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:9.rphs" $ETALON_PHASE_DIR"/490JS/phases_+7-7-2.rphs"
$CURRENT_FILE_PATH/test-phases.py $PHASE_DIR"/phase:10.rphs" $ETALON_PHASE_DIR"/490JS/phases_+8+1-4.rphs"
