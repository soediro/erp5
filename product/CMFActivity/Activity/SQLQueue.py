##############################################################################
#
# Copyright (c) 2002 Nexedi SARL and Contributors. All Rights Reserved.
#                    Jean-Paul Smets-Solanes <jp@nexedi.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import random
from Products.CMFActivity.ActivityTool import registerActivity
from RAMQueue import RAMQueue
from Products.CMFActivity.ActiveObject import DISTRIBUTABLE_STATE, INVOKE_ERROR_STATE, VALIDATE_ERROR_STATE

from zLOG import LOG

MAX_PRIORITY = 5

priority_weight = \
  [1] * 64 + \
  [2] * 20 + \
  [3] * 10 + \
  [4] * 5 + \
  [5] * 1

class ActivityFlushError(Exception):
    """Error during active message flush"""

class SQLQueue(RAMQueue):
  """
    A simple OOBTree based queue. It should be compatible with transactions
    and provide sequentiality. Should not create conflict
    because use of OOBTree.
  """

  def prepareQueueMessage(self, activity_tool, m):
    if m.is_registered:
      activity_tool.SQLQueue_writeMessage(path = '/'.join(m.object_path) ,
                                          method_id = m.method_id,
                                          priority = m.activity_kw.get('priority', 1),
                                          message = self.dumpMessage(m))

  def prepareDeleteMessage(self, activity_tool, m):
    # Erase all messages in a single transaction
    activity_tool.SQLQueue_delMessage(uid = m.uid)
    
  def dequeueMessage(self, activity_tool, processing_node):
    priority = random.choice(priority_weight)
    # Try to find a message at given priority level
    result = activity_tool.SQLQueue_readMessage(processing_node=processing_node, priority=priority)
    if len(result) == 0:
      # If empty, take any message
      result = activity_tool.SQLQueue_readMessage(processing_node=processing_node, priority=None)
    if len(result) > 0:
      line = result[0]
      path = line.path
      method_id = line.method_id
      # Make sure message can not be processed anylonger
      activity_tool.SQLQueue_processMessage(uid=line.uid)
      get_transaction().commit() # Release locks before starting a potentially long calculation
      m = self.loadMessage(line.message)
      # Make sure object exists
      if not m.validate(self, activity_tool):
        if line.priority > MAX_PRIORITY:
          # This is an error
          activity_tool.SQLQueue_assignMessage(uid=line.uid, processing_node = VALIDATE_ERROR_STATE)
                                                                            # Assign message back to 'error' state
          get_transaction().commit()                                        # and commit
        else:
          # Lower priority
          activity_tool.SQLQueue_setPriority(uid=line.uid, priority = line.priority + 1)
          get_transaction().commit() # Release locks before starting a potentially long calculation
      else:
        # Try to invoke
        activity_tool.invoke(m) # Try to invoke the message - what happens if read conflict error restarts transaction ?
        if m.is_executed:                                          # Make sure message could be invoked
          activity_tool.SQLQueue_delMessage(uid=line.uid)  # Delete it
          get_transaction().commit()                                        # If successful, commit
        else:
          get_transaction().abort()                                         # If not, abort transaction and start a new one
          if line.priority > MAX_PRIORITY:
            # This is an error
            activity_tool.SQLQueue_assignMessage(uid=line.uid, processing_node = INVOKE_ERROR_STATE)
                                                                              # Assign message back to 'error' state
            m.notifyUser(activity_tool)                                       # Notify Error
            get_transaction().commit()                                        # and commit
          else:
            # Lower priority
            activity_tool.SQLQueue_setPriority(uid=line.uid, priority = line.priority + 1)
            get_transaction().commit() # Release locks before starting a potentially long calculation
      return 0
    get_transaction().commit() # Release locks before starting a potentially long calculation
    return 1

  def hasActivity(self, activity_tool, object, **kw):
    my_object_path = '/'.join(object.getPhysicalPath())
    result = activity_tool.SQLQueue_hasMessage(path=my_object_path, **kw)
    if len(result) > 0:
      return result[0].message_count > 0
    return 0

  def flush(self, activity_tool, object_path, invoke=0, method_id=None, commit=0, **kw):
    """
      object_path is a tuple

      commit allows to choose mode
        - if we commit, then we make sure no locks are taken for too long
        - if we do not commit, then we can use flush in a larger transaction

      commit should in general not be used

      NOTE: commiting is very likely nonsenses here. We should just avoid to flush as much as possible
    """
    return # Do nothing here to precent overlocking
    path = '/'.join(object_path)
    # Parse each message in registered
    for m in activity_tool.getRegisteredMessageList(self):
      if object_path == m.object_path and (method_id is None or method_id == m.method_id):
        if invoke: activity_tool.invoke(m)
        activity_tool.unregisterMessage(self, m)
    # Parse each message in SQL queue
    # LOG('Flush', 0, str((path, invoke, method_id)))
    result = activity_tool.SQLQueue_readMessageList(path=path, method_id=method_id,processing_node=None)
    method_dict = {}
    for line in result:
      path = line.path
      method_id = line.method_id
      if not method_dict.has_key(method_id):
        # Only invoke once (it would be different for a queue)
        method_dict[method_id] = 1
        m = self.loadMessage(line.message, uid = line.uid)
        self.deleteMessage(m)
        if invoke:
          # First Validate
          if m.validate(self, activity_tool):
            activity_tool.invoke(m) # Try to invoke the message - what happens if invoke calls flushActivity ??
            if not m.is_executed:                                                 # Make sure message could be invoked
              # The message no longer exists
              raise ActivityFlushError, (
                  'Could not evaluate %s on %s' % (method_id , path))
          else:
            # The message no longer exists
            raise ActivityFlushError, (
                'The document %s does not exist' % path)

  def start(self, activity_tool, active_process=None):
    uid_list = activity_tool.SQLQueue_readUidList(path=path, active_process=active_process)
    activity_tool.SQLQueue_assignMessage(uid = uid_list, processing_node = DISTRIBUTABLE_STATE)

  def stop(self, activity_tool, active_process=None):
    uid_list = activity_tool.SQLQueue_readUidList(path=path, active_process=active_process)
    activity_tool.SQLQueue_assignMessage(uid = uid_list, processing_node = STOP_STATE)

  def getMessageList(self, activity_tool, processing_node=None):
    message_list = []
    result = activity_tool.SQLQueue_readMessageList(path=None, method_id=None, processing_node=None)
    for line in result:
      m = self.loadMessage(line.message)
      m.processing_node = line.processing_node
      m.priority = line.priority
      message_list.append(m)
    return message_list

  def distribute(self, activity_tool, node_count):
    processing_node = 1
    result = activity_tool.SQLQueue_readMessageList(path=None, method_id=None, processing_node = -1) # Only assign non assigned messages
    #LOG('distribute count',0,str(len(result)) )
    #LOG('distribute count',0,str(map(lambda x:x.uid, result)))
    #get_transaction().commit() # Release locks before starting a potentially long calculation
    uid_list = map(lambda x:x.uid, result)[0:100]
    for uid in uid_list:
      #LOG("distribute", 0, "assign %s" % uid)
      activity_tool.SQLQueue_assignMessage(uid=uid, processing_node=processing_node)
      #get_transaction().commit() # Release locks immediately to allow processing of messages
      processing_node = processing_node + 1
      if processing_node > node_count:
        processing_node = 1 # Round robin

registerActivity(SQLQueue)
