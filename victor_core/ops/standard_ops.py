import numpy as np
from victor_core.ops.omega_tensor import Op, register_op

@register_op('add')
class AddOp(Op):
    @staticmethod
    def forward(a_data, b_data): return a_data + b_data
    def backward(self, output_grad_data): return [output_grad_data, output_grad_data]

@register_op('mul')
class MulOp(Op):
    @staticmethod
    def forward(a_data, b_data): return a_data * b_data
    def backward(self, output_grad_data):
        a_data = self.args_for_backward[0].data
        b_data = self.args_for_backward[1].data
        return [output_grad_data * b_data, output_grad_data * a_data]

@register_op('sub')
class SubOp(Op):
    @staticmethod
    def forward(a_data, b_data): return a_data - b_data
    def backward(self, output_grad_data): return [output_grad_data, -output_grad_data]

@register_op('div')
class DivOp(Op):
    @staticmethod
    def forward(a_data, b_data): return a_data / b_data
    def backward(self, output_grad_data):
        a_data = self.args_for_backward[0].data
        b_data = self.args_for_backward[1].data
        return [output_grad_data / b_data, output_grad_data * (-a_data / (b_data**2))]

@register_op('pow')
class PowOp(Op):
    @staticmethod
    def forward(a_data, b_val_data): return a_data ** b_val_data # b_val is the exponent
    def backward(self, output_grad_data):
        a_data = self.args_for_backward[0].data
        b_val_data = self.args_for_backward[1].data # exponent
        grad_a = output_grad_data * (b_val_data * (a_data ** (b_val_data - 1)))
        # Gradient for exponent is not handled here, assuming exponent is not a tensor requiring grad
        return [grad_a, None]


@register_op('matmul')
class MatMulOp(Op):
    @staticmethod
    def forward(a_data, b_data): return np.matmul(a_data, b_data)
    def backward(self, output_grad_data):
        a_data = self.args_for_backward[0].data
        b_data = self.args_for_backward[1].data
        grad_a = np.matmul(output_grad_data, b_data.T)
        grad_b = np.matmul(a_data.T, output_grad_data)
        return [grad_a, grad_b]

@register_op('sum')
class SumOp(Op):
    @staticmethod
    def forward(a_data, axis=None, keepdims=False): return np.sum(a_data, axis=axis, keepdims=keepdims)
    def backward(self, output_grad_data):
        a_data = self.args_for_backward[0].data
        axis = self.kwargs_for_backward.get('axis')
        keepdims = self.kwargs_for_backward.get('keepdims', False)
        if axis is not None and not keepdims:
            output_grad_data = np.expand_dims(output_grad_data, axis=axis)
        return [np.ones_like(a_data) * output_grad_data]

@register_op('mean')
class MeanOp(Op):
    @staticmethod
    def forward(a_data, axis=None, keepdims=False): return np.mean(a_data, axis=axis, keepdims=keepdims)
    def backward(self, output_grad_data):
        a_data = self.args_for_backward[0].data
        axis = self.kwargs_for_backward.get('axis')
        keepdims = self.kwargs_for_backward.get('keepdims', False)

        num_elements = np.prod(a_data.shape)
        if axis is not None:
            num_elements_along_axis = a_data.shape[axis] if isinstance(axis, int) else np.prod(np.array(a_data.shape)[list(axis)])
        else: # full reduction
            num_elements_along_axis = num_elements

        if axis is not None and not keepdims:
             output_grad_data = np.expand_dims(output_grad_data, axis=axis)

        return [(output_grad_data / num_elements_along_axis) * np.ones_like(a_data)]

@register_op('relu')
class ReLUOp(Op):
    @staticmethod
    def forward(a_data): return np.maximum(0, a_data)
    def backward(self, output_grad_data):
        a_data = self.args_for_backward[0].data
        return [output_grad_data * (a_data > 0)]

@register_op('log')
class LogOp(Op): # Natural logarithm
    @staticmethod
    def forward(a_data): return np.log(a_data)
    def backward(self, output_grad_data):
        a_data = self.args_for_backward[0].data
        return [output_grad_data * (1 / a_data)]

@register_op('exp')
class ExpOp(Op):
    @staticmethod
    def forward(a_data): return np.exp(a_data)
    def backward(self, output_grad_data):
        # forward_output_data_cache is exp(a_data)
        return [output_grad_data * self.forward_output_data_cache]


@register_op('transpose')
class TransposeOp(Op):
    @staticmethod
    def forward(a_data, axes=None): return np.transpose(a_data, axes=axes)
    def backward(self, output_grad_data):
        axes = self.kwargs_for_backward.get('axes')
        if axes is None:
            # If axes is None, np.transpose reverses the axes.
            # To revert, we need the inverse permutation, which is the same permutation for reversal.
            inv_axes = None # Or tuple(reversed(range(output_grad_data.ndim))) if explicit needed
        else:
            inv_axes = np.argsort(axes)
        return [np.transpose(output_grad_data, axes=inv_axes)]

@register_op('reshape')
class ReshapeOp(Op):
    @staticmethod
    def forward(a_data, new_shape): return np.reshape(a_data, new_shape)
    def backward(self, output_grad_data):
        original_shape = self.args_for_backward[0].shape
        return [np.reshape(output_grad_data, original_shape)]

@register_op('softmax')
class SoftmaxOp(Op):
    @staticmethod
    def forward(a_data, axis=-1):
        e_x = np.exp(a_data - np.max(a_data, axis=axis, keepdims=True))
        return e_x / np.sum(e_x, axis=axis, keepdims=True)
    def backward(self, output_grad_data):
        # s is the softmax output, already computed in forward and cached
        s = self.forward_output_data_cache
        # The Jacobian of softmax is a bit complex: S_i * (delta_ij - S_j)
        # Element-wise product of output_grad_data and s
        s_times_grad = output_grad_data * s
        # Sum of s_times_grad along the softmax axis
        sum_s_times_grad = np.sum(s_times_grad, axis=self.kwargs_for_backward.get('axis', -1), keepdims=True)
        # Grad for input x_i is s_i * (output_grad_i - sum(output_grad_j * s_j))
        return [s * (output_grad_data - sum_s_times_grad)]
