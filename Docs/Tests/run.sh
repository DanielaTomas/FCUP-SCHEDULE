TMLIM=600
INPUT_FILES="comp01.ctt comp02.ctt comp03.ctt comp04.ctt comp05.ctt comp11.ctt"
for CPAR in 1000 500 100 50 10 1 0.1; do
    for SEED in `seq -f "%02g" 1 10`; do
        echo "C=$CPAR, seed=$SEED"
        pypy3 -u mcts_input_parser.py --time_limit=$TMLIM --c_param=$CPAR --seed=$SEED --input_files=$INPUT_FILES
        tar zcvf mcts-$TMLIM-$CPAR-$SEED.tgz mcts_tree/ constraint_progress/ output/ log/ profiler/
        rm -rf mcts_tree/ constraint_progress/ output/ log/ profiler/
    done
done


TMLIM=86400
SEED=1
CPAR=0.1
FILE="comp01.ctt"
echo "input_file=$FILE, time_limit=$TMLIM, C=$CPAR, seed=$SEED"
pypy3 -u mcts_input_parser.py --time_limit=$TMLIM --c_param=$CPAR --seed=$SEED --input_files=$FILE
tar zcvf mcts-$TMLIM-$CPAR-$SEED.tgz mcts_tree/ constraint_progress/ output/ log/ profiler/
rm -rf mcts_tree/ constraint_progress/ output/ log/ profiler/

<<'
echo pypy3 -u -mcts_input_parser.py --time_limit=3600 --c_param=100
pypy3 -u -mcts_input_parser.py --time_limit=3600 --c_param=100
tar zcvf mcts_c100.tgz mcts_tree/ constraint_progress/ output/
rm -rf mcts_tree/ constraint_progress/ output

echo pypy3 -u -mcts_input_parser.py --time_limit=3600 --c_param=10
pypy3 -u mcts_input_parser.py --time_limit=3600 --c_param=10
tar zcvf mcts_c10.tgz mcts_tree/ constraint_progress/ output/
rm -rf mcts_tree/ constraint_progress/ output

echo pypy3 -u -mcts_input_parser.py --time_limit=3600 --c_param=1
pypy3 -u mcts_input_parser.py --time_limit=3600 --c_param=1
tar zcvf mcts_c1.tgz mcts_tree/ constraint_progress/ output/
rm -rf mcts_tree/ constraint_progress/ output
'
