import numpy as np

OpRegistry = {}

def register_op(name):
    def decorator(op_cls):
        OpRegistry[name] = op_cls()
        return op_cls
    return decorator

class OmegaTensor:
    def __init__(self, data, requires_grad=False, device='cpu', name=None):
        if not isinstance(data, np.ndarray):
            data = np.array(data, dtype=np.float32)
        self.data = data
        self.requires_grad = requires_grad
        self.grad = None
        self._creator_op_instance = None
        self._creator_parents = tuple()
        self.device = device
        self.name = name
        self._version = 0

    def _ensure_tensor(self, other_data):
        if isinstance(other_data, OmegaTensor): return other_data
        return OmegaTensor(other_data)

    def set_creator(self, op_instance, *parents):
        self._creator_op_instance = op_instance
        self._creator_parents = parents
        if self.requires_grad:
            for p in parents:
                if isinstance(p, OmegaTensor): p.requires_grad = True

    def zero_grad(self): self.grad = None

    def backward(self, grad_output_data=None):
        if not self.requires_grad: return
        if grad_output_data is None:
            if self.data.size == 1: grad_output_data = np.array(1.0, dtype=np.float32)
            else: raise ValueError("grad_output_data must be specified for non-scalar OmegaTensors in backward()")
        if not isinstance(grad_output_data, np.ndarray): grad_output_data = np.array(grad_output_data, dtype=np.float32)
        if self.grad is None: self.grad = grad_output_data.copy()
        else: self.grad += grad_output_data
        if self._creator_op_instance:
            grads_for_parents_data = self._creator_op_instance.backward(self.grad)
            if not isinstance(grads_for_parents_data, (list, tuple)): grads_for_parents_data = [grads_for_parents_data]
            if len(self._creator_parents) != len(grads_for_parents_data):
                raise ValueError(f"Op {type(self._creator_op_instance).__name__}: Mismatch parents ({len(self._creator_parents)}) vs grads ({len(grads_for_parents_data)}).")
            for parent_tensor, parent_grad_data in zip(self._creator_parents, grads_for_parents_data):
                if isinstance(parent_tensor, OmegaTensor) and parent_tensor.requires_grad and parent_grad_data is not None:
                    parent_tensor.backward(parent_grad_data)
    @property
    def shape(self): return self.data.shape
    def __len__(self): return len(self.data)
    def __repr__(self): return (f"OmegaTensor(shape={self.shape}, name='{self.name}', grad_fn={type(self._creator_op_instance).__name__ if self._creator_op_instance else None}, grad={'Yes' if self.grad is not None else 'No'})\n{self.data}")
    def __add__(self, other): return OpRegistry['add'](self, self._ensure_tensor(other))
    def __mul__(self, other): return OpRegistry['mul'](self, self._ensure_tensor(other))
    def __sub__(self, other): return OpRegistry['sub'](self, self._ensure_tensor(other))
    def __truediv__(self, other): return OpRegistry['div'](self, self._ensure_tensor(other))
    def __pow__(self, exponent_val): exponent = self._ensure_tensor(exponent_val); return OpRegistry['pow'](self, exponent)
    def matmul(self, other): return OpRegistry['matmul'](self, self._ensure_tensor(other))
    def sum(self, axis=None, keepdims=False): return OpRegistry['sum'](self, axis=axis, keepdims=keepdims)
    def mean(self, axis=None, keepdims=False): return OpRegistry['mean'](self, axis=axis, keepdims=keepdims)
    def relu(self): return OpRegistry['relu'](self)
    def log(self): return OpRegistry['log'](self)
    def exp(self): return OpRegistry['exp'](self)
    def transpose(self, *axes):
        if not axes: axes = tuple(reversed(range(self.data.ndim)))
        elif len(axes) == 1 and isinstance(axes[0], (list, tuple)): axes = tuple(axes[0])
        return OpRegistry['transpose'](self, axes=axes)
    @property
    def T(self):
        if self.data.ndim < 2: return self
        axes = tuple(reversed(range(self.data.ndim)))
        return self.transpose(axes)
    def reshape(self, *new_shape):
        if len(new_shape) == 1 and isinstance(new_shape[0], (tuple, list)): new_shape = tuple(new_shape[0])
        return OpRegistry['reshape'](self, new_shape=new_shape)
    def softmax(self, axis=-1): return OpRegistry['softmax'](self, axis=axis)

class Op:
    def __call__(self, *args, **kwargs):
        self.args_for_backward = args
        self.kwargs_for_backward = kwargs
        processed_args_data = []
        for arg in args:
            if isinstance(arg, OmegaTensor): processed_args_data.append(arg.data)
            elif isinstance(arg, (int, float, list, tuple, np.ndarray)): processed_args_data.append(np.array(arg, dtype=np.float32) if not isinstance(arg, np.ndarray) else arg.astype(np.float32))
            else: processed_args_data.append(arg)
        result_data = self.forward(*processed_args_data, **kwargs)
        requires_grad = any(isinstance(arg, OmegaTensor) and arg.requires_grad for arg in args)
        output_tensor = OmegaTensor(result_data, requires_grad=requires_grad)
        if requires_grad: output_tensor.set_creator(self, *[arg for arg in args if isinstance(arg, OmegaTensor)])
        self.forward_output_data_cache = result_data
        return output_tensor
    @staticmethod
    def forward(*args_data, **kwargs): raise NotImplementedError
    def backward(self, output_grad_data): raise NotImplementedError
