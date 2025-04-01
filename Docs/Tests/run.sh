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

TMLIM=600
for CPAR in 1000 500 200 100 50 20 10 5 2 1; do
    for SEED in `seq -f "%02g" 1 10`; do
        echo "C=$CPAR, seed=$SEED"
        pypy3 -u mcts_input_parser.py --time_limit=$TMLIM --c_param=$CPAR --seed=$SEED
        tar zcvf mcts_time-$TMLIM_C-$CPAR_$SEED.tgz mcts_tree/ constraint_progress/ output/
        rm -rf mcts_tree/ constraint_progress/ output/
    done
done