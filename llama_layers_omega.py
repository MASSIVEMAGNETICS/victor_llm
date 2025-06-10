import numpy as np
from OmegaTensor import OmegaTensor, OpRegistry # OpRegistry might not be directly needed if using tensor methods
from typing import Optional

from typing import List # Added for type hinting

# Placeholder for ModelArgs - will be properly defined later
class SimpleModelArgs:
    def __init__(self, dim: int, n_layers: int, n_heads: int, n_kv_heads: Optional[int],
                 vocab_size: int, ffn_hidden_dim: int, max_seq_len: int,
                 norm_eps: float = 1e-5, rope_theta: float = 10000.0):
        self.dim = dim
        self.n_layers = n_layers
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads if n_kv_heads is not None else n_heads # For MHA if n_kv_heads is None
        self.vocab_size = vocab_size
        self.ffn_hidden_dim = ffn_hidden_dim
        self.max_seq_len = max_seq_len
        self.norm_eps = norm_eps
        self.rope_theta = rope_theta
        self.head_dim = dim // n_heads
        if self.head_dim * self.n_heads != self.dim:
            raise ValueError(f"dim ({dim}) must be divisible by n_heads ({n_heads})")


# Helper function for Rotary Positional Embedding
def apply_rotary_emb(x: OmegaTensor, freqs_cis: OmegaTensor) -> OmegaTensor:
    """
    Applies rotary positional embedding to input tensor x.
    Args:
        x: OmegaTensor of shape (bsz, seq_len, dim) or (bsz, num_heads, seq_len, head_dim)
        freqs_cis: OmegaTensor of shape (seq_len, dim) or (seq_len, head_dim) containing
                   interleaved cos/sin values. Expected to not require gradients.
                   Shape must be broadcastable to the last two dimensions of x.
    Returns:
        OmegaTensor with rotary embeddings applied, same shape as x.
    """
    # This function now directly uses the RotaryEmbeddingOp via the OmegaTensor method.
    if not hasattr(x, 'apply_rotary_embedding'):
        raise AttributeError("OmegaTensor instance does not have 'apply_rotary_embedding' method. "
                             "Ensure OmegaTensor.py is updated with RotaryEmbeddingOp and its method.")
    return x.apply_rotary_embedding(freqs_cis)

def repeat_kv(x: OmegaTensor, n_rep: int) -> OmegaTensor:
    """
    Repeats the Key/Value heads n_rep times for Grouped Query Attention.
    Input x: OmegaTensor of shape (bsz, n_kv_heads, seq_len, head_dim)
    Output: OmegaTensor of shape (bsz, n_kv_heads * n_rep, seq_len, head_dim)
    """
    if n_rep == 1:
        return x

    bsz, n_kv_heads, seq_len, head_dim = x.shape

    # Step 1: Reshape to (bsz, n_kv_heads, 1, seq_len, head_dim)
    # The reshape op in OmegaTensor needs a tuple for the new shape.
    x_expanded = x.reshape((bsz, n_kv_heads, 1, seq_len, head_dim))

    # Step 2: Create a list of n_rep copies of x_expanded
    repeated_tensors_list = [x_expanded] * n_rep

    # Step 3: Concatenate along the newly added dimension (axis=2)
    # Resulting shape: (bsz, n_kv_heads, n_rep, seq_len, head_dim)
    tiled_x = OmegaTensor.concatenate(repeated_tensors_list, axis=2)

    # Step 4: Reshape to merge n_kv_heads and n_rep dimensions
    # Final shape: (bsz, n_kv_heads * n_rep, seq_len, head_dim)
    final_output = tiled_x.reshape((bsz, n_kv_heads * n_rep, seq_len, head_dim))

    return final_output

class OmegaLayer:
    """
    Base class for layers in the Omega framework, similar to torch.nn.Module.
    It can manage parameters and define a forward pass.
    """
    def __init__(self):
        self._parameters = {} # For storing OmegaTensor parameters directly in this layer
        self._sub_layers = [] # For storing sub-OmegaLayer instances

    def __call__(self, *args, **kwargs):
        # The forward pass logic will be implemented by subclasses
        raise NotImplementedError("Each OmegaLayer must implement its own __call__ method.")

    def parameters(self):
        """
        Returns a list of all learnable OmegaTensor parameters in this layer
        and any registered sub-layers. Ensures uniqueness.
        """
        param_list = []
        # Add parameters directly registered to this layer
        for name, param in self._parameters.items():
            if isinstance(param, OmegaTensor) and param.requires_grad:
                param_list.append(param)

        # Add parameters from registered sub-layers
        for layer in self._sub_layers:
            param_list.extend(layer.parameters()) # Recursively get parameters

        # Return unique parameters (important if a parameter could be shared or added multiple times)
        # Using dict.fromkeys to maintain order and get uniqueness, then list()
        return list(dict.fromkeys(param_list))


    def _register_parameter(self, name: str, tensor: OmegaTensor):
        """Registers an OmegaTensor parameter, making it accessible as an attribute."""
        if not isinstance(tensor, OmegaTensor):
            raise TypeError(f"Can only register OmegaTensor as a parameter, got {type(tensor)} for '{name}'.")

        setattr(self, name, tensor) # Make it accessible as self.name (e.g., self.weight)
        self._parameters[name] = tensor # Track it in the internal dictionary

    def _register_layer(self, name: str, layer):
        """Registers a sub-layer, making it accessible as an attribute and collecting its parameters."""
        if not isinstance(layer, OmegaLayer):
            raise TypeError(f"Can only register OmegaLayer as a sub-layer, got {type(layer)} for '{name}'.")
        setattr(self, name, layer) # Make it accessible as self.name (e.g., self.wq)
        self._sub_layers.append(layer) # Add to list for parameter collection


class Embedding(OmegaLayer):
    """
    Embedding layer: looks up embedding vectors for given indices.
    """
    def __init__(self, num_embeddings: int, embedding_dim: int, name: str = "embedding"):
        super().__init__()
        self.num_embeddings = num_embeddings
        self.embedding_dim = embedding_dim

        # Initialize weight matrix
        # Standard practice: initialize with small random values, e.g., from N(0, 0.02^2) or U(-sqrt(k), sqrt(k))
        # Using normal distribution here.
        weight_data = np.random.randn(num_embeddings, embedding_dim).astype(np.float32) * 0.02

        # Register the weight as a parameter
        self._register_parameter(f"{name}_weight", OmegaTensor(weight_data, requires_grad=True, name=f"{name}_weight"))
        # self.weight is now accessible via getattr from _register_parameter

    def __call__(self, indices):
        """
        Performs the embedding lookup.
        Args:
            indices: An OmegaTensor, list, or NumPy array of integer indices.
        Returns:
            An OmegaTensor containing the corresponding embedding vectors.
        """
        # Ensure indices is an OmegaTensor.
        # The OmegaTensor constructor handles np.array and list inputs.
        # The EmbeddingOp (called by indices_omega.embedding) will handle dtype conversion for .data
        if not isinstance(indices, OmegaTensor):
            indices_omega = OmegaTensor(indices, requires_grad=False, name="embedding_indices")
        else:
            indices_omega = indices

        # Check if the OmegaTensor class has the 'embedding' method
        if hasattr(indices_omega, 'embedding') and callable(getattr(indices_omega, 'embedding')):
            # Use the method: indices_tensor.embedding(self.weight)
            # self.weight is accessed via its registered name, e.g., self.embedding_weight
            # Need to access the weight parameter correctly. It was set as self.<name>_weight.
            # For a default name "embedding", it's self.embedding_weight.
            weight_param_name = [name for name in self._parameters.keys() if name.endswith("_weight")][0]
            return indices_omega.embedding(getattr(self, weight_param_name))
        else:
            # Fallback to OpRegistry if the method is not available for some reason
            # This also requires accessing the weight parameter correctly.
            weight_param_name = [name for name in self._parameters.keys() if name.endswith("_weight")][0]
            return OpRegistry['embedding'](getattr(self, weight_param_name), indices_omega)

    def parameters(self):
        """
        Returns the list of learnable parameters for this Embedding layer.
        """
        # Overrides the base class method to return specific parameters.
        # Parameters are already collected by the base class's parameters() method
        # if _register_parameter is used correctly.
        return super().parameters()

class Linear(OmegaLayer):
    """
    Linear transformation layer: y = xW + b
    """
    def __init__(self, in_features: int, out_features: int, bias: bool = True, name: str = "linear_default_name"):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.use_bias = bias
        self.name = name

        # Initialize weight matrix
        weight_data = np.random.randn(in_features, out_features).astype(np.float32) * np.sqrt(1. / in_features)
        self._register_parameter("weight", OmegaTensor(weight_data, requires_grad=True, name=f"{self.name}_weight"))

        if self.use_bias:
            bias_data = np.zeros(out_features, dtype=np.float32)
            self._register_parameter("bias", OmegaTensor(bias_data, requires_grad=True, name=f"{self.name}_bias"))
        else:
            self.bias = None # Explicitly set to None if no bias

    def __call__(self, input_tensor: OmegaTensor):
        """
        Applies the linear transformation.
        Args:
            input_tensor: An OmegaTensor with shape (..., in_features).
        Returns:
            An OmegaTensor with shape (..., out_features).
        """
        if not isinstance(input_tensor, OmegaTensor):
            input_tensor = OmegaTensor(input_tensor, requires_grad=getattr(input_tensor, 'requires_grad', False))

        output = input_tensor.matmul(self.weight)

        if self.use_bias and self.bias is not None:
            output = output + self.bias
        return output

class RMSNorm(OmegaLayer):
    """
    Root Mean Square Layer Normalization.
    RMSNorm = x / sqrt(mean(x^2) + eps) * weight
    """
    def __init__(self, dim: int, eps: float = 1e-5, name: str = "rmsnorm_default_name"):
        super().__init__()
        self.dim = dim
        self.eps = eps # epsilon is a Python float, used in calculations
        self.name = name

        # Initialize weight (gamma) parameter, typically to ones
        weight_data = np.ones(dim, dtype=np.float32)
        self._register_parameter("weight", OmegaTensor(weight_data, requires_grad=True, name=f"{self.name}_weight"))

    def __call__(self, x: OmegaTensor):
        """
        Applies RMSNorm to the input tensor x.
        Args:
            x: An OmegaTensor, typically with shape (..., dim). Normalization is over the last dimension.
        Returns:
            An OmegaTensor with the same shape as x.
        """
        if not isinstance(x, OmegaTensor):
            # Convert if not already an OmegaTensor, though inputs to layers usually are.
            x = OmegaTensor(x, requires_grad=getattr(x, 'requires_grad', False))

        # Calculate Root Mean Square: sqrt(mean(x^2))
        # 1. Square the input: x_squared = x * x  (or x.pow(2.0))
        #    x.pow(2.0) uses OpRegistry['pow'](self, self._ensure_tensor(exponent_val))
        #    self._ensure_tensor(2.0) creates OmegaTensor(2.0, requires_grad=False)
        x_squared = x.pow(2.0)

        # 2. Mean of squares along the last dimension
        #    mean(axis=-1, keepdims=True)
        mean_x_squared = x_squared.mean(axis=-1, keepdims=True)

        # 3. Add epsilon for numerical stability: mean_x_squared + eps
        #    self.eps is a float. OmegaTensor's __add__ calls _ensure_tensor(self.eps)
        variance_plus_eps = mean_x_squared + self.eps

        # 4. Compute reciprocal square root: (mean_x_squared + eps)^(-0.5)
        rsqrt_val = variance_plus_eps.pow(-0.5)

        # 5. Normalize x: x_normalized = x * rsqrt_val
        x_normalized = x * rsqrt_val

        # 6. Scale by the learnable weight parameter
        #    self.weight has shape (dim,). x_normalized has shape (..., dim).
        #    Broadcasting should apply.
        output = x_normalized * self.weight

        return output

# SiLU activation function: x * sigmoid(x)
def silu(x: OmegaTensor) -> OmegaTensor:
    """
    SiLU (Swish) activation function: x * sigmoid(x)
    Sigmoid = 1 / (1 + exp(-x))
    """
    # Ensure '1.0' is an OmegaTensor for ops, with matching dtype if possible, and no grad.
    # OmegaTensor defaults to float32. If x can be other types, this might need adjustment
    # or rely on ops to handle mixed types if they can.
    # For now, assume x.data.dtype is compatible with float32 or is float32.
    one = OmegaTensor(1.0, requires_grad=False, name="const_one_silu")

    # sigmoid_x = 1.0 / (1.0 + (-x).exp())
    # Need to ensure all ops handle OmegaTensor with scalar or OmegaTensor with OmegaTensor.
    # (-x) is handled by __neg__ if defined, or MulOp(x, OmegaTensor(-1.0)).
    # .exp() is an OmegaTensor method.
    # (one + tensor) uses __add__.
    # (one / tensor) uses __truediv__.
    sigmoid_x = one / (one + (-x).exp())

    return x * sigmoid_x

class FeedForward(OmegaLayer):
    """
    FeedForward network block used in Transformer, typically with SiLU activation.
    Uses three linear layers: w1 (gate), w3 (up-projection), w2 (down-projection).
    Output = w2(silu(w1(x)) * w3(x))
    """
    def __init__(self, dim: int, hidden_dim: int,
                 multiple_of: int = 256, # Not directly used if hidden_dim is pre-calculated
                 ffn_dim_multiplier: Optional[float] = None, # Not directly used if hidden_dim is pre-calculated
                 name: str = "ffn_default_name"):
        super().__init__()
        self.name = name

        # Assuming hidden_dim is the final calculated dimension for the intermediate layer
        # The logic for multiple_of and ffn_dim_multiplier would typically be applied
        # by the model configuration before this layer is instantiated.

        # Initialize linear layers
        w1 = Linear(dim, hidden_dim, bias=False, name=f"{name}_w1")
        w2 = Linear(hidden_dim, dim, bias=False, name=f"{name}_w2")
        w3 = Linear(dim, hidden_dim, bias=False, name=f"{name}_w3")

        # Register sub-layers so their parameters are collected
        self._register_layer("w1", w1)
        self._register_layer("w2", w2)
        self._register_layer("w3", w3)

    def __call__(self, x: OmegaTensor):
        """
        Forward pass for the FeedForward network.
        Args:
            x: Input OmegaTensor, typically shape (batch_size, seq_len, dim).
        Returns:
            Output OmegaTensor, shape (batch_size, seq_len, dim).
        """
        # Ensure x is an OmegaTensor (though typically it will be)
        if not isinstance(x, OmegaTensor):
            x = OmegaTensor(x, requires_grad=getattr(x, 'requires_grad', False))

        # Apply transformations
        # gate_output = silu(w1(x))
        # value_output = w3(x)
        # combined = gate_output * value_output
        # output = w2(combined)

        # Using self.w1, self.w2, self.w3 because _register_layer sets them as attributes
        swish_gate_output = silu(self.w1(x))
        value_vector = self.w3(x)

        hidden_states = swish_gate_output * value_vector
        output = self.w2(hidden_states)

        return output

class Attention(OmegaLayer):
    def __init__(self, dim: int, n_heads: int, n_kv_heads: int, head_dim: int, name: str = "attention"):
        super().__init__()
        self.dim = dim
        self.n_heads = n_heads
        self.n_kv_heads = n_kv_heads
        self.head_dim = head_dim
        self.name = name

        if self.n_heads % self.n_kv_heads != 0:
            raise ValueError(f"n_heads ({self.n_heads}) must be divisible by n_kv_heads ({self.n_kv_heads})")
        self.n_rep = self.n_heads // self.n_kv_heads

        # Linear projections
        self.wq = Linear(dim, self.n_heads * self.head_dim, bias=False, name=f"{name}_wq")
        self.wk = Linear(dim, self.n_kv_heads * self.head_dim, bias=False, name=f"{name}_wk")
        self.wv = Linear(dim, self.n_kv_heads * self.head_dim, bias=False, name=f"{name}_wv")
        self.wo = Linear(self.n_heads * self.head_dim, dim, bias=False, name=f"{name}_wo")

        # Register sub-layers
        self._register_layer("wq", self.wq)
        self._register_layer("wk", self.wk)
        self._register_layer("wv", self.wv)
        self._register_layer("wo", self.wo)

    def __call__(self, x: OmegaTensor, freqs_cis: OmegaTensor, mask: Optional[OmegaTensor]) -> OmegaTensor:
        bsz, seqlen, _ = x.shape # x is (bsz, seqlen, dim)

        # QKV projections
        xq, xk, xv = self.wq(x), self.wk(x), self.wv(x)
        # xq: (bsz, seqlen, n_heads * head_dim)
        # xk: (bsz, seqlen, n_kv_heads * head_dim)
        # xv: (bsz, seqlen, n_kv_heads * head_dim)

        # Reshape for RoPE application (bsz, seqlen, num_selected_heads, head_dim)
        xq_rope = xq.reshape(bsz, seqlen, self.n_heads, self.head_dim)
        xk_rope = xk.reshape(bsz, seqlen, self.n_kv_heads, self.head_dim)

        # Apply rotary embeddings
        # freqs_cis shape is (seqlen, head_dim)
        xq_applied_rope = apply_rotary_emb(xq_rope, freqs_cis)
        xk_applied_rope = apply_rotary_emb(xk_rope, freqs_cis)

        # Reshape for multi-head attention: (bsz, n_heads_variant, seqlen, head_dim) and transpose
        xq = xq_applied_rope.transpose(1, 2) # (bsz, n_heads, seqlen, head_dim)
        xk = xk_applied_rope.transpose(1, 2) # (bsz, n_kv_heads, seqlen, head_dim)
        xv = xv.reshape(bsz, seqlen, self.n_kv_heads, self.head_dim).transpose(1, 2) # (bsz, n_kv_heads, seqlen, head_dim)

        # Repeat KV heads if GQA/MQA
        if self.n_rep > 1:
            xk = repeat_kv(xk, self.n_rep) # (bsz, n_heads, seqlen, head_dim)
            xv = repeat_kv(xv, self.n_rep) # (bsz, n_heads, seqlen, head_dim)

        # Scaled dot-product attention
        scores = xq.matmul(xk.transpose(-2, -1)) # (bsz, n_heads, seqlen, seqlen)

        scaler = OmegaTensor(self.head_dim**-0.5, requires_grad=False)
        scores = scores * scaler

        if mask is not None:
            scores = scores + mask # Mask should broadcast: (1,1,seqlen,seqlen) or (bsz,n_heads,seqlen,seqlen)

        attn_weights = scores.softmax(axis=-1)

        output = attn_weights.matmul(xv) # (bsz, n_heads, seqlen, head_dim)

        # Concatenate heads and reshape back
        output = output.transpose(1, 2).reshape(bsz, seqlen, self.dim) # (bsz, seqlen, dim)

        output = self.wo(output)

        return output

class TransformerBlock(OmegaLayer):
    def __init__(self, layer_id: int, args: SimpleModelArgs, name: str = "block"):
        super().__init__()
        self.layer_id = layer_id
        self.args = args # Store args if needed later, e.g. for printing
        self.name = name

        # Attention component
        self.attention = Attention(
            args.dim,
            args.n_heads,
            args.n_kv_heads,
            args.head_dim,
            name=f"{name}{layer_id}_attn"
        )
        # FeedForward component
        self.feed_forward = FeedForward(
            args.dim,
            args.ffn_hidden_dim,
            name=f"{name}{layer_id}_ffn"
        )
        # Normalization layers
        self.attention_norm = RMSNorm(args.dim, eps=args.norm_eps, name=f"{name}{layer_id}_attn_norm")
        self.ffn_norm = RMSNorm(args.dim, eps=args.norm_eps, name=f"{name}{layer_id}_ffn_norm")

        # Register sub-layers
        self._register_layer("attention_norm", self.attention_norm)
        self._register_layer("attention", self.attention)
        self._register_layer("ffn_norm", self.ffn_norm)
        self._register_layer("feed_forward", self.feed_forward)

    def __call__(self, x: OmegaTensor, freqs_cis: OmegaTensor, mask: Optional[OmegaTensor]) -> OmegaTensor:
        # Residual connection for attention
        normed_x = self.attention_norm(x)
        attn_out = self.attention(normed_x, freqs_cis, mask)
        h = x + attn_out

        # Residual connection for feed-forward
        normed_h = self.ffn_norm(h)
        ffn_out = self.feed_forward(normed_h)
        out = h + ffn_out

        return out

class TransformerOmega(OmegaLayer):
    def __init__(self, args: SimpleModelArgs, name: str = "transformer"):
        super().__init__()
        self.args = args
        self.name = name

        self.tok_embeddings = Embedding(args.vocab_size, args.dim, name=f"{name}_tok_emb")
        self._register_layer("tok_embeddings", self.tok_embeddings)

        self.layers = []
        for i in range(args.n_layers):
            block = TransformerBlock(i, args, name=f"{name}_block")
            self.layers.append(block)
            self._register_layer(f"block{i}", block)

        self.norm = RMSNorm(args.dim, eps=args.norm_eps, name=f"{name}_norm")
        self._register_layer("norm", self.norm)

        self.output = Linear(args.dim, args.vocab_size, bias=False, name=f"{name}_output_linear")
        self._register_layer("output", self.output)

        # Precompute freqs_cis for rotary embeddings
        # max_seq_len * 2 for potential sequence length variations or KV caching, common practice
        self.freqs_cis = self._precompute_freqs_cis(
            args.head_dim,
            args.max_seq_len * 2,
            args.rope_theta
        )
        self.freqs_cis.name = "freqs_cis_const" # Give it a name for clarity if printed

    def _precompute_freqs_cis(self, head_dim: int, max_seq_len_computed: int, theta: float) -> OmegaTensor:
        # Calculate frequencies for RoPE
        # freqs are 1.0 / (theta^( (0, 2, ..., head_dim-2) / head_dim ))
        freqs_part = np.arange(0, head_dim, 2)[: (head_dim // 2)].astype(np.float32)
        freqs = 1.0 / (theta ** (freqs_part / head_dim))

        # Create sequence position array
        t = np.arange(max_seq_len_computed, dtype=np.float32)

        # Outer product to get freqs for each position and each frequency component
        # freqs_matrix shape: (max_seq_len_computed, head_dim / 2)
        freqs_matrix = np.outer(t, freqs)

        # Interleave cosine and sine values
        # freqs_cis_data shape: (max_seq_len_computed, head_dim)
        freqs_cis_data = np.zeros((max_seq_len_computed, head_dim), dtype=np.float32)
        freqs_cis_data[:, 0::2] = np.cos(freqs_matrix)
        freqs_cis_data[:, 1::2] = np.sin(freqs_matrix)

        return OmegaTensor(freqs_cis_data, requires_grad=False)

    def __call__(self, tokens: OmegaTensor, mask: Optional[OmegaTensor] = None) -> OmegaTensor:
        if tokens.ndim == 1: # If single sequence of tokens (seqlen,)
            _bsz = 1
            seqlen = tokens.shape[0]
            # Reshape to (1, seqlen) before embedding
            h = self.tok_embeddings(tokens.reshape(1, seqlen))
        elif tokens.ndim == 2: # (bsz, seqlen)
            _bsz, seqlen = tokens.shape
            h = self.tok_embeddings(tokens)
        else:
            raise ValueError(f"Input tokens must be 1D or 2D, got {tokens.ndim}D")

        # Slice freqs_cis to current sequence length
        # self.freqs_cis is (max_seq_len_computed, head_dim)
        # We need (seqlen, head_dim)
        # Slicing .data and re-wrapping is fine as freqs_cis is non-trainable and fixed.
        if seqlen > self.freqs_cis.shape[0]:
             raise ValueError(f"Input sequence length ({seqlen}) exceeds precomputed freqs_cis length ({self.freqs_cis.shape[0]})")

        current_freqs_cis_data = self.freqs_cis.data[0:seqlen, :]
        current_freqs_cis_omega = OmegaTensor(current_freqs_cis_data, requires_grad=False, name="freqs_cis_slice")

        for layer in self.layers:
            h = layer(h, current_freqs_cis_omega, mask)

        h = self.norm(h)
        logits = self.output(h)

        return logits

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    print("Testing OmegaLayer and Embedding...")

    # Test OmegaLayer parameter registration
    base_layer = OmegaLayer()
    p1 = OmegaTensor(np.random.randn(5,5), requires_grad=True, name="p1")
    base_layer._register_parameter("param1", p1)
    print(f"Base layer parameters: {base_layer.parameters()}")

    # Test Embedding layer
    num_embed = 10
    embed_dim = 3
    embedding_layer = Embedding(num_embeddings=num_embed, embedding_dim=embed_dim)

    print(f"Embedding layer parameters: {embedding_layer.parameters()}")
    if embedding_layer.parameters():
        print(f"  Weight name: {embedding_layer.parameters()[0].name}")
        print(f"  Weight shape: {embedding_layer.parameters()[0].shape}")

    # Test forward pass
    # Test with a list
    indices_list = [1, 3, 5, 1]
    output_list = embedding_layer(indices_list)
    print(f"\nOutput for list indices {indices_list}:")
    print(output_list)

    # Test with a NumPy array
    indices_np = np.array([0, 2, 2, 4], dtype=np.int32)
    output_np = embedding_layer(indices_np)
    print(f"\nOutput for NumPy array indices {indices_np.tolist()}:")
    print(output_np)

    # Test with an OmegaTensor
    indices_omega_tensor = OmegaTensor(np.array([7, 8]), requires_grad=False, name="test_indices") # Ensure int if not handled by op
    output_omega = embedding_layer(indices_omega_tensor)
    print(f"\nOutput for OmegaTensor indices {indices_omega_tensor.data.tolist()}:")
    print(output_omega)

    # Test backward pass (simple case)
    if output_np.requires_grad:
        print("\nTesting backward pass...")
        # Create a dummy gradient output
        # If output_np.data is (say) 4x3, then dummy_grad_output should be 4x3
        dummy_grad_output_data = np.ones_like(output_np.data)

        # Assuming all parents of output_np correctly propagate requires_grad
        # and EmbeddingOp is set up.
        try:
            output_np.backward(dummy_grad_output_data)

            # Check gradient of the embedding weight
            weight_param = embedding_layer.parameters()[0]
            if weight_param.grad is not None:
                print(f"Gradient for weight (shape {weight_param.grad.shape}):")
                print(weight_param.grad)

                # Verify accumulation for repeated indices (index 2 was repeated)
                # grad for row 0: should be 1 (from indices_np[0])
                # grad for row 2: should be 2 (from indices_np[1] and indices_np[2])
                # grad for row 4: should be 1 (from indices_np[3])
                # All other rows should have zero gradient
                print(f"Gradient for row 0: {weight_param.grad[0]}")
                print(f"Gradient for row 2: {weight_param.grad[2]}") # Should sum up for repeated indices
                print(f"Gradient for row 4: {weight_param.grad[4]}")
                if weight_param.grad[2].sum() == 2 * embed_dim : # Each element of the vector gets ones
                     print("Gradient accumulation for repeated indices appears correct.")
                else:
                     print(f"Gradient for row 2 sum: {weight_param.grad[2].sum()}, expected {2*embed_dim}. Check accumulation.")

            else:
                print("No gradient computed for weight.")
        except Exception as e:
            print(f"Error during backward pass test: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nOutput does not require grad, skipping backward pass test.")

    print("\nScript execution finished.")


    # ===== Linear Layer Tests =====
    print("\n\n--- Testing Linear Layer ---")

    # [Test Case 5: Linear Layer Initialization]
    print("\n[Test Case Linear Init: Linear Layer Initialization]")
    in_f, out_f = 10, 5
    linear_layer_with_bias = Linear(in_f, out_f, bias=True, name="fc1")
    linear_layer_no_bias = Linear(in_f, out_f, bias=False, name="fc2")

    params_with_bias = linear_layer_with_bias.parameters()
    params_no_bias = linear_layer_no_bias.parameters()

    print(f"Params (with bias): {[p.name for p in params_with_bias]}")
    assert len(params_with_bias) == 2, "Linear layer with bias should have 2 parameters (weight, bias)"
    assert linear_layer_with_bias.weight in params_with_bias
    assert linear_layer_with_bias.bias in params_with_bias
    assert linear_layer_with_bias.weight.shape == (in_f, out_f)
    assert linear_layer_with_bias.bias.shape == (out_f,)


    print(f"Params (no bias): {[p.name for p in params_no_bias]}")
    assert len(params_no_bias) == 1, "Linear layer without bias should have 1 parameter (weight)"
    assert linear_layer_no_bias.weight in params_no_bias
    assert getattr(linear_layer_no_bias, 'bias', None) is None # Check bias attribute is None
    assert linear_layer_no_bias.weight.shape == (in_f, out_f)
    print("Linear layer initialization (with/without bias) seems OK.")

    # [Test Case 6: Linear Layer Forward Pass]
    print("\n[Test Case Linear Fwd: Linear Layer Forward Pass]")
    batch_size, seq_len = 2, 3

    # 2D input
    input_2d_data = np.random.randn(batch_size, in_f).astype(np.float32)
    input_2d = OmegaTensor(input_2d_data, requires_grad=True)

    output_2d_with_bias = linear_layer_with_bias(input_2d)
    print(f"Output 2D (with bias) shape: {output_2d_with_bias.shape}")
    assert output_2d_with_bias.shape == (batch_size, out_f)

    output_2d_no_bias = linear_layer_no_bias(input_2d)
    print(f"Output 2D (no bias) shape: {output_2d_no_bias.shape}")
    assert output_2d_no_bias.shape == (batch_size, out_f)

    # 3D input
    input_3d_data = np.random.randn(batch_size, seq_len, in_f).astype(np.float32)
    input_3d = OmegaTensor(input_3d_data, requires_grad=True)

    output_3d_with_bias = linear_layer_with_bias(input_3d)
    print(f"Output 3D (with bias) shape: {output_3d_with_bias.shape}")
    assert output_3d_with_bias.shape == (batch_size, seq_len, out_f)

    output_3d_no_bias = linear_layer_no_bias(input_3d)
    print(f"Output 3D (no bias) shape: {output_3d_no_bias.shape}")
    assert output_3d_no_bias.shape == (batch_size, seq_len, out_f)
    print("Linear layer forward pass (2D and 3D inputs) seems OK.")

    # [Test Case 7: Linear Layer Backward Pass]
    print("\n[Test Case Linear Bwd: Linear Layer Backward Pass]")

    # Using 2D input for simplicity in checking grads
    linear_layer_for_grad_test = Linear(in_f, out_f, bias=True, name="fc_backward_test")
    input_for_grad_data = np.random.randn(batch_size, in_f).astype(np.float32)
    input_for_grad = OmegaTensor(input_for_grad_data, requires_grad=True, name="input_for_linear_grad")

    # Zero out any previous grads
    linear_layer_for_grad_test.weight.zero_grad()
    if linear_layer_for_grad_test.bias is not None: # It is not None in this case
        linear_layer_for_grad_test.bias.zero_grad()

    output_for_grad = linear_layer_for_grad_test(input_for_grad)

    dummy_grad_out_data = np.random.randn(*output_for_grad.shape).astype(np.float32)

    print("Running backward pass for Linear layer...")
    try:
        output_for_grad.backward(dummy_grad_out_data)

        weight_grad = linear_layer_for_grad_test.weight.grad
        bias_grad = linear_layer_for_grad_test.bias.grad

        assert weight_grad is not None, "Weight grad should not be None"
        print(f"Weight grad shape: {weight_grad.shape}")
        assert weight_grad.shape == linear_layer_for_grad_test.weight.shape, "Weight grad shape mismatch"

        assert bias_grad is not None, "Bias grad should not be None when bias is used"
        print(f"Bias grad shape: {bias_grad.shape}")
        assert bias_grad.shape == linear_layer_for_grad_test.bias.shape, "Bias grad shape mismatch"

        expected_bias_grad = np.sum(dummy_grad_out_data, axis=0) # Sum over batch for 2D input
        if not np.allclose(bias_grad, expected_bias_grad):
            print(f"ERROR: Bias gradient calculation issue. Expected sum: {expected_bias_grad}, Got: {bias_grad}")
        else:
            print("Bias gradient sum check (for 2D input) seems OK.")

        assert input_for_grad.grad is not None, "Input grad should not be None if requires_grad was True"
        print(f"Input grad shape: {input_for_grad.grad.shape}")
        assert input_for_grad.grad.shape == input_for_grad.shape, "Input grad shape mismatch"

        print("Linear layer backward pass seems OK (grads exist and have correct shapes).")

    except Exception as e:
        print(f"ERROR during Linear layer backward pass test: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- All Layer Tests Finished (Embedding & Linear) ---")


    # ===== RMSNorm Layer Tests =====
    print("\n\n--- Testing RMSNorm Layer ---")

    # [Test Case 8: RMSNorm Initialization]
    print("\n[Test Case RMSNorm Init: RMSNorm Layer Initialization]")
    norm_dim = 10
    rmsnorm_layer = RMSNorm(dim=norm_dim, name="rms1")

    params_rmsnorm = rmsnorm_layer.parameters()
    print(f"RMSNorm params: {[p.name for p in params_rmsnorm]}")
    assert len(params_rmsnorm) == 1, "RMSNorm should have 1 parameter (weight)"
    assert rmsnorm_layer.weight in params_rmsnorm
    assert rmsnorm_layer.weight.shape == (norm_dim,)
    assert np.allclose(rmsnorm_layer.weight.data, np.ones(norm_dim)), "RMSNorm weight should initialize to ones"
    print("RMSNorm layer initialization seems OK.")

    # [Test Case 9: RMSNorm Forward Pass & Stats]
    print("\n[Test Case RMSNorm Fwd: Forward Pass & Statistics]")
    batch_s, seq_l = 2, 3

    # Create input data
    input_rms_2d_data = np.random.rand(batch_s, norm_dim).astype(np.float32) * 10 # Multiply to give some variance
    input_rms_2d = OmegaTensor(input_rms_2d_data, requires_grad=True)

    input_rms_3d_data = np.random.rand(batch_s, seq_l, norm_dim).astype(np.float32) * 10
    input_rms_3d = OmegaTensor(input_rms_3d_data, requires_grad=True)

    # Test with default weight (all ones)
    output_rms_2d = rmsnorm_layer(input_rms_2d)
    print(f"Output RMSNorm 2D shape: {output_rms_2d.shape}")
    assert output_rms_2d.shape == (batch_s, norm_dim)

    # Check RMS of each row in output_rms_2d.data (should be close to 1 if weight is 1)
    rms_2d_output = np.sqrt(np.mean(np.square(output_rms_2d.data), axis=-1))
    print(f"RMS of 2D output rows (target approx 1.0): {rms_2d_output}")
    assert np.allclose(rms_2d_output, 1.0, atol=1e-6), "RMS of output rows should be close to 1 when weight is 1"

    output_rms_3d = rmsnorm_layer(input_rms_3d)
    print(f"Output RMSNorm 3D shape: {output_rms_3d.shape}")
    assert output_rms_3d.shape == (batch_s, seq_l, norm_dim)

    rms_3d_output = np.sqrt(np.mean(np.square(output_rms_3d.data), axis=-1))
    print(f"RMS of 3D output feature vectors (target approx 1.0): {rms_3d_output.flatten()[:5]}...") # print first 5
    assert np.allclose(rms_3d_output, 1.0, atol=1e-6), "RMS of output vectors should be close to 1 when weight is 1"

    # Test with a non-default weight
    rmsnorm_layer.weight.data *= 2.0 # Scale weights
    output_rms_2d_scaled = rmsnorm_layer(input_rms_2d)
    rms_2d_output_scaled = np.sqrt(np.mean(np.square(output_rms_2d_scaled.data), axis=-1))
    print(f"RMS of 2D output rows (scaled weights, target approx 2.0): {rms_2d_output_scaled}")
    assert np.allclose(rms_2d_output_scaled, 2.0, atol=1e-6), "RMS of output rows should scale with weight"
    rmsnorm_layer.weight.data /= 2.0 # Reset weight for next test

    print("RMSNorm forward pass (2D, 3D inputs) and statistics check seem OK.")

    # [Test Case 10: RMSNorm Backward Pass]
    print("\n[Test Case RMSNorm Bwd: Backward Pass]")

    # Using 2D input for simplicity
    rmsnorm_layer_for_grad = RMSNorm(dim=norm_dim, name="rms_grad_test")
    input_rms_for_grad_data = np.random.rand(batch_s, norm_dim).astype(np.float32) * 5
    input_rms_for_grad = OmegaTensor(input_rms_for_grad_data, requires_grad=True, name="input_for_rms_grad")

    # Zero grads
    rmsnorm_layer_for_grad.weight.zero_grad()

    output_rms_for_grad = rmsnorm_layer_for_grad(input_rms_for_grad)
    dummy_grad_out_rms_data = np.random.randn(*output_rms_for_grad.shape).astype(np.float32)

    print("Running backward pass for RMSNorm layer...")
    try:
        output_rms_for_grad.backward(dummy_grad_out_rms_data)

        weight_grad_rms = rmsnorm_layer_for_grad.weight.grad
        assert weight_grad_rms is not None, "RMSNorm Weight grad should not be None"
        print(f"RMSNorm Weight grad shape: {weight_grad_rms.shape}")
        assert weight_grad_rms.shape == rmsnorm_layer_for_grad.weight.shape, "RMSNorm Weight grad shape mismatch"

        input_grad_rms = input_rms_for_grad.grad
        assert input_grad_rms is not None, "RMSNorm Input grad should not be None"
        print(f"RMSNorm Input grad shape: {input_grad_rms.shape}")
        assert input_grad_rms.shape == input_rms_for_grad.shape, "RMSNorm Input grad shape mismatch"

        print("RMSNorm layer backward pass seems OK (grads exist and have correct shapes).")

    except Exception as e:
        print(f"ERROR during RMSNorm layer backward pass test: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- All Layer Tests Finished (Embedding, Linear & RMSNorm) ---")


    # ===== SiLU Function Tests =====
    print("\n\n--- Testing SiLU Function ---")
    # [Test Case 11: SiLU Forward Pass]
    print("\n[Test Case SiLU Fwd: Forward Pass]")
    silu_input_data = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=np.float32)
    silu_input_tensor = OmegaTensor(silu_input_data, requires_grad=True, name="silu_input")

    silu_output_tensor = silu(silu_input_tensor)
    print(f"SiLU Input: {silu_input_tensor.data}")
    print(f"SiLU Output: {silu_output_tensor.data}")

    # Expected values: x * (1 / (1 + exp(-x)))
    # x=-2: -2 * (1/(1+e^2)) = -2 * (1/(1+7.389)) = -2 * 0.1192 = -0.2384
    # x=-1: -1 * (1/(1+e^1)) = -1 * (1/(1+2.718)) = -1 * 0.2689 = -0.2689
    # x=0:  0 * (1/(1+e^0)) =  0 * 0.5 = 0.0
    # x=1:  1 * (1/(1+e^-1)) = 1 * (1/(1+0.3678)) = 1 * 0.731 = 0.731
    # x=2:  2 * (1/(1+e^-2)) = 2 * (1/(1+0.1353)) = 2 * 0.8808 = 1.7616
    expected_silu_output = np.array([-0.23840584, -0.26894142,  0.        ,  0.73105858,  1.76159416], dtype=np.float32)
    assert np.allclose(silu_output_tensor.data, expected_silu_output, atol=1e-5), "SiLU forward pass output mismatch."
    print("SiLU forward pass seems OK.")

    # [Test Case 12: SiLU Backward Pass]
    print("\n[Test Case SiLU Bwd: Backward Pass]")
    silu_input_tensor.zero_grad() # Clear previous grads if any (though it's a new tensor here)
    dummy_grad_silu_out = OmegaTensor(np.ones_like(silu_output_tensor.data), requires_grad=False)
    try:
        silu_output_tensor.backward(dummy_grad_silu_out.data) # Pass raw data for grad_output
        assert silu_input_tensor.grad is not None, "Gradient for SiLU input should not be None."
        print(f"SiLU Input Grad: {silu_input_tensor.grad}")
        # d(silu(x))/dx = sigmoid(x) * (1 + x * (1 - sigmoid(x)))
        # For x=0, grad = 0.5 * (1 + 0) = 0.5. Our dummy grad_out is 1, so grad should be 0.5.
        assert np.isclose(silu_input_tensor.grad[2], 0.5, atol=1e-5), "SiLU gradient at x=0 mismatch"
        print("SiLU backward pass seems OK.")
    except Exception as e:
        print(f"ERROR during SiLU backward pass test: {e}")
        import traceback
        traceback.print_exc()

    # ===== FeedForward Layer Tests =====
    print("\n\n--- Testing FeedForward Layer ---")
    # [Test Case 13: FeedForward Initialization]
    print("\n[Test Case FF Init: FeedForward Layer Initialization]")
    ff_dim = 10
    ff_hidden_dim = 20 # Example hidden dim
    feedforward_layer = FeedForward(dim=ff_dim, hidden_dim=ff_hidden_dim, name="ff1")

    ff_params = feedforward_layer.parameters()
    print(f"FeedForward params: {[p.name for p in ff_params]}")
    # Expected: w1.weight, w2.weight, w3.weight (bias=False for Linear layers in FF)
    assert len(ff_params) == 3, "FeedForward should have 3 parameters (weights of w1, w2, w3)"
    assert feedforward_layer.w1.weight in ff_params
    assert feedforward_layer.w2.weight in ff_params
    assert feedforward_layer.w3.weight in ff_params
    assert feedforward_layer.w1.weight.shape == (ff_dim, ff_hidden_dim)
    assert feedforward_layer.w2.weight.shape == (ff_hidden_dim, ff_dim)
    assert feedforward_layer.w3.weight.shape == (ff_dim, ff_hidden_dim)
    print("FeedForward layer initialization and parameter registration seems OK.")

    # [Test Case 14: FeedForward Forward Pass]
    print("\n[Test Case FF Fwd: Forward Pass]")
    ff_batch_s, ff_seq_l = 2, 3

    input_ff_2d_data = np.random.rand(ff_batch_s, ff_dim).astype(np.float32)
    input_ff_2d = OmegaTensor(input_ff_2d_data, requires_grad=True, name="ff_input2d")

    input_ff_3d_data = np.random.rand(ff_batch_s, ff_seq_l, ff_dim).astype(np.float32)
    input_ff_3d = OmegaTensor(input_ff_3d_data, requires_grad=True, name="ff_input3d")

    output_ff_2d = feedforward_layer(input_ff_2d)
    print(f"Output FeedForward 2D shape: {output_ff_2d.shape}")
    assert output_ff_2d.shape == (ff_batch_s, ff_dim)

    output_ff_3d = feedforward_layer(input_ff_3d)
    print(f"Output FeedForward 3D shape: {output_ff_3d.shape}")
    assert output_ff_3d.shape == (ff_batch_s, ff_seq_l, ff_dim)
    print("FeedForward forward pass (2D, 3D inputs) seems OK.")

    # [Test Case 15: FeedForward Backward Pass]
    print("\n[Test Case FF Bwd: Backward Pass]")

    # Using 2D input for simplicity
    ff_layer_for_grad = FeedForward(dim=ff_dim, hidden_dim=ff_hidden_dim, name="ff_grad_test")
    input_ff_for_grad_data = np.random.rand(ff_batch_s, ff_dim).astype(np.float32)
    input_ff_for_grad = OmegaTensor(input_ff_for_grad_data, requires_grad=True, name="input_for_ff_grad")

    # Zero grads for all parameters in the FeedForward layer
    for p in ff_layer_for_grad.parameters():
        p.zero_grad()

    output_ff_for_grad = ff_layer_for_grad(input_ff_for_grad)
    dummy_grad_out_ff_data = np.random.randn(*output_ff_for_grad.shape).astype(np.float32)

    print("Running backward pass for FeedForward layer...")
    try:
        output_ff_for_grad.backward(dummy_grad_out_ff_data)

        # Check grads for sub-layer parameters
        assert ff_layer_for_grad.w1.weight.grad is not None, "FF w1.weight grad should not be None"
        assert ff_layer_for_grad.w2.weight.grad is not None, "FF w2.weight grad should not be None"
        assert ff_layer_for_grad.w3.weight.grad is not None, "FF w3.weight grad should not be None"
        print(f"FF w1.weight grad shape: {ff_layer_for_grad.w1.weight.grad.shape}")
        print(f"FF w2.weight grad shape: {ff_layer_for_grad.w2.weight.grad.shape}")
        print(f"FF w3.weight grad shape: {ff_layer_for_grad.w3.weight.grad.shape}")

        input_grad_ff = input_ff_for_grad.grad
        assert input_grad_ff is not None, "FeedForward Input grad should not be None"
        print(f"FeedForward Input grad shape: {input_grad_ff.shape}")
        assert input_grad_ff.shape == input_ff_for_grad.shape, "FeedForward Input grad shape mismatch"

        print("FeedForward layer backward pass seems OK (grads exist for sub-layers and input).")

    except Exception as e:
        print(f"ERROR during FeedForward layer backward pass test: {e}")
        import traceback
        traceback.print_exc()

    print("\n--- All Layer Tests Finished (Embedding, Linear, RMSNorm & FeedForward) ---")


    # ===== Rotary Embedding Helper Tests =====
    print("\n\n--- Testing apply_rotary_emb ---")
    # [Test Case 16: apply_rotary_emb Forward Pass]
    print("\n[Test Case RoPE Fwd: Forward Pass]")
    bsz, seq_len_rope, dim_rope = 1, 2, 4

    x_rope_data = np.arange(bsz * seq_len_rope * dim_rope, dtype=np.float32).reshape(bsz, seq_len_rope, dim_rope)
    # x_rope_data = [[ [0,1,2,3], [4,5,6,7] ]]
    x_rope = OmegaTensor(x_rope_data, requires_grad=True, name="x_rope")

    # freqs_cis: (seq_len, dim)
    # Example: seq_pos 0: (cos(m*theta_0), sin(m*theta_0), cos(m*theta_1), sin(m*theta_1))
    # For 90-deg rotation on all pairs: cos=0, sin=1. So (0,1,0,1)
    freqs_cis_data = np.zeros((seq_len_rope, dim_rope), dtype=np.float32)
    freqs_cis_data[:, 0::2] = 0 # cos components
    freqs_cis_data[:, 1::2] = 1 # sin components
    # freqs_cis_data = [[0,1,0,1], [0,1,0,1]]
    freqs_cis_rope = OmegaTensor(freqs_cis_data, requires_grad=False, name="freqs_cis_rope")

    # x_real = [0,2], [4,6]
    # x_imag = [1,3], [5,7]
    # ocos = 0, osin = 1
    # out_real = x_real * 0 - x_imag * 1 = -x_imag = [-1,-3], [-5,-7]
    # out_imag = x_real * 1 + x_imag * 0 =  x_real = [ 0, 2], [ 4, 6]
    # output interleaved: [[-1,0,-3,2], [-5,4,-7,6]]

    expected_output_data = np.array([[[-1,0,-3,2],[-5,4,-7,6]]], dtype=np.float32)

    output_rope = apply_rotary_emb(x_rope, freqs_cis_rope)
    print(f"Input x for RoPE:\n{x_rope.data}")
    print(f"Input freqs_cis for RoPE:\n{freqs_cis_rope.data}")
    print(f"Output of apply_rotary_emb:\n{output_rope.data}")

    assert output_rope.shape == x_rope.shape, f"RoPE output shape mismatch. Expected {x_rope.shape}, Got {output_rope.shape}"
    assert np.allclose(output_rope.data, expected_output_data, atol=1e-6), "RoPE forward pass output mismatch."
    print("apply_rotary_emb forward pass seems OK.")

    # [Test Case 17: apply_rotary_emb Backward Pass Autograd Check]
    print("\n[Test Case RoPE Bwd: Backward Pass Autograd Check]")
    x_rope.zero_grad()
    # It's important that freqs_cis_rope does not require grad.
    assert freqs_cis_rope.requires_grad is False, "freqs_cis should not require grad for this test."

    # Recompute output for a clean graph if necessary, though OmegaTensor ops build graph on the fly
    output_rope_for_grad = apply_rotary_emb(x_rope, freqs_cis_rope)

    # Create a simple scalar loss
    loss_rope = output_rope_for_grad.sum()
    loss_rope.name = "loss_rope"
    print(f"RoPE test loss: {loss_rope.data}")

    try:
        loss_rope.backward() # Default grad_output for scalar is 1.0

        if x_rope.grad is not None:
            print(f"Gradient for x_rope (shape {x_rope.grad.shape}):\n{x_rope.grad}")
            # With RotaryEmbeddingOp, the gradient should now be correctly computed.
            # The numerical correctness is tested in OmegaTensor.py's RotaryEmbeddingOp test.
            # Here, we primarily verify that the gradient is populated.
            print("apply_rotary_emb backward pass: Gradients were populated for x_rope using RotaryEmbeddingOp.")
            # Verify against expected gradient for the 90-degree rotation case and sum loss (grad_out=1 for all elements)
            # From OmegaTensor.py test: grad_x_real=1, grad_x_imag=-1
            expected_grad_x_rope_data = np.empty_like(x_rope.data)
            expected_grad_x_rope_data[..., 0::2] = 1.0  # grad for real parts
            expected_grad_x_rope_data[..., 1::2] = -1.0 # grad for imag parts
            # This expected grad is if the grad_output for apply_rotary_emb was all ones.
            # Since loss is sum(), d(loss)/d(output_rope_for_grad_element) = 1.
            # So, the grad flowing into RotaryEmbeddingOp's backward is indeed all ones.
            assert np.allclose(x_rope.grad, expected_grad_x_rope_data, atol=1e-6), \
                f"RoPE backward pass gradient mismatch. Expected:\n{expected_grad_x_rope_data}\nGot:\n{x_rope.grad}"
            print("apply_rotary_emb backward pass gradient values verified against expected for 90-deg rotation.")
        else:
            # This case should ideally not be reached if RotaryEmbeddingOp works.
            print("apply_rotary_emb backward pass: x_rope.grad is None. Autograd link is broken.")
            assert False, "x_rope.grad is None. RotaryEmbeddingOp did not propagate gradients."

    except Exception as e:
        print(f"ERROR during apply_rotary_emb backward pass test: {e}")
        import traceback
        traceback.print_exc()
        # If an error occurs, it might be due to graph inconsistencies or ops not handling inputs.
        # For this specific implementation, error might occur if intermediate tensors (x_real, etc.)
        # are not correctly participating in graph for sum() or other ops.

    print("\n--- All Layer Tests Finished (Embedding, Linear, RMSNorm, FeedForward & RoPE) ---")


    # ===== repeat_kv Function Tests =====
    print("\n\n--- Testing repeat_kv Function ---")
    # [Test Case 18: repeat_kv n_rep=1]
    print("\n[Test Case repeat_kv n_rep=1: Forward Pass]")
    bsz_kv, n_kv_heads_kv, seq_len_kv, head_dim_kv = 1, 2, 3, 4
    x_kv_data_n1 = np.random.rand(bsz_kv, n_kv_heads_kv, seq_len_kv, head_dim_kv).astype(np.float32)
    x_kv_n1 = OmegaTensor(x_kv_data_n1, requires_grad=True, name="x_kv_n1")

    output_kv_n1 = repeat_kv(x_kv_n1, 1)
    assert output_kv_n1 is x_kv_n1, "repeat_kv with n_rep=1 should return the original tensor."
    print("repeat_kv with n_rep=1 seems OK.")

    # [Test Case 19: repeat_kv n_rep > 1 Forward Pass]
    print("\n[Test Case repeat_kv n_rep>1 Fwd: Forward Pass]")
    n_rep_kv = 2
    x_kv_data_n_rep = np.arange(bsz_kv * n_kv_heads_kv * seq_len_kv * head_dim_kv, dtype=np.float32).reshape(bsz_kv, n_kv_heads_kv, seq_len_kv, head_dim_kv)
    # Example: x_kv_data_n_rep has shape (1,2,3,4)
    # Head 0: [[[ 0,  1,  2,  3], [ 4,  5,  6,  7], [ 8,  9, 10, 11]]]
    # Head 1: [[[12, 13, 14, 15], [16, 17, 18, 19], [20, 21, 22, 23]]]
    x_kv_n_rep = OmegaTensor(x_kv_data_n_rep, requires_grad=True, name="x_kv_n_rep")

    output_kv_n_rep = repeat_kv(x_kv_n_rep, n_rep_kv)
    expected_shape = (bsz_kv, n_kv_heads_kv * n_rep_kv, seq_len_kv, head_dim_kv)
    print(f"Output repeat_kv shape: {output_kv_n_rep.shape}, Expected: {expected_shape}")
    assert output_kv_n_rep.shape == expected_shape, "repeat_kv output shape mismatch."

    # Verify data repetition
    # Expected: output[:, 0, :, :] == x[:, 0, :, :]
    #           output[:, 1, :, :] == x[:, 0, :, :] (repeated)
    #           output[:, 2, :, :] == x[:, 1, :, :]
    #           output[:, 3, :, :] == x[:, 1, :, :] (repeated)
    correct_repetition = True
    for i in range(n_kv_heads_kv):
        for j in range(n_rep_kv):
            output_slice = output_kv_n_rep.data[:, i * n_rep_kv + j, :, :]
            original_slice = x_kv_data_n_rep[:, i, :, :]
            if not np.allclose(output_slice, original_slice):
                correct_repetition = False
                print(f"Data mismatch at n_kv_head {i}, repetition {j}")
                break
        if not correct_repetition:
            break
    assert correct_repetition, "repeat_kv data repetition error."
    print("repeat_kv with n_rep>1 forward pass data and shape seem OK.")

    # [Test Case 20: repeat_kv n_rep > 1 Backward Pass]
    print("\n[Test Case repeat_kv n_rep>1 Bwd: Backward Pass]")
    x_kv_n_rep.zero_grad() # Zero gradient from previous tests if any (though it's a new tensor)

    # Recompute for clean graph for this specific backward test
    output_for_grad_kv = repeat_kv(x_kv_n_rep, n_rep_kv)

    dummy_grad_output_kv = np.ones_like(output_for_grad_kv.data)
    output_for_grad_kv.backward(dummy_grad_output_kv)

    assert x_kv_n_rep.grad is not None, "Gradient for repeat_kv input should not be None."
    assert x_kv_n_rep.grad.shape == x_kv_n_rep.shape, "Gradient shape mismatch for repeat_kv input."

    # Expected gradient: sum of gradients from all repetitions.
    # Since dummy_grad_output_kv is all ones, each element of x_kv_n_rep.grad should be n_rep_kv.
    expected_grad_kv = np.full_like(x_kv_n_rep.data, float(n_rep_kv))
    assert np.allclose(x_kv_n_rep.grad, expected_grad_kv), "repeat_kv backward pass gradient value mismatch."
    print(f"repeat_kv input grad (first element): {x_kv_n_rep.grad.flatten()[0]}, Expected: {float(n_rep_kv)}")
    print("repeat_kv backward pass seems OK.")

    print("\n--- All Layer Tests Finished (Embedding, Linear, RMSNorm, FeedForward, RoPE & repeat_kv) ---")


    # ===== Attention Layer Tests =====
    print("\n\n--- Testing Attention Layer ---")
    # [Test Case 21: Attention Layer Initialization]
    print("\n[Test Case Attn Init: Initialization]")
    attn_dim, attn_n_heads, attn_n_kv_heads, attn_head_dim = 32, 4, 2, 8 # dim = n_heads * head_dim if n_heads == n_kv_heads
                                                                        # Here, dim for q, k, v linear layers input
    # For this test, ensure dim = n_heads * head_dim for wo output to match input dim for residual connection
    # So, wo input is n_heads * head_dim = 4 * 8 = 32. wo output is dim=32.
    # wq input is dim=32, output is n_heads*head_dim = 32
    # wk input is dim=32, output is n_kv_heads*head_dim = 2*8 = 16
    # wv input is dim=32, output is n_kv_heads*head_dim = 16

    attention_layer = Attention(
        dim=attn_dim,
        n_heads=attn_n_heads,
        n_kv_heads=attn_n_kv_heads,
        head_dim=attn_head_dim,
        name="attn1"
    )

    attn_params = attention_layer.parameters()
    print(f"Attention params: {[p.name for p in attn_params]}")
    # Expected: wq.weight, wk.weight, wv.weight, wo.weight (bias=False for Linear layers)
    assert len(attn_params) == 4, "Attention layer should have 4 parameters (weights of wq, wk, wv, wo)"
    assert attention_layer.wq.weight in attn_params
    assert attention_layer.wk.weight in attn_params
    assert attention_layer.wv.weight in attn_params
    assert attention_layer.wo.weight in attn_params
    print("Attention layer initialization and parameter registration seems OK.")

    # [Test Case 22: Attention Forward Pass - MHA (n_kv_heads = n_heads)]
    print("\n[Test Case Attn Fwd MHA: Forward Pass MHA]")
    mha_n_heads = 4
    mha_n_kv_heads = 4 # MHA case
    mha_head_dim = 8
    mha_dim = mha_n_heads * mha_head_dim # 32

    mha_layer = Attention(dim=mha_dim, n_heads=mha_n_heads, n_kv_heads=mha_n_kv_heads, head_dim=mha_head_dim, name="mha")

    bsz_attn, seqlen_attn = 1, 5
    x_attn_data = np.random.rand(bsz_attn, seqlen_attn, mha_dim).astype(np.float32)
    x_attn = OmegaTensor(x_attn_data, requires_grad=True, name="x_attn_mha")

    freqs_cis_attn_data = np.random.rand(seqlen_attn, mha_head_dim).astype(np.float32) # RoPE freqs for head_dim
    freqs_cis_attn = OmegaTensor(freqs_cis_attn_data, requires_grad=False, name="freqs_cis_attn")

    mask_attn = None # No mask for this simple test

    output_mha = mha_layer(x_attn, freqs_cis_attn, mask_attn)
    print(f"Output MHA shape: {output_mha.shape}, Expected: {(bsz_attn, seqlen_attn, mha_dim)}")
    assert output_mha.shape == (bsz_attn, seqlen_attn, mha_dim), "MHA output shape mismatch."
    print("Attention MHA forward pass shape seems OK.")

    # [Test Case 23: Attention Forward Pass - GQA (n_kv_heads < n_heads)]
    print("\n[Test Case Attn Fwd GQA: Forward Pass GQA]")
    gqa_n_heads = 4
    gqa_n_kv_heads = 2 # GQA case
    gqa_head_dim = 8
    gqa_dim = gqa_n_heads * gqa_head_dim # 32 (wo input)
                                         # For wq, wk, wv input_dim is also gqa_dim

    gqa_layer = Attention(dim=gqa_dim, n_heads=gqa_n_heads, n_kv_heads=gqa_n_kv_heads, head_dim=gqa_head_dim, name="gqa")

    x_gqa_data = np.random.rand(bsz_attn, seqlen_attn, gqa_dim).astype(np.float32)
    x_gqa = OmegaTensor(x_gqa_data, requires_grad=True, name="x_attn_gqa")

    # freqs_cis data needs to match head_dim for RoPE application on xq, xk
    freqs_cis_gqa_data = np.random.rand(seqlen_attn, gqa_head_dim).astype(np.float32)
    freqs_cis_gqa = OmegaTensor(freqs_cis_gqa_data, requires_grad=False, name="freqs_cis_gqa")

    output_gqa = gqa_layer(x_gqa, freqs_cis_gqa, mask_attn)
    print(f"Output GQA shape: {output_gqa.shape}, Expected: {(bsz_attn, seqlen_attn, gqa_dim)}")
    assert output_gqa.shape == (bsz_attn, seqlen_attn, gqa_dim), "GQA output shape mismatch."
    print("Attention GQA forward pass shape seems OK.")

    # [Test Case 24: Attention Forward Pass - With Mask]
    print("\n[Test Case Attn Fwd Mask: Forward Pass with Mask]")
    # Using MHA setup for simplicity
    mask_data = np.triu(np.full((seqlen_attn, seqlen_attn), -np.inf, dtype=np.float32), k=1)
    # mask_data for seqlen=3: [[0, -inf, -inf], [0,  0, -inf], [0,  0,  0]]
    # This needs to be broadcastable to (bsz, n_heads, seqlen, seqlen)
    # So, mask_omega should be (1, 1, seqlen, seqlen) or similar.
    # Or, if the AddOp handles (seqlen,seqlen) + (bsz,n_heads,seqlen,seqlen), that's also fine.
    # Let's make it (1,1,seqlen,seqlen)
    mask_omega = OmegaTensor(mask_data.reshape(1, 1, seqlen_attn, seqlen_attn), requires_grad=False)

    output_mha_masked = mha_layer(x_attn, freqs_cis_attn, mask_omega)
    print(f"Output MHA with mask shape: {output_mha_masked.shape}")
    assert output_mha_masked.shape == (bsz_attn, seqlen_attn, mha_dim), "MHA with mask output shape mismatch."
    # A deeper check would involve inspecting attn_weights inside the call, which is harder here.
    # For now, ensuring it runs and shape is correct is the main goal.
    print("Attention MHA with mask forward pass runs and shape is OK.")


    # [Test Case 25: Attention Backward Pass]
    print("\n[Test Case Attn Bwd: Backward Pass]")
    # Using GQA layer for a more comprehensive test
    x_gqa.zero_grad() # Clear previous grads
    for p in gqa_layer.parameters(): p.zero_grad()

    # Recompute output for a clean graph
    output_gqa_for_grad = gqa_layer(x_gqa, freqs_cis_gqa, mask_attn) # mask_attn is None here

    dummy_grad_attn_output = np.random.rand(*output_gqa_for_grad.shape).astype(np.float32)
    output_gqa_for_grad.backward(dummy_grad_attn_output)

    # Check gradients for sub-layer parameters
    assert gqa_layer.wq.weight.grad is not None, "Attention wq.weight grad should not be None"
    assert gqa_layer.wk.weight.grad is not None, "Attention wk.weight grad should not be None"
    assert gqa_layer.wv.weight.grad is not None, "Attention wv.weight grad should not be None"
    assert gqa_layer.wo.weight.grad is not None, "Attention wo.weight grad should not be None"
    print("Gradients for all attention sub-layer weights are populated.")

    assert x_gqa.grad is not None, "Attention input x_gqa.grad should not be None"
    print(f"Attention input x_gqa grad shape: {x_gqa.grad.shape}")
    assert x_gqa.grad.shape == x_gqa.shape, "Attention input x_gqa grad shape mismatch."
    print("Attention backward pass seems OK (grads exist for sub-layers and input).")

    print("\n--- All Layer Tests Finished (Embedding, Linear, RMSNorm, FeedForward, RoPE, repeat_kv & Attention) ---")


    # ===== Attention Layer Tests =====
    print("\n\n--- Testing Attention Layer ---")
    # [Test Case 21: Attention Layer Initialization]
    print("\n[Test Case Attn Init: Initialization]")
    attn_args = SimpleModelArgs(dim=32, n_heads=4, n_kv_heads=2, head_dim=8, ffn_hidden_dim=64, norm_eps=1e-5)
    # dim = n_heads * head_dim if output projection is to recover original dim.
    # Here, input dim = 32. n_heads=4, head_dim=8 => 4*8=32 for Wq and Wo.
    # n_kv_heads=2, head_dim=8 => 2*8=16 for Wk and Wv.

    attention_layer = Attention(
        dim=attn_args.dim,
        n_heads=attn_args.n_heads,
        n_kv_heads=attn_args.n_kv_heads,
        head_dim=attn_args.head_dim,
        name="attn1"
    )

    attn_params = attention_layer.parameters()
    print(f"Attention params: {[p.name for p in attn_params]}")
    assert len(attn_params) == 4, "Attention layer should have 4 parameters (weights of wq, wk, wv, wo)"
    assert attention_layer.wq.weight in attn_params
    assert attention_layer.wk.weight in attn_params
    assert attention_layer.wv.weight in attn_params
    assert attention_layer.wo.weight in attn_params
    print("Attention layer initialization and parameter registration seems OK.")

    # [Test Case 22: Attention Forward Pass - MHA (n_kv_heads = n_heads)]
    print("\n[Test Case Attn Fwd MHA: Forward Pass MHA]")
    mha_args = SimpleModelArgs(dim=32, n_heads=4, n_kv_heads=4, head_dim=8, ffn_hidden_dim=64, norm_eps=1e-5)
    mha_layer = Attention(dim=mha_args.dim, n_heads=mha_args.n_heads, n_kv_heads=mha_args.n_kv_heads, head_dim=mha_args.head_dim, name="mha")

    bsz_attn, seqlen_attn = 1, 5
    x_attn_data = np.random.rand(bsz_attn, seqlen_attn, mha_args.dim).astype(np.float32)
    x_attn = OmegaTensor(x_attn_data, requires_grad=True, name="x_attn_mha")

    freqs_cis_attn_data = np.random.rand(seqlen_attn, mha_args.head_dim).astype(np.float32)
    freqs_cis_attn = OmegaTensor(freqs_cis_attn_data, requires_grad=False, name="freqs_cis_attn")
    mask_attn = None

    output_mha = mha_layer(x_attn, freqs_cis_attn, mask_attn)
    print(f"Output MHA shape: {output_mha.shape}, Expected: {(bsz_attn, seqlen_attn, mha_args.dim)}")
    assert output_mha.shape == (bsz_attn, seqlen_attn, mha_args.dim), "MHA output shape mismatch."
    print("Attention MHA forward pass shape seems OK.")

    # [Test Case 23: Attention Forward Pass - GQA (n_kv_heads < n_heads)]
    print("\n[Test Case Attn Fwd GQA: Forward Pass GQA]")
    gqa_args = SimpleModelArgs(dim=32, n_heads=4, n_kv_heads=2, head_dim=8, ffn_hidden_dim=64, norm_eps=1e-5)
    gqa_layer = Attention(dim=gqa_args.dim, n_heads=gqa_args.n_heads, n_kv_heads=gqa_args.n_kv_heads, head_dim=gqa_args.head_dim, name="gqa")

    x_gqa_data = np.random.rand(bsz_attn, seqlen_attn, gqa_args.dim).astype(np.float32)
    x_gqa = OmegaTensor(x_gqa_data, requires_grad=True, name="x_attn_gqa")
    freqs_cis_gqa_data = np.random.rand(seqlen_attn, gqa_args.head_dim).astype(np.float32)
    freqs_cis_gqa = OmegaTensor(freqs_cis_gqa_data, requires_grad=False, name="freqs_cis_gqa")

    output_gqa = gqa_layer(x_gqa, freqs_cis_gqa, mask_attn) # mask_attn is None
    print(f"Output GQA shape: {output_gqa.shape}, Expected: {(bsz_attn, seqlen_attn, gqa_args.dim)}")
    assert output_gqa.shape == (bsz_attn, seqlen_attn, gqa_args.dim), "GQA output shape mismatch."
    print("Attention GQA forward pass shape seems OK.")

    # [Test Case 24: Attention Forward Pass - With Mask]
    print("\n[Test Case Attn Fwd Mask: Forward Pass with Mask]")
    mask_data = np.triu(np.full((seqlen_attn, seqlen_attn), -1e9, dtype=np.float32), k=1) # Using large negative for mask
    mask_omega = OmegaTensor(mask_data.reshape(1, 1, seqlen_attn, seqlen_attn), requires_grad=False)

    output_mha_masked = mha_layer(x_attn, freqs_cis_attn, mask_omega) # Using mha_layer
    print(f"Output MHA with mask shape: {output_mha_masked.shape}")
    assert output_mha_masked.shape == (bsz_attn, seqlen_attn, mha_args.dim), "MHA with mask output shape mismatch."
    print("Attention MHA with mask forward pass runs and shape is OK.")

    # [Test Case 25: Attention Backward Pass]
    print("\n[Test Case Attn Bwd: Backward Pass]")
    x_gqa.zero_grad()
    for p in gqa_layer.parameters(): p.zero_grad()
    output_gqa_for_grad = gqa_layer(x_gqa, freqs_cis_gqa, None)
    dummy_grad_attn_output = np.random.rand(*output_gqa_for_grad.shape).astype(np.float32)
    output_gqa_for_grad.backward(dummy_grad_attn_output)

    for name, sub_layer in [("wq",gqa_layer.wq), ("wk",gqa_layer.wk), ("wv",gqa_layer.wv), ("wo",gqa_layer.wo)]:
        assert sub_layer.weight.grad is not None, f"Attention {name}.weight grad should not be None"
    print("Gradients for all attention sub-layer weights are populated.")
    assert x_gqa.grad is not None, "Attention input x_gqa.grad should not be None"
    assert x_gqa.grad.shape == x_gqa.shape, "Attention input x_gqa grad shape mismatch."
    print("Attention backward pass seems OK.")

    # ===== TransformerBlock Tests =====
    print("\n\n--- Testing TransformerBlock ---")
    # [Test Case 26: TransformerBlock Initialization]
    print("\n[Test Case TxB Init: Initialization]")
    tb_args = SimpleModelArgs(dim=32, n_heads=4, n_kv_heads=2, head_dim=8, ffn_hidden_dim=64, norm_eps=1e-5)
    transformer_block = TransformerBlock(layer_id=0, args=tb_args, name="tx_block_")

    tb_params = transformer_block.parameters()
    # Expected: attn_norm.weight, attention.wq.weight, wk.weight, wv.weight, wo.weight,
    #           ffn_norm.weight, feed_forward.w1.weight, w2.weight, w3.weight
    # Total: 2 for RMSNorms + 4 for Attention + 3 for FeedForward = 9 parameters
    print(f"TransformerBlock params ({len(tb_params)}): {[p.name for p in tb_params]}")
    assert len(tb_params) == 9, "TransformerBlock parameter count mismatch."
    assert transformer_block.attention_norm.weight in tb_params
    assert transformer_block.ffn_norm.weight in tb_params
    assert transformer_block.attention.wq.weight in tb_params # Example check
    assert transformer_block.feed_forward.w1.weight in tb_params # Example check
    print("TransformerBlock initialization and parameter registration seems OK.")

    # [Test Case 27: TransformerBlock Forward Pass]
    print("\n[Test Case TxB Fwd: Forward Pass]")
    x_tb_data = np.random.rand(bsz_attn, seqlen_attn, tb_args.dim).astype(np.float32)
    x_tb = OmegaTensor(x_tb_data, requires_grad=True, name="x_tb")
    freqs_cis_tb_data = np.random.rand(seqlen_attn, tb_args.head_dim).astype(np.float32)
    freqs_cis_tb = OmegaTensor(freqs_cis_tb_data, requires_grad=False, name="freqs_cis_tb")
    mask_tb = None # Using mha_layer's mask_omega for causal mask test if needed later

    output_tb = transformer_block(x_tb, freqs_cis_tb, mask_tb)
    print(f"Output TransformerBlock shape: {output_tb.shape}, Expected: {x_tb.shape}")
    assert output_tb.shape == x_tb.shape, "TransformerBlock output shape mismatch."
    print("TransformerBlock forward pass shape seems OK.")

    # [Test Case 28: TransformerBlock Backward Pass]
    print("\n[Test Case TxB Bwd: Backward Pass]")
    x_tb.zero_grad()
    for p in transformer_block.parameters(): p.zero_grad()

    output_tb_for_grad = transformer_block(x_tb, freqs_cis_tb, mask_tb)
    dummy_grad_tb_output = np.random.rand(*output_tb_for_grad.shape).astype(np.float32)
    output_tb_for_grad.backward(dummy_grad_tb_output)

    all_params_have_grad = True
    for p in transformer_block.parameters():
        if p.grad is None:
            all_params_have_grad = False
            print(f"ERROR: Parameter {p.name} in TransformerBlock has no grad.")
            break
    assert all_params_have_grad, "Not all parameters in TransformerBlock received gradients."
    print("Gradients for all TransformerBlock sub-layer parameters are populated.")

    assert x_tb.grad is not None, "TransformerBlock input x_tb.grad should not be None"
    print(f"TransformerBlock input x_tb grad shape: {x_tb.grad.shape}")
    assert x_tb.grad.shape == x_tb.shape, "TransformerBlock input x_tb grad shape mismatch."
    print("TransformerBlock backward pass seems OK.")


    print("\n--- All Layer Tests Finished (Embedding, Linear, RMSNorm, FeedForward, RoPE, repeat_kv, Attention & TransformerBlock) ---")


    # ===== TransformerOmega Model Tests =====
    print("\n\n--- Testing TransformerOmega Model ---")
    # [Test Case 29: TransformerOmega Initialization]
    print("\n[Test Case Model Init: Initialization]")
    model_args = SimpleModelArgs(
        dim=32, n_layers=2, n_heads=4, n_kv_heads=2, vocab_size=50,
        ffn_hidden_dim=64, max_seq_len=20, norm_eps=1e-5, rope_theta=1000.0 # smaller theta for test stability if any
    )
    transformer_model = TransformerOmega(args=model_args)

    model_params = transformer_model.parameters()
    # Expected params:
    # tok_emb.weight (1)
    # N_LAYERS * (
    #   attn_norm.weight (1)
    #   attention.wq.weight (1)
    #   attention.wk.weight (1)
    #   attention.wv.weight (1)
    #   attention.wo.weight (1)
    #   ffn_norm.weight (1)
    #   feed_forward.w1.weight (1)
    #   feed_forward.w2.weight (1)
    #   feed_forward.w3.weight (1)
    # ) = N_LAYERS * 9
    # norm.weight (1)
    # output.weight (1)
    # Total = 1 + (N_LAYERS * 9) + 1 + 1
    expected_param_count = 1 + (model_args.n_layers * 9) + 1 + 1
    print(f"TransformerOmega params ({len(model_params)}): {[p.name for p in model_params if 'block0' in p.name or 'tok_emb' in p.name][:5]}...") # Print a few
    assert len(model_params) == expected_param_count, f"TransformerOmega parameter count mismatch. Expected {expected_param_count}, Got {len(model_params)}"
    assert transformer_model.tok_embeddings.embedding_default_name_weight in model_params # Check specific sub-layer param
    assert transformer_model.layers[0].attention.wq.weight in model_params
    assert transformer_model.output.weight in model_params
    print(f"TransformerOmega precomputed freqs_cis shape: {transformer_model.freqs_cis.shape}")
    assert transformer_model.freqs_cis.shape == (model_args.max_seq_len * 2, model_args.head_dim)
    print("TransformerOmega initialization and parameter registration seems OK.")

    # [Test Case 30: TransformerOmega Forward Pass]
    print("\n[Test Case Model Fwd: Forward Pass]")
    test_bsz, test_seqlen = 1, 5 # Keep seqlen <= max_seq_len
    dummy_tokens_data = np.random.randint(0, model_args.vocab_size, size=(test_bsz, test_seqlen))
    dummy_tokens = OmegaTensor(dummy_tokens_data, name="dummy_tokens")

    # Causal mask for testing (optional, but good for attention)
    # (bsz, n_heads, seqlen, seqlen) or (1,1,seqlen,seqlen)
    causal_mask_data = np.triu(np.full((test_seqlen, test_seqlen), -1e9, dtype=np.float32), k=1)
    causal_mask = OmegaTensor(causal_mask_data.reshape(1,1,test_seqlen,test_seqlen), requires_grad=False)

    logits = transformer_model(dummy_tokens, mask=causal_mask)
    expected_logits_shape = (test_bsz, test_seqlen, model_args.vocab_size)
    print(f"Output logits shape: {logits.shape}, Expected: {expected_logits_shape}")
    assert logits.shape == expected_logits_shape, "TransformerOmega output logits shape mismatch."
    print("TransformerOmega forward pass shape seems OK.")

    # [Test Case 31: TransformerOmega Backward Pass]
    print("\n[Test Case Model Bwd: Backward Pass]")
    # Zero grads for all parameters
    for p in transformer_model.parameters():
        p.zero_grad()

    # Recompute for a clean graph
    # Note: dummy_tokens don't require grad, so no grad will flow to them.
    # If we wanted to check grad w.r.t. embeddings, we'd need requires_grad on token_embeddings output.
    # Here, we are primarily checking if all model weights receive gradients.
    logits_for_grad = transformer_model(dummy_tokens, mask=causal_mask)

    # Simple sum loss
    loss = logits_for_grad.sum()
    loss.name = "model_loss"
    print(f"Model test loss: {loss.data}")

    loss.backward()

    # Check a few key parameter gradients
    # (tok_embeddings is tricky as input is indices, grad may not be directly checked on weight like this
    # unless specific indices were chosen to ensure all weights are hit by the dummy grad.
    # For now, just check existence for weights that are certainly used.)
    # Let's check a weight from each major component.
    assert transformer_model.tok_embeddings.embedding_default_name_weight.grad is not None, "tok_embeddings.weight grad is None."
    print("tok_embeddings.weight grad is populated.")

    assert transformer_model.layers[0].attention.wq.weight.grad is not None, "block0.attention.wq.weight grad is None."
    print("block0.attention.wq.weight grad is populated.")

    assert transformer_model.layers[0].feed_forward.w1.weight.grad is not None, "block0.feed_forward.w1.weight grad is None."
    print("block0.feed_forward.w1.weight grad is populated.")

    assert transformer_model.norm.weight.grad is not None, "model.norm.weight grad is None."
    print("model.norm.weight grad is populated.")

    assert transformer_model.output.weight.grad is not None, "model.output.weight grad is None."
    print("model.output.weight grad is populated.")

    # Check if all parameters received a grad (optional, but good)
    all_model_params_have_grad = True
    for p_model in transformer_model.parameters():
        if p_model.grad is None:
            all_model_params_have_grad = False
            print(f"ERROR: Model Parameter {p_model.name} has no grad.")
            break
    assert all_model_params_have_grad, "Not all parameters in TransformerOmega received gradients."
    print("All registered parameters in TransformerOmega received gradients.")
    print("TransformerOmega backward pass seems OK.")

    print("\n--- All Layer & Model Tests Finished ---")

# Ensure OpRegistry is accessible if used directly.
# from OmegaTensor import OpRegistry is one way.
# Another is to pass it around or have a global accessor.
# For now, the tensor method `indices_omega.embedding(self.weight)` is preferred.
# And EmbeddingOp handles integer casting of indices.data.
# The OmegaTensor class's _ensure_tensor now defaults to requires_grad=False,
# which is good for indices that are constants.
# The `OmegaTensor.embedding` method was added in the previous step.
# The line `out.set_creator(self, weight_tensor, indices_tensor)` in EmbeddingOp
# ensures that the graph is built correctly.
# The `OmegaLayer` provides a basic structure for parameter management.
# The name of the weight tensor in Embedding is `f"{name}_weight"`, so it's e.g. "embedding_weight".
# Accessing it via `self.embedding_weight` is possible due to `setattr` in `_register_parameter`.
# The `parameters()` method in `OmegaLayer` now correctly iterates `_parameters.items()`.
# The test code in `if __name__ == '__main__':` helps verify functionality.
# The `EmbeddingOp` in `OmegaTensor.py` must correctly cast indices.data to an integer type if it's not already.
# The current `EmbeddingOp` has: `indices_data = indices_data.astype(np.intp)`
# So this should be fine.
# The `OmegaTensor` constructor itself does: `data = np.array(data, dtype=np.float32)`
# So, when `OmegaTensor(indices_list)` is called, `indices_list` becomes float32.
# This is why the cast within `EmbeddingOp` is critical.
# `indices_omega = OmegaTensor(indices, requires_grad=False, name="embedding_indices")` is correct
# for creating the indices tensor if it's not one already.
# The method call `indices_omega.embedding(getattr(self, weight_param_name))` is the correct way.
# `weight_param_name` lookup is a bit clunky; could be `self.weight` if `_register_parameter` sets `self.weight` directly.
# Let's refine `_register_parameter` to set `self.name_of_parameter` (e.g. `self.weight`)
# and also store it in `self._parameters` perhaps with its original name for clarity.
# Current `_register_parameter` sets `setattr(self, name, tensor)`. So if `name` is "embedding_weight",
# it's accessible as `self.embedding_weight`. This is fine.
# The `weight_param_name` lookup `[name for name in self._parameters.keys() if name.endswith("_weight")][0]`
# is a bit fragile if there could be multiple weights.
# It's better to have a fixed attribute name like `self.weight`.
# I will adjust the `Embedding` layer to use `self.weight` directly.
# So `_register_parameter("weight", ...)` and then use `self.weight`.
# This simplifies access.
#
# Final check on `OmegaTensor.embedding` method signature:
# The prompt for *this* subtask (llama_layers_omega.py) states:
# "The report implies the method on OmegaTensor is indices_tensor.embedding(weights_tensor), so it's indices.embedding(self.weight)."
# And the previous report (for OmegaTensor.py modification) stated:
# "Added OmegaTensor.embedding method: def embedding(self, weights_tensor): return OpRegistry['embedding'](weights_tensor, self)"
# This means that `self` in `OmegaTensor.embedding` is the `indices_tensor`, and `weights_tensor` is the argument.
# So `indices_omega.embedding(self.weight)` is indeed the correct usage.
#
# The `OmegaLayer.parameters()` method was updated to be more robust.
# The `Embedding.parameters()` can just call `super().parameters()` if `_register_parameter` is used.
#
# The test script includes a backward pass test, which is good.
# It verifies gradient accumulation for repeated indices.
# `weight_param.grad[2].sum() == 2 * embed_dim` is a good check.
# (Each element of the embedding vector for index 2 receives a gradient of 1.0 from the dummy_grad_output.
# Since index 2 is repeated, it receives this twice. So the sum of gradients for that row should be 2 * embedding_dim).
# This assumes `dummy_grad_output` is all ones.
# `np.add.at` handles this accumulation correctly.
#
# Looks good.Okay, I've reviewed the plan and the considerations. I'll now create the `llama_layers_omega.py` file with the `OmegaLayer` and `Embedding` class definitions. I'll ensure `Embedding` uses `self.weight` for clarity and that the parameter registration and retrieval are straightforward.

Here's the code I'll be writing to the file:
