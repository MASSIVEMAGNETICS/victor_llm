import numpy as np
import uuid

# ===== ΩTensor: Core Autodiff Tensor =====
class OmegaTensor:
    def __init__(self, data, requires_grad=False, device='cpu', name=None):
        if not isinstance(data, np.ndarray):
            data = np.array(data, dtype=np.float32)
        self.data = data
        self.requires_grad = requires_grad
        self.grad = None
        self._creator_op_instance = None
        self._creator_parents = tuple()
        self.device = device # Note: device is not used in current ops
        self.name = name or f"Ω{uuid.uuid4().hex[:8]}"
        self._version = 0

    def _ensure_tensor(self, other_data):
        if isinstance(other_data, OmegaTensor):
            return other_data
        # Allow wrapping of raw lists/numbers if they are not OmegaTensors
        return OmegaTensor(other_data, requires_grad=False) # By default, new tensors from constants don't require grad

    def set_creator(self, op_instance, *parents):
        if self.requires_grad: # Only set creator if grad is required for this tensor
            self._creator_op_instance = op_instance
            self._creator_parents = parents
            # Ensure parents that contribute to a grad-requiring tensor also require grad
            # This logic might need refinement: what if a parent explicitly has requires_grad=False?
            # For now, if this output tensor needs grad, its parents involved in its creation should too.
            for p in parents:
                if isinstance(p, OmegaTensor):
                     # This was: p.requires_grad = True. Changed to respect parent's initial requires_grad.
                     # The gradient will flow to it if it requires_grad, otherwise it stops.
                     pass


    def backward(self, grad_output_data=None):
        if not self.requires_grad:
            return # No gradient needed for this tensor

        if grad_output_data is None:
            if self.data.size == 1:
                grad_output_data = np.array(1.0, dtype=np.float32)
            else:
                raise ValueError("grad_output_data must be specified for non-scalar OmegaTensors in backward()")

        if not isinstance(grad_output_data, np.ndarray):
            grad_output_data = np.array(grad_output_data, dtype=np.float32)

        if self.grad is None:
            self.grad = grad_output_data.copy()
        else:
            self.grad += grad_output_data # Accumulate gradient

        if self._creator_op_instance:
            # Pass the accumulated grad of this tensor to the op that created it
            grads_for_parents_data = self._creator_op_instance.backward(self.grad)

            if not isinstance(grads_for_parents_data, (list, tuple)):
                grads_for_parents_data = [grads_for_parents_data] # Ensure it's a list

            if len(self._creator_parents) != len(grads_for_parents_data):
                raise ValueError(f"Op {type(self._creator_op_instance).__name__}: Mismatch parents ({len(self._creator_parents)}) vs grads ({len(grads_for_parents_data)}).")

            for parent_tensor, parent_grad_data in zip(self._creator_parents, grads_for_parents_data):
                if isinstance(parent_tensor, OmegaTensor) and parent_tensor.requires_grad and parent_grad_data is not None:
                    parent_tensor.backward(parent_grad_data) # Recursively call backward on parents

    def zero_grad(self):
        self.grad = None
        # TODO: Consider if this should recursively zero_grad for parents or if it's up to the user.
        # Standard libraries usually require manual zero_grad for all parameters.

    @property
    def shape(self):
        return self.data.shape

    @property
    def ndim(self):
        return self.data.ndim

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return (f"ΩTensor(shape={self.shape}, name='{self.name}', grad_fn={type(self._creator_op_instance).__name__ if self._creator_op_instance else None}, grad_present={'Yes' if self.grad is not None else 'No'})
{self.data}")

    # ======== OPS ========
    # These dunder methods will call Ops from the OpRegistry

    def __add__(self, other):
        return OpRegistry['add'](self, self._ensure_tensor(other))

    def __radd__(self, other): # other + self
        return OpRegistry['add'](self._ensure_tensor(other), self)

    def __mul__(self, other):
        return OpRegistry['mul'](self, self._ensure_tensor(other))

    def __rmul__(self, other): # other * self
        return OpRegistry['mul'](self._ensure_tensor(other), self)

    def __sub__(self, other):
        return OpRegistry['sub'](self, self._ensure_tensor(other))

    def __rsub__(self, other): # other - self
        return OpRegistry['sub'](self._ensure_tensor(other), self)

    def __truediv__(self, other):
        return OpRegistry['div'](self, self._ensure_tensor(other))

    def __rtruediv__(self, other): # other / self
        return OpRegistry['div'](self._ensure_tensor(other), self)

    def __pow__(self, exponent_val):
        # exponent_val should be a scalar or an OmegaTensor
        return OpRegistry['pow'](self, self._ensure_tensor(exponent_val))

    def __neg__(self):
        return OpRegistry['mul'](self, OmegaTensor(-1.0))


    def matmul(self, other):
        return OpRegistry['matmul'](self, self._ensure_tensor(other))

    def sum(self, axis=None, keepdims=False):
        return OpRegistry['sum'](self, axis=axis, keepdims=keepdims)

    def mean(self, axis=None, keepdims=False):
        return OpRegistry['mean'](self, axis=axis, keepdims=keepdims)

    def relu(self):
        return OpRegistry['relu'](self)

    def log(self): # Natural logarithm
        return OpRegistry['log'](self)

    def exp(self):
        return OpRegistry['exp'](self)

    def transpose(self, *axes):
        if not axes: # Default transpose (e.g., for 2D matrix)
            axes_tuple = tuple(reversed(range(self.data.ndim)))
        elif len(axes) == 1 and isinstance(axes[0], (list, tuple)):
            axes_tuple = tuple(axes[0])
        else:
            axes_tuple = axes
        return OpRegistry['transpose'](self, axes=axes_tuple)

    @property
    def T(self):
        if self.data.ndim < 2:
            return self # Transpose of scalar or 1D array is itself
        axes = tuple(reversed(range(self.data.ndim)))
        return self.transpose(axes)

    def reshape(self, *new_shape):
        if len(new_shape) == 1 and isinstance(new_shape[0], (tuple, list)):
            shape_tuple = tuple(new_shape[0])
        else:
            shape_tuple = new_shape
        return OpRegistry['reshape'](self, new_shape=shape_tuple)

    def softmax(self, axis=-1):
        return OpRegistry['softmax'](self, axis=axis)

    def sin(self):
        return OpRegistry['sin'](self)

    def cos(self):
        return OpRegistry['cos'](self)

    def apply_rotary_embedding(self, freqs_cis: 'OmegaTensor'):
        """Applies rotary embedding to this tensor using the provided frequencies."""
        return OpRegistry['rotary_embedding'](self, freqs_cis)

    @staticmethod
    def concatenate(tensors: list['OmegaTensor'], axis: int):
        """Concatenates a list of OmegaTensors along a specified axis."""
        # Basic validation
        if not tensors:
            raise ValueError("Input tensor list cannot be empty for concatenate.")
        if not all(isinstance(t, OmegaTensor) for t in tensors):
            raise TypeError("All items in tensors list must be OmegaTensor instances.")

        return OpRegistry['concatenate'](tensors, axis=axis)

# ================= Base Op Class (Optional but good practice) =================
class OmegaTensorOp:
    def __call__(self, *args, **kwargs):
        # This method will be overridden by specific ops
        raise NotImplementedError

    def backward(self, grad_out):
        # This method will be overridden by specific ops
        raise NotImplementedError

    def _store_context_for_backward(self, *tensors):
        # Helper to store parent tensors for backward pass
        # Ops will typically store self._parents from OmegaTensor.set_creator
        pass

# ================= OPS =================
# Each Op should ideally inherit from OmegaTensorOp

class EmbeddingOp(OmegaTensorOp):
    def __call__(self, weight_tensor, indices_tensor):
        # Ensure weight is OmegaTensor
        if not isinstance(weight_tensor, OmegaTensor):
            # This case should ideally be handled by a higher-level API or OmegaTensor.embedding() method
            # For direct Op usage, we expect OmegaTensors
            raise TypeError("EmbeddingOp weight must be an OmegaTensor.")

        # Ensure indices is OmegaTensor and its data is integer type
        if not isinstance(indices_tensor, OmegaTensor):
            # If raw list/numpy array is passed for indices, _ensure_tensor in a potential
            # OmegaTensor.embedding() method would wrap it.
            # However, OmegaTensor by default casts to float32.
            # For direct Op use, we might need to be flexible or strict.
            # Let's assume indices_tensor is already an OmegaTensor here.
            raise TypeError("EmbeddingOp indices must be an OmegaTensor.")

        indices_data = indices_tensor.data
        if not np.issubdtype(indices_data.dtype, np.integer):
            # Attempt to cast to a platform-independent integer type for indexing
            # np.intp is generally a good choice for indexing.
            indices_data = indices_data.astype(np.intp)
            # Warn if precision loss, though for indices it's usually about type not precision.
            # print("Warning: Casting indices data to integer type for EmbeddingOp.")

        # Forward pass: Gather rows from weight_tensor
        selected_vectors = weight_tensor.data[indices_data]

        out = OmegaTensor(selected_vectors, requires_grad=weight_tensor.requires_grad)
        if weight_tensor.requires_grad:
            out.set_creator(self, weight_tensor, indices_tensor) # Pass both as parents for graph completeness

        # Store necessary context for backward pass
        self._parents = (weight_tensor, indices_tensor) # Store original tensors
        self.indices_data_for_backward = indices_data # Store processed integer indices
        self.weight_shape_for_backward = weight_tensor.shape # Store shape for grad initialization

        return out

    def backward(self, grad_out):
        weight_tensor, indices_tensor = self._parents
        grad_weight = None

        if weight_tensor.requires_grad:
            grad_weight = np.zeros(self.weight_shape_for_backward, dtype=np.float32)
            # Accumulate gradients: for each item in grad_out, add it to the row in grad_weight
            # specified by the corresponding index in self.indices_data_for_backward
            # np.add.at is suitable for this, as it handles repeated indices correctly by accumulating.
            np.add.at(grad_weight, self.indices_data_for_backward, grad_out)

        # No gradient with respect to indices typically
        return [grad_weight, None]


class AddOp(OmegaTensorOp):
    def __call__(self, a, b):
        # Ensure inputs are OmegaTensors
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        b = b if isinstance(b, OmegaTensor) else OmegaTensor(b)

        out_data = a.data + b.data
        out = OmegaTensor(out_data, requires_grad=(a.requires_grad or b.requires_grad))
        out.set_creator(self, a, b)
        self._parents = (a,b) # Store for backward
        return out

    def backward(self, grad_out):
        a, b = self._parents
        grad_a = grad_out if a.requires_grad else None
        grad_b = grad_out if b.requires_grad else None

        # Handle broadcasting in backward pass
        if grad_a is not None and a.shape != grad_out.shape:
            grad_a = self._unbroadcast_gradient(grad_a, a.shape)
        if grad_b is not None and b.shape != grad_out.shape:
            grad_b = self._unbroadcast_gradient(grad_b, b.shape)

        return [grad_a, grad_b]

    def _unbroadcast_gradient(self, grad, original_shape):
        # Sum out dimensions that were broadcasted
        while grad.ndim > len(original_shape):
            grad = grad.sum(axis=0)
        for axis, dim in enumerate(original_shape):
            if dim == 1 and grad.shape[axis] > 1: # Was broadcast along this axis
                grad = grad.sum(axis=axis, keepdims=True)
        return grad


class SubOp(OmegaTensorOp):
    def __call__(self, a, b):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        b = b if isinstance(b, OmegaTensor) else OmegaTensor(b)
        out_data = a.data - b.data
        out = OmegaTensor(out_data, requires_grad=(a.requires_grad or b.requires_grad))
        out.set_creator(self, a, b)
        self._parents = (a,b)
        return out

    def backward(self, grad_out):
        a, b = self._parents
        grad_a = grad_out if a.requires_grad else None
        grad_b = -grad_out if b.requires_grad else None

        if grad_a is not None and a.shape != grad_out.shape:
            grad_a = AddOp._unbroadcast_gradient(None, grad_a, a.shape) # Use static method for unbroadcasting
        if grad_b is not None and b.shape != grad_out.shape: # grad_out shape check for grad_b as well
            grad_b = AddOp._unbroadcast_gradient(None, grad_b, b.shape)

        return [grad_a, grad_b]


class MulOp(OmegaTensorOp):
    def __call__(self, a, b):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        b = b if isinstance(b, OmegaTensor) else OmegaTensor(b)
        out_data = a.data * b.data
        out = OmegaTensor(out_data, requires_grad=(a.requires_grad or b.requires_grad))
        out.set_creator(self, a, b)
        self._parents = (a,b)
        return out

    def backward(self, grad_out):
        a, b = self._parents
        grad_a = grad_out * b.data if a.requires_grad else None
        grad_b = grad_out * a.data if b.requires_grad else None

        if grad_a is not None and a.shape != grad_out.shape:
            grad_a = AddOp._unbroadcast_gradient(None, grad_a, a.shape)
        if grad_b is not None and b.shape != grad_out.shape:
            grad_b = AddOp._unbroadcast_gradient(None, grad_b, b.shape)

        return [grad_a, grad_b]


class DivOp(OmegaTensorOp):
    def __call__(self, a, b):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        b = b if isinstance(b, OmegaTensor) else OmegaTensor(b)
        # Add small epsilon for stability if b.data can be zero
        # For now, assume b.data is not zero where division occurs
        out_data = a.data / b.data
        out = OmegaTensor(out_data, requires_grad=(a.requires_grad or b.requires_grad))
        out.set_creator(self, a, b)
        self._parents = (a,b)
        return out

    def backward(self, grad_out):
        a, b = self._parents
        # Add small epsilon for stability if b.data can be zero
        b_data_stable = b.data + 1e-8 # Basic stability for division by zero in gradient

        grad_a = grad_out / b_data_stable if a.requires_grad else None
        grad_b = -grad_out * a.data / (b_data_stable ** 2) if b.requires_grad else None

        if grad_a is not None and a.shape != grad_out.shape:
            grad_a = AddOp._unbroadcast_gradient(None, grad_a, a.shape)
        if grad_b is not None and b.shape != grad_out.shape:
            grad_b = AddOp._unbroadcast_gradient(None, grad_b, b.shape)

        return [grad_a, grad_b]


class PowOp(OmegaTensorOp):
    def __call__(self, a, b_exponent): # b_exponent is an OmegaTensor (ensured by __pow__)
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        # b_exponent is already an OmegaTensor due to _ensure_tensor in __pow__
        out_data = a.data ** b_exponent.data
        out = OmegaTensor(out_data, requires_grad=(a.requires_grad or b_exponent.requires_grad))
        out.set_creator(self, a, b_exponent)
        self._parents = (a, b_exponent)
        return out

    def backward(self, grad_out):
        a, b_exponent = self._parents
        base = a.data
        exponent = b_exponent.data

        grad_a = None
        if a.requires_grad:
            grad_a = grad_out * exponent * (base ** (exponent - 1))
            if a.shape != grad_out.shape: # Check if broadcasting happened for base
                 grad_a = AddOp._unbroadcast_gradient(None, grad_a, a.shape)


        grad_b = None
        if b_exponent.requires_grad:
            # Add small epsilon for stability if base can be zero or negative for log
            base_stable_for_log = np.where(base > 0, base, 1e-8)
            grad_b = grad_out * (base ** exponent) * np.log(base_stable_for_log)
            if b_exponent.shape != grad_out.shape: # Check if broadcasting happened for exponent
                grad_b = AddOp._unbroadcast_gradient(None, grad_b, b_exponent.shape)

        return [grad_a, grad_b]


class MatmulOp(OmegaTensorOp):
    def __call__(self, a, b):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        b = b if isinstance(b, OmegaTensor) else OmegaTensor(b)
        out_data = np.matmul(a.data, b.data)
        out = OmegaTensor(out_data, requires_grad=(a.requires_grad or b.requires_grad))
        out.set_creator(self, a, b)
        self._parents = (a,b)
        return out

    def backward(self, grad_out):
        a, b = self._parents
        grad_a = np.matmul(grad_out, b.data.T) if a.requires_grad else None
        grad_b = np.matmul(a.data.T, grad_out) if b.requires_grad else None
        return [grad_a, grad_b]


class SumOp(OmegaTensorOp):
    def __call__(self, a, axis=None, keepdims=False):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        out_data = np.sum(a.data, axis=axis, keepdims=keepdims)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a) # Only a is parent
        self._parents = (a,)
        self.axis = axis
        self.keepdims = keepdims
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]

        grad = grad_out
        # If keepdims was False, the summed axis was removed. Need to add it back for broadcasting.
        if self.axis is not None and not self.keepdims:
            grad = np.expand_dims(grad, axis=self.axis)
        return [np.ones_like(a.data) * grad]


class MeanOp(OmegaTensorOp):
    def __call__(self, a, axis=None, keepdims=False):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        out_data = np.mean(a.data, axis=axis, keepdims=keepdims)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        self.axis = axis
        self.keepdims = keepdims
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]

        shape = a.data.shape
        if self.axis is not None:
            n = shape[self.axis]
        else: # Mean over all elements
            n = a.data.size

        grad = grad_out / n

        if self.axis is not None and not self.keepdims:
            grad = np.expand_dims(grad, axis=self.axis)

        return [np.ones_like(a.data) * grad]


class ReluOp(OmegaTensorOp):
    def __call__(self, a):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        out_data = np.maximum(0, a.data)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]
        grad = grad_out * (a.data > 0)
        return [grad]


class LogOp(OmegaTensorOp): # Natural Logarithm
    def __call__(self, a):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        # Add small epsilon for stability if a.data can be zero or negative
        a_data_stable = np.where(a.data > 0, a.data, 1e-8)
        out_data = np.log(a_data_stable)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]
        # Use stable a.data for gradient as well
        a_data_stable = np.where(a.data > 0, a.data, 1e-8)
        grad = grad_out / a_data_stable
        return [grad]


class ExpOp(OmegaTensorOp):
    def __call__(self, a):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        out_data = np.exp(a.data)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]
        # The output of exp (which is self.data of the output tensor from forward) is needed here
        # We stored a as parent, so we use a.data to recompute exp(a.data)
        grad = grad_out * np.exp(a.data) # Or grad_out * out.data (if out was stored, but it's not)
        return [grad]


class TransposeOp(OmegaTensorOp):
    def __call__(self, a, axes=None): # axes should be a tuple
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        out_data = np.transpose(a.data, axes=axes)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        self.axes = axes
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]

        if self.axes:
            axes_inv = np.argsort(self.axes)
            grad = np.transpose(grad_out, axes=axes_inv)
        else: # Default transpose (e.g., for 2D, reverses axes)
            # The inverse of reversing axes is reversing them again
            grad = np.transpose(grad_out) # This assumes default np.transpose behavior matches inverse
        return [grad]


class ReshapeOp(OmegaTensorOp):
    def __call__(self, a, new_shape=None): # new_shape should be a tuple
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        out_data = np.reshape(a.data, new_shape)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        self.orig_shape = a.data.shape
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]
        grad = np.reshape(grad_out, self.orig_shape)
        return [grad]

class SoftmaxOp(OmegaTensorOp):
    def __call__(self, a, axis=-1):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        # Numerically stable softmax
        max_val = np.max(a.data, axis=axis, keepdims=True)
        exps = np.exp(a.data - max_val)
        self.out_data = exps / np.sum(exps, axis=axis, keepdims=True) # Store for backward

        out = OmegaTensor(self.out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        self.axis = axis # Store for backward as well, though not strictly needed if using self.out_data
        return out

    def backward(self, grad_out):
        # Based on https://eli.thegreenplace.net/2016/the-softmax-function-and-its-derivative/
        # d(softmax_i)/d(input_j) = softmax_i * (delta_ij - softmax_j)
        # For vector z and loss L, dL/dz_i = sum_k (dL/ds_k * ds_k/dz_i)
        # ds_k/dz_i = s_k * (delta_ki - s_i)
        # dL/dz_i = sum_k (grad_out_k * s_k * (delta_ki - s_i))
        # dL/dz_i = grad_out_i * s_i * (1 - s_i) + sum_{k!=i} (grad_out_k * s_k * (-s_i))
        # dL/dz_i = s_i * (grad_out_i * (1-s_i) - sum_{k!=i} (grad_out_k * s_k))
        # dL/dz_i = s_i * (grad_out_i - grad_out_i * s_i - sum_{k!=i} (grad_out_k * s_k))
        # dL/dz_i = s_i * (grad_out_i - sum_all_k (grad_out_k * s_k))
        # This is s * (grad_out - sum(grad_out * s, axis=axis, keepdims=True))

        a, = self._parents
        if not a.requires_grad:
            return [None]

        s = self.out_data # Softmax output from forward pass

        # Element-wise product of grad_out and s
        prod_grad_s = grad_out * s

        # Sum of these products along the softmax axis
        sum_prod_grad_s = np.sum(prod_grad_s, axis=self.axis, keepdims=True)

        # Jacobian-vector product for softmax
        grad = s * (grad_out - sum_prod_grad_s)
        return [grad]

class SinOp(OmegaTensorOp):
    def __call__(self, a):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        out_data = np.sin(a.data)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]
        grad_a = grad_out * np.cos(a.data)
        return [grad_a]

class CosOp(OmegaTensorOp):
    def __call__(self, a):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        out_data = np.cos(a.data)
        out = OmegaTensor(out_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]
        grad_a = grad_out * (-np.sin(a.data))
        return [grad_a]

class ConcatenateOp(OmegaTensorOp):
    def __call__(self, tensors: list[OmegaTensor], axis: int):
        if not tensors:
            raise ValueError("Tensor list for concatenation cannot be empty.")
        # It's assumed tensors are already OmegaTensor instances,
        # as this op would typically be called via OmegaTensor.concatenate

        self.axis = axis
        self.input_shapes = [t.shape for t in tensors]

        data_arrays = [t.data for t in tensors]
        output_data = np.concatenate(data_arrays, axis=axis)

        requires_grad = any(t.requires_grad for t in tensors)
        out = OmegaTensor(output_data, requires_grad=requires_grad)

        if out.requires_grad:
            out.set_creator(self, *tensors) # Pass all input tensors as parents

        self._parents = tuple(tensors) # Store for backward pass as well
        return out

    def backward(self, grad_out):
        # Split grad_out along self.axis according to the original shapes
        split_indices = np.cumsum([shape[self.axis] for shape in self.input_shapes[:-1]])

        grads_for_parents_data = np.split(grad_out, split_indices, axis=self.axis)

        # Ensure the number of gradient segments matches the number of parent tensors
        if len(grads_for_parents_data) != len(self._parents):
            # This should not happen if np.split works as expected with cumsum indices
            raise ValueError(f"ConcatenateOp backward: Mismatch between split grads ({len(grads_for_parents_data)}) and parents ({len(self._parents)}).")

        result_grads = []
        for i, parent_tensor in enumerate(self._parents):
            if parent_tensor.requires_grad:
                result_grads.append(grads_for_parents_data[i])
            else:
                result_grads.append(None)

        return result_grads

class RotaryEmbeddingOp(OmegaTensorOp):
    def __call__(self, x: OmegaTensor, freqs_cis: OmegaTensor):
        x_np = x.data
        freqs_cis_np = freqs_cis.data # Expected shape e.g., (seq_len, features) or (1, 1, seq_len, features) for broadcasting

        # Reshape x to view the last dimension as pairs
        # Input x shape e.g., (bsz, seq_len, dim) or (bsz, num_heads, seq_len, head_dim)
        x_reshaped_np = x_np.reshape(*x_np.shape[:-1], -1, 2)
        x_real_np = x_reshaped_np[..., 0]
        x_imag_np = x_reshaped_np[..., 1]

        # freqs_cis is (seq_len, dim) or (seq_len, head_dim)
        # We need to make it broadcastable with x_real_np/x_imag_np.
        # Target shape for freqs_cos/sin: (1, ..., seq_len, dim/2) matching x_real_np
        # Or ensure freqs_cis_np itself is already shaped like (1, ..., seq_len, dim)
        # For (bsz, seq_len, dim), freqs_cis (seq_len, dim) -> needs (1, seq_len, dim/2) for cos/sin parts.
        # For (bsz, n_h, seq_len, d_h), freqs_cis (seq_len, d_h) -> needs (1, 1, seq_len, d_h/2) for cos/sin parts.

        # Reshape freqs_cis to interpret the last dimension as pairs
        # The original freqs_cis_np has its last dim as head_dim or features_dim
        # Example: freqs_cis_np (..., features) -> (..., features/2, 2)
        freqs_reshaped_np = freqs_cis_np.reshape(*freqs_cis_np.shape[:-1], -1, 2)

        # Prepare for broadcasting with x_real_np/x_imag_np.
        # x_real_np could be (bsz, num_heads, seq_len, dim_pairs)
        # freqs_reshaped_np could be (seq_len, dim_pairs, 2)
        # We need ocos/osin to be (1, 1, seq_len, dim_pairs) for broadcasting, or similar.
        # This requires freqs_cis to be passed with a shape that's either directly broadcastable
        # or easily made so. Typically, freqs_cis is (seq_len, features).
        # The feature dimension of freqs_cis must match x's feature dimension.

        # Add singleton dimensions to freqs_reshaped_np to match x_reshaped_np's batch/head dimensions
        # Example: if x is (b,h,s,d/2,2) and freqs_cis was (s,d), freqs_reshaped is (s,d/2,2)
        # We need freqs_cos/sin to be (1,1,s,d/2) to broadcast with (b,h,s,d/2)
        # Number of singleton dims to add: x_reshaped_np.ndim - freqs_reshaped_np.ndim
        num_prefix_dims = x_reshaped_np.ndim - freqs_reshaped_np.ndim
        broadcast_shape_for_freqs = (1,) * num_prefix_dims + freqs_reshaped_np.shape

        freqs_cos_np_final = freqs_reshaped_np[..., 0].reshape(broadcast_shape_for_freqs[:-1]) # Remove the pair dim
        freqs_sin_np_final = freqs_reshaped_np[..., 1].reshape(broadcast_shape_for_freqs[:-1])

        self.freqs_cos_data = freqs_cos_np_final
        self.freqs_sin_data = freqs_sin_np_final

        # Perform rotation
        out_real_np = x_real_np * self.freqs_cos_data - x_imag_np * self.freqs_sin_data
        out_imag_np = x_real_np * self.freqs_sin_data + x_imag_np * self.freqs_cos_data

        # Interleave back
        output_np = np.empty_like(x_np)
        output_np[..., 0::2] = out_real_np
        output_np[..., 1::2] = out_imag_np

        out = OmegaTensor(output_np, requires_grad=x.requires_grad)
        if out.requires_grad:
            # x is the primary tensor whose gradient is computed. freqs_cis is constant.
            out.set_creator(self, x, freqs_cis)
        self._parents = (x, freqs_cis) # Store both for completeness, though only x's grad matters.
        return out

    def backward(self, grad_out_data: np.ndarray):
        x, _ = self._parents # freqs_cis is not used for grad computation itself here

        # Retrieve stored ocos and osin (already shaped for broadcasting)
        ocos_data = self.freqs_cos_data
        osin_data = self.freqs_sin_data

        # Slice grad_out_data into real and imaginary components
        grad_out_reshaped = grad_out_data.reshape(*grad_out_data.shape[:-1], -1, 2)
        grad_out_real_data = grad_out_reshaped[..., 0]
        grad_out_imag_data = grad_out_reshaped[..., 1]

        # Compute gradients for x_real and x_imag parts
        # grad_L_wrt_x_real = grad_L_wrt_out_real * d(out_real)/d(x_real) + grad_L_wrt_out_imag * d(out_imag)/d(x_real)
        # d(out_real)/d(x_real) = ocos_data
        # d(out_imag)/d(x_real) = osin_data
        grad_x_real_data = grad_out_real_data * ocos_data + grad_out_imag_data * osin_data

        # grad_L_wrt_x_imag = grad_L_wrt_out_real * d(out_real)/d(x_imag) + grad_L_wrt_out_imag * d(out_imag)/d(x_imag)
        # d(out_real)/d(x_imag) = -osin_data
        # d(out_imag)/d(x_imag) = ocos_data
        grad_x_imag_data = -grad_out_real_data * osin_data + grad_out_imag_data * ocos_data

        # Interleave back to get grad_x_data
        grad_x_data = np.empty_like(x.data)
        grad_x_data[..., 0::2] = grad_x_real_data
        grad_x_data[..., 1::2] = grad_x_imag_data

        return [grad_x_data, None] # No gradient for freqs_cis

# ===== OP REGISTRY (alien ops can be plugged here!) =====
OpRegistry = {
    'add': AddOp(),
    'sub': SubOp(),
    'mul': MulOp(),
    'div': DivOp(),
    'pow': PowOp(),
    'matmul': MatmulOp(),
    'sum': SumOp(),
    'mean': MeanOp(),
    'relu': ReluOp(),
    'log': LogOp(),
    'exp': ExpOp(),
    'transpose': TransposeOp(),
    'reshape': ReshapeOp(),
    'softmax': SoftmaxOp(),
    'embedding': EmbeddingOp(),
    'sin': SinOp(),
    'cos': CosOp(),
    'concatenate': ConcatenateOp(),
    'rotary_embedding': RotaryEmbeddingOp(),
}

# ============ ALIEN INTELLIGENCE INJECTION EXAMPLE ==============
class AlienFractalSumOp(OmegaTensorOp):
    def __call__(self, a, axis=None, keepdims=False):
        a = a if isinstance(a, OmegaTensor) else OmegaTensor(a)
        data = a.data
        # Example: fractal sigmoid weights based on element index
        element_indices = np.arange(data.size)
        weights = 1 / (1 + np.exp(-np.sin(element_indices * 0.1))) # Some arbitrary fractal-like weights
        weights_reshaped = weights.reshape(data.shape) # Ensure weights match data shape if needed for broadcasting

        # Apply weights. If data is multidimensional, ensure broadcasting is handled.
        # For simplicity, let's assume weights apply element-wise to flattened data then sum.
        if data.ndim > 1 and weights_reshaped.shape != data.shape : # Simple check
             weights_applied = data * weights_reshaped # This might need more careful broadcasting
        else:
             weights_applied = data * weights_reshaped


        summed_data = np.sum(weights_applied, axis=axis, keepdims=keepdims)

        out = OmegaTensor(summed_data, requires_grad=a.requires_grad)
        out.set_creator(self, a)
        self._parents = (a,)
        self.axis = axis
        self.keepdims = keepdims
        self.weights_reshaped = weights_reshaped # Store for backward
        return out

    def backward(self, grad_out):
        a, = self._parents
        if not a.requires_grad:
            return [None]

        # Gradient is grad_out scaled by the weights
        grad = grad_out * self.weights_reshaped

        # Handle un-summing / broadcasting for the gradient
        if self.axis is not None and not self.keepdims:
            # If summed along an axis and keepdims=False, grad_out will have one less dim.
            # We need to expand it back to correctly broadcast with weights_reshaped.
             grad_expanded = np.expand_dims(grad_out, axis=self.axis)
             grad = grad_expanded * self.weights_reshaped
        else: # Covers keepdims=True or axis=None (sum over all)
             grad = grad_out * self.weights_reshaped


        # Ensure the final gradient has the same shape as the original input 'a'
        # This part is tricky if 'weights_reshaped' was broadcasted to 'a.data'
        # For now, assume weights_reshaped had same shape as a.data
        # If a.data was [N, M] and sum was over M, grad_out could be [N,1] or [N].
        # grad would be [N,M] * [N,M] if weights are per element.
        # If grad_out was [N] and weights [N,M], then grad_expanded is [N,1] * [N,M] -> [N,M] (correct)

        return [grad]

# Example: plug in the alien op!
# OpRegistry['alien_sum'] = AlienFractalSumOp() # Commenting out alien op for now to focus on EmbeddingOp

if __name__ == '__main__':
    # Basic functionality tests
    print("--- Basic OmegaTensor Tests ---")

    # Test tensor creation
    a_data = np.array([1,2,3], dtype=np.float32)
    a = OmegaTensor(a_data, requires_grad=True, name="a")
    print(f"Tensor a: {a}")
    assert a.shape == (3,)
    assert a.name == "a"

    b_list = [4,5,6]
    b = OmegaTensor(b_list, requires_grad=True, name="b")
    print(f"Tensor b: {b}")
    assert b.shape == (3,)
    assert b.data.dtype == np.float32

    # Test AddOp
    print("\n--- Testing AddOp ---")
    c = a + b
    c.name = "c_add"
    print(f"c = a + b: {c}")
    assert np.allclose(c.data, np.array([5,7,9]))
    assert c._creator_op_instance == OpRegistry['add']

    # Test backward for AddOp
    c.backward(np.array([1,1,1], dtype=np.float32))
    print(f"a.grad after c.backward: {a.grad}")
    print(f"b.grad after c.backward: {b.grad}")
    assert np.allclose(a.grad, np.array([1,1,1]))
    assert np.allclose(b.grad, np.array([1,1,1]))

    # Test MulOp
    print("\n--- Testing MulOp ---")
    a.zero_grad()
    b.zero_grad()
    d = a * b
    d.name = "d_mul"
    print(f"d = a * b: {d}")
    assert np.allclose(d.data, np.array([4,10,18]))
    d.backward(np.array([1,1,1], dtype=np.float32))
    print(f"a.grad after d.backward: {a.grad}") # Expected: b.data * grad_out = [4,5,6]
    print(f"b.grad after d.backward: {b.grad}") # Expected: a.data * grad_out = [1,2,3]
    assert np.allclose(a.grad, b.data)
    assert np.allclose(b.grad, a.data)

    # Test PowOp
    print("\n--- Testing PowOp ---")
    a.zero_grad()
    e_val = OmegaTensor(2.0, name="exponent_two") # Exponent
    e = a.pow(e_val) # a^2
    e.name = "e_pow"
    print(f"e = a ** 2: {e}") # [1,4,9]
    assert np.allclose(e.data, np.array([1,4,9]))
    e.backward(np.array([1,1,1], dtype=np.float32)) # d(a^2)/da = 2a
    print(f"a.grad after e.backward: {a.grad}") # Expected: 2 * a.data * grad_out = [2,4,6]
    assert np.allclose(a.grad, 2 * a.data)
    assert e_val.grad is None # Exponent does not require_grad by default in _ensure_tensor

    # Test MatmulOp
    print("\n--- Testing MatmulOp ---")
    m1_data = np.array([[1,2],[3,4]], dtype=np.float32)
    m1 = OmegaTensor(m1_data, requires_grad=True, name="m1")
    m2_data = np.array([[5,6],[7,8]], dtype=np.float32)
    m2 = OmegaTensor(m2_data, requires_grad=True, name="m2")
    m_out = m1.matmul(m2)
    m_out.name = "m_out"
    # [[1*5+2*7, 1*6+2*8], [3*5+4*7, 3*6+4*8]] = [[19,22],[43,50]]
    print(f"m_out = m1 @ m2: {m_out}")
    assert np.allclose(m_out.data, np.array([[19,22],[43,50]]))

    dummy_grad_matmul = np.ones_like(m_out.data)
    m_out.backward(dummy_grad_matmul)
    print(f"m1.grad shape: {m1.grad.shape}") # Expected: dummy_grad @ m2.T
    # m2.T = [[5,7],[6,8]]
    # dummy_grad @ m2.T = [[1,1],[1,1]] @ [[5,7],[6,8]] = [[11,15],[11,15]]
    assert np.allclose(m1.grad, np.array([[11,15],[11,15]]))
    print(f"m2.grad shape: {m2.grad.shape}") # Expected: m1.T @ dummy_grad
    # m1.T = [[1,3],[2,4]]
    # m1.T @ dummy_grad = [[1,3],[2,4]] @ [[1,1],[1,1]] = [[4,4],[6,6]]
    assert np.allclose(m2.grad, np.array([[4,4],[6,6]]))

    # Test SinOp and CosOp
    print("\n--- Testing SinOp and CosOp ---")
    val_for_trig_data = np.array([0, np.pi/2, np.pi], dtype=np.float32)
    val_for_trig = OmegaTensor(val_for_trig_data, requires_grad=True, name="trig_input")

    # Test Sin
    sin_val = val_for_trig.sin()
    sin_val.name = "sin_output"
    print(f"sin(input): {sin_val.data}") # Expected: [0, 1, 0] (approx for np.pi)
    assert np.allclose(sin_val.data, np.array([0, 1, np.sin(np.pi)], dtype=np.float32), atol=1e-7)

    sin_val.backward(np.array([1,1,1], dtype=np.float32))
    print(f"grad for sin input: {val_for_trig.grad}") # Expected: cos(input) * grad_out = [cos(0), cos(pi/2), cos(pi)] = [1,0,-1]
    assert np.allclose(val_for_trig.grad, np.cos(val_for_trig_data), atol=1e-7)

    # Test Cos
    val_for_trig.zero_grad() # Reset grad
    cos_val = val_for_trig.cos()
    cos_val.name = "cos_output"
    print(f"cos(input): {cos_val.data}") # Expected: [1, 0, -1]
    assert np.allclose(cos_val.data, np.array([1, 0, -1], dtype=np.float32), atol=1e-7)

    cos_val.backward(np.array([1,1,1], dtype=np.float32))
    print(f"grad for cos input: {val_for_trig.grad}") # Expected: -sin(input) * grad_out = [-sin(0), -sin(pi/2), -sin(pi)] = [0,-1,0]
    assert np.allclose(val_for_trig.grad, -np.sin(val_for_trig_data), atol=1e-7)

    print("\n--- All OmegaTensor basic tests finished ---")


    # Test ConcatenateOp
    print("\n--- Testing ConcatenateOp ---")
    t1_data = np.array([[1,2],[3,4]], dtype=np.float32)
    t1 = OmegaTensor(t1_data, requires_grad=True, name="t1_cat")
    t2_data = np.array([[5,6],[7,8]], dtype=np.float32)
    t2 = OmegaTensor(t2_data, requires_grad=True, name="t2_cat")
    t3_data = np.array([[9,10],[11,12]], dtype=np.float32)
    t3 = OmegaTensor(t3_data, requires_grad=True, name="t3_cat")

    # Test concatenate along axis 0
    cat_axis0 = OmegaTensor.concatenate([t1, t2, t3], axis=0)
    cat_axis0.name = "cat_axis0"
    expected_axis0_data = np.concatenate([t1_data, t2_data, t3_data], axis=0)
    print(f"Concatenated along axis 0:\n{cat_axis0.data}")
    assert np.allclose(cat_axis0.data, expected_axis0_data), "Concat axis 0 data mismatch"
    assert cat_axis0.shape == (6,2), "Concat axis 0 shape mismatch"

    # Backward for axis 0
    cat_axis0.backward(np.ones_like(cat_axis0.data))
    assert t1.grad is not None and np.allclose(t1.grad, np.ones_like(t1_data)), "t1.grad mismatch for axis 0 concat"
    assert t2.grad is not None and np.allclose(t2.grad, np.ones_like(t2_data)), "t2.grad mismatch for axis 0 concat"
    assert t3.grad is not None and np.allclose(t3.grad, np.ones_like(t3_data)), "t3.grad mismatch for axis 0 concat"
    print("Backward pass for axis 0 concatenation seems OK.")

    t1.zero_grad(); t2.zero_grad(); t3.zero_grad()

    # Test concatenate along axis 1
    cat_axis1 = OmegaTensor.concatenate([t1, t2, t3], axis=1)
    cat_axis1.name = "cat_axis1"
    expected_axis1_data = np.concatenate([t1_data, t2_data, t3_data], axis=1)
    print(f"Concatenated along axis 1:\n{cat_axis1.data}")
    assert np.allclose(cat_axis1.data, expected_axis1_data), "Concat axis 1 data mismatch"
    assert cat_axis1.shape == (2,6), "Concat axis 1 shape mismatch"

    # Backward for axis 1
    cat_axis1.backward(np.ones_like(cat_axis1.data))
    assert t1.grad is not None and np.allclose(t1.grad, np.ones_like(t1_data)), "t1.grad mismatch for axis 1 concat"
    assert t2.grad is not None and np.allclose(t2.grad, np.ones_like(t2_data)), "t2.grad mismatch for axis 1 concat"
    assert t3.grad is not None and np.allclose(t3.grad, np.ones_like(t3_data)), "t3.grad mismatch for axis 1 concat"
    print("Backward pass for axis 1 concatenation seems OK.")

    # Test with one tensor not requiring grad
    t1.zero_grad(); t2.zero_grad(); t3.zero_grad()
    t2.requires_grad = False
    cat_axis1_partial_grad = OmegaTensor.concatenate([t1, t2, t3], axis=1)
    cat_axis1_partial_grad.backward(np.ones_like(cat_axis1_partial_grad.data))
    assert t1.grad is not None, "t1.grad should exist"
    assert t2.grad is None, "t2.grad should be None as requires_grad was False"
    assert t3.grad is not None, "t3.grad should exist"
    print("Backward pass with partial requires_grad seems OK for concatenate.")
    t2.requires_grad = True # Reset for any future tests

    print("\n--- All OmegaTensor tests (including ConcatenateOp) finished ---")


    # Test RotaryEmbeddingOp
    print("\n--- Testing RotaryEmbeddingOp ---")
    # x: (bsz, seq_len, dim) e.g. (1, 2, 4)
    # freqs_cis: (seq_len, dim) e.g. (2, 4)
    x_rope_data_op = np.array([[[0,1,2,3], [4,5,6,7]]], dtype=np.float32) # bsz=1, seq_len=2, dim=4
    x_rope_op = OmegaTensor(x_rope_data_op, requires_grad=True, name="x_rope_op")

    freqs_cis_rope_data_op = np.zeros((2,4), dtype=np.float32) # seq_len=2, dim=4
    freqs_cis_rope_data_op[:, 0::2] = 0 # cos components = 0
    freqs_cis_rope_data_op[:, 1::2] = 1 # sin components = 1
    # This means: cos_theta=0, sin_theta=1 (90 degree rotation)
    # freqs_cis_op_data = [[0,1,0,1], [0,1,0,1]]
    freqs_cis_rope_op = OmegaTensor(freqs_cis_rope_data_op, requires_grad=False, name="freqs_cis_rope_op")

    # Expected output (90 deg rotation):
    # x_real = [0,2], [4,6]
    # x_imag = [1,3], [5,7]
    # For cos=0, sin=1:
    # out_real = x_real * 0 - x_imag * 1 = -x_imag = [[-1,-3], [-5,-7]]
    # out_imag = x_real * 1 + x_imag * 0 =  x_real = [[ 0, 2], [ 4, 6]]
    # Interleaved: [[-1,0,-3,2], [-5,4,-7,6]]
    expected_output_rope_op_data = np.array([[[-1,0,-3,2],[-5,4,-7,6]]], dtype=np.float32)

    # Forward pass
    output_rope_op = x_rope_op.apply_rotary_embedding(freqs_cis_rope_op)
    output_rope_op.name = "output_rope_op"
    print(f"RotaryEmbeddingOp Input x:\n{x_rope_op.data}")
    print(f"RotaryEmbeddingOp Input freqs_cis:\n{freqs_cis_rope_op.data}")
    print(f"RotaryEmbeddingOp Output:\n{output_rope_op.data}")
    assert np.allclose(output_rope_op.data, expected_output_rope_op_data, atol=1e-6), "RotaryEmbeddingOp forward pass output mismatch."
    print("RotaryEmbeddingOp forward pass seems OK.")

    # Backward pass
    x_rope_op.zero_grad()
    # Sum all elements of output as loss
    loss_rope_op = OmegaTensor(output_rope_op.data.sum(), requires_grad=True) # Create a new tensor for loss sum
    loss_rope_op.set_creator(OpRegistry['sum'], output_rope_op) # Manually set creator for sum if not using .sum() method
                                                                # Or simply: loss_rope_op = output_rope_op.sum()

    # To test backward through RotaryEmbeddingOp, create grad_output for output_rope_op
    # For simplicity, let grad_output be all ones.
    dummy_grad_output_for_rope = np.ones_like(output_rope_op.data)
    output_rope_op.backward(dummy_grad_output_for_rope)

    assert x_rope_op.grad is not None, "x_rope_op.grad should not be None after backward."
    print(f"x_rope_op.grad:\n{x_rope_op.grad}")

    # Manual grad calculation for this specific case (cos=0, sin=1 for freqs_cis)
    # out_real = -x_imag
    # out_imag =  x_real
    # If grad_out_real=1, grad_out_imag=1 for all components:
    # grad_x_real = grad_out_real * cos + grad_out_imag * sin = 1*0 + 1*1 = 1
    # grad_x_imag = -grad_out_real * sin + grad_out_imag * cos = -1*1 + 1*0 = -1
    # So, grad_x should be: [[[1,-1,1,-1], [1,-1,1,-1]]]
    expected_grad_x_data = np.empty_like(x_rope_data_op)
    expected_grad_x_data[..., 0::2] = 1.0 # grad for real parts
    expected_grad_x_data[..., 1::2] = -1.0 # grad for imag parts

    assert np.allclose(x_rope_op.grad, expected_grad_x_data, atol=1e-6), "RotaryEmbeddingOp backward pass gradient mismatch."
    print("RotaryEmbeddingOp backward pass seems OK.")

    print("\n--- All OmegaTensor tests (including RotaryEmbeddingOp) finished ---")
