# -*- coding: utf-8 -*-

import os
import yaml
import numpy as np
from matplotlib import pyplot as plt
from collections import defaultdict

from optimization.main import main, load_factors


def log_ticks(x):
    x_min = int(np.round(np.min(x)) - 1)
    x_max = int(np.round(np.max(x)) + 1)
    ticks = range(x_min, x_max)
    labels = [r'$10^{%d}$' % i for i in ticks]
    return ticks, labels


def plot_stats(stats):
    if type(stats) is str:
        with open(stats, 'r') as f:
            stats = yaml.safe_load(f)

    ax = plt.axes()
    all_x, all_y = np.array([]), np.array([])
    cmap = plt.get_cmap('gnuplot')
    colors = [cmap(i) for i in np.linspace(0, 1, len(stats))]
    i = 0

    for solver, solver_stats in stats.items():
        x = np.log10(solver_stats['problem_size'])
        y = np.log10(solver_stats['runtime'])
        if x.size == 0 or y.size == 0:
            print('Skipping %s' % solver)
            continue

        m, b = np.polyfit(x, y, 1)  # y = mx + b
        x_fit = x.copy()
        y_fit = m * x_fit + b

        ax.scatter(x, y, color=colors[i], label=solver)
        ax.plot(x_fit, y_fit, color=colors[i])
        i += 1

        all_x = np.hstack((all_x, x))
        all_y = np.hstack((all_y, y))

    ax.set_title('problem size vs. solve time')
    x_ticks, x_labels = log_ticks(all_x)
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels)
    y_ticks, y_labels = log_ticks(all_y)
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel('problem size')
    ax.set_ylabel('solve time [s]')
    ax.legend()

    filename = 'images/solve_times.pdf'
    plt.savefig(filename)
    print('Saved figure to: %s' % filename)
    plt.show()


def plot_factors_vs_difficulty(datasets, difficulties, save_to=None):
    num_prior, num_and, num_inv, num_same = [], [], [], []

    for i, dataset in enumerate(datasets):
        factor_file = os.path.join(dataset, 'factors.txt')
        factors = load_factors(factor_file)
        factor_counts = defaultdict(lambda: 0)
        for f in factors.values():
            factor_counts[f.factor_type] += 1
        num_prior.append(factor_counts['PRIOR'])
        num_same.append(factor_counts['SAME'])
        num_and.append(factor_counts['AND'])
        num_inv.append(factor_counts['INV'])

    ax = plt.axes()
    ax.set_title('SHA-256: # factors vs. # rounds')
    ax.set_xlabel('# rounds')
    ax.set_ylabel('# factors')
    ax.plot(difficulties, num_prior, label='PRIOR')
    ax.plot(difficulties, num_same, label='SAME')
    ax.plot(difficulties, num_and, label='AND')
    ax.plot(difficulties, num_inv, label='INV')
    ax.legend()
    ax.set_xticks(np.linspace(1, 64, 8))

    if save_to is not None:
        plt.savefig(save_to)
        print('Saved figure to: %s' % save_to)
    plt.show()


def eval_solver(solver, datasets, difficulties):
    total_stats = {
        'solver': solver,
        'problem_size': [],
        'difficulty': [],
        'runtime': [],
        'success': []
    }

    for i, dataset in enumerate(datasets):
        print('\nTrying difficulty %d...\n' % difficulties[i])
        try:
            stats = main(dataset, solver)
        except:
            break
        total_stats['problem_size'] += stats['problem_size']
        total_stats['difficulty'] += stats['difficulty']
        total_stats['runtime'] += stats['runtime']
        total_stats['success'] += stats['success']

    stats_file = '%s_stats.yaml' % solver
    with open(stats_file, 'w') as f:
        yaml.dump(total_stats, f, default_flow_style=None)
        print('Saved stats to: %s' % stats_file)
    return total_stats


if __name__ == '__main__':
    difficulties = [1, 4, 8, 12, 16] # 17, 18, 19, 20, 21, 22, 23, 24, 32, 64]
    datasets = ['data/sha256_d%d' % d for d in difficulties]
    plot_factors_vs_difficulty(datasets, difficulties,
        save_to='images/sha256_factors.pdf')

    stats = {
        'gurobi_milp': eval_solver('gurobi_milp', datasets, difficulties),
        'cplex_milp': eval_solver('cplex_milp', datasets, difficulties),
        'ortools_cp': eval_solver('ortools_cp', datasets, difficulties),
        'ortools_milp': eval_solver('ortools_milp', datasets, difficulties),
        'minisat': eval_solver('minisat', datasets, difficulties),
        'crypto_minisat': eval_solver('crypto_minisat', datasets, difficulties)
    }
    plot_stats(stats)
