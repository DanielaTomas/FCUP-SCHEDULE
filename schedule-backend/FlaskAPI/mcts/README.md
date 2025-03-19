# Installation

* Install [PyPy](https://pypy.org/download.html)

* Ensure pip is installed for PyPy:
    ```SHELL
    $ pypy -m ensurepip
    ```
    
* Install ``graphviz`` and ``plotly`` libraries:
    ```SHELL
    $ pypy -m pip install graphviz # depending on your OS, you may also need to install the Graphviz system package

    $ pypy -m pip install plotly
    ```

# How to run

* Run the main script:
    ```SHELL
    $ cd FCUP-SCHEDULE/schedule-backend/FlaskAPI/mcts
    $ pypy mcts_input_parser.py --time_limit <seconds> --iterations <num_iterations> --c_param <c_parameter> --input_files <file_1> ... <file_n> --seed <random_number>
    ```
    * **``--time_limit`` (optional):** Sets the maximum execution time in seconds (**default:** 300 seconds)

    * **``--iterations`` (optional):** Specifies the maximum number of iterations for the MCTS algorithm (**default:** unlimited unless a stopping condition is met)

    * **``--c_param`` (optional):** Specifies the ``C`` parameter for the MCTS algorithm (**default:** 1.4).

    * **``--input_files`` (optional):** Specifies the list of input files to process from the input folder (**default:** processes all 21 competition files from comp01.ctt to comp21.ctt).

    * **``--seed (optional):`` (optional):** Set the seed for the random number generator to ensure reproducibility (**default:** random).

    * Example:
        ```SHELL
        $ pypy mcts_input_parser.py --time_limit 600 --iterations 1000 --input_files comp01.ctt comp02.ctt --seed 42
        ```
        * This command will run the MCTS algorithm with a 10-minute time limit, 1000 iterations, on comp01.ctt and comp02.ctt, and with a fixed random seed (42).

* After running the script, the following folders will be created (if they do not already exist) and populated with the respective outputs:
    * **``output`` folder:** Contains the best solution (simulation result) encountered during the execution of the MCTS algorithm;

    * **``final_output`` folder:** Contains the final solution, which is the result obtained by following the tree's best path;
        * This folder is only created if the algorithm successfully finds a complete path, which may not happen due to the typically vast search space
        * This solution does not necessarily match the results in the output folder

    * **``log`` folder :** Contains the best solution found over time;

    * **``constraint_progress`` folder:** Contains HTML plots that display the evolution of hard and soft constraint values over the iterations;

    * **``mcts_tree`` folder :** Contains a Graphviz-generated file displaying the tree structure.
        * To include a label in each node, modify the ``visualize_tree`` function in ``debug.py``:      
            * Modify ``label = ""`` to include meaningful information about the node, such as the node's score or visit count
            * Then ensure you have: 
                ```PY 
                dot.node(str(id(node)), label=label, shape="plaintext", width="0.01", height="0.01")
                ```
                instead of:
                ```PY 
                dot.node(str(id(node)), label=label, shape="point", width="0.01", height="0.01")
                ```
    * **Note:** Generating ``constraint_progress`` and especially ``mcts_tree`` can be time-consuming. To disable them, you can comment out the following lines at the end of the ``mcts.py`` file respectively:
        ```PY
        plot_progress(self.iterations_data, self.current_hard_values, self.best_hard_values, self.current_soft_values, self.best_soft_values, f"{input_file_name}_constraint_progress.html")

        visualize_tree(self.root, f"{input_file_name}_tree")
        ```

* After running the script, the ``test_results.xlsx`` file will also be generated.
    * Contains the log information for all the runs, formatted as an Excel sheet;
    * Only generated when all 21 instances have been processed;
    * Each run refers to the processing of all 21 instances (comp01.ctt to comp21.ctt)
    * If the file already exists, the script will not overwrite it. Instead, it will add a new sheet for each run, ensuring that the existing data is preserved. 

* The [ITC-2007 validator](https://www.eeecs.qub.ac.uk/itc2007/curriculmcourse/course_curriculm_index_files/validation.htm) can be used to verify the correctness of the generated timetables:
    * Ensure you have g++ installed. Then, compile the ``validator.cc`` file:
        ```SHELL
        $ g++ validator.cc -o validator
        ```
    * Execute the compiled binary by providing the input and output file paths as command-line arguments. 
        * Example:
            ```SHELL
            $ ./validator "input/comp01.ctt" "output/comp01_output.txt"
            ```
