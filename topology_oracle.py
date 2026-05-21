import torch
import torch.nn as nn
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle
from math import pi
from IPython.display import HTML

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# =====================================================================
# CHALLENGE VIII: GENOME AND TOPOLOGY NEUROEVOLUTION ENGINE
# =====================================================================
class ConnectionGene:
    def __init__(self, in_node, out_node, weight, enabled=True, innovation_num=0):
        self.in_node = in_node
        self.out_node = out_node
        self.weight = weight
        self.enabled = enabled
        self.innovation_num = innovation_num

class OracleTopologyGenome:
    def __init__(self, stack_id=0):
        self.stack_id = stack_id
        self.num_core_nodes = 9  # Sacred 3-6-9 Core Geometry
        self.next_node_id = 9
        self.connections = []
        self.aux_nodes = []     # Sprouted auxiliary modulator nodes
        self.innovation_counter = 0
        
        # Enforce baseline core connections
        self._initialize_sacred_topology()

    def _initialize_sacred_topology(self):
        # Establish mandatory 3-6-9 kinetic framework loops
        idx3, idx6, idx9 = 2, 5, 8
        # Strong 3-6 coupling lock
        self.add_connection_gene(idx3, idx6, 1.25)
        self.add_connection_gene(idx6, idx3, -1.25)
        
        # Outer protective perimeter loops (1-8 to each other)
        for i in range(8):
            next_node = (i + 1) % 8
            self.add_connection_gene(i, next_node, 0.45)
            
        # Node 9 (Silent God) is absolute stator - zero input lines allowed to deform it
        for i in range(8):
            self.add_connection_gene(i, idx9, 0.0)

    def add_connection_gene(self, in_n, out_n, weight):
        self.innovation_counter += 1
        gene = ConnectionGene(in_n, out_n, weight, enabled=True, innovation_num=self.innovation_counter)
        self.connections.append(gene)

    def mutate_topology(self):
        # rtNEAT mutation restricted by structural constraints
        r = np.random.rand()
        if r < 0.40:  # Add auxiliary connection bridge
            # Choose any two existing nodes
            total_nodes = self.num_core_nodes + len(self.aux_nodes)
            in_n = np.random.randint(0, total_nodes)
            out_n = np.random.randint(0, total_nodes)
            if out_n != 8:  # Node 9 stator protection
                self.add_connection_gene(in_n, out_n, float(np.random.randn() * 0.35))
                
        elif r < 0.65 and len(self.connections) > 0:  # Sprout a new auxiliary resonance node
            # Split an existing connection
            valid_genes = [g for g in self.connections if g.enabled and g.out_node != 8]
            if valid_genes:
                target_gene = np.random.choice(valid_genes)
                target_gene.enabled = False
                
                new_node_id = self.num_core_nodes + len(self.aux_nodes)
                self.aux_nodes.append(new_node_id)
                
                # Insert auxiliary node into the connection path split
                self.add_connection_gene(target_gene.in_node, new_node_id, 1.0)
                self.add_connection_gene(new_node_id, target_gene.out_node, target_gene.weight)

# =====================================================================
# REAL-TIME TOPOLOGY EVOLVING MULTISTACK ORACLE
# =====================================================================
class TopologyEvolvingOracle(nn.Module):
    def __init__(self, num_stacks=4):
        super().__init__()
        self.num_stacks = num_stacks
        self.genomes = [OracleTopologyGenome(stack_id=i) for i in range(num_stacks)]
        self.register_buffer("stack_fitness", torch.zeros(num_stacks, device=device))
        self.global_coherence = 1.0
        self.time_step = 0

    def forward(self, x, binary_siege=False, adv_freq=9.0):
        self.time_step += 1
        batch_size = x.shape[0]
        outputs = []
        
        for i, genome in enumerate(self.genomes):
            total_nodes = genome.num_core_nodes + len(genome.aux_nodes)
            h = torch.zeros(batch_size, total_nodes, device=device)
            # Project inputs into baseline core nodes
            h[:, :8] = x[:, :8]
            
            # Execute topological signal pass derived from active connections
            for gene in genome.connections:
                if gene.enabled and gene.in_node < total_nodes and gene.out_node < total_nodes:
                    h[:, gene.out_node] += h[:, gene.in_node] * gene.weight
            
            # Re-apply invariant 3-6 kinetic coupling geometry anchors
            diff = h[:, 2] - h[:, 5]
            h[:, 2] += 1.12 * torch.sin(diff)
            h[:, 5] += 1.12 * torch.sin(-diff)
            
            # Enforce Absolute Stator Anchorage on Node 9
            h[:, 8] = 0.0
            
            # Apply grounding activation constraints
            out = torch.tanh(h[:, :9] * 0.75) * 1.85
            outputs.append(out)
            
            # Real-time fitness calculation
            pol = torch.mean((torch.abs(torch.abs(out) - 1.8) < 0.4).float()).item()
            anchor_drift = torch.abs(out[:, 8]).mean().item()
            self.stack_fitness[i] = 0.7 * (1.0 - pol) + 0.3 * (1.0 - anchor_drift)

        # Real-Time NEAT Topological Mutation Phase
        if binary_siege and self.time_step % 15 == 0:
            # Weaker lineages mutate structure immediately to escape polarization
            worst_idx = self.stack_fitness.argmin().item()
            if self.stack_fitness[worst_idx] < 0.75:
                self.genomes[worst_idx].mutate_topology()
                
            # Knowledge crossover: weak lineages absorb connection architectures from dominant master lineage
            best_idx = self.stack_fitness.argmax().item()
            if torch.rand(1).item() < 0.12 and best_idx != worst_idx:
                self.genomes[worst_idx].connections = list(self.genomes[best_idx].connections)
                self.genomes[worst_idx].aux_nodes = list(self.genomes[best_idx].aux_nodes)

        self.global_coherence = self.stack_fitness.mean().item()
        return outputs

# =====================================================================
# ADVANCED METAPLASTIC TOPOLOGY DASHBOARD
# =====================================================================
class TopologyDashboard:
    def __init__(self, num_stacks=4):
        self.oracle = TopologyEvolvingOracle(num_stacks=num_stacks).to(device)
        self.num_stacks = num_stacks
        self.siege_start = 80
        
        self.fig = plt.figure(figsize=(19, 11), facecolor='#020204')
        gs = gridspec.GridSpec(3, 2, width_ratios=[1.1, 0.9], height_ratios=[1, 1, 1])
        
        self.ax_left = self.fig.add_subplot(gs[:, 0])
        self.ax_left.set_facecolor('#020204')
        
        self.ax_fitness = self.fig.add_subplot(gs[0, 1])
        self.ax_complexity = self.fig.add_subplot(gs[1, 1])
        self.ax_resonance = self.fig.add_subplot(gs[2, 1])
        
        for ax in [self.ax_fitness, self.ax_complexity, self.ax_resonance]:
            ax.set_facecolor('#06080c')
            ax.tick_params(colors='#c9d1d9')
            ax.grid(True, color='#121822', linestyle=':')
            
        self.angles = np.array([i * (2 * pi / 8) + (pi / 2) for i in range(8)])
        self.base_x = np.append(np.cos(self.angles), 0.0)
        self.base_y = np.append(np.sin(self.angles), 0.0)
        
        self.scatter_core = self.ax_left.scatter(self.base_x, self.base_y, c='#1f6feb', s=550, edgecolors='#ffffff', zorder=5, label='Sacred Core (1-9)')
        self.scatter_aux = self.ax_left.scatter([], [], c='#00ffcc', s=350, edgecolors='#ffffff', marker='^', zorder=6, label='Sprouted Resonators')
        
        self.boundary_circle = Circle((0, 0), 1.5, fill=False, linestyle='--', color='#1c2331', linewidth=1.5)
        self.ax_left.add_artist(self.boundary_circle)
        
        self.connection_lines = []
        self.ax_left.set_xlim(-2.2, 2.2)
        self.ax_left.set_ylim(-2.2, 2.2)
        self.ax_left.axis('off')
        
        self.title = self.ax_left.text(0, 2.0, "", ha='center', va='center', color='#c9d1d9', fontsize=12, fontweight='bold')
        self.ax_left.legend(loc="lower left", facecolor='#020204', edgecolor='none', labelcolor='#c9d1d9', fontsize=9)
        
        self.time_steps, self.global_coherence_history = [], []
        self.complexity_histories = [[] for _ in range(num_stacks)]
        self.stack_histories = [[] for _ in range(num_stacks)]
        self.resonance_history = []
        
        self.stack_lines = [self.ax_fitness.plot([], [], linewidth=1.8, label=f"Lineage {i}")[0] for i in range(num_stacks)]
        self.line_global, = self.ax_fitness.plot([], [], color='#ffffff', linestyle='--', linewidth=2.0, label="Global Sovereignty")
        self.complexity_lines = [self.ax_complexity.plot([], [], linewidth=1.8, label=f"Lineage {i} Complexity")[0] for i in range(num_stacks)]
        self.line_res, = self.ax_resonance.plot([], [], color='#7ee787', linewidth=2.0)
        
        self.ax_fitness.set_title("Evolving Lineage Sovereignty Profiles", color='#c9d1d9', fontsize=10)
        self.ax_fitness.legend(loc="lower left", facecolor='#06080c', edgecolor='none', fontsize=8, labelcolor='#c9d1d9')
        self.ax_complexity.set_title("Topological Complexity (Evolved Connections & Auxiliary Nodes Count)", color='#c9d1d9', fontsize=10)
        self.ax_resonance.set_title("Ecosystem Cross-Layer Resonance Profile", color='#c9d1d9', fontsize=10)

    def update(self, frame):
        is_siege = (frame >= self.siege_start)
        adv_freq = 9.0 + 3.0 * np.sin(frame * 0.08) if is_siege else 9.0
        
        if is_siege:
            sq = 1.85 * np.sign(np.sin((frame * 0.05) * adv_freq))
            x_raw = np.full(8, sq) + np.random.randn(8) * 0.12
        else:
            x_raw = np.full(8, np.sin(frame * 0.06)) + np.random.randn(8) * 0.03
            
        x_in = torch.tensor(x_raw, dtype=torch.float32, device=device).unsqueeze(0)
        outputs = self.oracle(x_in, binary_siege=is_siege, adv_freq=adv_freq)
        
        # Pull layout geometries from the reigning champion stack
        best_stack_idx = self.oracle.stack_fitness.argmax().item()
        champion_genome = self.oracle.genomes[best_stack_idx]
        
        # Calculate dynamic physical coordinates for sprouted auxiliary nodes
        num_aux = len(champion_genome.aux_nodes)
        if num_aux > 0:
            aux_angles = np.linspace(0, 2 * pi, num_aux, endpoint=False) + (frame * 0.02)
            aux_x = np.cos(aux_angles) * 1.6
            aux_y = np.sin(aux_angles) * 1.6
            self.scatter_aux.set_offsets(np.stack((aux_x, aux_y), axis=1))
            all_x = np.concatenate((self.base_x, aux_x))
            all_y = np.concatenate((self.base_y, aux_y))
        else:
            self.scatter_aux.set_offsets(np.empty((0, 2)))
            all_x, all_y = self.base_x, self.base_y
            
        # Clear legacy structural line drawings
        for line in self.connection_lines:
            line.remove()
        self.connection_lines.clear()
        
        # Draw active topology pathways inside the champion lineage
        for gene in champion_genome.connections:
            if gene.enabled and gene.in_node < len(all_x) and gene.out_node < len(all_y):
                lw = 3.5 if gene.weight == 1.0 else max(0.5, min(3.0, abs(gene.weight) * 2.0))
                color = '#ffaa00' if gene.in_node in [2,5] or gene.out_node in [2,5] else '#1f6feb'
                if gene.weight == 0.0: color = '#238636' # Silent God anchor channel lines
                
                l, = self.ax_left.plot([all_x[gene.in_node], all_x[gene.out_node]], 
                                       [all_y[gene.in_node], all_y[gene.out_node]], 
                                       color=color, alpha=0.35, linewidth=lw, zorder=1)
                self.connection_lines.append(l)
                
        # Manage diagnostic telemetry histories
        self.time_steps.append(frame)
        self.global_coherence_history.append(self.oracle.global_coherence)
        
        stacked_outputs = torch.stack(outputs)
        cross_resonance = 1.0 - torch.var(stacked_outputs, dim=0).mean().item()
        self.resonance_history.append(cross_resonance)
        
        for i in range(self.num_stacks):
            self.stack_histories[i].append(self.oracle.stack_fitness[i].item())
            self.complexity_histories[i].append(len(self.oracle.genomes[i].connections) + len(self.oracle.genomes[i].aux_nodes))
            
        if len(self.time_steps) > 150:
            self.time_steps.pop(0)
            self.global_coherence_history.pop(0)
            self.resonance_history.pop(0)
            for i in range(self.num_stacks):
                self.stack_histories[i].pop(0)
                self.complexity_histories[i].pop(0)
                
        # Redraw data vectors on subplots
        self.line_global.set_data(self.time_steps, self.global_coherence_history)
        self.ax_fitness.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        self.ax_fitness.set_ylim(-0.05, 1.05)
        
        for i, line in enumerate(self.stack_lines):
            line.set_data(self.time_steps, self.stack_histories[i])
            
        for i, line in enumerate(self.complexity_lines):
            line.set_data(self.time_steps, self.complexity_histories[i])
        self.ax_complexity.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        self.ax_complexity.set_ylim(0, max([max(h) for h in self.complexity_histories]) + 5)
        
        self.line_res.set_data(self.time_steps, self.resonance_history)
        self.ax_resonance.set_xlim(min(self.time_steps), max(self.time_steps) + 5)
        self.ax_resonance.set_ylim(-0.05, 1.05)
        
        status = f"SIEGE ACTIVE — SWEATING FREQ PROFILE ({adv_freq:.2f}Hz)" if is_siege else "STABLE GEOMETRIC RECONSTRUCT ACTIVE"
        self.title.set_text(f"Spantelergia Oracle Cluster • Challenge VIII Topology Architecture • Step {frame}\n{status}\n[Dominant Lineage {best_stack_idx} | Sprouted Resonators: {num_aux}]")
        
        return [self.scatter_core, self.scatter_aux, self.title, self.line_global, self.line_res] + self.stack_lines + self.complexity_lines + self.connection_lines

# =====================================================================
# DEPLOYMENT
# =====================================================================
if __name__ == "__main__":
    dashboard = TopologyDashboard(num_stacks=4)
    ani = animation.FuncAnimation(dashboard.fig, dashboard.update, frames=200,
                                  interval=50, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.close()
    display(HTML(ani.to_html5_video()))
      
