##############################################################################
#
# Copyright (c) 2003 Nexedi SARL and Contributors. All Rights Reserved.
#          Sebastien Robin <seb@nexedi.com>
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
##############################################################################

import smtplib # to send emails
from Subscription import Subscription,Signature
from xml.dom.ext.reader.Sax2 import FromXmlStream, FromXml
from xml.dom.ext import PrettyPrint
from XMLSyncUtils import XMLSyncUtils
import commands
from Conduit.ERP5Conduit import ERP5Conduit
from zLOG import LOG

class SubscriptionSynchronization(XMLSyncUtils):

  def SubSyncInit(self, subscription):
    """
      Send the first XML message from the client
    """
    LOG('SubSyncInit',0,'starting....')
    cmd_id = 1 # specifies a SyncML message-unique command identifier
    xml = ""
    xml += '<SyncML>\n'

    # syncml header
    xml += self.SyncMLHeader(subscription.getSessionId(), "1",
        subscription.getPublicationUrl(), subscription.getSubscriptionUrl())

    # syncml body
    xml += ' <SyncBody>\n'
    subscription.NewAnchor()

    # We have to set every object as NOT_SYNCHRONIZED
    subscription.startSynchronization()

    # alert message
    xml += self.SyncMLAlert(cmd_id, subscription.getSynchronizationType(),
                            subscription.getPublicationUrl(),
                            subscription.getDestinationPath(),
                            subscription.getLastAnchor(), subscription.getNextAnchor())
    cmd_id += 1

    xml += '  <Put>\n'
    xml += '   <CmdID>%s</CmdID>\n' % cmd_id ; cmd_id += 1
    # TODO add the DTD and the value devinf11
    # TODO here should be the client specification
    xml += '  </Put>\n'
    xml += ' </SyncBody>\n'

    xml += '</SyncML>\n'

    self.sendResponse(from_url=subscription.subscription_url, to_url=subscription.publication_url,
                sync_id=subscription.id, xml=xml)

  def SubSync(self, id, msg=None, RESPONSE=None):
    """
      This is the synchronization method for the client
    """
    LOG('SubSync',0,'starting... id: %s' % str(id))
    LOG('SubSync',0,'starting... msg: %s' % str(msg))

    has_response = 0 #check if subsync replies to this messages
    subscription = self.getSubscription(id)

    if msg==None:
      msg = self.readResponse(sync_id=id,from_url=subscription.getSubscriptionUrl())
    if msg==None:
      self.SubSyncInit(self.getSubscription(id))
      has_response = 1
    else:
      xml_client = msg
      if type(xml_client) in (type('a'),type(u'a')):
        xml_client = FromXml(xml_client)
      has_response = self.SubSyncModif(self.getSubscription(id),xml_client)


    if RESPONSE is not None:
      RESPONSE.redirect('manageSubscriptions')
    else:
      LOG('SubSync',0,'has_response: %s' % str(has_response))
      return has_response

  def SubSyncModif(self, subscription, xml_client):
    """
      Send the client modification, this happens after the Synchronization
      initialization
    """
    return self.SyncModif(subscription, xml_client)


  def SubLastSync(self, subscription, xml_client=None, RESPONSE=None):
    """
      Now we can read the last response of the server
    """
    self.SyncModif(subscription,xml_client)

    if RESPONSE is not None:
      RESPONSE.redirect('manageSubscriptions')

