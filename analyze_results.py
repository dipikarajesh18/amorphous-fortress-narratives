#!/usr/bin/env python3
"""
Analyze experimental results from amorphous fortress narratives experiments
"""

import json
import os
import re
from collections import defaultdict
import numpy as np
import pandas as pd

def parse_experiment_name(exp_dir):
    """Parse experiment directory name to extract metadata"""
    # Format: exp{X}_{experiment_type}_{game}_{timestamp}_{pop_size}_{generations}
    # or: exp{X}_{experiment_type}_{MC-type}_{game}_{timestamp}_{pop_size}_{generations}
    
    parts = exp_dir.split('_')
    
    exp_num = parts[0]  # exp1, exp2, exp3
    
    if parts[1] == 'pure':
        exp_type = 'pure_random'
        game = parts[3]
        mc_type = None
    elif parts[1] == 'random':
        exp_type = 'random_mc_assoc'
        game = parts[4]
        mc_type = None
    elif parts[1] == 'fixed':
        exp_type = 'fixed_mc_assoc'
        mc_type = parts[3]  # MC-person, MC-explorer, etc.
        game = parts[4]
    
    return {
        'exp_number': exp_num,
        'exp_type': exp_type,
        'mc_type': mc_type,
        'game': game,
        'full_name': exp_dir
    }

def load_experiment_data(base_path, algorithm):
    """Load all experiment data for a given algorithm"""
    results = []
    
    exp_path = os.path.join(base_path, algorithm)
    if not os.path.exists(exp_path):
        return results
    
    for exp_dir in os.listdir(exp_path):
        if exp_dir.startswith('.'):
            continue
            
        exp_info = parse_experiment_name(exp_dir)
        exp_full_path = os.path.join(exp_path, exp_dir)
        
        # Load best genome data
        best_genome_path = os.path.join(exp_full_path, 'best_genome.json')
        archive_path = os.path.join(exp_full_path, 'archive.json')
        
        if not os.path.exists(best_genome_path):
            continue
            
        try:
            with open(best_genome_path, 'r') as f:
                best_genome = json.load(f)
            
            # Load archive data
            archive_data = []
            if os.path.exists(archive_path):
                with open(archive_path, 'r') as f:
                    archive_data = json.load(f)
            
            # Calculate metrics
            best_fitness = best_genome.get('fitness', 0)
            archive_size = len(archive_data) if isinstance(archive_data, list) else len(archive_data)
            
            # Archive diversity metrics
            if isinstance(archive_data, list) and len(archive_data) > 0:
                fitnesses = [item.get('fitness', 0) for item in archive_data if 'fitness' in item]
                if fitnesses:
                    avg_fitness = np.mean(fitnesses)
                    std_fitness = np.std(fitnesses)
                    max_fitness = np.max(fitnesses)
                else:
                    avg_fitness = std_fitness = max_fitness = 0
            elif isinstance(archive_data, dict):
                # MAP-Elites format
                all_fitnesses = []
                for cell_data in archive_data.values():
                    if isinstance(cell_data, list):
                        for item in cell_data:
                            if 'fitness' in item:
                                all_fitnesses.append(item['fitness'])
                
                if all_fitnesses:
                    avg_fitness = np.mean(all_fitnesses)
                    std_fitness = np.std(all_fitnesses)
                    max_fitness = np.max(all_fitnesses)
                else:
                    avg_fitness = std_fitness = max_fitness = 0
            else:
                avg_fitness = std_fitness = max_fitness = 0
            
            results.append({
                'algorithm': algorithm,
                'exp_number': exp_info['exp_number'],
                'exp_type': exp_info['exp_type'],
                'mc_type': exp_info['mc_type'],
                'game': exp_info['game'],
                'full_name': exp_info['full_name'],
                'best_fitness': best_fitness,
                'archive_size': archive_size,
                'avg_fitness': avg_fitness,
                'std_fitness': std_fitness,
                'max_fitness': max_fitness,
                'best_mc': best_genome.get('mc', 'unknown')
            })
            
        except Exception as e:
            print(f"Error processing {exp_full_path}: {e}")
            continue
    
    return results

def analyze_results():
    """Main analysis function"""
    base_path = '/Users/dipikarajesh/Desktop/research/nyu/amorphous-fortress-narratives/experiments'
    
    # Load data for both algorithms
    novelty_results = load_experiment_data(base_path, 'novelty_search')
    mapelites_results = load_experiment_data(base_path, 'map_elites')
    
    all_results = novelty_results + mapelites_results
    
    if not all_results:
        print("No results found!")
        return
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(all_results)
    
    print("=== EXPERIMENTAL RESULTS ANALYSIS ===")
    print(f"Total experiments: {len(df)}")
    print(f"Algorithms: {df['algorithm'].unique()}")
    print(f"Experiment types: {df['exp_type'].unique()}")
    print(f"Games: {df['game'].unique()}")
    print()
    
    # Summary by experiment type
    print("=== RESULTS BY EXPERIMENT TYPE ===")
    exp_summary = df.groupby(['exp_type', 'algorithm']).agg({
        'best_fitness': ['mean', 'std', 'max'],
        'archive_size': ['mean', 'std', 'max'],
        'avg_fitness': 'mean'
    }).round(4)
    print(exp_summary)
    print()
    
    # Summary by game
    print("=== RESULTS BY GAME ===")
    game_summary = df.groupby(['game', 'algorithm']).agg({
        'best_fitness': ['mean', 'std', 'max'],
        'archive_size': ['mean', 'std', 'max']
    }).round(4)
    print(game_summary)
    print()
    
    # Algorithm comparison
    print("=== ALGORITHM COMPARISON ===")
    algo_summary = df.groupby('algorithm').agg({
        'best_fitness': ['mean', 'std', 'max'],
        'archive_size': ['mean', 'std', 'max'],
        'avg_fitness': 'mean'
    }).round(4)
    print(algo_summary)
    print()
    
    # Best performing experiments
    print("=== TOP 10 BEST FITNESS RESULTS ===")
    top_results = df.nlargest(10, 'best_fitness')[['algorithm', 'exp_type', 'game', 'mc_type', 'best_fitness', 'archive_size', 'best_mc']]
    print(top_results.to_string(index=False))
    print()
    
    # Main character analysis for fixed MC experiments
    if df['mc_type'].notna().any():
        print("=== MAIN CHARACTER TYPE ANALYSIS (exp3) ===")
        mc_results = df[df['mc_type'].notna()]
        mc_summary = mc_results.groupby(['mc_type', 'algorithm']).agg({
            'best_fitness': ['mean', 'std', 'max'],
            'archive_size': ['mean', 'std', 'max']
        }).round(4)
        print(mc_summary)
        print()
    
    # Statistical significance tests could be added here
    
    return df

if __name__ == "__main__":
    df = analyze_results()
