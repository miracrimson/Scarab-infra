import os
import json
import argparse
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as mpatches

matplotlib.rc('font', size=14)

def read_descriptor_from_json(descriptor_filename):
    try:
        with open(descriptor_filename, 'r') as json_file:
            descriptor_data = json.load(json_file)
        return descriptor_data
    except FileNotFoundError:
        print(f"Error: File '{descriptor_filename}' not found.")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file '{descriptor_filename}': {e}")
        return None

def get_dcache_miss_partitioned(descriptor_data, sim_path, output_dir):
    benchmarks_org = descriptor_data["workloads_list"].copy()
    benchmarks = []
    dcache_miss_ratios = {
        'compulsory': {},
        'capacity': {},
        'conflict': {}
    }

    for config_key in descriptor_data["configurations"].keys():
        compulsory_config = []
        capacity_config = []
        conflict_config = []
        avg_compulsory = avg_capacity = avg_conflict = 0.0

        for benchmark in benchmarks_org:
            exp_path = sim_path + '/' + benchmark + '/' + descriptor_data["experiment"] + '/'
            compulsory_miss = capacity_miss = conflict_miss = None
            dcache_hit = None

            try:
                with open(exp_path + config_key + '/memory.stat.0.csv') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('DCACHE_COMPULSORY_MISS_count,'):
                            compulsory_miss = float(line.split(',')[1].strip())
                        elif line.startswith('DCACHE_CAPACITY_MISS_count,'):
                            capacity_miss = float(line.split(',')[1].strip())
                        elif line.startswith('DCACHE_CONFLICT_MISS_count,'):
                            conflict_miss = float(line.split(',')[1].strip())
                        elif line.startswith('DCACHE_HIT_count,'):
                            dcache_hit = float(line.split(',')[1].strip())

            except FileNotFoundError:
                print(f"File not found for {benchmark} in {config_key}, skipping.")
                continue

            total_accesses = compulsory_miss + capacity_miss + conflict_miss + dcache_hit if all(
                v is not None for v in [compulsory_miss, capacity_miss, conflict_miss, dcache_hit]) else 0

            if total_accesses > 0:
                compulsory_ratio = compulsory_miss / total_accesses
                capacity_ratio = capacity_miss / total_accesses
                conflict_ratio = conflict_miss / total_accesses

                avg_compulsory += compulsory_ratio
                avg_capacity += capacity_ratio
                avg_conflict += conflict_ratio

                compulsory_config.append(compulsory_ratio)
                capacity_config.append(capacity_ratio)
                conflict_config.append(conflict_ratio)

            if len(benchmarks_org) > len(benchmarks):
                benchmarks.append(benchmark.split("/"))

        num = len(benchmarks_org)
        if num > 0:
            compulsory_config.append(avg_compulsory / num)  #change to arithmetic mean
            capacity_config.append(avg_capacity / num)
            conflict_config.append(avg_conflict / num)
        else:
            compulsory_config.append(0)
            capacity_config.append(0)
            conflict_config.append(0)

        dcache_miss_ratios['compulsory'][config_key] = compulsory_config
        dcache_miss_ratios['capacity'][config_key] = capacity_config
        dcache_miss_ratios['conflict'][config_key] = conflict_config

    if 'Avg' not in benchmarks:
        benchmarks.append('Avg')

    plot_stacked_bars(benchmarks, dcache_miss_ratios, '3C Misses', output_dir + '/Figure_Dcache_Miss_3C.png')


def plot_stacked_bars(benchmarks, data, ylabel_name, fig_name):
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  
    num_configs = len(next(iter(data['compulsory'].values())))

    partitions = [benchmarks[i:i + 8] for i in range(0, len(benchmarks), 8)] #8 on each plus avg

    for i, part_benchmarks in enumerate(partitions):
        fig, ax = plt.subplots(figsize=(14, 4.4), dpi=80)
        ind = np.arange(len(part_benchmarks)) * 1.8  
        width = 0.2

        for idx, key in enumerate(data['compulsory'].keys()):
            compulsory_vals = data['compulsory'][key][i*8:(i+1)*8]  
            capacity_vals = data['capacity'][key][i*8:(i+1)*8]
            conflict_vals = data['conflict'][key][i*8:(i+1)*8]

            ax.bar(ind + (idx - 1) * width, compulsory_vals, width=width, color=colors[0], edgecolor='black',  #set bottom as existing bars for stacking
                    label=f'{key} - Compulsory')
            ax.bar(ind + (idx - 1) * width, capacity_vals, width=width, color=colors[1], edgecolor='black', 
                     bottom=compulsory_vals, label=f'{key} - Capacity')
            ax.bar(ind + (idx - 1) * width, conflict_vals, width=width, color=colors[2], edgecolor='black', 
                     bottom=np.array(compulsory_vals) + np.array(capacity_vals), 
                   label=f'{key} - Conflict')

        ax.set_xlabel("Benchmarks")
        ax.set_ylabel(ylabel_name)
        ax.set_xticks(ind)
        ax.set_xticklabels(part_benchmarks, rotation=45, ha='right')
        ax.grid('x')

        handles = [
            mpatches.Patch(facecolor=colors[0], edgecolor='black', label='Compulsory Miss'),
            mpatches.Patch(facecolor=colors[1], edgecolor='black', label='Capacity Miss'),
            mpatches.Patch(facecolor=colors[2], edgecolor='black',  label='Conflict Miss')
        ]
        ax.legend(handles=handles, loc="upper left", ncol=2)

        part_fig_name = fig_name.replace(".png", f"_part{i + 1}.png")
        plt.tight_layout()
        plt.savefig(part_fig_name, format="png", bbox_inches="tight")
        plt.show()


# Main function
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Read descriptor file name')
    parser.add_argument('-o', '--output_dir', required=True, help='Output path. Usage: -o /home/$USER/plot')
    parser.add_argument('-d', '--descriptor_name', required=True, help='Experiment descriptor name. Usage: -d /home/$USER/lab1.json')
    parser.add_argument('-s', '--simulation_path', required=True, help='Simulation result path. Usage: -s /home/$USER/exp/simulations')

    args = parser.parse_args()
    descriptor_filename = args.descriptor_name

    descriptor_data = read_descriptor_from_json(descriptor_filename)
    
    get_dcache_miss_partitioned(descriptor_data, args.simulation_path, args.output_dir)

    plt.grid('x')
    plt.tight_layout()
    plt.show()
