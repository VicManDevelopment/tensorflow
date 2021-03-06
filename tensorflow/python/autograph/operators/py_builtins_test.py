# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for py_builtins module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

import six

from tensorflow.python.autograph.operators import data_structures
from tensorflow.python.autograph.operators import py_builtins
from tensorflow.python.data.ops import dataset_ops
from tensorflow.python.framework import constant_op
from tensorflow.python.framework import dtypes
from tensorflow.python.framework import errors_impl
from tensorflow.python.framework import test_util
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import tensor_array_ops
from tensorflow.python.platform import test


class PyBuiltinsTest(test.TestCase):

  def test_abs(self):
    self.assertEqual(py_builtins.abs_(-1), 1)
    with self.cached_session() as sess:
      t = py_builtins.abs_(constant_op.constant(-1))
      self.assertEqual(self.evaluate(t), 1)
      t = py_builtins.abs_(constant_op.constant([-1, 2, -3]))
      self.assertAllEqual(self.evaluate(t), [1, 2, 3])

  def test_float(self):
    self.assertEqual(py_builtins.float_(10), 10.0)
    self.assertEqual(py_builtins.float_('10.0'), 10.0)
    with self.cached_session() as sess:
      t = py_builtins.float_(constant_op.constant(1, dtype=dtypes.int64))
      self.assertEqual(self.evaluate(t), 1.0)
      st = py_builtins.float_(constant_op.constant('1.0'))
      self.assertEqual(self.evaluate(st), 1.0)

  def test_int(self):
    self.assertEqual(py_builtins.int_(10.0), 10)
    self.assertEqual(py_builtins.int_('11', 2), 3)
    with self.cached_session() as sess:
      t = py_builtins.int_(constant_op.constant(1, dtype=dtypes.float64))
      self.assertEqual(self.evaluate(t), 1)
      st = py_builtins.int_(constant_op.constant('1'))
      self.assertEqual(self.evaluate(st), 1)
      st = py_builtins.int_(constant_op.constant('1'), 10)
      self.assertEqual(self.evaluate(st), 1)

  def test_int_unsupported_base(self):
    t = constant_op.constant(1, dtype=dtypes.float64)
    with self.assertRaises(NotImplementedError):
      py_builtins.int_(t, 2)

  def test_len(self):
    self.assertEqual(py_builtins.len_([1, 2, 3]), 3)
    with self.cached_session() as sess:
      t = py_builtins.len_(constant_op.constant([[1], [2], [3]]))
      self.assertEqual(t, 3)
      ta = py_builtins.len_(tensor_array_ops.TensorArray(dtypes.int32, size=5))
      self.assertEqual(self.evaluate(ta), 5)
      tl = py_builtins.len_(data_structures.tf_tensor_list_new([3, 4, 5]))
      self.assertEqual(self.evaluate(tl), 3)

  def test_len_scalar(self):
    with self.assertRaises(ValueError):
      py_builtins.len_(constant_op.constant(1))

  @test_util.run_deprecated_v1
  def test_len_dynamic_shape(self):
    with self.cached_session() as sess:
      p = array_ops.placeholder(dtype=dtypes.int32, shape=None)
      t = py_builtins.len_(p)
      self.assertEqual(sess.run(t, {p: [1, 2, 3]}), 3)

      with self.assertRaises(errors_impl.InvalidArgumentError):
        t = py_builtins.len_(p)
        sess.run(t, {p: 1})

  @test_util.run_deprecated_v1
  def test_print_tensors(self):
    try:
      out_capturer = six.StringIO()
      sys.stdout = out_capturer
      with self.cached_session() as sess:
        sess.run(py_builtins.print_(constant_op.constant('test message'), 1))
        self.assertEqual(out_capturer.getvalue(), 'test message 1\n')
    finally:
      sys.stdout = sys.__stdout__

  @test_util.run_deprecated_v1
  def test_print_complex(self):
    try:
      out_capturer = six.StringIO()
      sys.stdout = out_capturer
      with self.cached_session() as sess:
        sess.run(
            py_builtins.print_(constant_op.constant('test message'), [1, 2]))
        self.assertEqual(out_capturer.getvalue(), 'test message [1, 2]\n')
    finally:
      sys.stdout = sys.__stdout__

  def test_range(self):
    self.assertListEqual(list(py_builtins.range_(3)), [0, 1, 2])
    self.assertListEqual(list(py_builtins.range_(1, 3)), [1, 2])
    self.assertListEqual(list(py_builtins.range_(2, 0, -1)), [2, 1])

  def test_range_tensor(self):
    with self.cached_session() as sess:
      r = py_builtins.range_(constant_op.constant(3))
      self.assertAllEqual(self.evaluate(r), [0, 1, 2])
      r = py_builtins.range_(1, constant_op.constant(3))
      self.assertAllEqual(self.evaluate(r), [1, 2])
      r = py_builtins.range_(2, 0, constant_op.constant(-1))
      self.assertAllEqual(self.evaluate(r), [2, 1])

  def test_range_tensor_empty_range(self):
    with self.session() as sess:
      r = py_builtins.range_(constant_op.constant(-3))
      self.assertAllEqual(self.evaluate(r), [])
      r = py_builtins.range_(5, constant_op.constant(2))
      self.assertAllEqual(self.evaluate(r), [])

  def test_enumerate(self):
    self.assertListEqual(
        list(py_builtins.enumerate_([3, 2, 1])), [(0, 3), (1, 2), (2, 1)])
    self.assertListEqual(
        list(py_builtins.enumerate_([3, 2, 1], 5)), [(5, 3), (6, 2), (7, 1)])
    self.assertListEqual(list(py_builtins.enumerate_([-8], -3)), [(-3, -8)])

  def test_enumerate_dataset(self):
    dataset = dataset_ops.DatasetV2.from_tensor_slices(['a', 'c'])
    start = constant_op.constant(20, dtype=dtypes.int64)
    dataset = py_builtins.enumerate_(dataset, start)
    iterator = dataset_ops.make_one_shot_iterator(dataset)

    with self.cached_session() as sess:
      self.assertAllEqual(self.evaluate(iterator.get_next()), (20, b'a'))
      self.assertAllEqual(self.evaluate(iterator.get_next()), (21, b'c'))

  def test_eval_in_original_context(self):

    def caller_1(lvl_delta):
      l = 1  # pylint:disable=unused-variable
      return py_builtins.eval_in_original_context(eval, ('l',), lvl_delta)

    def caller_2(lvl_delta):
      l = 2  # pylint:disable=unused-variable
      return caller_1(lvl_delta)

    def caller_3(lvl_delta):
      l = 3  # pylint:disable=unused-variable
      return caller_2(lvl_delta)

    self.assertEqual(caller_3(0), 1)
    self.assertEqual(caller_3(1), 2)
    self.assertEqual(caller_3(2), 3)

  def test_super_with_one_arg_in_original_context(self):
    test_case_self = self

    class TestBase(object):

      def plus_twenty(self, x):
        return x + 20

    class TestSubclass(TestBase):

      def plus_twenty(self, x):
        test_case_self.fail('This should never be called.')

      def one_arg(self):
        test_base_unbound = py_builtins.super_in_original_context(
            super, (TestSubclass,), 0)
        test_base = test_base_unbound.__get__(self, TestSubclass)
        return test_base.plus_twenty(1)

    tc = TestSubclass()
    self.assertEqual(tc.one_arg(), 21)

  def test_super_with_two_args_in_original_context(self):
    test_case_self = self

    class TestBase(object):

      def plus_twenty(self, x):
        return x + 20

    class TestSubclass(TestBase):

      def plus_twenty(self, x):
        test_case_self.fail('This should never be called.')

      def two_args(self):
        test_base = py_builtins.super_in_original_context(
            super, (TestSubclass, self), 0)
        return test_base.plus_twenty(1)

    tc = TestSubclass()
    self.assertEqual(tc.two_args(), 21)


if __name__ == '__main__':
  test.main()
