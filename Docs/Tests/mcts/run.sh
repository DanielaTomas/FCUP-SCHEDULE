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
