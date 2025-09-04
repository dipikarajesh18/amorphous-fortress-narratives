import multiprocessing
from evolution import (
    setup_models_and_data, 
    pre_encode_data,
    novelty_search, 
    map_elites,
    export_ns_archive,
    export_me_archive,
    run_algorithm,
    plot_fitness
)
import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def read_story_specific_mcs():
    """Read story-specific main characters from logs/ent_mc_names.txt"""
    story_mcs = {}
    try:
        with open('exp_config/ent_mc_names.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if line and ' - ' in line:
                    story_name, mcs = line.split(' - ')
                    # Store ALL MC options (they're separated by |)
                    mc_options = [mc.strip() for mc in mcs.split('|')]
                    story_mcs[f'{story_name}.txt'] = mc_options
    except FileNotFoundError:
        print("Warning: exp_config/ent_mc_names.txt not found, using default MCs")
        return {
            'castle2.txt': ['person'],
            'drunk_sokoban.txt': ['person'], 
            'zelda.txt': ['person'],
            'lock_n_key.txt': ['person']
        }
    return story_mcs

def run_experiment(story_file, CONFIG_FILE, set_mc=False, experiment_name="experiment"):
    # Initialize models and data for each worker process
    setup_models_and_data(data_path='bank_files')
    pre_encode_data(use_file=True)
    
    for algorithm in ['novelty_search', 'map_elites']:
        print(f"Running {experiment_name} with {algorithm} for {story_file}...")
        if set_mc:
            # Set the MC to the first option from the story-specific MCs
            STORY_SPECIFIC_MCS = read_story_specific_mcs()
            if story_file in STORY_SPECIFIC_MCS:
                mc_options = STORY_SPECIFIC_MCS[story_file]
                for mc in mc_options:
                    run_algorithm(algorithm, f'sifted_logs/{story_file}', CONFIG_FILE=CONFIG_FILE, export=True, experiment_name=f"{experiment_name}_MC-{mc}", set_mc=mc)
        else:
            run_algorithm(algorithm, f'sifted_logs/{story_file}', CONFIG_FILE=CONFIG_FILE, export=True, experiment_name=experiment_name)

if __name__ == "__main__":
    stories = [
        'castle2.txt', 
        'drunk_sokoban.txt', 
        'zelda.txt', 
        'lock_n_key.txt'
    ]

    # # # Experiment 1: Pure Random
    # print("Running Experiment 1: Pure Random")
    # CONFIG_FILE = 'exp_config/pure_random_experiment.yaml'
    # with multiprocessing.Pool(processes=2) as pool:
    #     pool.starmap(run_experiment, [(story_file, CONFIG_FILE, False, "exp1_pure_random") for story_file in stories])

    # # Experiment 2: Random MC + Associations
    print("Running Experiment 2: Random MC + Associations")
    CONFIG_FILE = 'exp_config/random_mc_assoc_experiment.yaml'
    with multiprocessing.Pool(processes=2) as pool:
        pool.starmap(run_experiment, [(story_file, CONFIG_FILE, False, "exp2_random_mc_assoc") for story_file in stories])

    # # Experiment 3: Fixed MC + Associations
    # print("Running Experiment 3: Fixed MC + Associations")
    # CONFIG_FILE = 'exp_config/fixed_mc_assoc_experiment.yaml'

    # with multiprocessing.Pool(processes=2) as pool:
    #     pool.starmap(run_experiment, [(story_file, CONFIG_FILE, True, "exp3_fixed_mc_assoc") for story_file in stories])
