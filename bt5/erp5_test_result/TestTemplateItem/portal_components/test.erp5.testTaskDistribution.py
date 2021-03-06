from Products.ERP5Type.tests.ERP5TypeTestCase import ERP5TypeTestCase
import json 
from time import sleep
from DateTime import DateTime

class TestTaskDistribution(ERP5TypeTestCase):
  def afterSetUp(self):
    self.portal = portal = self.getPortalObject()
    self.test_node_module = self.portal.getDefaultModule(portal_type = 'Test Node Module')
    self.test_suite_module = self.portal.getDefaultModule(portal_type = 'Test Suite Module')
    self.test_result_module = self.portal.getDefaultModule(portal_type = 'Test Result Module')
    self.test_suite = self.portal.getDefaultModule(portal_type = 'Test Suite')
    self.tool = tool = self.portal.portal_task_distribution
    if getattr(tool, "TestTaskDistribution", None) is None:
      tool.newContent(id="TestTaskDistribution",
           portal_type="ERP5 Project Unit Test Distributor")
    tool.TestTaskDistribution.setMaxTestSuite(None)
    if getattr(tool, "TestPerformanceTaskDistribution", None) is None:
      tool.newContent(id="TestPerformanceTaskDistribution",
           portal_type="Cloud Performance Unit Test Distributor")
    if getattr(tool, "TestScalabilityTaskDistribution", None) is None:
      tool.newContent(id="TestScalabilityTaskDistribution",
           portal_type="ERP5 Scalability Distributor")
    self.distributor = tool.TestTaskDistribution
    self.performance_distributor = tool.TestPerformanceTaskDistribution
    self.scalability_distributor = tool.TestScalabilityTaskDistribution
    if getattr(portal, "test_test_node_module", None) is None:
      portal.newContent(portal_type="Test Node Module",
                        id="test_test_node_module")
    if getattr(portal, "test_test_suite_module", None) is None:
      portal.newContent(portal_type="Test Suite Module",
                        id="test_test_suite_module")
    self.test_suite_module = portal.test_test_suite_module
    self.test_node_module = portal.test_test_node_module
    self.test_suite_module.manage_delObjects(ids=[
      x for x in self.test_suite_module.objectIds()])
    self.test_node_module.manage_delObjects(ids=[
      x for x in self.test_node_module.objectIds()])

    original_class = self.distributor.__class__
    original_scalability_class = self.scalability_distributor.__class__
    original_performance_class = self.performance_distributor.__class__

    self._original_getTestNodeModule = original_class._getTestNodeModule
    def _getTestNodeModule(self):
      return self.getPortalObject().test_test_node_module
    original_class._getTestNodeModule = _getTestNodeModule
    original_scalability_class._getTestNodeModule = _getTestNodeModule
    original_performance_class._getTestNodeModule = _getTestNodeModule

    self._original_getTestSuiteModule = original_class._getTestSuiteModule
    def _getTestSuiteModule(self):
      return self.getPortalObject().test_test_suite_module
    original_class._getTestSuiteModule = _getTestSuiteModule
    original_scalability_class._getTestSuiteModule = _getTestSuiteModule
    original_performance_class._getTestSuiteModule = _getTestSuiteModule

    self._cleanupTestResult()

  def beforeTearDown(self):
    original_class = self.distributor.__class__
    original_scalability_class = self.scalability_distributor.__class__
    original_performance_class = self.performance_distributor.__class__
    
    original_class._getTestNodeModule = self._original_getTestNodeModule
    original_class._getTestSuiteModule = self._original_getTestSuiteModule
    original_scalability_class._getTestNodeModule = self._original_getTestNodeModule
    original_scalability_class._getTestSuiteModule = self._original_getTestSuiteModule
    original_performance_class._getTestNodeModule = self._original_getTestNodeModule
    original_performance_class._getTestSuiteModule = self._original_getTestSuiteModule



  def _createTestNode(self, quantity=1, reference_correction=0,
                      specialise_value=None):
    if specialise_value is None:
      specialise_value = self.distributor
    test_node_list = []
    for i in range(quantity):
      test_node = self.test_node_module.newContent(
        title = 'UnitTestNode %i' % (i + 1 + reference_correction),
        test_suite_max = 4,
        specialise_value = specialise_value,
        )
      test_node_list.append(test_node)
    return test_node_list

  def _createTestSuite(self,quantity=1,priority=1, reference_correction=0,
                       specialise_value=None, title=None, portal_type="Test Suite",
                       graph_coordinate="1", cluster_configuration='{ "test": {{ count }} }'):
    if title is None:
      title = ""
    if specialise_value is None:
      specialise_value = self.distributor
    test_suite_list = []
    for i in range(quantity):
      test_suite_title = "test suite %i" % (i + 1 + reference_correction)
      if title:
        test_suite_title += " %s" % title

      test_suite =  self.test_suite_module.newContent(
                    portal_type = portal_type,
                    title = test_suite_title,
                    test_suite_title = test_suite_title,
                    test_suite = 'B%i' % i,
                    int_index = priority,
                    specialise_value = specialise_value,
                   )

      test_suite.setClusterConfiguration(cluster_configuration)
      if portal_type == "Scalability Test Suite":
        test_suite.setGraphCoordinate(graph_coordinate)


      test_suite.newContent( portal_type= 'Test Suite Repository',
                        branch = 'master',
                        git_url = 'https://lab.nexedi.com/nexedi/erp5.git',
                        buildout_section_id  = 'erp5',
                        profile_path = 'software-release/software.cfg'
                        )
      test_suite.validate()
      test_suite_list.append(test_suite)
    return test_suite_list 

  def test_01_createTestNode(self):
    test_node = self._createTestNode()[0]
    self.assertEqual(test_node.getPortalType(), "Test Node")

  def test_02_createTestSuite(self):
    # Test Test Suite
    test_suite,  = self._createTestSuite()
    self.assertEquals(test_suite.getPortalType(), "Test Suite")
    self.assertEquals(test_suite.getSpecialise(), self.distributor.getRelativeUrl())
    # Test Scalability Test Suite
    scalability_test_suite,  = self._createTestSuite(
                                 portal_type="Scalability Test Suite",
                                 specialise_value = self.scalability_distributor
                               )
    self.assertEquals(scalability_test_suite.getPortalType(),
                       "Scalability Test Suite")
    self.assertEquals(scalability_test_suite.getSpecialise(),
                       self.scalability_distributor.getRelativeUrl())

  def _callOptimizeAlarm(self):
    self.portal.portal_alarms.task_distributor_alarm_optimize.activeSense()
    self.tic()

  def _callRestartStuckTestResultAlarm(self):
    self.portal.portal_alarms.test_result_alarm_restarted_stuck_test_result.activeSense()
    self.tic()

  def test_03_startTestSuiteWithOneTestNode(self):
    config_list = json.loads(self.distributor.startTestSuite(
                             title="COMP32-Node1"))
    self.assertEqual([], config_list)
    self._createTestSuite(quantity=3)
    self.tic()
    self._callOptimizeAlarm()
    config_list = json.loads(self.distributor.startTestSuite(
                             title="COMP32-Node1"))
    self.assertEqual(3, len(config_list))
    self.assertEqual(set(['B0','B1','B2']),
                      set([x['test_suite'] for x in config_list]))

  def test_04_startTestSuiteWithTwoTestNode(self):
    """
    When we have two test suites and we have two test nodes, we should have
    one test suite distributed per test node
    """
    config_list = json.loads(self.distributor.startTestSuite(
                             title="COMP32-Node1"))
    config_list = json.loads(self.distributor.startTestSuite(
                             title="COMP32-Node2"))
    self.assertEqual([], config_list)
    self._createTestSuite(quantity=2)
    self.tic()
    self._callOptimizeAlarm()
    def checkConfigListForTestNode(test_node_title):
      config_list = json.loads(self.distributor.startTestSuite(
                             title=test_node_title))
      self.assertEqual(1, len(config_list))
      return (test_node_title, set([x['test_suite'] for x in config_list]))
    config1 = checkConfigListForTestNode("COMP32-Node1")
    config2 = checkConfigListForTestNode("COMP32-Node2")
    self.assertTrue([config1, config2] in  [
                    [('COMP32-Node1',set([u'B0'])), ('COMP32-Node2',set([u'B1']))],
                    [('COMP32-Node1',set([u'B1'])), ('COMP32-Node2',set([u'B0']))]],
                    "%r" % ([config1, config2],))

  def test_04b_startTestSuiteOrder(self):
    """
    When we have many test suites associated to one test nodes, the method
    startTestSuite should give first test suites with oldest test results. Like
    this we stop using the random order that was unfair for unlucky peoples
    """
    config_list = json.loads(self.distributor.startTestSuite(
                             title="COMP42-Node1"))
    self.assertEqual([], config_list)
    self._createTestSuite(quantity=3)
    self.tic()
    self._callOptimizeAlarm()
    def getTestSuiteList():
      config_list = json.loads(self.distributor.startTestSuite(
                             title="COMP42-Node1"))
      return ["%s" % x["test_suite_title"] for x in config_list]
    # By default we have random order between test suites
    self.assertEquals(set(["test suite 1", "test suite 2", "test suite 3"]),
                      set(getTestSuiteList()))
    # Check that if test suite 1 and test suite 2 are recently processed,
    # then next work must be test suite 3
    def processTest(test_title, revision, start_count=2, stop_count=2):
      """start_count: number of test line to start
         stop_count: number of test line to stop
      """
      status_dict = {}
      test_result_path, revision = self._createTestResult(revision=revision,
        test_list=['testFoo', 'testBar'], test_title=test_title)
      if start_count:
        line_url, test = self.tool.startUnitTest(test_result_path)
      if start_count == 2:
        next_line_url, next_test = self.tool.startUnitTest(test_result_path)
        self.assertEqual(set(['testFoo', 'testBar']), set([test, next_test]))
      if stop_count:
        self.tool.stopUnitTest(line_url, status_dict)
      if stop_count == 2:
        self.tool.stopUnitTest(next_line_url, status_dict)
      test_result = self.portal.restrictedTraverse(test_result_path)
      if stop_count == 2:
        self.assertEquals(test_result.getSimulationState(), "stopped")
      else:
        self.assertEquals(test_result.getSimulationState(), "started")

    processTest("test suite 1", "r0=a")
    self.tic()
    sleep(1) # needed because creation date sql value does not record millesecond
    processTest("test suite 2", "r0=b")
    self.tic()
    sleep(1)
    self.assertEquals(getTestSuiteList()[0], "test suite 3")
    processTest("test suite 3", "r0=b")
    # after test suite 3, we now have to process test suite 1
    # since it is the oldest one
    self.tic()
    sleep(1)
    self.assertEquals(getTestSuiteList()[0], "test suite 1")
    processTest("test suite 1", "r0=c")
    # after test suite 1, we now have to process test suite 2
    # since it is the oldest one
    self.tic()
    sleep(1)
    self.assertEquals(getTestSuiteList()[0], "test suite 2")
    processTest("test suite 2", "r0=d")
    self.tic()
    sleep(1)
    # now let's say for any reason test suite 1 has been done
    processTest("test suite 1", "r0=e")
    self.tic()
    sleep(1)
    # we should then have by order 3, 2, 1
    self.assertEquals(["test suite 3", "test suite 2", "test suite 1"],
                      getTestSuiteList())
    # now launch all test of test 3, even if they are not finished yet
    processTest("test suite 3", "r0=f", stop_count=1)
    self.tic()
    sleep(1)
    self.assertEquals(["test suite 2", "test suite 1", "test suite 3"],
                      getTestSuiteList())
    # now launch partially tests of suite 2, it must have priority over
    # test 3, even if test 3 is older because all tests of test 3 are ongoing
    processTest("test suite 2", "r0=g", start_count=1, stop_count=0)
    self.tic()
    sleep(1)
    self.assertEquals(["test suite 1", "test suite 2", "test suite 3"],
                      getTestSuiteList())

  def _cleanupTestResult(self):
    self.tic()
    cleanup_state_list = ['started', 'stopped']
    test_list =  self.test_result_module.searchFolder(title='"TEST FOO" OR "test suite %"',
               simulation_state=cleanup_state_list)
    for test_result in test_list:
      if test_result.getSimulationState() in cleanup_state_list:
        test_result.cancel()
    self.tic()

  def _createTestResult(self, revision="r0=a,r1=a", node_title="Node0",
                              test_list=None, tic=1, allow_restart=False,
                              test_title="TEST FOO"):
    result =  self.tool.createTestResult(
                               "", revision, test_list or [], allow_restart,
                               test_title=test_title, node_title=node_title)
    # we commit, since usually we have a remote call only doing this
    (self.tic if tic else self.commit)()
    return result
    
  def test_05_createTestResult(self):
    """
    We will check the method createTestResult of task distribution tool
    """
    test_result_path, revision = self._createTestResult()
    self.assertEqual("r0=a,r1=a", revision)
    self.assertTrue(test_result_path.startswith("test_result_module/"))
    # If we ask again with another revision, we should get with previous
    # revision
    next_test_result_path, next_revision = self._createTestResult(
      revision="r0=a,r1=b", node_title="Node1")
    self.assertEqual(revision, next_revision)
    self.assertEqual(next_test_result_path, test_result_path)
    # Check if test result object is well created
    test_result = self.getPortalObject().unrestrictedTraverse(test_result_path)
    self.assertEqual("Test Result", test_result.getPortalType())
    self.assertEqual(0, len(test_result.objectValues(
                             portal_type="Test Result Line")))
    # now check that if we pass list of test, new lines will be created
    next_test_result_path, next_revision = self._createTestResult(
      test_list=['testFoo', 'testBar'])
    self.assertEqual(next_test_result_path, test_result_path)
    line_list = test_result.objectValues(portal_type="Test Result Line")
    self.assertEqual(2, len(line_list))
    self.assertEqual(set(['testFoo', 'testBar']), set([x.getTitle() for x
                      in line_list]))
    line_url, test = self.tool.startUnitTest(test_result_path)
    result = self._createTestResult(test_list=['testFoo', 'testBar'])
    self.assertEqual((test_result_path, revision), result)
    next_line_url, next_test = self.tool.startUnitTest(test_result_path)
    # all tests of this test suite are now started, stop affecting test node to it
    result = self._createTestResult(test_list=['testFoo', 'testBar'])
    self.assertEqual(None, result)
    # though, is we restart one line, we will have affectation again
    self.portal.restrictedTraverse(line_url).redraft()
    self.commit()
    result = self._createTestResult(test_list=['testFoo', 'testBar'])
    self.assertEqual((test_result_path, revision), result)
    next_line_url, next_test = self.tool.startUnitTest(test_result_path)

  def test_05b_createTestResultDoesNotReexecuteRevision(self):
    """
    Make sure to no retest former revision. This scenario must work
    - testnode call createTestResult with revision r0=b. Test is executed
    - By hand is created test with revision r0=a (to make testnode checking old
      revision). Test is executed
    - if testnode ask again for r0=b, no test must be created
    - if testnode ask for r0=c, then usual test is created/executed
    """
    # launch test r0=b
    test_result_path, revision = self._createTestResult(revision="r0=b", test_list=["testFoo"])
    line_url, test = self.tool.startUnitTest(test_result_path)
    status_dict = {}
    self.tool.stopUnitTest(line_url, status_dict)
    test_result = self.getPortalObject().unrestrictedTraverse(test_result_path)
    self.assertEqual("stopped", test_result.getSimulationState())
    # launch test r0=a
    test_result_path, revision = self._createTestResult(revision="r0=a", test_list=["testFoo"])
    line_url, test = self.tool.startUnitTest(test_result_path)
    self.tool.stopUnitTest(line_url, status_dict)
    test_result = self.getPortalObject().unrestrictedTraverse(test_result_path)
    self.assertEqual("stopped", test_result.getSimulationState())
    # Make sure we do not relaunch test with revision r0=b
    result = self._createTestResult(revision="r0=b", test_list=["testFoo"])
    self.assertEqual(None, result)
    # launch test r0=c
    test_result_path, revision = self._createTestResult(revision="r0=c", test_list=["testFoo"])
    line_url, test = self.tool.startUnitTest(test_result_path)
    self.tool.stopUnitTest(line_url, status_dict)
    test_result = self.getPortalObject().unrestrictedTraverse(test_result_path)
    self.assertEqual("stopped", test_result.getSimulationState())

  def test_06_startStopUnitTest(self):
    """
    We will check methods startUnitTest/stopUnitTest of task distribution tool
    """
    test_result_path, revision = self._createTestResult(
      test_list=['testFoo', 'testBar'])
    test_result = self.getPortalObject().unrestrictedTraverse(test_result_path)
    line_url, test = self.tool.startUnitTest(test_result_path)
    next_line_url, next_test = self.tool.startUnitTest(test_result_path)
    # once all tests are affected, stop affecting resources on this test result
    next_result = self.tool.startUnitTest(test_result_path)
    self.assertEqual(None, next_result)
    # first launch, we have no time optimisations, so tests are
    # launched in alphabetical order
    self.assertEqual(['testBar', 'testFoo'], [test, next_test])
    status_dict = {}
    self.tool.stopUnitTest(line_url, status_dict)
    self.tool.stopUnitTest(next_line_url, status_dict)
    line = self.portal.unrestrictedTraverse(line_url)
    def checkDuration(line):
      duration = getattr(line, "duration", None)
      self.assertTrue(isinstance(duration, float))
      self.assertTrue(duration>0)
    checkDuration(line)
    next_line = self.portal.unrestrictedTraverse(next_line_url)
    checkDuration(next_line)
    # Make sure second test takes more time
    next_line.duration = line.duration + 1
    # So if we launch another unit test, it will process first the
    # one which is the slowest
    self.assertEqual("stopped", test_result.getSimulationState())
    self.tic()
    next_test_result_path, revision = self._createTestResult(
      test_list=['testFoo', 'testBar'], revision="r0=a,r1=b")
    self.assertNotEquals(next_test_result_path, test_result_path)
    line_url, test = self.tool.startUnitTest(next_test_result_path)
    next_line_url, next_test = self.tool.startUnitTest(next_test_result_path)
    self.assertEqual(['testFoo', 'testBar'], [test, next_test])

  def test_06b_restartStuckTest(self):
    """
    Check if a test result line is not stuck in 'started', if so, redraft
    if with alarm to let opportunity of another test node to work on it
    """
    test_result_path, revision = self._createTestResult(
      test_list=['testFoo', 'testBar'])
    test_result = self.portal.unrestrictedTraverse(test_result_path)
    line_url, test = self.tool.startUnitTest(test_result_path)
    now = DateTime()
    def checkTestResultLine(expected):
      line_list = test_result.objectValues(portal_type="Test Result Line")
      found_list = [(x.getTitle(), x.getSimulationState()) for x in line_list]
      found_list.sort(key=lambda x: x[0])
      self.assertEqual(expected, found_list)
    checkTestResultLine([('testBar', 'started'), ('testFoo', 'draft')])
    self._callRestartStuckTestResultAlarm()
    checkTestResultLine([('testBar', 'started'), ('testFoo', 'draft')])
    line_url, test = self.tool.startUnitTest(test_result_path)
    checkTestResultLine([('testBar', 'started'), ('testFoo', 'started')])
    self._callRestartStuckTestResultAlarm()
    checkTestResultLine([('testBar', 'started'), ('testFoo', 'started')])
    # now let change history to do like if a test result line was started
    # a long time ago
    line = self.portal.restrictedTraverse(line_url)
    for history_line in line.workflow_history["test_result_workflow"]:
      if history_line['action'] == 'start':
        history_line['time'] = now - 1
    self._callRestartStuckTestResultAlarm()
    checkTestResultLine([('testBar', 'started'), ('testFoo', 'draft')])

  def test_07_reportTaskFailure(self):
    test_result_path, revision = self._createTestResult(node_title="Node0")
    next_test_result_path, revision = self._createTestResult(node_title="Node1")
    self.assertEqual(test_result_path, next_test_result_path)
    test_result = self.getPortalObject().unrestrictedTraverse(test_result_path)
    self.assertEqual("started", test_result.getSimulationState())
    node_list = test_result.objectValues(portal_type="Test Result Node",
                                         sort_on=[("title", "ascending")])
    def checkNodeState(first_state, second_state):
      self.assertEqual([("Node0", first_state), ("Node1", second_state)],
              [(x.getTitle(), x.getSimulationState()) for x in node_list])
    checkNodeState("started", "started")
    self.tool.reportTaskFailure(test_result_path, {}, "Node0")
    self.assertEqual("started", test_result.getSimulationState())
    checkNodeState("failed", "started")
    self.tool.reportTaskFailure(test_result_path, {}, "Node1")
    self.assertEqual("failed", test_result.getSimulationState())
    checkNodeState("failed", "failed")

  def test_08_checkWeCanNotCreateTwoTestResultInParallel(self):
    """
    To avoid duplicates of test result when several testnodes works on the
    same suite, we create test and we immediately reindex it. So we must
    be able to find new test immediately after.
    """
    test_result_path, revision = self._createTestResult(
                                      node_title="Node0", tic=0)
    next_test_result_path, revision = self._createTestResult(
                                      node_title="Node1", tic=0)
    self.assertEqual(test_result_path, next_test_result_path)

  def _checkCreateTestResultAndAllowRestart(self, tic=False):
    test_result_path, revision = self._createTestResult(test_list=["testFoo"])
    line_url, test = self.tool.startUnitTest(test_result_path)
    status_dict = {}
    self.tool.stopUnitTest(line_url, status_dict)
    if tic:
      self.tic()
    test_result = self.getPortalObject().unrestrictedTraverse(test_result_path)
    self.assertEqual("stopped", test_result.getSimulationState())
    self.assertEqual(None, self._createTestResult(test_list=["testFoo"]))
    next_test_result_path, next_revision = self._createTestResult(
      test_list=["testFoo"], allow_restart=True)
    self.assertTrue(next_test_result_path != test_result_path)

  def test_09_checkCreateTestResultAndAllowRestartWithoutTic(self):
    """
    The option allow restart of createTestResult enable to possibility to
    always launch tests even if the given revision is already tested.

    Is this really useful and used ?
    """
    self._checkCreateTestResultAndAllowRestart()    

  def test_09b_checkCreateTestResultAndAllowRestartWithTic(self):
    """
    The option allow restart of createTestResult enable to possibility to
    always launch tests even if the given revision is already tested. We
    try here with reindex after stopUnitTest
    """
    self._checkCreateTestResultAndAllowRestart(tic=True)

  def test_10_cancelTestResult(self):
    pass

  def test_10b_generateConfiguration(self):
    """
    It shall be possible on a test suite to define configuration we would like
    to use to create slapos instance.
    """
    test_suite, = self._createTestSuite(cluster_configuration=None)
    self.tic()
    self.assertEquals('{"configuration_list": [{}]}', self.distributor.generateConfiguration(test_suite.getTitle()))
    test_suite.setClusterConfiguration("{'foo': 3}")
    self.assertEquals('{"configuration_list": [{}]}', self.distributor.generateConfiguration(test_suite.getTitle()))
    test_suite.setClusterConfiguration('{"foo": 3}')
    self.assertEquals('{"configuration_list": [{"foo": 3}]}', self.distributor.generateConfiguration(test_suite.getTitle()))

  def _checkTestSuiteAggregateList(self, *args):
    self.tic()
    self._callOptimizeAlarm()
    for test_node, aggregate_list in args:
      test_note_aggregate_title_list = [x.split(" ")[-1] for x in test_node.getAggregateTitleList()]
      self.assertEqual(set(test_note_aggregate_title_list),
        set(aggregate_list),
        "incorrect aggregate for %r, got %r instead of %r" % \
        (test_node.getTitle(), test_note_aggregate_title_list, aggregate_list))

  def test_11_checkERP5ProjectOptimizationIsStable(self):
    """
    When we have two test suites and we have two test nodes, we should have
    one test suite distributed per test node
    """
    test_node_one, test_node_two = self._createTestNode(quantity=2)
    test_suite_one = self._createTestSuite(reference_correction=+0,
                              title='one')[0]
    self._createTestSuite(reference_correction=+1,
                              title='two')[0].getRelativeUrl()
    self.tic()
    self._callOptimizeAlarm()
    check = self._checkTestSuiteAggregateList
    check([test_node_one, ["one"]],
          [test_node_two, ["two"]])
    # first test suite is invalidated, so it should be removed from nodes, 
    # but this should not change assignment of second test suite
    test_suite_one.invalidate()
    check([test_node_one, []],
          [test_node_two, ["two"]])
    # an additional test node is added, with lower title, this should
    # still not change anyting
    test_node_zero = self._createTestNode(quantity=1, reference_correction=-1)[0]
    check([test_node_zero, []],
          [test_node_one, []],
          [test_node_two, ["two"]])
    # test suite one is validated again, it is installed on first
    # available test node
    test_suite_one.validate()
    check([test_node_zero, ["one"]],
          [test_node_one, []],
          [test_node_two, ["two"]])
    # for some reasons, test_node two is dead, so the work is distributed
    # to remaining test nodes
    test_node_two.invalidate()
    check([test_node_zero, ["one"]],
          [test_node_one, ["two"]],
          [test_node_two, []])
    # we add another test suite, since all test node already have one
    # test suite, the new test suite is given to first available one
    self._createTestSuite(reference_correction=+2,
                                title='three')[0].getRelativeUrl()
    check([test_node_zero, ["one", "three"]],
          [test_node_one, ["two"]],
          [test_node_two, []])
    # test node two is coming back. To have better repartition of work,
    # move some work from overloaded test node to less busy test node, while
    # still trying to move as less test suite as possible (here only one)
    test_node_two.validate()
    check([test_node_zero, ["three"]],
          [test_node_one, ["two"]],
          [test_node_two, ["one"]])
    # Now let's create a test suite needing between 1 to 2 test nodes
    # Make sure additional work is added without moving other test suites
    self._createTestSuite(reference_correction=+3,
                             priority=4, title='four')[0].getRelativeUrl()
    check([test_node_zero, ["three", "four"]],
          [test_node_one, ["two", "four"]],
          [test_node_two, ["one"]])
    # Now let's create a a test suite needing 1 nodes
    # to make sure test nodes with less work get the work first
    test_suite_five = self._createTestSuite(reference_correction=+4,
                             title='five')[0]
    check([test_node_zero, ["three", "four"]],
          [test_node_one, ["two", "four"]],
          [test_node_two, ["one", "five"]])
    # Now let's create another test suite needing between 2 to 3 test nodes
    # and increase priority of one suite to make all test nodes almost satured
    test_suite_five.setIntIndex(7)
    self._createTestSuite(reference_correction=+5,
                             priority=7, title='six')
    check([test_node_zero, ["three", "four","five", "six"]],
          [test_node_one, ["two", "four", "five", "six"]],
          [test_node_two, ["one", "five", "six"]])
    # Then, check what happens if all nodes are more than saturated
    # with a test suite needing between 3 to 5 test nodes
    self._createTestSuite(reference_correction=+6,
                             priority=9, title='seven')
    check([test_node_zero, ["three", "four", "five", "six"]],
          [test_node_one, ["two", "four", "five", "six"]],
          [test_node_two, ["one", "seven", "five", "six"]])
    # No place any more, adding more test suite has no consequence
    # we need 5*2 + 3*2  + 2*1 + 1*3 => 21 slots
    self._createTestSuite(reference_correction=+7,
                             priority=9, title='height')
    check([test_node_zero, ["three", "four", "five", "six"]],
          [test_node_one, ["two", "four", "five", "six"]],
          [test_node_two, ["one", "seven", "five", "six"]])
    # free some place by removing a test suite
    # make sure free slots are fairly distributed to test suite having
    # less test nodes
    # We remove 3 slots, so we would need 18 slots
    test_suite_five.invalidate()
    check([test_node_zero, ["three", "four", "height", "six"]],
          [test_node_one, ["two", "four", "seven" , "six"]],
          [test_node_two, ["one", "seven", "height" , "six"]])
    # Check that additional test node would get work for missing assignments
    # No move a test suite is done since in average we miss slots
    test_node_three, = self._createTestNode(reference_correction=2)
    check([test_node_zero, ["three", "four", "height", "six"]],
          [test_node_one, ["two", "four", "seven" , "six"]],
          [test_node_two, ["one", "seven", "height" , "six"]],
          [test_node_three, ["seven", "height"]])
    # With even more test node, check that we move some work to less
    # busy test nodes
    test_node_four, = self._createTestNode(reference_correction=3)
    test_node_five, = self._createTestNode(reference_correction=4)
    check([test_node_zero, ["three", "six", "height"]],
          [test_node_one, ["two", "six", "seven"]],
          [test_node_two, ["one", "seven", "height"]],
          [test_node_three, ["four", "seven", "height"]],
          [test_node_four, ["four", "seven", "height"]],
          [test_node_five, ["six", "seven", "height"]])
    test_node_six, = self._createTestNode(reference_correction=5)
    test_node_seven, = self._createTestNode(reference_correction=6)
    check([test_node_zero, ["three", "height"]],
          [test_node_one, ["two", "seven"]],
          [test_node_two, ["one", "height"]],
          [test_node_three, ["seven", "height"]],
          [test_node_four, ["four", "seven", "height"]],
          [test_node_five, ["six", "seven", "height"]],
          [test_node_six, ["six", "seven"]],
          [test_node_seven, ["four", "six"]])

  def test_11b_checkERP5ProjectDistributionWithCustomMaxQuantity(self):
    """
    Check that the property max_test_suite on the distributor could
    be used to customize the quantity of test suite affected per test node
    """
    test_node, = self._createTestNode(quantity=1)
    test_suite_list = self._createTestSuite(quantity=5)
    self.tool.TestTaskDistribution.setMaxTestSuite(None)
    self.tic()
    self._callOptimizeAlarm()
    self.assertEqual(4, len(set(test_node.getAggregateList())))
    self.tool.TestTaskDistribution.setMaxTestSuite(1)
    self._callOptimizeAlarm()
    self.assertEqual(1, len(set(test_node.getAggregateList())))
    self.tool.TestTaskDistribution.setMaxTestSuite(10)
    self._callOptimizeAlarm()
    self.assertEqual(5, len(set(test_node.getAggregateList())))
    self.assertEqual(set(test_node.getAggregateList()), 
                     set([x.getRelativeUrl() for x in test_suite_list]))

  def test_12_checkCloudPerformanceOptimizationIsStable(self):
    """
    When we have two test suites and we have two test nodes, we should have
    one test suite distributed per test node
    """
    test_node_one, test_node_two = self._createTestNode(quantity=2,
                               specialise_value=self.performance_distributor)
    test_suite_one, = self._createTestSuite(
                          title='one', specialise_value=self.performance_distributor)
    self._createTestSuite(title='two', reference_correction=+1,
                          specialise_value=self.performance_distributor)
    self.tic()
    self._callOptimizeAlarm()
    check = self._checkTestSuiteAggregateList
    check([test_node_one, ["one", "two"]],
          [test_node_two, ["one", "two"]])
    # first test suite is invalidated, so it should be removed from nodes, 
    # but this should not change assignment of second test suite
    test_suite_one.invalidate()
    check([test_node_one, ["two"]],
          [test_node_two, ["two"]])
    # an additional test node is added, with lower title, it should
    # get in any case all test suite
    test_node_zero = self._createTestNode(quantity=1, reference_correction=-1,
                            specialise_value=self.performance_distributor)[0]
    check([test_node_zero, ["two"]],
          [test_node_one, ["two"]],
          [test_node_two, ["two"]])
    # test suite one is validating again, it is installed on first
    # available test node
    test_suite_one.validate()
    check([test_node_zero, ["one", "two"]],
          [test_node_one, ["one", "two"]],
          [test_node_two, ["one", "two"]])
    # for some reasons, test_node two is dead, this has no consequence
    # for others
    test_node_two.invalidate()
    check([test_node_zero, ["one", "two"]],
          [test_node_one, ["one", "two"]],
          [test_node_two, ["one", "two"]])
    # we add another test suite, all test nodes should run it, except
    # test_node_two which is dead
    self._createTestSuite(title="three", reference_correction=+2,
                             specialise_value=self.performance_distributor)
    check([test_node_zero, ["one", "two", "three"]],
          [test_node_one, ["one", "two", "three"]],
          [test_node_two, ["one", "two"]])
    # test node two is coming back. It should run all test suites
    test_node_two.validate()
    check([test_node_zero, ["one", "two", "three"]],
          [test_node_one, ["one", "two", "three"]],
          [test_node_two, ["one", "two", "three"]])
    # now we are going to

  def test_13_startTestSuiteWithOneTestNodeAndPerformanceDistributor(self):
    config_list = json.loads(self.performance_distributor.startTestSuite(
                             title="COMP32-Node1"))
    self.assertEqual([], config_list)
    self._createTestSuite(quantity=2, 
                          specialise_value=self.performance_distributor)
    self.tic()
    self._callOptimizeAlarm()
    config_list = json.loads(self.performance_distributor.startTestSuite(
                             title="COMP32-Node1"))
    self.assertEqual(2, len(config_list))
    self.assertEqual(set(['test suite 1-COMP32-Node1',
                           'test suite 2-COMP32-Node1']),
                      set([x['test_suite_title'] for x in config_list]))

  def test_14_subscribeNodeCheckERP5ScalabilityDistributor(self):
    """
    Check test node subscription.
    """
    test_node_module = self.test_node_module
    
    # Generate informations for nodes to subscribe
    nodes = dict([("COMP%d-Scalability-Node_test14" %i, "COMP-%d" %i) for i in range(0,5)])
    # Subscribe nodes
    for node_title in nodes.keys():
      self.scalability_distributor.subscribeNode(node_title, computer_guid=nodes[node_title])
    self.tic()
    # Get validated test nodes
    test_nodes = test_node_module.searchFolder(validation_state = 'validated')
    # Get test node title list
    test_node_titles = [x.getTitle() for x in test_nodes]
    # Check subscription
    for node_title in nodes.keys():
      self.assertTrue(node_title in test_node_titles)
    # Check ping date
    # TODO..

  def test_15_optimizeConfigurationCheckElectionERP5ScalabilityDistributor(self):
    """
    Check optimizeConfiguration method of scalability distributor.
     - Check the master election
    """
    test_node_module = self.test_node_module
    
    ## 1 (check election, classic)
    # Subscribe nodes
    self.scalability_distributor.subscribeNode("COMP1-Scalability-Node1", computer_guid="COMP-1")
    self.scalability_distributor.subscribeNode("COMP2-Scalability-Node2", computer_guid="COMP-2")
    self.scalability_distributor.subscribeNode("COMP3-Scalability-Node3", computer_guid="COMP-3")
    self.scalability_distributor.subscribeNode("COMP4-Scalability-Node4", computer_guid="COMP-4")
    self.tic()
    # Check test node election
    def getMasterAndSlaveNodeList():
      """
      Optimize the configuration and return which nodes are master/slave
      """
      self._callOptimizeAlarm()
      master_test_node_list = [x for x in test_node_module.searchFolder()\
                               if (x.getMaster() == True  and x.getValidationState() == 'validated')]
      slave_test_node_list =  [x for x in test_node_module.searchFolder()\
                               if (x.getMaster() == False and x.getValidationState() == 'validated')]
      return master_test_node_list, slave_test_node_list
    master_test_node_list, slave_test_node_list = getMasterAndSlaveNodeList()

    # -Only one master must be elected
    self.assertEquals(1, len(master_test_node_list))
    # -Others test node must not be the matser
    self.assertEquals(3, len(slave_test_node_list))
    
    # Get the current master test node 
    current_master_test_node_1 = master_test_node_list[0]
    
    ## 2 (check election, with adding new nodes)
    # Add new nodes
    self.scalability_distributor.subscribeNode("COMP5-Scalability-Node5", computer_guid="COMP-5")
    self.scalability_distributor.subscribeNode("COMP6-Scalability-Node6", computer_guid="COMP-6")
    self.tic()
    # Check test node election
    master_test_node_list, slave_test_node_list = getMasterAndSlaveNodeList()
    # -Only one master must be elected
    self.assertEquals(1, len(master_test_node_list))
    # -Others test node must not be the matser
    self.assertEquals(5, len(slave_test_node_list))

    # Get the current master test node
    current_master_test_node_2 =  master_test_node_list[0]
    # Master test node while he is alive
    self.assertEquals(current_master_test_node_1.getTitle(),
                      current_master_test_node_2.getTitle())

    ## 3 (check election, with master deletion)
    # Invalidate master
    current_master_test_node_2.invalidate()
    # Check test node election
    master_test_node_list, slave_test_node_list = getMasterAndSlaveNodeList()
    # -Only one master must be elected
    self.assertEquals(1, len(master_test_node_list))
    # -Others test node must not be the matser
    self.assertEquals(4, len(slave_test_node_list))

    # Get the current master test node 
    current_master_test_node_3 = master_test_node_list[0]
    # Master test node must be an other test node than previously
    self.assertNotEquals(current_master_test_node_2.getTitle(), 
                         current_master_test_node_3.getTitle())
    

  def test_16_startTestSuiteERP5ScalabilityDistributor(self):
    """
    Check test suite getting, for the scalability case only the master
    test node receive test suite.
    """
    test_node_module = self.test_node_module

    # Subscribe nodes
    nodes = [self.scalability_distributor.subscribeNode("COMP1-Scalability-Node1", computer_guid="COMP-1"),
             self.scalability_distributor.subscribeNode("COMP2-Scalability-Node2", computer_guid="COMP-2"),
             self.scalability_distributor.subscribeNode("COMP3-Scalability-Node3", computer_guid="COMP-3"),
             self.scalability_distributor.subscribeNode("COMP4-Scalability-Node4", computer_guid="COMP-4")]
     # Create test suite
    test_suite = self._createTestSuite(quantity=1,priority=1, reference_correction=0,
                       specialise_value=self.scalability_distributor, portal_type="Scalability Test Suite")  
    self.tic()
    self._callOptimizeAlarm()
    # Get current master test node
    master_test_nodes = [x for x in test_node_module.searchFolder()\
                         if (x.getMaster() == True and x.getValidationState() == "validated")]     
    current_master_test_node = master_test_nodes[0]
    self.tic()
    # Each node run startTestSuite
    config_nodes = {
                     'COMP1-Scalability-Node1' :
                        json.loads(self.scalability_distributor.startTestSuite(
                                   title="COMP1-Scalability-Node1")),
                     'COMP2-Scalability-Node2' :
                        json.loads(self.scalability_distributor.startTestSuite(
                                   title="COMP2-Scalability-Node2")),
                     'COMP3-Scalability-Node3' :
                        json.loads(self.scalability_distributor.startTestSuite(
                                   title="COMP3-Scalability-Node3")),
                     'COMP4-Scalability-Node4' :
                        json.loads(self.scalability_distributor.startTestSuite(
                                   title="COMP4-Scalability-Node4"))
                   }
    # Check if master has got a non empty configuration
    self.assertNotEquals(config_nodes[current_master_test_node.getTitle()], [])
    # -Delete master test node suite from dict
    del config_nodes[current_master_test_node.getTitle()]
    # Check if slave test node have got empty list
    for suite in config_nodes.values():
      self.assertEquals(suite, [])

  def test_17_isMasterTestnodeERP5ScalabilityDistributor(self):
    """
    Check the method isMasterTestnode()
    """
    test_node_module = self.test_node_module

    # Subscribe nodes
    self.scalability_distributor.subscribeNode("COMP1-Scalability-Node1", computer_guid="COMP-1")
    self.scalability_distributor.subscribeNode("COMP2-Scalability-Node2", computer_guid="COMP-2")
    self.scalability_distributor.subscribeNode("COMP3-Scalability-Node3", computer_guid="COMP-3")
    self.scalability_distributor.subscribeNode("COMP4-Scalability-Node4", computer_guid="COMP-4")
    self.tic()
    self._callOptimizeAlarm()
    # Optimize configuration
    self.scalability_distributor.optimizeConfiguration()
    self.tic()
    # Get test nodes 
    master_test_nodes = [x for x in test_node_module.searchFolder()
                         if (x.getMaster() == True and x.getValidationState() == 'validated')]
    slave_test_nodes = [x for x in test_node_module.searchFolder()
                         if (x.getMaster() == False and x.getValidationState() == 'validated')]
    # Check isMasterTestnode method
    for master in master_test_nodes:
      self.assertTrue(self.scalability_distributor.isMasterTestnode(master.getTitle()))
    for slave in slave_test_nodes:
      self.assertTrue(not self.scalability_distributor.isMasterTestnode(slave.getTitle()))

  def test_18_checkConfigurationGenerationERP5ScalabilityDistributor(self):
    """
    Check configuration generation
    """
    test_node_module = self.test_node_module

    # Subscribe nodes
    node_list = [self.scalability_distributor.subscribeNode("COMP1-Scalability-Node1", computer_guid="COMP-1"),
             self.scalability_distributor.subscribeNode("COMP2-Scalability-Node2", computer_guid="COMP-2"),
             self.scalability_distributor.subscribeNode("COMP3-Scalability-Node3", computer_guid="COMP-3"),
             self.scalability_distributor.subscribeNode("COMP4-Scalability-Node4", computer_guid="COMP-4")]
    self.tic()
    self._callOptimizeAlarm()

    #
    def generateZopePartitionDict(i):
      """
      Generate a configuration wich uses jinja2
      """
      partition_dict = ""
      for j in range(0,i):
        family_name = ['user', 'activity'][j%2]
        partition_dict += '"%s-%s":{\n' %(family_name, node_list[j].getReference())
        partition_dict += ' "instance-count": {{ count }},\n'
        partition_dict += ' "family": "%s",\n' %family_name
        partition_dict += ' "computer_guid": "%s"\n' %node_list[j].getReference()
        partition_dict += '}' 
        if j != i-1:
          partition_dict += ',\n'
        else:
          partition_dict += '\n'
      return partition_dict


    # Generate a test suite
    # -Generate a configuration adapted to the test node list length
    cluster_configuration = '{"zope-partition-dict":{\n'
    zope_partition_dict = ""
    for i in range(1, len(node_list)+1):
      zope_partition_dict += "{%% if count == %d %%}\n" %i
      zope_partition_dict += generateZopePartitionDict(i)
      zope_partition_dict += "{% endif %}\n"
    cluster_configuration += zope_partition_dict + '\n}}'
    # -Generate graph coordinate
    graph_coordinate = range(1, len(node_list)+1)
    # -Create the test suite
    test_suite = self._createTestSuite(quantity=1,priority=1, reference_correction=0,
                       specialise_value=self.scalability_distributor, portal_type="Scalability Test Suite",
                       graph_coordinate=graph_coordinate, cluster_configuration=cluster_configuration)
    self.tic()

    # Master test node launch startTestSuite
    for node in node_list:
      if node.getMaster():
        test_suite_title = self.scalability_distributor.startTestSuite(title=node.getTitle())
#        log("test_suite_title: %s" %test_suite_title)
        break
    # Get configuration list generated from test suite
#    configuration_list = self.scalability_distributor.generateConfiguration(test_suite_title)
   
    # logs
#    log(configuration_list)    

    def test_19_testMultiDistributor(self):
      pass

