# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for tfx.components.trainer.executor."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import tensorflow as tf

from tfx.components.testdata.module_file import trainer_module
from tfx.components.trainer import executor
from tfx.proto import trainer_pb2
from tfx.utils import types
from google.protobuf import json_format


class ExecutorTest(tf.test.TestCase):

  def setUp(self):
    super(ExecutorTest, self).setUp()
    self.source_data_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'testdata')
    self.output_data_dir = os.path.join(
        os.environ.get('TEST_UNDECLARED_OUTPUTS_DIR', self.get_temp_dir()),
        self._testMethodName)

    # Create input dict.
    train_examples = types.TfxArtifact(type_name='ExamplesPath', split='train')
    train_examples.uri = os.path.join(self.source_data_dir,
                                      'transform/transformed_examples/train/')
    eval_examples = types.TfxArtifact(type_name='ExamplesPath', split='eval')
    eval_examples.uri = os.path.join(self.source_data_dir,
                                     'transform/transformed_examples/eval/')
    transform_output = types.TfxArtifact(type_name='TransformPath')
    transform_output.uri = os.path.join(self.source_data_dir,
                                        'transform/transform_output/')
    schema = types.TfxArtifact(type_name='ExamplesPath')
    schema.uri = os.path.join(self.source_data_dir, 'schema_gen/')

    self.input_dict = {
        'examples': [train_examples, eval_examples],
        'transform_output': [transform_output],
        'schema': [schema],
    }

    # Create output dict.
    self.model_exports = types.TfxArtifact(type_name='ModelExportPath')
    self.model_exports.uri = os.path.join(self.output_data_dir,
                                          'model_export_path')
    self.output_dict = {'output': [self.model_exports]}

    # Create exec properties skeleton.
    self.exec_properties = {
        'train_args':
            json_format.MessageToJson(trainer_pb2.TrainArgs(num_steps=1000)),
        'eval_args':
            json_format.MessageToJson(trainer_pb2.EvalArgs(num_steps=500)),
        'warm_starting':
            False,
    }

    self.module_file = os.path.join(self.source_data_dir, 'module_file',
                                    'trainer_module.py')
    self.trainer_fn = '%s.%s' % (trainer_module.trainer_fn.__module__,
                                 trainer_module.trainer_fn.__name__)

  def _verify_model_exports(self):
    self.assertTrue(
        tf.gfile.Exists(os.path.join(self.model_exports.uri, 'eval_model_dir')))
    self.assertTrue(
        tf.gfile.Exists(
            os.path.join(self.model_exports.uri, 'serving_model_dir')))

  def test_do_with_module_file(self):
    self.exec_properties['module_file'] = self.module_file
    trainer_executor = executor.Executor()
    trainer_executor.Do(
        input_dict=self.input_dict,
        output_dict=self.output_dict,
        exec_properties=self.exec_properties)
    self._verify_model_exports()

  def test_do_with_trainer_fn(self):
    self.exec_properties['trainer_fn'] = self.trainer_fn
    trainer_executor = executor.Executor()
    trainer_executor.Do(
        input_dict=self.input_dict,
        output_dict=self.output_dict,
        exec_properties=self.exec_properties)
    self._verify_model_exports()

  def test_do_with_no_trainer_fn(self):
    trainer_executor = executor.Executor()
    with self.assertRaises(ValueError):
      trainer_executor.Do(
          input_dict=self.input_dict,
          output_dict=self.output_dict,
          exec_properties=self.exec_properties)

  def test_do_with_duplicate_trainer_fn(self):
    self.exec_properties['module_file'] = self.module_file
    self.exec_properties['trainer_fn'] = self.trainer_fn
    trainer_executor = executor.Executor()
    with self.assertRaises(ValueError):
      trainer_executor.Do(
          input_dict=self.input_dict,
          output_dict=self.output_dict,
          exec_properties=self.exec_properties)


if __name__ == '__main__':
  tf.test.main()
