import pytest
from abulafia.task_specs import ImageClassification
from toloka.client import TolokaClient
import toloka.client as toloka


@pytest.fixture
def dummy_client():

    return TolokaClient('XXX', 'SANDBOX')


@pytest.fixture
def test_task(dummy_client):

    return ImageClassification(configuration='data/detect_text.yaml',
                               client=dummy_client,
                               test=True)


class TestTask:

    def test_condition(self, test_task):

        assert test_task.test is True

    def test_name(self, test_task):

        assert test_task.name == 'detect_text'

    def test_project_type(self, test_task):

        assert isinstance(test_task.project, toloka.Project)

    def test_project_desc_type(self, test_task):

        assert isinstance(test_task.project.public_description, str)

    def test_project_conf_type(self, test_task):

        assert isinstance(test_task.conf, dict)

    def test_project_client_type(self, test_task):

        assert isinstance(test_task.client, TolokaClient)

    def test_project_data_conf(self, test_task):

        assert isinstance(test_task.data_conf, dict)

    def test_project_proj_conf(self, test_task):

        assert isinstance(test_task.project_conf, dict)

    def test_project_action_conf(self, test_task):

        assert isinstance(test_task.action_conf, dict) or isinstance(test_task.action_conf, type(None))

    def test_project_pool_conf(self, test_task):

        assert isinstance(test_task.pool_conf, dict)

    def test_project_train_conf(self, test_task):

        assert isinstance(test_task.train_conf, dict) or isinstance(test_task.train_conf, type(None))

    def test_project_qual_conf(self, test_task):

        assert isinstance(test_task.qual_conf, dict) or isinstance(test_task.qual_conf, type(None))

    def test_training_type(self, test_task):

        assert isinstance(test_task.training, toloka.Training) or isinstance(test_task.training, type(None))

    def test_pool_type(self, test_task):

        assert isinstance(test_task.pool, toloka.Pool)

    def test_tasks_type(self, test_task):

        assert isinstance(test_task.tasks, list)

    def test_tasks_object_types(self, test_task):

        assert all(isinstance(x, toloka.Task) for x in test_task.tasks)


class TestProject:

    def test_project_public_name(self, test_task):

        assert test_task.project.public_name == 'Check if an image contains text, letters or ' \
                                                'numbers'

    def test_project_public_description(self, test_task):

        assert test_task.project.public_description == 'Look at diagrams from science textbooks ' \
                                                       'and state if they contain text, letters ' \
                                                       'or numbers.'

    def test_project_task_spec(self, test_task):

        # Build a task interface similar to the one defined in data/detect_text.yaml
        task_spec = toloka.project.task_spec.TaskSpec(input_spec={'image': toloka.project.UrlSpec(required=True,
                                                                                                  hidden=False)},
                                                      output_spec={'result': toloka.project.BooleanSpec(required=True,
                                                                                                        hidden=False,
                                                                                                        allowed_values=None)},
                                                      view_spec=toloka.project.TemplateBuilderViewSpec(settings=None,
                                                                                                       config=toloka.project.template_builder.TemplateBuilder(
                                                                                                           view=toloka.project.template_builder.ListViewV1(items=[
                                                                                                               toloka.project.template_builder.ImageViewV1(url=toloka.project.template_builder.InputData(path='image', default=None), full_height=True, max_width=None, min_width=None, no_border=None, no_lazy_load=None, popup=None, ratio=None, rotatable=True, scrollable=None, hint=None, label=None, validation=None, version='1.0.0'),
                                                                                                               toloka.project.template_builder.TextViewV1(content='Does the diagram contain text, letters or numbers?', hint=None, label=None, validation=None, version='1.0.0'),
                                                                                                               toloka.project.template_builder.ButtonRadioGroupFieldV1(data=toloka.project.template_builder.OutputData(path='result', default=None),
                                                                                                                                                                       options=[toloka.project.template_builder.GroupFieldOption(value=True, label='Yes', hint=None),
                                                                                                                                                                                toloka.project.template_builder.GroupFieldOption(value=False, label='No', hint=None)], hint=None, label=None, validation=toloka.project.template_builder.RequiredConditionV1(data=None, hint='You must choose one response.', version='1.0.0'), version='1.0.0')], direction=None, size=None, hint=None, label=None, validation=None, version='1.0.0'),
                                                                                                           plugins=[toloka.project.template_builder.TolokaPluginV1(layout=toloka.project.template_builder.TolokaPluginV1.TolokaPluginLayout(kind='scroll', task_width=500), notifications=None, version='1.0.0'),
                                                                                                                    toloka.project.template_builder.HotkeysPluginV1(key_1=toloka.project.template_builder.SetActionV1(data=toloka.project.template_builder.OutputData(path='result', default=None), payload=True, version='1.0.0'),
                                                                                                                                                                    key_2=toloka.project.template_builder.SetActionV1(data=toloka.project.template_builder.OutputData(path='result', default=None), payload=False, version='1.0.0'), version='1.0.0')], vars=None), core_version='1.0.0', infer_data_spec=False))

        assert test_task.project.task_spec == task_spec

    def test_project_public_instructions(self, test_task):

        assert test_task.project.public_instructions == 'Check if an image contains text, ' \
                                                        'letters or numbers.'

    def test_project_quality_control(self, test_task):

        assert test_task.project.quality_control is None

    def test_project_metadata(self, test_task):

        assert test_task.project.metadata is None


class TestPool:

    def test_pool_private_name(self, test_task):

        assert test_task.pool.private_name == 'Detect text'

    def test_pool_adult_content(self, test_task):

        assert test_task.pool.may_contain_adult_content is False

    def test_pool_reward(self, test_task):

        assert test_task.pool.reward_per_assignment == 0.034

    def test_pool_max_duration(self, test_task):

        assert test_task.pool.assignment_max_duration_seconds == 600

    def test_pool_default_overlap_suite(self, test_task):

        assert test_task.pool.defaults.default_overlap_for_new_task_suites == 1

    def test_pool_default_overlap_task(self, test_task):

        assert test_task.pool.defaults.default_overlap_for_new_tasks == 1

    def test_pool_auto_accept(self, test_task):

        assert test_task.pool.auto_accept_solutions is True

    def test_pool_filter(self, test_task):

        # Reconstruct the filter for clients
        filter_defs = [(toloka.filter.ClientType(operator=toloka.primitives.operators.IdentityOperator('EQ'), value='TOLOKA_APP')),
                       (toloka.filter.ClientType(operator=toloka.primitives.operators.IdentityOperator('EQ'), value='BROWSER'))]

        pool_filter = toloka.filter.FilterOr(filter_defs)

        assert test_task.pool.filter == pool_filter

    def test_quality_control(self, test_task):

        # Reconstruct the quality control rules
        qual_control = toloka.quality_control.QualityControl(training_requirement=None,
                                                             configs=[toloka.quality_control.QualityControl.QualityControlConfig(
                                                                 rules=[toloka.quality_control.QualityControl.QualityControlConfig.RuleConfig(
                                                                     action=toloka.actions.RestrictionV2(scope='PROJECT',
                                                                                                         duration=7,
                                                                                                         duration_unit='DAYS',
                                                                                                         private_comment='Fast responses'),
                                                                     conditions=[toloka.conditions.FastSubmittedCount(operator=toloka.primitives.operators.CompareOperator('GT'),
                                                                                                                      value=3)])],
                                                                 collector_config=toloka.collectors.AssignmentSubmitTime(fast_submit_threshold_seconds=2,
                                                                                                                         history_size=5)),
                                                                 toloka.quality_control.QualityControl.QualityControlConfig(
                                                                     rules=[toloka.quality_control.QualityControl.QualityControlConfig.RuleConfig(
                                                                         action=toloka.actions.RestrictionV2(scope='PROJECT',
                                                                                                             duration=7,
                                                                                                             duration_unit='DAYS',
                                                                                                             private_comment='Skipped assignments'),
                                                                         conditions=[toloka.conditions.SkippedInRowCount(operator=toloka.primitives.operators.CompareOperator('GT'),
                                                                                                                         value=3)])],
                                                                 collector_config=toloka.collectors.SkippedInRowAssignments())],
                                                             checkpoints_config=None
                                                             )

        assert test_task.pool.quality_control == qual_control
