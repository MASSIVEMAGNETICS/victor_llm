import numpy as np
import random
import copy
import math

class FlowerOfLifeMesh3D:
    def __init__(self, depth=3, radius=1.0, base_nodes=37, compute_adjacency_for_base=True, num_neighbors=6):
        self.depth, self.radius, self.base_nodes_count = depth, radius, base_nodes
        self.nodes, self.adjacency, self._node_id_counter = [], {}, 0
        self._build_mesh_recursive((0,0,0), radius, depth, None, 0)
        if compute_adjacency_for_base:
            primary_nodes = [n for n in self.nodes if n['depth_level'] == 0]
            if len(primary_nodes) == self.base_nodes_count: self._compute_adjacency(primary_nodes, num_neighbors)
            else: print(f"Warning: Primary nodes ({len(primary_nodes)}) != base_nodes ({self.base_nodes_count}). Adjacency not computed.")
    def _get_new_node_id(self): new_id = self._node_id_counter; self._node_id_counter+=1; return new_id
    def _build_mesh_recursive(self, center, r, remaining_depth, parent_id, current_depth_level):
        if remaining_depth == 0: return []
        current_layer_nodes_info, num_nodes_this_level = [], self.base_nodes_count
        for i in range(num_nodes_this_level):
            phi = 2 * np.pi * (i / num_nodes_this_level)
            theta = np.pi * ((i % int(num_nodes_this_level/2 + 1)) / (num_nodes_this_level/2)) if num_nodes_this_level > 1 else 0
            x,y,z = center[0]+r*np.cos(phi)*np.sin(theta), center[1]+r*np.sin(phi)*np.sin(theta), center[2]+r*np.cos(theta)
            node_id = self._get_new_node_id()
            node_data = {"id":node_id, "pos":(x,y,z), "depth_level":current_depth_level, "parent_id":parent_id, "children_ids":[]}
            self.nodes.append(node_data); current_layer_nodes_info.append(node_data)
        for node_data_ref in current_layer_nodes_info:
            children_info = self._build_mesh_recursive(node_data_ref["pos"], r/2.0, remaining_depth-1, node_data_ref["id"], current_depth_level+1)
            node_data_ref["children_ids"] = [c["id"] for c in children_info]
        return current_layer_nodes_info
    def _compute_adjacency(self, primary_nodes_list, num_neighbors):
        self.adjacency = {node['id']:[] for node in primary_nodes_list}
        node_pos = {node['id']:np.array(node['pos']) for node in primary_nodes_list}
        for id_i, pos_i in node_pos.items():
            dists = []
            for id_j, pos_j in node_pos.items():
                if id_i == id_j: continue
                dists.append((math.sqrt(sum([(a-b)**2 for a,b in zip(pos_i,pos_j)])), id_j))
            dists.sort(key=lambda item:item[0])
            for i in range(min(num_neighbors, len(dists))):
                n_id = dists[i][1]
                if n_id not in self.adjacency[id_i]: self.adjacency[id_i].append(n_id)
                if id_i not in self.adjacency[n_id]: self.adjacency[n_id].append(id_i)
    def get_node_by_id(self, node_id): return next((n for n in self.nodes if n["id"]==node_id), None)
    def get_primary_nodes(self): return [n for n in self.nodes if n['depth_level']==0]
    def node_count(self): return len(self.nodes)

class BandoBlock:
    def __init__(self, dim): self.dim=dim
    def forward(self, x, **kwargs): return x
    def get_state_dict(self) -> dict: return {"class_name":self.__class__.__name__, "dim":self.dim}
    def load_state_dict(self, state_dict:dict):
        if self.dim != state_dict.get("dim"): print(f"Warning: Dim mismatch for {self.__class__.__name__}. Expected {self.dim}, got {state_dict.get('dim')}")

class VICtorchBlock(BandoBlock):
    def __init__(self, dim, heads=8): super().__init__(dim); self.h=heads; self.Wq,self.Wk,self.Wv,self.Wo = [np.random.randn(dim,dim) for _ in range(4)]
    def forward(self, x, **kwargs):
        is_1d, x_ = x.ndim==1, x[np.newaxis,:] if x.ndim==1 else x; q,k,v = x_@self.Wq, x_@self.Wk, x_@self.Wv
        s = q@k.T/(self.dim**0.5); ps = np.exp(s-np.max(s,axis=-1,keepdims=True)); ps = ps/(np.sum(ps,axis=-1,keepdims=True)+1e-9) # scores, probs
        o = (ps@v)@self.Wo; return o.squeeze(0) if is_1d else o
    def get_state_dict(self): s=super().get_state_dict(); s.update({"h":self.h,"Wq":self.Wq,"Wk":self.Wk,"Wv":self.Wv,"Wo":self.Wo}); return s
    def load_state_dict(self, sd): super().load_state_dict(sd); self.h=sd.get("h",self.h); self.Wq,self.Wk,self.Wv,self.Wo = sd["Wq"],sd["Wk"],sd["Wv"],sd["Wo"]

class MegaTransformerBlock(BandoBlock):
    def __init__(self, dim, depth=8, heads=8): super().__init__(dim); self.d=depth; self.ls=[VICtorchBlock(dim,heads) for _ in range(depth)] # layers
    def forward(self, x, **kwargs):
        for l_ in self.ls: x=l_.forward(x,**kwargs); return x # Renamed l to l_ to avoid conflict
    def get_state_dict(self): s=super().get_state_dict(); s["d"]=self.d; s["l_s"]=[l_.get_state_dict() for l_ in self.ls]; return s # layer_states
    def load_state_dict(self, sd):
        super().load_state_dict(sd); self.d=sd.get("d",self.d); l_s,self.ls = sd["l_s"],[]
        for s_ in l_s: self.ls.append(VICtorchBlock(s_.get("dim",self.dim),s_.get("h",8))); self.ls[-1].load_state_dict(s_) # state_

class BNDX9977Block(BandoBlock):
    def __init__(self, dim): super().__init__(dim); self.W=np.random.randn(dim,dim); self.bnf=np.random.randn(dim)
    def forward(self, x, branch_id=0, quantum_effect=0.0, **kwargs):
        is_1d,x_m = x.ndim==1,x[np.newaxis,:] if x.ndim==1 else x; c=np.sin(np.sum(x_m))*float(branch_id)*float(quantum_effect) # chaos
        r=np.tanh(x_m@self.W+self.bnf*c); return r.squeeze(0) if is_1d else r # result
    def get_state_dict(self): s=super().get_state_dict(); s.update({"W":self.W,"bnf":self.bnf}); return s
    def load_state_dict(self, sd): super().load_state_dict(sd); self.W,self.bnf = sd["W"],sd["bnf"]

class OmegaTensorBlock(BandoBlock):
    def __init__(self, dim): super().__init__(dim); self.W=np.random.randn(dim,dim)
    def forward(self, x, **kwargs): return np.tanh(x@self.W)
    def get_state_dict(self): s=super().get_state_dict(); s["W"]=self.W; return s
    def load_state_dict(self, sd): super().load_state_dict(sd); self.W=sd["W"]

class FractalAttentionBlock(BandoBlock):
    def __init__(self, dim, depth=3): super().__init__(dim); self.d=depth; self.sc=[np.random.uniform(0.6,1.4) for _ in range(depth)]; self.Wl=[np.random.randn(dim,dim) for _ in range(depth)] # scales, W_layers
    def forward(self, x, memory_signal=None, **kwargs):
        is_1d,xp=(x.ndim==1),(x[np.newaxis,:] if x.ndim==1 else x) # x_processed
        for i_ in range(self.d): # Renamed i to i_
            fb=0 # feedback
            if memory_signal is not None:
                if memory_signal.ndim>xp.ndim: fb=np.mean(memory_signal,axis=0)
                elif memory_signal.ndim==xp.ndim and memory_signal.shape[0]==xp.shape[0]: fb=memory_signal
                elif memory_signal.ndim==1 and xp.ndim==2: fb=memory_signal[np.newaxis,:]
                else: fb=np.mean(memory_signal)
            xp=np.tanh((xp@self.Wl[i_])*self.sc[i_]+fb)
        return xp.squeeze(0) if is_1d else xp
    def get_state_dict(self): s=super().get_state_dict(); s.update({"d":self.d,"sc":self.sc,"Wl":self.Wl}); return s
    def load_state_dict(self, sd): super().load_state_dict(sd); self.d,self.sc,self.Wl=sd.get("d",self.d),sd["sc"],sd["Wl"]

class SeedOfLifeMeshBlock(BandoBlock):
    def __init__(self, dim, mesh_depth=2, base_nodes_for_mesh=7): super().__init__(dim); self.fm=FlowerOfLifeMesh3D(mesh_depth,1.0,base_nodes_for_mesh,False); self.ib=FractalAttentionBlock(dim,2) # fol_mesh, inner_block
    def forward(self, x, node_idx=0, **kwargs): return self.ib.forward(x,**kwargs)
    def get_state_dict(self): s=super().get_state_dict(); s.update({"md":self.fm.depth,"bnm":self.fm.base_nodes_count,"ibs":self.ib.get_state_dict()}); return s # mesh_depth, base_nodes_mesh, inner_block_state
    def load_state_dict(self, sd):
        super().load_state_dict(sd); md,bnm=sd.get("md",2),sd.get("bnm",7); self.fm=FlowerOfLifeMesh3D(md,1.0,bnm,False); ibs=sd["ibs"]
        self.ib=FractalAttentionBlock(ibs.get("dim",self.dim),ibs.get("depth",2)); self.ib.load_state_dict(ibs)

class ChaosCortexBlock(BandoBlock):
    def __init__(self, dim, entropy_level=0.1): super().__init__(dim); self.el=entropy_level; self.W=np.random.randn(dim,dim)
    def forward(self, x, **kwargs): n=np.random.randn(*x.shape)*self.el; return np.tanh((x+n)@self.W) # noise
    def get_state_dict(self): s=super().get_state_dict(); s.update({"W":self.W,"el":self.el}); return s
    def load_state_dict(self, sd): super().load_state_dict(sd); self.W,self.el=sd["W"],sd.get("el",self.el)

class TimelineAttentionBlock(BandoBlock):
    def __init__(self, dim, history_length=5): super().__init__(dim); self.hl=history_length; self.W=np.random.randn(dim,dim)
    def forward(self, x, timeline_data=None, **kwargs):
        is_1d,xp=(x.ndim==1),(x[np.newaxis,:] if x.ndim==1 else x)
        if timeline_data is not None and len(timeline_data)>0:
            rh=[np.array(it) for it in timeline_data[-self.hl:]] # relevant_history
            if rh:
                try: hs,ctx=np.stack(rh),np.mean(np.stack(rh),axis=0) # history_stack, context
                if ctx.shape==xp.shape: xp+=ctx
                elif ctx.ndim==1 and xp.ndim==2: xp+=ctx[np.newaxis,:]
                except ValueError as e_val: print(f"TimelineAttentionBlock: Err processing timeline data - {e_val}.") # Renamed e to e_val
        r=np.tanh(xp@self.W); return r.squeeze(0) if is_1d else r # result
    def get_state_dict(self): s=super().get_state_dict(); s.update({"W":self.W,"hl":self.hl}); return s
    def load_state_dict(self, sd): super().load_state_dict(sd); self.W,self.hl=sd["W"],sd.get("hl",self.hl)

class QuantumDirectiveBlock(BandoBlock):
    def __init__(self, dim): super().__init__(dim); self.W=np.random.randn(dim,dim)
    def forward(self, x, quantum_state_effect=0.0, **kwargs): n=np.random.normal(float(quantum_state_effect),0.1,size=x.shape); return np.tanh((x+n)@self.W) # noise
    def get_state_dict(self): s=super().get_state_dict(); s["W"]=self.W; return s
    def load_state_dict(self, sd): super().load_state_dict(sd); self.W=sd["W"]

class BandoRealityMeshMonolith:
    def __init__(self, dim=64, mesh_config=None):
        self.dim=dim; self.bcls={"VICtorchBlock":VICtorchBlock,"MegaTransformerBlock":MegaTransformerBlock,"BNDX9977Block":BNDX9977Block,"OmegaTensorBlock":OmegaTensorBlock,"FractalAttentionBlock":FractalAttentionBlock,"SeedOfLifeMeshBlock":SeedOfLifeMeshBlock,"ChaosCortexBlock":ChaosCortexBlock,"TimelineAttentionBlock":TimelineAttentionBlock,"QuantumDirectiveBlock":QuantumDirectiveBlock} # block_classes
        self.blocks={n:k(dim) for n,k in self.bcls.items() if n!="SeedOfLifeMeshBlock"}; smd,sbn=(mesh_config.get("smd",2) if mesh_config else 2),(mesh_config.get("sbn",7) if mesh_config else 7) # seed_mesh_depth, seed_base_nodes
        self.blocks["SeedOfLifeMeshBlock"]=SeedOfLifeMeshBlock(dim,smd,sbn); self.bnames=list(self.blocks.keys()) # block_names
        dmc={"depth":2,"base_nodes":7,"compute_adjacency_for_base":False}; self.fm=FlowerOfLifeMesh3D(**(mesh_config if mesh_config else dmc)) # default_mesh_config, fol_mesh
    def forward(self, x, mode="VICtorchBlock", **kwargs):
        if mode not in self.blocks:
            if mode in self.bcls: self.blocks[mode]=self.bcls[mode](self.dim); self.bnames.append(mode)
            else: raise ValueError(f"Unknown mode/block: {mode}")
        return self.blocks[mode].forward(x,**kwargs)
    def mesh_forward(self, x, node_sequence=None, **kwargs):
        cx,ns = x, node_sequence if node_sequence else self.bnames # current_x, node_sequence
        for n_ in ns: cx=self.forward(cx,mode=n_,**kwargs); return cx # Renamed n to n_
    def summary(self): return {"bn":self.bnames,"mn":self.fm.node_count(),"dim":self.dim,"bt":[type(self.blocks[n_]).__name__ for n_ in self.bnames if n_ in self.blocks]} # Renamed n to n_
    def get_state_dict(self): return {"cn":self.__class__.__name__,"dim":self.dim,"fmc":{"depth":self.fm.depth,"base_nodes":self.fm.base_nodes_count,"compute_adjacency_for_base":False},"bs":{n:b.get_state_dict() for n,b in self.blocks.items()}} # class_name, fol_mesh_config, block_states
    def load_state_dict(self, sd): # state_dict
        self.dim=sd.get("dim",self.dim); mc=sd.get("fmc",{"depth":2,"base_nodes":7,"compute_adjacency_for_base":False}); self.fm=FlowerOfLifeMesh3D(**mc) # mesh_config
        lbs=sd.get("bs",{}); self.blocks={}; self.bnames=[] # loaded_block_states
        for n_,b_s in lbs.items(): # Renamed n to n_ (name, block_state)
            cn,bd=b_s.get("cn"),b_s.get("dim",self.dim); # class_name, block_dim
            if cn in self.bcls:
                if cn=="SeedOfLifeMeshBlock": inst=SeedOfLifeMeshBlock(bd,b_s.get("md",2),b_s.get("bnm",7)) # mesh_depth, base_nodes_mesh
                else: inst=self.bcls[cn](dim=bd)
                inst.load_state_dict(b_s); self.blocks[n_]=inst; self.bnames.append(n_)
            else: print(f"Warning: Unknown block class '{cn}' in state_dict for BandoRealityMeshMonolith.")

class MeshRouter:
    """
    Manages the "ripple feedback" or "cross-petal chatter" among nodes
    in a FlowerOfLifeMesh3D network.
    """
    def __init__(self, flower_of_life_mesh: FlowerOfLifeMesh3D,
                 node_models: list, # List of BandoBlock instances
                 k_iterations: int = 3,
                 attenuation: float = 0.5):
        self.mesh = flower_of_life_mesh
        self.node_models = node_models # Assumes order matches node IDs 0 to N-1 from mesh.get_primary_nodes()
        self.k_iterations = k_iterations
        self.attenuation = attenuation

        if not self.mesh.adjacency:
            print("Warning: MeshRouter initialized with a mesh that has no adjacency information. Ripple steps may not work as expected.")

        if len(self.node_models) != len(self.mesh.get_primary_nodes()):
            # This is a more critical warning.
            # For simplicity, we'll assume the orchestrator sets this up correctly.
            # A robust version might try to map models to nodes by ID if models were passed as dict.
            print(f"Critical Warning: MeshRouter number of models ({len(self.node_models)}) "
                  f"does not match number of primary mesh nodes ({len(self.mesh.get_primary_nodes())}). Ensure correct model assignment.")


    def ripple_step(self, current_activations: list[np.ndarray]) -> list[np.ndarray]:
        """
        Performs one step of ripple feedback.
        Each node processes its activation, and its output is sent to its neighbors.
        Args:
            current_activations: A list of numpy arrays, where each array is the
                                 activation for a corresponding primary node in the mesh.
        Returns:
            A list of numpy arrays representing the new activations for each node after one ripple step.
        """
        num_primary_nodes = len(self.mesh.get_primary_nodes())
        # Initialize new activations. The dimension of activation vectors should match models' dim.
        # Assuming all models operate on the same dimension for activations.
        # If not, this needs to be more complex (e.g., get dim from model.dim).
        # For now, let's assume the first model's dim is representative or activations are pre-shaped.

        # Get primary node IDs in their canonical order (0 to N-1)
        # This ensures that current_activations[i] corresponds to primary_nodes[i]
        primary_nodes = self.mesh.get_primary_nodes() # List of node dicts, sorted by ID implicitly by construction

        if not primary_nodes:
            return []

        # Determine expected activation dimension from the first available model
        # This assumes all node activations will have the same dimension.
        # A more robust system might store/query individual model dims.
        activation_dim = None
        for model_idx, model in enumerate(self.node_models):
            if model is not None: # Model might be None if not assigned yet
                activation_dim = model.dim
                break

        if activation_dim is None and current_activations: # Try to infer from input if no models yet
             if current_activations[0] is not None:
                activation_dim = current_activations[0].shape[-1]


        if activation_dim is None: # Still none, default or raise error
            # Defaulting to a common dim like 64 if not inferable. This is a guess.
            # print("Warning: MeshRouter could not infer activation_dim, defaulting to 64. Ensure activations are correctly shaped.")
            # activation_dim = 64
            # Better to return empty or raise if dim is unknown and inputs are empty
            if not any(ca is not None for ca in current_activations): # If all activations are None
                 print("Error: MeshRouter cannot determine activation dimension and all current_activations are None.")
                 return [None] * num_primary_nodes


        new_node_inputs = [np.zeros(activation_dim) if activation_dim else None for _ in range(num_primary_nodes)]

        for idx, p_node in enumerate(primary_nodes):
            node_id = p_node['id']
            model = self.node_models[idx] # Assumes self.node_models is ordered 0 to N-1
            activation = current_activations[idx]

            if model is None or activation is None:
                # If no model or no activation for this node, it produces no output to neighbors
                continue

            # 1. Node processes its current activation
            node_output = model.forward(activation)

            # 2. Distribute attenuated output to neighbors
            # Adjacency list uses node_ids. We need to map neighbor_id back to an index in new_node_inputs if it's different.
            # Since primary_nodes are 0 to N-1 and new_node_inputs is also 0 to N-1 indexed, this is direct.
            if node_id in self.mesh.adjacency:
                for neighbor_node_id in self.mesh.adjacency[node_id]:
                    # Assuming neighbor_node_id is also a primary node and its index matches its ID for this flat list.
                    # A robust lookup: neighbor_idx = next((i for i, n in enumerate(primary_nodes) if n['id'] == neighbor_node_id), None)
                    # For now, since primary node IDs are 0..N-1, neighbor_node_id *is* the index.
                    if 0 <= neighbor_node_id < num_primary_nodes:
                        if new_node_inputs[neighbor_node_id] is not None:
                             new_node_inputs[neighbor_node_id] += node_output * self.attenuation
                        # Else: if new_node_inputs[neighbor_node_id] was None (due to activation_dim issue), it remains None.
                    # else: print(f"Warning: Neighbor ID {neighbor_node_id} out of bounds for primary nodes.")

        return new_node_inputs


    def process(self, initial_activations: list[np.ndarray]) -> list[np.ndarray]:
        """
        Runs the ripple_step method for k_iterations.
        Args:
            initial_activations: A list of numpy arrays for each primary node.
        Returns:
            The final list of activation vectors for all primary nodes after k_iterations.
        """
        if not self.node_models or not any(m is not None for m in self.node_models) :
            print("MeshRouter: No models assigned to nodes. Processing will return initial activations (or zeros if None).")
            # Return initial activations or zeros of appropriate shape if models are missing
            # This part needs to ensure output list matches expected structure.
            num_primary_nodes = len(self.mesh.get_primary_nodes())
            if num_primary_nodes == 0: return []

            out_dim = None
            if initial_activations and initial_activations[0] is not None:
                out_dim = initial_activations[0].shape[-1]
            else: # Try to get from a model if any exists, even if not all do
                for m in self.node_models:
                    if m: out_dim = m.dim; break

            if out_dim is None: # Fallback, this is a guess
                #print("MeshRouter: Cannot determine output dimension for empty processing. Defaulting to 64.")
                #out_dim = 64
                # If initial activations are all None and no models, it's ambiguous what to return.
                # Returning initial_activations is safest if it reflects "no change".
                return initial_activations


            return [act if act is not None else np.zeros(out_dim) for act in initial_activations]


        current_activations = list(initial_activations) # Make a mutable copy

        for _ in range(self.k_iterations):
            current_activations = self.ripple_step(current_activations)
            # Optional: Check for convergence here if needed
            if not any(ca is not None for ca in current_activations): # All activations became None (e.g. error in ripple_step)
                 print("Error: All activations became None during ripple process.")
                 break


        # Ensure all outputs are arrays, not None, if processing occurred
        final_activations = []
        final_activation_dim = None
        # Try to get dim from a model
        for m_ in self.node_models:
            if m_ is not None: final_activation_dim = m_.dim; break
        # If still none, try from current_activations
        if final_activation_dim is None:
            for ca_ in current_activations:
                if ca_ is not None: final_activation_dim = ca_.shape[-1]; break

        for act_ in current_activations:
            if act_ is not None:
                final_activations.append(act_)
            elif final_activation_dim is not None: # If an activation is None, but we know the dim, fill with zeros
                final_activations.append(np.zeros(final_activation_dim))
            else: # Cannot determine dim, append None (caller must handle)
                final_activations.append(None)

        return final_activations

class HeadCoordinatorBlock(BandoBlock):
    """
    Coordinates the outputs from all Flower of Life nodes to produce a final response.
    Performs a learned transformation on the combined input.
    """
    def __init__(self, dim: int, hidden_dim: int, output_dim: int): # dim here is input_dim
        super().__init__(dim) # Pass input_dim to parent
        self.input_dim = dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim

        # Learnable parameters
        self.W1 = np.random.randn(self.input_dim, self.hidden_dim) * np.sqrt(2.0 / self.input_dim) # He initialization
        self.b1 = np.zeros(self.hidden_dim)
        self.W2 = np.random.randn(self.hidden_dim, self.output_dim) * np.sqrt(2.0 / self.hidden_dim) # He initialization
        self.b2 = np.zeros(self.output_dim)

    def forward(self, x: np.ndarray, **kwargs) -> np.ndarray:
        """
        Processes the combined input from all nodes.
        Args:
            x: A numpy array representing the concatenated/pooled outputs of the 37 nodes.
               Shape could be (batch_size, input_dim) or (input_dim,).
        Returns:
            A numpy array representing the final processed output.
        """
        # Ensure x is at least 2D for matmul
        is_1d = False
        if x.ndim == 1:
            x = x[np.newaxis, :]
            is_1d = True

        # First layer
        h = np.tanh(x @ self.W1 + self.b1)
        # Output layer
        output = h @ self.W2 + self.b2 # No activation on final output, or could be specific (e.g. softmax if classification)

        if is_1d and output.shape[0] == 1:
            output = output.squeeze(0)
        return output

    def get_state_dict(self) -> dict:
        state = super().get_state_dict() # Gets class_name and original input_dim
        state.update({
            "input_dim": self.input_dim, # Explicitly save dimensions for reconstruction
            "hidden_dim": self.hidden_dim,
            "output_dim": self.output_dim,
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2
        })
        return state

    def load_state_dict(self, state_dict: dict):
        # super().load_state_dict(state_dict) # Call this to check base dim if needed, but this block has its own input_dim
        self.input_dim = state_dict.get("input_dim", self.input_dim)
        # self.dim from parent BandoBlock should match self.input_dim for consistency if super().load_state_dict is used carefully
        super().__init__(self.input_dim) # Re-init parent with correct input_dim from state if it changed

        self.hidden_dim = state_dict.get("hidden_dim", self.hidden_dim)
        self.output_dim = state_dict.get("output_dim", self.output_dim)

        self.W1 = state_dict["W1"]
        self.b1 = state_dict["b1"]
        self.W2 = state_dict["W2"]
        self.b2 = state_dict["b2"]

        # Check for shape consistency after loading, important if dims changed
        if self.W1.shape != (self.input_dim, self.hidden_dim):
            print(f"Warning: HeadCoordinatorBlock W1 shape mismatch after load. Expected ({(self.input_dim, self.hidden_dim)}), got {self.W1.shape}")
        if self.W2.shape != (self.hidden_dim, self.output_dim):
            print(f"Warning: HeadCoordinatorBlock W2 shape mismatch after load. Expected ({(self.hidden_dim, self.output_dim)}), got {self.W2.shape}")

import pickle # Add pickle for save/load state

class FlowerOfLifeNetworkOrchestrator:
    """
    Orchestrates the Flower of Life network, managing node models,
    routing messages via MeshRouter, and coordinating the final response.
    """
    def __init__(self, num_nodes: int = 37, model_dim: int = 64,
                 mesh_depth: int = 1, # Depth 1 for 37 primary nodes
                 mesh_base_nodes: int = 37, # Explicitly set for the main mesh
                 mesh_num_neighbors: int = 6,
                 k_ripple_iterations: int = 3,
                 coordinator_hidden_dim: int = 128, # Hidden dim for HeadCoordinator
                 coordinator_output_dim: int = None # Defaults to model_dim if None
                 ):

        self.num_nodes = num_nodes
        self.model_dim = model_dim # Expected dimension for individual node models and activations

        self.mesh = FlowerOfLifeMesh3D(depth=mesh_depth,
                                       radius=1.0, # Default radius
                                       base_nodes=mesh_base_nodes,
                                       compute_adjacency_for_base=True,
                                       num_neighbors=mesh_num_neighbors)

        if len(self.mesh.get_primary_nodes()) != self.num_nodes:
            raise ValueError(f"FlowerOfLifeMesh3D did not create the expected number of primary nodes! "
                             f"Expected {self.num_nodes}, got {len(self.mesh.get_primary_nodes())}.")

        self.node_models: list[BandoBlock | None] = [None] * self.num_nodes

        # Store available block classes for dynamic instantiation
        self.available_block_classes = {
            kls.__name__: kls for kls in BandoBlock.__subclasses__()
        }
        # Add BandoBlock itself if it's meant to be assignable (usually not)
        # self.available_block_classes[BandoBlock.__name__] = BandoBlock


        coordinator_input_dim = self.num_nodes * self.model_dim # After concatenation
        final_coordinator_output_dim = coordinator_output_dim if coordinator_output_dim is not None else self.model_dim

        self.head_coordinator = HeadCoordinatorBlock(dim=coordinator_input_dim,
                                                     hidden_dim=coordinator_hidden_dim,
                                                     output_dim=final_coordinator_output_dim)

        # Router needs the actual list of models, which can be updated
        self.router = MeshRouter(flower_of_life_mesh=self.mesh,
                                 node_models=self.node_models, # Pass the list reference
                                 k_iterations=k_ripple_iterations)

    def assign_block_to_node(self, node_idx: int, block_class_name: str, **block_params) -> bool:
        """
        Assigns a BandoBlock instance to a specific node.
        Args:
            node_idx: Index of the node (0 to num_nodes-1).
            block_class_name: Name of the block class to instantiate (e.g., "VICtorchBlock").
            block_params: Dictionary of parameters to pass to the block's constructor (e.g., dim, heads).
                          'dim' will default to self.model_dim if not provided.
        Returns:
            True if assignment was successful, False otherwise.
        """
        if not (0 <= node_idx < self.num_nodes):
            print(f"Error: Node index {node_idx} is out of bounds.")
            return False

        block_class = self.available_block_classes.get(block_class_name)
        if not block_class:
            print(f"Error: Block class '{block_class_name}' not found in available classes: {list(self.available_block_classes.keys())}")
            return False

        # Ensure 'dim' is correctly passed; default to self.model_dim
        current_block_dim = block_params.pop('dim', self.model_dim) # Use provided dim or default

        try:
            instance = block_class(dim=current_block_dim, **block_params)
            self.node_models[node_idx] = instance
            # The router holds a reference to self.node_models, so it's updated automatically.
            print(f"Assigned {block_class_name} (dim={current_block_dim}) to node {node_idx}.")
            return True
        except Exception as e:
            print(f"Error instantiating or assigning block {block_class_name} to node {node_idx}: {e}")
            return False

    def load_block_weights_to_node(self, node_idx: int, state_dict: dict) -> bool:
        if not (0 <= node_idx < self.num_nodes):
            print(f"Error: Node index {node_idx} is out of bounds.")
            return False
        if self.node_models[node_idx] is None:
            print(f"Error: No model assigned to node {node_idx}. Assign a block first.")
            return False

        try:
            self.node_models[node_idx].load_state_dict(state_dict)
            print(f"Loaded weights into model at node {node_idx}.")
            return True
        except Exception as e:
            print(f"Error loading weights for model at node {node_idx}: {e}")
            return False

    def save_block_weights_from_node(self, node_idx: int) -> dict | None:
        if not (0 <= node_idx < self.num_nodes):
            print(f"Error: Node index {node_idx} is out of bounds.")
            return None
        if self.node_models[node_idx] is None:
            print(f"Error: No model assigned to node {node_idx}.")
            return None

        try:
            return self.node_models[node_idx].get_state_dict()
        except Exception as e:
            print(f"Error saving weights from model at node {node_idx}: {e}")
            return None

    def _pool_outputs(self, node_outputs: list[np.ndarray | None]) -> np.ndarray | None:
        """ Helper to concatenate node outputs. Assumes each output is a 1D vector of self.model_dim. """
        valid_outputs = [out for out in node_outputs if out is not None and out.ndim > 0] # Basic check
        if not valid_outputs:
            print("Warning: No valid node outputs to pool.")
            # Return a zero vector of the expected concatenated shape for the HeadCoordinatorBlock
            return np.zeros(self.num_nodes * self.model_dim)

        # Ensure all outputs are consistently shaped before concatenation
        processed_outputs = []
        for i, out in enumerate(node_outputs):
            if out is None:
                # print(f"Warning: Node {i} output is None. Replacing with zeros for pooling.")
                processed_outputs.append(np.zeros(self.model_dim))
            elif out.shape == (self.model_dim,):
                processed_outputs.append(out)
            elif out.size == self.model_dim : # e.g. (1, model_dim) or (model_dim, 1)
                processed_outputs.append(out.reshape(self.model_dim))
            else:
                # print(f"Warning: Node {i} output shape {out.shape} unexpected. Replacing with zeros.")
                # This case should ideally not happen if blocks are well-behaved.
                processed_outputs.append(np.zeros(self.model_dim))

        try:
            return np.concatenate(processed_outputs, axis=0) # Concatenates into a single flat vector
        except ValueError as e:
            print(f"Error concatenating node outputs: {e}. Check individual output shapes.")
            # Fallback to zero vector of expected shape
            return np.zeros(self.num_nodes * self.model_dim)


    def process_input(self, global_input: np.ndarray | list[np.ndarray | None]) -> np.ndarray | None:
        """
        Processes a global input through the Flower of Life network.
        Args:
            global_input:
                - If np.ndarray: Assumed to be a single vector of shape (self.model_dim,).
                  This input will be fed to all nodes that expect it.
                - If list: Assumed to be a list of np.ndarray or None, one for each node.
                  Each element is the initial activation for the corresponding node.
                  None entries mean that node starts with zero activation.
        Returns:
            The final ASI response from the HeadCoordinatorBlock.
        """
        initial_activations = [None] * self.num_nodes

        if isinstance(global_input, list):
            if len(global_input) == self.num_nodes:
                for i in range(self.num_nodes):
                    if global_input[i] is not None:
                        if global_input[i].shape == (self.model_dim,):
                            initial_activations[i] = global_input[i].copy()
                        else:
                            print(f"Warning: Shape mismatch for initial_activations[{i}]. Expected {(self.model_dim,)}, got {global_input[i].shape}. Using zeros.")
                            initial_activations[i] = np.zeros(self.model_dim)
                    else:
                        initial_activations[i] = np.zeros(self.model_dim) # Default to zeros if None
            else:
                print(f"Error: global_input list length {len(global_input)} does not match num_nodes {self.num_nodes}. Using zero activations.")
                initial_activations = [np.zeros(self.model_dim) for _ in range(self.num_nodes)]
        elif isinstance(global_input, np.ndarray):
            if global_input.shape == (self.model_dim,):
                initial_activations = [global_input.copy() for _ in range(self.num_nodes)]
            else:
                print(f"Error: global_input array shape {global_input.shape} does not match model_dim {(self.model_dim,)}. Using zero activations.")
                initial_activations = [np.zeros(self.model_dim) for _ in range(self.num_nodes)]
        else:
            print("Error: Invalid global_input type. Must be np.ndarray or list. Using zero activations.")
            initial_activations = [np.zeros(self.model_dim) for _ in range(self.num_nodes)]

        # Ripple process
        final_node_outputs = self.router.process(initial_activations)
        if not isinstance(final_node_outputs, list) or len(final_node_outputs) != self.num_nodes:
             print("Error: MeshRouter did not return expected list of outputs. Cannot proceed to HeadCoordinator.")
             return None # Or a zero vector of coordinator's output dim

        # Pool outputs
        pooled_output = self._pool_outputs(final_node_outputs)
        if pooled_output is None:
            print("Error: Failed to pool node outputs. Cannot proceed to HeadCoordinator.")
            return None


        # Final coordination
        asi_response = self.head_coordinator.forward(pooled_output)
        return asi_response

    def save_network_state(self, file_path: str) -> bool:
        """ Saves the network: assigned block types and their states, and HeadCoordinator state. """
        try:
            node_model_states = []
            for model in self.node_models:
                if model:
                    node_model_states.append({
                        "class_name": model.__class__.__name__,
                        "state_dict": model.get_state_dict()
                    })
                else:
                    node_model_states.append(None)

            network_state = {
                "num_nodes": self.num_nodes,
                "model_dim": self.model_dim,
                "mesh_config": { # Save essential mesh construction params
                    "depth": self.mesh.depth,
                    "radius": self.mesh.radius,
                    "base_nodes": self.mesh.base_nodes_count,
                    "compute_adjacency_for_base": True, # Assuming it was computed
                    "num_neighbors": self.mesh.adjacency[0].__len__() if self.mesh.adjacency and self.num_nodes > 0 and self.mesh.adjacency.get(0) else 6 # Infer from first node or default
                },
                "router_config": {
                    "k_iterations": self.router.k_iterations,
                    "attenuation": self.router.attenuation
                },
                "node_model_states": node_model_states,
                "head_coordinator_state": self.head_coordinator.get_state_dict()
            }
            with open(file_path, "wb") as f:
                pickle.dump(network_state, f)
            print(f"FlowerOfLifeNetworkOrchestrator state saved to {file_path}")
            return True
        except Exception as e:
            print(f"Error saving network state: {e}")
            return False

    def load_network_state(self, file_path: str) -> bool:
        """ Loads the network state from a file. """
        try:
            with open(file_path, "rb") as f:
                network_state = pickle.load(f)

            # Re-initialize components based on saved state
            self.num_nodes = network_state["num_nodes"]
            self.model_dim = network_state["model_dim"]

            mesh_conf = network_state.get("mesh_config", { # Provide defaults if missing
                "depth": 1, "radius": 1.0, "base_nodes": self.num_nodes,
                "compute_adjacency_for_base": True, "num_neighbors": 6
            })
            self.mesh = FlowerOfLifeMesh3D(
                depth=mesh_conf["depth"], radius=mesh_conf["radius"], base_nodes=mesh_conf["base_nodes"],
                compute_adjacency_for_base=mesh_conf["compute_adjacency_for_base"],
                num_neighbors=mesh_conf["num_neighbors"]
            )

            self.node_models = [None] * self.num_nodes
            loaded_node_model_states = network_state["node_model_states"]
            for i, model_state_info in enumerate(loaded_node_model_states):
                if model_state_info:
                    class_name = model_state_info["class_name"]
                    state_dict = model_state_info["state_dict"]
                    block_class = self.available_block_classes.get(class_name)
                    if block_class:
                        # Determine dim from state_dict, fallback to self.model_dim
                        block_dim = state_dict.get("dim", self.model_dim)
                        # For blocks like VICtorchBlock, 'heads' might be in state_dict or need default
                        # This simplified instantiation assumes 'dim' is primary constructor arg after class name
                        # More complex blocks might need more sophisticated reconstruction from state_dict keys

                        # A more robust way: check constructor signature or have factory method
                        # For now, assuming 'dim' is the main one.
                        # Example: if block_class is VICtorchBlock, heads = state_dict.get('heads', 8)
                        # For simplicity, pass all of state_dict as params, let block constructor pick
                        # No, block constructors are specific. We need to extract relevant params.

                        # Simplification: just pass dim for now. assign_block_to_node is more robust for this.
                        # Or, blocks should be able to init from their own state_dict['dim'] etc.
                        try:
                             # Pass only dim; specific params like 'heads' are loaded via load_state_dict
                            instance = block_class(dim=block_dim)
                            instance.load_state_dict(state_dict)
                            self.node_models[i] = instance
                        except Exception as e_inst:
                             print(f"Error instantiating/loading state for block {class_name} at node {i}: {e_inst}")
                    else:
                        print(f"Warning: Block class '{class_name}' for node {i} not found. Node will be empty.")

            router_conf = network_state.get("router_config", {"k_iterations":3, "attenuation":0.5})
            self.router = MeshRouter(self.mesh, self.node_models,
                                     k_iterations=router_conf["k_iterations"],
                                     attenuation=router_conf["attenuation"])

            head_coord_state = network_state["head_coordinator_state"]
            coord_input_dim = head_coord_state.get("input_dim", self.num_nodes * self.model_dim)
            coord_hidden_dim = head_coord_state.get("hidden_dim", 128) # Default if not in state
            coord_output_dim = head_coord_state.get("output_dim", self.model_dim) # Default if not in state

            self.head_coordinator = HeadCoordinatorBlock(dim=coord_input_dim,
                                                         hidden_dim=coord_hidden_dim,
                                                         output_dim=coord_output_dim)
            self.head_coordinator.load_state_dict(head_coord_state)

            print(f"FlowerOfLifeNetworkOrchestrator state loaded from {file_path}")
            return True
        except Exception as e:
            print(f"Error loading network state: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    np.random.seed(777); dim_ex=32; x_in=np.random.randn(dim_ex,dim_ex)
    print("\n--- Testing FlowerOfLifeMesh3D ---")
    fol_tst=FlowerOfLifeMesh3D(depth=1,radius=1.0,base_nodes=7,compute_adjacency_for_base=True,num_neighbors=3)
    print(f"FOLMesh3D (7 nodes, depth 1) node count: {fol_tst.node_count()}")
    p_nodes=fol_tst.get_primary_nodes(); print(f"Primary nodes: {len(p_nodes)}")
    if p_nodes: print(f"Adj for node 0 ({p_nodes[0]['id']}): {fol_tst.adjacency.get(p_nodes[0]['id'])}")
    print("\n--- Testing BandoRealityMeshMonolith ---")
    mono=BandoRealityMeshMonolith(dim=dim_ex); print(f">>> Monolith internal mesh node count: {mono.fm.node_count()}")
    out_mf=mono.mesh_forward(x_in,node_sequence=["VICtorchBlock","FractalAttentionBlock","MegaTransformerBlock"])
    print(f">>> Output shape after mesh_forward: {out_mf.shape}"); print(f">>> Monolith summary: {mono.summary()}")
    print("\n--- Testing Block Save/Load ---")
    vt_b=VICtorchBlock(dim=dim_ex); vt_b.Wq[0,0]=123.456; sd_vt=vt_b.get_state_dict()
    n_vt_b=VICtorchBlock(dim=dim_ex); n_vt_b.load_state_dict(sd_vt); assert n_vt_b.Wq[0,0]==123.456, "VTBlock load fail"
    print("VICtorchBlock save/load test PASSED.")
    print("\n--- Testing Monolith Save/Load ---")
    mono.blocks["VICtorchBlock"].Wq[0,1]=789.123; sd_m=mono.get_state_dict()
    import pickle
    with open("temp_monolith_test.pkl","wb") as f_pkl: pickle.dump(sd_m,f_pkl) # Renamed f to f_pkl
    with open("temp_monolith_test.pkl","rb") as f_pkl_rb: lsd_m=pickle.load(f_pkl_rb) # Renamed f to f_pkl_rb loaded_state_dict_mono
    n_mono=BandoRealityMeshMonolith(dim=dim_ex); n_mono.load_state_dict(lsd_m)
    assert n_mono.blocks["VICtorchBlock"].Wq[0,1]==789.123, "Monolith load fail"
    print("BandoRealityMeshMonolith save/load test PASSED.")

    print("\n--- Testing MeshRouter ---")
    # Use a small mesh for testing the router
    # Ensure FlowerOfLifeMesh3D is tested with compute_adjacency_for_base=True for this to work
    # Let's use the 7-node mesh already created for testing FlowerOfLifeMesh3D: fol_tst
    # fol_tst = FlowerOfLifeMesh3D(depth=1, radius=1.0, base_nodes=7, compute_adjacency_for_base=True, num_neighbors=2)
    # print(f"Mesh for Router Test - Adjacency: {fol_tst.adjacency}")

    num_test_nodes = len(fol_tst.get_primary_nodes())
    test_node_dim = dim_ex # Using dim_ex from previous tests

    # Create dummy models for the router test
    test_models = []
    for i in range(num_test_nodes):
        # Alternate block types for variety, ensure they exist
        if i % 2 == 0 and "VICtorchBlock" in locals():
            test_models.append(VICtorchBlock(dim=test_node_dim))
        elif "OmegaTensorBlock" in locals():
            test_models.append(OmegaTensorBlock(dim=test_node_dim))
        else: # Fallback if specific blocks aren't defined in this scope (should be)
            test_models.append(BandoBlock(dim=test_node_dim))


    router = MeshRouter(flower_of_life_mesh=fol_tst,
                        node_models=test_models,
                        k_iterations=2,
                        attenuation=0.5)

    # Initial activations: list of numpy arrays
    initial_acts = [np.random.randn(test_node_dim) for _ in range(num_test_nodes)]

    final_acts = router.process(initial_activations=initial_acts)

    print(f"MeshRouter initial activation example shape: {initial_acts[0].shape if num_test_nodes > 0 else 'N/A'}")
    print(f"MeshRouter final activation example shape: {final_acts[0].shape if num_test_nodes > 0 and final_acts[0] is not None else 'N/A'}")
    print(f"Number of final activations: {len(final_acts)}")

    assert len(final_acts) == num_test_nodes, "MeshRouter did not return correct number of activations."
    if num_test_nodes > 0 and final_acts[0] is not None:
        assert final_acts[0].shape == (test_node_dim,), "MeshRouter output activation shape mismatch."
    print("MeshRouter basic processing test PASSED (structural checks).")

    print("\n--- Testing HeadCoordinatorBlock ---")
    input_dim_hcb = 37 * dim_ex # Example: 37 nodes, each with dim_ex output
    hidden_dim_hcb = 128
    output_dim_hcb = dim_ex # Example output dim

    hcb = HeadCoordinatorBlock(dim=input_dim_hcb, hidden_dim=hidden_dim_hcb, output_dim=output_dim_hcb)

    # Create dummy combined input from 37 nodes
    dummy_fol_output = np.random.randn(input_dim_hcb)
    final_response = hcb.forward(dummy_fol_output)
    print(f"HeadCoordinatorBlock input shape: {dummy_fol_output.shape}, output shape: {final_response.shape}")
    assert final_response.shape == (output_dim_hcb,), "HeadCoordinatorBlock output shape mismatch"

    hcb.W1[0,0] = 99.88
    hcb_state = hcb.get_state_dict()

    new_hcb = HeadCoordinatorBlock(dim=input_dim_hcb, hidden_dim=hidden_dim_hcb, output_dim=output_dim_hcb)
    new_hcb.load_state_dict(hcb_state)
    assert new_hcb.W1[0,0] == 99.88, "HeadCoordinatorBlock load_state_dict failed"
    print("HeadCoordinatorBlock save/load test PASSED.")

    print("\n--- Testing FlowerOfLifeNetworkOrchestrator ---")
    fol_orchestrator = FlowerOfLifeNetworkOrchestrator(
        num_nodes=7, # Smaller for testing
        model_dim=dim_ex,
        mesh_depth=1,
        mesh_base_nodes=7,
        mesh_num_neighbors=2,
        k_ripple_iterations=1,
        coordinator_hidden_dim=64,
        coordinator_output_dim=dim_ex
    )

    # Assign some blocks
    fol_orchestrator.assign_block_to_node(0, "VICtorchBlock", heads=4) # dim defaults to model_dim (dim_ex)
    fol_orchestrator.assign_block_to_node(1, "OmegaTensorBlock")
    # Node 2 will remain None (no model)
    fol_orchestrator.assign_block_to_node(3, "FractalAttentionBlock", depth=2)

    # Test processing with a single vector input
    print("Testing orchestrator process_input with single vector...")
    single_input_vector = np.random.randn(dim_ex)
    response = fol_orchestrator.process_input(single_input_vector)
    if response is not None:
        print(f"Orchestrator response shape (single input): {response.shape}")
        assert response.shape == (dim_ex,), "Orchestrator response shape mismatch for single input."
    else:
        print("Orchestrator process_input (single) returned None, check logs.")


    # Test processing with a list of inputs
    print("Testing orchestrator process_input with list of vectors...")
    list_input_vectors = [np.random.randn(dim_ex) if i != 2 else None for i in range(7)] # Node 2 has None input
    response_list_input = fol_orchestrator.process_input(list_input_vectors)
    if response_list_input is not None:
        print(f"Orchestrator response shape (list input): {response_list_input.shape}")
        assert response_list_input.shape == (dim_ex,), "Orchestrator response shape mismatch for list input."
    else:
        print("Orchestrator process_input (list) returned None, check logs.")


    # Test save/load of the network state
    orchestrator_save_path = "temp_fol_orchestrator_state.pkl"
    print(f"Saving orchestrator state to {orchestrator_save_path}...")
    save_success = fol_orchestrator.save_network_state(orchestrator_save_path)
    assert save_success, "Failed to save orchestrator state."

    if save_success:
        print(f"Loading orchestrator state from {orchestrator_save_path}...")
        new_orchestrator = FlowerOfLifeNetworkOrchestrator(num_nodes=7, model_dim=dim_ex) # Create fresh instance
        load_success = new_orchestrator.load_network_state(orchestrator_save_path)
        assert load_success, "Failed to load orchestrator state."

        if load_success:
            assert new_orchestrator.node_models[0] is not None and isinstance(new_orchestrator.node_models[0], VICtorchBlock)
            assert new_orchestrator.node_models[1] is not None and isinstance(new_orchestrator.node_models[1], OmegaTensorBlock)
            assert new_orchestrator.node_models[2] is None # Was not assigned
            assert new_orchestrator.node_models[3] is not None and isinstance(new_orchestrator.node_models[3], FractalAttentionBlock)
            # Optionally, check some weights if they were modified and saved/loaded, e.g.
            # fol_orchestrator.node_models[0].Wq[0,0] = 11.22
            # fol_orchestrator.save_network_state(orchestrator_save_path)
            # new_orchestrator.load_network_state(orchestrator_save_path)
            # assert new_orchestrator.node_models[0].Wq[0,0] == 11.22

            # Test processing with loaded network
            print("Testing processing with loaded orchestrator...")
            response_after_load = new_orchestrator.process_input(single_input_vector)
            if response_after_load is not None:
                 print(f"Orchestrator response shape (after load): {response_after_load.shape}")
                 assert response_after_load.shape == (dim_ex,)
            else:
                 print("Orchestrator process_input (after load) returned None.")

            print("FlowerOfLifeNetworkOrchestrator save/load and functionality test PASSED.")
        try:
            os.remove(orchestrator_save_path)
        except Exception as e_rem:
            print(f"Could not remove temp file {orchestrator_save_path}: {e_rem}")

    try: import os; os.remove("temp_monolith_test.pkl")
    except: pass
