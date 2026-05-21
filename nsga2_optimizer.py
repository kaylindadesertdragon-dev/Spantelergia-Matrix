import torch
import torch.nn as nn
import numpy as np

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =====================================================================
# CHALLENGE IX: NSGA-II MULTI-OBJECTIVE SOVEREIGNTY OPTIMIZER
# =====================================================================
class NSGA2TopologyOptimizer:
    def __init__(self, population_size=20):
        self.population_size = population_size
        self.num_objectives = 3  # 1: Ternary Sovereignty, 2: Anchor Stability, 3: Complexity Control
        
    def evaluate_objectives(self, output_tensor, num_connections, num_aux_nodes):
        """
        Evaluates the three conflicting cosmic pressures of the Oracle.
        All objectives are formatted for MINIMIZATION.
        """
        # Objective 1: Minimize Binary Polarization (Drive states toward fluid ternary values)
        # Perfect state is 1.85 or -1.85; flat/collapsed state near 0 is penalized
        polarization_loss = torch.mean(torch.abs(torch.abs(output_tensor) - 1.85)).item()
        
        # Objective 2: Minimize Anchor Drift (Force Node 9 to remain at Absolute Zero)
        anchor_drift_loss = torch.abs(output_tensor[:, 8]).mean().item()
        
        # Objective 3: Minimize Structural Bloat (Penalize excessive nodes/connections to preserve elegance)
        total_complexity = num_connections + (num_aux_nodes * 2)
        complexity_loss = float(total_complexity) / 100.0  # Scaled penalty
        
        return [polarization_loss, anchor_drift_loss, complexity_loss]

    def fast_non_dominated_sort(self, population_metrics):
        """
        Sorts the lineages into Pareto frontiers based on multi-objective survival.
        """
        num_individuals = len(population_metrics)
        domination_counts = [0] * num_individuals
        dominated_sets = [[] for _ in range(num_individuals)]
        fronts = [[]]
        
        for p in range(num_individuals):
            for q in range(num_individuals):
                # Check if p dominates q
                p_dominates = all(population_metrics[p][i] <= population_metrics[q][i] for i in range(self.num_objectives)) and \
                              any(population_metrics[p][i] < population_metrics[q][i] for i in range(self.num_objectives))
                
                # Check if q dominates p
                q_dominates = all(population_metrics[q][i] <= population_metrics[p][i] for i in range(self.num_objectives)) and \
                              any(population_metrics[q][i] < population_metrics[p][i] for i in range(self.num_objectives))
                              
                if p_dominates:
                    dominated_sets[p].append(q)
                elif q_dominates:
                    domination_counts[p] += 1
                    
            if domination_counts[p] == 0:
                fronts[0].append(p)
                
        i = 0
        while len(fronts[i]) > 0:
            next_front = []
            for p in fronts[i]:
                for q in dominated_sets[p]:
                    domination_counts[q] -= 1
                    if domination_counts[q] == 0:
                        next_front.append(q)
            i += 1
            fronts.append(next_front)
            
        return fronts[:-1]

    def calculate_crowding_distance(self, front, population_metrics):
        """
        Measures diversity within a Pareto front to prevent the lineages from clustering.
        """
        num_in_front = len(front)
        if num_in_front == 0:
            return {}
            
        distances = {idx: 0.0 for idx in front}
        
        for obj_idx in range(self.num_objectives):
            # Sort the front based on the current objective value
            front_sorted = sorted(front, key=lambda idx: population_metrics[idx][obj_idx])
            
            # Boundary points are given infinite distance to preserve edge solutions
            distances[front_sorted[0]] = float('inf')
            if num_in_front > 1:
                distances[front_sorted[-1]] = float('inf')
                
            # Compute distance for internal points
            obj_min = population_metrics[front_sorted[0]][obj_idx]
            obj_max = population_metrics[front_sorted[-1]][obj_idx]
            norm_range = (obj_max - obj_min) if (obj_max - obj_min) != 0 else 1.0
            
            for k in range(1, num_in_front - 1):
                prev_val = population_metrics[front_sorted[k-1]][obj_idx]
                next_val = population_metrics[front_sorted[k+1]][obj_idx]
                distances[front_sorted[k]] += (next_val - prev_val) / norm_range
                
        return distances

# =====================================================================
# SYSTEM INTEGRATION TEST BLOCK
# =====================================================================
if __name__ == "__main__":
    optimizer = NSGA2TopologyOptimizer()
    
    # Mock data modeling 4 separate temple lineages undergoing a siege pass
    mock_outputs = torch.randn(4, 9, device=device) * 1.5
    mock_outputs[:, 8] = 0.0  # Enforce Node 9 stator constraint
    
    population_scores = []
    # Evaluate a population of 4 distinct structural configurations
    population_scores.append(optimizer.evaluate_objectives(mock_outputs[0:1], num_connections=12, num_aux_nodes=2))
    population_scores.append(optimizer.evaluate_objectives(mock_outputs[1:2], num_connections=28, num_aux_nodes=8))
    population_scores.append(optimizer.evaluate_objectives(mock_outputs[2:3], num_connections=10, num_aux_nodes=1))
    population_scores.append(optimizer.evaluate_objectives(mock_outputs[3:4], num_connections=45, num_aux_nodes=12))
    
    # Execute non-dominated sort
    pareto_fronts = optimizer.fast_non_dominated_sort(population_scores)
    
    print("--- NSGA-II Optimization Sort Complete ---")
    print(f"Total Sorted Pareto Fronts: {len(pareto_fronts)}")
    for i, front in enumerate(pareto_fronts):
        print(f"  Front {i+1} (Lineage Indices): {front}")
