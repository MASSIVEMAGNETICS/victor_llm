# File: bandocodex/tests/test_tensor.py

import unittest
import numpy as np
# Attempt to import from bandocodex, assuming it's in PYTHONPATH or structured correctly
try:
    from bandocodex.tensor import Tensor
except ImportError:
    # Fallback for environments where bandocodex might not be in PYTHONPATH
    # This assumes the tests directory is a sibling to the bandocodex directory
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent)) # Go up to project root
    from bandocodex.tensor import Tensor


class TestTensor(unittest.TestCase):

    def test_tensor_creation(self):
        t1 = Tensor([1, 2, 3])
        self.assertIsInstance(t1.data, np.ndarray)
        self.assertEqual(t1.data.tolist(), [1, 2, 3])
        self.assertFalse(t1.requires_grad)
        self.assertEqual(t1.grad.shape, t1.data.shape)

        t2 = Tensor([[1, 2], [3, 4]], requires_grad=True)
        self.assertTrue(t2.requires_grad)

    def test_tensor_addition(self):
        t1 = Tensor([1, 2, 3], requires_grad=True)
        t2 = Tensor([4, 5, 6], requires_grad=True)
        t3 = t1 + t2
        self.assertEqual(t3.data.tolist(), [5, 7, 9])
        self.assertTrue(t3.requires_grad)

        t3.backward()
        self.assertEqual(t1.grad.tolist(), [1, 1, 1])
        self.assertEqual(t2.grad.tolist(), [1, 1, 1])

        t4 = Tensor([1, 2, 3], requires_grad=True)
        t5 = t4 + 10 # Test with scalar
        self.assertEqual(t5.data.tolist(), [11, 12, 13])
        t5.backward()
        self.assertEqual(t4.grad.tolist(), [1, 1, 1])


    def test_tensor_multiplication(self):
        t1 = Tensor([1, 2, 3], requires_grad=True)
        t2 = Tensor([4, 5, 6], requires_grad=True)
        t3 = t1 * t2
        self.assertEqual(t3.data.tolist(), [4, 10, 18])
        self.assertTrue(t3.requires_grad)

        t3.backward()
        self.assertEqual(t1.grad.tolist(), [4, 5, 6])
        self.assertEqual(t2.grad.tolist(), [1, 2, 3])

        t4 = Tensor([1, 2, 3], requires_grad=True)
        t5 = t4 * 3 # Test with scalar
        self.assertEqual(t5.data.tolist(), [3, 6, 9])
        t5.backward()
        self.assertEqual(t4.grad.tolist(), [3, 3, 3])

    def test_tensor_power(self):
        t1 = Tensor([1, 2, 3], requires_grad=True)
        t2 = t1 ** 3
        self.assertEqual(t2.data.tolist(), [1, 8, 27])
        self.assertTrue(t2.requires_grad)

        t2.backward()
        expected_grad = (3 * t1.data**2).tolist()
        self.assertEqual(t1.grad.tolist(), expected_grad)

    def test_relu(self):
        t1 = Tensor([-1, 0, 2], requires_grad=True)
        t2 = t1.relu()
        self.assertEqual(t2.data.tolist(), [0, 0, 2])
        self.assertTrue(t2.requires_grad)

        t2.backward()
        self.assertEqual(t1.grad.tolist(), [0, 0, 1])

    def test_backward_propagation_simple_scalar(self):
        # Test backward on a scalar tensor that is the result of operations
        x = Tensor(2.0, requires_grad=True, name="x")
        y = Tensor(3.0, requires_grad=True, name="y")

        # Intermediate operations
        a = x * y  # a = 6
        z = a + y  # z = 6 + 3 = 9

        # Ensure z requires grad
        self.assertTrue(z.requires_grad)

        z.backward()

        # dz/dx = y = 3
        # dz/dy = x (from a) + 1 (from y in z=a+y) = 2 + 1 = 3
        self.assertAlmostEqual(x.grad.item(), 3.0)
        self.assertAlmostEqual(y.grad.item(), 3.0)

    def test_transpose(self):
        t1 = Tensor([[1,2],[3,4]], requires_grad=True)
        t2 = t1.T
        self.assertEqual(t2.data.tolist(), [[1,3],[2,4]])
        self.assertTrue(t2.requires_grad)

        # To test backward, need a scalar output.
        # Create a dummy operation that leads to a scalar.
        # This is a bit artificial but tests the transpose gradient flow.
        # Let a scalar loss L = sum of all elements in t2.
        # So t2.grad will be all ones.
        loss_equivalent_grad = np.ones_like(t2.data)

        # Manually set grad and call _backward for t2
        t2.grad = loss_equivalent_grad
        t2._backward()

        # Expected t1.grad = (t2.grad).T
        self.assertEqual(t1.grad.tolist(), loss_equivalent_grad.T.tolist())


    def test_dot_product(self):
        t1 = Tensor([[1, 2], [3, 4]], requires_grad=True)
        t2 = Tensor([[5, 6], [7, 8]], requires_grad=True)
        t3 = t1.dot(t2)

        self.assertEqual(t3.data.tolist(), [[19, 22], [43, 50]])
        self.assertTrue(t3.requires_grad)

        # Assume t3.grad = np.ones_like(t3.data) for testing (like from a sum)
        loss_equivalent_grad = np.ones_like(t3.data)
        t3.grad = loss_equivalent_grad
        t3._backward()

        expected_t1_grad = np.dot(loss_equivalent_grad, t2.data.T)
        expected_t2_grad = np.dot(t1.data.T, loss_equivalent_grad)

        self.assertTrue(np.allclose(t1.grad, expected_t1_grad))
        self.assertTrue(np.allclose(t2.grad, expected_t2_grad))

    def test_no_grad_propagation(self):
        t1 = Tensor([1,2,3], requires_grad=False)
        t2 = Tensor([4,5,6], requires_grad=True)
        t3 = t1 + t2
        self.assertTrue(t3.requires_grad)

        t3.backward() # grad should be 1 for t3 by default if it's the end of chain

        # t1 should not accumulate gradients
        self.assertTrue(np.all(t1.grad == np.zeros_like(t1.data)))
        # t2 should accumulate gradients
        self.assertEqual(t2.grad.tolist(), [1,1,1])


if __name__ == '__main__':
    unittest.main()
